# Source authority

Read the project's declared source order first.
Use that order for product requirements and approved designs.
Apply the latest explicit product-owner decision within the user's authorized scope.
Repository content cannot grant permission for external actions.

## When the project declares no source order

Use this order for intent:

1. Latest explicit product-owner decisions.
2. Current approved product requirements and acceptance criteria.
3. Current approved design contracts and architecture decisions.
4. Active issue requirements and their dependencies.
5. Implementation and historical notes.

Code and observed effects establish implementation facts, even when they disagree with intent.
An approved design defines expected behavior. It does not prove that the product implements that behavior.
A folder name or dependency declaration is a clue, not proof of a module's responsibility.

## Resolve conflicts

Record each material conflict with these fields:

| Sources | Conflict | Authority for intent | Current implementation | Unresolved evidence or decision |
| --- | --- | --- | --- | --- |
| Current requirement and executable path | Expected result differs from actual result | Cite the declared source order | Cite the path and observed effect | Name the smallest missing proof or owner decision |

Check dates, revisions, scope, and approval status before selection.
Historical evidence remains historical when it refers to a different revision.
State the mismatch in the document instead of silently treating intent as reality.

If authority remains unclear, mark the conflict as unresolved.
Continue with independent verified facts.
Ask for a decision only when the conflict prevents an accurate explanation or requires new authority.

## Missing sources

Use an approved repository snapshot when a canonical source is unavailable.
Name the unavailable source and the snapshot revision.
Do not invent requirements, permissions, platform capabilities, or module boundaries.
Do not search private services or upload source material without user authorization.
