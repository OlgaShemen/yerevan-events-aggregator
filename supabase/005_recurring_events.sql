-- Apply before deploying the recurring-event backend.
-- Adds fields only; existing event data is preserved.
begin;

alter table public.events add column if not exists recurring_schedule text;
alter table public.events add column if not exists display_until date;

create unique index if not exists idx_events_recurring_key
  on public.events (normalized_key) where display_until is not null;

grant select (recurring_schedule, display_until) on public.events to anon, authenticated;

-- Append new columns to preserve the existing view column order.
create or replace view public.public_events
with (security_invoker = true) as
select
  e.id,
  e.title,
  e.description,
  e.original_text,
  e.category,
  e.language,
  e.date_start,
  e.time_start,
  e.date_end,
  e.time_end,
  coalesce(v.name, e.venue_name) as venue_name,
  coalesce(v.address, e.address) as address,
  e.price_text,
  e.source_url,
  e.confidence_score,
  e.created_at,
  e.recurring_schedule,
  e.display_until
from public.events e
left join public.venues v on v.id = e.venue_id
where e.status = 'published'
  and (e.display_until is null or e.display_until >= (now() at time zone 'Asia/Yerevan')::date);

grant select on public.public_events to anon, authenticated;
notify pgrst, 'reload schema';
commit;
