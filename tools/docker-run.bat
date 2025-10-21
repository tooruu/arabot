docker rm --force arabot
docker run --env-file=.env --name arabot -it tooruu/arabot:test %*
