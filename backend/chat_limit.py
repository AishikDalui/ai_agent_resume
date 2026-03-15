from datetime import datetime
from zoneinfo import ZoneInfo


DAILY_CHAT_LIMIT = 7
CONTACT_LIMIT_MESSAGE = (
    "You exceeded your daily limit (7 questions). "
    "Please contact Aishik Dalui at 8167278091 "
    "or email aishikdalui@gmail.com for more info."
)

_IST = ZoneInfo("Asia/Kolkata")
_daily_counts: dict[tuple[str, str], int] = {}


def _today_key() -> str:
    return datetime.now(_IST).strftime("%Y-%m-%d")


def can_ask_question(email: str) -> bool:
    key = (email.lower().strip(), _today_key())
    return _daily_counts.get(key, 0) < DAILY_CHAT_LIMIT


def consume_question(email: str) -> int:
    """
    Increment today's chat count for email and return updated count.
    """
    key = (email.lower().strip(), _today_key())
    current = _daily_counts.get(key, 0) + 1
    _daily_counts[key] = current
    return current
