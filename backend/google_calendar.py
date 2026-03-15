import logging
from datetime import timedelta
from uuid import uuid4

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import get_settings, resolve_project_path
from models import BookingCreateEventRequest, BookingCreateEventResponse


_LOGGER = logging.getLogger(__name__)
_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _build_calendar_service():
    settings = get_settings()
    credentials_path = resolve_project_path(settings.google_service_account_json)
    creds = Credentials.from_service_account_file(
        str(credentials_path),
        scopes=_CALENDAR_SCOPES,
    )
    if settings.google_calendar_impersonate_user:
        creds = creds.with_subject(settings.google_calendar_impersonate_user)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def create_google_meet_event(payload: BookingCreateEventRequest) -> BookingCreateEventResponse:
    settings = get_settings()
    service = _build_calendar_service()

    end_at = payload.start_at + timedelta(minutes=payload.duration_minutes)
    summary = f"Portfolio Session with {payload.name}"
    description_parts = [
        "Booked via Aishik Dalui portfolio website.",
        f"Guest name: {payload.name}",
        f"Guest email: {payload.email}",
    ]
    if payload.notes:
        description_parts.append(f"Notes: {payload.notes}")

    event_body = {
        "summary": summary,
        "description": "\n".join(description_parts),
        "start": {
            "dateTime": payload.start_at.isoformat(),
            "timeZone": settings.google_calendar_timezone,
        },
        "end": {
            "dateTime": end_at.isoformat(),
            "timeZone": settings.google_calendar_timezone,
        },
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    try:
        created_event = service.events().insert(
            calendarId=settings.google_calendar_id,
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="none",
        ).execute()
    except HttpError as exc:
        error_text = str(exc)
        if "Invalid conference type value" not in error_text:
            raise
        _LOGGER.warning("Conference creation failed; creating event without Meet: %s", error_text)
        fallback_body = {
            "summary": event_body["summary"],
            "description": event_body["description"],
            "start": event_body["start"],
            "end": event_body["end"],
        }
        created_event = service.events().insert(
            calendarId=settings.google_calendar_id,
            body=fallback_body,
            sendUpdates="none",
        ).execute()

    event_id = created_event.get("id", "")
    event_link = created_event.get("htmlLink", "")
    meet_link = created_event.get("hangoutLink", "")
    if not meet_link:
        entry_points = created_event.get("conferenceData", {}).get("entryPoints", [])
        meet_link = next((x.get("uri", "") for x in entry_points if x.get("uri")), "")

    if not event_id:
        _LOGGER.warning("Google Calendar did not return an event ID.")

    return BookingCreateEventResponse(
        event_id=event_id,
        event_link=event_link,
        meet_link=meet_link,
        start_at=payload.start_at,
        end_at=end_at,
    )
