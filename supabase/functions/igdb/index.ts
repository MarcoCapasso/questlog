// Edge Function "igdb": il catalogo di Questlog passa da qui, così le credenziali IGDB restano sul server.
// Risponde solo agli utenti con il login fatto e solo alle azioni di queries.ts.

import { withSupabase } from "npm:@supabase/server@1.6.1";
import {
  type Action,
  detailsQuery,
  gamesByIdsQuery,
  newReleasesQuery,
  parseAction,
  searchQuery,
  TRENDING_QUERY,
  upcomingQuery,
} from "./queries.ts";

const TOKEN_URL = "https://id.twitch.tv/oauth2/token";
const API_URL = "https://api.igdb.com/v4";
const TIMEOUT_MS = 10_000;
const TOKEN_SAFETY_SECONDS = 60;
// IGDB accetta al massimo 4 richieste al secondo per app (condivise da tutti gli utenti): oltre risponde 429.
const TOO_MANY_REQUESTS = 429;
const RETRY_DELAY_MS = 1_000;
// I segreti si leggono dai Secrets del progetto Supabase: non sono nel codice né su GitHub.
const CLIENT_ID = Deno.env.get("IGDB_CLIENT_ID") ?? "";
const CLIENT_SECRET = Deno.env.get("IGDB_CLIENT_SECRET") ?? "";

type IgdbRow = Record<string, unknown>;

// Un errore con un messaggio adatto all'utente e il codice HTTP da restituire all'app.
class CatalogError extends Error {
  constructor(message: string, readonly status = 502) {
    super(message);
  }
}

// Il token di Twitch resta in memoria finché la funzione è "calda": non se ne chiede uno a ogni ricerca.
let cachedToken: { value: string; expiresAt: number } | null = null;

async function twitchToken(): Promise<string> {
  if (cachedToken !== null && Date.now() < cachedToken.expiresAt) {
    return cachedToken.value;
  }
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    client_secret: CLIENT_SECRET,
    grant_type: "client_credentials",
  });
  const response = await fetch(`${TOKEN_URL}?${params}`, {
    method: "POST",
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  if (!response.ok) {
    throw new CatalogError("Il catalogo non è configurato correttamente sul server.");
  }
  const data = await response.json();
  cachedToken = {
    value: data.access_token,
    expiresAt: Date.now() + (data.expires_in - TOKEN_SAFETY_SECONDS) * 1000,
  };
  return cachedToken.value;
}

async function queryIgdb(endpoint: string, body: string): Promise<IgdbRow[]> {
  let response = await sendToIgdb(endpoint, body);
  if (response.status === TOO_MANY_REQUESTS) {
    // Troppe richieste in questo secondo: si aspetta un attimo e si riprova una volta sola.
    await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
    response = await sendToIgdb(endpoint, body);
  }
  if (response.status === TOO_MANY_REQUESTS) {
    throw new CatalogError("Il catalogo è molto richiesto in questo momento: riprova tra qualche secondo.", 429);
  }
  if (response.status === 401) {
    cachedToken = null; // token scaduto o revocato: al prossimo giro se ne chiede uno nuovo
    throw new CatalogError("IGDB ha rifiutato l'accesso: riprova tra poco.");
  }
  if (!response.ok) {
    throw new CatalogError(`IGDB ha risposto con un errore (${response.status}).`);
  }
  return await response.json();
}

async function sendToIgdb(endpoint: string, body: string): Promise<Response> {
  return await fetch(`${API_URL}/${endpoint}`, {
    method: "POST",
    headers: { "Client-ID": CLIENT_ID, Authorization: `Bearer ${await twitchToken()}` },
    body,
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
}

// Esegue l'azione chiesta e restituisce le righe di IGDB (l'app le trasforma in CatalogGame).
async function runAction(request: Action): Promise<IgdbRow[]> {
  const now = Math.floor(Date.now() / 1000);
  switch (request.action) {
    case "search":
      return await queryIgdb("games", searchQuery(request.text));
    case "trending": {
      const popularity = await queryIgdb("popularity_primitives", TRENDING_QUERY);
      const ids = popularity.map((row) => Number(row.game_id));
      if (ids.length === 0) {
        return [];
      }
      const games = await queryIgdb("games", gamesByIdsQuery(ids));
      return games.sort((a, b) => ids.indexOf(Number(a.id)) - ids.indexOf(Number(b.id)));
    }
    case "new_releases":
      return await queryIgdb("games", newReleasesQuery(now));
    case "upcoming":
      return await queryIgdb("games", upcomingQuery(now));
    case "details":
      return await queryIgdb("games", detailsQuery(request.id));
  }
}

export default {
  // auth: "user" fa entrare solo chi manda il token di un utente: senza login la funzione non parte.
  fetch: withSupabase({ auth: "user" }, async (req, ctx) => {
    if (ctx.userClaims?.role !== "authenticated") {
      return Response.json({ error: "Serve il login." }, { status: 401 });
    }
    const request = parseAction(await req.json().catch(() => null));
    if (request === null) {
      return Response.json({ error: "Richiesta non valida." }, { status: 400 });
    }
    try {
      return Response.json({ games: await runAction(request) });
    } catch (error) {
      console.error(error); // finisce nei log della funzione su Supabase, non all'utente
      if (error instanceof CatalogError) {
        return Response.json({ error: error.message }, { status: error.status });
      }
      return Response.json({ error: "Il catalogo non risponde: riprova." }, { status: 502 });
    }
  }),
};
