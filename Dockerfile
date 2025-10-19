FROM python:3.13-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk update && apk add \
    openssl \
    ffmpeg

COPY resources/gacha_py-2.0.0-py3-none-any.whl resources/
COPY requirements.txt schema.prisma ./
RUN pip install -r requirements.txt

RUN --mount=type=secret,target=.env \
    prisma db push

COPY . .
CMD ["python", "-m", "arabot"]
