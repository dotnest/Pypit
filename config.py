import json

def write(config):
    """Write config to a file."""
    with open("config.json", "w") as f:
        f.write(json.dumps(config, indent=4, sort_keys=True))


def load():
    """Read config from a file."""
    with open("config.json", "r") as f:
        return json.load(f)
