-- Fix Supabase Security Advisor warning:
-- public.public_events should use caller permissions instead of view-owner permissions.

alter table events enable row level security;
alter table venues enable row level security;

grant select (
  id,
  title,
  description,
  original_text,
  category,
  language,
  date_start,
  time_start,
  date_end,
  time_end,
  venue_id,
  venue_name,
  address,
  price_text,
  source_url,
  status,
  confidence_score,
  created_at
) on events to anon, authenticated;

grant select (
  id,
  name,
  address
) on venues to anon, authenticated;

drop policy if exists "Public can read published events" on events;
create policy "Public can read published events"
on events
for select
to anon, authenticated
using (status = 'published');

drop policy if exists "Public can read venues" on venues;
create policy "Public can read venues"
on venues
for select
to anon, authenticated
using (true);

create or replace view public_events
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
  e.created_at
from events e
left join venues v on v.id = e.venue_id
where e.status = 'published';

grant select on public_events to anon, authenticated;
