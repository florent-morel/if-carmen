# syntax=docker/dockerfile:1

# ── Base: Python 3.12 + Node.js 22 LTS ──────────────────────────────────────
FROM python:3.11-slim AS base

ARG USER_UID=1000
ARG USER_GID=1000
ARG APP_USER=dev

ENV NODE_VERSION=18
ENV NODE_NO_WARNINGS=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV USERNAME=$APP_USER

RUN apt-get update \
    && apt-get install -y --no-install-recommends git sudo curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create user matching host UID/GID
RUN groupadd --gid $USER_GID $APP_USER \
    && useradd --uid $USER_UID --gid $USER_GID --shell /bin/bash --create-home $APP_USER \
    && echo "$APP_USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install Node.js 22 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pre-commit

RUN mkdir -p /app && chown $APP_USER:$APP_USER /app

WORKDIR /app
USER $APP_USER

# ── Development stage ─────────────────────────────────────────────────────────
FROM base AS development

COPY --chown=$USERNAME pyproject.toml package.json ./
RUN pip install --no-cache-dir -e '.[all]' || true \
    && npm install

COPY --chown=$USERNAME . .
RUN pip install --no-cache-dir -e '.[all]'
