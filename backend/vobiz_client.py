from urllib.parse import urlencode

import requests

from config import get_settings


VOBIZ_API_BASE = "https://api.vobiz.ai/api/v1"


def trigger_outbound_call(*, from_number: str, to_number: str, answer_url: str, hangup_url: str, caller_name: str) -> dict:
    settings = get_settings()
    if not settings.vobiz_auth_id or not settings.vobiz_auth_token:
        raise ValueError("Vobiz credentials are not configured.")

    endpoint = f"{VOBIZ_API_BASE}/Account/{settings.vobiz_auth_id}/Call/"
    payload = {
        "from": from_number.replace("+", ""),
        "to": to_number.replace("+", ""),
        "answer_url": answer_url,
        "answer_method": "POST",
        "hangup_url": hangup_url,
        "hangup_method": "POST",
        "caller_name": caller_name[:50],
        "ring_timeout": 30,
        "time_limit": 900,
        "machine_detection": "false",
    }
    response = requests.post(
        endpoint,
        headers={
            "X-Auth-ID": settings.vobiz_auth_id,
            "X-Auth-Token": settings.vobiz_auth_token,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def build_voice_webhook_url(path: str, **query: str) -> str:
    settings = get_settings()
    base = settings.public_backend_url.strip().rstrip("/")
    if not base:
        raise ValueError("PUBLIC_BACKEND_URL is not configured.")

    encoded = urlencode({key: value for key, value in query.items() if value})
    return f"{base}{path}" + (f"?{encoded}" if encoded else "")
