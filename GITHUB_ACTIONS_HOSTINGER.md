# GitHub Actions Setup For Hostinger VPS

This project now includes:

- [pr-check.yml](/Users/oishikdalui/Desktop/ai_agent_resume/.github/workflows/pr-check.yml) for pull request build checks
- [deploy.yml](/Users/oishikdalui/Desktop/ai_agent_resume/.github/workflows/deploy.yml) for branch-based VPS deployment

## Branch flow

- `develop` = staging
- `main` = production

Recommended flow:

1. Create a feature branch from `develop`.
2. Open a PR into `develop`.
3. GitHub runs the PR checks.
4. Merge to `develop` to deploy staging automatically.
5. Test on staging.
6. Open a PR from `develop` into `main`.
7. Merge to `main` to deploy production automatically.

## GitHub secrets to add

Go to GitHub repository settings, then `Secrets and variables` -> `Actions`.

### Staging secrets

- `STAGING_HOST`
- `STAGING_PORT`
- `STAGING_USER`
- `STAGING_SSH_KEY`
- `STAGING_APP_PATH`

### Production secrets

- `PRODUCTION_HOST`
- `PRODUCTION_PORT`
- `PRODUCTION_USER`
- `PRODUCTION_SSH_KEY`
- `PRODUCTION_APP_PATH`

## Example values

Staging example:

- `STAGING_HOST=your_server_ip`
- `STAGING_PORT=22`
- `STAGING_USER=root`
- `STAGING_APP_PATH=/opt/ai_agent_resume_staging`

Production example:

- `PRODUCTION_HOST=your_server_ip`
- `PRODUCTION_PORT=22`
- `PRODUCTION_USER=root`
- `PRODUCTION_APP_PATH=/opt/ai_agent_resume`

## VPS folder strategy

Use two separate copies of the app on the VPS:

- `/opt/ai_agent_resume_staging`
- `/opt/ai_agent_resume`

Each folder should have its own `.env`.

That lets you keep staging and production isolated even on one server.

## First-time VPS prep

For staging:

```bash
cd /opt
git clone <your-github-repo-url> ai_agent_resume_staging
cd /opt/ai_agent_resume_staging
git checkout develop
cp .env.example .env
nano .env
docker compose -f docker-compose.prod.yml up -d --build
```

For production:

```bash
cd /opt
git clone <your-github-repo-url> ai_agent_resume
cd /opt/ai_agent_resume
git checkout main
cp .env.example .env
nano .env
docker compose -f docker-compose.prod.yml up -d --build
```

## Important notes

- Keep staging and production on different domains or subdomains.
- Keep different `.env` values in each folder.
- Do not store `.env` in GitHub secrets unless you really want env-file generation inside CI.
- The workflow assumes Docker and Git are already installed on the VPS.
- The workflow also assumes the repository is already cloned once on the server.
