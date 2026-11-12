// Le richieste a IGDB che il catalogo di Questlog può fare: le costruisce il server, mai l'app.
// Sono le stesse di core/igdb.py, scritte in TypeScript.

export const SECTION_SIZE = 20;
const SEARCH_SIZE = 30;
const MAX_SEARCH_LENGTH = 100;
const NEW_RELEASES_DAYS = 60;
const SECONDS_PER_DAY = 24 * 60 * 60;
const TRENDING_POPULARITY_TYPE = 1;
const GAME_FIELDS = "fields name, cover.image_id, first_release_date, platforms.name, genres.name, summary;";
const DETAIL_FIELDS =
  "fields name, cover.image_id, first_release_date, platforms.name, genres.name, summary, " +
  "screenshots.image_id, artworks.image_id;";

// Le sole azioni accettate: qualsiasi altra richiesta viene rifiutata.
export type Action =
  | { action: "search"; text: string }
  | { action: "trending" }
  | { action: "new_releases" }
  | { action: "upcoming" }
  | { action: "details"; id: number };

// Controlla il JSON arrivato dall'app: restituisce l'azione se è valida, altrimenti null.
export function parseAction(body: unknown): Action | null {
  if (typeof body !== "object" || body === null) {
    return null;
  }
  const data = body as Record<string, unknown>;
  switch (data.action) {
    case "search":
      return typeof data.text === "string" && data.text.trim() !== ""
        ? { action: "search", text: data.text }
        : null;
    case "trending":
    case "new_releases":
    case "upcoming":
      return { action: data.action };
    case "details":
      return typeof data.id === "number" && Number.isInteger(data.id) && data.id > 0
        ? { action: "details", id: data.id }
        : null;
    default:
      return null;
  }
}

// Ricerca per titolo: virgolette e barre tolte per non rompere la sintassi di IGDB, testo accorciato.
export function searchQuery(text: string): string {
  const cleanText = text.replaceAll('"', "").replaceAll("\\", "").trim().slice(0, MAX_SEARCH_LENGTH);
  return `search "${cleanText}"; ${GAME_FIELDS} where version_parent = null; limit ${SEARCH_SIZE};`;
}

// Classifica di popolarità: restituisce solo gli id dei giochi, in ordine.
export const TRENDING_QUERY =
  `fields game_id, value; where popularity_type = ${TRENDING_POPULARITY_TYPE}; ` +
  `sort value desc; limit ${SECTION_SIZE};`;

// I dati dei giochi con questi id (per la classifica di popolarità).
export function gamesByIdsQuery(ids: number[]): string {
  return `${GAME_FIELDS} where id = (${ids.join(", ")}); limit ${SECTION_SIZE};`;
}

// Giochi attesi usciti negli ultimi 60 giorni; now è l'ora attuale in secondi.
export function newReleasesQuery(now: number): string {
  const since = now - NEW_RELEASES_DAYS * SECONDS_PER_DAY;
  return (
    `${GAME_FIELDS} where first_release_date >= ${since} & first_release_date <= ${now} ` +
    `& hypes > 0 & cover != null & version_parent = null; ` +
    `sort first_release_date desc; limit ${SECTION_SIZE};`
  );
}

// Giochi non ancora usciti, dal più atteso.
export function upcomingQuery(now: number): string {
  return (
    `${GAME_FIELDS} where first_release_date > ${now} & hypes > 0 ` +
    `& cover != null & version_parent = null; sort hypes desc; limit ${SECTION_SIZE};`
  );
}

// Un gioco con descrizione, screenshot e artwork.
export function detailsQuery(id: number): string {
  return `${DETAIL_FIELDS} where id = ${id};`;
}
