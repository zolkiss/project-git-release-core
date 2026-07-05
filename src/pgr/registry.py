from importlib.metadata import entry_points

from pgr import Connector


def get_connector(name: str) -> type[Connector]:
    eps = entry_points(group="pgr.connectors")
    matches = [ep for ep in eps if ep.name == name]
    if not matches:
        raise ValueError(f"No connector named {name!r} registered")
    return matches[0].load()
