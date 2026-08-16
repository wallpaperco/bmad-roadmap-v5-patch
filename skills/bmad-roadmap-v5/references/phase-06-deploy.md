# Phase 6 — Deploy

**Goal:** Ship the built app to production. For Abozaid personal projects, this means deploying to the DigitalOcean Droplet (see global CLAUDE.md `# DigitalOcean Server (Personal)`). For Nozom projects, deploy to the Kubernetes cluster via GitLab CI.

**Exit:** production URL returns 200 + every journey walkable end-to-end.

---

## Steps (DigitalOcean personal — adapt for Nozom k8s)

1. **Server setup**
   ```bash
   ssh root@64.226.92.112
   mkdir -p /opt/apps/{project-name}
   cd /opt/apps/{project-name}
   git clone git@github.com:wallpaperco/{project-repo}.git .
   ```

2. **Caddy reverse proxy** — add domain to `/opt/caddy/Caddyfile`:
   ```
   {domain} {
       reverse_proxy {project}-nginx:80
   }
   ```
   Then `docker compose -f /opt/caddy/docker-compose.yml restart caddy`.

3. **Production Docker setup** — create the following from the v5 build:
   - `docker-compose.prod.yml` — production services (api, web, nginx, db; container names prefixed with project name)
   - `docker/php/Dockerfile.prod` or `docker/api/Dockerfile.prod` — multi-stage backend build, target <200MB
   - `docker/web/Dockerfile.prod` — multi-stage Next.js build with `NEXT_PUBLIC_*` build args
   - `docker/nginx/prod.conf` — nginx routing (`/api/v1/*` → backend, `/*` → frontend)

4. **GitHub Actions deploy pipeline** — `.github/workflows/deploy.yml`:
   - PR to main: checks only (typecheck + lint + tests)
   - Push to main: check → build (Docker matrix to GHCR) → deploy (SSH) → notify (Telegram)
   - Required secrets at repo or org level: `SERVER_IP`, `SSH_PRIVATE_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - Required variable: `SITE_URL`

5. **Docker proxy network** — join the existing `proxy` external network on the droplet so Caddy can reach the new nginx.

6. **DNS** — point the domain's A record to `64.226.92.112`. Wait ~5min for propagation.

7. **First deploy** — push to main, watch CI, verify Telegram notification. SSH to droplet, run:
   ```bash
   curl -fsS https://{domain}/api/v1/health   # expect 200 with DB + Redis status
   curl -fsS https://{domain}/                # expect 200, Next.js HTML
   ```

8. **Smoke-test every journey** — walk through the user journeys from UX spec §13 manually. Note any production-only bugs (env-var typos, secret misconfiguration).

9. **Update global CLAUDE.md `# Deployed Apps` table** — add the new project:
   | App | Domain | Server Path | GitHub Repo | GHCR Prefix |
   |---|---|---|---|---|
   | {project} | {domain} | /opt/apps/{project}/ | wallpaperco/{repo} | ghcr.io/wallpaperco/{repo}/ |

---

## Phase exit checklist

- [ ] Production URL returns 200
- [ ] `/api/v1/health` returns 200 with DB + Redis healthy
- [ ] Every journey walked end-to-end on production
- [ ] Caddy SSL active (Let's Encrypt cert issued)
- [ ] Telegram CI notifications delivered
- [ ] Global CLAUDE.md `# Deployed Apps` table updated

On exit, update `roadmap-progress.yaml`:
```yaml
6-deploy:
  status: complete
  completed: "{today}"
  prod_url: "https://{domain}"
```

Advance to Phase 7.
