#!/usr/bin/env python3
"""Build references/corpus.md — the topic-organised reading copy of the corpus.

    python3 scripts/build_corpus_md.py

The corpus files hold every harvested post; this file holds the same posts
re-arranged by topic, for reading rather than for machines. Every block is
printed verbatim out of the corpus, so the reading copy cannot quote a post
the corpus does not contain.

Sections:
  一、颖学样本        standalone posts that name the target
  二、《》题名长文     the book-title-marked essays
  三、其他长文样本     the remaining long-form posts
  四、《》题名清单     the title family, as a list
  五、孙宇晨对照组    the other account's voice, from the Sun repository
  六、颖学长样本       the 2026-10-11 long post, in full
"""
from __future__ import annotations

import json
import os
import re

ZENG_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUN_REPO = os.environ.get("SUN_REPO", "/Users/sqs/code/sun-yuchen-skill")
OUT = os.path.join(ZENG_REPO, "references", "corpus.md")

TARGET = ["孙割", "孙哥", "孙老师", "孙宇晨", "孙狗"]
TITLE = re.compile(r"《[^》]*》")
LONG = 260


def load(path):
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def block(row):
    return ["```text", row["text"], "```", ""]


def head(row):
    return ["### %s" % row["date"], "",
            "`@%s` — https://x.com/%s/status/%s" % (row["author"], row["author"], row["id"]),
            ""]


def main():
    zeng = load(os.path.join(ZENG_REPO, "references", "tweets.jsonl"))
    sun = load(os.path.join(SUN_REPO, "references", "tweets.jsonl"))

    def is_reply(row):
        return row["text"].lstrip().startswith("@")

    essays = [r for r in zeng if r["text"].lstrip().startswith("《")]
    titled = {r["id"] for r in essays}
    target_posts = [r for r in zeng if not is_reply(r) and any(k in r["text"] for k in TARGET)]
    other_long = [r for r in zeng
                  if not is_reply(r) and r["id"] not in titled and len(r["text"]) >= LONG]

    out = []
    out.append("# Corpus — 曾颖 与 孙宇晨 的 X 推文")
    out.append("")
    out.append("实测语料，供 `zeng-ying-style` 的风格判断与自检使用。")
    out.append("")
    out.append("## 采集方法")
    out.append("")
    out.append("- 账号：曾颖 `@zengying1107`、孙宇晨 `@justinsuntron` / `@sunyuchentron`")
    out.append("- 曾颖：时间轴 + 回复页 + 站内搜索三线采集，**%d 条**（%s → %s）"
               % (len(zeng), min(r["date"] for r in zeng), max(r["date"] for r in zeng)))
    out.append("- 孙宇晨：同一套采集线，**%d 条**（%s → %s），全量见 `sun-yuchen-skill` 仓库"
               % (len(sun), min(r["date"] for r in sun), max(r["date"] for r in sun)))
    out.append("- 本文件由 `scripts/build_corpus_md.py` 从 `references/tweets.jsonl` 生成，每段正文都是语料里的原文")
    out.append("- 采集日期：2026-10-23；曾颖推文全部为中文，孙宇晨以英文公关稿为主")
    out.append("")
    out.append("## 账号事实（采集时实测）")
    out.append("")
    out.append("| 事实 | 实测结果 |")
    out.append("| --- | --- |")
    out.append("| 曾颖主号 | `@zengying1107`，页面显示 1,905 帖子 |")
    out.append("| `@tenten19901107` | 打开显示「账号已被冻结」；曾颖本人 bio 写明「本人只有这一个x账号其他都是假号」 |")
    out.append("| 孙宇晨 | `@justinsuntron`，页面显示 2.3万 帖子；`@justinsun` 显示「此账号不存在」；bio 指向中文号 `@sunyuchentron` |")
    out.append("| 曾颖 bio | 早稻田金融毕业｜TEDx演讲嘉宾｜币圈OG｜fobers u30 china｜34岁退休环游世界｜科技金融博主｜人生是场体验 |")
    out.append("| 孙宇晨 bio | Entrepreneur｜Diplomat｜Astronaut #712｜Founder @trondao｜Advisor b.ai / bt.io / htx.com |")
    out.append("")

    out.append("## 一、曾颖：颖学样本（提到目标，%d 条，全文）" % len(target_posts))
    out.append("")
    for row in target_posts:
        out += head(row) + block(row)

    out.append("## 二、曾颖：《》题名长文（%d 篇，全文）" % len(essays))
    out.append("")
    for row in essays:
        out += head(row) + block(row)

    out.append("## 三、曾颖：其他长文样本（%d 条，全文）" % len(other_long))
    out.append("")
    for row in other_long:
        out += head(row) + block(row)

    titles = []
    for row in essays:
        m = TITLE.match(row["text"].lstrip())
        if m:
            titles.append((row["date"], m.group(0), row["id"]))
    out.append("## 四、曾颖：《》题名清单（%d 条）" % len(titles))
    out.append("")
    out.append("题名短章是她中长文的固定外形：《》包住一个抽象名词或意象，正文用短句分行。")
    out.append("")
    for date, title, tid in titles:
        out.append("- %s ｜ %s ｜ https://x.com/zengying1107/status/%s" % (date, title, tid))
    out.append("")

    out.append("## 五、孙宇晨：声音样本（对照组）")
    out.append("")
    out.append("孙宇晨的公开语体是**公关稿体**：英文为主、结论先行、数据背书、偶配 emoji 与话题标签；中文多为口号式短句。"
               "`@justinsuntron` 自述其内容产品为「孙学」（见 2026-10-10 一条）。全量语料见 `sun-yuchen-skill` 仓库。")
    out.append("")
    control = [r for r in sun if r["date"] >= "2026-10-01"]
    for row in control:
        out += head(row) + block(row)

    peak = [r for r in zeng if "薄肌大水" in r["text"]]
    out.append("## 六、2026-10-11 颖学长样本（薄肌大水 → 大壶兴国论）")
    out.append("")
    out.append("把对方的口头禅接住、放大、改造成一套完整的伪理论，再落到数字与口号——这是「颖学」最完整的一次演示，"
               "也是 `SKILL.md` 里「反差 + 数字 + 不评论」三件套的原型样本。")
    out.append("")
    for row in peak:
        out += head(row) + block(row)

    text = "\n".join(out).rstrip() + "\n"
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote %s (%d chars)" % (OUT, len(text)))


if __name__ == "__main__":
    main()
