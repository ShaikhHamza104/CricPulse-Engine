# =========================================================================
# Production Multi-Stage Dockerfile for CricPulse IPL Analytics API
# =========================================================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency manifests
COPY pyproject.toml uv.lock ./

# Install production dependencies into virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source and required metadata
COPY src ./src
COPY data ./data
COPY README.md .flake8 ./

# Sync project installation
RUN uv sync --frozen --no-dev

# =========================================================================
# Runtime Stage: Minimal production image
# =========================================================================
FROM python:3.13-slim AS runner

WORKDIR /app

# Create unprivileged system user for container security
RUN groupadd -r appgroup && useradd -r -g appgroup -s /bin/bash appuser

# Copy virtual environment and project from builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/src /app/src
COPY --from=builder --chown=appuser:appgroup /app/data /app/data

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "ipl_analytics.main:app", "--host", "0.0.0.0", "--port", "8000"]
