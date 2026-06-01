import secrets
import urllib.parse

from app.config import JITSI_DOMAIN


def generate_room_name(classroom_id: int) -> str:

    random_part = secrets.token_hex(8)

    return f"lms-classroom-{classroom_id}-{random_part}"


def create_room(room_name: str):

    safe_room = urllib.parse.quote(room_name)

    base_url = f"{JITSI_DOMAIN}/{safe_room}"

    config_params = [
        "config.prejoinPageEnabled=false",
        "config.startWithAudioMuted=false",
        "config.startWithVideoMuted=false",
        "config.disableModeratorIndicator=false",
        "config.enableWelcomePage=false",
    ]

    meeting_url = f"{base_url}#{'&'.join(config_params)}"

    return {
        "room_id": room_name,
        "host_url": meeting_url,
        "guest_url": meeting_url,
    }