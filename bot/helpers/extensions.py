from os import walk
from os.path import basename


def load_ext(client):
    for path, _, files in walk("bot/cogs"):
        path = path.split("/")
        if basename(path[-1])[0] != "_":
            for cog in files:
                if cog[0] != "_" and cog.endswith(".py"):
                    module = f"{'.'.join(path)}.{cog[:-3]}"
                    client.load_extension(module)
                    print("Loaded " + module)
