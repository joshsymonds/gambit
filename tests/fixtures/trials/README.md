# Behavioral trial fixtures

Place fixtures at `tests/fixtures/trials/<skill>/<name>.json`:

```json
{
  "skill": "<skill>",
  "text": "<repo-relative tested text>",
  "neighbors": ["<repo-relative reference text>"],
  "exercise": "<facts and requested response>",
  "checklist": ["<binary scoring item>"]
}
```

Each fixture produces one cell per fixed subject: `opus-low` is `claude-opus-5` at low effort and `fable-high` is `claude-fable-5-1` at high effort, judged by `claude-fable-5-1` at xhigh. Its ID is `<skill>/<name>@<subject>`. Subjects and judge run through `claude -p` on the subscription login, so `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` are removed from the child environment. The tested text is placed between `BEGIN/END SKILL`, neighbors between path-named `BEGIN/END REFERENCE` markers, and the exercise between `BEGIN/END EXERCISE`.

`results.json` maps each cell ID to:

```json
{
  "status": "ok|transport_failure|judge_failure",
  "pass": true,
  "hashes": {
    "fixture": "<sha256>",
    "text": "<sha256>",
    "neighbors": {"<path>": "<sha256>"}
  },
  "subject": {"model": "<model>", "effort": "<effort>"},
  "judge": {"model": "<model>", "effort": "xhigh"},
  "response": "<subject response>",
  "items": [{"item": "<checklist item>", "pass": true, "evidence": "<quote>"}],
  "judge_raw": "<last raw judge reply; judge_failure only>",
  "at": "<ISO timestamp>"
}
```

Run `python3 tests/trials/run.py --skill <skill>` to refresh cells, `--all` to refresh every fixture, `--check-fresh` to verify hashes and passing scores without calling any subject, `--probe` to test each subject and the judge, or `--dry-run --skill <skill>` to inspect prompts.
