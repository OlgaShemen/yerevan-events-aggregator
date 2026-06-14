-- Add original source text to public events.
-- Run this file in Supabase SQL Editor before reprocessing raw_items.

alter table events
add column if not exists original_text text;

update events e
set original_text = ri.raw_text
from event_sources es
join raw_items ri on ri.id = es.raw_item_id
where es.event_id = e.id
  and es.is_primary = true
  and e.original_text is null;

drop view if exists public_events;

create view public_events as
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
