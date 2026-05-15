# app/routers/ws_chat.py
"""
WebSocket Real-Time Chat Events
================================
Endpoints:
  WS /ws/chat/{conversation_id}   → Real-time DM events (messages, typing, read receipts)
  WS /ws/chat/group/{group_id}    → Real-time group chat events
  WS /ws/qa/{course_id}           → Real-time Q&A events (new questions, pin, answer)

Message format (JSON):
  Client → Server:
    { "type": "message", "text": "...", "attachment_url": null }
    { "type": "typing" }
    { "type": "read" }
    { "type": "ping" }

  Server → Client:
    { "type": "message", "data": { ...message object } }
    { "type": "typing", "user_id": 123, "user_name": "..." }
    { "type": "read", "user_id": 123 }
    { "type": "pin", "message_id": 456, "is_pinned": true }
    { "type": "delete", "message_id": 456 }
    { "type": "connected", "message": "..." }
    { "type": "error", "detail": "..." }
    { "type": "pong" }
"""

import json
from typing import Dict, Set, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from starlette.websockets import WebSocketState

router = APIRouter(tags=["Real-Time WebSocket"])


# ── In-Memory Connection Manager ──────────────────────────────────────────────

class ConnectionManager:
    """
    Simple in-memory manager for WebSocket connections.
    Groups connections by a 'room' key (conversation_id, group_id, or course_id).
    """

    def __init__(self):
        # room_key -> set of (user_id, WebSocket)
        self.rooms: Dict[str, List[tuple]] = {}

    def _ensure_room(self, room: str):
        if room not in self.rooms:
            self.rooms[room] = []

    async def connect(self, room: str, user_id: int, ws: WebSocket):
        await ws.accept()
        self._ensure_room(room)
        self.rooms[room].append((user_id, ws))

    def disconnect(self, room: str, user_id: int, ws: WebSocket):
        if room in self.rooms:
            self.rooms[room] = [
                (uid, w) for uid, w in self.rooms[room]
                if not (uid == user_id and w is ws)
            ]

    async def broadcast(self, room: str, payload: dict, exclude_user_id: int = None):
        """Broadcast a message to all connections in a room."""
        if room not in self.rooms:
            return
        dead = []
        for user_id, ws in self.rooms[room]:
            if exclude_user_id and user_id == exclude_user_id:
                continue
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(payload)
            except Exception:
                dead.append((user_id, ws))
        # Remove dead connections
        for item in dead:
            if item in self.rooms[room]:
                self.rooms[room].remove(item)

    async def send_personal(self, ws: WebSocket, payload: dict):
        try:
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.send_json(payload)
        except Exception:
            pass

    def member_count(self, room: str) -> int:
        return len(self.rooms.get(room, []))


manager = ConnectionManager()


# ── Token extraction (query param) ───────────────────────────────────────────

def _decode_token(token: str) -> dict:
    """Decode JWT token from query param. Returns user payload or raises."""
    from app.utils.security import JWT_SECRET, JWT_ALGORITHM
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return {}


# ── WS /ws/chat/{conversation_id} ────────────────────────────────────────────

