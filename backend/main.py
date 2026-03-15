import time
import logging
import hmac
from pathlib import Path
from xml.sax.saxutils import escape

from fastapi import Depends, FastAPI, HTTPException, Header, UploadFile, File, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_429_TOO_MANY_REQUESTS

from auth import (
    create_admin_access_token,
    create_access_token,
    create_and_store_booking_otp,
    create_and_store_otp,
    decode_access_token,
    verify_booking_otp,
    verify_otp,
)
from auth_rate_limit import is_allowed
from chat import ask_pdf_aware_gemini
from chat_limit import can_ask_question, consume_question, CONTACT_LIMIT_MESSAGE
from config import get_settings, resolve_project_path
from content_store import Project, SiteProfile, Skill, migrate_content_schema, seed_default_content
from db import Base, engine, get_db
from google_calendar import create_google_meet_event
from google_sheets import append_user_to_sheet
from imagekit_client import delete_imagekit_file, upload_image_to_imagekit, upload_pdf_to_imagekit
from models import (
    ContactUpdateRequest,
    AdminLoginRequest,
    DemoVideoUpdateRequest,
    BookingCreateEventRequest,
    BookingCreateEventResponse,
    BookingOTPRequest,
    BookingOTPVerify,
    ChatMessageRequest,
    ChatMessageResponse,
    OTPRequest,
    OTPVerify,
    ProjectImageUploadResponse,
    ProjectItem,
    ProjectUpsertRequest,
    ResumeUploadResponse,
    SiteContentResponse,
    SkillsUpdateRequest,
    AboutUpdateRequest,
    TokenResponse,
    VoiceCallSettingsResponse,
    VoiceCallSettingsUpdateRequest,
)
from pdf_loader import get_active_resume_source, load_pdf_text, set_active_pdf_path
from pdf_loader import clear_active_resume_state
from email_sender import send_otp_email
from tasks import (
    schedule_booking_confirmation_email,
    schedule_resume_email,
    schedule_voice_call,
)
from vobiz_client import build_voice_webhook_url
from voice_agent import VOICE_CALL_INTRO, build_voice_reply, clear_voice_history
from voice_call_service import normalize_phone_number


settings = get_settings()

app = FastAPI(title="Data Analyst Portfolio Backend", version="0.1.0")

VOICE_MAX_TURNS = 6

logger = logging.getLogger(__name__)

# Configure CORS at import time (required in newer Starlette/FastAPI versions)
# For local development we allow all origins. We don't rely on cookies,
# so credentials are disabled which keeps this configuration valid.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_init_db():
    if settings.is_production and not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be configured in production.")
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        migrate_content_schema(db)
        seed_default_content(db)
    finally:
        db.close()


def get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def enforce_rate_limit(bucket: str, identifier: str, limit: int, window_seconds: int) -> None:
    if is_allowed(bucket=bucket, identifier=identifier, limit=limit, window_seconds=window_seconds):
        return
    raise HTTPException(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Please wait a few minutes and try again.",
    )


