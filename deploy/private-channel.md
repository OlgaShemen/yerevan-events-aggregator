# Private Telegram event submissions

Set `TELEGRAM_PRIVATE_CHANNEL_IDS` in the backend environment to comma-separated
positive channel IDs, without the `-100` prefix. The authorized Telegram account
must already belong to these channels. Restart/recreate the pipeline container
with the updated environment and code for the setting to take effect.

Private channels use the existing fetch limit and pipeline schedule. Text posts
and media captions enter the normal event extraction, evidence validation,
publication, review and duplicate detection flow. No additional approval rule is
introduced. Messages without text are skipped; images are not transcribed.

For a forwarded public channel post, the importer uses the public original URL
when Telegram supplies the original channel username and message ID. Forwarded
announcements retain their original publication date for relative date handling.
For copied text, specify a concrete event date rather than relying on "tomorrow".

A line beginning with `Источник: https://...` overrides the forwarded source URL.
Private Telegram post and invitation URLs are not accepted as public sources.
Without an available public source URL, the event has no source link. The private
channel URL is never generated as an event source. The model cannot override this
source selection.

The database stores private sources under a stable `private:<id>` key in the
existing `telegram_username` field. No schema migration is needed. The source
cursor and `(source_id, external_id)` uniqueness prevent reimporting the same post.
Edits to an already imported Telegram message are not reprocessed automatically,
as with the other channels.
