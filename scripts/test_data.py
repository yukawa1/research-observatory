#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
papers = json.loads((root / "src/data/papers.json").read_text())
topics = json.loads((root / "config/topics.json").read_text())
assert topics, "topic profiles missing"
ids = [p["id"] for p in papers]
assert len(ids) == len(set(ids)), "duplicate arXiv ids"
for p in papers:
    for key in ("id", "title", "authors", "published", "updated", "link", "review_status", "topic"):
        assert p.get(key), f"missing {key}: {p.get('id')}"
    assert p["link"] == "https://arxiv.org/abs/" + p["id"]
    assert p["review_status"] in ("metadata_only", "curated"), p["review_status"]
    if p["review_status"] == "metadata_only":
        assert not p.get("lay_summary") and not p.get("scientific_summary"), "uncurated claims"
print(f"Validated {len(papers)} papers")
