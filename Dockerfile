# ===========================================================
# IEMS — Multi-stage Dockerfile
# ===========================================================
# Stage 1: Build the React frontend
# Stage 2: Python backend serving the SPA + API
# ===========================================================

# ---- Stage 1: Frontend build ----
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Backend + static files ----
FROM python:3.12-slim AS runtime
LABEL maintainer="IEMS Team"

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN addgroup --system iems && adduser --system --ingroup iems iems

WORKDIR /app

# Python deps
COPY backend/requirements-prod.txt ./requirements-prod.txt
RUN pip install --no-cache-dir -r requirements-prod.txt

# Backend source
COPY backend/ ./backend/

# Pre-built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
RUN test -f /app/frontend/dist/index.html

# Uploads volume
RUN mkdir -p /app/uploads && chown -R iems:iems /app/uploads
VOLUME ["/app/uploads"]

# Switch to non-root
USER iems

# Env defaults (override at runtime / docker-compose)
ENV MONGO_URL=mongodb://mongo:27017 \
    DB_NAME=iems_db \
    UPLOAD_DIR=/app/uploads \
    CORS_ORIGINS=http://localhost:3000

EXPOSE 8000

# Liveness probe hits /health/live (canonical FastAPI route). Readiness lives
# at /health/ready and is exercised by the deploy workflow, not the Docker
# healthcheck, because it depends on Mongo connectivity.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

WORKDIR /app/backend
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
