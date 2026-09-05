
#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5000}"

# Use the lightweight bootstrap so Replit health checks receive HTTP 200
# immediately while the full geospatial/ML API stays lazy until first use.
exec uvicorn bootstrap_api:app --app-dir src --host 0.0.0.0 --port "$PORT"
