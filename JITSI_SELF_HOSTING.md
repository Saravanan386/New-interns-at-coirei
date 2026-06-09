# Jitsi Self-Hosting

This project now generates signed Jitsi JWT links from the LMS backend so only authenticated LMS users can join a room.

## Local setup

1. Copy `.env.demo.example` to `.env.demo` and set strong secrets for `JWT_SECRET` and `JITSI_APP_SECRET`.
2. Start the full demo stack:
   ```bash
   docker compose --env-file .env.demo -f docker-compose.full-demo.yml up -d --build
   ```
3. Point the backend at the same base URL if you are not using the `.env.demo` file:
   ```env
   JITSI_BASE_URL=http://localhost:8080
   JITSI_DOMAIN=http://localhost:8080
   JITSI_APP_ID=lms-app
   JITSI_APP_SECRET=change-me
   JITSI_JWT_AUDIENCE=jitsi
   # This should be the hostname only, not the full URL.
   JITSI_JWT_SUBJECT=localhost
   ```

If you are demoing from another device on your LAN, replace `localhost` with the PC's LAN IP or a real domain in both `JITSI_BASE_URL` and `JITSI_JWT_SUBJECT`.

## How access works

- `/sessions/start` issues a moderator link for the instructor.
- `/sessions/active` and `/sessions/{session_id}/access` generate fresh room-specific JWT links for the authenticated caller.
- The Jitsi deployment is configured with JWT auth and guest access disabled.

## Notes

- The compose file exposes Jitsi through Nginx on `http://localhost:8080`.
- The backend API is on `http://localhost:8000`.
- For production, add TLS and update `JITSI_BASE_URL` to your real domain.
