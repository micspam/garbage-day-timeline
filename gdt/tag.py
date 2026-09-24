"""Open-ended tagging of approved quotes, as raw material for discovering categories later.

Two kinds of tag:
- Judgments (`moment`, `topics`): free text in the model's own words. Nothing to verify, and
  deliberately not from a fixed list yet -- `gdt vocab` counts them so categories can emerge.
- Facts (`entities`, `platforms`, `audiences`): each needs an exact phrase from the quote's
  paragraph. A fact tag without one is dropped, the same rule the dates follow.
"""
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from .extract import call_claude, issue_paths, norm
from .review import verdicts_for

DATA = Path("data")
FACT_FIELDS = ("entities", "platforms", "audiences")

_fact = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "evidence": {"type": "string"}},
    "required": ["name", "evidence"],
}
TOOL = {
    "name": "record_tags",
    "description": "Record descriptive tags for each numbered quote.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "n": {"type": "integer"},
                        "moment": {"type": "string"},
                        "topics": {"type": "array", "items": {"type": "string"}},
                        "entities": {"type": "array", "items": {**_fact, "properties": {**_fact["properties"], "kind": {"type": "string"}}}},
                        "platforms": {"type": "array", "items": _fact},
                        "audiences": {"type": "array", "items": _fact},
                    },
                    "required": ["n", "moment", "topics", "entities", "platforms", "audiences"],
                },
            }
        },
        "required": ["tags"],
    },
}

PROMPT = """Tag each numbered quote from the newsletter Garbage Day. The tags will be counted across hundreds of quotes to discover natural categories, so describe things plainly and consistently, in lowercase, using the most common name for each thing.

For each quote:
- `moment`: what kind of thing the quote describes, in 2-4 words (e.g. "viral dance trend", "platform shutdown", "news leak", "reaction to a news story", "subculture forming").
- `topics`: 1-4 short subject areas (e.g. "dance", "far-right politics", "fandom", "video games").
- `entities`: specific people, companies, communities, works, events or media outlets named in the text. Give each a `name` (full common name, e.g. "jeffrey epstein", "cnn"), a `kind` (person, company, community, work, event, media outlet, other) and `evidence`.
- `platforms`: online platforms the moment happened on or spread through (e.g. "tiktok", "4chan"), each with `evidence`.
- `audiences`: groups the moment involved or was popular with (e.g. "gen alpha", "millennials", "gamers"), each with `evidence`.

`evidence` must be an exact phrase copied from the quote's context paragraph that shows the tag is true. If you can't point to one, leave the tag out. Guessing an audience or a platform the text doesn't mention is worse than leaving it empty. Empty lists are fine.

Answer format:
{{"tags": [{{"n": 1, "moment": "...", "topics": ["..."], "entities": [{{"name": "...", "kind": "...", "evidence": "..."}}], "platforms": [{{"name": "...", "evidence": "..."}}], "audiences": [{{"name": "...", "evidence": "..."}}]}}]}}

{quotes}"""


def approved(record: dict) -> list[tuple[int, dict]]:
    """(quote number, quote) for quotes that passed review, numbered as in the review step."""
    verdicts = verdicts_for(record["slug"]) or {}
    return [(n, q) for n, q in enumerate(record["kept"], 1) if verdicts.get(n, {}).get("keep")]


def load_pair(slug: str) -> tuple[dict, dict] | None:
    ex, iss = DATA / "extracted" / f"{slug}.json", DATA / "issues" / f"{slug}.json"
    if not ex.exists() or not iss.exists():
        return None
    return json.loads(ex.read_text(encoding="utf-8")), json.loads(iss.read_text(encoding="utf-8"))


def build_prompt(record: dict, issue: dict) -> str:
    quotes = "\n\n".join(
        f"[{n}] Quote: \"{q['quote']}\"\nContext paragraph: \"{issue['paragraphs'][q['paragraph']]}\""
        for n, q in approved(record)
    )
    return PROMPT.format(quotes=quotes)


