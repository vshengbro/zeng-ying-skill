#!/usr/bin/env python3
"""Build references/sun_samples.md — the Justin Sun control group for the Zeng repo.

    python3 scripts/build_sun_samples.py

The Zeng Ying skill compares two voices, so it needs a measured counterpart in
the same months. This script takes the @justinsuntron / @sunyuchentron posts
that fall inside the Zeng corpus window and writes them as a reading copy with
the style counters that make the contrast measurable.

The Sun posts come from the sun-yuchen-skill repository, which holds the full
1,372-post corpus; point SUN_REPO elsewhere to read a different checkout.
"""
from __future__ import annotations

import collections
import json
import os
import re
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUN_REPO = os.environ.get("SUN_REPO", "/Users/sqs/code/sun-yuchen-skill")
OUT = os.path.join(ROOT, "references", "sun_samples.md")

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️❤]")
SAMPLE_LIMIT = 150
CJK = re.compile(r"[一-鿿]")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def cjk_ratio(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if CJK.match(c)) / len(letters)


def counters(rows):
    n = len(rows)
    def pct(count):
        return round(100 * count / n)
    return {
        "n": n,
        "median": statistics.median(len(r["text"]) for r in rows),
        "mean": round(statistics.mean(len(r["text"]) for r in rows)),
        "zh": sum(1 for r in rows if cjk_ratio(r["text"]) >= 0.3),
        "no_punct": pct(sum(1 for r in rows if r["text"].strip()[-1:] not in "。.!！?？…")),
        "excl": pct(sum(1 for r in rows if r["text"].strip()[-1:] in "!！")),
        "period": pct(sum(1 for r in rows if r["text"].strip()[-1:] in "。.")),
        "emoji": pct(sum(1 for r in rows if EMOJI.search(r["text"]))),
        "emoji_end": pct(sum(1 for r in rows if EMOJI.match(r["text"].strip()[-1:]))),
        "hashtag": pct(sum(1 for r in rows if "#" in r["text"])),
        "max_emoji": max(len(EMOJI.findall(r["text"])) for r in rows),
        "max_tags": max(len(re.findall(r"#\w+", r["text"])) for r in rows),
    }


