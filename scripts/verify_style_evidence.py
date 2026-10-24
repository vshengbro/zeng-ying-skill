#!/usr/bin/env python3
"""Verify the focused style supplement without changing the historical corpus.

Offline checks validate provenance metadata, baseline excerpts, counts and links.
--live re-fetches every selected public post and compares its exact text digest.
--self-test exercises deliberate corruption; it does not simulate live success.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import datetime
import hashlib
import json
import re
import sys
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
ACCOUNT = "zengying1107"
STATUS_ID = re.compile(r"[0-9]{19}")
REFERENCE = "references/voice-and-theory.md"


def text_errors(source, text):
    errors = []
    key = source["key"]
    if len(text) != source["full_text_chars"]:
        errors.append(f"{key}: full-text length changed")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != source["full_text_sha256"]:
        errors.append(f"{key}: full-text digest changed")
    for quote in source["excerpts"]:
        if quote not in text:
            errors.append(f"{key}: excerpt is not an exact substring")
    title = source["title"]
    if source["title_is_excerpt"]:
        if not title.endswith("…") or not text.startswith(title[:-1]):
            errors.append(f"{key}: title excerpt does not match the original")
    elif text.splitlines()[0] != title:
        errors.append(f"{key}: title does not match the original first line")
    return errors


def evidence_errors(data, rows):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    require(data["schema_version"] == 1, "unsupported schema version")
    require(data["account"] == ACCOUNT, "wrong manifest account")
    verified = datetime.date.fromisoformat(data["verified_on"])
    baseline = {r["id"]: r for r in rows}
    require(len(baseline) == len(rows), "duplicate baseline ID")
    require(all(r["author"] == ACCOUNT for r in rows), "wrong baseline author")
    require(data["baseline"]["path"] == "references/tweets.jsonl", "wrong baseline path")
    require(data["baseline"]["count"] == len(rows), "baseline count mismatch")
    require(data["baseline"]["from"] == min(r["date"] for r in rows), "baseline start mismatch")
    require(data["baseline"]["through"] == max(r["date"] for r in rows), "baseline end mismatch")

    posts = data["posts"]
    require(bool(posts), "no selected evidence")
    ids = [p["id"] for p in posts]
    keys = [p["key"] for p in posts]
    require(len(set(ids)) == len(ids), "duplicate selected ID")
    require(len(set(keys)) == len(keys), "duplicate evidence key")
    inventory = data["public_fetch_ids"]
    require(len(set(inventory)) == len(inventory), "duplicate fetch inventory ID")
    require(all(isinstance(sid, str) and STATUS_ID.fullmatch(sid) for sid in inventory),
            "malformed fetch inventory ID")
    require(set(ids).issubset(inventory), "selected source missing from fetch inventory")
    summary = data["summary"]
    require(summary["public_posts_fetched"] == len(inventory), "public fetch count mismatch")
    require(summary["analysis_posts"] == len(posts), "analysis count mismatch")
    require(summary["analysis_posts_not_in_baseline"] == sum(sid not in baseline for sid in ids),
            "new evidence count mismatch")
    excluded = data["excluded_access_limited"]
    require(summary["creator_subscription_posts_excluded"] == len(excluded),
            "access-limit count mismatch")
    excluded_urls = [p["url"] for p in excluded]
    require(len(set(excluded_urls)) == len(excluded_urls), "duplicate access-limit exclusion")
    for entry in excluded:
        match = re.fullmatch(r"https://x\.com/zengying1107/status/([0-9]{19})", entry["url"])
        require(bool(match), "malformed excluded URL")
        if match:
            require(match.group(1) not in inventory, "access-limited source was fetched")
        require(bool(entry["reason"].strip()), "missing exclusion reason")

    for source in posts:
        key, sid = source["key"], source["id"]
        require(bool(re.fullmatch(r"[a-z][a-z0-9_]*", key)), f"{key}: invalid key")
        require(isinstance(sid, str) and bool(STATUS_ID.fullmatch(sid)), f"{key}: malformed ID")
        require(source["author"] == ACCOUNT, f"{key}: wrong author")
        require(source["url"] == f"https://x.com/{ACCOUNT}/status/{sid}", f"{key}: wrong permalink")
        require(source["source_endpoint"] == f"https://api.fxtwitter.com/status/{sid}",
                f"{key}: wrong source endpoint")
        require(type(source["in_baseline"]) is bool and source["in_baseline"] == (sid in baseline),
                f"{key}: wrong baseline membership")
        published = datetime.datetime.fromisoformat(source["published_at_utc"])
        retrieved = datetime.datetime.fromisoformat(source["retrieved_at_utc"])
        require(published.utcoffset() == datetime.timedelta(0), f"{key}: publication time is not UTC")
        require(retrieved.utcoffset() == datetime.timedelta(0), f"{key}: retrieval time is not UTC")
        require(published.date().isoformat() == source["date_utc"], f"{key}: UTC date mismatch")
        require(published.date() <= verified, f"{key}: post is after the verification date")
        require(published <= retrieved, f"{key}: post is after retrieval")
        require(retrieved.astimezone(datetime.timezone(datetime.timedelta(hours=8))).date() == verified,
                f"{key}: verification date does not match the CST retrieval day")
        require(type(source["full_text_chars"]) is int and source["full_text_chars"] > 0,
                f"{key}: invalid full-text length")
        require(bool(re.fullmatch(r"[a-f0-9]{64}", source["full_text_sha256"])),
                f"{key}: invalid digest")
        quotes = source["excerpts"]
        require(bool(quotes) and all(isinstance(q, str) and q for q in quotes), f"{key}: empty excerpts")
        require(len(set(quotes)) == len(quotes), f"{key}: duplicate excerpts")
        require(sum(map(len, quotes)) <= 50, f"{key}: excerpts are too long")
        require(type(source["title_is_excerpt"]) is bool, f"{key}: invalid title flag")
        require(bool(source["analysis"].strip()), f"{key}: missing analysis")
        if sid in baseline:
            row = baseline[sid]
            require(row["date"] == source["date_utc"], f"{key}: baseline date mismatch")
            errors.extend(text_errors(source, row["text"]))
    return errors


def document_errors(data, documents):
    errors = []
    reference = documents[REFERENCE]
    anchors = re.findall(r'<a id="evidence-([a-z0-9_]+)"></a>', reference)
    expected = {p["key"] for p in data["posts"]}
    if len(anchors) != len(set(anchors)) or set(anchors) != expected:
        errors.append("reference evidence anchors do not match the manifest")
    for source in data["posts"]:
        if source["url"] not in reference:
            errors.append(f"{source['key']}: permalink missing from the reading reference")
        if any(quote not in reference for quote in source["excerpts"]):
            errors.append(f"{source['key']}: excerpt missing from the reading reference")

    summary = data["summary"]
    patterns = {
        "SKILL.md": [
            (r"选出 \*\*(\d+) 条\*\*分析证据", "analysis_posts"),
            (r"其中 \*\*(\d+) 条\*\*不在既有基线", "analysis_posts_not_in_baseline"),
            (r"另有 \*\*(\d+) 条\*\*创作者订阅帖", "creator_subscription_posts_excluded"),
        ],
        "README.md": [
            (r"\*\*(\d+) public posts in full\*\*", "public_posts_fetched"),
            (r"\*\*(\d+) evidence posts\*\*", "analysis_posts"),
            (r"\*\*(\d+) selected posts absent", "analysis_posts_not_in_baseline"),
            (r"\*\*(\d+) creator-subscription posts\*\*", "creator_subscription_posts_excluded"),
        ],
        REFERENCE: [
            (r"取得 \*\*(\d+) 条公开原帖全文\*\*", "public_posts_fetched"),
            (r"选出 \*\*(\d+) 条分析证据\*\*", "analysis_posts"),
            (r"其中 \*\*(\d+) 条不在既有基线\*\*", "analysis_posts_not_in_baseline"),
            (r"另外 \*\*(\d+) 条创作者订阅帖\*\*", "creator_subscription_posts_excluded"),
        ],
    }
    for name, text in documents.items():
        for pattern, metric in patterns[name]:
            match = re.search(pattern, text)
            if not match or int(match.group(1)) != summary[metric]:
                errors.append(f"{name}: {metric} is missing or incorrect")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if urlsplit(target).scheme or target.startswith("//"):
                continue
            path, _, fragment = target.partition("#")
            resolved = (ROOT / name).parent / unquote(path) if path else ROOT / name
            resolved = resolved.resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.is_file():
                errors.append(f"{name}: broken local link {target}")
                continue
            if fragment and f'id="{unquote(fragment)}"' not in resolved.read_text(encoding="utf-8"):
                errors.append(f"{name}: broken explicit anchor {target}")
    return errors


def live_errors(source, row):
    key = source["key"]
    if not row or not row.get("text") or row.get("error"):
        return [f"{key}: public full-text fetch failed"]
    errors = []
    if row.get("author") != ACCOUNT:
        errors.append(f"{key}: live author mismatch")
    if row.get("id") != source["id"]:
        errors.append(f"{key}: live ID mismatch")
    date = parsedate_to_datetime(row["date"]).astimezone(datetime.timezone.utc)
    if date.isoformat(timespec="seconds") != source["published_at_utc"]:
        errors.append(f"{key}: live publication time mismatch")
    errors.extend(text_errors(source, row["text"]))
    return errors


def run_self_tests(data, rows, documents):
    cases = [
        ("wrong author", lambda d: d["posts"][0].update(author="another_author"), "wrong author"),
        ("malformed ID", lambda d: d["posts"][0].update(id=d["posts"][0]["id"] + "x"), "malformed ID"),
        ("duplicate ID", lambda d: d["posts"].append(copy.deepcopy(d["posts"][0])), "duplicate selected ID"),
        ("wrong link", lambda d: d["posts"][0].update(url="https://x.com/other/status/1"), "wrong permalink"),
        ("invented quote", lambda d: d["posts"][0].update(excerpts=["THIS IS A DELIBERATELY FALSE QUOTE"]), "exact substring"),
        ("digest drift", lambda d: d["posts"][0].update(full_text_sha256="0" * 64), "digest changed"),
        ("date drift", lambda d: d["posts"][0].update(date_utc="2026-01-01"), "UTC date mismatch"),
        ("count drift", lambda d: d["summary"].update(analysis_posts=0), "analysis count mismatch"),
        ("inventory drift", lambda d: d["public_fetch_ids"].pop(), "public fetch count mismatch"),
        ("access-limit leak", lambda d: d["excluded_access_limited"][0].update(url=d["posts"][0]["url"]), "access-limited source was fetched"),
    ]
    for label, mutate, expected in cases:
        fixture = copy.deepcopy(data)
        mutate(fixture)
        errors = evidence_errors(fixture, rows)
        if not any(expected in error for error in errors):
            raise RuntimeError(f"self-test failed to reject {label}")
    broken = dict(documents)
    broken[REFERENCE] = broken[REFERENCE].replace(f'id="evidence-{data["posts"][0]["key"]}"', 'id="removed-evidence"', 1)
    if not any("anchors" in error for error in document_errors(data, broken)):
        raise RuntimeError("self-test failed to reject a missing reference anchor")
    source = data["posts"][0]
    fixture = next(r for r in rows if r["id"] == source["id"])
    fetched = dict(fixture, date=datetime.datetime.fromisoformat(source["published_at_utc"]).strftime("%a %b %d %H:%M:%S %z %Y"))
    if live_errors(source, fetched):
        raise RuntimeError("self-test rejected a valid existing baseline row")
    fetched["text"] += " DELIBERATE TEST CORRUPTION"
    if not any("digest changed" in error for error in live_errors(source, fetched)):
        raise RuntimeError("self-test failed to reject live text corruption")
    print(f"SELF-TEST PASS: {len(cases) + 2} negative fixtures rejected; valid baseline fixture accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="re-fetch all selected public posts")
    parser.add_argument("--self-test", action="store_true", help="test deliberate corruption in memory")
    args = parser.parse_args()
    data = json.loads((ROOT / "references/style_evidence.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (ROOT / "references/tweets.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    documents = {name: (ROOT / name).read_text(encoding="utf-8") for name in ("SKILL.md", "README.md", REFERENCE)}
    errors = evidence_errors(data, rows) + document_errors(data, documents)
    if errors:
        print("EVIDENCE FAIL:\n" + "\n".join(errors), file=sys.stderr)
        return 1
    summary = data["summary"]
    print(f"OFFLINE PASS: {summary['analysis_posts']} evidence posts; {summary['analysis_posts_not_in_baseline']} outside the {len(rows)}-post baseline; counts, excerpts and links match")
    if args.self_test:
        run_self_tests(data, rows, documents)
    if args.live:
        from harvest_x import fetch
        posts = data["posts"]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for source, row in zip(posts, pool.map(fetch, [p["id"] for p in posts])):
                failures = live_errors(source, row)
                errors.extend(failures)
                print(f"{'FAIL' if failures else 'PASS'} live {source['key']}")
        if errors:
            print("LIVE FAIL:\n" + "\n".join(errors), file=sys.stderr)
            return 1
        print(f"LIVE PASS: {len(posts)} public posts match author, ID, UTC time, full-text length, digest and excerpts")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, TypeError, ValueError, OSError, RuntimeError) as error:
        print(f"EVIDENCE FAIL: {error}", file=sys.stderr)
        sys.exit(1)
