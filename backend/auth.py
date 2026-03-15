import random
import string
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

import jwt

from config import get_settings
from models import OTPRequest
from runtime_store import with_redis


_otp_store: Dict[Tuple[str, str], Tuple[str, datetime]] = {}
_booking_otp_store: Dict[str, Tuple[str, datetime]] = {}


def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _otp_cache_key(email: str, phone: str) -> str:
    return f"otp:chat:{email.lower()}:{phone}"


def _booking_otp_cache_key(email: str) -> str:
    return f"otp:booking:{email.lower()}"


def create_and_store_otp(payload: OTPRequest, ttl_minutes: int | None = None) -> str:
    settings = get_settings()
    ttl_minutes = ttl_minutes or settings.otp_ttl_minutes
    otp = generate_otp()
    expires_at = _utc_now() + timedelta(minutes=ttl_minutes)
    key = (payload.email.lower(), payload.phone)
    _otp_store[key] = (otp, expires_at)
    with_redis(
        lambda client: client.setex(
            _otp_cache_key(payload.email, payload.phone),
            ttl_minutes * 60,
            otp,
        )
    )
    return otp


def verify_otp(email: str, phone: str, otp: str) -> bool:
    key = (email.lower(), phone)
    redis_key = _otp_cache_key(email, phone)
    stored_otp = with_redis(lambda client: client.get(redis_key))
    if isinstance(stored_otp, str):
        if stored_otp != otp:
            return False
        with_redis(lambda client: client.delete(redis_key))
        _otp_store.pop(key, None)
        return True
    if key not in _otp_store:
        return False
    stored_otp, expires_at = _otp_store[key]
    if _utc_now() > expires_at:
        _otp_store.pop(key, None)
        return False
    if stored_otp != otp:
        return False
    _otp_store.pop(key, None)
    return True


def create_access_token(email: str, phone: str, name: str, expires_minutes: int = 60) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email.lower(),
        "phone": phone,
        "name": name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def create_and_store_booking_otp(email: str, ttl_minutes: int | None = None) -> str:
    settings = get_settings()
    ttl_minutes = ttl_minutes or settings.otp_ttl_minutes
    otp = generate_otp()
    expires_at = _utc_now() + timedelta(minutes=ttl_minutes)
    _booking_otp_store[email.lower()] = (otp, expires_at)
    with_redis(
        lambda client: client.setex(
            _booking_otp_cache_key(email),
            ttl_minutes * 60,
            otp,
        )
    )
    return otp


def verify_booking_otp(email: str, otp: str) -> bool:
    key = email.lower()
    redis_key = _booking_otp_cache_key(email)
    stored_otp = with_redis(lambda client: client.get(redis_key))
    if isinstance(stored_otp, str):
        if stored_otp != otp:
            return False
        with_redis(lambda client: client.delete(redis_key))
        _booking_otp_store.pop(key, None)
        return True
    if key not in _booking_otp_store:
        return False
    stored_otp, expires_at = _booking_otp_store[key]
    if _utc_now() > expires_at:
        _booking_otp_store.pop(key, None)
        return False
    if stored_otp != otp:
        return False
    _booking_otp_store.pop(key, None)
    return True


def create_admin_access_token(email: str, expires_minutes: int = 60) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email.lower(),
        "role": "admin",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    data = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return data
