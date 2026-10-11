# HNTH Simple UID Info API (updated for Vercel)

Minimal Flask API — no Firebase, no login, no dashboard, no `api/` folder.
No `UPSTREAM_KEY` environment variable is required.

## What's fixed in this version
1. **CORS enabled for all origins** — any website or app can call this API
   directly from a browser without the "blocked by CORS policy" error.
2. **API key hidden** — opening the website URL (e.g. `GET /`) no longer
   shows the key anywhere; the example URL is just `/api/player`.
3. **No caching** — every response sends `Cache-Control: no-store`, so
   browsers never show a stale cached copy of the opening response.

## Files
- `app.py` — complete Flask API (CORS enabled, key hidden from `/`)
- `index.py` — compatibility import
- `vercel.json` — routes all requests to `app.py`
- `requirements.txt` — Python dependencies (includes `flask-cors`)

## Deploy on Vercel
1. Replace the files in your GitHub repository with these (keep the same
   filenames at the repository root).
2. Import the repository in Vercel and set Root Directory to the
   repository root (or just push — Vercel redeploys automatically).
3. Deploy. No `UPSTREAM_KEY` environment variable is needed.
4. Optional: if your upstream provider uses a different endpoint, set
   `UPSTREAM_URL` in Vercel (default is `https://apiv2.mlbbshop.com/ign`).

## Endpoints
- `GET /` — service information (API key NOT shown)
- `GET /api/health` — health check
- `GET /api/player?uid=1871114586&key=HNTH` — player lookup
  (the key is still required here and is forwarded to the upstream provider;
  it is just never displayed on the website's opening response)

## CORS
All responses include `Access-Control-Allow-Origin: *`, so browser
`fetch()` calls from any website will work — no CORS proxy needed.
To restrict access to specific websites later, change `origins: "*"`
in `app.py` to a list of your domains.
