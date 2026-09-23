# Garbage Day Timeline

The pipeline puts Garbage Day pull quotes on a timeline by the era they're *about*. In a Claude Code session there is no API key: **you** answer the per-issue prompts, and the code checks your answers against the source.

## "Run the pipeline on N issues"

```bash
python -m gdt fetch --limit N     # needs network access to www.garbageday.email
python -m gdt prepare --limit N   # writes data/prompts/<slug>.txt
```

### 1. Pick quotes

For every file in `data/prompts/`, read it and write `data/answers/<slug>.json` (same name, `.json`) in the answer format the prompt shows. Rules:

- Return **sentence numbers only**. Never type quote text, because the code copies quotes from the source itself.
- Only pick passages that are **about** a past era: what happened then, or what it was like. Skip passages where the past only comes up in passing. That includes then-vs-now setups, background dates in a story about the present, people's takes on current events that name a past year, and rhetorical questions. The prompt spells these out.
- `evidence` must be copied character for character from the same paragraph as the quote.
- Most issues have nothing that qualifies. `{"references": []}` is a correct and common answer. Don't stretch to fill the timeline.
- Judge each issue on its own. Don't reuse picks across issues.
- Keep each quote under 70 words; the build step drops longer ones.

With many prompts, split them into batches across subagents. Give each one the rules above and its list of file names.

```bash
python -m gdt extract --limit N   # validates answers; prints kept/rejected per issue
python -m gdt review --limit N    # writes data/review_prompts/<slug>.txt
```

### 2. Sanity pass (review)

For every file in `data/review_prompts/`, write `data/reviews/<slug>.json` with a verdict for each numbered quote, in the format the prompt shows.

- **Use fresh subagents that did not do step 1.** The reviewer should judge each quote cold, the way a reader of the timeline will see it, without knowing why it was picked.
- Keep a quote only if, on its own, it tells the reader something about the era it's filed under. When unsure, drop it.
- Quotes without a verdict are not published.

```bash
python -m gdt build               # writes site/data.json and prints the report
```

Look at the report:
- A high `evidence_not_in_source` or `sentence_id_out_of_range` count means answers were written carelessly, so fix them and rerun extract and build.
- `dropped_in_review` should be a minority. If most quotes get dropped, step 1 is ignoring the "about the era" rule, so redo step 1 rather than relaxing the review.
- Spot-check `data/review_dropped.json` to make sure the review isn't throwing out good quotes.

**Don't loosen the checks in `validate()`, or the review rules, to get more quotes on the timeline.** They are the point of the demo.

Commit only `site/data.json` (`data/` is gitignored on purpose, because full issue text is not published). The site is currently shown as a claude.ai Artifact: whoever maintains it rebuilds the Artifact from `site/data.json`.
