#!/usr/bin/env python3
"""Emit a curated markdown samples file from a harvested tweets.jsonl.

    python3 scripts/emit_samples.py references/tweets.jsonl references/samples.md \
        references/samples_spec.json

The spec is a JSON file: an optional "header" (the lines above the first
section) and a list of sections, each with a title, an optional intro and items.
An item picks one post out of the corpus with a predicate on id, date, author,
a substring and a minimum length, and carries the note that says what the post
shows.

Why a spec and not a hand-written file: the corpus changes on every harvest, so
a hand-written samples file drifts out of the corpus and ends up quoting posts
that no longer exist, with stale like counts. Selecting by predicate means the
file is regenerated from whatever the corpus currently holds, and every block it
prints is a verbatim post by construction.
"""
from __future__ import annotations

import json
import sys


def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def match(row, spec):
    if "id" in spec and row["id"] != spec["id"]:
        return False
    if "date" in spec and not row["date"].startswith(spec["date"]):
        return False
    if "author" in spec and row["author"] != spec["author"]:
        return False
    if "contains" in spec and spec["contains"] not in row["text"]:
        return False
    if "min_chars" in spec and len(row["text"]) < spec["min_chars"]:
        return False
    return True


def find(rows, spec):
    hits = [r for r in rows if match(r, spec)]
    if not hits:
        raise SystemExit("no row matched %r" % spec)
    if len(hits) > 1:
        raise SystemExit("%r matched %d rows: %s"
                         % (spec, len(hits), ", ".join(r["id"] for r in hits)))
    return hits[0]


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 1
    src, dst, spec_path = argv[1], argv[2], argv[3]
    rows = load(src)
    spec = json.load(open(spec_path, encoding="utf-8"))

    out = list(spec.get("header", []))
    if out:
        out.append("")
    for section in spec["sections"]:
        out.append("## %s" % section["title"])
        out.append("")
        if section.get("intro"):
            out.append(section["intro"])
            out.append("")
        for item in section["items"]:
            row = find(rows, item["match"])
            out.append("### %s · %s likes · %s" % (row["date"], row.get("likes"), row["url"]))
            if item.get("note"):
                out.append("")
                out.append("> %s" % item["note"])
            out.append("")
            out.append("```")
            out.append(row["text"])
            out.append("```")
            out.append("")

    text = "\n".join(out).rstrip() + "\n"
    open(dst, "w", encoding="utf-8").write(text)
    print("wrote %s (%d chars)" % (dst, len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))