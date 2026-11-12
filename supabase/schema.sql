-- Schema del database di Questlog su Supabase.
-- Si esegue una volta nel SQL Editor del progetto, un blocco alla volta.


-- 1. GIOCHI ------------------------------------------------------------------

create table public.games (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null default auth.uid() references auth.users (id) on delete cascade,
    title       text not null check (length(trim(title)) > 0),
    rating      smallint check (rating between 1 and 5),
    igdb_id     integer,
    cover_url   text,
    created_at  timestamptz not null default now()
);

-- Lo stesso utente non può avere due giochi con lo stesso titolo (maiuscole ignorate)
-- né due giochi collegati allo stesso gioco IGDB.
create unique index games_user_title_key on public.games (user_id, lower(title));
create unique index games_user_igdb_key on public.games (user_id, igdb_id);


-- 2. PARTITE -----------------------------------------------------------------

create table public.playthroughs (
    id               uuid primary key default gen_random_uuid(),
    game_id          uuid not null references public.games (id) on delete cascade,
    user_id          uuid not null default auth.uid() references auth.users (id) on delete cascade,
    position         smallint not null default 0,
    platform         text not null check (length(trim(platform)) > 0),
    status           text not null check (status in ('playing', 'completed', 'dropped')),
    hours_played     numeric(7, 1) not null default 0 check (hours_played >= 0),
    start_date       date,
    completion_date  date,
    notes            text not null default '',
    check (status <> 'completed' or hours_played > 0),
    check (status = 'completed' or completion_date is null),
    check (start_date is null or completion_date is null or completion_date >= start_date)
);

create index playthroughs_game_id_idx on public.playthroughs (game_id);


-- 3. CHI PUÒ USARE LE TABELLE (GRANT) E QUALI RIGHE VEDE (RLS) ----------------

-- Solo gli utenti che hanno fatto login; la chiave anon da sola non vede nulla.
grant select, insert, update, delete on public.games, public.playthroughs to authenticated;
grant all on public.games, public.playthroughs to service_role;

alter table public.games enable row level security;
alter table public.playthroughs enable row level security;

create policy "Ognuno gestisce solo i propri giochi"
on public.games
for all
to authenticated
using (user_id = (select auth.uid()))
with check (user_id = (select auth.uid()));

create policy "Ognuno gestisce solo le proprie partite"
on public.playthroughs
for all
to authenticated
using (user_id = (select auth.uid()))
with check (
    user_id = (select auth.uid())
    and exists (
        select 1
        from public.games
        where games.id = playthroughs.game_id
          and games.user_id = (select auth.uid())
    )
);
