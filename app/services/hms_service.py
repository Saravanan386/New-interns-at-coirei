# app/services/hms_service.py
"""
100ms helper service.
Provides management token generation, auth token generation,
and room creation for class sessions.
"""

import uuid
import httpx
import jwt as pyjwt
from datetime import datetime, timezone, timedelta

from app.config import HMS_APP_ACCESS_KEY, HMS_APP_SECRET, HMS_SUBDOMAIN


# ---------------------------------------------------------------------------
# MANAGEMENT TOKEN  (used only for server-side 100ms API calls)
# ---------------------------------------------------------------------------
def generate_management_token() -> str:
    """Short-lived JWT for calling 100ms REST API (not given to users)."""
    now = datetime.now(timezone.utc)
    payload = {
        "access_key": HMS_APP_ACCESS_KEY,
        "type": "management",
        "version": 2,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=10),
        "jti": str(uuid.uuid4()),
    }
    return pyjwt.encode(payload, HMS_APP_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# AUTH TOKEN  (given to participants to join a room)
# ---------------------------------------------------------------------------
def generate_auth_token(
    room_id: str,
    user_id: int,
    user_name: str,
    role: str = "guest",
) -> str:
    """
    Generate a signed auth token for a 100ms participant.
    role must match an exact role name in your 100ms template.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "access_key": HMS_APP_ACCESS_KEY,
        "room_id": room_id,
        "user_id": str(user_id),
        "role": role,
        "type": "app",
        "version": 2,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(hours=6),
        "jti": str(uuid.uuid4()),
    }
    return pyjwt.encode(payload, HMS_APP_SECRET, algorithm="HS256")


def _is_host_role(role_name: str) -> bool:
    """Fuzzy match: is this a host/instructor role?"""
    r = role_name.lower()
    return any(k in r for k in ("host", "instructor", "admin", "backstage", "broadcaster"))


def _build_join_url(code: str) -> str:
    """
    Build a join URL from a room code.
    Uses prebuilt UI subdomain if set, otherwise uses the universal 100ms link.
    """
    if HMS_SUBDOMAIN:
        return f"https://{HMS_SUBDOMAIN}.app.100ms.live/meeting/{code}"
    return f"https://app.100ms.live/preview/{code}"


# ---------------------------------------------------------------------------
# CREATE ROOM  (called once when instructor starts a session)
# ---------------------------------------------------------------------------
async def create_room(room_name: str) -> dict:
    """
    Creates a 100ms room and fetches role-based room codes.
    Auto-detects which code belongs to the host and which to the guest.
    Returns:
        {
            "room_id": str,
            "host_url": str,     # for instructor
            "guest_url": str,    # for students
            "host_role": str,    # actual role name in your template
            "guest_role": str,
        }
    """
    mgmt_token = generate_management_token()
    headers = {
        "Authorization": f"Bearer {mgmt_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:

        # 1 - Create the room
        room_resp = await client.post(
            "https://api.100ms.live/v2/rooms",
            json={
                "name": room_name,
                "description": f"LMS class: {room_name}",
            },
            headers=headers,
        )
        room_resp.raise_for_status()
        room_data = room_resp.json()
        room_id = room_data["id"]

        # 2 - Enable room codes for this room
        await client.post(
            f"https://api.100ms.live/v2/room-codes/room/{room_id}",
            headers=headers,
        )

        # 3 - Fetch room codes (one per role in your template)
        codes_resp = await client.get(
            f"https://api.100ms.live/v2/room-codes/room/{room_id}",
            headers=headers,
        )
        codes_resp.raise_for_status()
        codes_data = codes_resp.json()

    all_codes = codes_data.get("data", [])

    if not all_codes:
        raise ValueError(
            "No room codes returned from 100ms. "
            "Make sure your template has at least one role defined."
        )

    # Auto-detect host vs guest by fuzzy role name matching
    host_entry = None
    guest_entry = None

    for entry in all_codes:
        if _is_host_role(entry.get("role", "")):
            host_entry = entry
        else:
            guest_entry = entry

    # Fallback: use first code as host if no match found
    if host_entry is None:
        host_entry = all_codes[0]
    if guest_entry is None:
        guest_entry = next(
            (c for c in all_codes if c["code"] != host_entry["code"]),
            host_entry   # single-role template fallback
        )

    return {
        "room_id": room_id,
        "host_url": _build_join_url(host_entry["code"]),
        "guest_url": _build_join_url(guest_entry["code"]),
        "host_role": host_entry.get("role"),
        "guest_role": guest_entry.get("role"),
    }
