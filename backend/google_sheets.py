from datetime import datetime
import logging
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config import get_settings, resolve_project_path
from models import UserSheetEntry


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
_LOGGER = logging.getLogger(__name__)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_phone(phone: str) -> str:
    return phone.strip()


def _get_client() -> Optional[gspread.Client]:
    settings = get_settings()
    try:
        creds = Credentials.from_service_account_file(
            str(resolve_project_path(settings.google_service_account_json)), scopes=_SCOPES
        )
        return gspread.authorize(creds)
    except Exception as exc:
        _LOGGER.warning("Google Sheets client init failed: %s", exc)
        return None


def _is_header_row(row: list[str]) -> bool:
    if len(row) < 3:
        return False
    first_three = [c.strip().lower() for c in row[:3]]
    return first_three == ["name", "email", "phone"]


def _now_iso_utc() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _safe_int(value: str, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _sort_sheet_by_updated_at_desc(sheet: gspread.Worksheet, has_header: bool) -> None:
    """
    Sort rows by updated_at (column F) in descending order.
    Keeps header pinned when a header row exists.
    """
    start_row_index = 1 if has_header else 0
    try:
        sheet.spreadsheet.batch_update(
            {
                "requests": [
                    {
                        "sortRange": {
                            "range": {
                                "sheetId": sheet.id,
                                "startRowIndex": start_row_index,
                            },
                            "sortSpecs": [
                                {
                                    "dimensionIndex": 5,  # Column F (updated_at)
                                    "sortOrder": "DESCENDING",
                                }
                            ],
                        }
                    }
                ]
            }
        )
    except Exception as exc:
        _LOGGER.warning("Failed to sort rows by updated_at desc: %s", exc)


def append_user_to_sheet(name: str, email: str, phone: str) -> Optional[UserSheetEntry]:
    """
    Upsert user in Google Sheet using email OR phone as identity.
    - First time: create row with count=1.
    - Repeated OTP request: increment count, refresh updated_at.
    Rows are sorted by updated_at descending after each write.
    """
    settings = get_settings()
    if not settings.google_sheets_spreadsheet_id:
        return None

    client = _get_client()
    if client is None:
        return None

    try:
        sheet = client.open_by_key(settings.google_sheets_spreadsheet_id).sheet1
    except Exception as exc:
        # Keep auth flow working even if Sheets is misconfigured/unavailable.
        _LOGGER.warning("Failed to open Google Sheet by key: %s", exc)
        return None

    normalized_email = _normalize_email(email)
    normalized_phone = _normalize_phone(phone)
    now_iso = _now_iso_utc()

    try:
        rows = sheet.get_all_values()
    except Exception as exc:
        _LOGGER.warning("Failed to read existing rows from Google Sheet: %s", exc)
        return None

    has_header = bool(rows) and _is_header_row(rows[0])
    start_idx = 1 if has_header else 0
    match_row_index_1_based: Optional[int] = None
    existing_row: list[str] = []

    for idx in range(start_idx, len(rows)):
        row = rows[idx]
        row_email = _normalize_email(row[1]) if len(row) > 1 else ""
        row_phone = _normalize_phone(row[2]) if len(row) > 2 else ""
        if row_email == normalized_email or row_phone == normalized_phone:
            match_row_index_1_based = idx + 1
            existing_row = row
            break

    try:
        if match_row_index_1_based is None:
            created_at_iso = now_iso
            count = 1
            sheet.append_row(
                [name, email, phone, str(count), created_at_iso, now_iso],
                value_input_option="RAW",
            )
        else:
            created_at_iso = existing_row[4] if len(existing_row) > 4 and existing_row[4] else now_iso
            existing_count = existing_row[3] if len(existing_row) > 3 else "0"
            count = _safe_int(existing_count, 0) + 1
            sheet.update(
                f"A{match_row_index_1_based}:F{match_row_index_1_based}",
                [[name, email, phone, str(count), created_at_iso, now_iso]],
                value_input_option="RAW",
            )

        _sort_sheet_by_updated_at_desc(sheet, has_header=has_header)
    except Exception as exc:
        _LOGGER.warning("Failed to upsert row to Google Sheet: %s", exc)
        return None

    return UserSheetEntry(
        name=name,
        email=email,
        phone=phone,
        created_at=datetime.utcnow(),
    )
