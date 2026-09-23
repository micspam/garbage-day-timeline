"""Aggregate extracted references into the static site's data file and a validation report."""
import json
from collections import Counter
from pathlib import Path

from .extract import MAX_QUOTE_WORDS

DATA = Path("data")
SITE = Path("site")


def run():
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA / "extracted").glob("*.json"))]
    cards, reasons = [], Counter()
    issues_with_cards = 0
    for r in records:
        n = 0
        for ref in r["kept"]:
            if len(ref["quote"].split()) > MAX_QUOTE_WORDS:
                reasons["quote_too_long"] += 1
                continue
            cards.append({**ref, "url": r["url"], "title": r["title"], "published": r["published"]})
            n += 1
        issues_with_cards += bool(n)
        reasons.update(x["reason"] for x in r["rejected"])

    proposed = len(cards) + sum(reasons.values())
    report = {
        "issues_analyzed": len(records),
        "issues_with_past_references": issues_with_cards,
        "issues_with_none": len(records) - issues_with_cards,
        "references_proposed": proposed,
        "references_kept": len(cards),
        "references_rejected": dict(reasons.most_common()),
        "fabricated_quotes_possible": 0,  # quotes are copied from source text by code
    }
    SITE.mkdir(exist_ok=True)
    cards.sort(key=lambda c: (c["start_year"], c["published"]))
    (SITE / "data.json").write_text(json.dumps({"report": report, "cards": cards}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=2))
