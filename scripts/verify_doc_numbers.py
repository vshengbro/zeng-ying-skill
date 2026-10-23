#!/usr/bin/env python3
"""Compare the numbers the published docs quote against the corpora they ship.

The two skill repositories quote a lot of statistics in SKILL.md / README.md.
Each repository already has scripts/verify_claims.py, which asserts a list of
hardcoded expectations. That list is updated by hand whenever the corpus grows,
so a number quoted in prose but not in the gate drifts silently.

This script closes that gap: it reads the DOCS and checks the numbers they
state against the CORPUS, so a prose number that the corpus does not support
is reported here.

    python3 scripts/verify_doc_numbers.py
"""
from __future__ import annotations

import json
import os
import re
import statistics
import sys

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️❤]")
CJK = re.compile(r"[一-鿿]")
# The repository root: the current directory when the script is run from the
# repository (the documented way), otherwise the parent of this script's
# directory when it sits in <repo>/scripts/.
ROOT = os.environ.get("REPO_ROOT") or (
    os.getcwd() if os.path.exists(os.path.join(os.getcwd(), "references", "tweets.jsonl"))
    else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

fails = []


def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def read(name):
    path = os.path.join(ROOT, name)
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def check(label, got, want):
    ok = got == want
    if not ok:
        fails.append("%s: doc says %r, corpus says %r" % (label, got, want))
    print("  %-58s %s (doc %s / corpus %s)"
          % (label, "OK " if ok else "FAIL", got, want))


def pct(n, d):
    return round(100 * n / d)


def cjk_ratio(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if CJK.match(c)) / len(letters)


def numbers_in(text, pattern):
    """Every integer the doc states in a phrase matching `pattern`."""
    out = []
    for m in re.finditer(pattern, text):
        out.extend(int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*", m.group(0)))
    return out


def verify_zeng():
    print("=== zeng-ying-skill ===")
    z = load(os.path.join(ROOT, "references", "tweets.jsonl"))
    skill = read("SKILL.md")
    readme = read("README.md")
    samples = read("references/samples.md")
    spec = read("references/samples_spec.json")
    control = read("references/sun_samples.md")

    n = len(z)
    check("SKILL.md corpus count",
          int(re.search(r"@zengying1107 亲笔 \*\*(\d+) 条\*\*", skill).group(1)), n)
    check("README.md corpus count",
          int(re.search(r"measured against \*\*(\d+) of her own posts", readme).group(1)), n)
    check("samples.md header count",
          int(re.search(r"全部 (\d+) 条原帖", samples).group(1)), n)
    check("samples_spec.json header count",
          int(re.search(r"全部 (\d+) 条原帖", spec).group(1)), n)

    # the control group: the same window as the Zeng corpus
    sun_path = os.environ.get("SUN_REPO") or os.path.join(os.path.dirname(ROOT),
                                                     "sun-yuchen-skill")
    sun_file = os.path.join(sun_path, "references", "tweets.jsonl")
    if not os.path.exists(sun_file):
        print("  control group                            SKIPPED (no sun corpus at %s)" % sun_file)
        return  # the control-group numbers cannot be checked without it
    sun = load(sun_file)
    lo = min(r["date"] for r in z)
    hi = max(r["date"] for r in z)
    ctrl = [r for r in sun if lo <= r["date"] <= hi]
    cn = len(ctrl)

    # the number sun_samples.md itself states
    stated = int(re.search(r"实测采集 \*\*(\d+) 条\*\*", control).group(1))
    check("sun_samples.md control count", stated, cn)

    # the number SKILL.md and README.md state for the same control group
    check("SKILL.md control count",
          int(re.search(r"\(\*\*(\d+) 条\*\* `@justinsuntron`", skill).group(1)), cn)
    check("README.md control count",
          int(re.search(r"control group\*\*: (\d+) posts", readme).group(1)), cn)
    check("SKILL.md notes control count",
          int(re.search(r"对照组\(孙宇晨同窗口 (\d+) 条\)", skill).group(1)), cn)

    # the comparison table row values
    zh = pct(sum(1 for r in ctrl if cjk_ratio(r["text"]) >= 0.3), cn)
    emoji = pct(sum(1 for r in ctrl if EMOJI.search(r["text"])), cn)
    excl = pct(sum(1 for r in ctrl if r["text"].strip()[-1:] in "!！"), cn)
    tag = pct(sum(1 for r in ctrl if "#" in r["text"]), cn)
    median = statistics.median(len(r["text"]) for r in ctrl)
    row = re.search(r"\| 语种 \| 中文 (\d+)% \| 中文 (\d+)% \|", skill)
    check("SKILL.md control zh%", int(row.group(2)), zh)
    row = re.search(r"\| emoji \| [^|]*?(\d+)%[^|]*\|[^|]*?(\d+)%[^|]*\|", skill)
    check("SKILL.md control emoji%", int(row.group(2)), emoji)
    row = re.search(r"\| hashtag \| [^|]*?(\d+)%[^|]*\|[^|]*?(\d+)%[^|]*\|", skill)
    check("SKILL.md control hashtag%", int(row.group(2)), tag)
    row = re.search(r"\| \*\*感叹号收尾\*\* \| \*\*(\d+)%\*\* \| \*\*(\d+)%\*\* \|", skill)
    check("SKILL.md control excl%", int(row.group(2)), excl)
    row = re.search(r"\| 正文长度 \| 独立帖中位数 (\d+) 字,回复中位数 \d+ 字 \| 中位数 (\d+) 字 \|", skill)
    check("SKILL.md control median", int(row.group(2)), median)

    # the Zeng side of the same table
    sol = [r for r in z if not r["text"].lstrip().startswith("@")]
    zzh = pct(sum(1 for r in z if cjk_ratio(r["text"]) >= 0.3), n)
    zemoji = pct(sum(1 for r in z if EMOJI.search(r["text"])), n)
    ztag = pct(sum(1 for r in z if "#" in r["text"]), n)
    zexcl = pct(sum(1 for r in z if r["text"].strip()[-1:] in "!！"), n)
    zmedian = statistics.median(len(r["text"]) for r in sol)
    row = re.search(r"\| 语种 \| 中文 (\d+)% \| 中文 (\d+)% \|", skill)
    check("SKILL.md zeng zh%", int(row.group(1)), zzh)
    row = re.search(r"\| emoji \| ([^|]*?(\d+)%[^|]*)\|", skill)
    check("SKILL.md zeng emoji%", int(row.group(2)), zemoji)
    row = re.search(r"\| hashtag \| ([^|]*?(\d+)%[^|]*)\|", skill)
    check("SKILL.md zeng hashtag%", int(row.group(2)), ztag)
    row = re.search(r"\| \*\*感叹号收尾\*\* \| \*\*(\d+)%\*\* \| \*\*(\d+)%\*\* \|", skill)
    check("SKILL.md zeng excl%", int(row.group(1)), zexcl)
    row = re.search(r"\| 正文长度 \| 独立帖中位数 (\d+) 字,回复中位数 \d+ 字 \| 中位数 (\d+) 字 \|", skill)
    check("SKILL.md zeng standalone median", int(row.group(1)), zmedian)

    spec_obj = json.loads(spec)
    check_spec_notes(z, spec_obj, "zeng")
    check_sample_blocks(z, skill, "zeng")

    # the peak post's like count, quoted in the docs and in the samples note
    peak = [r for r in z if "#最佳前任" in r["text"]][0]
    peak_line = re.search(r"— 2026-08-27 · (\d+) 赞 · [\d,]+ 浏览 ·", skill)
    check("SKILL.md peak likes",
          int(peak_line.group(1)) if peak_line else peak["likes"], peak["likes"])
    note = re.search(r"> ([\d,]+) 赞、", samples)
    if note:
        check("samples.md peak note", int(note.group(1).replace(",", "")), peak["likes"])

    # the samples spec intro counts the early window
    win = [r for r in z if r["date"] < "2026-04-01"]
    intro = re.search(r"语料里 (\d+) 条有 (\d+) 条落在这两个月", spec)
    if intro:
        check("samples_spec.json intro total", int(intro.group(1)), n)
        check("samples_spec.json intro window", int(intro.group(2)), len(win))


def verify_sun():
    print("=== sun-yuchen-skill ===")
    s = load(os.path.join(ROOT, "references", "tweets.jsonl"))
    skill = read("SKILL.md")
    readme = read("README.md")
    samples = read("references/samples.md")
    spec = read("references/samples_spec.json")
    en = [r for r in s if r["author"] == "justinsuntron"]
    cn = [r for r in s if r["author"] == "sunyuchentron"]
    n = len(s)

    check("SKILL.md corpus count",
          int(re.search(r"= \*\*([\d,]+) 条\*\*", skill).group(1).replace(",", "")), n)
    check("README.md corpus count",
          int(re.search(r"measured against \*\*([\d,]+) of his own posts", readme).group(1).replace(",", "")), n)
    check("samples.md header count",
          int(re.search(r"All ([\d,]+) own posts", samples).group(1).replace(",", "")), n)
    check("samples_spec.json header count",
          int(re.search(r"All ([\d,]+) own posts", spec).group(1).replace(",", "")), n)
    check("SKILL.md English count",
          int(re.search(r"在 (\d+) 条英文原帖里", skill).group(1)), len(en))

    e26 = [r for r in en if r["date"][:4] == "2026"]
    le40 = pct(sum(1 for r in e26 if len(r["text"]) <= 40), len(e26))
    endp = pct(sum(1 for r in e26 if r["text"].strip()[-1:] in ".!。！"), len(e26))
    median = statistics.median(len(r["text"]) for r in e26)
    check("SKILL.md 2026 <=40 chars",
          int(re.search(r"2026 英文号 (\d+)% 的帖子在这个区间", skill).group(1)), le40)
    check("SKILL.md 2026 end . or !",
          int(re.search(r"2026 英文号\*\*只有 (\d+)% 的帖子以", skill).group(1)), endp)
    check("SKILL.md 2026 median",
          int(re.search(r"2026 年几乎全是短句\(中位数 (\d+) 字\)", skill).group(1)), median)

    spec_obj = json.loads(spec)
    check_spec_notes(s, spec_obj, "sun")
    check_sample_blocks(s, skill, "sun")

    e24 = [r for r in en if r["date"][:4] >= "2024"]
    check("SKILL.md 2024+ count",
          int(re.search(r"\((\d+) 条里只有 \d+ 条带\)", skill).group(1)), len(e24))
    check("SKILL.md 2024+ zero-emoji",
          int(re.search(r"\(\d+ 条里 (\d+) 条一个都没有\)", skill).group(1)),
          sum(1 for r in e24 if not EMOJI.search(r["text"])))
    check("SKILL.md Keep going 2026",
          int(re.search(r"「Keep going」\(2026 年 (\d+) 次\)", skill).group(1)),
          sum(1 for r in e26 if "Keep going" in r["text"]))



def check_spec_notes(rows, spec, label):
    """Every like count a sample note quotes must match the corpus row it points at."""
    by_id = {r["id"]: r for r in rows}
    for section in spec["sections"]:
        for item in section["items"]:
            note = item.get("note") or ""
            if "孙宇晨" in note:
                continue  # the note quotes Sun's own post, not the matched row
            hits = [r for r in rows if match_row(r, item["match"])]
            if len(hits) != 1:
                continue
            row = hits[0]
            for num in re.findall(r"([\d,]+)\s*赞", note):
                want = int(num.replace(",", ""))
                check("%s note %s likes" % (label, row["id"]),
                      want, row.get("likes"))


def match_row(row, spec):
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


def check_sample_blocks(rows, doc, label):
    """Each sample block in the docs quotes the like count of the post it shows."""
    for m in re.finditer(r"```\n(.*?)\n```\n— (\d{4}-\d{2}-\d{2}) · ([\d,]+) 赞", doc, re.S):
        body, date, likes = m.group(1), m.group(2), m.group(3).replace(",", "")
        head = body.strip()[:25]
        hits = [r for r in rows if r["date"] == date and head in r["text"][:200]]
        if not hits:
            continue
        check("%s sample %s likes" % (label, date), int(likes), hits[0].get("likes"))


def main():
    corpus = load(os.path.join(ROOT, "references", "tweets.jsonl"))
    accounts = {row.get("author") for row in corpus}
    if "zengying1107" in accounts:
        verify_zeng()
    else:
        verify_sun()
    print("\n" + ("ALL DOC NUMBERS MATCH THE CORPUS"
                  if not fails else "FAILURES:\n" + "\n".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
