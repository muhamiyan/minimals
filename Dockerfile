# --- frontend build -------------------------------------------------------
FROM node:22-slim AS frontend

WORKDIR /build

COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile

COPY frontend .
RUN yarn build


# --- runtime --------------------------------------------------------------
FROM python:3.11-slim

ARG APP_UID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Dependencies first so a code change does not reinstall the whole tree.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY framework ./framework
RUN uv sync --frozen --no-dev

# Always the freshly built assets, never a stale local build directory.
COPY --from=frontend /build/app/static/frontend ./app/static/frontend

RUN useradd -m -u "${APP_UID}" appuser && \
    mkdir -p /app/data /app/app/static/uploads && \
    chown -R appuser /app/data /app/app/static/uploads

USER appuser

ENV PORT=8000
EXPOSE 8000

# /ready touches the database, so a broken connection fails the check instead
# of reporting a healthy container that only serves 500s.
# X-Forwarded-Proto bypasses the FORCE_HTTPS redirect; without it curl -f gets a
# 302 and Docker reads that as a healthy response anyway.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f -H "X-Forwarded-Proto: https" http://localhost:8000/ready || exit 1

CMD ["python", "-m", "app.run"]
