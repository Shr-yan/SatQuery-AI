import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

from src.query_parser import parse_query


def test_query_parser():

    query = (
        "Show me Sentinel-2 satellite imagery "
        "for Lucknow from 2026-01-15"
    )

    result = parse_query(query)

    assert result["location"] == "Lucknow"

    assert result["date"] == "2026-01-15"

    assert result["data_type"] == "sentinel-2"

    assert result["request_type"] == "imagery"


if __name__ == "__main__":

    test_query_parser()

    print(
        "All query parser tests passed!"
    )