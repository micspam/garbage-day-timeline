"""Aggregate extracted references into the static site's data file and a validation report."""
import json
from collections import Counter
from pathlib import Path

from .extract import MAX_QUOTE_WORDS, issue_paths
from .review import verdicts_for

DATA = Path("data")
SITE = Path("site")


def run(limit: int | None = None):
    # With --limit, build from the same N newest issues as the other steps; otherwise everything extracted.
    paths = [DATA / "extracted" / p.name for p in issue_paths(limit)] if limit else sorted((DATA / "extracted").glob("*.json"))
    records = [json.loads(p.read_text(encoding="utf-8")) for p in paths if p.exists()]
    cards, reasons, review = [], Counter(), Counter()
    dropped = []
    issues_with_cards = 0
    for r in records:
        verdicts = verdicts_for(r["slug"])
        n = 0
        for i, ref in enumerate(r["kept"], 1):
            if len(ref["quote"].split()) > MAX_QUOTE_WORDS:
                reasons["quote_too_long"] += 1
                continue
            # Only reviewed quotes are published; a missing verdict counts as not yet approved.
            v = verdicts.get(i) if verdicts is not None else None
            if not v or not v.get("keep"):
                review["not_reviewed" if not v else "dropped"] += 1
                if v:
                    dropped.append({"quote": ref["quote"], "reason": v.get("reason", ""), "url": r["url"]})
                continue
            review["kept"] += 1
            cards.append({**ref, "url": r["url"], "title": r["title"], "published": r["published"]})
            n += 1
        issues_with_cards += bool(n)
        reasons.update(x["reason"] for x in r["rejected"])

    report = {
        "issues_analyzed": len(records),
        "issues_with_past_references": issues_with_cards,
        "issues_with_none": len(records) - issues_with_cards,
        "references_proposed": len(cards) + sum(reasons.values()) + review["dropped"] + review["not_reviewed"],
        "references_kept": len(cards),
        "references_rejected": dict(reasons.most_common()),  # failed the source checks
        "dropped_in_review": review["dropped"],  # passed the checks, but only mention the era in passing
        "not_reviewed": review["not_reviewed"],
        "fabricated_quotes_possible": 0,  # quotes are copied from source text by code
    }
    SITE.mkdir(exist_ok=True)
    cards.sort(key=lambda c: (c["start_year"], c["published"]))
    (SITE / "data.json").write_text(json.dumps({"report": report, "cards": cards}, ensure_ascii=False, indent=1), encoding="utf-8")
    # Dropped quotes go to data/ (not published) so the review can be spot-checked.
    (DATA / "review_dropped.json").write_text(json.dumps(dropped, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if review["not_reviewed"]:
        print(f"note: {review['not_reviewed']} quotes have no review verdict yet (run `python -m gdt review`)")
