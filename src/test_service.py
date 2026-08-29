import json

from satquery_service import (
    execute_query,
)


query = (
    "Analyze vegetation health "
    "for Varanasi on 2026-02-10"
)

response = execute_query(
    query
)

print(
    json.dumps(
        response,
        indent=4,
    )
)