# # ─── Builder stage ───────────────────────────────────────────────────────────
# FROM python:3.11-slim AS builder
# WORKDIR /app

# COPY pyproject.toml uv.lock ./
# RUN pip install uv \
#  && uv sync

# COPY . .
# # (You can omit CMD here; only the final stage’s CMD is used.)

# # ─── Final (runtime) stage ───────────────────────────────────────────────────
# FROM python:3.11-slim
# WORKDIR /app

# # Copy the synced virtualenv from the builder
# COPY --from=builder /app/.venv /app/.venv
# ENV PATH="/app/.venv/bin:${PATH}"

# COPY . .

# # This is the one Docker will actually use
# CMD ["uv", "run", "server.py"]


# ─── Builder stage ─────────────────────
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN pip install pip-tools \
 && pip install -r requirements.txt

COPY . .

# ─── Final stage ───────────────────────
FROM python:3.11-slim
WORKDIR /app

# Copy virtualenv
COPY --from=builder /app/.venv /opt/.venv
ENV PATH="/opt/.venv/bin:${PATH}"

COPY . .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

