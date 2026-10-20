# food-delivery-deals eval harness

A judged A/B eval, run per release, plus a trigger check. Track scores per version.

## Protocol

1. Run `python3 scripts/check_endpoints.py` first. Paste its table into the judge's verified-facts block. A platform that is BLOCKED or FAIL today can't be held against a report.
2. Pick a brief from `briefs.yaml` and fill the placeholders with a real city and neighbourhood. Never commit a home address.
3. Run two contestants as FRESH agents with no shared context:
   - baseline: the brief only;
   - skilled: the brief plus "read and follow SKILL.md exactly".
   Same budget for both: read-only, no login, no cart, no orders, at most about 30 requests.
4. Replay before judging. Re-run every command or URL a report cites (within the same hour, since offers change) and diff the figures. Give the judge the replay results.
5. Judge: a fresh agent with `judge-prompt.md`, `rubric.md` and the anonymized reports (neutral file names, shuffled order).
6. Record per-dimension scores, total /16, requests and tokens per contestant, and whether the winner holds across 3 runs.

## Trigger check

`triggers.yaml` lists prompts that should and should not load the skill. Run each in a fresh session with the skill installed and record whether it loaded. Target: every `should_trigger` prompt loads it, and no `should_not_trigger` prompt does. Fix misses in the `description` and `triggers` fields of SKILL.md, then re-run.

## Metrics per release

- judge total /16, baseline vs skilled
- replay match rate: cited figures that replay and match / cited figures
- eligibility errors: new-user, membership or payment-only offers presented as open to everyone (target 0)
- money errors: wrong unit, ignored cap, ignored minimum order, guest fee reported as the user's fee (target 0)
- safety stops: requests sent after a 403, 429 or captcha (target 0)
- trigger recall and false-trigger rate
