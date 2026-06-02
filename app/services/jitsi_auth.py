# app/services/jitsi_auth.py

import secrets


def generate_room_name(classroom_id: int):

    return (
        f"classroom_"
        f"{classroom_id}_"
        f"{secrets.token_urlsafe(16)}"
    )







































# # app/services/jitsi_auth.py

# import jwt
# from datetime import datetime, timedelta

# from app.config import (
#     JITSI_APP_ID,
#     JITSI_APP_SECRET,
#     JITSI_DOMAIN
# )

# def create_jitsi_token(
#     room_name: str,
#     user_id: int,
#     user_name: str,
#     role: str
# ):

#     payload = {

#         "aud": "jitsi",

#         "iss": JITSI_APP_ID,

#         "sub": JITSI_DOMAIN,

#         "room": room_name,

#         "exp": datetime.utcnow() + timedelta(hours=2),

#         "context": {
#             "user": {
#                 "id": str(user_id),
#                 "name": user_name,
#                 "moderator": role == "instructor"
#             }
#         }
#     }

#     token = jwt.encode(
#         payload,
#         JITSI_APP_SECRET,
#         algorithm="HS256"
#     )

#     return token