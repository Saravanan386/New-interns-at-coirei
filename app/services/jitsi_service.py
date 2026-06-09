from app.services.jitsi_auth import (
    build_meeting_url,
    generate_room_name,
)


def create_room(room_name: str):
    # Generic instructor/student links for the session start response.
    host_url = build_meeting_url(
        room_name=room_name,
        user_id=0,
        user_name="Instructor",
        role="instructor",
    )
    guest_url = build_meeting_url(
        room_name=room_name,
        user_id=0,
        user_name="Student",
        role="student",
    )

    return {
        "room_id": room_name,
        "host_url": host_url,
        "guest_url": guest_url,
    }

