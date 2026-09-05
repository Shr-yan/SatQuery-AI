from __future__ import annotations

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 20


CHECKS = [
    ("/health", "status", "healthy"),
    ("/ready", "ready", True),
    ("/model-registry", "success", True),
    ("/evaluation-center-data", "success", True),
    ("/runtime-status", "success", True),
]


def fetch_json(url: str) -> dict:
    with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        raw = response.read().decode("utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise RuntimeError("Expected a JSON object.")
    return value


def main() -> int:
    base_url = (
        sys.argv[1].rstrip("/")
        if len(sys.argv) > 1
        else DEFAULT_BASE_URL
    )

    print(f"SatQuery deployment smoke test: {base_url}")
    failures = 0

    for path, field, expected in CHECKS:
        url = base_url + path
        try:
            data = fetch_json(url)
            actual = data.get(field)
            if actual != expected:
                failures += 1
                print(
                    f"  FAIL {path} -> {field}={actual!r}; "
                    f"expected {expected!r}"
                )
            else:
                print(f"  PASS {path} -> {actual}")
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            failures += 1
            print(f"  FAIL {path} -> {exc}")

    if failures:
        print(f"FAILED: {failures} deployment check(s) did not pass.")
        return 1

    print("DONE: deployment-facing endpoints are responding and release-ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
