"""Upload a POS CSV to a running API (the "CSV Ingestion" box in the architecture diagram).

    python -m app.generator.generate_mock_pos --days 14 --phantom s1 --out mock_pos.csv
    python -m app.generator.load_csv mock_pos.csv --api http://localhost:8000

CSV header: timestamp,sku_id,quantity,unit_price[,store_id]. Sent in chunks of --rows rows so large
files don't hit request limits.
"""
import argparse
from collections.abc import Callable
from pathlib import Path


def load(path: Path, post: Callable[[str], dict], rows_per_chunk: int = 5000) -> dict:
    """`post(csv_text)` must return the endpoint's JSON ({ingested, rejected, errors})."""
    lines = path.read_text().splitlines()
    header, body = lines[0], lines[1:]
    total = {"ingested": 0, "rejected": 0, "errors": []}
    for i in range(0, len(body), rows_per_chunk):
        res = post("\n".join([header, *body[i:i + rows_per_chunk]]) + "\n")
        total["ingested"] += res["ingested"]
        total["rejected"] += res["rejected"]
        total["errors"] += [{**e, "index": e["index"] + i} for e in res["errors"]]  # index in the whole file
    return total


def main(argv: list[str] | None = None) -> int:
    import httpx

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", type=Path)
    p.add_argument("--api", default="http://localhost:8000")
    p.add_argument("--rows", type=int, default=5000, help="rows per request")
    a = p.parse_args(argv)

    def post(text: str) -> dict:
        r = httpx.post(f"{a.api}/api/v1/pos/stream/csv", content=text, headers={"Content-Type": "text/csv"},
                       timeout=120)
        if r.status_code not in (200, 422) or "ingested" not in r.json():
            raise SystemExit(f"{r.status_code}: {r.text[:300]}")
        return r.json()

    result = load(a.csv, post, a.rows)
    print(f"ingested {result['ingested']}, rejected {result['rejected']}")
    for e in result["errors"][:10]:
        print(f"  row {e['index'] + 1}: {e['message']}")
    return 0 if result["ingested"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
