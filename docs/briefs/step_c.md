# Step C brief: tag

**Model:** Sonnet-class or better.

You're given a list of issue slugs. For each one, read `data/tag_prompts/<slug>.txt` and write `data/tags/<slug>.json` in the format the prompt shows, with one extra top-level field: `"model": "<your model id>"`. If the file already exists (an issue re-listed because a newly approved quote has no tags), rewrite the whole file.

## Rules

- `moment`: exactly one kind from the list in the prompt, or "other". Put your own description in `moment_detail`.
- `topics`: 1-4 specific subject areas, lowercase, common names. No catch-alls ("internet culture", "social media", "technology"). No moment kinds as topics (not "cultural shift"). No platform names as topics.
- Entities, platforms and audiences each need an exact `evidence` phrase from the quote's context paragraph. No phrase, no tag. Never guess an audience or platform.
- **Tag platforms exactly as the text names them.** Don't substitute a similar site: "2chan" is not "2channel". The one exception: always "twitter" for both Twitter and X.
- Audiences describe who was involved, not a guess at a generation: "teens" for teenagers of any era, "gen z" only when the text says so.

## Before you finish

- **Write a file for every slug you were given**, then list the folder and confirm each one exists.
- Don't run `gdt prepare`, `gdt review` or `gdt tag`. They clear prompt folders that other agents may be reading.
- Never disable the sandbox. If a tool or command fails, stop and report it.