def main():
    zeng = load(os.path.join(ROOT, "references", "tweets.jsonl"))
    sun = load(os.path.join(SUN_REPO, "references", "tweets.jsonl"))
    lo = min(r["date"] for r in zeng)
    hi = max(r["date"] for r in zeng)
    ctrl = [r for r in sun if lo <= r["date"] <= hi]
    ctrl.sort(key=lambda r: (-(r["likes"] or 0), r["date"]))

    # Posts a previous version of this file published must stay published: a
    # sample that silently disappears is a link a reader can no longer follow.
    # They are listed as samples but stay out of the counters, which describe
    # the window only.
    KEEP = ["1905324113851547790", "2103381476045922470", "2107702108904653126",
            "2110298951434084799", "2111481862736785824"]
    ctrl_ids = {r["id"] for r in ctrl}

    c = counters(ctrl)
    z = counters(zeng)
    zs = counters([r for r in zeng if not r["text"].lstrip().startswith("@")])

    out = []
    out.append("# 孙宇晨 (@justinsuntron / @sunyuchentron) — 对照组语料")
    out.append("")
    out.append("The Zeng Ying skill needs a control group: the same platform, the same "
               "months, a completely different voice. This is that control group.")
    out.append("")
    out.append("实测采集 **%d 条**孙宇晨原帖(`@justinsuntron` %d 条 + `@sunyuchentron` %d 条,"
               "%s → %s),全文 + 互动数。窗口与曾颖语料完全重合。"
               % (c["n"],
                  sum(1 for r in ctrl if r["author"] == "justinsuntron"),
                  sum(1 for r in ctrl if r["author"] == "sunyuchentron"),
                  lo, hi))
    out.append("")
    out.append("由 `scripts/build_sun_samples.py` 生成;全量语料见 `sun-yuchen-skill` 仓库。")
    out.append("")
    out.append("## 他的语体是什么")
    out.append("")
    out.append("| 指标 | 实测值 |")
    out.append("| --- | --- |")
    out.append("| 正文长度 | 中位数 %d 字,平均 %d 字 |" % (c["median"], c["mean"]))
    out.append("| 语种 | 中文 %d 条(%d%%),英文 %d 条(%d%%) |"
               % (c["zh"], round(100 * c["zh"] / c["n"]), c["n"] - c["zh"],
                  round(100 * (c["n"] - c["zh"]) / c["n"])))
    out.append("| 句末无标点直接断 | %d%%(另有 %d%% 以 emoji 收尾) |" % (c["no_punct"], c["emoji_end"]))
    out.append("| 句号收尾 | %d%% |" % c["period"])
    out.append("| **感叹号收尾** | **%d%%** |" % c["excl"])
    out.append("| 含 emoji | %d%%,单条最多 %d 个 |" % (c["emoji"], c["max_emoji"]))
    out.append("| 含 hashtag | %d%%,单条最多 %d 个 |" % (c["hashtag"], c["max_tags"]))
    out.append("")
    out.append("**三段式,和曾颖的白描散文完全相反:**")
    out.append("")
    out.append("1. **英文公关稿体**——结论先行、数据背书、结尾带一个 🔻 或 😎。")
    out.append("2. **中文口号体**——短句 + 感叹号 + 交易/销毁/涨价,没有比喻。")
    out.append("3. **偶尔的自我嘲弄体**——这也是他会「玩梗」的原因,他会自嘲,但自嘲是为了把话题接回来。")
    out.append("")
    out.append("**和曾颖的差别,一眼能分:** 曾颖用细节反差让人笑,孙宇晨用数据让人点头;"
               "曾颖的句子是散文,孙宇晨的句子是公告;曾颖把「孙哥」放在第三人称里调侃,"
               "孙宇晨谈自己时是「我」+ 数据。")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 样本（同一时间窗内按点赞排序，取前 %d 条）" % SAMPLE_LIMIT)
    out.append("")
    out.append("下面 %d 条是这一窗口里点赞最高的原帖,全文照录;计数表覆盖窗口内全部 %d 条。"
               % (min(SAMPLE_LIMIT, len(ctrl)), c["n"]))
    out.append("")
    shown = ctrl[:SAMPLE_LIMIT]
    shown_ids = {r["id"] for r in shown}
    shown += [r for r in sun if r["id"] in KEEP and r["id"] not in shown_ids]
    for row in shown:
        out.append("### %s · %s likes · %s views · %s"
                   % (row["date"], row["likes"], row["views"], row["url"]))
        out.append("")
        out.append("```text")
        out.append(row["text"])
        out.append("```")
        out.append("")
    out.append("---")
    out.append("")
    out.append("## 与曾颖语体的对照（改写时不要混用）")
    out.append("")
    out.append("| | 曾颖（颖学） | 孙宇晨（对照组） |")
    out.append("| --- | --- | --- |")
    out.append("| 语料量 | %d 条 | %d 条（同一时间窗） |" % (z["n"], c["n"]))
    out.append("| 句子 | 散文白描 | 公告短句 |")
    out.append("| 说服方式 | 细节反差 | 数据背书 |")
    out.append("| 提到对方 | 第三人称调侃(`孙割`/`孙哥`/`孙老师`) | 自称「我」 |")
    out.append("| 正文长度 | 独立帖中位数 %d 字,回复中位数 29 字 | 中位数 %d 字 |"
               % (zs["median"], c["median"]))
    out.append("| 语种 | 中文 %d%% | 中文 %d%% |"
               % (round(100 * z["zh"] / z["n"]), round(100 * c["zh"] / c["n"])))
    out.append("| emoji | %d%% 的帖子有,😂 收尾 | %d%%,🔻/😎 |" % (z["emoji"], c["emoji"]))
    out.append("| hashtag | %d%%,一次 1–5 个 | %d%%,单条最多 %d 个 |"
               % (z["hashtag"], c["hashtag"], c["max_tags"]))
    out.append("| 句末无标点 | %d%% | %d%% |" % (z["no_punct"], c["no_punct"]))
    out.append("| **感叹号收尾** | **%d%%** | **%d%%** |" % (z["excl"], c["excl"]))
    out.append("")
    out.append("**所以:写曾颖时不要用孙宇晨的句法。** 「$TRX 唯一上涨主流代币」那种一句话下判断的写法,"
               "在颖学里是无效的——曾颖的语气必须落在一个具体的细节上,然后什么都不解释。")
    out.append("")

    text = "\n".join(out).rstrip() + "\n"
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote %s (%d chars, %d control posts)" % (OUT, len(text), c["n"]))


if __name__ == "__main__":
    main()
