"""Usage: python -m gdt {fetch,prepare,extract,build} [--limit N]"""
import argparse

from . import build, extract, fetch

ap = argparse.ArgumentParser(prog="gdt")
ap.add_argument("step", choices=["fetch", "prepare", "extract", "build"])
ap.add_argument("--limit", type=int, help="only process the first N issues")
args = ap.parse_args()

if args.step == "fetch":
    fetch.run(args.limit)
elif args.step == "prepare":
    extract.prepare(args.limit)
elif args.step == "extract":
    extract.run(args.limit)
else:
    build.run()
