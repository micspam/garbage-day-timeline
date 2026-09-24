# Garbage Day Timeline

The pipeline puts Garbage Day pull quotes on a timeline by the era they're *about*, then tags them so categories and sub-timelines can be discovered from the data. In a Claude Code session there is no API key: **you** answer the prompts, and the code checks your answers against the source.

The model's answers are committed (`data/answers/`, `data/reviews/`, `data/tags/`), so work resumes across sessions. Full issue text (`data/issues/`, `data/raw/`) is never committed. Each session re-fetches it.

## "Continue the archive run" (or "run the pipeline on N issues")

Setup, once per session (the full archive takes ~20 minutes at 1 request/sec; with `--limit N`, only the N newest readable issues, and pass the same `--limit N` to every step below):

```bash
python -m gdt fetch               # needs network access to www.garbageday.email
```

Then loop in **batches of about 50 prompts**, committing after each batch so nothing is lost if the session ends:

```bash
python -m gdt prepare             # data/prompts/ now holds only unanswered issues
```

**A. Pick quotes.** For up to ~50 files in `data/prompts/`, write `data/answers/<slug>.json` in the format the prompt shows.
- Return **sentence numbers only**. Never type quote text; the code copies quotes from the source.
- Only pick passages that are **about** a past era: what happened then, or what it was like. Skip passing mentions (then-vs-now setups, background dates in a present-day story, takes on current events, rhetorical questions). The prompt spells these out.
- `evidence` must be copied character for character from the same paragraph as the quote.
- Most issues have nothing that qualifies. `{"references": []}` is a correct and common answer.
- Judge each issue on its own. Keep each quote under 70 words.

```bash
python -m gdt extract             # validates answers against the source
python -m gdt review              # data/review_prompts/ now holds only unreviewed issues
```

**B. Sanity pass.** For each file in `data/review_prompts/`, write `data/reviews/<slug>.json`.
- **Use fresh subagents that did not do step A**, so each quote is judged cold, the way a reader sees it.
- Keep a quote only if, on its own, it tells the reader something about the era it's filed under. When unsure, drop it.

```bash
python -m gdt tag                 # data/tag_prompts/ now holds only untagged issues
```

**C. Tag.** For each file in `data/tag_prompts/`, write `data/tags/<slug>.json`. `gdt tag` also re-lists an already-tagged issue if a later review approved a quote in it that has no tags yet. Rewrite the whole file then.
- `moment` is one kind from the list in the prompt, plus a free-text `moment_detail`. `topics` are free text. Use plain, lowercase, common names consistently ("tiktok", not "TikTok app"; "twitter" for both Twitter and X). No catch-all topics like "internet culture".
- Entities, platforms and audiences each need an exact `evidence` phrase from the quote's context paragraph. No phrase, no tag. Never guess an audience or platform.
- Give review (step B) subagents the prompt exactly as written, whatever model they run on. Its checklist is what keeps the review strict.

```bash
python -m gdt build               # site/data.json + report
python -m gdt vocab               # data/vocab.json: every tag value with quote/issue/era counts
git add data/answers data/reviews data/tags data/vocab.json data/aliases.json site/data.json
git commit -m "Archive run: batch N" && git push origin HEAD:main
```

**Push to `main`**, not a session branch: the maintainer works from `main`. If pushing to `main` is refused, say so in your summary and name the branch you pushed.

**Keep the tag vocabulary tidy.** After `vocab`, look for new near-duplicates (e.g. "meme culture" and "memes") or catch-alls. Merge or drop them by editing `data/aliases.json`, not by re-tagging. The merges apply whenever tags are read.

Then run `prepare` again for the next batch. Stop when `prepare` reports 0 prompts.

Use subagents to parallelize steps A, B and C. Give each one the rules for its step and its list of file names.

## Checks

- A high `evidence_not_in_source` or `sentence_id_out_of_range` count means answers were written carelessly: fix them and rerun extract.
- `dropped_in_review` should be a minority. If most quotes get dropped, step A is ignoring the "about the era" rule.
- `vocab` prints how many fact tags were dropped for missing evidence. A high share means step C is guessing.
- Spot-check `data/review_dropped.json` to make sure the review isn't throwing out good quotes.

**Don't loosen the checks in `validate()`, the review rules or the tag evidence rule to get more data.** They are the point of the project.

The site is shown as a claude.ai Artifact that is rebuilt from `site/data.json` by whoever maintains it.
