# app/services/livekit_service.py
"""
LiveKit helper service.
Provides token generation and room creation for class sessions.
"""

import time
from livekit import api
from app.config import LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_SECRET


def generate_token(
    room_name: str,
    user_id: int,
    user_name: str,
    is_instructor: bool = False
) -> str:
    """
    Generate a signed LiveKit JWT for a participant.

    - Instructors get can_publish=True (they share video/audio/screen)
    - Students get can_publish=True too (so they can speak/show video)
    - Both get can_subscribe=True (receive others' streams)
    """
    grants = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,

        # ── Host / Instructor privileges ──────────────────────────────────
        # room_admin : can mute, kick participants, and end the meeting
        # room_create: allows the instructor to create/own the room (host)
        # room_record: instructor can start/stop recording
        room_admin=is_instructor,
        room_create=is_instructor,
        room_record=is_instructor,
    )

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_SECRET)
        .with_grants(grants)
        .with_identity(str(user_id))
        .with_name(user_name)
        .to_jwt()           # default TTL = 6 hours (timedelta(hours=6))
    )
    return token


async def create_room(room_name: str, max_participants: int = 30) -> dict:
    """
    Create (or ensure existence of) a LiveKit room.
    Returns room info dict.
    """
    lk_api = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_SECRET,
    )

    try:
        room = await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                max_participants=max_participants,
                empty_timeout=300,        # auto-close after 5 min empty
            )
        )
        return {"name": room.name, "sid": room.sid}
    finally:
        await lk_api.aclose()
