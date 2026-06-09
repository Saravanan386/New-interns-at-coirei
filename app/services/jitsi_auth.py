import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote

import jwt

from app.config import (
    JITSI_APP_ID,
    JITSI_APP_SECRET,
    JITSI_BASE_URL,
    JITSI_DOMAIN,
    JITSI_JWT_AUDIENCE,
    JITSI_JWT_ISSUER,
    JITSI_JWT_SUBJECT,
    JITSI_TOKEN_TTL_MINUTES,
)


def generate_room_name(classroom_id: int) -> str:
    return f"classroom_{classroom_id}_{secrets.token_urlsafe(16)}"


def _base_meeting_url(room_name: str) -> str:
    base_url = JITSI_BASE_URL or JITSI_DOMAIN
    return f"{base_url.rstrip('/')}/{quote(room_name)}"


def create_jitsi_token(
    room_name: str,
    user_id: int,
    user_name: str,
    role: str,
    *,
    expires_in_minutes: Optional[int] = None,
) -> Optional[str]:
    if not JITSI_APP_ID or not JITSI_APP_SECRET:
        return None

    ttl = expires_in_minutes or JITSI_TOKEN_TTL_MINUTES
    now = datetime.now(timezone.utc)

    payload = {
        "aud": JITSI_JWT_AUDIENCE,
        "iss": JITSI_JWT_ISSUER or JITSI_APP_ID,
        "sub": JITSI_JWT_SUBJECT,
        "room": room_name,
        "exp": now + timedelta(minutes=ttl),
        "nbf": now - timedelta(seconds=10),
        "iat": now,
        "context": {
            "user": {
                "id": str(user_id),
                "name": user_name,
                "moderator": role in {"instructor", "admin", "moderator"},
            }
        },
    }

    token = jwt.encode(payload, JITSI_APP_SECRET, algorithm="HS256")
    return token.decode("utf-8") if isinstance(token, bytes) else token


def build_meeting_url(
    room_name: str,
    user_id: int,
    user_name: str,
    role: str,
    *,
    extra_config: Optional[list[str]] = None,
) -> str:
    token = create_jitsi_token(
        room_name=room_name,
        user_id=user_id,
        user_name=user_name,
        role=role,
    )

    url = _base_meeting_url(room_name)

    query_parts = []
    if token:
        query_parts.append(f"jwt={quote(token)}")

    if query_parts:
        url = f"{url}?{'&'.join(query_parts)}"

    config_parts = [
        "config.prejoinPageEnabled=false",
        "config.startWithAudioMuted=false",
        "config.startWithVideoMuted=false",
        "config.disableModeratorIndicator=false",
        "config.enableWelcomePage=false",
        f"userInfo.displayName={quote(user_name)}",
    ]

    if extra_config:
        config_parts.extend(extra_config)

    return f"{url}#{'&'.join(config_parts)}"
