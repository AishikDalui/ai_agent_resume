import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from config import get_settings
from pdf_loader import get_active_resume_source

FIXED_RESUME_FILENAME = "Aishik Dalui_resume.pdf"

logger = logging.getLogger(__name__)


def _attach_active_resume_pdf(msg: EmailMessage) -> Optional[str]:
    """
    Attach the currently active uploaded resume PDF (if available).
    Returns:
      - "attached" on success
      - "pdf_missing" when no active local PDF is available
    """
    active_resume = get_active_resume_source()
    attachment_path = Path(active_resume.get("pdf_path", "")).expanduser()
    if not attachment_path.exists() or not attachment_path.is_file():
        logger.error("Active uploaded resume PDF not found at: %s", attachment_path)
        return "pdf_missing"

    with attachment_path.open("rb") as f:
        data = f.read()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=FIXED_RESUME_FILENAME,
        )
    return "attached"


def send_otp_email(to_email: str, otp: str) -> Optional[str]:
    """
    Send the OTP to the given email address using SMTP.
    Returns a short status string on success, or None if email is not configured.
    This uses only the Python standard library (smtplib), no paid third‑party SDKs.
    """
    settings = get_settings()
    host = getattr(settings, "smtp_host", "") or ""
    port = int(getattr(settings, "smtp_port", 587) or 587)
    username = getattr(settings, "smtp_user", "") or ""
    password = (getattr(settings, "smtp_password", "") or "").replace(" ", "")
    from_email = getattr(settings, "smtp_from_email", "") or username

    if not (host and port and username and password and from_email):
        # SMTP not configured; skip sending.
        return "not_configured"

    msg = EmailMessage()
    msg["Subject"] = "Your verification code"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(f"Your one-time verification code is: {otp}")

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return "sent"
    except Exception as e:
        # Print the error so you can see it in the backend terminal
        logger.exception("OTP email send failed for %s: %s", to_email, e)
        return "failed"


def send_resume_email(to_email: str, user_name: str) -> Optional[str]:
    """
    Send resume email with PDF attachment to the given email address.
    Returns a short status string for operational visibility.
    """
    settings = get_settings()
    host = getattr(settings, "smtp_host", "") or ""
    port = int(getattr(settings, "smtp_port", 587) or 587)
    username = getattr(settings, "smtp_user", "") or ""
    password = (getattr(settings, "smtp_password", "") or "").replace(" ", "")
    from_email = getattr(settings, "smtp_from_email", "") or username

    if not (host and port and username and password and from_email):
        return "not_configured"

    message_body = (
        f"Hi {user_name}\n"
        "You are receiving this mail because you visited Aishik Dalui portfolio website.\n"
        "name: Aishik Dalui\n"
        "year of experience: 2\n"
        "working domain: Data Analyst/Business Strategist and Full stack web developer, AI automation\n"
        "email: aishikdalui@gmail.com\n"
        "phone: 8167278091\n"
        "Thanks & Regards:\n"
        "Aishik Dalui\n"
        "Data Analyst, Full stack developer with AI automation"
    )

    msg = EmailMessage()
    msg["Subject"] = "Aishik Dalui's updated resume"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(message_body)

    attach_status = _attach_active_resume_pdf(msg)
    if attach_status != "attached":
        return attach_status

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return "sent"
    except Exception as e:
        logger.exception("Resume email send failed for %s: %s", to_email, e)
        return "failed"


def send_booking_confirmation_email(
    to_email: str,
    user_name: str,
    start_at_iso: str,
    end_at_iso: str,
    meet_link: str,
    event_link: str,
) -> Optional[str]:
    """
    Send booking confirmation email including Meet and event links.
    """
    settings = get_settings()
    host = getattr(settings, "smtp_host", "") or ""
    port = int(getattr(settings, "smtp_port", 587) or 587)
    username = getattr(settings, "smtp_user", "") or ""
    password = (getattr(settings, "smtp_password", "") or "").replace(" ", "")
    from_email = getattr(settings, "smtp_from_email", "") or username

    if not (host and port and username and password and from_email):
        return "not_configured"

    body = (
        f"Hi {user_name},\n\n"
        "Your consultation appointment has been booked successfully.\n\n"
        f"Start time: {start_at_iso}\n"
        f"End time: {end_at_iso}\n"
        f"Google Meet link: {meet_link or 'Will be available on event details'}\n"
        f"Google Calendar event: {event_link or 'N/A'}\n\n"
        "Thanks & Regards,\n"
        "Aishik Dalui"
    )

    msg = EmailMessage()
    msg["Subject"] = "Your consultation booking confirmation"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)
    attach_status = _attach_active_resume_pdf(msg)
    if attach_status != "attached":
        return attach_status

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return "sent"
    except Exception as e:
        logger.exception("Booking confirmation email send failed for %s: %s", to_email, e)
        return "failed"
