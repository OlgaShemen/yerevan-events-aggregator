# Frontend

Simple static HTML/CSS/JS frontend for Yerevan Events Aggregator.

## Files

- `index.html` - page markup.
- `styles.css` - page styles.
- `app.js` - Supabase loading, rendering and filters.
- `review.html` - local moderation page.
- `review.js` - loads events from the local review API.
- `config.js` - local Supabase config. This file is ignored by Git.

## Run locally

From the project root, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_local.ps1
```

Then open:

```text
http://127.0.0.1:5500/index.html
http://127.0.0.1:5500/review.html
```

## Notes

The frontend uses only `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
Never put `SUPABASE_SERVICE_ROLE_KEY` into frontend code.

The moderation page uses the local backend API:

```text
http://127.0.0.1:8000/review/events
```
