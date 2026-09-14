# Trade Craft — Deploy (shareable URL)

The app is packaged as **one service**: the FastAPI backend serves both the API and
the built React frontend, so a single deploy gives you one URL. Config: `Dockerfile`
(multi-stage: builds the frontend, then runs the backend) + `.dockerignore`.

> **Status:** repo is **private**. This URL is for **personal use only** right now — do
> **not** share it publicly until the pre-share bug below is fixed (see "Before sharing").

## Deploy it (one time, ~10 min)

Any host that builds a Dockerfile works. **Render** is the simplest:

1. Push this repo to GitHub (already done; it's private).
2. Go to <https://render.com> → sign up / log in (your account).
3. **New → Web Service** → connect the `trade101` repo.
4. Render auto-detects the `Dockerfile`. Instance type: **Free** is fine to start.
5. Under **Environment**, add your keys (same names as local `.env`):
   - `TRADE101_ANALYSIS_KEY` = your Claude API key
   - `TRADE101_NEWS_KEY` = your Finnhub key
   - (optional) `TRADE101_MODEL` = `claude-sonnet-5`
   - Do **not** set `PORT` — Render provides it; the app reads `$PORT`.
6. **Create Web Service** → wait for the build → you get a URL like
   `https://trade-craft.onrender.com`. That's your shareable link.

(Fly.io / Railway work the same way — point them at the Dockerfile and set the two
env vars. Render's free tier sleeps after ~15 min idle, so the first hit after a nap
is slow; that's normal.)

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
