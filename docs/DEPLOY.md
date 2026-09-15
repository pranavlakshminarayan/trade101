# Trade Craft — Deploy (shareable URL)

The app is packaged as **one service**: the FastAPI backend serves both the API and
the built React frontend (`app.py` mounts `frontend/dist`), so a single deploy gives
you one URL. This is pure app behavior, independent of *how* it's built — so you can
deploy it with or without Docker; no app code changes either way.

> **Status:** repo is **private**. This URL is for **personal use only** right now — do
> **not** share it publicly until the pre-share bug below is fixed (see "Before sharing").

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
   - `TRADE101_ANALYSIS_KEY` = your Claude API key
   - `TRADE101_NEWS_KEY` = your Finnhub key
   - `TRADE101_MODEL` is pre-filled to `claude-sonnet-5` in `render.yaml`; change if you want.
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
the image; same two env vars, same free-tier behavior.

## Add the link to the repo

Once you have the URL, put it on the repo (GitHub → repo **About** → Website field, or
the README). Ask Claude and it'll add it to the README.

## Before sharing publicly — the pre-share bug (fix at end of Phase 3)

**Every visitor's `/analyze` and `/ask` calls spend YOUR Claude API key.** On a public
URL, a stranger could run up your bill. While the URL is private/personal this is fine,
but **before sharing with anyone**, add access control + cost protection, e.g.:
- a simple shared password / access token gate on the app, and/or
- rate-limiting or a per-day cap on the paid endpoints (`/analyze`, `/ask`), and/or
- a spend cap on the Claude key in the Anthropic console.

This is tracked as the "pre-share" item — do not distribute the link until it's done.

## Local dev is unchanged

Two terminals (`uvicorn ... --reload` + `npm run dev`) still work exactly as before —
in dev the frontend calls `http://127.0.0.1:8000`; in the built/deployed app it calls
the same origin automatically (`api.js` switches on `import.meta.env.DEV`).
