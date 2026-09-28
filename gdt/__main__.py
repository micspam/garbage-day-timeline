"""Usage: python -m gdt {fetch,prepare,extract,review,tag,vocab,build} [--limit N]
       python -m gdt review --redo-from A --redo-to B   (re-review issues A..B, newest first)"""
import argparse
import os
import sys

from . import build, extract, fetch, review, tag

ap = argparse.ArgumentParser(prog="gdt")
ap.add_argument("step", choices=["fetch", "prepare", "extract", "review", "tag", "vocab", "build"])
ap.add_argument("--limit", type=int, help="only process the N newest issues")
ap.add_argument("--redo-from", type=int, help="review: first issue position to re-review (1 = newest)")
ap.add_argument("--redo-to", type=int, help="review: last issue position to re-review")
args = ap.parse_args()

steps = {
    "fetch": fetch.run,
    "prepare": extract.prepare,
    "extract": extract.run,
    "review": lambda limit: review.run(limit, (args.redo_from, args.redo_to) if args.redo_from else None),
    "tag": tag.run,
    "vocab": tag.vocab,
    "build": build.run,
}
try:
    steps[args.step](args.limit)
except BrokenPipeError:
    # Output piped to `head` etc. closed early; files were already written, so exit quietly.
    sys.stdout = open(os.devnull, "w")
