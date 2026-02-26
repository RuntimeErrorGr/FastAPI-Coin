FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV PYTHONUNBUFFERED=1 
ENV PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml uv.lock ./

FROM base AS test

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --extra dev

COPY ./app ./app
COPY ./tests ./tests

ENTRYPOINT ["uv", "run", "pytest"]

FROM base AS dev

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY ./app ./app

ENTRYPOINT ["uv", "run", "python", "-m", "app.server"]