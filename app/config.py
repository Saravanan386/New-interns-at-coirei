import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

# 100ms video conferencing configuration
HMS_APP_ACCESS_KEY = os.getenv("HMS_APP_ACCESS_KEY")
HMS_APP_SECRET = os.getenv("HMS_APP_SECRET")
HMS_SUBDOMAIN = os.getenv("HMS_SUBDOMAIN")   # e.g. "myapp" (from 100ms dashboard)
JITSI_DOMAIN = os.getenv("JITSI_DOMAIN")


JITSI_BASE_URL = os.getenv("JITSI_BASE_URL", "https://10.97.42.239")
JITSI_APP_ID = os.getenv("JITSI_APP_ID", "lms-app")
JITSI_APP_SECRET = os.getenv("JITSI_APP_SECRET", "my_super_secret_key")
JITSI_JWT_AUDIENCE = os.getenv("JITSI_JWT_AUDIENCE", "jitsi")
JITSI_JWT_SUBJECT = os.getenv("JITSI_JWT_SUBJECT", "10.97.42.239")