def run(limit: int | None):
    """Write tag prompts for a Claude Code session, or answer them via the API if a key is set."""
    prompt_dir, tag_dir = DATA / "tag_prompts", DATA / "tags"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for old in prompt_dir.glob("*.txt"):  # only outstanding prompts stay in the folder
        old.unlink()
    tag_dir.mkdir(parents=True, exist_ok=True)
    use_api = "ANTHROPIC_API_KEY" in os.environ
    todo = 0
    for p in issue_paths(limit):
        pair = load_pair(p.stem)
        if not pair or not approved(pair[0]) or (tag_dir / p.name).exists():
            continue
        prompt = build_prompt(*pair)
        if use_api:
            answer = call_claude(prompt, TOOL)
            (tag_dir / p.name).write_text(json.dumps(answer, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {p.stem}: tagged")
        else:
            (prompt_dir / f"{p.stem}.txt").write_text(prompt, encoding="utf-8")
            todo += 1
    if not use_api:
        print(f"{todo} tag prompts in {prompt_dir}/ need answers in {tag_dir}/<same name>.json")


def clean_name(s: str) -> str:
    return " ".join(str(s).lower().split())


def checked_tags(record: dict, issue: dict, stats: Counter | None = None) -> dict[int, dict]:
    """Quote number -> tags, keeping only fact tags whose evidence is in the quote's paragraph."""
    f = DATA / "tags" / f"{record['slug']}.json"
    if not f.exists():
        return {}
    quotes = dict(approved(record))
    out = {}
    for t in json.loads(f.read_text(encoding="utf-8")).get("tags", []):
        q = quotes.get(t.get("n"))
        if not q:
            continue
        para = norm(issue["paragraphs"][q["paragraph"]])
        tags = {"moment": clean_name(t.get("moment", "")), "topics": [clean_name(x) for x in t.get("topics", []) if str(x).strip()]}
        for field in FACT_FIELDS:
            tags[field] = []
            for fact in t.get(field, []):
                ev = norm(str(fact.get("evidence", "")))
                ok = len(ev) >= 2 and ev in para
                if stats is not None:
                    stats[f"{field}_{'kept' if ok else 'dropped_no_evidence'}"] += 1
                if ok:
                    entry = {"name": clean_name(fact.get("name", ""))}
                    if field == "entities":
                        entry["kind"] = clean_name(fact.get("kind", "other"))
                    tags[field].append(entry)
        out[t["n"]] = tags
    return out


def vocab(limit: int | None):
    """Count every tag value across tagged quotes -> data/vocab.json, to discover categories."""
    counts: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"quotes": 0, "issues": set(), "eras": set()}))
    stats, tagged = Counter(), 0
    for p in issue_paths(limit):
        pair = load_pair(p.stem)
        if not pair:
            continue
        record, issue = pair
        quotes = dict(approved(record))
        for n, tags in checked_tags(record, issue, stats).items():
            tagged += 1
            era = quotes[n]["start_year"] // 5 * 5
            values = [("moment", tags["moment"])] + [("topics", t) for t in tags["topics"]]
            values += [(f, x["name"]) for f in FACT_FIELDS for x in tags[f]]
            for field, value in values:
                if not value:
                    continue
                c = counts[field][value]
                c["quotes"] += 1
                c["issues"].add(record["slug"])
                c["eras"].add(era)

    out = {"tagged_quotes": tagged, "evidence_checks": dict(stats), "fields": {}}
    for field, values in counts.items():
        rows = [{"value": v, "quotes": c["quotes"], "issues": len(c["issues"]), "eras": len(c["eras"])} for v, c in values.items()]
        out["fields"][field] = sorted(rows, key=lambda r: (-r["quotes"], r["value"]))
    (DATA / "vocab.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{tagged} tagged quotes; evidence checks: {dict(stats)}")
    for field, rows in out["fields"].items():
        top = ", ".join(f"{r['value']} ({r['quotes']})" for r in rows[:12])
        print(f"  {field}: {len(rows)} distinct -- {top}")
