"""Sanity pass: judge each kept quote on its own, the way a reader of the timeline would see it.

The reviewer sees only the quote and the era it's filed under -- not the rest of the issue --
and decides whether the quote is really about that era or just mentions it in passing.
Build only publishes quotes with a "keep" verdict.
"""
import json
import os
from pathlib import Path

from .extract import call_claude, issue_paths

DATA = Path("data")

TOOL = {
    "name": "record_verdicts",
    "description": "Record a keep/drop verdict for each numbered quote.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "n": {"type": "integer"},
                        "keep": {"type": "boolean"},
                        "reason": {"type": "string", "description": "One short sentence."},
                    },
                    "required": ["n", "keep", "reason"],
                },
            }
        },
        "required": ["verdicts"],
    },
}

PROMPT = """Each quote below will appear alone on a timeline, filed under the era shown. A reader sees just the quote and the era.

Go through this checklist for every quote. Keep it only if the answer to all four is yes:

1. Is the era the subject? Most of the quote describes what happened in that era, or what it was like. It's not mainly about the present, with the past as setup or contrast ("the people who did X in the 2010s now do Y").
2. Is it more than a date stamp? It doesn't just give a background date for a present-day story ("he entered the US in 2019", "the site launched in 2022", "allegations back in 2023").
3. Does it stand alone? A reader who hasn't seen the article understands what it's describing. It doesn't depend on "this", "he" or "that" from earlier, and it isn't a rhetorical question.
4. Is it description, not a take? It isn't mainly someone's opinion about current events that happens to name a past year.

Be strict. A quote that mentions an era is not the same as a quote about an era, and a lenient pass fills the timeline with passing mentions. When unsure, drop it. In the reason, name the first check that failed, or say why it passes all four.

Answer format:
{{"verdicts": [{{"n": 1, "keep": true, "reason": "one short sentence"}}]}}

{quotes}"""


def years(q: dict) -> str:
    return str(q["start_year"]) if q["start_year"] == q["end_year"] else f"{q['start_year']}-{q['end_year']}"


def build_prompt(record: dict) -> str:
    quotes = "\n\n".join(
        f"[{n}] Filed under {years(q)} ({q['label']}):\n\"{q['quote']}\""
        for n, q in enumerate(record["kept"], 1)
    )
    return PROMPT.format(quotes=quotes)


def run(limit: int | None):
    """Write review prompts for a Claude Code session, or answer them via the API if a key is set."""
    prompt_dir, review_dir = DATA / "review_prompts", DATA / "reviews"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for old in prompt_dir.glob("*.txt"):  # only outstanding prompts stay in the folder
        old.unlink()
    review_dir.mkdir(parents=True, exist_ok=True)
    use_api = "ANTHROPIC_API_KEY" in os.environ
    todo = 0
    for p in (DATA / "extracted" / ip.name for ip in issue_paths(limit)):
        if not p.exists():
            continue
        record = json.loads(p.read_text(encoding="utf-8"))
        if not record["kept"] or (review_dir / p.name).exists():
            continue
        prompt = build_prompt(record)
        if use_api:
            verdicts = call_claude(prompt, TOOL)
            (review_dir / p.name).write_text(json.dumps(verdicts, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {p.stem}: reviewed {len(record['kept'])} quotes")
        else:
            (prompt_dir / f"{p.stem}.txt").write_text(prompt, encoding="utf-8")
            todo += 1
    if not use_api:
        print(f"{todo} review prompts in {prompt_dir}/ need verdicts in {review_dir}/<same name>.json")


def verdicts_for(slug: str) -> dict[int, dict] | None:
    """Map quote number -> verdict, or None if this issue hasn't been reviewed."""
    f = DATA / "reviews" / f"{slug}.json"
    if not f.exists():
        return None
    return {v["n"]: v for v in json.loads(f.read_text(encoding="utf-8")).get("verdicts", [])}
