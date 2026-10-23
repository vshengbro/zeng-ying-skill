#!/usr/bin/env python3
"""Assert every number the SKILL.md and README.md quote against the corpus.

    python3 scripts/verify_claims.py

Every check is computed from references/tweets.jsonl, so a doc that quotes a
statistic the corpus does not support fails here rather than in a reader's
head. The script exits non-zero on the first failing group.
"""
from __future__ import annotations

import collections
import json
import os
import re
import statistics
import sys

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️❤]")
SENT = re.compile(r"[^。!！?？\n…]*[。!！?？…]|[^。!！?？\n…]+")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

fails = []


def check(label, got, want):
    ok = got == want
    if not ok:
        fails.append("%s: got %r want %r" % (label, got, want))
    print("  %-56s %s (%s)" % (label, "OK " if ok else "FAIL", got))


def pct(n, d):
    return round(100 * n / d)


def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def verify_zeng():
    print("=== zeng-ying-skill ===")
    z = load(os.path.join(ROOT, "references", "tweets.jsonl"))
    rep = [r for r in z if r["text"].lstrip().startswith("@")]
    sol = [r for r in z if not r["text"].lstrip().startswith("@")]
    we = [r for r in z if EMOJI.search(r["text"])]
    ess = [r for r in z if r["text"].lstrip().startswith("《")]

    check("883 posts", len(z), 883)
    check("range 2026-02-12 .. 2026-10-22",
          (min(r["date"] for r in z), max(r["date"] for r in z)), ("2026-02-12", "2026-10-22"))
    check("replies 54%", pct(len(rep), len(z)), 54)
    check("reply median 29", statistics.median(len(r["text"]) for r in rep), 29)
    check("replies 99.8% single-line",
          pct(sum(1 for r in rep if len(r["text"].strip().split("\n")) == 1), len(rep)), 100)
    check("replies 72% <=40", pct(sum(1 for r in rep if len(r["text"]) <= 40), len(rep)), 72)
    check("replies 12% end 。", pct(sum(1 for r in rep if r["text"].strip().endswith("。")), len(rep)), 12)
    check("replies 17% end emoji",
          pct(sum(1 for r in rep if EMOJI.search(r["text"].strip()[-2:])), len(rep)), 17)
    check("standalone 47% end 。", pct(sum(1 for r in sol if r["text"].strip().endswith("。")), len(sol)), 47)
    check("emoji 22% of posts", pct(len(we), len(z)), 22)
    check("emoji mean 0.27", round(sum(len(EMOJI.findall(r["text"])) for r in z) / len(z), 2), 0.27)
    check("78% zero emoji", pct(sum(1 for r in z if not EMOJI.search(r["text"])), len(z)), 78)
    check("198 with emoji", len(we), 198)
    check("170 have exactly one", sum(1 for r in we if len(EMOJI.findall(r["text"])) == 1), 170)
    ec = collections.Counter()
    for r in z:
        ec.update(EMOJI.findall(r["text"]))
    for k, v in (("😂", 74), ("😅", 25), ("😭", 15), ("🤣", 13), ("❤", 11)):
        check("emoji %s = %d" % (k, v), ec[k], v)
    check("hashtag 2.8%", round(100 * sum(1 for r in z if "#" in r["text"]) / len(z), 1), 2.8)
    check("25 posts with hashtag", sum(1 for r in z if "#" in r["text"]), 25)
    check("97% no hashtag", pct(sum(1 for r in z if "#" not in r["text"]), len(z)), 97)
    check("max 5 tags", max(len(re.findall(r"#\w+", r["text"])) for r in z), 5)
    check("exclamation 7%", pct(sum(1 for r in z if "!" in r["text"] or "！" in r["text"]), len(z)), 7)
    end = collections.Counter()
    for r in z:
        b = r["text"].strip()
        if not b:
            continue
        last = b[-1]
        if last in "。.":
            end["period"] += 1
        elif last in "！!":
            end["excl"] += 1
        elif last in "？?":
            end["q"] += 1
        elif last in "…":
            end["ell"] += 1
        elif EMOJI.match(last):
            end["emoji"] += 1
        else:
            end["bare"] += 1
    tot = sum(end.values())
    for k, want in (("bare", 45), ("period", 29), ("emoji", 17), ("q", 5), ("excl", 3), ("ell", 2)):
        check("end-punct %s = %d%%" % (k, want), pct(end[k], tot), want)
    for kw, want in (("孙割", 28), ("孙哥", 25), ("孙老师", 6), ("孙宇晨", 9), ("孙狗", 4),
                     ("某人", 0), ("波场那位", 0), ("赢学", 0), ("颖学之", 2), ("是那个", 3)):
        check("name %s = %d" % (kw, want), sum(1 for r in z if kw in r["text"]), want)
    check("那位 = 4", sum(1 for r in z if "那位" in r["text"]), 4)
    check("《》 essays = 27", len(ess), 27)
    check("《》 share 3.1%", round(100 * len(ess) / len(z), 1), 3.1)
    check("《》 median 727", statistics.median(len(r["text"]) for r in ess), 727)
    check("《》 with emoji = 2", sum(1 for r in ess if EMOJI.search(r["text"])), 2)
    check("《》 with hashtag = 3", sum(1 for r in ess if "#" in r["text"]), 3)
    paras = [len([l for l in r["text"].split("\n") if l.strip()]) - 1 for r in ess]
    check("《》 paragraphs 3-47", (min(paras), max(paras)), (3, 47))
    titles = []
    for r in ess:
        m = re.match(r"《[^》]*》", r["text"].lstrip())
        titles.append(m.group(0) if m else "")
    check("《》 distinct titles 25", len(set(titles)), 25)
    check("《欲望…》 written 3x", titles.count("《欲望是人生陷入痛苦的诅咒》"), 3)
    peak = [r for r in z if "#最佳前任" in r["text"]][0]
    check("peak likes 14601", peak["likes"], 14601)
    cnt = collections.Counter()
    for r in z:
        for para in r["text"].split("\n"):
            para = para.strip()
            if not para:
                continue
            for m in SENT.finditer(para):
                t = m.group(0).strip()
                if not t:
                    continue
                last = t[-1]
                if last in "。":
                    cnt["period"] += 1
                elif last in "！!":
                    cnt["excl"] += 1
                elif last in "？?":
                    cnt["q"] += 1
                elif last in "…":
                    cnt["ell"] += 1
                elif EMOJI.match(last):
                    cnt["emoji"] += 1
    term = cnt["period"] + cnt["excl"] + cnt["q"] + cnt["ell"]
    check("punctuated sentences: 88% period", pct(cnt["period"], term), 88)

    # the period split the skill documents
    for label, lo, hi, n, reply, emoji, excl, insult in (
            ("2026-02..03", "0000-00-00", "2026-04-01", 284, 70, 17, 5, 5),
            ("2026-04..07", "2026-04-01", "2026-08-01", 414, 42, 24, 5, 0),
            ("2026-08..10", "2026-08-01", "9999-99-99", 185, 55, 27, 15, 0)):
        rows = [r for r in z if lo <= r["date"] < hi]
        check("%s n" % label, len(rows), n)
        check("%s reply%%" % label,
              pct(sum(1 for r in rows if r["text"].lstrip().startswith("@")), len(rows)), reply)
        check("%s emoji%%" % label, pct(sum(1 for r in rows if EMOJI.search(r["text"])), len(rows)), emoji)
        check("%s excl%%" % label,
              pct(sum(1 for r in rows if "!" in r["text"] or "！" in r["text"]), len(rows)), excl)
        check("%s insult posts" % label,
              sum(1 for r in rows if any(k in r["text"] for k in
                                         ("傻逼", "神经病", "弱智", "闭嘴", "老婊子", "婊"))), insult)

    # the account facts the skill records
    check("appeal letter 2026-02-23 present",
          any(r["id"] == "2026005822644580553" and "Authenticity policy" in r["text"] for r in z), True)
    check("appeal letter 3976 chars", len([r for r in z if r["id"] == "2026005822644580553"][0]["text"]), 3976)
    check("充电宝 sample present",
          any(r["id"] == "2051860252879167688" for r in z), True)
    check("版本答案 exchange present",
          any(r["id"] == "2098460056933310828" for r in z), True)


