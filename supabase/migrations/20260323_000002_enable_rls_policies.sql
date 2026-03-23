-- Phase 2 / 3 hardening scaffold
-- This migration is intentionally safe to keep in the repo before rollout.
-- It will not affect production until applied in Supabase.

begin;

-- Enable Row Level Security on operational tables.
alter table if exists site_metrics enable row level security;
alter table if exists site_visitors enable row level security;
alter table if exists chat_logs enable row level security;
alter table if exists chat_log_reviews enable row level security;
alter table if exists chat_feedback enable row level security;
alter table if exists sheet_approvals enable row level security;
alter table if exists handoff_requests enable row level security;
alter table if exists knowledge_sync_runs enable row level security;
alter table if exists knowledge_base enable row level security;

-- Remove broad client access assumptions before defining policies.
revoke all on table site_metrics from anon, authenticated;
revoke all on table site_visitors from anon, authenticated;
revoke all on table chat_logs from anon, authenticated;
revoke all on table chat_log_reviews from anon, authenticated;
revoke all on table chat_feedback from anon, authenticated;
revoke all on table sheet_approvals from anon, authenticated;
revoke all on table handoff_requests from anon, authenticated;
revoke all on table knowledge_sync_runs from anon, authenticated;
revoke all on table knowledge_base from anon, authenticated;

-- Public website clients should not query operational tables directly.
-- Backend requests are expected to use the service role key and therefore bypass RLS.

drop policy if exists "deny anon site_metrics" on site_metrics;
create policy "deny anon site_metrics"
  on site_metrics
  for all
  to anon, authenticated
  using (false)
  with check (false);

drop policy if exists "deny anon site_visitors" on site_visitors;
create policy "deny anon site_visitors"
  on site_visitors
  for all
  to anon, authenticated
  using (false)
  with check (false);

drop policy if exists "deny anon chat_logs" on chat_logs;
create policy "deny anon chat_logs"
  on chat_logs
  for all
  to anon, authenticated
  using (false)
  with check (false);

drop policy if exists "deny anon chat_log_reviews" on chat_log_reviews;
create policy "deny anon chat_log_reviews"
  on chat_log_reviews
  for all
  to anon, authenticated
  using (false)
  with check (false);

drop policy if exists "deny anon chat_feedback" on chat_feedback;
create policy "deny anon chat_feedback"
  on chat_feedback
  for all
  to anon, authenticated
  using (false)
  with check (false);

drop policy if exists "deny anon sheet_approvals" on sheet_approvals;
create policy "deny anon sheet_approvals"
  on sheet_approvals
  for all
  to anon, authenticated
  using (false)
  with check (false);

drop policy if exists "deny anon handoff_requests" on handoff_requests;
create policy "deny anon handoff_requests"
  on handoff_requests
  for all
  to anon, authenticated
  using (false)
  with check (false);

drop policy if exists "deny anon knowledge_sync_runs" on knowledge_sync_runs;
create policy "deny anon knowledge_sync_runs"
  on knowledge_sync_runs
  for all
  to anon, authenticated
  using (false)
  with check (false);

-- Optional read-only policy for direct client access to knowledge rows.
-- Keep disabled by default unless a future frontend uses Supabase directly.
drop policy if exists "read active knowledge base" on knowledge_base;
create policy "read active knowledge base"
  on knowledge_base
  for select
  to authenticated
  using (false);

commit;
