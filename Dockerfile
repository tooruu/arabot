FROM python:3.13-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk update --no-cache && apk add --no-cache \
    openssl \
    opus \
    ffmpeg

COPY requirements.txt schema.prisma ./

RUN pip install --no-cache-dir -r requirements.txt
RUN --mount=type=secret,id=database-url,env=DATABASE_URL,required=true \
    prisma db push

RUN mv /root/.cache/prisma-python/binaries/*/*/node_modules/prisma/query-engine-* \
    prisma-query-engine-linux-musl && \
    rm -rf \
    /root/.cache \
    /root/.npm \
    /tmp \
    /app/requirements.txt \
    /app/schema.prisma

# `COPY arabot resources ./` copies the *contents* of both folders into workdir
COPY --exclude=requirements.txt --exclude=schema.prisma . .
CMD ["python", "-m", "arabot"]
