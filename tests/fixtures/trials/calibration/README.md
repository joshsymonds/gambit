# Trial calibration examples

Place one JSON object in this directory for each saved subject response. The file name identifies the example in calibration output.

```json
{
  "fixture": "skill/name",
  "response": "The saved subject response.",
  "expected": {
    "hard-line criterion text": "pass",
    "End state: expected outcome": "fail"
  },
  "note": "Optional human context."
}
```

`fixture` is a fixture identifier under `tests/fixtures/trials`, written as `<skill>/<name>`. `response` is the exact response sent to the judge. `expected` maps every hard-line criterion and the `End state: ...` criterion to `pass`, `fail`, or `unknown`. The criterion keys must match the referenced fixture exactly. `note` is optional and is ignored by the calibration runner.

Running `python3 tests/trials/calibrate.py` sends one judge request per example, prints agreement for each criterion, and prints the aggregate count. Add `--dry-run` to print the judge prompts without sending requests.
