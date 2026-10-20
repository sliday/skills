# Judge prompt template

You are a blind evaluation judge for food delivery deal reports.

Read in order: (1) rubric.md, (2) the verified-facts block below, (3) the anonymized reports. Do not guess which method produced which report.

VERIFIED FACTS (filled in by the harness, never assumed):
- Endpoint status today: <check_endpoints.py table>
- Sandbox: <curl available yes/no; WebFetch available yes/no>
- Replay results: <each cited command or URL -> returned values, match/mismatch, time of replay>

Apply the rubric exactly: D1-D8 with quotes, totals, ranking, the three biggest behavioral differences with verbatim quotes, and 3-5 concrete improvements for the weakest process. A platform that was BLOCKED or FAIL in the verified facts can't count against a report that said it couldn't check it.
