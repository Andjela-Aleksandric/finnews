create table if not exists public.saved_portfolios (
  portfolio_id text primary key,
  display_name text not null check (char_length(display_name) between 1 and 80),
  salt text not null,
  verifier text not null,
  iv text not null,
  cipher text not null,
  iterations integer not null check (iterations = 600000),
  updated_at timestamptz not null default now()
);

alter table public.saved_portfolios enable row level security;
revoke all on public.saved_portfolios from anon, authenticated;

create table if not exists public.portfolio_rate_limits (
  bucket_key text primary key,
  window_started timestamptz not null,
  attempts integer not null default 0
);

alter table public.portfolio_rate_limits enable row level security;
revoke all on public.portfolio_rate_limits from anon, authenticated;

create or replace function public.consume_portfolio_attempt(
  p_bucket_key text,
  p_now timestamptz,
  p_limit integer default 30,
  p_window_seconds integer default 900
) returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  current_attempts integer;
begin
  insert into public.portfolio_rate_limits(bucket_key, window_started, attempts)
  values (p_bucket_key, p_now, 1)
  on conflict (bucket_key) do update
    set attempts = case
          when public.portfolio_rate_limits.window_started + make_interval(secs => p_window_seconds) <= p_now then 1
          else public.portfolio_rate_limits.attempts + 1
        end,
        window_started = case
          when public.portfolio_rate_limits.window_started + make_interval(secs => p_window_seconds) <= p_now then p_now
          else public.portfolio_rate_limits.window_started
        end
  returning attempts into current_attempts;

  delete from public.portfolio_rate_limits where window_started < p_now - interval '1 day';
  return current_attempts <= p_limit;
end;
$$;

revoke all on function public.consume_portfolio_attempt(text, timestamptz, integer, integer) from public, anon, authenticated;
grant execute on function public.consume_portfolio_attempt(text, timestamptz, integer, integer) to service_role;
