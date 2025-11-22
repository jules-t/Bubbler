"""Quick status report of available data sources and what fed into bubble_data.json."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

import duckdb

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db" / "redit_pipeline.duckdb"
BUBBLE_JSON = BASE_DIR / "outputs" / "bubble_data.json"


def table_row_counts(con: duckdb.DuckDBPyConnection) -> Dict[str, int]:
    """Return row counts for known tables, if they exist."""
    tables = [
        "ai_bubble_data.reddit_posts",
        "ai_bubble_data.rss_ai_news",
        "ai_bubble_data.google_trends_interest",
        "ai_bubble_data.newsapi_ai_news",
        "ai_bubble_data.fred_macro",
        "ai_bubble_data.alpha_vantage_overview",
        "ai_bubble_data.ai_equity_history",
    ]
    counts: Dict[str, int] = {}
    for table in tables:
        try:
            counts[table] = con.execute(f"select count(*) from {table}").fetchone()[0]
        except Exception:
            counts[table] = 0
    return counts


def bubble_json_breakdown(path: Path) -> Dict[str, Dict[str, int]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    by_category = Counter()
    sample_titles = defaultdict(list)
    for item in data:
        cat = item.get("category", "unknown")
        by_category[cat] += 1
        if len(sample_titles[cat]) < 3 and item.get("title"):
            sample_titles[cat].append(item["title"])
    return {"counts": dict(by_category), "samples": {k: v for k, v in sample_titles.items()}}


def main() -> None:
    print(f"Checking DuckDB at: {DB_PATH}")
    if not DB_PATH.exists():
        print("DuckDB file not found.")
    else:
        con = duckdb.connect(DB_PATH)
        counts = table_row_counts(con)
        print("Table row counts:")
        for tbl, cnt in counts.items():
            status = "OK" if cnt > 0 else "EMPTY/MISSING"
            print(f"  - {tbl}: {cnt} rows ({status})")

    print(f"\nChecking bubble_data.json at: {BUBBLE_JSON}")
    breakdown = bubble_json_breakdown(BUBBLE_JSON)
    if not breakdown:
        print("bubble_data.json not found or empty.")
    else:
        print("bubble_data.json category counts:")
        for cat, cnt in breakdown["counts"].items():
            print(f"  - {cat}: {cnt}")
        print("Sample titles (up to 3 per category):")
        for cat, titles in breakdown["samples"].items():
            print(f"  - {cat}:")
            for t in titles:
                print(f"      * {t}")


if __name__ == "__main__":
    main()
