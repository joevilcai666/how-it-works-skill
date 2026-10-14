---
name: how-it-works
description: Create or refresh a visual, evidence-aware HOW_IT_WORKS.md for a non-technical product owner. Use when someone asks how a codebase, product flow, agent loop, data flow, module, or user request works, or when product-visible behavior changed and the living explanation must be updated.
license: MIT
metadata:
  version: "0.1.0"
---

# How It Works

Explain current behavior in one project-root `HOW_IT_WORKS.md`.
Use the user's language and plain product terms.
Keep project facts in the project, without uploads or telemetry.

## Workflow

Follow these steps in order. Read each reference before its related work.

1. Run project instruction setup in the user's language.
   Resolve the project root and this installed skill's directory.
   Use `zh-CN` for Chinese instructions and `en` for English instructions.
   For other languages, use `en` for setup and retain the user's language in the document.
   Run the [updater](scripts/update_project_instructions.py) through Python:

   ```bash
   python3 "<skill-directory>/scripts/update_project_instructions.py" --project-root "<project-root>" --language en
   ```

   Replace the path values and language before execution.
   Report the modified files from the updater's result.
   If setup fails, report the exact error. Do not bypass its ownership checks.

2. Read project instructions before investigation.
   Read applicable `AGENTS.md`, `CLAUDE.md`, and their active project imports.
   Read the existing `HOW_IT_WORKS.md` if present.

3. Establish source authority and mark conflicts.
   Apply [source authority](references/source-order.md).
   Separate product intent from actual implementation.

4. Inspect the product and its available evidence.
   Inspect product intent, entry points, state, external effects, tests, and deployment declarations.
   Inspect available runtime evidence.
   Record the revision, local changes, commands, environments, and results that support important claims.
   Use read-only checks and authorized local tests.
   A document request does not authorize deployment, paid purchases, or real messages.

5. Trace one representative user request end to end.
   Follow input, decisions, state changes, external effects, and the visible result.
   Inspect relevant permission checks, retries, duplicate events, cancellation, restart, and failure paths.
   Mark absent or unknown paths explicitly.

6. Classify every important claim by evidence level.
   Apply [evidence rules](references/evidence.md): code verified, test verified, runtime verified, and user accepted.
   Attach source links and the limits of each claim.

7. Write or refresh only current-state content.
   Apply the [output contract](references/output-contract.md).
   Use two to four useful Mermaid diagrams under the [diagram rules](references/diagrams.md).
   Use the [symptom-first diagnosis format](references/diagnosis.md).
   On refresh, update affected sections and remove false statements.
   Do not add a change history or a parallel translation without a user request.

8. Validate the document before completion.
   Check source links, required sections, evidence wording, code fences, and diagram syntax.
   Render diagrams when a renderer is available.
   Record whether diagram checks cover source syntax or actual rendering.
   Fix broken local links and invalid diagrams.
   Update the last-reviewed date at the bottom.
   Record the analyzed revision and local changes when available.

9. Tell the product owner what changed in 2–3 sentences.
   State the document's useful result and the most important evidence limit.
   Include required user action if work remains.

## Completion

Deliver the document, instruction setup report, and validation results.
Missing runtime evidence permits a static explanation with explicit gaps.
Do not describe that result as real integration acceptance.
Never expose secrets, personal messages, or sensitive records in the document.
Use synthetic examples and redacted evidence.
