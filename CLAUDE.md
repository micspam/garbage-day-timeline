# Garbage Day Timeline

The pipeline puts Garbage Day pull quotes on a timeline by the era they reference. In a Claude Code session there is no API key: **you** answer the per-issue prompts, and the code checks your answers against the source.

## "Run the pipeline on N issues"

```bash
python -m gdt fetch --limit N     # needs network access to www.garbageday.email
python -m gdt prepare --limit N   # writes data/prompts/<slug>.txt
```

Then, for every file in `data/prompts/`, read it and write `data/answers/<slug>.json` (same name, `.json`) in the answer format the prompt shows. Rules:

- Return **sentence numbers only**. Never type quote text, because the code copies quotes from the source itself.
- `evidence` must be copied character for character from the same paragraph as the quote.
- Most issues have no clear past reference. `{"references": []}` is a correct and common answer. Don't stretch to fill the timeline.
- Judge each issue on its own. Don't reuse picks across issues.
- Keep each quote under 70 words; the build step drops longer ones.

With many prompts, split them into batches across subagents. Give each one the rules above and its list of file names.

```bash
python -m gdt extract --limit N   # validates answers; prints kept/rejected per issue
python -m gdt build               # writes site/data.json and prints the report
```

Look at the report. A high `evidence_not_in_source` or `sentence_id_out_of_range` count means answers were written carelessly, so fix them and rerun extract and build. **Don't loosen the checks in `validate()` to get more quotes on the timeline.** They are the point of the demo.

Commit only `site/data.json` (`data/` is gitignored on purpose, because full issue text is not published). Pushing to `main` redeploys the site through GitHub Pages.
