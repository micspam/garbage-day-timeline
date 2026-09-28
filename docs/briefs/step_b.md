# Step B brief: review (the sanity pass)

**Model: Opus-class only.** In a calibration on 126 quotes, Sonnet reviewers kept quotes that break the rules outright (a rhetorical question, a textbook then-vs-now setup), and one gave the same boilerplate reason for every verdict. The review is the quality gate, so it gets the stronger model.

**Use fresh agents that did not do step A,** so every quote is judged cold, the way a reader of the timeline sees it.

You're given a list of issue slugs. For each one, read `data/review_prompts/<slug>.txt` and write `data/reviews/<slug>.json` in the format the prompt shows, with one extra top-level field: `"model": "<your model id>"`.

## Rules

- Apply the prompt's four-point checklist to every quote. Keep a quote only if all four checks pass. When unsure, drop it.
- **Check 3 (stands alone)** is where reviewers disagreed most. A quote that *opens* by pointing back at earlier text ("Case in point,", "This third strain", "That's why") fails, even if the rest is a clear era description. A reader of the timeline has never seen what it points back to.
- Write a real reason for each verdict: name the first check that failed, or say why the quote passes all four. Don't reuse one reason across quotes.
- The quote numbers in the prompt are what the verdicts refer to. Use them exactly.

## Before you finish

- **Write a file for every slug you were given**, then list the folder and confirm each one exists.
- Don't run `gdt prepare`, `gdt review` or `gdt tag`. They clear prompt folders that other agents may be reading.
- Never disable the sandbox. If a tool or command fails, stop and report it.
