# hotel-hunting eval harness

Quantified regression eval. Run per release; track scores per version.

## Protocol

1. Pick a brief from `briefs.yaml` (or a private known-stay anchor; see below).
2. Run contestants as FRESH agents (no shared context):
   - baseline: brief only, plus "Use hotelist.com/mcp."
   - skilled: brief plus "read and follow SKILL.md exactly".
   Same lookup cap (~12), read-only, never book or sign in.
3. VERIFY TOOL AVAILABILITY EMPIRICALLY before judging: run
   `scripts/hotelist.py search "<city>"` yourself; replay every acquisition
   command cited in the reports and diff claimed vs returned values. Hand the
   judge a verified-facts block. Never assert availability from assumption:
   one wrong premise silently moves 1-3 points per report.
4. Judge: fresh agent, `judge-prompt.md` + `rubric.md` + anonymized reports
   (neutral filenames, shuffled order).
5. Record: per-dimension scores, total /16, tokens and tool calls per
   contestant, winner stability across repeat runs.

## Metrics tracked per release

- judge total /16 (baseline vs skilled)
- anchor recall: % of known-stay positive anchors surfaced WITH a gate verdict
- reproducibility: replayed-and-matching Hotelist figures / cited figures
- negative-coverage completeness: finalists with full query matrix / finalists
- D5 price-honesty mean; points per 100k tokens
- winner stability across 3 runs, conditioned on identical negative-coverage
  matrices (asymmetric coverage legitimately flips winners; only same-coverage
  disagreement counts as instability)
- paired uplift (skill vs no-skill) sized on discordant pairs (McNemar), not a
  one-proportion bound; report raw counts, no decimals below n=30

## Private anchors

Known-stay ground truth (real hotels the maintainer stayed at) lives OUTSIDE
this repo. The harness loads it from `$HOTEL_EVAL_ANCHORS` (a YAML/markdown
file) when set. Never commit hotel names or personal stay data here; names in
the repo would also skew agent outputs.
