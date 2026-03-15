import logging

from sqlalchemy import select

from config import get_settings
from content_store import SiteProfile
from db import SessionLocal
from vobiz_client import build_voice_webhook_url, trigger_outbound_call

logger = logging.getLogger(__name__)


def normalize_phone_number(raw_value: str) -> str:
    digits = "".join(ch for ch in (raw_value or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"
    if len(digits) == 10:
        return f"+91{digits}"
    return f"+{digits}"


def trigger_portfolio_voice_call(name: str, email: str, phone: str) -> dict | None:
    settings = get_settings()
    db = SessionLocal()
    try:
        profile = db.scalar(select(SiteProfile).limit(1))
        if not profile or not profile.auto_call_enabled or not profile.auto_call_from_number.strip():
            logger.warning("Voice call skipped because auto-call is disabled or no from-number is configured.")
            return None
        from_number = normalize_phone_number(profile.auto_call_from_number)
    except Exception as exc:
        logger.exception("Voice call setup failed while reading profile: %s", exc)
        return None
    finally:
        db.close()

    if not from_number or not settings.public_backend_url.strip():
        logger.warning("Voice call skipped because from-number or PUBLIC_BACKEND_URL is missing.")
        return None

    to_number = normalize_phone_number(phone)
    if not to_number:
        logger.warning("Voice call skipped because destination phone is invalid: %r", phone)
        return None

    try:
        answer_url = build_voice_webhook_url(
            "/vobiz/voice/answer",
            token=settings.vobiz_webhook_secret,
            lead_name=name,
            lead_email=email,
        )
        hangup_url = build_voice_webhook_url(
            "/vobiz/voice/hangup",
            token=settings.vobiz_webhook_secret,
        )
        response = trigger_outbound_call(
            from_number=from_number,
            to_number=to_number,
            answer_url=answer_url,
            hangup_url=hangup_url,
            caller_name="Aishik AI Assistant",
        )
        logger.info("Voice call triggered successfully to=%s response=%s", to_number, response)
        return response
    except Exception as exc:
        logger.exception("Voice call trigger failed for to=%s: %s", to_number, exc)
        return None
