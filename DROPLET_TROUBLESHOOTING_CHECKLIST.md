# DROPLET TROUBLESHOOTING CHECKLIST

### Starting and Troubleshooting AgentGuard on DigitalOcean Droplet

- **System Startup Sequence**: Begin with Docker Compose to launch all services simultaneously, ensuring dependencies like PostgreSQL and Redis are ready before FastAPI and Next.js; monitor with `docker compose logs` for immediate feedback.
- **Core Troubleshooting Principles**: Always check logs first (e.g., Docker, Nginx, application-specific); verify network connectivity and ports; restart services incrementally; use tools like `netstat` or `ufw status` for firewall issues.
- **Payment and Auth Focus**: For Stripe and Clerk, test in sandbox mode to avoid real transactions; common issues include webhook signature mismatches or auth middleware misconfigurations, resolved by validating environment variables.
- **Readiness Indicators**: The system is production-ready when all tests pass, including load simulations for 1000 users, with latency under 100ms and 99.9% uptime confirmed via monitoring dashboards.

#### Quick Startup Guide
Log into your Droplet via SSH. Navigate to the project directory and run `docker compose up -d --build` to start services. Access the frontend at `https://your_domain`, backend APIs at `https://your_domain/api`. For payments, trigger a test subscription via the pricing page; confirm webhook processing in logs.

#### Common Issues Overview
- **Docker/Compose**: Fails if ports conflict or volumes corrupt—clear volumes with `docker compose down -v` and rebuild.
- **Databases**: PostgreSQL may error on data directory changes in v18; Redis password mismatches block connections—verify configs.
- **Web Servers**: Nginx 502 errors often from upstream failures; Cloudflare 521 indicates origin connection issues—check firewalls.
- **Payments/Auth**: Stripe timeouts from local testing; Clerk errors from missing middleware—ensure routes are protected.

#### Pre-Launch Checklist
Verify environment variables in `.env`; run unit tests (`pytest` for backend, `npm test` for frontend); simulate traffic with Locust; enable monitoring alerts.

---

### In-Depth Guide to Operating and Resolving Issues in AgentGuard Deployment

This comprehensive survey provides a detailed, professional-level walkthrough for starting, monitoring, and troubleshooting the AgentGuard AI safety platform deployed on a DigitalOcean Droplet with Ubuntu 24.04 LTS. Built around Docker Compose for containerization, the system integrates FastAPI (backend), Next.js (frontend), PostgreSQL 18 (database), Redis 8.0.4 (caching), Nginx (reverse proxy), Cloudflare (security/CDN), Prometheus/Grafana/Sentry (monitoring), AWS S3 (backups), Stripe (payments), and Clerk (authentication/paywall). The guide draws from established best practices, emphasizing proactive logging, incremental restarts, and tool-specific diagnostics to achieve your 99.9% uptime SLA and <100ms latency goals. We'll cover startup procedures, common failure modes, resolution steps, and preventive measures for each component, ensuring the system is fully production-ready for your December 1, 2025 launch.

#### System-Wide Startup and Initial Verification
To start the entire system, ensure you're SSH'd into the Droplet as the deploy user (e.g., `ssh deployuser@your_droplet_ip`). Navigate to the project root (`cd agentguard`). The primary command is `docker compose up -d --build`, which builds images if needed and starts containers in detached mode. This launches backend (FastAPI on port 8000), frontend (Next.js on 3000), db (PostgreSQL on 5432), and redis (on 6379). Verify with `docker compose ps`—all services should show "Up" status. If not, check logs: `docker compose logs -f` for real-time output or `docker compose logs service_name` for specifics.

Post-startup, run migrations: `docker compose exec backend python scripts/init_workspace_db.py`. Test basic access: `curl https://your_domain/api/health` (expect 200 OK) for backend; browser load `https://your_domain` for frontend dashboards. For payments, use Stripe's test mode to simulate a subscription; for auth, sign up via Clerk and verify paywall restricts features.

Common system-wide issues include port conflicts (e.g., if another service binds 80/443—use `netstat -tulpn` to identify and kill processes) or insufficient resources (8GB RAM may strain under load—monitor with `htop` and scale Droplet if CPU >80%). Preventive: Set UFW rules (`sudo ufw allow 80,443,22`) and enable auto-restarts in `docker-compose.yml` with `restart: always`.

#### Docker Compose: Core Orchestration Layer
Startup: From the repo root, `docker compose up -d` starts all services. For rebuilds (e.g., code changes), add `--build`. To stop: `docker compose down` (add `-v` to remove volumes if corrupted).

