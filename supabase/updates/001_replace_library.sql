-- Aggiornamento per il database già creato con schema.sql (Fase 6, lezione 4).
-- Si esegue una volta sola nel SQL Editor: aggiunge l'ordine dei giochi e la funzione che salva tutta la libreria.

alter table public.games add column position integer not null default 0;

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
