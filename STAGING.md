# Staging Guide

## Purpose

Staging is the environment where you test changes before production.

Recommended branch:

- `develop`

Recommended domain:

- `staging.yourdomain.com`

## Server layout

Recommended VPS folder:

- `/opt/ai_agent_resume_staging`

Recommended deployment model:

- Docker Compose with [docker-compose.prod.yml](/Users/oishikdalui/Desktop/ai_agent_resume/docker-compose.prod.yml)
- Nginx reverse proxy
- HTTPS enabled

## First-time setup

```bash
cd /opt
git clone <your-github-repo-url> ai_agent_resume_staging
cd /opt/ai_agent_resume_staging
git checkout develop
cp .env.example .env
nano .env
docker compose -f docker-compose.prod.yml up -d --build
```

## Recommended staging env values

```env
APP_ENV=production
DEBUG=false
EXPOSE_DEBUG_OTPS=false
FRONTEND_ORIGIN=https://staging.yourdomain.com
CORS_ALLOW_ORIGINS=https://staging.yourdomain.com
PUBLIC_BACKEND_URL=https://staging.yourdomain.com/api
```

Use separate values from production for:

- admin credentials
- JWT secret
- Postgres password
- provider accounts if possible

## What to test in staging

- frontend loads
- backend health endpoint works
- admin login works
- public content loads
- OTP request and verify flow works
- booking flow works
- resume upload works
- worker-driven tasks run correctly

## Deploying staging manually

```bash
cd /opt/ai_agent_resume_staging
git checkout develop
git pull origin develop
docker compose -f docker-compose.prod.yml up -d --build
```

## Deploying staging with GitHub Actions

If using the included workflow:

- pushes to `develop` deploy staging automatically

See [GITHUB_ACTIONS_HOSTINGER.md](/Users/oishikdalui/Desktop/ai_agent_resume/GITHUB_ACTIONS_HOSTINGER.md).
