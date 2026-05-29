
# app/services/jitsi_service.py

import secrets
import urllib.parse
from app.config import JITSI_DOMAIN


def generate_room_name(course_id: int, batch_name: str) -> str:
    """
    Generates a unique but readable room name.
    """
    random_part = secrets.token_hex(4)

    safe_batch = (
        batch_name.lower()
        .replace(" ", "-")
        .replace("_", "-")
    )

    return f"lms-{course_id}-{safe_batch}-{random_part}"


def create_room(
    room_name: str,
    user_name: str | None = None,
    is_instructor: bool = False,
):
    """
    Generates secure Jitsi meeting URLs.
    """

    safe_room = urllib.parse.quote(room_name)

    base_url = f"{JITSI_DOMAIN}/{safe_room}"

    params = {
        "config.prejoinPageEnabled": "false",
        "config.startWithAudioMuted": "false",
        "config.startWithVideoMuted": "false",
        "config.disableModeratorIndicator": "false",
        "config.enableWelcomePage": "false",
    }

    if user_name:
        params["userInfo.displayName"] = user_name

    query_string = "&".join(
        f"{k}={urllib.parse.quote(v)}"
        for k, v in params.items()
    )

    meeting_url = f"{base_url}#{query_string}"

    return {
        "room_id": room_name,
        "host_url": meeting_url,
        "guest_url": meeting_url,
    }

