FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk update --no-cache && apk add --no-cache \
    openssl \
    opus \
    ffmpeg

COPY pyproject.toml uv.lock schema.prisma ./

RUN uv sync --locked --no-cache

RUN --mount=type=secret,id=database-url,env=DATABASE_URL,required=true \
    uv run prisma db push

RUN mv /root/.cache/prisma-python/binaries/*/*/node_modules/prisma/query-engine-* \
    prisma-query-engine-linux-musl && \
    rm -rf \
    /root/.cache \
    /root/.npm \
    /tmp/* \
    /app/pyproject.toml \
    /app/uv.lock \
    /app/schema.prisma

COPY --exclude=pyproject.toml --exclude=uv.lock --exclude=schema.prisma . .
CMD ["uv", "run", "-m", "arabot"]
