# Garbage Day Timeline

The pipeline puts Garbage Day pull quotes on a timeline by the era they're *about*, then tags them so categories and sub-timelines can be discovered from the data. In a Claude Code session there is no API key: **you** answer the prompts (through subagents), and the code checks the answers against the source.

The model's answers are committed (`data/answers/`, `data/reviews/`, `data/tags/`), so work resumes across sessions. Full issue text (`data/issues/`, `data/raw/`) is never committed. Each session re-fetches it.

## "Continue the archive run" (or "run the pipeline on N issues")

Setup, once per session. The full archive fetch takes **about 50 minutes** at 1 request/sec, so start it first. With `--limit N`, it fetches only the N newest readable issues; pass the same `--limit N` to every step below.

```bash
python -m gdt fetch               # needs network access to www.garbageday.email
python -m gdt status              # where the run stands: per-stage counts, issues awaiting review or tags, skipped files
```

Then loop in **batches of about 50 issues**, committing after each batch so nothing is lost if the session ends. Each step has a committed brief in `docs/briefs/`. **Hand subagents the brief for their step verbatim**, plus their list of slugs.

| Step | Brief | Model |
| --- | --- | --- |
| A. Pick quotes | `docs/briefs/step_a.md` | Sonnet-class or better |
| B. Review | `docs/briefs/step_b.md` | **Opus-class only**, fresh agents that didn't do step A |
| C. Tag | `docs/briefs/step_c.md` | Sonnet-class or better |

Every answer, review and tag file records the model that wrote it in a top-level `"model"` field.

```bash
python -m gdt prepare             # data/prompts/ now holds only unanswered issues
# A: subagents write data/answers/<slug>.json for ~50 of them
python -m gdt extract             # validates answers against the source
python -m gdt review              # data/review_prompts/ now holds issues with unreviewed quotes
# B: subagents write data/reviews/<slug>.json
python -m gdt tag                 # data/tag_prompts/ now holds issues with untagged approved quotes
# C: subagents write data/tags/<slug>.json
python -m gdt build               # site/data.json + report
python -m gdt vocab               # data/vocab.json: every tag value with quote/issue/era counts
git add data/answers data/reviews data/tags data/vocab.json data/aliases.json site/data.json
git commit -m "Archive run: batch N (issues X-Y)" && git push origin HEAD:main
```

Then run `prepare` again for the next batch. Stop when `prepare` reports 0 prompts. Name the issue range in each commit message (positions in newest-first order), because later re-reviews use those ranges.

**Only the main session runs `gdt` commands.** `prepare`, `review` and `tag` clear their prompt folders before writing, so running one while subagents are reading would pull files out from under them.

**Push to `main`**, not a session branch: the maintainer works from `main`. If pushing to `main` is refused, say so in your summary and name the branch you pushed.

**Keep the tag vocabulary tidy.** After `vocab`, look for new near-duplicates (e.g. "meme culture" and "memes"), catch-alls, or moment kinds used as topics. Merge or drop them by editing `data/aliases.json`, not by re-tagging. The merges apply whenever tags are read.

## After the archive is done: re-review batches 5-8

Opus keep rates varied from 75% to 90% across batches 5-8, mostly on check 3 (quotes that open by pointing back at earlier text). Once `prepare` reports 0, re-judge those batches with the current step B brief so the whole timeline meets one standard:

```bash
python -m gdt review --redo-from A --redo-to B   # A, B: batch 5's first and batch 8's last issue position (see git log)
# B: Opus subagents rewrite data/reviews/<slug>.json for every listed issue
python -m gdt tag                                  # tags any quote the re-review newly approved
# C, then build, vocab, commit and push as above
```

## Checks

- A high `evidence_not_in_source`, `spans_paragraphs` or `sentence_id_out_of_range` count means answers were written carelessly: fix them and rerun extract.
- `quote_too_long` is now rejected at `extract`, before review and tagging.
- `dropped_in_review` should be a minority. If most quotes get dropped, step A is ignoring the "about the era" rule.
- `dates_estimated` counts quotes whose evidence has no year or decade; the site shows those dates as approximate.
- `vocab` prints how many fact tags were dropped for missing evidence (a high share means step C is guessing) and lists possible near-duplicate tag names to merge in `data/aliases.json`.
- Run `gdt status` at the end of every batch: it flags prompt files an agent skipped, and quotes still awaiting review or tags.
- Spot-check `data/review_dropped.json` to make sure the review isn't throwing out good quotes.

**Don't loosen the checks in `validate()`, the review rules or the tag evidence rule to get more data.** They are the point of the project. **Never disable the sandbox.** If a tool fails, stop and report it.

The site is shown as a claude.ai Artifact (https://claude.ai/artifact/5WC1RuWDapKRqEJmY6VKXb). Its page is `site/artifact_template.html` with `site/data.json` pasted in place of `__DATA__` (escape every `</` in the data as `<\/`); whoever owns the Artifact republishes it.
