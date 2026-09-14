# Trade Craft — single-service image: build the React frontend, then run the
# FastAPI backend which serves BOTH the API and the built frontend on one port.

# 1) Build the frontend
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 2) Python runtime — API + static frontend
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/
COPY --from=web /web/dist ./frontend/dist
# API keys are provided by the host as env vars (never baked into the image):
#   TRADE101_ANALYSIS_KEY, TRADE101_NEWS_KEY, optional TRADE101_MODEL
ENV PORT=8000
EXPOSE 8000
WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