@app.post("/auth/request-otp", response_model=dict)
def request_otp(payload: OTPRequest, request: Request):
    """
    Step 1: User submits name, email, phone.
    We create and store an OTP, and send it via email
    (if SMTP is configured, e.g. Gmail).
    For development, we still include the OTP in the response so you can
    test even if SMS/email aren't set up yet.
    """
    client_id = get_client_identifier(request)
    enforce_rate_limit(
        bucket="auth-request-otp-ip",
        identifier=client_id,
        limit=settings.auth_request_otp_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    enforce_rate_limit(
        bucket="auth-request-otp-email",
        identifier=payload.email.lower(),
        limit=settings.auth_request_otp_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    otp = create_and_store_otp(payload)

    # Track OTP requests in Sheets (count increases for repeated email/phone).
    append_user_to_sheet(name=payload.name, email=payload.email, phone=payload.phone)

    # Send via email using SMTP (e.g. Gmail app password).
    email_status = send_otp_email(payload.email, otp)

    response = {
        "message": "OTP generated.",
        "email_status": email_status,    # 'sent' or null
    }
    if settings.expose_debug_otps:
        response["otp"] = otp
    return response


@app.post("/auth/verify-otp", response_model=TokenResponse)
def verify_otp_endpoint(payload: OTPVerify, name: str, request: Request):
    """
    Step 2: User submits email, phone, and OTP (and we also receive the name as a query param).
    On success, we return an access token.
    """
    client_id = get_client_identifier(request)
    enforce_rate_limit(
        bucket="auth-verify-otp-ip",
        identifier=client_id,
        limit=settings.auth_verify_otp_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    enforce_rate_limit(
        bucket="auth-verify-otp-email",
        identifier=payload.email.lower(),
        limit=settings.auth_verify_otp_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    if not verify_otp(payload.email, payload.phone, payload.otp):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP.",
        )

    token = create_access_token(email=payload.email, phone=payload.phone, name=name)

    schedule_resume_email(payload.email, name, countdown=15)
    schedule_voice_call(
        name,
        payload.email,
        payload.phone,
        countdown=max(get_settings().vobiz_call_delay_seconds, 0),
    )

    return TokenResponse(access_token=token)


@app.post("/booking/request-otp", response_model=dict)
def request_booking_otp(payload: BookingOTPRequest, request: Request):
    """
    Booking flow OTP request (name + email only).
    """
    client_id = get_client_identifier(request)
    enforce_rate_limit(
        bucket="booking-request-otp-ip",
        identifier=client_id,
        limit=settings.auth_request_otp_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    enforce_rate_limit(
        bucket="booking-request-otp-email",
        identifier=payload.email.lower(),
        limit=settings.auth_request_otp_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    otp = create_and_store_booking_otp(payload.email)
    email_status = send_otp_email(payload.email, otp)
    response = {
        "message": "Booking OTP generated.",
        "email_status": email_status,
    }
    if settings.expose_debug_otps:
        response["otp"] = otp
    return response


@app.post("/booking/verify-otp", response_model=dict)
def verify_booking_otp_endpoint(payload: BookingOTPVerify, request: Request):
    """
    Booking flow OTP verify. On success, schedule resume email and return calendar URL.
    """
    client_id = get_client_identifier(request)
    enforce_rate_limit(
        bucket="booking-verify-otp-ip",
        identifier=client_id,
        limit=settings.auth_verify_otp_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    enforce_rate_limit(
        bucket="booking-verify-otp-email",
        identifier=payload.email.lower(),
        limit=settings.auth_verify_otp_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    if not verify_booking_otp(payload.email, payload.otp):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP.",
        )

    schedule_resume_email(payload.email, payload.name)

    return {
        "verified": True,
        "calendar_url": settings.google_calendar_booking_url,
    }


@app.post("/booking/create-meet-event", response_model=BookingCreateEventResponse)
def create_booking_meet_event(payload: BookingCreateEventRequest):
    """
    Create Google Calendar event with Google Meet link and email confirmation to the user.
    """
    try:
        settings = get_settings()
        created_event = create_google_meet_event(payload)
        effective_meet_link = created_event.meet_link or settings.default_meet_link
        created_event.meet_link = effective_meet_link
        created_event.email_status = schedule_booking_confirmation_email(
            payload.email,
            payload.name,
            created_event.start_at.isoformat(),
            created_event.end_at.isoformat(),
            effective_meet_link,
            created_event.event_link,
        )
        return created_event
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Google Meet event: {exc}",
        )


def get_current_user(authorization: str = Header(default="")) -> dict:
    """
    Simple bearer token extractor/validator.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing Bearer token.")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")


def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Admin authorization required.")
    return user


def build_voice_call_settings_response(db: Session) -> VoiceCallSettingsResponse:
    profile = db.scalar(select(SiteProfile).limit(1))
    return VoiceCallSettingsResponse(
        auto_call_enabled=bool(profile.auto_call_enabled) if profile else False,
        auto_call_from_number=profile.auto_call_from_number if profile else "",
    )


def _xml_response(body: str) -> Response:
    return Response(content=body, media_type="application/xml")


def cleanup_uploaded_resume_files(upload_dir: Path, keep_paths: set[Path] | None = None) -> int:
    keep_resolved = {path.resolve() for path in (keep_paths or set()) if path.exists()}
    removed_count = 0

    if not upload_dir.exists():
        return removed_count

    for candidate in upload_dir.glob("*.pdf"):
        try:
            resolved = candidate.resolve()
            if resolved in keep_resolved:
                continue
            candidate.unlink(missing_ok=True)
            removed_count += 1
        except Exception:
            continue

    return removed_count


def build_site_content_response(db: Session) -> SiteContentResponse:
    profile = db.scalar(select(SiteProfile).limit(1))
    about_text = profile.about_me if profile else ""
    contact_heading = profile.contact_heading if profile else "Contact"
    demo_video_url = profile.demo_video_url if profile else ""
    contact_message = profile.contact_message if profile else ""

    skills = db.scalars(select(Skill).order_by(Skill.sort_order.asc(), Skill.id.asc())).all()
    skill_names = [item.name for item in skills]

    projects = db.scalars(select(Project).order_by(Project.sort_order.asc(), Project.id.asc())).all()
    project_items = [
        ProjectItem(
            id=item.id,
            title=item.title,
            description=item.description,
            image_url=item.image_url,
            image_file_id=item.image_file_id,
            project_link=item.project_link,
            sort_order=item.sort_order,
        )
        for item in projects
    ]
    return SiteContentResponse(
        about_me=about_text,
        contact_heading=contact_heading,
        demo_video_url=demo_video_url,
        contact_message=contact_message,
        skills=skill_names,
        projects=project_items,
    )


@app.get("/content/public", response_model=SiteContentResponse)
def get_public_content(db: Session = Depends(get_db)):
    return build_site_content_response(db)


@app.post("/admin/login", response_model=TokenResponse)
def admin_login(payload: AdminLoginRequest, request: Request):
    settings = get_settings()
    client_id = get_client_identifier(request)
    enforce_rate_limit(
        bucket="admin-login-ip",
        identifier=client_id,
        limit=settings.admin_login_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    enforce_rate_limit(
        bucket="admin-login-email",
        identifier=payload.email.lower(),
        limit=settings.admin_login_limit,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )
    if not settings.admin_email or not settings.admin_password:
        raise HTTPException(
            status_code=500,
            detail="Admin credentials are not configured on the server.",
        )
    email_ok = hmac.compare_digest(payload.email.lower(), settings.admin_email.lower())
    password_ok = hmac.compare_digest(payload.password, settings.admin_password)
    if not email_ok or not password_ok:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials.")
    token = create_admin_access_token(payload.email)
    return TokenResponse(access_token=token)


@app.put("/admin/content/about", response_model=SiteContentResponse)
def admin_update_about(payload: AboutUpdateRequest, _admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    profile = db.scalar(select(SiteProfile).limit(1))
    if not profile:
        profile = SiteProfile(
            id=1,
            about_me=payload.about_me.strip(),
            contact_heading="Contact",
            demo_video_url="",
            auto_call_enabled=False,
            auto_call_from_number="",
            contact_message="",
        )
        db.add(profile)
    else:
        profile.about_me = payload.about_me.strip()
    db.commit()
    return build_site_content_response(db)


@app.put("/admin/content/contact", response_model=SiteContentResponse)
def admin_update_contact(
    payload: ContactUpdateRequest,
    _admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(SiteProfile).limit(1))
    if not profile:
        profile = SiteProfile(
            id=1,
            about_me="",
            contact_heading=payload.contact_heading.strip(),
            demo_video_url="",
            auto_call_enabled=False,
            auto_call_from_number="",
            contact_message=payload.contact_message.strip(),
        )
        db.add(profile)
    else:
        profile.contact_heading = payload.contact_heading.strip()
        profile.contact_message = payload.contact_message.strip()
    db.commit()
    return build_site_content_response(db)


@app.put("/admin/content/demo-video", response_model=SiteContentResponse)
def admin_update_demo_video(
    payload: DemoVideoUpdateRequest,
    _admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(SiteProfile).limit(1))
    if not profile:
        profile = SiteProfile(
            id=1,
            about_me="",
            contact_heading="Contact",
            demo_video_url=payload.demo_video_url.strip(),
            auto_call_enabled=False,
            auto_call_from_number="",
            contact_message="",
        )
        db.add(profile)
    else:
        profile.demo_video_url = payload.demo_video_url.strip()
    db.commit()
    return build_site_content_response(db)


@app.get("/admin/settings/voice-call", response_model=VoiceCallSettingsResponse)
def admin_get_voice_call_settings(
    _admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return build_voice_call_settings_response(db)


@app.put("/admin/settings/voice-call", response_model=VoiceCallSettingsResponse)
def admin_update_voice_call_settings(
    payload: VoiceCallSettingsUpdateRequest,
    _admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(SiteProfile).limit(1))
    if not profile:
        profile = SiteProfile(
            id=1,
            about_me="",
            contact_heading="Contact",
            demo_video_url="",
            auto_call_enabled=payload.auto_call_enabled,
            auto_call_from_number=payload.auto_call_from_number.strip(),
            contact_message="",
        )
        db.add(profile)
    else:
        profile.auto_call_enabled = payload.auto_call_enabled
        profile.auto_call_from_number = payload.auto_call_from_number.strip()
    db.commit()
    return build_voice_call_settings_response(db)


@app.put("/admin/content/skills", response_model=SiteContentResponse)
def admin_update_skills(
    payload: SkillsUpdateRequest,
    _admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    normalized = [item.strip() for item in payload.skills if item and item.strip()]
    deduped: list[str] = []
    for skill_name in normalized:
        if skill_name not in deduped:
            deduped.append(skill_name)

    if len(deduped) > 10:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Maximum 10 skills are allowed.")

    db.query(Skill).delete()
    for idx, skill_name in enumerate(deduped):
        db.add(Skill(name=skill_name, sort_order=idx))
    db.commit()
    return build_site_content_response(db)


@app.post("/admin/upload-project-image", response_model=ProjectImageUploadResponse)
async def admin_upload_project_image(file: UploadFile = File(...), _admin: dict = Depends(get_current_admin)):
    filename = (file.filename or "").strip()
    lower_name = filename.lower()
    allowed_exts = (".png", ".jpg", ".jpeg", ".webp", ".gif")
    if not lower_name.endswith(allowed_exts):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Only image files are allowed.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Uploaded image is empty.")

    try:
        result = upload_image_to_imagekit(file_bytes, Path(filename).name.replace(" ", "_"))
    except Exception as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"Image upload failed: {exc}")

    return ProjectImageUploadResponse(
        image_url=result.get("url", ""),
        image_file_id=result.get("file_id", ""),
    )


@app.post("/admin/content/projects", response_model=SiteContentResponse)
def admin_create_project(
    payload: ProjectUpsertRequest,
    _admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    project_count = db.query(Project).count()
    if project_count >= 3:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Only up to 3 projects are allowed.")

    db.add(
        Project(
            title=payload.title.strip(),
            description=payload.description.strip(),
            image_url=payload.image_url.strip(),
            image_file_id=payload.image_file_id.strip(),
            project_link=payload.project_link.strip(),
            sort_order=payload.sort_order,
        )
    )
    db.commit()
    return build_site_content_response(db)


@app.put("/admin/content/projects/{project_id}", response_model=SiteContentResponse)
def admin_update_project(
    project_id: int,
    payload: ProjectUpsertRequest,
    _admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    old_image_file_id = project.image_file_id
    project.title = payload.title.strip()
    project.description = payload.description.strip()
    project.image_url = payload.image_url.strip()
    project.image_file_id = payload.image_file_id.strip()
    project.project_link = payload.project_link.strip()
    project.sort_order = payload.sort_order
    db.commit()

    if old_image_file_id and old_image_file_id != project.image_file_id:
        try:
            delete_imagekit_file(old_image_file_id)
        except Exception:
            pass

    return build_site_content_response(db)


@app.delete("/admin/content/projects/{project_id}", response_model=SiteContentResponse)
def admin_delete_project(
    project_id: int,
    _admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    old_image_file_id = project.image_file_id
    db.delete(project)
    db.commit()

    if old_image_file_id:
        try:
            delete_imagekit_file(old_image_file_id)
        except Exception:
            pass

    return build_site_content_response(db)


@app.post("/admin/upload-resume", response_model=ResumeUploadResponse)
async def admin_upload_resume(file: UploadFile = File(...), _admin: dict = Depends(get_current_admin)):
    filename = (file.filename or "").strip()
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    settings = get_settings()
    upload_dir = resolve_project_path(settings.uploaded_resume_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name.replace(" ", "_")
    local_file_path = upload_dir / f"{int(time.time())}_{safe_name}"
    local_file_path.write_bytes(file_bytes)

    previous_resume = get_active_resume_source()
    previous_imagekit_file_id = previous_resume.get("imagekit_file_id", "")

    try:
        upload_result = upload_pdf_to_imagekit(file_bytes, safe_name)
    except Exception as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"ImageKit upload failed: {exc}")

    imagekit_url = upload_result.get("url", "")
    new_imagekit_file_id = upload_result.get("file_id", "")

    set_active_pdf_path(
        str(local_file_path),
        imagekit_url=imagekit_url,
        imagekit_file_id=new_imagekit_file_id,
    )
    extracted_text = load_pdf_text()
    if not extracted_text:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Could not extract text from the uploaded PDF.",
        )

    if previous_imagekit_file_id and previous_imagekit_file_id != new_imagekit_file_id:
        try:
            delete_imagekit_file(previous_imagekit_file_id)
        except Exception:
            # Do not fail upload response if old file cleanup fails.
            pass

    cleanup_uploaded_resume_files(upload_dir, keep_paths={local_file_path})

    return ResumeUploadResponse(
        message="Resume uploaded successfully.",
        imagekit_url=imagekit_url,
        active_pdf_path=str(local_file_path),
        extracted_chars=len(extracted_text),
    )


@app.post("/admin/remove-local-resume", response_model=dict)
def admin_remove_local_resume(_admin: dict = Depends(get_current_admin)):
    settings = get_settings()
    active_resume = get_active_resume_source()
    active_path = Path(active_resume.get("pdf_path", ""))
    upload_dir = resolve_project_path(settings.uploaded_resume_dir)
    old_imagekit_file_id = active_resume.get("imagekit_file_id", "")

    removed_local = False
    try:
        if active_path.exists() and active_path.resolve().is_relative_to(upload_dir):
            active_path.unlink(missing_ok=True)
            removed_local = True
    except Exception:
        removed_local = False

    clear_active_resume_state()
    removed_imagekit = False
    if old_imagekit_file_id:
        try:
            delete_imagekit_file(old_imagekit_file_id)
            removed_imagekit = True
        except Exception:
            removed_imagekit = False
    cleanup_uploaded_resume_files(upload_dir)
    return {
        "message": "Active resume removed.",
        "removed_local_file": removed_local,
        "removed_imagekit_file": removed_imagekit,
    }


@app.post("/chat", response_model=ChatMessageResponse)
def chat_with_pdf(payload: ChatMessageRequest, user: dict = Depends(get_current_user)):
    """
    Chat endpoint that uses Gemini + PDF content to answer questions.
    Requires a valid Bearer token in the Authorization header.
    """
    user_email = str(user.get("sub", "")).lower().strip()
    if not user_email:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid user identity in token.")

    if not can_ask_question(user_email):
        raise HTTPException(status_code=HTTP_429_TOO_MANY_REQUESTS, detail=CONTACT_LIMIT_MESSAGE)

    consume_question(user_email)

    try:
        reply = ask_pdf_aware_gemini(payload.message)
        return reply
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {exc}")


@app.post("/vobiz/voice/answer")
async def vobiz_voice_answer(
    request: Request,
    token: str = "",
    lead_name: str = "",
    lead_email: str = "",
):
    settings = get_settings()
    if settings.vobiz_webhook_secret and token != settings.vobiz_webhook_secret:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Vobiz webhook token.")

    form = await request.form()
    form_data = {key: str(value) for key, value in form.items()}
    call_id = str(form.get("CallUUID") or form.get("call_uuid") or "").strip() or f"voice-{int(time.time())}"
    logger.info("voice answer webhook received call_id=%s keys=%s payload=%s", call_id, sorted(form_data.keys()), form_data)
    caller_name = escape((lead_name or "there").strip())
    speak_text = escape(VOICE_CALL_INTRO.replace("Aishik’s", "Aishik's"))
    xml_body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Speak>{speak_text}</Speak>"
        "</Response>"
    )
    return _xml_response(xml_body)


@app.post("/vobiz/voice/respond")
async def vobiz_voice_respond(
    request: Request,
    token: str = "",
    call_id: str = "",
    lead_name: str = "",
    lead_email: str = "",
    turn: str = "1",
):
    settings = get_settings()
    if settings.vobiz_webhook_secret and token != settings.vobiz_webhook_secret:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Vobiz webhook token.")

    form = await request.form()
    form_data = {key: str(value) for key, value in form.items()}
    speech_candidates = [
        form.get("Speech"),
        form.get("speech"),
        form.get("SpeechResult"),
        form.get("transcript"),
        form.get("Transcript"),
        form.get("text"),
        form.get("Text"),
        form.get("query"),
    ]
    speech_text = ""
    for candidate in speech_candidates:
        candidate_text = str(candidate or "").strip()
        if candidate_text:
            speech_text = candidate_text
            break
    current_turn = max(int(turn or "1"), 1)
    logger.info(
        "voice respond webhook received call_id=%s turn=%s speech=%r keys=%s payload=%s",
        call_id,
        current_turn,
        speech_text,
        sorted(form_data.keys()),
        form_data,
    )

    if not speech_text:
        if current_turn >= 2:
            clear_voice_history(call_id)
            xml_body = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                "<Response>"
                "<Speak>Thank you for your time. You can connect with Aishik by email at aishikdalui@gmail.com. Goodbye.</Speak>"
                "</Response>"
            )
            return _xml_response(xml_body)

        retry_url = build_voice_webhook_url(
            "/vobiz/voice/respond",
            token=settings.vobiz_webhook_secret,
            call_id=call_id,
            lead_name=lead_name,
            lead_email=lead_email,
            turn=str(current_turn + 1),
        )
        xml_body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            "<Speak>I could not hear the question clearly. Please ask a short question about Aishik's skills, projects, or hiring availability.</Speak>"
            f'<Gather inputType="speech" action="{escape(retry_url)}" method="POST" speechTimeout="4" hints="skills, experience, projects, hiring, React Native, Python, FastAPI" />'
            "</Response>"
        )
        return _xml_response(xml_body)

    try:
        reply = build_voice_reply(call_id=call_id, user_text=speech_text, caller_name=lead_name)
        logger.info("voice reply generated call_id=%s turn=%s reply=%r", call_id, current_turn, reply)
    except Exception as exc:
        logger.exception("voice-call gemini reply failed call_id=%s: %s", call_id, exc)
        reply = (
            "Let me quickly go through Aishik's resume. He works on React Native, FastAPI, Python, AI automation, "
            "and business growth solutions. If you would like, I can ask Aishik to connect with you by email."
        )

    if current_turn >= VOICE_MAX_TURNS:
        clear_voice_history(call_id)
        xml_body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f"<Speak>{escape(reply)}</Speak>"
            "<Speak>Thank you for your interest. Please feel free to email Aishik at aishikdalui@gmail.com. Goodbye.</Speak>"
            "</Response>"
        )
        return _xml_response(xml_body)

    next_url = build_voice_webhook_url(
        "/vobiz/voice/respond",
        token=settings.vobiz_webhook_secret,
        call_id=call_id,
        lead_name=lead_name,
        lead_email=lead_email,
        turn=str(current_turn + 1),
    )
    xml_body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Speak>{escape(reply)}</Speak>"
        f'<Gather inputType="speech" action="{escape(next_url)}" method="POST" speechTimeout="auto" />'
        "</Response>"
    )
    return _xml_response(xml_body)


@app.post("/vobiz/voice/hangup")
async def vobiz_voice_hangup(request: Request, token: str = ""):
    settings = get_settings()
    if settings.vobiz_webhook_secret and token != settings.vobiz_webhook_secret:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Vobiz webhook token.")
    form = await request.form()
    call_id = str(form.get("CallUUID") or form.get("call_uuid") or "").strip()
    if call_id:
        clear_voice_history(call_id)
    return JSONResponse({"status": "ok"})


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})
