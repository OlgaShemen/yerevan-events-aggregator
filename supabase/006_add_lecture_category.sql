-- Add the lecture category without changing existing events.
alter type public.event_category add value if not exists 'lecture';
notify pgrst, 'reload schema';
