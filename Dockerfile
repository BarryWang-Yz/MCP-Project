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

