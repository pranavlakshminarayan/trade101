# Trade Craft — Deploy (shareable URL)

The app is packaged as **one service**: the FastAPI backend serves both the API and
the built React frontend (`app.py` mounts `frontend/dist`), so a single deploy gives
you one URL. This is pure app behavior, independent of *how* it's built — so you can
deploy it with or without Docker; no app code changes either way.

> **Status:** repo is **private**. The pre-share guard is built into the app (see "Before
> sharing" below), but it's **off until you set `TRADE101_ACCESS_TOKEN`** on the host — treat
> the URL as personal-use only until you've done that.

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
   - Leave `TRADE101_ACCESS_TOKEN` unset for now if you just want a personal link — add it
     later (Render dashboard → your service → Environment) exactly when you're ready to
     share, per "Before sharing publicly" below.
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

## Before sharing publicly — the pre-share guard (built in, 2026-09-15)

**Every visitor's `/analyze` and `/ask` calls spend YOUR Claude API key.** On a public
URL, a stranger could run up your bill. The app now has a built-in guard for this
(`services/access.py`), but it's **off by default** — you turn it on with two env vars
on your host (same place you set `TRADE101_ANALYSIS_KEY`):

- `TRADE101_ACCESS_TOKEN` — pick any secret string. Once set, `/analyze` and `/ask`
  require it (as the `X-Access-Token` header) or they 401. Share the app link once as
  `https://yourapp.onrender.com/?token=<your secret>` — the browser saves it to
  `localStorage` and strips it from the visible URL, so every link after that keeps
  working without the token showing.
- `TRADE101_DAILY_CAP` — max combined `/analyze` + `/ask` calls per day across every
  visitor (default 50 if you don't set it). A backstop even if the token above leaks.

As a last-resort third layer, you can also set a spend cap on the Claude key itself in
the Anthropic console.

**Do not share the link until `TRADE101_ACCESS_TOKEN` is actually set on the host** —
without it, the guard is a no-op and every visitor can trigger paid calls freely.

## Local dev is unchanged

Two terminals (`uvicorn ... --reload` + `npm run dev`) still work exactly as before —
in dev the frontend calls `http://127.0.0.1:8000`; in the built/deployed app it calls
the same origin automatically (`api.js` switches on `import.meta.env.DEV`).
