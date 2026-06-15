-- Track manual category checks in the admin UI.
-- Run this file in Supabase SQL Editor before deploying the admin/API change.

alter table events
add column if not exists category_checked boolean not null default false;

create index if not exists idx_events_status_category_checked
  on events (status, category_checked);
