# zeng-ying-style

A Hermes Agent skill for Zeng Ying's (曾颖 / @zengying1107) Chinese writing voice, expression habits, and stated ideas, grounded in her public X posts. Version 1.4.0 separates rhetorical analysis from the author's opinions and from verified facts.

## More than ironic breakup stories

Her public writing uses several registers, not a single fixed persona:

- Detail-driven satire: build an expectation, then let an ordinary object, action, or receipt overturn it.
- Personal argument: revisit an old assumption, make hidden costs visible, and draw a practical boundary.
- Reflective memoir: preserve affection, regret, and vulnerability through concrete objects and scenes.
- Practical tutorials: state personal circumstances, numbered steps, exceptions, and conditions that require verification.
- Public advocacy: make judgments and express compassion, rather than always remaining a neutral observer.
- Short replies: follow the current conversation and change one keyword or explanation to land a joke.

The historical baseline shows that 77% of posts contain no emoji. That distribution is a useful default, not a per-post prohibition. Third-person nicknames and restrained commentary belong to particular satirical contexts, not every subject she writes about.

## What this skill does

Use it to analyze her posts or draft Chinese social-media writing with an appropriate register. The skill covers satire, reflection, argument, practical explanation, and replies. It also distinguishes her stated ideas about autonomy, hidden costs, emotional costs, attention and cooperation, privacy, desire, and compassion from the analyst's rhetorical categories. Do not invent real people's experiences to make a draft resemble the samples.

## Corpus-grounded

The historical statistics were measured against **892 of her own posts** (@zengying1107, 2026-02-12 → 2026-10-22), not against media paraphrase. This is a dated sample, not her complete or current timeline. The measurements corrected several things the earlier version of this skill got wrong:

| Earlier claim | Measured reality |
| --- | --- |
| Signature cadence is "是那个…的孙哥 / 也是那个…的孙哥" | That sentence appears **0 times** in 892 posts. Her real cadence is 对仗短语组. |
| "那位 / 某人 / 波场那位" as her address terms | "某人" and "波场那位" appear **0 times**; of the 4 "那位" hits, only "反派的那位" points at him. She writes 孙割 (28), 孙哥 (25), 孙老师 (6), 孙宇晨 (9). |
| Hashtag is her one permitted ornament | Emoji is used far more often (23% of posts vs 2.8% with a hashtag); 😂 is the signature. |
| 80% of sentences end in a full stop | Post-level: 29%. Sentence-level among punctuated sentences: 88%. 45% of posts end with no punctuation at all. |
| Her register is uniform | It is not: all 5 baseline posts matching the defined insult-word list occur in 2026-02/03. Later samples span satire, reflection, tutorials, advocacy, and commercial writing; no keyword hit is not proof that all later language is restrained. |
| "@tenten19901107" is the main account | It is **suspended**. @zengying1107 is the only live account, and her bio says so. |
| "孙学的本质是赢学" is her line | It is **Justin Sun's own 2026-03-07 post** (1,246 likes). Hers is "孙学就是颖学". |

## Focused reading update: October 24, 2026

The update retrieved **65 public posts in full**, selected **36 evidence posts**, and indexed **14 selected posts absent from the historical baseline**. It used the account's profile, replies, and author-restricted X search. **5 creator-subscription posts** showed only public previews and were excluded from full-text analysis.

- `references/voice-and-theory.md` explains the writing mechanisms, register choices, stated ideas, and tensions between different posts. Every source has a permalink.
- `references/style_evidence.json` records short exact excerpts, authorship, UTC publication times, full-text character counts, and SHA-256 digests. It does not duplicate the long articles.
- The 892-post baseline is unchanged. The focused supplement is not mixed into its statistical denominator.
- Personal economic, psychological, religious, historical, and legal assertions remain the author's claims, not verified professional conclusions. Her quoted classics and other people's words are not automatically her original theories.

## When NOT to use this skill

- Impersonating the real account or attributing invented experiences or statements to real people.
- Treating one register as a universal template, especially banning emotion, judgment, or sincere affection.
- Presenting the author's personal views as legal, medical, psychological, or financial advice.

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
- `references/tweets.jsonl` — all 892 harvested posts (id, date, engagement, permalink, text)
- `references/samples.md` — curated samples grouped by register, each with date, like count and permalink
- `references/sun_samples.md` — the Justin Sun **control group**: 798 posts from the same months, useful for comparing selected registers rather than defining either author's entire voice
- `references/corpus.md` — a second reading copy of the corpus, organised by topic instead of by register
- `references/ids.txt` — the status ids, for re-harvesting
- `references/samples_spec.json` — the selection rules `scripts/emit_samples.py` uses to build `samples.md`
- `references/voice-and-theory.md` — focused close reading of rhetoric, expression habits, and stated ideas, with a source index
- `references/style_evidence.json` — dated evidence metadata, short excerpts, digests, and access-limit exclusions
- `scripts/harvest_x.py` — re-fetch the corpus and print the style statistics
- `scripts/verify_claims.py` — assert every statistic the docs quote against the corpus
- `scripts/verify_doc_numbers.py` — re-read the published prose and check each number in it against the corpus
- `scripts/verify_style_evidence.py` — check the focused evidence offline, re-fetch it with `--live`, and exercise negative fixtures with `--self-test`

## Refreshing the corpus

```bash
python3 scripts/harvest_x.py references/ids.txt --out references/tweets.jsonl --stats
```

The script pulls each post by status id from the public fxtwitter mirror API and reports the per-account statistics (length, emoji share, hashtag share, reply share) used in `SKILL.md`.

`references/samples.md` is generated, not hand-written, so it cannot drift away from the corpus:

```bash
python3 scripts/emit_samples.py references/tweets.jsonl references/samples.md references/samples_spec.json
```

Two more files are generated the same way, so they cannot drift either:

```bash
python3 scripts/build_corpus_md.py       # references/corpus.md  — topic-ordered reading copy
python3 scripts/build_sun_samples.py     # references/sun_samples.md — the Sun control group
```

And `scripts/verify_claims.py` asserts every statistic quoted in `SKILL.md` and this README against `references/tweets.jsonl`, exiting non-zero on a mismatch. `scripts/verify_doc_numbers.py` then re-reads the published prose and checks each number it states against the corpus, so a figure that drifted out of the docs is caught rather than shipped. Run both after any harvest:

```bash
python3 scripts/verify_claims.py
python3 scripts/verify_doc_numbers.py
python3 scripts/verify_style_evidence.py
python3 scripts/verify_style_evidence.py --live
python3 scripts/verify_style_evidence.py --self-test
```


## License

MIT — style replication for creative writing, marketing drafts, character-study research. Do not publish under the real person's name.
