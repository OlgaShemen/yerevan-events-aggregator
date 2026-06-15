-- Yerevan Events Aggregator - Supabase/PostgreSQL schema for MVP
-- Run this file in Supabase SQL Editor.

create extension if not exists pgcrypto;

-- Source type: where raw event data comes from.
do $$
begin
  if not exists (select 1 from pg_type where typname = 'source_type') then
    create type source_type as enum ('telegram', 'website', 'manual');
  end if;
end $$;

-- Processing status for raw collected items.
do $$
begin
  if not exists (select 1 from pg_type where typname = 'raw_item_status') then
    create type raw_item_status as enum (
      'new',
      'processing',
      'processed',
      'failed',
      'ignored'
    );
  end if;
end $$;

-- Publication/review status for normalized events.
do $$
begin
  if not exists (select 1 from pg_type where typname = 'event_status') then
    create type event_status as enum (
      'draft',
      'needs_review',
      'published',
      'archived',
      'rejected'
    );
  end if;
end $$;

-- Broad categories are enough for MVP.
do $$
begin
  if not exists (select 1 from pg_type where typname = 'event_category') then
    create type event_category as enum (
      'concert',
      'theatre',
      'exhibition',
      'party',
      'movie',
      'workshop',
      'tourism',
      'food',
      'kids',
      'other'
    );
  end if;
end $$;

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  type source_type not null,
  url text,
  telegram_username text,
  is_active boolean not null default true,
  priority integer not null default 100,
  last_checked_at timestamptz,
  last_seen_external_id text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint sources_has_location check (
    url is not null or telegram_username is not null
  )
);

create table if not exists raw_items (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references sources(id) on delete cascade,
  external_id text,
  source_url text,
  raw_text text not null,
  raw_html text,
  raw_payload jsonb not null default '{}'::jsonb,
  language_hint text,
  status raw_item_status not null default 'new',
  error_message text,
  collected_at timestamptz not null default now(),
  processed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint raw_items_unique_external unique (source_id, external_id)
);

create table if not exists venues (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  address text,
  city text not null default 'Yerevan',
  latitude numeric(10, 7),
  longitude numeric(10, 7),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint venues_unique_name_address unique (name, address)
);

create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  original_text text,
  category event_category not null default 'other',
  language text not null default 'unknown',
  date_start date,
  time_start time,
  date_end date,
  time_end time,
  venue_id uuid references venues(id) on delete set null,
  venue_name text,
  address text,
  price_text text,
  source_url text,
  status event_status not null default 'draft',
  category_checked boolean not null default false,
  confidence_score numeric(4, 3) not null default 0,
  normalized_key text,
  ai_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint events_confidence_range check (
    confidence_score >= 0 and confidence_score <= 1
  )
);

-- One normalized event can be found in several raw sources.
create table if not exists event_sources (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references events(id) on delete cascade,
  raw_item_id uuid references raw_items(id) on delete set null,
  source_id uuid not null references sources(id) on delete cascade,
  source_url text,
  is_primary boolean not null default false,
  created_at timestamptz not null default now(),

  constraint event_sources_unique_raw_item unique (event_id, raw_item_id)
);

create table if not exists processing_logs (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references sources(id) on delete set null,
  raw_item_id uuid references raw_items(id) on delete set null,
  event_id uuid references events(id) on delete set null,
  step text not null,
  status text not null,
  message text,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_sources_type_active
  on sources (type, is_active);

create index if not exists idx_raw_items_status_collected
  on raw_items (status, collected_at);

create index if not exists idx_raw_items_source_external
  on raw_items (source_id, external_id);

create index if not exists idx_events_status_date
  on events (status, date_start);

create index if not exists idx_events_category
  on events (category);

create index if not exists idx_events_status_category_checked
  on events (status, category_checked);

create index if not exists idx_events_language
  on events (language);

create index if not exists idx_events_venue_name
  on events (venue_name);

create index if not exists idx_events_normalized_key
  on events (normalized_key);

create index if not exists idx_processing_logs_created
  on processing_logs (created_at);

-- Public view for the future frontend.
create or replace view public_events as
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

-- Simple helper to keep updated_at fresh.
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_sources_updated_at on sources;
create trigger trg_sources_updated_at
before update on sources
for each row execute function set_updated_at();

drop trigger if exists trg_raw_items_updated_at on raw_items;
create trigger trg_raw_items_updated_at
before update on raw_items
for each row execute function set_updated_at();

drop trigger if exists trg_venues_updated_at on venues;
create trigger trg_venues_updated_at
before update on venues
for each row execute function set_updated_at();

drop trigger if exists trg_events_updated_at on events;
create trigger trg_events_updated_at
before update on events
for each row execute function set_updated_at();
