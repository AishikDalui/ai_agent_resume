# Open Source Checklist

Use this checklist before making the repository public.

## Secrets and credentials

- [ ] `.env` is not committed.
- [ ] No live API keys remain in tracked files.
- [ ] No service-account JSON file is tracked in git.
- [ ] All previously used secrets have been rotated if there is any chance they were exposed.
- [ ] `.env.example` contains placeholders only.

## Production safety

- [ ] `APP_ENV=production` is used on live systems.
- [ ] `EXPOSE_DEBUG_OTPS=false` is used on live systems.
- [ ] `JWT_SECRET_KEY` is long and unique in production.
- [ ] `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set only in server env files.
- [ ] `CORS_ALLOW_ORIGINS` contains only trusted frontend domains in production.

## Deployment hygiene

- [ ] Local development uses [docker-compose.yml](/Users/oishikdalui/Desktop/ai_agent_resume/docker-compose.yml).
- [ ] VPS production uses [docker-compose.prod.yml](/Users/oishikdalui/Desktop/ai_agent_resume/docker-compose.prod.yml).
- [ ] Nginx config is reviewed before production use.
- [ ] Redis and Postgres are not exposed publicly in production.

## Repository hygiene

- [ ] README instructions do not leak secrets or private infrastructure details.
- [ ] Old sample files or uploads are removed if they should not be public.
- [ ] Demo screenshots and videos do not expose credentials or personal data.
- [ ] CI/CD secrets exist only in GitHub Actions secrets, not in workflow files.

## Functional checks

- [ ] Frontend builds successfully.
- [ ] Backend starts successfully.
- [ ] `http://localhost:8000/health` works locally.
- [ ] OTP request and verify flows work locally.
- [ ] Admin login works with env-configured credentials.
- [ ] Production deploy docs are up to date.

## Nice-to-have before publishing

- [ ] Add screenshots and setup notes to README.
- [ ] Add a license file.
- [ ] Add `SECURITY.md`.
- [ ] Add local, staging, and production docs.
- [ ] Add automated tests for auth and booking flows.
