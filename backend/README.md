# Backend

Python backend scripts for Yerevan Events Aggregator.

## What is inside now

- `requirements.txt` - Python dependencies.
- `.env.example` - example environment variables.
- `app/config.py` - reads settings from `.env`.
- `app/db.py` - creates Supabase client.
- `check_connection.py` - simple Supabase connection check.
- `ingest_manual_raw_item.py` - saves one test raw event text to Supabase.
- `extract_event_from_raw_item.py` - extracts structured event JSON from one raw item.
- `process_raw_item_to_event.py` - extracts one or several event JSON objects and saves them to `events`.
- `batch_process_raw_items.py` - processes several `raw_items` with a safe limit.
- `ingest_telegram_posts.py` - reads Telegram channel posts and saves them to `raw_items`.
- `check_counts.py` - prints row counts for main Supabase tables.
- `list_events.py` - prints saved events.
- `list_events_with_ids.py` - prints saved events with IDs and date ranges.
- `show_event_raw.py` - prints raw source text linked to an event.
- `check_public_events.py` - checks what the frontend can read with anon key.
- `list_review_events.py` - prints events waiting for manual review.
- `review_event.py` - updates, publishes or rejects reviewed events.
- `review_api.py` - local API for the review admin page.
- `find_duplicate_events.py` - finds possible duplicate events without changing data.
- `merge_events.py` - manually merges one duplicate event into another.
- `run_pipeline.py` - runs Telegram ingestion, raw item processing and duplicate check.
- `reset_demo_data.py` - clears demo data and resets Telegram last seen markers.

## Setup

Open PowerShell in the project folder:

```powershell
cd "C:\Users\oshem\Desktop\Yerevan Events Aggregator\backend"
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create local env file:

```powershell
Copy-Item .env.example .env
```

Then open `.env` and paste values from Supabase.

## Check Supabase connection

```powershell
python check_connection.py
```

## Save one manual raw item

```powershell
python ingest_manual_raw_item.py
```

## Extract event JSON from one raw item

```powershell
python extract_event_from_raw_item.py
```

For MVP tests, the default model is `gpt-5.4-mini`. If extraction quality is too low on real event texts, switch `OPENAI_MODEL` in `.env` to a stronger model.

## Convert one raw item to a saved event

```powershell
python process_raw_item_to_event.py
```

## Convert several raw items to saved events

```powershell
python batch_process_raw_items.py --limit 5
```

## Ingest Telegram posts

Add Telegram settings to `.env`:

```env
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your-api-hash
TELEGRAM_SESSION_NAME=yerevan_events
TELEGRAM_CHANNELS=@channel_one,@channel_two
TELEGRAM_FETCH_LIMIT=20
```

Then run:

```powershell
python ingest_telegram_posts.py
```

On the first run, Telethon will ask for your phone number and Telegram login code.
It will create a local `.session` file. This file is ignored by Git.

## Check table counts

```powershell
python check_counts.py
```

## List saved events

```powershell
python list_events.py
```

## Check frontend-readable events

```powershell
python check_public_events.py
```

## Review events

List events that need manual review:

```powershell
python list_review_events.py
```

Update a field:

```powershell
python review_event.py update --event-id EVENT_ID --set venue_name="Cinema Moscow"
```

Publish an event:

```powershell
python review_event.py publish --event-id EVENT_ID
```

Reject an event:

```powershell
python review_event.py reject --event-id EVENT_ID --reason "Not an event"
```

## Run local review API

This API is for the local moderation page. It uses `SUPABASE_SERVICE_ROLE_KEY`
from `backend/.env`, so keep it local and do not deploy it publicly.

```powershell
python review_api.py
```

Local endpoints:

```text
GET    http://127.0.0.1:8000/review/events
PATCH  http://127.0.0.1:8000/review/events/EVENT_ID
POST   http://127.0.0.1:8000/review/events/EVENT_ID/publish
POST   http://127.0.0.1:8000/review/events/EVENT_ID/reject
```

## Deduplicate events

Find possible duplicates:

```powershell
python find_duplicate_events.py
```

Merge a confirmed duplicate into the event you want to keep:

```powershell
python merge_events.py --primary-id EVENT_ID_TO_KEEP --duplicate-id EVENT_ID_TO_ARCHIVE
```

## Run MVP pipeline

Run Telegram ingestion, process up to 10 raw items, then check duplicates:

```powershell
python run_pipeline.py --process-limit 10
```

Process existing raw items only, without reading Telegram:

```powershell
python run_pipeline.py --skip-telegram --process-limit 10
```
