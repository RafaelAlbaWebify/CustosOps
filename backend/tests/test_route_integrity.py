from collections import Counter

from app.main import app


def test_api_routes_are_not_registered_more_than_once():
    route_keys = []

    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set())

        if not path.startswith("/api/"):
            continue

        normalized_methods = tuple(sorted(method for method in methods if method not in {"HEAD", "OPTIONS"}))
        route_keys.append((path, normalized_methods))

    counts = Counter(route_keys)
    duplicates = [f"{path} {methods}" for (path, methods), count in counts.items() if count > 1]

    assert duplicates == []
