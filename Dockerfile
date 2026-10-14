FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./

# https://docs.railway.com/builds/dockerfiles#cache-mounts
RUN --mount=type=cache,id=s/aa94b290-bdcf-48d6-b677-26f8335691ae-/root/.cache/uv,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY . .

RUN --mount=type=cache,id=s/aa94b290-bdcf-48d6-b677-26f8335691ae-/root/.cache/uv,target=/root/.cache/uv \
    uv sync --locked


FROM python:3.14-alpine

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN addgroup -S appgroup \
    && adduser -SG appgroup appuser \
    && apk add --no-cache ffmpeg openssl opus

USER appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /app /app

CMD ["python", "-m", "arabot"]
