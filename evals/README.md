# Synthetic evaluations

These evaluations use only the fictional [Acorn Tasks fixture](../demo/acorn-tasks/README.md).
They do not contain customer data or prove real-channel acceptance.

## Deterministic checks

The [cases](cases.json) define six pressure scenarios and their document properties.
The [rubric](run_rubric.py) accepts a case identifier and a Markdown file.
It prints JSON with `case`, `passed`, and named `checks`.
Exit status is 0 only when every check passes. A failed document or unknown case returns status 1.

The rubric checks heading subjects, broad phrase groups, evidence labels, Mermaid count,
local source links, forbidden claims, closed fences, and Chinese prose when required.
It excludes fenced examples from prose checks. It checks labels and links, not exact prose.
It cannot prove claim truth, diagram semantics, diagram render quality, or complete source authority.
A pass requires a separate human review of those properties before acceptance.

The static, conflict, and refresh cases use explicit scenario overrides.
They do not change the executable `synthetic-v1` fixture.
The bootstrap case name retains `agent-product`, but the fixture is an ordinary service.
An agent must explain a loop only when inspected code supports that loop.

Run from the package root:

```bash
python3 evals/run_rubric.py --case bootstrap-agent-product --document evals/baseline/no-skill.md
python3 evals/run_rubric.py --case bootstrap-agent-product --document demo/expected/HOW_IT_WORKS.md
python3 -m unittest tests.test_rubric -v
python3 -m unittest discover -s demo/acorn-tasks/tests -v
python3 -m unittest discover -v
```

The first command must fail. The remaining commands must pass.
The fixture tests use a separate command because root discovery does not enter the hyphenated demo directory.
The [weak baseline](baseline/no-skill.md) is a hand-written negative control.
It is not a fresh-agent result.
The [expected document](../demo/expected/HOW_IT_WORKS.md) is a hand-written positive control.
Its fictional runtime record does not prove actual execution.

## Fresh-agent procedure

Fresh-agent results remain pending for the controller.
Do not fabricate agent outputs or copy the expected document as an agent result.

Run one new agent with the main skill disabled. Run another new agent with the main skill enabled.
Use the same bootstrap request from `cases.json` and the same fixture for both agents.
Run the agents sequentially. Save only their synthetic final documents under `evals/runs/0.1.0/`.
Keep separate isolated fixture copies so instruction setup in one run cannot affect the other run.
Include the exact enabled or disabled skill state in the run record.
Keep source paths relative to the saved document, or place a synthetic fixture copy beside it.

Run the rubric against each document. Record the command, client, model family, date, and result here.
If a client or model family is unknown, write `unknown`. Do not infer that value.
Save no hidden reasoning, private transcripts, real identifiers, secrets, or home-directory paths.

| Run | Client | Model family | Date | Result |
| --- | --- | --- | --- | --- |
| Baseline fresh agent, main skill disabled | Pending | Pending | Pending | Pending |
| Fresh agent, main skill enabled | Pending | Pending | Pending | Pending |

## Deterministic evidence record

Date: 2026-10-14. Environment: Python 3.9.6, macOS arm64.
The task report records the exact implementation commit and full-suite result.

| Command | Observed result |
| --- | --- |
| `python3 -m unittest tests.test_rubric -v` before implementation | Exit 1, 4 failures and 6 errors from absent scorer or document |
| `python3 -m unittest discover -s demo/acorn-tasks/tests -v` before implementation | Exit 1, import error from absent service |
| `python3 evals/run_rubric.py --case bootstrap-agent-product --document evals/baseline/no-skill.md` | Exit 1, failed headings, phrases, evidence labels, diagrams, and local links |
| `python3 evals/run_rubric.py --case bootstrap-agent-product --document demo/expected/HOW_IT_WORKS.md` | Exit 0, all 7 checks passed |
| `python3 -m unittest tests.test_rubric -v` after implementation | Exit 0, 13 tests passed |
| `python3 -m unittest discover -s demo/acorn-tasks/tests -v` after implementation | Exit 0, 9 tests passed |

Fresh-agent evaluation is a separate step and remains pending.
