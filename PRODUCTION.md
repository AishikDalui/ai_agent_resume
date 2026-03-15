# Production Guide

## Purpose

Production is the live environment used by real visitors.

Recommended branch:

- `main`

Recommended domain:

- `yourdomain.com`
- `www.yourdomain.com`

## Server layout

Recommended VPS folder:

- `/opt/ai_agent_resume`

Recommended deployment model:

- Docker Compose with [docker-compose.prod.yml](/Users/oishikdalui/Desktop/ai_agent_resume/docker-compose.prod.yml)
- Nginx reverse proxy
- HTTPS enabled

## First-time setup

```bash
cd /opt
git clone <your-github-repo-url> ai_agent_resume
cd /opt/ai_agent_resume
git checkout main
cp .env.example .env
nano .env
docker compose -f docker-compose.prod.yml up -d --build
```

## Recommended production env values

```env
APP_ENV=production
DEBUG=false
EXPOSE_DEBUG_OTPS=false
FRONTEND_ORIGIN=https://yourdomain.com
CORS_ALLOW_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
PUBLIC_BACKEND_URL=https://yourdomain.com/api
```

Also set strong and unique values for:

- `JWT_SECRET_KEY`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `POSTGRES_PASSWORD`
- provider API keys and tokens

## Production safety checks

- backend health endpoint responds
- Nginx routes `/` to frontend
- Nginx routes `/api/` to backend
- HTTPS is valid
- Redis and Postgres are private
- OTP debug output is disabled
- admin login works
- logs do not expose secrets

## Deploying production manually

```bash
cd /opt/ai_agent_resume
git checkout main
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

## Deploying production with GitHub Actions

If using the included workflow:

- pushes to `main` deploy production automatically

See [GITHUB_ACTIONS_HOSTINGER.md](/Users/oishikdalui/Desktop/ai_agent_resume/GITHUB_ACTIONS_HOSTINGER.md).

## Ongoing maintenance

- renew and verify TLS certificates
- monitor disk space for Docker images and Postgres data
- back up Postgres regularly
- rotate secrets if exposure is suspected
- review logs for repeated failed auth attempts
