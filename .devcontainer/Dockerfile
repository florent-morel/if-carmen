# syntax=docker/dockerfile:1
 
# ── Base: Python 3.11 + Node.js 18 + uv ─────────────────────────────────────
FROM python:3.11-slim
 
ARG USER_UID=1000
ARG USER_GID=1000
ARG APP_USER=dev
 
ENV NODE_VERSION=18
ENV NODE_NO_WARNINGS=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV USERNAME=$APP_USER
 
RUN apt-get update \
    && apt-get install -y --no-install-recommends git sudo curl ca-certificates lsb-release bash-completion \
    && rm -rf /var/lib/apt/lists/*
 
# Create user matching host UID/GID
RUN groupadd --gid $USER_GID $APP_USER \
    && useradd --uid $USER_UID --gid $USER_GID --shell /bin/bash --create-home $APP_USER \
    && echo "$APP_USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
 
# Install Node.js 18 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*
 
# Install uv
RUN pip install --no-cache-dir uv
 
USER $APP_USER