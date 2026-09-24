"""Usage: python -m gdt {fetch,prepare,extract,review,tag,vocab,build} [--limit N]"""
import argparse

from . import build, extract, fetch, review, tag

ap = argparse.ArgumentParser(prog="gdt")
ap.add_argument("step", choices=["fetch", "prepare", "extract", "review", "tag", "vocab", "build"])
ap.add_argument("--limit", type=int, help="only process the N newest issues")
args = ap.parse_args()

steps = {
    "fetch": fetch.run,
    "prepare": extract.prepare,
    "extract": extract.run,
    "review": review.run,
    "tag": tag.run,
    "vocab": tag.vocab,
    "build": build.run,
}
steps[args.step](args.limit)
