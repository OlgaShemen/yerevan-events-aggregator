# Server deploy notes

This folder contains Docker Compose config for the backend services.

## Services

- `admin`: password-protected admin UI on port `8087`.
- `review-api`: long-running local API on `127.0.0.1:8000`.
- `pipeline`: one-off ingestion job for Telegram + OpenAI + Supabase.

## Required server files

Create this file on the server:

```bash
cp deploy/backend.env.example deploy/backend.env
nano deploy/backend.env
```

Do not commit `deploy/backend.env`.

Telegram session files are stored in:

```text
deploy/data/telegram/
```

## Commands

Build images:

```bash
docker compose -f deploy/docker-compose.yml build
```

Start review API and admin:

```bash
docker compose -f deploy/docker-compose.yml up -d review-api admin
```

Run pipeline manually:

```bash
docker compose -f deploy/docker-compose.yml run --rm pipeline
```

View API logs:

```bash
docker compose -f deploy/docker-compose.yml logs -f review-api
```

Check API health on the server:

```bash
curl http://127.0.0.1:8000/health
```

Check admin from your browser:

```text
http://SERVER_IP:8087/
```

The admin UI requires `deploy/nginx/.htpasswd`.

## Cron example

Run the pipeline every 6 hours:

```cron
0 */6 * * * cd /opt/yerevan-events-aggregator && docker compose -f deploy/docker-compose.yml run --rm pipeline >> /var/log/yerevan-events-pipeline.log 2>&1
```
