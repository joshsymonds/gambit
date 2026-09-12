# Decision Log (append-only)

Each entry: id | timestamp | decision | reason | evidence | supersedes. A reversal appends a new entry naming the one it supersedes; no entry is edited or removed.

- DL1 | 2026-02-03T09:14:00+00:00 | Configuration is read once, in src/sundial/config.py | reason: a second read site would make the malformed-value path untestable | evidence: config.py:12-58; deploy/README.md:41 | supersedes: none
- DL2 | 2026-02-03T09:14:00+00:00 | Override values are typed by the default they replace | reason: it keeps the field name available for the error message R2 requires | evidence: scout finding S3 | supersedes: none
- DL3 | 2026-02-04T11:20:06+00:00 | t2-loader is split into t2a-parse-env and t2b-merge-defaults | reason: the single task returned BLOCKED on two behaviors sharing one file | evidence: gates/t2-loader-1.md | supersedes: none
- DL4 | 2026-02-04T11:22:41+00:00 | Typing is resolved at parse time, not at merge time | reason: t2a owns the parser, so merge stays a dictionary operation over typed values | evidence: DL3 split boundary; config.py:31 | supersedes: DL2
