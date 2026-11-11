# syntax=docker/dockerfile:1
# Frise — image de la sonde d'Immich (étape 0). Tourne une fois, écrit un rapport, s'arrête.
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /venv
COPY requirements.txt .
RUN /venv/bin/pip install -r requirements.txt

FROM python:3.12-slim
ARG VERSION=dev
LABEL org.opencontainers.image.source="https://github.com/baloodusudouest/frise" \
      org.opencontainers.image.description="Frise — sonde d'Immich en lecture seule (étape 0)" \
      org.opencontainers.image.version="${VERSION}"
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH" \
    DATA_DIR=/data
COPY --from=builder /venv /venv
WORKDIR /app
COPY sonde.py /app/sonde.py
RUN mkdir -p /data
VOLUME ["/data"]
CMD ["python", "/app/sonde.py"]
