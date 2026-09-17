# Trade Craft — Deploy (shareable URL)

The app is packaged as **one service**: the FastAPI backend serves both the API and
the built React frontend (`app.py` mounts `frontend/dist`), so a single deploy gives
you one URL. This is pure app behavior, independent of *how* it's built — so you can
deploy it with or without Docker; no app code changes either way.

> **Status:** repo is **private**. The app now runs on **BYOK (bring-your-own-key)**,
> added 2026-09-17 (see "AI features cost nothing to you" below): every visitor's AI
> calls are billed to THEIR OWN Anthropic API key, never yours. There is no owner-side
> cost risk to manage before sharing the link — deploy it, share it.

## Option A — no Docker (recommended, free): Render native runtime

Render's build image already includes both Node and Python, so a plain **Python**
web service can run the frontend build as part of its build step — no Dockerfile
needed. Config lives in `render.yaml` at the repo root (a Render "Blueprint").

1. Push this repo to GitHub (already done; it's private).
2. Go to <https://render.com> → sign up / log in (your account).
3. **New → Blueprint** → connect the `trade101` repo. Render reads `render.yaml`
   and pre-fills the service (build command, start command, free plan) automatically.
   *(No Blueprint option in your dashboard? Use **New → Web Service** instead, pick
   **Runtime: Python 3**, and paste in the Build/Start commands from `render.yaml`
   by hand — same result.)*
4. When prompted, add your keys (same names as local `.env`):
   - `TRADE101_NEWS_KEY` = your Finnhub key (powers the free, deterministic news feed
     for every visitor — this one IS shared, since it costs nothing per-call on
     Finnhub's free tier).
   - `TRADE101_MODEL` is pre-filled to `claude-sonnet-5` in `render.yaml`; change if you want.
   - `TRADE101_ANALYSIS_KEY` is **optional and NOT recommended on a shared/deployed
     host** — see the BYOK section below. Only set it for a private, personal-use
     deploy where you're the only visitor.
   - Don't set `PORT` — Render provides it; the app reads `$PORT`.
5. **Apply / Create** → wait for the build → you get a URL like
   `https://trade-craft.onrender.com`. That's your shareable link.

This is genuinely free (Render's free web-service tier), with the same idle-sleep
behavior as any free tier: it sleeps after ~15 min with no traffic, so the first hit
after a nap is slow — that's normal, not a bug.

## Option B — Docker (if you prefer, or for a host that requires it)

A multi-stage `Dockerfile` (builds the frontend, then runs the backend) + `.dockerignore`
are also in the repo, for hosts like Fly.io/Railway that expect a Dockerfile, or if you
just prefer containers. Same steps as Option A, except Render (or another host) auto-detects
the `Dockerfile` instead of `render.yaml` — pick **New → Web Service** and let it build
the image; same env vars, same free-tier behavior.

**Netlify is not a fit for this app.** Netlify is a static-site + serverless-functions
platform; it can't run the persistent FastAPI process this app is built as. Moving to
Netlify would mean either splitting into two separately-hosted services (frontend +
backend elsewhere, reintroducing CORS) or rewriting the backend as serverless
functions — real rearchitecting, not warranted here. Stick with Render or another
plain Python/container host (Fly.io, Railway).

## Add the link to the repo

Once you have the URL, put it on the repo (GitHub → repo **About** → Website field, or
the README). Ask Claude and it'll add it to the README.

## AI features cost nothing to you — BYOK (bring-your-own-key, 2026-09-17)

**Every visitor supplies their own Anthropic API key**, pasted once into the app itself
(a first-run gate, `components/ApiKeyGate.jsx`) and saved permanently in THEIR OWN
browser (`localStorage` — never sent anywhere except as the `X-Anthropic-Key` header on
`/analyze` and `/ask`, never logged or stored server-side). This replaced the old
shared `TRADE101_ACCESS_TOKEN` + daily-cap gate entirely: there's no cap to hit, no
token to distribute, and no bill that's ever yours from a stranger using the link.

- The deterministic parts of the app (chart, indicators, news, patterns, ecosystem)
  need no key at all and stay fully free/open for anyone, same as always.
- Only the AI features (the momentum read, Ask TC-Buddy) need a key, and it's always
  the visitor's own.
- `TRADE101_ANALYSIS_KEY` (env var) still works as a **local-dev-only fallback** when
  no visitor key is supplied — convenient for your own testing. **Do not set it on a
  shared/deployed host**, or a visitor without their own key silently falls back to
  spending yours, defeating the whole point. Only set it for a genuinely
  personal/private deploy.
- A visitor with no Anthropic account yet can get one at
  <https://console.anthropic.com/settings/keys>.

## Local dev is unchanged

Two terminals (`uvicorn ...` + `npm run dev`) still work exactly as before — in dev
the frontend calls the backend on its own port (see `CLAUDE.md` for the currently
live port on this machine); in the built/deployed app it calls the same origin
automatically (`api.js` switches on `import.meta.env.DEV`).
