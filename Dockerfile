# Étape de build pour le frontend
FROM node:18-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend .
RUN npm run build

# Étape de build pour le backend
FROM python:3.10-slim as backend-builder
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Étape finale
FROM python:3.10-slim
WORKDIR /app
EXPOSE 5000

# Copie des artefacts de build
COPY --from=backend-builder /root/.local /root/.local
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
COPY . .

# Configuration sécurité
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --disabled-password --gecos '' krediuser && \
    chown -R krediuser:krediuser /app

USER krediuser
ENV PATH=/root/.local/bin:$PATH \
    FLASK_APP=app.py \
    FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "app:app"]
