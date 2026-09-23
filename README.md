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

**In a Claude Code session (no API key).** Open the repo in Claude Code and ask it to "run the pipeline on 50 issues". [CLAUDE.md](CLAUDE.md) has the steps. Claude answers each prompt file itself, and the same checks apply.

**With an API key (unattended).** If `ANTHROPIC_API_KEY` is set, `extract` calls Claude Haiku for any issue that doesn't have an answer yet.

```bash
python -m gdt fetch --limit 50      # public issues via the sitemap, 1 req/sec, cached in data/
python -m gdt prepare --limit 50    # prompt files for a Claude Code session to answer (skip if using the API)
python -m gdt extract --limit 50    # checks the answers against the source
python -m gdt review --limit 50     # sanity pass: is each quote really about its era?
python -m gdt build                 # writes site/data.json
python -m http.server -d site 8000  # view at http://localhost:8000
```

Pushing `site/` to `main` deploys to GitHub Pages (set Settings → Pages → Source to **GitHub Actions**).

Paid issues only show their headline publicly, so they're skipped. With a Beehiiv API key, `fetch.py` could be replaced by an API-based fetcher that covers the full archive.

## What's published

Full issue text stays in `data/`, which is gitignored. The site only shows short excerpts (70 words max), each linking back to the original issue.