Troubleshooting:
- **Build Failures**: Often from missing dependencies—ensure `requirements.txt` and `package.json` are up-to-date; check logs for pip/npm errors. Fix: `docker compose build --no-cache` to force fresh installs.
- **Container Exits Immediately**: Inspect logs (`docker logs container_id`); common causes include invalid env vars or dependency order—use `depends_on` in YAML.
- **Network Issues**: Services can't communicate—ensure they're on the same network (default in Compose); test with `docker compose exec backend ping db`.
- **Volume Problems**: Data loss or corruption—back up volumes regularly (`docker volume ls` and copy); for PostgreSQL v18 upgrades, note path changes from `/var/lib/postgresql/data` which can break mounts.

Preventive: Add healthchecks to `docker-compose.yml` (e.g., for backend: `healthcheck: { test: ["CMD", "curl", "-f", "http://localhost:8000/health"], interval: 30s }`); use `docker system prune` to clean up.

#### FastAPI Backend: AI Safety Core
Startup: Handled by Docker; manually test with `docker compose exec backend uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload` for dev.

Troubleshooting:
- **Reload Not Working**: In production, remove `--reload` to avoid performance hits; if code changes don't apply, rebuild image.
- **Dependency Errors**: ML models (e.g., Hugging Face) fail to load—check RAM (8GB min); use lighter images like `python:3.14-slim`.
- **API 404/500**: Misconfigured routes or env vars—verify `PYTHONPATH` and API keys; debug with `pdb` or logs.
- **Performance**: Latency >100ms—optimize with semantic caching; profile with Prometheus.

Preventive: Enable Sentry for error tracking; integrate health endpoints.

#### Next.js Frontend: User Interface and Dashboards
Startup: Docker handles; dev mode: `docker compose exec frontend npm run dev`.

Troubleshooting:
- **Build Failures**: Missing .next dir—ensure not in .gitignore; use `npm run build` manually.
- **No Response**: Hangs on access—check port binding (0.0.0.0); for v14, metadata changes may break—update next.config.js.
- **Data Fetch Errors**: SSR fails—ensure backend URL uses container names (e.g., `http://backend:8000`).
- **CORS Issues**: Add headers in FastAPI or Next.js config.

Preventive: Use Vercel for hybrid if scaling; monitor with Sentry.

#### PostgreSQL 18: Persistent Data Store
Startup: Docker auto-starts; connect: `docker compose exec db psql -U agentguard -d agentguard`.

Troubleshooting:
- **Connection Refused**: Wrong port/user—verify env; for v18, data path changes break volumes—recreate if upgraded.
- **Disk Full Errors**: Out-of-space corrupts—free space and restart.
- **Query Failures**: Migrations incomplete—rerun script.

Preventive: Enable persistence; backup daily.

#### Redis 8.0.4: Semantic Caching Layer
Startup: Docker; test: `docker compose exec redis redis-cli -a securepass ping` (expect PONG).

Troubleshooting:
- **Auth Errors**: Wrong password—update env and restart.
- **Connection Issues**: Bind to localhost only—use container name for internal access.
- **Persistence Failures**: RDB/AOF errors—check conf for `requirepass`.

Preventive: Monitor keys with Prometheus.

#### Nginx: Traffic Routing
Startup: `sudo systemctl start nginx`; reload config: `sudo nginx -s reload`.

Troubleshooting:
- **502 Bad Gateway**: Upstream down—check Docker services; proxy_pass misconfig.
- **Config Errors**: Test with `nginx -t`.
- **SSL Issues**: Certbot failures—renew manually.

Preventive: Log errors to file; rate-limit for OWASP compliance.

#### Monitoring: Prometheus, Grafana, Sentry
Startup: Start Prometheus (`./prometheus`), Grafana (`sudo systemctl start grafana-server`), Sentry via Docker.

Troubleshooting:
- **No Metrics**: Scrape config wrong—verify endpoints.
- **Grafana Login Fails**: Default admin/admin—change immediately.
- **Sentry Not Capturing**: SDK init wrong—test with manual errors.

Preventive: Import pre-built dashboards; set alerts for >65% cache hits.

#### AWS S3 Backups: Data Resilience
Startup: Schedule via crontab; manual: `./backup.sh`.

Troubleshooting:
- **Permission Denied**: IAM roles insufficient—add S3 full access.
- **Upload Failures**: Network issues—test with `s3cmd ls`.
- **Large Files**: Split if >5GB.

Preventive: Use versioning; test restores weekly.

