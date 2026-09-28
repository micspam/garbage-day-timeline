# Garbage Day Timeline

A proof of concept: pull quotes from [Garbage Day](https://www.garbageday.email) placed on a sideways-scrolling timeline by **the era they reference**, not when they were published.

It's a response to the newsletter's vibe-coding post, where the AI step kept hallucinating quotes and putting issues in the wrong place. The fix here is in the pipeline, not the model:

- **The model never writes quote text.** It sees each issue as numbered sentences and returns only sentence numbers. Code copies the quote from the source, so fabricated quotes aren't possible.
- **One issue per call.** Code attaches the issue URL and title, so quotes can't end up under the wrong issue.
- **Claims have to be backed up.** Each reference needs an exact phrase from the text that dates it. If the phrase isn't in the issue, or the years are impossible, the reference is rejected and counted.
- **"Nothing here" is allowed.** Most issues are about the present, and returning an empty list is an acceptable answer.
- **Quotes have to be about their era.** A separate review reads each quote alone, the way a timeline reader sees it, and drops ones that only mention the era in passing ("back in the 2010s… but now").

`site/data.json` contains a validation report showing what was kept and why things were rejected.

## Run it

Python 3.10+, standard library only. There are two ways to get the model's answers.

**In a Claude Code session (no API key).** Open the repo in Claude Code and ask it to "continue the archive run". [CLAUDE.md](CLAUDE.md) has the batch loop and [docs/briefs/](docs/briefs/) the per-step rules for subagents. The model's answers are committed, so a run resumes across sessions.

**With an API key (unattended).** If `ANTHROPIC_API_KEY` is set, `extract`, `review` and `tag` call Claude for anything that doesn't have an answer yet.

```bash
python -m gdt fetch       # public issues via the sitemap, 1 req/sec, cached in data/ (~50 min for all)
python -m gdt prepare     # step A prompts: pick quotes by sentence number
python -m gdt extract     # checks the answers against the source
python -m gdt review      # step B prompts: is each quote really about its era?
python -m gdt tag         # step C prompts: kind of moment, topics, evidence-backed platforms/people/audiences
python -m gdt build       # writes site/data.json and a report
python -m gdt vocab       # counts every tag value; lists near-duplicates to merge in data/aliases.json
python -m gdt status      # where the run stands
```

Every step takes `--limit N` to work on the N newest issues only.

The site is a single page, [site/artifact_template.html](site/artifact_template.html), with `site/data.json` embedded. It has named eras, search, and sub-timelines for any tag with enough history, each with a shareable link.

Paid issues only show their headline publicly, so they're skipped. With a Beehiiv API key, `fetch.py` could be replaced by an API-based fetcher that covers the full archive.

## What's published

Full issue text stays in `data/`, which is gitignored. The site only shows short excerpts (70 words max), each linking back to the original issue.
