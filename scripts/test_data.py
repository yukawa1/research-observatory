#!/usr/bin/env python3
"""Check that automated abstracts cannot masquerade as detailed analyses."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
papers = json.loads((root / "src/data/papers.json").read_text(encoding="utf-8"))
topics = json.loads((root / "config/topics.json").read_text(encoding="utf-8"))
assert topics, "topic profiles missing"
ids = [p["id"] for p in papers]
assert len(ids) == len(set(ids)), "duplicate arXiv ids"
reviewed = 0
for p in papers:
    for key in ("id", "title", "authors", "published", "updated", "link", "review_status", "topic"):
        assert p.get(key), f"missing {key}: {p.get('id')}"
    assert p["link"] == "https://arxiv.org/abs/" + p["id"]
    assert p["review_status"] in ("metadata_only", "curated"), p["review_status"]
    if p["review_status"] == "metadata_only":
        assert not p.get("lay_summary") and not p.get("scientific_summary"), "uncurated claims"
        assert not p.get("analysis"), f"auto-imported paper has analysis: {p['id']}"
    else:
        reviewed += 1
        assert len(p.get("lay_summary", "")) >= 100, f"short plain-language overview: {p['id']}"
        analysis = p.get("analysis", {})
        for key in ("question", "approach", "interpretation", "limitations", "relevance"):
            assert len(analysis.get(key, "")) >= 80, f"missing detailed {key}: {p['id']}"
        assert len(analysis.get("findings", [])) >= 3, f"too few key results: {p['id']}"
print(f"Validated {len(papers)} papers ({reviewed} detailed analyses)")

# Curated explanations must have an editorial comic with a descriptive alternative text.
for paper in papers:
    if paper.get("review_status") == "curated":
        assert paper.get("comic") == f"comics/{paper['id']}.svg", paper["id"]
        assert len(paper.get("comic_alt", "")) > 25, paper["id"]
    else:
        assert not paper.get("comic"), f"Unreviewed comic: {paper['id']}"

for paper in papers:
    if paper.get("comic"):
        assert paper.get("comic_original") == f"comics/{paper['id']}.png"
