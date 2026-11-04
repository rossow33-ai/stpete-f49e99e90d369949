# St. Pete property ranker

Public app: https://rossow33-ai.github.io/stpete-f49e99e90d369949/ (GitHub Pages, static, single `index.html`)

Shared data lives in one JSON document on textdb.dev (no login, open CORS):

- Read:  `GET  https://textdb.dev/api/data/<KEY>`   (KEY is in `tdkey.txt`; add `?_=<timestamp>` to bust caches)
- Write: `POST https://textdb.dev/api/data/<KEY>` with header `Content-Type: text/plain` and the full JSON as body. A POST **replaces the whole document**, so always read, modify, then write back (and keep every existing item untouched).

## Format

```json
{ "v": 2, "items": [ { ...item }, ... ] }
```

Array order is the ranking. List and Discarded show items with that status in array order; Realtinder shows status `queue` items in array order (first = shown first).

Item fields:

| field | type | notes |
|---|---|---|
| id | string | unique; use the MLS number (e.g. `TB8557907`) |
| mls | string | MLS number (used for dedupe and the Zillow link) |
| addr | string | street address, e.g. `6273 20th St S` |
| zip | string | e.g. `33712` |
| price | number or null | dollars |
| sqft | number or null | living area; $/sf is computed as round(price/sqft) and shown as `$313/sf` |
| lat, lon | number or null | used for miles from Central Ave (nearest point on lat 27.7709, lon -82.75..-82.63) |
| img | string | main photo URL (empty string = placeholder) |
| by | string | who added it: `Tom`, `Realtor` or `Bot` (shown as a tag) |
| status | string | `queue` (Realtinder), `list` or `discard` |
| notes | array | `{ "by": "Tom"|"Realtor"|"Bot", "text": "...", "ts": <epoch ms> }` |

## Appending new listings from a daily job

1. GET the document. 2. Skip any listing whose `mls` already exists in `items` (any status). 3. **Insert new items at the FRONT** of `items` (`unshift`) with `status: "queue"`, `by: "Bot"`, `notes: []`. 4. POST the whole document back right away (keep the read-to-write window small; the app does the same merge on every edit).

Example item:

```json
{"id":"TB8999999","mls":"TB8999999","addr":"123 4th Ave S","zip":"33705","price":450000,"sqft":1500,"lat":27.7585,"lon":-82.6490,"img":"https://photos.zillowstatic.com/fp/....jpg","by":"Bot","status":"queue","notes":[]}
```

Photo/price/sqft can come from the listing page (the app gets photos via `https://r.jina.ai/<zillow-address-url>`). Missing values: leave `null` / `""`. Users can edit address, ZIP, price and sqft in the app.

## Behaviour notes

- Realtinder never advances on its own: the card on screen only changes when the user swipes or taps ♥ / ✕ (a background refresh every 6s keeps the current card; new Bot adds wait their turn behind it).
- `seed.json` / `cur3.json` are earlier snapshots used for resets.

## RULES: never touch the production data

- **NEVER reset, reseed or overwrite the shared data when updating the app.** Deploys change code only (`index.html`); the data lives in textdb.dev and is not part of the repo. The app contains no seed data and never writes on load; it writes only when a user edits something, and it always re-reads the latest data first, so it can never replace the list with an old copy.
- **Do not run tests against the production key.** Use the mock in `test6.py` (browser requests to textdb.dev are intercepted and answered from an in-memory copy, so nothing is written), or a separate throwaway key.
- Before any deploy, back up the live data: `curl -s "https://textdb.dev/api/data/\$(cat tdkey.txt)?_=\$RANDOM" -o backup-\$(date +%Y%m%d-%H%M%S).json` (backups are also kept in /workspace/stpete-backups/).
- To change data (e.g. a daily job adding listings) do a read-modify-write that keeps every existing item, status, order and note exactly as is. Never POST a snapshot file.
- A backup of the live state is `backup-*.json` in this folder; to restore, POST it back only if the user explicitly asks.
- Icon: `icons/flamingo.svg` (source), PNGs in `icons/`, `favicon.ico`, `manifest.webmanifest`.

Notes sheet link buttons: Maps (Google Maps search by address), Zillow, OneHome. OneHome is invite-only (per-buyer token), so the button copies the MLS# and opens https://portal.onehome.com/. Icons: icons/app-*.png (App Store artwork).
