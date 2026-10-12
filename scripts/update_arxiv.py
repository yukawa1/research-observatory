#!/usr/bin/env python3
"""Daily, dependency-free arXiv metadata ingestion for Research Observatory.

Automatic entries stay 'metadata_only' and never invent scientific findings.
Run: python scripts/update_arxiv.py --dry-run
"""
import argparse
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "data" / "papers.json"
TOPICS = ROOT / "config" / "topics.json"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
USER_AGENT = "ResearchObservatory/0.1 (academic metadata discovery; https://github.com/yukawa1/research-observatory)"
LIMIT = 100
MAX_NEW = 25


def score(text, config):
    low = text.lower()
    return sum(weight for keyword, weight in config["keywords"] if keyword.lower() in low)


def plain(text):
    return re.sub(r"\s+", " ", text or "").strip()


def fetch_entries(config, days):
    categories = " OR ".join("cat:" + c for c in config["categories"])
    params = urllib.parse.urlencode({"search_query": f"({categories})", "start": 0, "max_results": LIMIT, "sortBy": "submittedDate", "sortOrder": "descending"})
    url = "https://export.arxiv.org/api/query?" + params
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/atom+xml"})
    with urllib.request.urlopen(req, timeout=40) as response:
        root = ET.fromstring(response.read())
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    for entry in root.findall(ATOM + "entry"):
        raw_id = plain(entry.findtext(ATOM + "id"))
        match = re.search(r"/abs/([^/?]+)", raw_id)
        if not match:
            continue
        identifier = re.sub(r"v\d+$", "", match.group(1))
        published = plain(entry.findtext(ATOM + "published"))
        updated = plain(entry.findtext(ATOM + "updated"))
        try:
            published_at = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
            updated_at = dt.datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except ValueError:
            continue
        if max(published_at, updated_at) < cutoff:
            continue
        title = plain(entry.findtext(ATOM + "title"))
        abstract = plain(entry.findtext(ATOM + "summary"))
        authors = [plain(a.findtext(ATOM + "name")) for a in entry.findall(ATOM + "author")]
        categories = [c.get("term", "") for c in entry.findall(ATOM + "category")]
        primary = entry.find(ARXIV + "primary_category")
        category = primary.get("term", categories[0] if categories else "") if primary is not None else (categories[0] if categories else "")
        tags = [key for key, weight in config["keywords"] if key.lower() in (title + " " + abstract).lower() and weight >= 4][:5]
        rank = score(title + " " + abstract, config)
        if rank < config["min_score"]:
            continue
        yield {
            "id": identifier,
            "title": title,
            "authors": authors,
            "published": published_at.date().isoformat(),
            "updated": updated_at.date().isoformat(),
            "category": category,
            "categories": categories,
            "topic": "agn",
            "tags": tags or ["AGN"],
            "score": rank,
            "status": "Preprint / verify journal status",
            "version": int(re.search(r"v(\d+)$", match.group(1)).group(1)) if re.search(r"v(\d+)$", match.group(1)) else 1,
            "review_status": "metadata_only",
            "evidence_level": "arXiv abstract (unreviewed)",
            "link": "https://arxiv.org/abs/" + identifier,
            "abstract": abstract,
            "lay_summary": "",
            "scientific_summary": "",
            "caveat": "",
            "reference": ", ".join(authors[:3]) + (" et al." if len(authors)>3 else "") + f" ({published_at.year}), arXiv:{identifier}."
        }


def merge(existing, incoming):
    current = {p["id"]: p for p in existing}
    added = changed = 0
    for p in incoming:
        old = current.get(p["id"])
        if old is None:
            current[p["id"]] = p
            added += 1
        elif p["version"] > old.get("version", 0) or p["updated"] > old.get("updated", ""):
            # Preserve all editorial fields and analysis; update version and metadata only.
            for key in ("title", "authors", "published", "updated", "category", "categories", "version", "link", "abstract"):
                old[key] = p[key]
            changed += 1
    output = sorted(current.values(), key=lambda p: (p["published"], p.get("score", 0)), reverse=True)
    return output, added, changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    topics = json.loads(TOPICS.read_text(encoding="utf-8"))
    previous = json.loads(DATA.read_text(encoding="utf-8"))
    fresh = []
    for topic, config in topics.items():
        try:
            matches = list(fetch_entries(config, args.days))
            for p in matches:
                p["topic"] = topic
            fresh.extend(matches)
        except (OSError, TimeoutError, ET.ParseError) as exc:
            raise SystemExit(f"arXiv fetch failed for {topic}; existing archive left untouched: {exc}")
        time.sleep(3)
    fresh.sort(key=lambda p: (p["published"], p["score"]), reverse=True)
    archive, added, changed = merge(previous, fresh[:MAX_NEW])
    if not args.dry_run:
        DATA.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Matched {len(fresh)} recent records, added {added}, updated {changed}, total {len(archive)}. dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
