Add, modify, or query Docker Compose configuration in this repo.

## Repo structure
- `services/<name>/compose.yml` — reusable service definition
- `machines/<name>/docker-compose.yml` — per-machine deployment, uses `include:` to pull in services
- Only `services/tools/` has a custom Dockerfile; everything else uses upstream images
- CI builds `services/tools/` on push to main → `ghcr.io/carlzhangxuan/homelab-agent/tools`

## Machines
- **macmini** — management plane: runs tools + open-webui + monitoring
- **titanx / 4090 / 5090** — workers: run gpu-exporter only

## Rules when editing
- New service → create `services/<name>/compose.yml`, then add to relevant machine(s) via `include:`
- Port overrides go in `machines/<name>/.env.example`, never hardcoded in compose files
- Worker machines only get services they actually need
- After any change, verify `docker compose -f machines/<machine>/docker-compose.yml config` would resolve cleanly

## Common tasks
- "Add service X to macmini" → create `services/X/compose.yml`, add include line to `machines/macmini/docker-compose.yml`
- "Add a new worker machine" → create `machines/<name>/docker-compose.yml` with gpu-exporter, add scrape target to `services/monitoring/prometheus.yml`
- "Change port for grafana" → update `GRAFANA_PORT` default in `services/monitoring/compose.yml` and `.env.example`
