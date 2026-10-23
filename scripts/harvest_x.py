#!/usr/bin/env python3
"""Harvest full tweet text for a list of X status IDs and print corpus stats.

Usage:
    python3 scripts/harvest_x.py ids.txt --out corpus.jsonl --stats

WHY THIS EXISTS
The X timeline DOM truncates long posts, hides quoted text behind a click and
never exposes the engagement counters as plain numbers, so a profile scroll is
only good for DISCOVERY. Once the status ids are known, this script fetches the
complete post text plus the engagement counters from the public fxtwitter
mirror API and writes one JSON object per post:

    {"id", "author", "name", "date", "likes", "retweets", "replies", "views", "text"}

The ids file holds one status id per line, e.g. taken from a permalink
(x.com/<handle>/status/<id>). Blank lines and lines starting with # are
ignored, so a permalink list can be pasted in unchanged.

--stats prints per-account counts, date range and the style counters used by
this skill (emoji per post, hashtag share, median length).
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import datetime
import json
import re
import statistics
import sys
import time
import urllib.request

API = "https://api.fxtwitter.com/status/%s"
UA = "Mozilla/5.0"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️❤]")
WORKERS = 8


def read_ids(path: str) -> list[str]:
    ids: list[str] = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.search(r"/status/(\d+)", line)
        ids.append(m.group(1) if m else line)
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def fetch(tid: str, retries: int = 3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(API % tid, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode())
            tweet = data.get("tweet") or {}
            if not tweet:
                return None
            author = tweet.get("author") or {}
            return {
                "id": tid,
                "author": author.get("screen_name"),
                "name": author.get("name"),
                "date": tweet.get("created_at"),
                "likes": tweet.get("likes"),
                "retweets": tweet.get("retweets"),
                "replies": tweet.get("replies"),
                "views": tweet.get("views"),
                "text": tweet.get("text") or "",
            }
        except Exception:
            if attempt == retries - 1:
                return {"id": tid, "error": "fetch failed"}
            time.sleep(1.5 * (attempt + 1))
    return None


def fetch_all(ids: list[str]) -> list[dict]:
    rows: list[dict] = []
    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for row in pool.map(fetch, ids):
            done += 1
            if row and row.get("text"):
                rows.append(row)
            if done % 100 == 0:
                print("fetched %d/%d" % (done, len(ids)), file=sys.stderr)
    return rows


def parse_date(value: str):
    if not value:
        return None
    value = value.replace(" UTC", "")
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%a %b %d %H:%M:%S %Y"):
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def print_stats(rows: list[dict]) -> None:
    by_author = collections.defaultdict(list)
    for row in rows:
        if row.get("text"):
            by_author[row.get("author") or "?"].append(row)
    for author, items in sorted(by_author.items()):
        lengths = [len(r["text"]) for r in items]
        emoji = [len(EMOJI.findall(r["text"])) for r in items]
        dates = [parse_date(r.get("date")) for r in items]
        dates = [d for d in dates if d]
        print("\n%s: %d posts" % (author, len(items)))
        if dates:
            print("  range      %s -> %s" % (min(dates).date(), max(dates).date()))
        print("  chars      median %d, mean %.0f" % (
            statistics.median(lengths), statistics.mean(lengths)))
        print("  emoji      mean %.2f, %d%% of posts with none" % (
            statistics.mean(emoji),
            100 * sum(1 for e in emoji if e == 0) // max(1, len(emoji))))
        print("  hashtags   %d%% of posts with none" % (
            100 * sum(1 for r in items if "#" not in r["text"]) // max(1, len(items))))
        print("  replies    %d%% of posts start with @" % (
            100 * sum(1 for r in items if r["text"].lstrip().startswith("@")) // max(1, len(items))))


def main(argv: list[str]) -> int:
    global WORKERS

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ids", help="file with one status id or permalink per line")
    ap.add_argument("--out", help="write JSONL here")
    ap.add_argument("--stats", action="store_true", help="print corpus statistics")
    ap.add_argument("--workers", type=int, default=WORKERS, help="parallel fetches")
    args = ap.parse_args(argv[1:])

    ids = read_ids(args.ids)
    if not ids:
        print("no status ids in %s" % args.ids, file=sys.stderr)
        return 1

    WORKERS = max(1, args.workers)
    rows = fetch_all(ids)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print("wrote %d posts to %s" % (len(rows), args.out), file=sys.stderr)

    if args.stats:
        print_stats(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
