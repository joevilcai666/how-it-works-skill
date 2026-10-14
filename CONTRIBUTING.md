# Contribute to How It Works

Help a product owner understand current behavior, its evidence, and the next place to investigate.
Keep one shared workflow in `skills/how-it-works/SKILL.md`.
Use adapters for client package support. Do not maintain separate workflow copies for each client.

## Use synthetic examples

Use the fictional [Acorn Tasks fixture](demo/acorn-tasks/README.md), or create another small synthetic project.
Keep private repository names, local user paths, credentials, personal messages, and sensitive records out of files and Git history.
Use relative paths and public source links.
Do not use a private screenshot or an image with personal metadata.

The [evidence rules](skills/how-it-works/references/evidence.md) apply to documents and reports.
Separate code inspection, local tests, actual execution, and user acceptance.
Record a failed evaluation as a failed evaluation. Do not change recorded output to improve its score.

## Local checks

Use Python 3.9 or later and Git.
Run from the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s demo/acorn-tasks/tests -v
python3 scripts/check_repo.py
```

The demo needs a separate command because root discovery does not enter its hyphenated directory.
The checker includes known-pattern privacy checks over current files and reachable Git history.
It checks local links, code fences, Mermaid counts, manifest consistency, and whitespace.
It does not perform complete Mermaid syntax or visual checks.
Render changed diagrams with a Mermaid renderer when available. Record the renderer and result.

For a release, install the official Agent Skills reference validator into an ignored `.venv/`.
Make Claude Code available for strict plugin validation.
Run both skills through `skills-ref validate` and the package through `claude plugin validate --strict .`.
The checker invokes these validators when available. A `SKIP` result does not meet the release requirement.

No runtime package dependency is required for those development validators.
Use local checks on the exact release commit. A CI service status is not evidence that these commands passed.

## Propose a change

Describe the user problem and the expected visible result in an issue or pull request.
Add a regression case that fails before an updater or validator correction.
For skill instructions, use a synthetic agent evaluation and record visible output and evidence gaps.
Preserve unrelated project instructions in every updater change.

If the change affects the skill workflow or visible behavior, update root `HOW_IT_WORKS.md` and its relevant diagrams.
Keep the English and Chinese README claims consistent.
Do not alter a saved evidence record to turn an incomplete run into a success.

## Report compatibility

Use the compatibility issue form.
Include client name and version, operating system, Python version, package version or commit, install route, and a synthetic prompt.
Record each stage separately: installation, discovery, setup, saved document, validation, and user review.
Include commands and exit codes without private paths or credentials.

Label any omitted stage as unverified. A validator pass alone does not prove a usable client session.

## Preview asset

Edit `assets/social-preview.svg`. Keep the output at 1280 × 640 pixels.
Use local vector shapes and synthetic text only.

Export with a deterministic local SVG renderer, such as sharp or resvg.
The current export used sharp 0.35.5, libvips 8.18.7, and librsvg 2.63.2.

Remove PNG metadata and retain only `IHDR`, `IDAT`, and `IEND` chunks.
Run `python3 -m unittest tests.test_public_docs -v` to check dimensions, size, and chunk types.
The renderer is a development tool, not a dependency for users of the skill.

## Privacy and release status

Use [private vulnerability reporting](SECURITY.md) for security details.
Keep distribution rows `planned` until a public directory entry or installation proves the claimed stage.
Do not publish a guessed checksum, approval, or policy review date.
Contributions use the repository's [MIT license](LICENSE).
