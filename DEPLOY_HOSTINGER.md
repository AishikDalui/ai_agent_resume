# Hostinger VPS Deployment Guide

## 1. Before GitHub

- Copy `.env.example` to `.env`.
- Put real secrets only in `.env`.
- Keep service-account JSON files outside git. This repo now ignores them.
- Set production values before deployment:
  - `APP_ENV=production`
  - `EXPOSE_DEBUG_OTPS=false`
  - `CORS_ALLOW_ORIGINS=https://yourdomain.com,https://www.yourdomain.com`
  - `PUBLIC_BACKEND_URL=https://yourdomain.com/api`
  - `POSTGRES_PASSWORD=...strong-password...`
  - `DATABASE_URL` is handled by `docker-compose.prod.yml`

## 2. Push to GitHub

```bash
git init
git add .
git commit -m "Prepare app for production deployment"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

If this project was already pushed earlier with real secrets, rotate them before going live.

## 3. Prepare the VPS

Connect to the VPS:

```bash
ssh root@your-server-ip
```

Install Docker, Compose plugin, Nginx, Certbot, and Git:

```bash
apt update
apt install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx git
systemctl enable docker
systemctl start docker
```

## 4. Clone the project on the VPS

```bash
cd /opt
git clone <your-github-repo-url> ai_agent_resume
cd /opt/ai_agent_resume
```

Create your production env file:

```bash
cp .env.example .env
nano .env
```

Recommended production values:

```env
APP_ENV=production
DEBUG=false
EXPOSE_DEBUG_OTPS=false
JWT_SECRET_KEY=replace_with_a_long_random_value
FRONTEND_ORIGIN=https://yourdomain.com
CORS_ALLOW_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
PUBLIC_BACKEND_URL=https://yourdomain.com/api
ADMIN_EMAIL=you@example.com
ADMIN_PASSWORD=replace_with_a_strong_password
POSTGRES_DB=ai_agent_resume
POSTGRES_USER=ai_agent_resume
POSTGRES_PASSWORD=replace_with_a_strong_password
```

Also set the rest of your real provider secrets:

- `GEMINI_API_KEY`
- `GEMINI_API_KEY2`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `SMTP_*`
- `IMAGEKIT_*`
- `VOBIZ_*`

For the Google service account file, place it on the server, for example:

```bash
mkdir -p /opt/ai_agent_resume/backend/credentials
nano /opt/ai_agent_resume/backend/credentials/service_account.json
```

Then set:

```env
GOOGLE_SERVICE_ACCOUNT_JSON=./backend/credentials/service_account.json
```

## 5. Start the app

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check status:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend --tail=100
```

## 6. Configure Nginx

Copy the sample config:

```bash
cp deploy/nginx/ai-agent-resume.conf /etc/nginx/sites-available/ai-agent-resume
```

Edit the domain names:

```bash
nano /etc/nginx/sites-available/ai-agent-resume
```

Enable the site:

```bash
ln -s /etc/nginx/sites-available/ai-agent-resume /etc/nginx/sites-enabled/ai-agent-resume
nginx -t
systemctl reload nginx
```

## 7. Enable HTTPS

Point your domain DNS to the VPS IP first, then run:

```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 8. Update workflow

Local development:

```bash
docker compose up --build
```

Production deploy after changes:

```bash
git add .
git commit -m "Your change"
git push origin main
ssh root@your-server-ip
cd /opt/ai_agent_resume
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

## 9. Recommended next improvement

After the first manual deploy is stable, add GitHub Actions for:

- build checks on push
- optional VPS auto-deploy on `main`
