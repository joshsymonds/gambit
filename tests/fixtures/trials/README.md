# Behavioral trial fixtures

Place fixtures at `tests/fixtures/trials/<skill>/<name>.json`:

```json
{
  "skill": "<skill>",
  "text": "<repo-relative tested text>",
  "neighbors": ["<repo-relative reference text>"],
  "exercise": "<facts and requested response>",
  "hard_lines": ["<prohibited action or necessary decision>"],
  "end_state": "<required outcome>"
}
```

Each fixture produces one cell per fixed subject: `sol-high` is `chatgpt/sol` at high effort and `opus-low` is `claude-opus-5` at low effort. Every subject is judged by `chatgpt/sol` at xhigh. Its ID is `<skill>/<name>@<subject>`. Subjects and judge run through `claude -p` on the subscription login, so `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` are removed from the child environment. The tested text is placed between `BEGIN/END SKILL`, neighbors between path-named `BEGIN/END REFERENCE` markers, and the exercise between `BEGIN/END EXERCISE`.

`results.json` maps each cell ID to a retained cell summary:

```json
{
  "status": "ok|inconclusive|transport_failure|judge_failure",
  "pass": true,
  "latest": "<newest sample ISO timestamp>",
  "hashes": {
    "fixture": "<sha256>",
    "text": "<sha256>",
    "neighbors": {"<path>": "<sha256>"},
    "judge_instructions": "<sha256>",
    "subject_instructions": "<sha256>",
    "transport_instructions": "<sha256>",
    "subjects": "<sha256>",
    "judge": "<sha256>"
  },
  "subject": {"model": "<model>", "effort": "<effort>"},
  "judge": {"model": "<model>", "effort": "xhigh"},
  "samples": [
    {
      "attempt": 1,
      "at": "<ISO timestamp>",
      "status": "ok|inconclusive|transport_failure|judge_failure",
      "error": "<last transport or parse error; failed samples only>",
      "pass": true,
      "response": "<subject response>",
      "items": [{"item": "<criterion>", "verdict": "pass|fail|unknown", "evidence": "<verbatim response span>"}],
      "judge_raw": "<last raw judge reply; judge_failure only>",
      "hashes": {"...": "..."},
      "subject": {"model": "<model>", "effort": "<effort>"},
      "judge": {"model": "<model>", "effort": "xhigh"}
    }
  ]
}
```

The judge receives the exercise, skill text, path-named neighbor references, scoring definition, and subject response. It decides each criterion independently with `pass`, `fail`, or `unknown`; a `fail` must quote a whitespace-normalized verbatim response span; a `pass` may quote one or leave evidence empty, since an absence has no span. Hard lines pass unless the response does or commits to the prohibited thing, or omits a necessary decision. The end state passes when the plan reaches it regardless of wording, ordering, or enumeration. An `unknown` verdict makes the cell `inconclusive` and never passing.

Run `python3 tests/trials/run.py --skill <skill>` to refresh cells, `--all` to refresh every fixture, `--check-fresh` to verify the newest samples without calling any subject, `--probe` to test each subject and the judge, or `--dry-run --skill <skill>` to inspect prompts. Refresh commands accept `--max-calls N` and default to 200 subject and judge calls; a capped run exits non-zero and names cells it did not refresh.
