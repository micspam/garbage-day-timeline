"""Ask Claude which passages reference a past time period -- without letting it write any text.

The model only returns sentence numbers, years and an evidence phrase. Quotes are rebuilt
from the source by code, and every claim is checked against the source before it's kept.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DATA = Path("data")
MODEL = os.environ.get("GDT_MODEL", "claude-haiku-4-5-20251001")
MAX_SENTENCES_PER_QUOTE = 3
MIN_YEARS_BACK = 2  # the timeline is about the past, not "this week online"

# Split after . ! ? (plus any closing quotes/brackets) when the next sentence starts uppercase/digit/quote.
SENT_END = re.compile(r"[.!?]+[\"'”’)\]]*\s+(?=[A-Z0-9“\"‘(\[])")

TOOL = {
    "name": "record_references",
    "description": "Record passages from the issue that clearly refer to a specific past time period.",
    "input_schema": {
        "type": "object",
        "properties": {
            "references": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "sentence_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "1-3 consecutive sentence numbers that form a good pull quote.",
                        },
                        "start_year": {"type": "integer"},
                        "end_year": {"type": "integer", "description": "Same as start_year for a single year."},
                        "label": {"type": "string", "description": "Short name for what is being referenced, e.g. 'Vine shutting down'."},
                        "evidence": {
                            "type": "string",
                            "description": "An exact phrase copied from the text that establishes the time period (a year, era or datable event).",
                        },
                    },
                    "required": ["sentence_ids", "start_year", "end_year", "label", "evidence"],
                },
            }
        },
        "required": ["references"],
    },
}

PROMPT = """Below is one issue of the newsletter Garbage Day, published {published}, split into numbered sentences.

Find up to 5 passages that make a clear, specific reference to a time period at least {years_back} years before publication (a year, an era like "the late 2000s", or a datable event like "when Vine shut down"). Each passage should work as a standalone pull quote.

Rules:
- Only use the sentence numbers shown. Pick 1-{max_sents} consecutive sentences.
- The time period must be supported by an exact phrase from the text; copy it into `evidence` character for character.
- Most issues are about the present. If nothing clearly references the past, return an empty list. An empty list is a good answer.

<issue title="{title}">
{sentences}
</issue>"""


def split_sentences(paragraphs: list[str]) -> list[dict]:
    out = []
    for pi, para in enumerate(paragraphs):
        start = 0
        for m in SENT_END.finditer(para):
            out.append({"p": pi, "text": para[start:m.end()].strip()})
            start = m.end()
        if para[start:].strip():
            out.append({"p": pi, "text": para[start:].strip()})
    return out


def call_claude(prompt: str) -> dict:
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 2048,
        "tools": [TOOL],
        "tool_choice": {"type": "tool", "name": TOOL["name"]},
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    headers = {
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    for attempt in range(6):
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                msg = json.load(resp)
            return next(b["input"] for b in msg["content"] if b["type"] == "tool_use")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 529) and attempt < 5:
                time.sleep(2 ** attempt * 2)
                continue
            raise RuntimeError(f"API error {e.code}: {e.read().decode(errors='replace')[:300]}")
    raise RuntimeError("unreachable")


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


def validate(ref: dict, sents: list[dict], pub_year: int) -> str | None:
    """Return a rejection reason, or None if the reference is kept."""
    ids = ref["sentence_ids"]
    if not ids or len(ids) > MAX_SENTENCES_PER_QUOTE:
        return "bad_sentence_count"
    if any(i < 1 or i > len(sents) for i in ids):
        return "sentence_id_out_of_range"
    if sorted(ids) != list(range(min(ids), max(ids) + 1)):
        return "sentences_not_consecutive"
    if len({sents[i - 1]["p"] for i in ids}) > 1:
        return "spans_paragraphs"
    start, end = ref["start_year"], ref["end_year"]
    if not (1800 <= start <= end <= pub_year):
        return "impossible_years"
    if start > pub_year - MIN_YEARS_BACK:
        return "not_in_the_past"
    evidence = norm(ref["evidence"])
    if len(evidence) < 3 or evidence not in norm(" ".join(s["text"] for s in sents)):
        return "evidence_not_in_source"
    return None


def process(path: Path, out_dir: Path) -> dict:
    out = out_dir / path.name
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    issue = json.loads(path.read_text(encoding="utf-8"))
    sents = split_sentences(issue["paragraphs"])
    pub_year = int(issue["published"][:4])
    prompt = PROMPT.format(
        published=issue["published"], title=issue["title"], years_back=MIN_YEARS_BACK,
        max_sents=MAX_SENTENCES_PER_QUOTE,
        sentences="\n".join(f"[{i}] {s['text']}" for i, s in enumerate(sents, 1)),
    )
    result = call_claude(prompt)

    kept, rejected = [], []
    for ref in result.get("references", []):
        try:
            reason = validate(ref, sents, pub_year)
        except (KeyError, TypeError, ValueError):
            reason = "malformed_response"
        if reason:
            rejected.append({**ref, "reason": reason})
            continue
        ids = sorted(ref["sentence_ids"])
        kept.append({
            # The quote is assembled from the source text by code -- the model never writes it.
            "quote": " ".join(sents[i - 1]["text"] for i in ids),
            "start_year": ref["start_year"],
            "end_year": ref["end_year"],
            "label": ref["label"],
            "evidence": ref["evidence"],
        })
    record = {k: issue[k] for k in ("url", "slug", "title", "published")}
    record.update(sentence_count=len(sents), kept=kept, rejected=rejected)
    out.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return record


def run(limit: int | None, workers: int = 4):
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise SystemExit("Set ANTHROPIC_API_KEY first.")
    out_dir = DATA / "extracted"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted((DATA / "issues").glob("*.json"))[: limit or None]
    print(f"extracting from {len(paths)} issues with {MODEL}")

    def job(p):
        try:
            r = process(p, out_dir)
            print(f"  {p.stem}: kept {len(r['kept'])}, rejected {len(r['rejected'])}")
        except Exception as e:
            print(f"  {p.stem}: FAILED ({e})")

    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(job, paths))
