from os import walk
from os.path import basename


def load_ext(client):
    for path, _, files in walk("bot/cogs"):
        if basename(path := path[4:])[0] != "_":
            path = path.replace("/", ".").replace("\\", ".") + "."
            for cog in files:
                if cog[0] != "_" and cog.endswith(".py"):
                    client.load_extension(path + cog[:-3])
                    print(f"Loaded {path}{cog[:-3]}")