#### Stripe Payments: Monetization Engine
Startup: Webhooks auto-handle; test endpoint: `curl -X POST https://your_domain/api/stripe/webhook -H "Stripe-Signature: valid_sig"`.

Troubleshooting:
- **Webhook Timeouts**: Local dev—use Stripe CLI for forwarding; prod: ensure public endpoint.
- **Signature Errors**: Mismatch—verify secret in env.
- **Payment Declines**: Test cards only; check dashboard for logs.

Preventive: Replay events in Stripe UI; secure with HMAC.

#### Clerk Authentication and Paywall: Access Control
Startup: Clerk auto-inits in Next.js; test signup/login.

Troubleshooting:
- **Auth Failures**: Middleware missing—add to `middleware.ts`; rate limits in v15—check IP quotas.
- **Paywall Bypasses**: Metadata sync fails—debug webhook updates.
- **OAuth Issues**: Provider misconfig—verify Clerk dashboard.

Preventive: Use Clerk's debug tools; test all tiers.

| Component | Startup Command | Common Error | Resolution | Prevention |
|-----------|-----------------|--------------|------------|------------|
| Docker Compose | `docker compose up -d` | Build timeout | `--no-cache` rebuild | Healthchecks in YAML |
| FastAPI | Auto via Docker | Model load fail | Check RAM/env | Sentry integration |
| Next.js | Auto via Docker | Fetch error | Container URLs | Local emulation |
| PostgreSQL | Auto via Docker | Dir change (v18) | Recreate volume | Version pinning |
| Redis | Auto via Docker | Auth fail | Update password | Conf backups |
| Nginx | `systemctl start nginx` | 502 Gateway | Upstream check | Error logging |
| Cloudflare | Dashboard enable | 521 Error | Firewall allow | Strict SSL |
| Monitoring | Start services | No data | Scrape config | Alerts setup |
| S3 Backups | `./backup.sh` | Permissions | IAM roles | Test restores |
| Stripe | Webhook endpoint | Timeout | CLI forwarding | Replay events |
| Clerk | Auto in app | Middleware error | Add to ts file | Debug mode |

This survey equips you for robust operation, minimizing downtime and ensuring scalability to 500+ users post-launch.

### Key Citations
- [How to Install Docker Compose on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04)
- [Docker deployment not reloading](https://www.reddit.com/r/FastAPI/comments/miydua/docker_deployment_not_reloading_what_am_i_doing/)
- [API works locally, but not in Docker](https://github.com/tiangolo/fastapi/issues/5946)
- [Getting Started: Deploying Next.js](https://nextjs.org/docs/app/getting-started/deploying)
- [Next.js 14 app not responding in Docker](https://stackoverflow.com/questions/78117966/why-is-my-nextjs-14-app-not-responding-when-ran-in-docker-container)
- [Mysterious Docker issue with postgres](https://forums.docker.com/t/mysterious-docker-issue-with-postgres/149898)
- [PostgreSQL 18 volume mount breaks](https://github.com/activepieces/activepieces/issues/9568)
- [Run Redis on Docker](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/docker/)
- [Nginx reverse-proxy problem](https://forums.docker.com/t/nginx-reverse-proxy-general-understanding-problem/131532)
- [NGINX Reverse Proxy not working](https://serverfault.com/questions/1152566/nginx-reverse-proxy-configuration-not-working)
- [Get started with Grafana and Prometheus](https://grafana.com/docs/grafana/latest/getting-started/get-started-grafana-prometheus/)
- [Troubleshooting AWS Backup](https://docs.aws.amazon.com/aws-backup/latest/devguide/troubleshooting.html)
- [Troubleshoot S3 Backup Issues](https://n2ws.com/blog/troubleshooting-common-s3-backup-issues-step-by-step)
- [Stripe Webhook timeout](https://stackoverflow.com/questions/78819839/stripe-webhook-timeout-on-localhost-with-fastapi)
- [Troubleshooting webhook delivery](https://support.stripe.com/questions/troubleshooting-webhook-delivery-issues)
- [Clerk Auth not working](https://www.reddit.com/r/nextjs/comments/1gwazeo/clerk_auth_not_working_can_someone_guide_me_what/)
- [Next.js/Clerk Integration Error](https://stackoverflow.com/questions/79307820/next-js-clerk-integration-error-auth-not-working-with-minimal-setup-typescri)
- [Cloudflare and DigitalOcean](https://community.cloudflare.com/t/cloudflare-and-digitalocean-wordpress-droplet/493710)

