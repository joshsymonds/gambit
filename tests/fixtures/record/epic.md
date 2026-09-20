# Epic: config-loader

Repository: sundial. Accepted 2026-02-03T09:14:00+00:00 at 9d31ba7.

Sundial reads its configuration from the environment with typed overrides and named errors. Level of care: serious. Decisions needed: none.

## What you asked for
Running sundial in a container requires editing a file baked into the image, so every deployment carries a hand-patched copy. When this is done an operator sets configuration through the environment, sees a named error when a value is malformed, and never edits a packaged file to change a timeout.

## What could go wrong, and how much we care
| If this happened | How bad | What we do |
|---|---|---|
| F1 A malformed timeout was silently accepted and a deployment ran with the default | serious | prevent: a malformed value exits nonzero naming the field (R2) |
| F2 An unset key vanished when an override merged | serious | prevent: the merge case in `tests/test_config.py` asserts every default survives (R3) |
| F3 A deployment kept editing the packaged file after release | limited | accept: `deploy/README.md:41` names the environment as the surface |
Level of care: serious, set by F1. Effort ceiling: 4.

## Things you did not ask for
| Where | What | Why | Cost |
|---|---|---|---|
| R2 | The error names the failing field | The person asked for "a named error"; the field name is the smallest name that helps | none |

## What will be true when done
| Must be true | How we'll know |
|---|---|
| R1 Packaged defaults load with no environment set | `python3 -m pytest tests/test_config.py -q` passes the default-load case |
| R2 An environment override replaces the matching default with a typed value, and a malformed value exits nonzero naming the field | `SUNDIAL_TIMEOUT=abc python3 -m sundial` exits nonzero printing `timeout` |
| R3 Overrides merge onto defaults without dropping unset keys | `python3 -m pytest tests/test_config.py -q` passes the merge case |

## What I'm assuming
| Assumption | If wrong |
|---|---|
| P1 Configuration is read in exactly one place, `src/sundial/config.py:12-58` | Intent survives; every additional read site joins the first task's owned files |
| P2 No deployment depends on the packaged defaults file staying writable, per `deploy/README.md:41` | Intent cannot survive as written; the file would remain the supported configuration surface |

## What we won't do
- A second configuration read site. P1 is the whole basis for the task boundary.
- Reading configuration at import time. It makes the failure path untestable without a subprocess.

## How, and why not the other ways
One loader in `src/sundial/config.py` reads the packaged defaults, then applies typed environment overrides, raising a named error per field, grounded in P1.
| Alternative | Why not | Reconsider when |
|---|---|---|
| A configuration library | Three settings do not carry a dependency | The setting count passes twenty or nested structures appear |

## What leaves this machine or can't be undone
| Step | Target | Undo |
|---|---|---|
| 1 `git push origin main`, so the reviewed candidate is the published tip | sundial, branch main | push the prior tip |
| 2 `python3 -m build && python3 -m twine upload dist/*`, so version 0.4.0 resolves for a fresh install | the sundial package index entry | none |
Then: `git ls-remote origin main` names the candidate revision, and `pip download sundial==0.4.0` succeeds from an empty cache.

## Decisions I need from you
None.

## Checks the machines run
Done: `python3 -m pytest tests/test_config.py -q` from the repository root; `python3 -m pytest -q` then `python3 -m ruff check src tests`.
Evidence: the default-load and merge cases in `tests/test_config.py`; `SUNDIAL_TIMEOUT=abc python3 -m sundial` exiting nonzero printing `timeout`.
Quality Bar: Failing, low-quality, or bad code is unacceptable, but failure to meet a mythic platonic ideal of code or cover literally every imaginable edge case is NOT itself a defect. This bar is FIXED for every epic; write it verbatim — never elicit it, strengthen it, or make it a per-project preference. A defect is exactly one of: a Requirement's named evidence not met; a Must Not Ship entry present; a change outside the task's owned files; a change the contract did not ask for; a violation of the worker contract's mechanical floor (a suppressed check, a weakened or tautological test, dead code, an unhandled error); or a security or data-loss failure with a reachable precondition that the change itself introduces. Everything else the orchestrator or a reviewer notices is an observation — it may be recorded in the Decision Log and the report; it never becomes work during the run. The craftsmanship asked of the worker is one line: simple, foundational, secure; match the surrounding code.
