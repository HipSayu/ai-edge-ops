class RouteTable:
    """Which upstream serves a path: longest matching prefix wins, the default upstream takes the rest."""

    def __init__(self, routes: dict[str, str], default: str) -> None:
        self._routes = sorted(((p, u.rstrip("/")) for p, u in routes.items()), key=lambda r: -len(r[0]))
        self._default = default.rstrip("/")

    def upstream(self, path: str) -> str:
        for prefix, url in self._routes:
            if path == prefix or path.startswith(f"{prefix}/"):
                return url
        return self._default
