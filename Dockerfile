FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY app ./app
COPY framework ./framework

RUN pip install --no-cache-dir . && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser && mkdir -p /app/data && chown -R appuser /app/data
USER appuser

ENV PORT=8000
EXPOSE 8000

# X-Forwarded-Proto bypasses the FORCE_HTTPS redirect; without it curl -f gets a
# 302 and Docker reads that as a healthy response anyway.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD curl -f -H "X-Forwarded-Proto: https" http://localhost:8000/health || exit 1

CMD ["python", "-m", "app.run"]
