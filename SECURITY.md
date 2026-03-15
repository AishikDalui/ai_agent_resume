# Security Policy

## Supported setup

This project is intended to be run with:

- local development using [docker-compose.yml](/Users/oishikdalui/Desktop/ai_agent_resume/docker-compose.yml)
- VPS production using [docker-compose.prod.yml](/Users/oishikdalui/Desktop/ai_agent_resume/docker-compose.prod.yml)

## Reporting a vulnerability

Please do not open a public GitHub issue for sensitive security problems.

Report security issues privately to:

- Email: `replace-this-with-your-security-email@example.com`

When reporting, include:

- affected endpoint or file
- steps to reproduce
- expected vs actual behavior
- screenshots or logs if relevant

## Security expectations for contributors

- Never commit `.env` files.
- Never commit service-account JSON credentials.
- Never commit live API keys, SMTP passwords, JWT secrets, or provider tokens.
- Keep production values out of source control.
- Use `.env.example` as the public reference file.

## Current protections in the project

- CORS is controlled through environment variables in [backend/config.py](/Users/oishikdalui/Desktop/ai_agent_resume/backend/config.py).
- OTP debug exposure can be disabled with `EXPOSE_DEBUG_OTPS=false`.
- OTP and admin login flows are rate-limited in [backend/main.py](/Users/oishikdalui/Desktop/ai_agent_resume/backend/main.py).
- OTP storage uses Redis when available, with local fallback for development.
- Secrets and local runtime files are ignored by git in [.gitignore](/Users/oishikdalui/Desktop/ai_agent_resume/.gitignore).

## Before making the repository public

1. Rotate any secrets that may have been used in local `.env` files.
2. Rotate any provider credentials that may have been copied into screenshots, logs, or previous commits.
3. Confirm `APP_ENV=production` and `EXPOSE_DEBUG_OTPS=false` in production.
4. Confirm `CORS_ALLOW_ORIGINS` only includes trusted frontend origins.
5. Confirm admin credentials are strong and unique.
6. Confirm the Google service-account JSON file is only stored on the server, not in git.

## Operational recommendations

- Use HTTPS in staging and production.
- Restrict public ports to only what is necessary.
- Keep Redis and Postgres private to the Docker network in production.
- Review logs for repeated OTP or admin login attempts.
- Back up Postgres before major upgrades.

## Out of scope

The following are deployment responsibilities rather than source-code guarantees:

- VPS firewall configuration
- domain and DNS ownership
- TLS certificate renewal
- operating system patching
- Docker daemon hardening
