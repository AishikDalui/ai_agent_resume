# Local Development

## Purpose

Use this guide when running the project on your own machine.

## Main command

```bash
docker compose up --build
```

This uses [docker-compose.yml](/Users/oishikdalui/Desktop/ai_agent_resume/docker-compose.yml).

## Local URLs

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

## Local env file

Create a local env file:

```bash
cp .env.example .env
```

Fill in the provider values you actually want to use.

Recommended local values:

```env
APP_ENV=development
DEBUG=false
EXPOSE_DEBUG_OTPS=true
FRONTEND_ORIGIN=http://localhost:3000
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:5500
```

## Services started locally

- `frontend`
- `backend`
- `redis`
- `worker`

The default local compose file still uses SQLite for convenience.

## Typical local workflow

1. Update `.env`.
2. Run `docker compose up --build`.
3. Open `http://localhost:3000`.
4. Check `http://localhost:8000/health` if the frontend cannot connect.

## Common problems

### Frontend says it cannot connect to backend

Check:

- backend container is running
- `http://localhost:8000/health` loads
- browser is using `http://localhost:3000`
- old `backend_base_url` is not stuck in browser localStorage

If needed, hard refresh the page or clear local storage for `localhost:3000`.

### OTP does not arrive

If SMTP is not configured, local mode can still expose the OTP when:

```env
EXPOSE_DEBUG_OTPS=true
```

### Redis is down

Some auth runtime state falls back to in-memory behavior for local development, but you should still keep Redis running when possible because the worker depends on it.

## Useful commands

Start:

```bash
docker compose up --build
```

Stop:

```bash
docker compose down
```

View logs:

```bash
docker compose logs backend --tail=200
docker compose logs frontend --tail=100
```

Rebuild cleanly:

```bash
docker compose down
docker compose up --build
```
