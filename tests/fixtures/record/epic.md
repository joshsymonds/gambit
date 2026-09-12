# Epic: config-loader

Repository: sundial. Accepted 2026-02-03T09:14:00+00:00 at 9d31ba7.

## Intent

Running sundial in a container requires editing a file baked into the image, so every deployment carries a hand-patched copy. The desired end state is that an operator sets configuration through the environment, sees a named error when a value is malformed, and never edits a packaged file to change a timeout.

## Premises

- P1: Configuration is read in exactly one place, `src/sundial/config.py:12-58`. If false, the Intent survives with the stated design consequence: every additional read site joins the first task's owned files.
- P2: No deployment depends on the packaged defaults file staying writable, per `deploy/README.md:41`. If false, the Intent cannot survive as written, because the file would remain the supported configuration surface.

## Requirements

- R1: Packaged defaults load with no environment set. Evidence: `python3 -m pytest tests/test_config.py -q` passes the default-load case.
- R2: An environment override replaces the matching default with a typed value, and a malformed value exits nonzero naming the field. Evidence: `SUNDIAL_TIMEOUT=abc python3 -m sundial` exits nonzero printing `timeout`.
- R3: Overrides merge onto defaults without dropping unset keys. Evidence: `python3 -m pytest tests/test_config.py -q` passes the merge case.

## Must Not Ship

- A second configuration read site. Reason: P1 is the whole basis for the task boundary.
- Reading configuration at import time. Reason: it makes the failure path untestable without a subprocess.

## Quality Bar

Failing, low-quality, or bad code is unacceptable, but failure to meet a mythic platonic ideal of code or cover literally every imaginable edge case is NOT itself a defect. This bar is FIXED for every epic; write it verbatim — never elicit it, strengthen it, or make it a per-project preference. A defect is exactly one of: a Requirement's named evidence not met; a Must Not Ship entry present; a change outside the task's owned files; a change the contract did not ask for; a violation of the worker contract's mechanical floor (a suppressed check, a weakened or tautological test, dead code, an unhandled error); or a security or data-loss failure with a reachable precondition that the change itself introduces. Everything else the orchestrator or a reviewer notices is an observation — it may be recorded in the Decision Log and the report; it never becomes work during the run. The craftsmanship asked of the worker is one line: simple, foundational, secure; match the surrounding code.

## Approach and Rejected Approaches

Chosen: one loader in `src/sundial/config.py` that reads the packaged defaults, then applies typed environment overrides, raising a named error per field, grounded in P1.
Rejected: a configuration library. Reason: three settings do not carry a dependency. Reconsider only if the setting count passes twenty or nested structures appear.

## Done

- Task fast check: `python3 -m pytest tests/test_config.py -q` from the repository root.
- Integrated candidate full gate: `python3 -m pytest -q` then `python3 -m ruff check src tests`.

## Release

1. Action: `git push origin main`. Target: sundial, branch main. Intended effect: the reviewed candidate is the published tip.
2. Action: `python3 -m build && python3 -m twine upload dist/*`. Target: the sundial package index entry. Intended effect: version 0.4.0 resolves for a fresh install.
Postconditions: `git ls-remote origin main` names the candidate revision, and `pip download sundial==0.4.0` succeeds from an empty cache.
