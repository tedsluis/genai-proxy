# ==== Build stage ====
FROM python:3.12-slim AS builder

WORKDIR /app

# Zorg voor snellere/kleinere wheels
RUN pip install --upgrade pip wheel
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ==== Runtime stage ====
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Defaults: pas eventueel aan via -e bij podman run
    GENAI_SUBSCRIPTION_NAME=some-subscription-name \
    GENAI_API_KEY=some-api-key \
    GENAI_BASE_URL="https://genai.example.com" \
    REQUEST_TIMEOUT="60" \
    MAX_RETRIES="2" \
    RETRY_BACKOFF_SEC="0.5" \
    LOG_BODIES="true" \
    LOG_STREAM_MAX_BYTES="0" \
    ALLOWED_ORIGINS=""

WORKDIR /app

# Install wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy app
COPY main.py .

# Note: models.yaml is expected at runtime in /app/models.yaml.
# Mount it in containers, for example:
#   podman run -v $PWD/models.yaml:/app/models.yaml:ro ... genai-proxy:latest

# Corporate proxy support:
#   Set HTTPS_PROXY to route outbound traffic via a corporate proxy (no auth).
#   Example:
#     podman run -e HTTPS_PROXY=http://proxy.domain.org:8080 ... genai-proxy:latest

# (optioneel) non-root user
RUN useradd -u 10001 appuser
USER appuser

EXPOSE 8111

# Start Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8111", "--proxy-headers"]
