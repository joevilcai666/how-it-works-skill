# Output contract

Create one authoritative `HOW_IT_WORKS.md` at the project root.
Use the user's language for the document and product-owner summary.
Translate section titles without changing their purpose.
Explain current behavior. Do not write a change log or implementation diary.

## Required sections

Use this order. Combine adjacent sections when that makes the document easier to read.
Keep each required subject present even when its evidence is unavailable.

| Section | Required content |
| --- | --- |
| Product position | One sentence about the user, problem, and current product role |
| Current verified status | Important capability claims, evidence types, scope, and missing proof |
| Overall behavior | Main user flows, system boundaries, and a useful architecture diagram |
| Core workflow | Actual agent or service workflow, decisions, effects, and relevant recovery paths |
| Representative request | One input-to-result trace with a sequence diagram |
| Concepts | Plain definitions and short analogies for necessary technical concepts |
| Module responsibilities | Module, product responsibility, boundary, and source link |
| Current decisions | Material trade-offs and constraints that affect current behavior |
| Diagnosis | Symptom-first guidance with evidence and proof requirements |
| Limits and evidence gaps | What remains unknown, absent, simulated, or unaccepted |
| Sources and review record | Source links, analyzed revision, relevant local changes, and last-reviewed date |

For an absent subject, write an explicit statement such as “No agent workflow exists in this product.”
Do not invent a workflow, module, decision, or acceptance result to fill a section.
Use two to four diagrams that explain distinct relationships.
Use product terms in diagrams, then connect them to source paths in the module table.

## Optional sections

Add these sections only when they explain current user behavior:

- State lifecycle for persistence, retries, restart, or cancellation.
- Data flow for storage, trust boundaries, or external delivery.
- Permission boundaries and execution ownership.
- Internal agent cooperation when the product actually contains it.
- Operational checks with recorded commands, environment, revision, and results.

## Clear explanations

Use short sentences and consistent names.
Explain one important concept per paragraph.
For example: “A queue holds work until a worker can process it. It acts like a service counter's ticket line.”
Then state the analogy's practical limit when that limit affects behavior.
Distinguish verified behavior, an uncertain explanation, and a recommended check.

## Refresh rules

Compare the existing document with current sources and evidence.
Update affected journeys, modules, concepts, diagrams, claims, and limits.
Preserve accurate current content.
Remove obsolete behavior instead of appending its replacement as history.
Do not create a second language version without an explicit request.
Keep project-specific facts out of global instruction files.

## Validation and handoff

Check every required subject and local source link.
Check diagram source, code fences, labels, and arrow directions against the traced behavior.
State when no diagram renderer is available. Do not claim a render check without an actual render.
Fix invalid diagram syntax or broken local links before completion.
Check that evidence descriptions match their actual scope.

Put the last-reviewed date at the bottom in `YYYY-MM-DD` form.
Use “最后核对日期” for Chinese documents.
Record the actual review date, analyzed revision, and relevant local changes.
Do not imply that the review date is a runtime or acceptance date.

Deliver an instruction setup report and validation results with the document.
Give the product owner 2–3 sentences about the document's result and its most important limit.
State any required user action.
