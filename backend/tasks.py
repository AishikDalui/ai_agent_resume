import threading
import time
from typing import Any, Callable

from celery.utils.log import get_task_logger

from celery_app import celery_app
from email_sender import send_booking_confirmation_email, send_resume_email
from voice_call_service import trigger_portfolio_voice_call


logger = get_task_logger(__name__)

_WORKER_CHECK_TTL_SECONDS = 10
_last_worker_check_at = 0.0
_last_worker_available = False


def _has_active_celery_worker() -> bool:
    global _last_worker_check_at, _last_worker_available

    now = time.time()
    if now - _last_worker_check_at < _WORKER_CHECK_TTL_SECONDS:
        return _last_worker_available

    try:
        inspector = celery_app.control.inspect(timeout=1)
        ping_response = inspector.ping() if inspector else None
        _last_worker_available = bool(ping_response)
    except Exception as exc:
        logger.warning("celery worker availability check failed: %s", exc)
        _last_worker_available = False

    _last_worker_check_at = now
    return _last_worker_available


def _run_local_background_job(
    *,
    job_name: str,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    countdown: int = 0,
) -> None:
    def runner() -> None:
        if countdown > 0:
            time.sleep(countdown)
        try:
            result = func(*args)
            logger.info("local background job %s completed with result=%s", job_name, result)
        except Exception as exc:
            logger.exception("local background job %s failed: %s", job_name, exc)

    threading.Thread(target=runner, daemon=True, name=f"local-{job_name}").start()


def schedule_resume_email(to_email: str, user_name: str, countdown: int = 0) -> str:
    args = (to_email, user_name)
    if _has_active_celery_worker():
        send_resume_email_task.apply_async(args=list(args), countdown=countdown)
        return "queued"

    _run_local_background_job(
        job_name="resume-email",
        func=send_resume_email,
        args=args,
        countdown=countdown,
    )
    return "local_background"


def schedule_booking_confirmation_email(
    to_email: str,
    user_name: str,
    start_at_iso: str,
    end_at_iso: str,
    meet_link: str,
    event_link: str,
) -> str:
    args = (to_email, user_name, start_at_iso, end_at_iso, meet_link, event_link)
    if _has_active_celery_worker():
        send_booking_confirmation_email_task.delay(*args)
        return "queued"

    _run_local_background_job(
        job_name="booking-confirmation-email",
        func=send_booking_confirmation_email,
        args=args,
    )
    return "local_background"


def schedule_voice_call(name: str, email: str, phone: str, countdown: int = 0) -> str:
    args = (name, email, phone)
    if _has_active_celery_worker():
        trigger_voice_call_task.apply_async(args=list(args), countdown=countdown)
        return "queued"

    _run_local_background_job(
        job_name="voice-call",
        func=trigger_portfolio_voice_call,
        args=args,
        countdown=countdown,
    )
    return "local_background"


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
    name="tasks.send_resume_email_task",
)
def send_resume_email_task(self, to_email: str, user_name: str) -> str:
    status = send_resume_email(to_email, user_name) or "unknown"
    logger.info("resume email task completed for %s with status=%s", to_email, status)
    return status


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
    name="tasks.send_booking_confirmation_email_task",
)
def send_booking_confirmation_email_task(
    self,
    to_email: str,
    user_name: str,
    start_at_iso: str,
    end_at_iso: str,
    meet_link: str,
    event_link: str,
) -> str:
    status = send_booking_confirmation_email(
        to_email=to_email,
        user_name=user_name,
        start_at_iso=start_at_iso,
        end_at_iso=end_at_iso,
        meet_link=meet_link,
        event_link=event_link,
    ) or "unknown"
    logger.info("booking confirmation email task completed for %s with status=%s", to_email, status)
    return status


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 4},
    name="tasks.trigger_voice_call_task",
)
def trigger_voice_call_task(self, name: str, email: str, phone: str) -> str:
    result = trigger_portfolio_voice_call(name=name, email=email, phone=phone)
    logger.info("voice call task completed for %s with result=%s", phone, bool(result))
    return "triggered" if result else "skipped"
