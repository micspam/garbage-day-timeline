# Garbage Day Timeline

A proof of concept: pull quotes from [Garbage Day](https://www.garbageday.email) placed on a sideways-scrolling timeline by **the era they reference**, not when they were published.

It's a response to the newsletter's vibe-coding post, where the AI step kept hallucinating quotes and putting issues in the wrong place. The fix here is in the pipeline, not the model:

- **The model never writes quote text.** It sees each issue as numbered sentences and returns only sentence numbers. Code copies the quote from the source, so fabricated quotes aren't possible.
- **One issue per call.** Code attaches the issue URL and title, so quotes can't end up under the wrong issue.
- **Claims have to be backed up.** Each reference needs an exact phrase from the text that dates it. If the phrase isn't in the issue, or the years are impossible, the reference is rejected and counted.
- **"Nothing here" is allowed.** Most issues are about the present, and returning an empty list is an acceptable answer.

`site/data.json` contains a validation report showing what was kept and why things were rejected.

## Run it on GitHub (no local setup)

1. Add your Anthropic API key as a repo secret named `ANTHROPIC_API_KEY` (Settings → Secrets and variables → Actions).
2. Set Settings → Pages → Source to **GitHub Actions**.
3. Go to Actions → **Build timeline and deploy** → Run workflow, and pick how many issues to process.

The workflow fetches issues, runs the extraction, commits `site/data.json`, and publishes the site.

## Run it locally

Python 3.10+, standard library only.

```bash
python -m gdt fetch --limit 50      # public issues via the sitemap, 1 req/sec, cached in data/
export ANTHROPIC_API_KEY=...        # PowerShell: $env:ANTHROPIC_API_KEY="..."
python -m gdt extract --limit 50    # Claude Haiku, one issue per call
python -m gdt build                 # writes site/data.json
python -m http.server -d site 8000  # view at http://localhost:8000
```

Paid issues only show their headline publicly, so they're skipped. With a Beehiiv API key, `fetch.py` could be replaced by an API-based fetcher that covers the full archive.

## What's published

Full issue text stays in `data/`, which is gitignored. The site only shows short excerpts (70 words max), each linking back to the original issue.
