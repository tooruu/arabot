FROM ghcr.io/astral-sh/uv:python3.14-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

RUN apk update --no-cache && apk add --no-cache \
    openssl \
    opus \
    ffmpeg

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-cache

RUN rm -rf \
    /root/.cache \
    /root/.npm \
    /tmp/* \
    /app/pyproject.toml \
    /app/uv.lock

COPY arabot arabot
COPY resources resources

CMD ["uv", "run", "-m", "arabot"]
