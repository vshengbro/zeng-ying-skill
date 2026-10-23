# zeng-ying-style

A Hermes Agent skill that replicates Zeng Ying's (曾颖 / @zengying1107) "颖学" Chinese social-media voice, rebuilt against a harvested corpus of her real posts.

## What's the right Zeng Ying?

**Not** the TRON-wife / casual-flex / 夫妻档 it-girl that circulated in mid-2026. **Not** the 凡尔赛 / luxury-brand-code-switch style.

**Zeng Ying (@zengying1107)** is the **ex-girlfriend of Justin Sun** who went viral in 2026-08 with a unique "颖学" voice:

- White-descriptive prose that lands the absurdity without commentary
- Detail-vs-detail contrasts that make the target "self-incriminate" (貂皮大衣 ↔ 刷墙 / 优惠券 ↔ 肯德基套餐)
- Third-person address ("孙割 / 孙哥 / 孙老师") that maintains ironic distance
- Repeated-cadence short-line groups ("放下大水，立地成壶。/ 每天省下10块钱…")
- A relaxed observer posture — she doesn't fight, she records
- Almost no emoji (77% of posts have none), almost no exclamation marks, no flowery language
- Quoted in Chinese media as: 冷幽默 / 白描 / 讽刺 / 松弛 / 围观 / 视角清醒 / 拒绝华丽辞藻

## What this skill does

Loads into any Hermes Agent session and rewrites your draft Chinese social-media copy in Zeng Ying's "颖学" voice — for past-relationship exhumations, ironic open-letters to a "孙哥"-style target, 玩梗 viral posts, 自嘲 self-deprecation, or observer-posture commentary. It also covers her second register, the 《》-titled Chinese prose essay (读经 / 敦煌 / 健身 / 人生清单).

## Corpus-grounded

Every rule in `SKILL.md` was measured against **637 of her own posts** (@zengying1107, 2026-02-26 → 2026-10-22), not against media paraphrase. The measurements corrected several things the earlier version of this skill got wrong:

| Earlier claim | Measured reality |
| --- | --- |
| Signature cadence is "是那个…的孙哥 / 也是那个…的孙哥" | That sentence appears **0 times** in 637 posts. Her real cadence is 对仗短语组. |
| "那位 / 某人 / 波场那位" as her address terms | "某人" and "波场那位" appear **0 times**; the one "那位" is unrelated. She writes 孙割 (19), 孙哥 (21), 孙老师 (6), 孙宇晨 (6). |
| Hashtag is her one permitted ornament | Emoji is used far more often (23% of posts vs 2.5% with a hashtag); 😂 is the signature. |
| 80% of sentences end in a full stop | Post-level: 29%. Sentence-level among punctuated sentences: 89%. 44% of posts end with no punctuation at all. |
| "@tenten19901107" is the main account | It is **suspended**. @zengying1107 is the only live account, and her bio says so. |
| "孙学的本质是赢学" is her line | It is **Justin Sun's own 2026-03-07 post** (1,246 likes). Hers is "孙学就是颖学". |

## When NOT to use this skill

- 凡尔赛名媛 / 高奢生活秀 — that's a different person (Stella)
- 恩爱秀夫妻档互动 — Zeng Ying and Justin Sun broke up in 2024; the relationship is ironic by definition
- Direct insults without ironic distance
- Serious legal / medical / financial writing

## Install

```bash
git clone https://github.com/vshengbro/zeng-ying-skill.git
# the directory must carry the skill's name (frontmatter name: zeng-ying-style)
mv zeng-ying-skill zeng-ying-style
cp -r zeng-ying-style ~/.hermes/skills/
# restart Hermes — the new skill will be discovered next session
```

## Files

- `SKILL.md` — the skill itself
- `references/tweets.jsonl` — all 787 harvested posts (id, date, engagement, permalink, text): 637 from @zengying1107, 150 from @justinsuntron
- `references/samples.md` — curated Zeng Ying samples grouped by register, each with date, like count and permalink
- `references/sun_samples.md` — the Justin Sun **control group**, same platform and months, a completely different voice
- `references/corpus.md` — a second reading copy of the corpus, organised by topic instead of by register
- `references/ids.txt` — the status ids, for re-harvesting
- `scripts/harvest_x.py` — re-fetch the corpus and print the style statistics

## Refreshing the corpus

```bash
python3 scripts/harvest_x.py references/ids.txt --out references/tweets.jsonl --stats
```

The script pulls each post by status id from the public fxtwitter mirror API and reports the per-account statistics (length, emoji share, hashtag share, reply share) used in `SKILL.md`.

## License

MIT — style replication for creative writing, marketing drafts, character-study research. Do not publish under the real person's name.
