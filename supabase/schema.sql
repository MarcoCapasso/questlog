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
    position    integer not null default 0,
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

-- 4. SALVATAGGIO DELL'INTERA LIBRERIA IN UN COLPO -----------------------------

-- L'app manda tutta la libreria come JSON: la funzione cancella i giochi dell'utente e li riscrive.
-- Una funzione Postgres gira in un'unica transazione: se una riga non va bene, non cambia niente.
-- security invoker: gira con i permessi di chi la chiama, quindi valgono le regole RLS qui sopra.
create or replace function public.replace_library(library jsonb)
returns void
language plpgsql
security invoker
set search_path = ''
as $$
declare
    game jsonb;
    game_position bigint;
    new_game_id uuid;
begin
    if (select auth.uid()) is null then
        raise exception 'Serve un utente con il login fatto';
    end if;
    if jsonb_typeof(library) <> 'array' then
        raise exception 'La libreria deve essere una lista di giochi';
    end if;

    delete from public.games where user_id = (select auth.uid());

    for game, game_position in
        select item.value, item.ordinality - 1
        from jsonb_array_elements(library) with ordinality as item
    loop
        insert into public.games (title, rating, igdb_id, cover_url, position)
        values (
            game ->> 'title',
            (game ->> 'rating')::smallint,
            (game ->> 'igdb_id')::integer,
            game ->> 'cover_url',
            game_position
        )
        returning id into new_game_id;

        insert into public.playthroughs
            (game_id, position, platform, status, hours_played, start_date, completion_date, notes)
        select
            new_game_id,
            play.ordinality - 1,
            play.value ->> 'platform',
            play.value ->> 'status',
            (play.value ->> 'hours_played')::numeric,
            (play.value ->> 'start_date')::date,
            (play.value ->> 'completion_date')::date,
            coalesce(play.value ->> 'notes', '')
        from jsonb_array_elements(coalesce(game -> 'playthroughs', '[]'::jsonb)) with ordinality as play;
    end loop;
end;
$$;

-- Solo chi ha fatto login può chiamarla (Supabase di base la darebbe anche ad anon).
revoke execute on function public.replace_library(jsonb) from public, anon;
grant execute on function public.replace_library(jsonb) to authenticated;
