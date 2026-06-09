# Demo Quickstart

## 1. Prepare env

Copy `.env.demo.example` to `.env.demo` and replace the secret values:

- `JWT_SECRET`
- `JITSI_APP_SECRET`

You can keep the demo login credentials as-is:

- Instructor: `instructor@demo.com` / `Demo@12345`
- Student: `student@demo.com` / `Demo@12345`

## 2. Start everything

```bash
docker compose --env-file .env.demo -f docker-compose.full-demo.yml up -d --build
```

## 3. Open the app

- Backend health: `http://localhost:8001/health`
- Backend API docs: `http://localhost:8001/docs`
- Jitsi web: `http://localhost:8081`

## 4. Demo flow

- Log in as instructor.
- Start a session from `/sessions/start`.
- Log in as student.
- Join the same session from `/sessions/join` or `/sessions/active`.

## 5. Stop

```bash
docker compose --env-file .env.demo -f docker-compose.full-demo.yml down
```
