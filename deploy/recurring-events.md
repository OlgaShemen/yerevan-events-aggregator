# Weekly Recurring Offers

Status (2026-09-04): database migration and server deployment verified.
Both admin lists and the public view load successfully. The server uses gpt-5.6-luna.
The public frontend is included in this change for GitHub Pages publication.

## Behavior

- Explicit recurring offers without calendar dates retain null start/end dates.
- The model quotes the recurrence wording and all daily groups in `recurring_schedule`.
- The quote must appear in the source post and contain explicit recurrence wording.
- `display_until` is the Sunday of the Telegram publication week in Asia/Yerevan.
- Missing/invalid publication timestamps do not fall back to collection or processing time.
- Offers from expired weeks are ignored during processing.
- Reimports with the same normalized title/place/source/week reuse the existing card,
  preserving moderation. The unique partial index also prevents concurrent duplicates.
- A fresh post in a new week gets a new key. Changed titles can still require manual review.
- The public view and both admin lists hide expired offers; no archive job is needed.
- The public page also expires loaded cards when the calendar day changes.
- A date filter excludes recurring offers. Ordinary dated events behave as before.
- Admin displays the schedule and expiry. Entering a concrete date converts the card
  to a dated event. Approving an expired recurring offer is blocked by the review API.

## Deployment Order

1. Run `supabase/005_recurring_events.sql` in Supabase SQL Editor.
   The migration preserves existing data and the security-invoker view. New view
   columns are appended, so existing clients keep working during deployment.
2. Verify the new columns are readable through `events` with the server role and
   through `public_events` with the public role. Do not print any keys.
3. Upload these backend files to the existing server project:
   `app/recurring_events.py`, `app/event_extraction.py`, `process_raw_item_to_event.py`,
   `batch_process_raw_items.py`, `reprocess_raw_item_by_source.py`, `review_api.py`,
   `requirements.txt`, `test_recurring_events.py`.
   Preserve the advertising filters already deployed in `app/event_filtering.py`.
4. Build `pipeline` and `review-api`. Run the tests in the new image without
   calling OpenAI. Recreate `review-api`, check its health and admin requests.
   Verify `OPENAI_MODEL=gpt-5.6-luna` in the pipeline configuration.
5. Upload `frontend/app.js`, `frontend/index.html`, `frontend/review.js` and
   `frontend/review.html` to the server; publish `docs/app.js` and `docs/index.html`
   to GitHub Pages. Check both desktop and mobile.
6. The next cron run uses the new logic. Historical posts are not bulk reprocessed.
   Reprocess a specific current-week source only when requested.

## Verification

From `backend`: `.venv/Scripts/python.exe -B -m unittest test_recurring_events test_event_filtering`

From the project root: `node frontend/test-recurring.cjs`

The browser test uses Playwright and installed Chrome. When Playwright is bundled
outside the project, set `PLAYWRIGHT_MODULE_ROOT` to its containing `node_modules`
directory. Screenshots are saved in the operating system's temporary directory.

The browser test uses fixtures, not the production database or OpenAI.