def verify_sun():
    print("\n=== sun-yuchen-skill ===")
    s = load(os.path.join(ROOT, "references", "tweets.jsonl"))
    en = [r for r in s if r["author"] == "justinsuntron"]
    cn = [r for r in s if r["author"] == "sunyuchentron"]

    def sc(author=None, year=None):
        out = s
        if author:
            out = [r for r in out if r["author"] == author]
        if year:
            out = [r for r in out if r["date"][:4] == year]
        return out

    check("1300 total", len(s), 1300)
    check("justinsuntron 718", len(en), 718)
    check("sunyuchentron 582", len(cn), 582)
    check("EN from 2020-11-30", min(r["date"] for r in en), "2020-11-30")
    check("CN from 2020-03-06", min(r["date"] for r in cn), "2020-03-06")
    check("last 2026-10-23", max(r["date"] for r in s), "2026-10-23")
    for year, n, em, hs, med in (("2020", 101, 1.48, 1.69, 83), ("2022", 152, 0.74, 1.05, 133.5),
                                 ("2024", 69, 0.42, 0.00, 50), ("2025", 112, 0.36, 0.02, 48),
                                 ("2026", 269, 0.17, 0.03, 26)):
        tx = sc(author="justinsuntron", year=year)
        check("%s n" % year, len(tx), n)
        check("%s emoji" % year, round(sum(len(EMOJI.findall(r["text"])) for r in tx) / len(tx), 2), em)
        check("%s hashtag" % year, round(sum(len(re.findall(r"#\w+", r["text"])) for r in tx) / len(tx), 2), hs)
        check("%s median" % year, statistics.median(len(r["text"]) for r in tx), med)
    for kw, want in (("thrilled", 0), ("historic", 0), ("game-changing", 0),
                     ("revolutionary", 0), ("record-breaking", 0), ("world-class", 0),
                     ("industry-leading", 0), ("despite the fud", 0), ("announce", 4),
                     ("proud to announce", 1), ("massive", 4), ("more to come", 1), ("huge", 6),
                     ("excited to", 6), ("honored to", 4), ("join us", 4), ("bullish", 4),
                     ("stay tuned", 3), ("milestone", 2), ("best is yet to come", 1),
                     ("full sail ahead", 1)):
        check("hype %r = %d" % (kw, want), sum(1 for r in en if kw in r["text"].lower()), want)
    check("groundbreaking = 1", sum(1 for r in en if "groundbreaking" in r["text"].lower()), 1)
    check("groundbreaking is the banana post",
          [r["id"] for r in en if "groundbreaking" in r["text"].lower()], ["1862202741667635237"])
    e24 = [r for r in en if r["date"][:4] >= "2024"]
    check("2024+ n=450", len(e24), 450)
    check("2024+ with-hashtag 13", sum(1 for r in e24 if "#" in r["text"]), 13)
    check("2024+ zero-hashtag 97%", pct(sum(1 for r in e24 if "#" not in r["text"]), len(e24)), 97)
    check("2024+ zero-emoji 363", sum(1 for r in e24 if not EMOJI.search(r["text"])), 363)
    ec24 = collections.Counter()
    for r in e24:
        ec24.update(EMOJI.findall(r["text"]))
    for k, v in (("👏", 16), ("😂", 11), ("🔻", 8), ("😆", 7), ("💪", 6), ("🔹", 6)):
        check("2024+ emoji %s = %d" % (k, v), ec24[k], v)
    ec20 = collections.Counter()
    for r in sc(author="justinsuntron", year="2020"):
        ec20.update(EMOJI.findall(r["text"]))
    for k, v in (("🤗", 19), ("🗣", 15), ("🎉", 12), ("❤", 9), ("🎊", 7), ("🚀", 7)):
        check("2020 emoji %s = %d" % (k, v), ec20[k], v)
    ec22 = collections.Counter()
    for r in sc(author="justinsuntron", year="2022"):
        ec22.update(EMOJI.findall(r["text"]))
    for k, v in (("🔥", 10), ("🙌", 8), ("❤", 8), ("🚀", 7)):
        check("2022 emoji %s = %d" % (k, v), ec22[k], v)
    check("EN all-years 🌟 = 1", sum(1 for r in en if "🌟" in r["text"]), 1)
    check("EN all-years 💎 = 2", sum(1 for r in en if "💎" in r["text"]), 2)
    check("EN all-years 🚀 = 18", sum(1 for r in en if "🚀" in r["text"]), 18)
    check("2024+ 🚀 = 4", sum(1 for r in e24 if "🚀" in r["text"]), 4)
    e26 = sc(author="justinsuntron", year="2026")
    check("2026 median 26", statistics.median(len(r["text"]) for r in e26), 26)
    check("2026 66% <=40", pct(sum(1 for r in e26 if len(r["text"]) <= 40), len(e26)), 66)
    check("2026 35% end . or !", pct(sum(1 for r in e26 if r["text"].strip()[-1:] in ".!。！"), len(e26)), 35)
    check("2026 13% emoji", pct(sum(1 for r in e26 if EMOJI.search(r["text"])), len(e26)), 13)
    check("2026 3% hashtag", pct(sum(1 for r in e26 if "#" in r["text"]), len(e26)), 3)
    check("Keep going 15 in 2026", sum(1 for r in e26 if "Keep going" in r["text"]), 15)
    check("keep building 7 EN", sum(1 for r in en if "keep building" in r["text"].lower()), 7)
    check("keep buying 2 EN", sum(1 for r in en if "keep buying" in r["text"].lower()), 2)
    check("@elonmusk 8", sum(1 for r in en if "@elonmusk" in r["text"]), 8)
    check("@cz_binance 12", sum(1 for r in en if "@cz_binance" in r["text"]), 12)
    check("Trump 6", sum(1 for r in en if "Trump" in r["text"]), 6)
    check("Buffett 4", sum(1 for r in en if "Buffett" in r["text"]), 4)
    h20 = collections.Counter()
    for r in sc(author="justinsuntron", year="2020"):
        h20.update(re.findall(r"#\w+", r["text"]))
    for k, v in (("#TRON", 49), ("#BitTorrentX", 18), ("#TRX", 18), ("#LinktheFuture", 17), ("#BTT", 15)):
        check("2020 %s = %d" % (k, v), h20[k], v)
    cn21 = sc(author="sunyuchentron", year="2021")
    check("CN 2021 hashtag mean 2.14",
          round(sum(len(re.findall(r"#\w+", r["text"])) for r in cn21) / len(cn21), 2), 2.14)
    cn26 = sc(author="sunyuchentron", year="2026")
    check("CN 2026 hashtag mean 0.05",
          round(sum(len(re.findall(r"#\w+", r["text"])) for r in cn26) / len(cn26), 2), 0.05)
    check("CN 2026 median 19", statistics.median(len(r["text"]) for r in cn26), 19)
    letter = [r for r in en if "再致胡锡进老师" in r["text"]][0]
    check("letter likes 12589", letter["likes"], 12589)
    check("letter views 3059524", letter["views"], 3059524)
    check("letter chars 2160", len(letter["text"]), 2160)
    check("孙学/颖学 2948 likes", [r for r in en if "有”孙学”，就有”颖学”" in r["text"]][0]["likes"], 2948)
    check("孙学就是赢学 1246 likes", [r for r in en if "孙学就是赢学" in r["text"]][0]["likes"], 1246)
    art = [r for r in s if r["id"] == "2092932777612390850"][0]
    check("景甜 article likes 68343", art["likes"], 68343)
    check("大压抑时代 post 8013 likes",
          [r for r in en if "大压抑时代" in r["text"]][0]["likes"], 8013)


def main():
    # Dispatch on which account the corpus holds, not on the directory name:
    # a clone of the repository is not called zeng-ying-skill.
    corpus = load(os.path.join(ROOT, "references", "tweets.jsonl"))
    accounts = {row.get("author") for row in corpus}
    if "zengying1107" in accounts:
        verify_zeng()
    else:
        verify_sun()
    print("\n" + ("ALL CLAIMS VERIFIED" if not fails else "FAILURES:\n" + "\n".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
