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

## New-listing badge
An item shows an amber **New listing** badge (Realtinder card, and a small one on List/Discarded bars) when EITHER:
- `isNew: true` is set on the item (set `isNew:false` or delete it to clear), OR
- `listedDate` is an ISO date string (e.g. `"2026-11-04"`) within the last 7 days.
Items without either field are never flagged (all existing items are unflagged). The app only reads these fields; it never writes them. The daily routine should set `isNew:true` (and optionally `listedDate`) when it prepends a new listing.

## Taste game (≡ → Taste game)
A photo-swipe game that learns Tom's style and ranks homes by it. Files: `taste.js` (code), `taste.json` (photos + tags, prebuilt; the app never tags at runtime), `taste_summary.py` (read-only exporter → `taste-summary.md`).

- **Photos** (`taste.json` → `photos[]`): `{id, mls, url, tags}`. 136 photos from 63 listings (Zillow listing galleries: the homes in the app plus 18 other active south-side listings in `extra[]`), tagged by hand. Tags: `room` (ext|entry|kit|liv|din|bed|garage|yard|pool), `warmth` (warm|cool), `style` (modern|traditional), `open` (bool), `ext` (ranch|new|bung|mcm), `pool`, `yard` (big|small), `garage`, `hood` (neighborhood bucket from lat/lon).
- **extra[]**: other active listings `{id,mls,addr,zip,price,sqft,lat,lon,img,hood,built}` that appear in *Best matches* with an "Add to Realtinder" button.
- **Game data lives in a SEPARATE textdb key: `<KEY>-taste`** (KEY from `tdkey.txt`, i.e. `https://textdb.dev/api/data/<KEY>-taste`) plus localStorage `taste`. Format:
  ```json
  {"v":1,"people":{"Tom":{"swipes":[{"p":"p042","d":1,"ts":1762650000000}],"duels":[{"w":"p012","l":"p006","ts":...,"n":7}],"undone":[ts,...]}},
   "scores":{"Tom":{"warmth:warm":0.71,"ext:ranch":0.42,"warmth:cool":-0.58,"hood:Pinellas Point / Skyway":0.2}},"updated":<epoch ms>}
  ```
  `d` = 1 love / -1 nope. `scores[person][feature]` is in -1..1: `(pos-neg)/(pos+neg+2)` over the features of loved vs noped photos (this-or-that picks count 1.5 for the features that differ). Feature names: `warmth:warm|cool`, `style:modern|traditional`, `open|closed`, `ext:ranch|new|bung|mcm`, `pool`, `yard:big|small`, `garage`, `hood:<name>`.
  The game writes this key (read-merge-write, union of swipes) and nothing else.
- **Main shared data is written ONLY when Tom taps "Add to Realtinder"** on a Best-matches card: it prepends that one listing (`by:"Bot"`, `status:"queue"`, one Bot note with the match %) through the normal `mutate()` read-modify-write. Homes already in List/Realtinder just show "List #n" / "In Realtinder".
- **Daily routine**: GET `<KEY>-taste`, read `scores.Tom`, and rank/describe new listings with it (e.g. prefer features with score ≥ 0.2, avoid ≤ -0.2; `python3 taste_summary.py` prints a readable summary and writes `taste-summary.md`). Never POST to the taste key from a job.
- Tests: `test_taste.py <url> <tag>` mocks both keys (main copy from the latest `/workspace/stpete-backups/backup-*-pretaste.json`), plays the game, and asserts no main write except the explicit add.
- Rebuild photos/tags: tooling in `/workspace/taste/` (`fetch.py`, `extract.py`, `tags.txt`, `build.py`).
