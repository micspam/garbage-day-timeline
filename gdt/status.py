"""`gdt status`: where the run stands at every stage, in one command (read-only)."""
import json
from collections import Counter
from pathlib import Path

from .extract import MAX_QUOTE_WORDS, issue_paths
from .review import quote_numbers, verdicts_for
from .tag import approved

DATA = Path("data")


def slugs(folder: str, ext: str = "json") -> set[str]:
    return {p.stem for p in (DATA / folder).glob(f"*.{ext}")}


def run(limit: int | None):
    issues = [p.stem for p in issue_paths(limit)]
    answers, reviews, tags = slugs("answers"), slugs("reviews"), slugs("tags")

    rejected, too_long = Counter(), []
    awaiting_review, awaiting_tags = [], []
    kept = approved_n = 0
    for slug in issues:
        f = DATA / "extracted" / f"{slug}.json"
        if not f.exists():
            continue
        record = json.loads(f.read_text(encoding="utf-8"))
        rejected.update(r["reason"] for r in record["rejected"])
        numbered = quote_numbers(record)
        kept += len(numbered)
        too_long += [slug for _, q in numbered if len(q["quote"].split()) > MAX_QUOTE_WORDS]
        verdicts = verdicts_for(slug) or {}
        if any(n not in verdicts for n, _ in numbered):
            awaiting_review.append(slug)
        ok = approved(record)
        approved_n += len(ok)
        tagged = set()
        if slug in tags:
            tagged = {t.get("n") for t in json.loads((DATA / "tags" / f"{slug}.json").read_text(encoding="utf-8")).get("tags", [])}
        if any(n not in tagged for n, _ in ok):
            awaiting_tags.append(slug)

    # Prompt files with no answer yet (e.g. an agent skipped one).
    unanswered = {
        "prompts": sorted(slugs("prompts", "txt") - answers),
        "review_prompts": sorted(slugs("review_prompts", "txt") - reviews),
        "tag_prompts": sorted(slugs("tag_prompts", "txt") - tags),
    }

    print(f"issues fetched (readable):  {len(issues)}")
    print(f"  answered (step A):        {len(set(issues) & answers)}   not yet: {len(set(issues) - answers)}")
    print(f"  quotes kept at extract:   {kept}   rejected: {dict(rejected) or 0}")
    print(f"  issues awaiting review:   {len(awaiting_review)}")
    print(f"  quotes approved:          {approved_n}")
    print(f"  issues awaiting tags:     {len(awaiting_tags)}")
    if too_long:
        print(f"  over-long quotes still kept (re-run extract): {sorted(set(too_long))}")
    for folder, missing in unanswered.items():
        if missing:
            print(f"  {folder}/ with no answer file: {len(missing)} -- {', '.join(missing[:8])}{' ...' if len(missing) > 8 else ''}")
    if not (DATA / "issues").exists():
        print("note: data/issues/ is empty -- run `python -m gdt fetch` first")