@router.websocket("/ws/chat/{conversation_id}")
async def ws_dm_chat(
    websocket: WebSocket,
    conversation_id: int,
    token: str = Query(...)
):
    """
    WebSocket for 1-to-1 DM real-time events.
    Connect with: ws://host/ws/chat/{conversation_id}?token=<JWT>
    Supports: message, typing indicator, read receipt
    """
    payload = _decode_token(token)
    if not payload:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    user_id = payload.get("user_id") or payload.get("sub")
    user_name = payload.get("name", "User")
    room = f"dm:{conversation_id}"

    await manager.connect(room, user_id, websocket)
    await manager.send_personal(websocket, {
        "type": "connected",
        "message": f"Connected to conversation {conversation_id}",
        "online_count": manager.member_count(room)
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {"type": "error", "detail": "Invalid JSON"})
                continue

            event_type = data.get("type")

            if event_type == "ping":
                await manager.send_personal(websocket, {"type": "pong"})

            elif event_type == "typing":
                await manager.broadcast(room, {
                    "type": "typing",
                    "user_id": user_id,
                    "user_name": user_name,
                    "conversation_id": conversation_id,
                }, exclude_user_id=user_id)

            elif event_type == "read":
                await manager.broadcast(room, {
                    "type": "read",
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                }, exclude_user_id=user_id)

            elif event_type == "message":
                # Notify other party of the new message (REST API handles DB write)
                await manager.broadcast(room, {
                    "type": "new_message",
                    "conversation_id": conversation_id,
                    "sender_id": user_id,
                    "sender_name": user_name,
                    "text": data.get("text"),
                    "attachment_url": data.get("attachment_url"),
                }, exclude_user_id=user_id)

    except WebSocketDisconnect:
        manager.disconnect(room, user_id, websocket)
        await manager.broadcast(room, {
            "type": "user_offline",
            "user_id": user_id,
            "conversation_id": conversation_id,
        })


# ── WS /ws/chat/group/{group_id} ─────────────────────────────────────────────

@router.websocket("/ws/chat/group/{group_id}")
async def ws_group_chat(
    websocket: WebSocket,
    group_id: int,
    token: str = Query(...)
):
    """
    WebSocket for group/batch chat real-time events.
    Connect with: ws://host/ws/chat/group/{group_id}?token=<JWT>
    Supports: message, typing indicator, online member count, pin
    """
    payload = _decode_token(token)
    if not payload:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    user_id = payload.get("user_id") or payload.get("sub")
    user_name = payload.get("name", "User")
    room = f"group:{group_id}"

    await manager.connect(room, user_id, websocket)
    online_count = manager.member_count(room)

    # Notify all that a new user joined
    await manager.broadcast(room, {
        "type": "user_joined",
        "user_id": user_id,
        "user_name": user_name,
        "online_count": online_count,
    }, exclude_user_id=user_id)

    await manager.send_personal(websocket, {
        "type": "connected",
        "message": f"Connected to group {group_id}",
        "online_count": online_count
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {"type": "error", "detail": "Invalid JSON"})
                continue

            event_type = data.get("type")

            if event_type == "ping":
                await manager.send_personal(websocket, {"type": "pong"})

            elif event_type == "typing":
                await manager.broadcast(room, {
                    "type": "typing",
                    "user_id": user_id,
                    "user_name": user_name,
                    "group_id": group_id,
                }, exclude_user_id=user_id)

            elif event_type == "message":
                await manager.broadcast(room, {
                    "type": "new_message",
                    "group_id": group_id,
                    "sender_id": user_id,
                    "sender_name": user_name,
                    "text": data.get("text"),
                    "attachment_url": data.get("attachment_url"),
                })

            elif event_type == "pin":
                # Instructor can notify everyone of a pin via WS
                await manager.broadcast(room, {
                    "type": "pin",
                    "message_id": data.get("message_id"),
                    "is_pinned": data.get("is_pinned", True),
                    "pinned_by": user_name,
                    "group_id": group_id,
                })

            elif event_type == "delete":
                await manager.broadcast(room, {
                    "type": "delete",
                    "message_id": data.get("message_id"),
                    "group_id": group_id,
                })

    except WebSocketDisconnect:
        manager.disconnect(room, user_id, websocket)
        online_count = manager.member_count(room)
        await manager.broadcast(room, {
            "type": "user_left",
            "user_id": user_id,
            "user_name": user_name,
            "online_count": online_count,
            "group_id": group_id,
        })


# ── WS /ws/qa/{course_id} ────────────────────────────────────────────────────

@router.websocket("/ws/qa/{course_id}")
async def ws_qa(
    websocket: WebSocket,
    course_id: int,
    token: str = Query(...)
):
    """
    WebSocket for live Q&A updates.
    Events: new_question, new_answer, pin_update, delete_question
    Connect with: ws://host/ws/qa/{course_id}?token=<JWT>
    """
    payload = _decode_token(token)
    if not payload:
        await websocket.close(code=4401, reason="Unauthorized")
        return

    user_id = payload.get("user_id") or payload.get("sub")
    room = f"qa:{course_id}"

    await manager.connect(room, user_id, websocket)
    await manager.send_personal(websocket, {
        "type": "connected",
        "message": f"Connected to Q&A for course {course_id}"
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {"type": "error", "detail": "Invalid JSON"})
                continue

            event_type = data.get("type")

            if event_type == "ping":
                await manager.send_personal(websocket, {"type": "pong"})

            elif event_type in ("new_question", "new_answer", "pin_update", "delete_question"):
                # Broadcast Q&A events to all course subscribers
                await manager.broadcast(room, {
                    "type": event_type,
                    "course_id": course_id,
                    "sender_id": user_id,
                    "data": data.get("data", {}),
                })

    except WebSocketDisconnect:
        manager.disconnect(room, user_id, websocket)
