---
name: how-it-works-setup
description: Install project-local HOW_IT_WORKS.md maintenance instructions. Use when someone asks to set up this skill, install its document maintenance rules, or prepare a project for its first HOW_IT_WORKS.md.
license: MIT
metadata:
  version: "0.1.1"
---

# How It Works Setup

1. Choose `en` or `zh-CN` from the user's language.
   Use `zh-CN` for Chinese and `en` for English.
   For other languages, use `en` for the instruction block.

2. Resolve the project root and the installed `how-it-works` skill directory.
   Run its [updater](../how-it-works/scripts/update_project_instructions.py):

   ```bash
   python3 "<how-it-works-directory>/scripts/update_project_instructions.py" --project-root "<project-root>" --language en
   ```

   Replace the path values and language before execution.
   On failure, report the exact error. Do not bypass the updater's checks.

3. Report the modified files from the updater's result.
   Distinguish created, updated, unchanged, and absent files.

4. When the user asks to create or refresh the document, invoke `$how-it-works`.
   Read the [main skill](../how-it-works/SKILL.md) before that work.
   The main skill owns all investigation, evidence, and output rules.
