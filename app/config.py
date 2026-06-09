import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required"
    )

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is required"
    )

# 100ms video conferencing configuration
HMS_APP_ACCESS_KEY = os.getenv("HMS_APP_ACCESS_KEY")
HMS_APP_SECRET = os.getenv("HMS_APP_SECRET")
HMS_SUBDOMAIN = os.getenv("HMS_SUBDOMAIN")   # e.g. "myapp" (from 100ms dashboard)
JITSI_DOMAIN = os.getenv("JITSI_DOMAIN", "https://meet.jit.si").rstrip("/")
JITSI_BASE_URL = os.getenv("JITSI_BASE_URL", JITSI_DOMAIN)
JITSI_APP_ID = os.getenv("JITSI_APP_ID")
JITSI_APP_SECRET = os.getenv("JITSI_APP_SECRET")
JITSI_JWT_ISSUER = os.getenv("JITSI_JWT_ISSUER", JITSI_APP_ID)
JITSI_JWT_AUDIENCE = os.getenv("JITSI_JWT_AUDIENCE", "jitsi")


def _default_jitsi_subject() -> str:
    parsed = urlparse(JITSI_BASE_URL)
    if parsed.hostname:
        return parsed.hostname
    parsed = urlparse(JITSI_DOMAIN)
    if parsed.hostname:
        return parsed.hostname
    return JITSI_DOMAIN


JITSI_JWT_SUBJECT = os.getenv("JITSI_JWT_SUBJECT", _default_jitsi_subject())
JITSI_TOKEN_TTL_MINUTES = int(os.getenv("JITSI_TOKEN_TTL_MINUTES", "120"))
