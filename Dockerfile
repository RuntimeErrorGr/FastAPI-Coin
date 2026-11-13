FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /bin/uv

ARG APP_UID=1000
RUN useradd --create-home --uid ${APP_UID} app

WORKDIR /app
RUN chown app:app /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

FROM base AS test

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --extra dev

COPY --chown=app:app ./app ./app
COPY --chown=app:app ./tests ./tests

USER app

ENTRYPOINT ["pytest"]

FROM base AS dev

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY --chown=app:app ./app ./app

USER app

ENTRYPOINT ["python", "-m", "app.server"]
