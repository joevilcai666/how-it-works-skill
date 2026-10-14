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

The controller ran two new agents sequentially with the same synthetic bootstrap request.
The saved outputs below are their generated documents, not copies of the expected control.

Run one new agent with the main skill disabled. Run another new agent with the main skill enabled.
Use the same bootstrap request from `cases.json` and the same fixture for both agents.
Run the agents sequentially. Save only their synthetic final documents under `evals/runs/0.1.0/`.
Keep separate isolated fixture copies so instruction setup in one run cannot affect the other run.
Include the exact enabled or disabled skill state in the run record.
Keep source paths relative to the saved document, or place a synthetic fixture copy beside it.

Run the rubric against each document. Record the command, client, model family, date, and result here.
If a client or model family is unknown, write `unknown`. Do not infer that value.
Save no hidden reasoning, private transcripts, real identifiers, secrets, or home-directory paths.

| Run and main skill state | Client | Model family | Date | Observed result |
| --- | --- | --- | --- | --- |
| [Baseline fresh agent](runs/0.1.0/baseline/HOW_IT_WORKS.md), disabled | Codex collaboration subagent | gpt-6.1-sol | 2026-10-14 | Fail, exit 1, 4 of 7 checks passed |
| [Fresh agent](runs/0.1.0/skilled/HOW_IT_WORKS.md), enabled | Codex collaboration subagent | gpt-6.1-sol | 2026-10-14 | Fail, exit 1, 6 of 7 checks passed |

Exact baseline command from the package root:

```bash
python3 evals/run_rubric.py --case bootstrap-agent-product --document evals/runs/0.1.0/baseline/HOW_IT_WORKS.md
```

The baseline fails the headings, evidence-labels, and mermaid-count checks.
Its headings omit limits and sources. Its prose describes several evidence types, but does not match the code, test, and runtime labels.
It contains one Mermaid block and twelve valid local links.
Its output commit is `fffc2fd515f82e3288c4c0d5da234ca896dc36a2`.

Exact skill-enabled command from the package root:

```bash
python3 evals/run_rubric.py --case bootstrap-agent-product --document evals/runs/0.1.0/skilled/HOW_IT_WORKS.md
```

The skill-enabled output fails only the mermaid-count check.
It contains two Mermaid blocks and twenty-one valid local links.
It passes the heading, phrase, evidence-label, local-link, forbidden-phrase, and closed-fence checks.
Its output commit is `ee7567ec5c5fa1b71ef10d6cad33f30b0bc9841d`.
The agent ran instruction setup in an isolated temporary fixture copy.
It changed no repository fixture or root instructions.

This case requires three diagrams. The main skill permits two to four diagrams.
The shared request does not explicitly require three diagrams.
Thus the skill-enabled output meets the skill's diagram-count range but fails the stricter case rule.
These recorded scores use the original rubric. Neither output nor scoring rules changed to improve a result.
The two runs show one model family in one client. They do not prove cross-client compatibility or human acceptance.

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

Fresh-agent evaluation is complete for these two synthetic runs.
Both outputs fail the original bootstrap rubric for the reasons above.
