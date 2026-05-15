import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

# 100ms video conferencing configuration
HMS_APP_ACCESS_KEY = os.getenv("HMS_APP_ACCESS_KEY")
HMS_APP_SECRET = os.getenv("HMS_APP_SECRET")
HMS_SUBDOMAIN = os.getenv("HMS_SUBDOMAIN")   # e.g. "myapp" (from 100ms dashboard)
