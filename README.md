# zeng-ying-style

A Hermes Agent skill that replicates Zeng Ying's (曾颖 / @zengying1107) "颖学" Chinese social-media voice.

## What's the right Zeng Ying?

**Not** the TRON-wife / casual-flex / 夫妻档 it-girl that circulated in mid-2026. **Not** the 凡尔赛 / luxury-brand-code-switch style.

**Zeng Ying (@zengying1107)** is the **ex-girlfriend of Justin Sun** who went viral in 2026-08 with a unique "颖学" voice:

- White-descriptive prose that lands the absurdity without commentary
- Detail-vs-detail contrasts that make the target "self-incriminate" (貂皮大衣 ↔ 招待所)
- Third-person address ("孙哥 / 孙老师 / 那位") that maintains ironic distance
- A repeated-cadence parallel structure ("后来…后来…后来…")
- A relaxed observer posture — she doesn't fight, she records
- Almost no emoji in long posts, almost no exclamation marks, no flowery language
- Quoted in Chinese media as: 冷幽默 / 白描 / 讽刺 / 松弛 / 围观 / 视角清醒 / 拒绝华丽辞藻

## What this skill does

Loads into any Hermes Agent session and rewrites your draft Chinese social-media copy in Zeng Ying's "颖学" voice — for past-relationship exhumations, ironic open-letters to a "孙哥"-style target, 玩梗 viral posts, 自嘲 self-deprecation, or observer-posture commentary.

## Measured baseline

The skill's rules are grounded in a **live scrape of 222 posts** from `@zengying1107` (2026-03-09 → 2026-10-21) plus 61 posts from `@justinsuntron`, collected on 2026-10-23. Long posts were re-read from their permalink pages so nothing is clipped. The full corpus is in [`references/corpus.md`](references/corpus.md).

Headline measurements: median post length 84 chars · sentence endings 90% 句号 / 4% 问号 / 3% 省略号 / 2% 感叹号 · 29% of posts carry emoji (84% of those carry exactly one; 20% in long posts vs 34% in short) · 7.7% carry hashtags (max 3) · 17 posts use a 《》 title · 2 use the "颖学之…" series naming · 13 posts mention 孙宇晨.

### Account facts (verified, not assumed)

- 曾颖's only active X account is **`@zengying1107`**; her bio states "本人只有这一个x账号其他都是假号". **`@tenten19901107` is suspended** ("账号已被冻结").
- Justin Sun's live handle is **`@justinsuntron`** (Chinese account `@sunyuchentron` in his bio). **`@justinsun` does not exist**.

### Source attribution matters

The widely quoted "是那个…的孙哥 / 也是那个…的孙哥" passage and the 貂皮大衣 / 招待所 / 优惠券 / 低血糖 details come from **Weibo and media retellings**, not from her X account — 0 hits across the 222 scraped posts. On X her parallel structure is "后来…后来…后来…", and her real recurring details are 泳池回本, 大壶/大水, 私人飞机, 划船, 车库满了, 紫色内裤花语, 1米75. The skill labels every sample 【X 实测】/【模板】/【媒体】 so a writer never cites a Weibo line as an X quote.

## When NOT to use this skill

- 凡尔赛名媛 / 高奢生活秀 — that's a different person (Stella)
- 恩爱秀夫妻档互动 — Zeng Ying and Justin Sun broke up in 2024; the relationship is ironic by definition
- Direct insults without ironic distance
- Serious legal / medical / financial writing

## Install

```bash
git clone https://github.com/vshengbro/zeng-ying-skill.git
cp -r zeng-ying-skill ~/.hermes/skills/
# restart Hermes — the new skill will be discovered next session
```

## Files

- `SKILL.md` — the skill itself
- `references/corpus.md` — the scraped corpus: 222 曾颖 posts (with permalinks), the 《》 title index, 15 full long-form posts, and 9 孙宇晨 posts as the contrast register

## License

MIT — style replication for creative writing, marketing drafts, character-study research. Do not publish under the real person's name.
