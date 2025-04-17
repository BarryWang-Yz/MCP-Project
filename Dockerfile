# ─── Builder stage ───────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv \
 && uv sync

COPY . .
# (You can omit CMD here; only the final stage’s CMD is used.)

# ─── Final (runtime) stage ───────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Copy the synced virtualenv from the builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

COPY . .

# This is the one Docker will actually use
CMD ["uv", "run", "server.py"]
