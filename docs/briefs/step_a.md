# Step A brief: pick quotes

**Model:** Sonnet-class or better. (An Opus audit of Sonnet's empty answers found about 1 clear miss in 10 issues, which is acceptable.)

You're given a list of issue slugs. For each one, read `data/prompts/<slug>.txt` and write `data/answers/<slug>.json` in the answer format the prompt shows, with one extra top-level field: `"model": "<your model id>"`.

## Rules

- Return **sentence numbers only**. Never type quote text; code copies quotes from the source.
- Pick 1-3 consecutive sentences **from one paragraph**. A `¶` line in the prompt marks a paragraph break, so a quote can't cross one. The `evidence` phrase must come from the same paragraph.
- Only pick passages that are **about** a past era: what happened then, or what it was like. Skip passing mentions: then-vs-now setups, background dates in a present-day story, takes on current events, rhetorical questions.
- `evidence` is copied character for character. When the paragraph has a phrase with a year or decade in it, use that one. Vague phrases ("back in the day") are allowed, but the site marks those dates as estimated.
- **Years:** give the years the text gives. Only `start_year` must be at least 2 years before publication; `end_year` can run up to the publication year. Never shorten or shift a range to fit.
- Keep each quote to 70 words or fewer. Longer quotes are rejected at `extract`.
- Most issues have nothing that qualifies. `{"references": [], "model": "..."}` is a correct and common answer.

## Before you finish

- **Write a file for every slug you were given**, then list the folder and confirm each one exists. One agent silently skipped an issue last run.
- Don't run `gdt prepare`, `gdt review` or `gdt tag`. They clear prompt folders that other agents may be reading.
- Never disable the sandbox. If a tool or command fails, stop and report it.
