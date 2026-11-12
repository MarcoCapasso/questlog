import { deepStrictEqual as assertEquals } from "node:assert";
import { parseAction, searchQuery } from "./queries.ts";

Deno.test("accetta solo le azioni previste", () => {
  assertEquals(parseAction({ action: "search", text: "zelda" }), { action: "search", text: "zelda" });
  assertEquals(parseAction({ action: "details", id: 405460 }), { action: "details", id: 405460 });
  assertEquals(parseAction({ action: "trending" }), { action: "trending" });
  assertEquals(parseAction({ action: "search", text: "   " }), null);
  assertEquals(parseAction({ action: "details", id: "1; delete" }), null);
  assertEquals(parseAction({ action: "games", body: "fields *;" }), null);
  assertEquals(parseAction(null), null);
});

Deno.test("la ricerca toglie i caratteri che romperebbero la richiesta", () => {
  assertEquals(
    searchQuery('zel"da\\'),
    'search "zelda"; fields name, cover.image_id, first_release_date, platforms.name, genres.name, summary; ' +
      "where version_parent = null; limit 30;",
  );
});
