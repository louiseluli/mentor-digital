# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements-prod.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-prod.txt


# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copia apenas os pacotes instalados (sem pip, setuptools, etc.)
COPY --from=builder /install /usr/local

# Código fonte — sem testes, sem .env, sem venv
COPY src/ ./src/

# Railway injeta PORT automaticamente; fallback para 8000 em outros ambientes
ENV PORT=8000
EXPOSE 8000

# Executa com shell para expandir $PORT em tempo de execução
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]
