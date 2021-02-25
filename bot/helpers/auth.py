from os import environ


def getenv(*keys):
    if environ.get("token"):
        if len(keys) == 1:
            return environ.get(keys[0])
        key = [environ.get(k) for k in keys]
        return key if all(key) else None
    try:
        with open("./.env") as s:
            secret = {line.partition("=")[0]: line.partition("=")[-1] for line in s.read().splitlines()}
    except FileNotFoundError:
        return None
    if len(keys) == 1:
        return secret.get(keys[0])
    key = [secret.get(k) for k in keys]
    return key if all(key) else None


def req_auth(*api_keys):
    def wrapper(setup):
        def dpy_setup(client):
            if key := getenv(*api_keys):
                setup(client, key)
            else:
                print(f"{api_keys} key(s) not present on the system")

        return dpy_setup

    return wrapper
