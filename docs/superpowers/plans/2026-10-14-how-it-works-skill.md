# How It Works Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a privacy-safe, bilingual, cross-client Agent Skill that creates and maintains a visual `HOW_IT_WORKS.md` for non-technical product owners.

**Architecture:** One standards-compliant `how-it-works` skill owns the analysis and writing workflow. A small setup skill and a deterministic Python script install a marker-bounded maintenance contract in project instructions without touching global configuration. Portable, Codex, and Claude manifests all point to the same skills, while synthetic fixtures, deterministic rubric checks, and privacy scans protect the public release.

**Tech Stack:** Agent Skills Markdown, portable Agent Plugin JSON, Claude plugin JSON, Python 3.9+ standard library, `unittest`, Mermaid, Git, GitHub CLI.

**Spec:** `docs/specs/2026-10-14-how-it-works-skill-design.md`

## Global Constraints

- Keep `skills/how-it-works/SKILL.md` as the only authoritative analysis workflow.
- Support Codex, Claude Code, and clients that implement the Agent Skills specification.
- Use one authoritative project-root `HOW_IT_WORKS.md` unless the user explicitly requests parallel translations.
- Preserve the user's language. Provide English and Simplified Chinese public documentation.
- On first invocation, create or update the root `AGENTS.md`. If a root `CLAUDE.md` already exists, add one `@AGENTS.md` import. Do not create `CLAUDE.md`.
- Never modify user-global instruction files.
- Keep instruction updates idempotent and preserve unrelated content.
- Describe current behavior only. Do not place a change history in generated `HOW_IT_WORKS.md` files.
- Use two to four useful Mermaid diagrams in a full first-run document.
- Separate code, test, runtime, and user-acceptance evidence.
- Treat missing evidence as a visible limitation, not permission to infer behavior.
- Perform repository analysis locally. Do not upload source code and do not add in-skill telemetry.
- Use only synthetic projects, records, names, screenshots, and diagrams in the public repository.
- Use MIT licensing and semantic version `0.1.0` for the first public release.
- Keep all marketplace listings on the same GitHub release and record their release checksum.
- Do not use GitHub Actions as the release gate. Run every release check locally on the exact release commit.

## File Map

| Path | Responsibility |
|---|---|
| `plugin.json` | Canonical portable Agent Plugin identity and OpenAI presentation metadata. |
| `.codex-plugin/plugin.json` | Codex compatibility overlay for older/current compatibility paths. |
| `.claude-plugin/plugin.json` | Claude Code plugin metadata. |
| `.claude-plugin/marketplace.json` | Self-hosted Claude marketplace entry. |
| `skills/how-it-works/SKILL.md` | Authoritative codebase investigation and `HOW_IT_WORKS.md` workflow. |
| `skills/how-it-works-setup/SKILL.md` | Thin onboarding workflow that installs project instructions and then hands off to the main skill. |
| `skills/how-it-works/scripts/update_project_instructions.py` | Safe, idempotent project-level `AGENTS.md` and `CLAUDE.md` updater. |
| `skills/how-it-works/assets/maintenance-block.en.md` | English managed maintenance contract. |
| `skills/how-it-works/assets/maintenance-block.zh-CN.md` | Simplified Chinese managed maintenance contract. |
| `skills/how-it-works/references/*.md` | Focused evidence, source-order, diagram, diagnosis, and output guidance loaded only when needed. |
| `skills/how-it-works/agents/openai.yaml` | Codex skill-list presentation metadata. |
| `demo/acorn-tasks/` | Fully synthetic codebase and expected product explanation. |
| `evals/cases.json` | Pressure cases and observable scoring rules. |
| `evals/run_rubric.py` | Deterministic evaluator for generated documents. |
| `scripts/privacy_scan.py` | Current-tree, Git-history, link, and image-metadata privacy checks. |
| `scripts/check_repo.py` | One local entry point for all deterministic release checks. |
| `tests/` | Standard-library unit and integration tests. |
| `README.md`, `README.zh-CN.md` | English and Chinese discovery, installation, and ten-second product explanation. |
| `HOW_IT_WORKS.md` | This public repository's own current product explanation. |
| `docs/distribution.md` | Public registry of marketplace status, version, checksum, permissions, update, and removal routes. |

## Review Focus

1. A project has CRLF files, Unicode text, or a malformed managed marker: preserve valid content and stop safely on ambiguous ownership. Task 2 tests these cases.
2. `AGENTS.md` or `CLAUDE.md` is a symlink, or `CLAUDE.md` already imports `AGENTS.md`: refuse symlink writes and never duplicate imports. Task 2 tests these cases.
3. Invocation starts inside a nested directory or outside a Git repository: find the nearest repository root, and otherwise require an explicit project root. Task 2 tests these cases.
4. The target is not an agent product, sources conflict, or runtime evidence is absent: generate a useful static explanation and label uncertainty without inventing an agent loop. Task 4 tests these cases.
5. Sensitive content exists only in deleted Git history or image metadata: fail the release before push. Task 5 tests these cases.

---

### Task 1: Create the portable package identity

**Files:**

- Create: `VERSION`
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `plugin.json`
- Create: `.codex-plugin/plugin.json`
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `skills/how-it-works/agents/openai.yaml`
- Create: `assets/icon.svg`
- Create: `assets/logo.svg`
- Create: `tests/test_manifests.py`

**Interfaces:**

- Consumes: the approved name `how-it-works`, repository URL `https://github.com/joevilcai666/how-it-works-skill`, and release version from `VERSION`.
- Produces: valid manifests that discover `skills/`, expose `./skills/how-it-works-setup/SKILL.md` as the OpenAI onboarding skill, and use the same name, version, repository, and license.

- [ ] **Step 1: Write manifest consistency tests**

Create `tests/test_manifests.py` with tests that load all JSON files and assert:

```python
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ManifestTests(unittest.TestCase):
    def load_json(self, relative_path: str) -> dict:
        return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))

    def test_portable_manifest_identity_and_onboarding(self):
        manifest = self.load_json("plugin.json")
        self.assertEqual(manifest["$schema"], "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertEqual(manifest["name"], "how-it-works")
        self.assertEqual(manifest["version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(
            manifest["extensions"]["com.openai"]["onboardingSkill"],
            "./skills/how-it-works-setup/SKILL.md",
        )

    def test_all_manifests_share_release_identity(self):
        version = (ROOT / "VERSION").read_text().strip()
        codex = self.load_json(".codex-plugin/plugin.json")
        claude = self.load_json(".claude-plugin/plugin.json")
        market = self.load_json(".claude-plugin/marketplace.json")
        self.assertEqual(codex["version"], version)
        self.assertEqual(claude["version"], version)
        self.assertEqual(market["name"], "how-it-works-skill")
        self.assertEqual(market["plugins"][0]["version"], version)
        self.assertEqual(market["plugins"][0]["source"], "./")

    def test_manifest_assets_exist(self):
        manifest = self.load_json("plugin.json")
        interface = manifest["extensions"]["com.openai"]["interface"]
        for key in ("composerIcon", "logo"):
            self.assertTrue((ROOT / interface[key]).is_file())
```

- [ ] **Step 2: Run the tests and confirm the package does not exist yet**

Run: `python3 -m unittest tests.test_manifests -v`

Expected: errors for missing `plugin.json` and `VERSION`.

- [ ] **Step 3: Add the version, MIT license, and manifests**

Use `0.1.0` in `VERSION`. Ignore `.venv/`, Python cache files, macOS metadata, and generated evaluation output outside `evals/runs/0.1.0/`. Build the portable manifest with the official schema, repository URL, `Productivity` category, `Read` and `Write` capabilities, two default prompts, `./assets/icon.svg`, `./assets/logo.svg`, and the onboarding skill path. Use `How It Works Contributors` as the public author name and omit personal email addresses.

The compatibility manifests must repeat only fields required by their clients. They must not duplicate skill content. The Codex overlay must include the same interface and onboarding path as the portable OpenAI extension because older compatibility readers do not merge the two manifests. Tests must compare those duplicated fields. The Claude marketplace must be named `how-it-works-skill` and expose one plugin named `how-it-works` from `./`.

- [ ] **Step 4: Add square synthetic SVG brand assets**

Create 256×256 SVG files with no embedded raster image, external URL, creator metadata, local path, or private text. Use the visual metaphor “code blocks become a readable map” and the shared brand color `#2563EB`.

- [ ] **Step 5: Run manifest and JSON checks**

Run:

```bash
python3 -m unittest tests.test_manifests -v
python3 -m json.tool plugin.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
```

Expected: all tests pass and every JSON command exits with status 0.

- [ ] **Step 6: Commit the package identity**

```bash
git add VERSION .gitignore LICENSE plugin.json .codex-plugin .claude-plugin assets skills/how-it-works/agents tests/test_manifests.py
git commit -m "feat: add cross-client plugin manifests"
```

---

### Task 2: Add safe first-run project instruction setup

**Files:**

- Create: `skills/how-it-works/assets/maintenance-block.en.md`
- Create: `skills/how-it-works/assets/maintenance-block.zh-CN.md`
- Create: `skills/how-it-works/scripts/update_project_instructions.py`
- Create: `tests/test_update_project_instructions.py`

**Interfaces:**

- Consumes: `--project-root PATH`, `--language en|zh-CN`, and optional `--dry-run`.
- Produces: JSON `{"project_root": str, "agents": "created|updated|unchanged", "claude": "updated|unchanged|absent"}` on stdout; exit 0 for success and exit 2 for unsafe or ambiguous files.
- Produces internal functions `find_project_root(start: Path) -> Path`, `update_managed_block(text: str, block: str) -> tuple[str, bool]`, and `apply_setup(project_root: Path, language: str, dry_run: bool = False) -> SetupReport`.

- [ ] **Step 1: Write CLI integration tests**

Use `tempfile.TemporaryDirectory`, `subprocess.run`, and temporary `.git` directories. Cover these assertions:

```python
SCRIPT = ROOT / "skills/how-it-works/scripts/update_project_instructions.py"

def run_setup(project_root: Path, language: str, *, check: bool = False):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--project-root", str(project_root), "--language", language],
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(result.stderr)
    return result

def test_creates_agents_but_not_claude_in_fresh_project(self):
    result = run_setup(self.root, "en")
    self.assertEqual(result.returncode, 0)
    self.assertTrue((self.root / "AGENTS.md").exists())
    self.assertFalse((self.root / "CLAUDE.md").exists())

def test_second_run_is_idempotent(self):
    run_setup(self.root, "zh-CN", check=True)
    before = (self.root / "AGENTS.md").read_bytes()
    report = json.loads(run_setup(self.root, "zh-CN", check=True).stdout)
    self.assertEqual((self.root / "AGENTS.md").read_bytes(), before)
    self.assertEqual(report["agents"], "unchanged")

def test_existing_claude_gets_one_import_and_keeps_content(self):
    (self.root / "CLAUDE.md").write_text("# Project rules\n\nKeep this.\n", encoding="utf-8")
    run_setup(self.root, "en", check=True)
    text = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
    self.assertEqual(text.count("@AGENTS.md"), 1)
    self.assertIn("Keep this.", text)
```

Also test existing imports, CRLF preservation, Chinese text, nested working directories, explicit non-Git roots, malformed or duplicated markers, symlinks, and `--dry-run`.

- [ ] **Step 2: Run the updater tests and confirm failure**

Run: `python3 -m unittest tests.test_update_project_instructions -v`

Expected: import or file-not-found errors because the updater does not exist.

- [ ] **Step 3: Add the two managed maintenance blocks**

Each block must state that `HOW_IT_WORKS.md` is a living product document and must be refreshed after changes to core flows, agent behavior, architecture, module responsibility, or user-visible behavior. It must require current-state prose, updated Mermaid, plain-language analogies, evidence-level accuracy, the last-reviewed date, and a 2–3 sentence product-owner summary.

Wrap the inserted text with exactly:

```text
<!-- how-it-works:start -->
...
<!-- how-it-works:end -->
```

- [ ] **Step 4: Implement the updater with atomic writes**

Use `Path.resolve()`, refuse symlink targets, detect newline style from the original bytes, and write to a sibling temporary file before `Path.replace()`. The repository-root search must walk parents for `.git`; when none exists, the CLI must require `--project-root` instead of guessing.

Use this result contract:

```python
@dataclass(frozen=True)
class SetupReport:
    project_root: str
    agents: Literal["created", "updated", "unchanged"]
    claude: Literal["updated", "unchanged", "absent"]
```

For an existing `CLAUDE.md`, add this block only when no active `@AGENTS.md` line exists:

```text
<!-- how-it-works:claude-import:start -->
@AGENTS.md
<!-- how-it-works:claude-import:end -->
```

If either marker appears without its matching partner, return exit 2 and leave both files unchanged.

- [ ] **Step 5: Run updater tests and inspect byte-level preservation**

Run:

```bash
python3 -m unittest tests.test_update_project_instructions -v
python3 skills/how-it-works/scripts/update_project_instructions.py --help
```

Expected: all tests pass; help lists `--project-root`, `--language`, and `--dry-run`.

- [ ] **Step 6: Commit the first-run setup**

```bash
git add skills/how-it-works/assets skills/how-it-works/scripts tests/test_update_project_instructions.py
git commit -m "feat: install living-document maintenance rules"
```

---

### Task 3: Write the authoritative skill and focused references

**Files:**

- Create: `skills/how-it-works/SKILL.md`
- Create: `skills/how-it-works-setup/SKILL.md`
- Create: `skills/how-it-works/references/source-order.md`
- Create: `skills/how-it-works/references/evidence.md`
- Create: `skills/how-it-works/references/output-contract.md`
- Create: `skills/how-it-works/references/diagrams.md`
- Create: `skills/how-it-works/references/diagnosis.md`
- Create: `tests/test_skill_contract.py`

**Interfaces:**

- Consumes: a user request to explain, create, or refresh a project's `HOW_IT_WORKS.md` and the local repository evidence available to the agent.
- Produces: one project-root `HOW_IT_WORKS.md`, an instruction setup report, validation results, and a 2–3 sentence product-owner summary.
- The setup skill consumes the same language choice, runs the updater, and explicitly invokes the main workflow; it owns no duplicate analysis rules.

- [ ] **Step 1: Write static contract tests**

Assert both skill directories match their frontmatter names, descriptions say what and when, the main file stays below 500 lines, every referenced local file exists, and the body contains these required concepts:

```python
REQUIRED_MAIN_TERMS = (
    "HOW_IT_WORKS.md",
    "current behavior",
    "code verified",
    "test verified",
    "runtime verified",
    "user accepted",
    "Mermaid",
    "two to four",
)
```

Also assert the setup skill references `update_project_instructions.py` and `how-it-works`, but does not copy the evidence taxonomy or output outline.

- [ ] **Step 2: Run the skill contract tests and confirm failure**

Run: `python3 -m unittest tests.test_skill_contract -v`

Expected: missing `SKILL.md` failures.

- [ ] **Step 3: Write `SKILL.md` as the orchestration layer**

Use Agent Skills frontmatter:

```yaml
---
name: how-it-works
description: Create or refresh a visual, evidence-aware HOW_IT_WORKS.md for a non-technical product owner. Use when someone asks how a codebase, product flow, agent loop, data flow, module, or user request works, or when product-visible behavior changed and the living explanation must be updated.
license: MIT
metadata:
  version: "0.1.0"
---
```

The body must require this order:

1. Run project instruction setup in the user's language.
2. Read project instructions before investigation.
3. Establish source authority and mark conflicts.
4. Inspect product intent, entry points, state, external effects, tests, deployment declarations, and available runtime evidence.
5. Trace one representative user request end to end.
6. Classify every important claim by evidence level.
7. Write or refresh only current-state content.
8. Validate links, diagrams, required sections, evidence wording, and last-reviewed date.
9. Tell the product owner what changed in 2–3 sentences.

The body must route detailed work directly to the five references, with no reference-to-reference chains.

- [ ] **Step 4: Write focused reference documents**

Define:

- source authority and conflict handling in `source-order.md`;
- the four evidence levels plus missing-evidence wording in `evidence.md`;
- required and optional document sections in `output-contract.md`;
- the choice rules and syntax patterns for flowchart, sequence, state, and data-flow Mermaid in `diagrams.md`;
- a symptom-first table format with “what the user sees / likely boundary / evidence to inspect / safest change / proof” in `diagnosis.md`.

Explicitly tell the agent not to draw an agent loop for a non-agent product and not to claim that a passing build proves a real integration.

- [ ] **Step 5: Write the thin setup skill**

Its entire workflow must be: choose `en` or `zh-CN` from the user's language, run the updater against the project root, report modified files, then invoke `$how-it-works` when the user asked to create or refresh the document.

- [ ] **Step 6: Validate both skills**

Run:

```bash
python3 -m unittest tests.test_skill_contract -v
python3 -m venv .venv
git clone --depth 1 https://github.com/agentskills/agentskills.git .venv/agentskills-source
.venv/bin/python -m pip install -e .venv/agentskills-source/skills-ref
.venv/bin/skills-ref validate skills/how-it-works
.venv/bin/skills-ref validate skills/how-it-works-setup
```

Expected: the official validator accepts both skills and all tests pass.

- [ ] **Step 7: Commit the skill workflow**

```bash
git add skills/how-it-works skills/how-it-works-setup tests/test_skill_contract.py
git commit -m "feat: add evidence-aware how-it-works workflow"
```

---

### Task 4: Build the synthetic demo and pressure evaluations

**Files:**

- Create: `demo/acorn-tasks/README.md`
- Create: `demo/acorn-tasks/docs/product.md`
- Create: `demo/acorn-tasks/src/acorn_tasks.py`
- Create: `demo/acorn-tasks/tests/test_acorn_tasks.py`
- Create: `demo/acorn-tasks/runtime/sample-run.json`
- Create: `demo/expected/HOW_IT_WORKS.md`
- Create: `evals/cases.json`
- Create: `evals/baseline/no-skill.md`
- Create: `evals/run_rubric.py`
- Create: `evals/README.md`
- Create: `tests/test_rubric.py`

**Interfaces:**

- Consumes: an evaluation case ID and a generated Markdown path.
- Produces: JSON `{"case": str, "passed": bool, "checks": [{"name": str, "passed": bool, "detail": str}]}` and exit 0 only when every required check passes.

- [ ] **Step 1: Write rubric tests**

Test that the intentionally weak baseline fails for missing evidence distinctions and diagrams, while `demo/expected/HOW_IT_WORKS.md` passes. Test a Chinese sample for Chinese headings and a static product sample that must not mention an agent loop.

- [ ] **Step 2: Run rubric tests and confirm failure**

Run: `python3 -m unittest tests.test_rubric -v`

Expected: file-not-found or import errors.

- [ ] **Step 3: Create the Acorn Tasks synthetic repository**

Model a small task inbox with three observable actions: submit a task, mark it complete, and list current tasks. Keep product requirements, code, unit tests, and one synthetic runtime record separate so the expected document can demonstrate all four evidence levels without using private material.

The runtime JSON must use fictional IDs, dates, names, and content. It must not contain an email address, access token, home-directory path, or external signed URL.

- [ ] **Step 4: Create the expected product-owner document**

Write `demo/expected/HOW_IT_WORKS.md` in plain English with three Mermaid diagrams: system relationship, one request sequence, and task state flow. Include evidence labels, a symptom-first diagnosis table, current limitations, source links, analyzed revision label `synthetic-v1`, and last-reviewed date `2026-10-14`.

- [ ] **Step 5: Define pressure cases and deterministic scoring**

Add these case IDs to `evals/cases.json`:

- `bootstrap-agent-product`: requires three diagrams and all four evidence classes.
- `static-no-runtime`: requires an explicit runtime gap and forbids runtime-success claims.
- `conflicting-sources`: requires the conflict and selected authority to be named.
- `non-agent-product`: forbids invented agent-loop and memory sections.
- `refresh-current-state`: forbids changelog language and stale limitations.
- `bilingual-zh-cn`: requires Chinese prose while allowing unchanged technical identifiers.

Implement heading, phrase, forbidden-phrase, Mermaid-count, local-link, and evidence-label checks. Keep wording checks broad enough to allow natural writing.

- [ ] **Step 6: Run RED/GREEN evidence**

Run:

```bash
python3 evals/run_rubric.py --case bootstrap-agent-product --document evals/baseline/no-skill.md
python3 evals/run_rubric.py --case bootstrap-agent-product --document demo/expected/HOW_IT_WORKS.md
python3 -m unittest tests.test_rubric -v
```

Expected: the first command exits 1; the second and third exit 0.

- [ ] **Step 7: Run fresh-agent pressure tests**

Use a fresh agent with the main skill disabled for the baseline and another fresh agent with the skill enabled for the same synthetic request. Save only synthetic generated outputs under `evals/runs/0.1.0/`. Run the rubric on both and record the command, client, model family, date, and pass/fail result in `evals/README.md`. Do not record hidden reasoning.

- [ ] **Step 8: Commit the demo and evaluations**

```bash
git add demo evals tests/test_rubric.py
git commit -m "test: add synthetic cross-client skill evaluations"
```

---

### Task 5: Add repository and privacy release checks

**Files:**

- Create: `scripts/privacy_scan.py`
- Create: `scripts/check_repo.py`
- Create: `tests/test_privacy_scan.py`
- Create: `tests/test_check_repo.py`

**Interfaces:**

- `privacy_scan.py --root PATH [--history]` prints JSON findings and exits 1 when it finds a blocked path, credential pattern, private key header, signed URL, email outside the explicit public allowlist, SVG metadata, or PNG metadata chunk.
- `check_repo.py` runs unit tests, manifest consistency, skill structure, local Markdown links, Mermaid fence counts, privacy scanning, and Git diff checks; it exits nonzero on any failure.

- [ ] **Step 1: Write privacy and orchestration tests**

Create temporary repositories that contain:

- a clean synthetic Markdown file;
- an absolute home-directory path assembled from path segments in the test so the public repository does not contain the blocked literal itself;
- an API-key-shaped token;
- a secret committed and then deleted from the working tree;
- an SVG `<metadata>` element;
- a PNG containing a `tEXt` chunk.

Assert the clean repository passes and each unsafe repository fails with a finding that names the file or history object without printing the full secret.

- [ ] **Step 2: Run checks and confirm failure**

Run: `python3 -m unittest tests.test_privacy_scan tests.test_check_repo -v`

Expected: missing-script failures.

- [ ] **Step 3: Implement redacted privacy scanning**

Scan non-ignored tracked and untracked files, then scan `git log --all -p --no-ext-diff` when `--history` is present. Report rule ID, path or commit, and line number; replace matched values with `[REDACTED]`.

Parse PNG chunks with `struct` and reject `tEXt`, `zTXt`, `iTXt`, and `eXIf`. Parse SVG as text and reject `<metadata>`, embedded base64 images, absolute local paths, and external image URLs.

- [ ] **Step 4: Implement the single local check entry point**

`check_repo.py` must invoke subprocesses with argument arrays, never shell interpolation. It must run:

1. `python3 -m unittest discover -s tests -v`;
2. JSON and YAML-frontmatter structural checks;
3. local Markdown link resolution;
4. Mermaid fence balance and expected count checks for README/demo/HOW_IT_WORKS files;
5. `privacy_scan.py --root . --history`;
6. `git diff --check`.

If `.venv/bin/skills-ref` or `claude` is installed, also run `.venv/bin/skills-ref validate skills/how-it-works`, `.venv/bin/skills-ref validate skills/how-it-works-setup`, and `claude plugin validate --strict .`. Print a clear skipped check when an optional validator is unavailable; release verification in Task 7 must run both official validators before publication.

- [ ] **Step 5: Run the deterministic release checks**

Run:

```bash
python3 -m unittest tests.test_privacy_scan tests.test_check_repo -v
python3 scripts/check_repo.py
```

Expected: all required checks pass, and optional validator status is explicit.

- [ ] **Step 6: Commit validation tooling**

```bash
git add scripts tests/test_privacy_scan.py tests/test_check_repo.py
git commit -m "test: add privacy and release validation"
```

---

### Task 6: Create public documentation and discovery assets

**Files:**

- Create: `README.md`
- Create: `README.zh-CN.md`
- Create: `HOW_IT_WORKS.md`
- Create: `SECURITY.md`
- Create: `CONTRIBUTING.md`
- Create: `CHANGELOG.md`
- Create: `docs/distribution.md`
- Create: `docs/releases/v0.1.0.md`
- Create: `assets/social-preview.svg`
- Create: `assets/social-preview.png`
- Create: `.github/ISSUE_TEMPLATE/bug.yml`
- Create: `.github/ISSUE_TEMPLATE/compatibility.yml`
- Create: `.github/ISSUE_TEMPLATE/feature.yml`
- Create: `.github/pull_request_template.md`
- Create: `tests/test_public_docs.py`

**Interfaces:**

- Consumes: the actual install commands and verified behavior from Tasks 1–5.
- Produces: a stranger-readable bilingual landing page, a repository self-explanation, a synthetic social preview, contribution paths, and a public marketplace status ledger.

- [ ] **Step 1: Write public-document contract tests**

Assert both README files contain:

- the user problem above the first long section;
- a before/after Mermaid diagram;
- Codex, Claude Code, and generic installation paths;
- a five-minute first-use prompt;
- a link to the synthetic demo;
- a privacy statement;
- a compatibility matrix;
- reciprocal language links.

Assert `HOW_IT_WORKS.md` contains two to four Mermaid diagrams, evidence levels, limitations, module responsibilities, and a last-reviewed date. Assert the social preview is exactly 1280×640 and smaller than 1 MiB.

- [ ] **Step 2: Run public-document tests and confirm failure**

Run: `python3 -m unittest tests.test_public_docs -v`

Expected: missing-file failures.

- [ ] **Step 3: Write the English and Chinese README files**

Use this first-screen sequence in both languages:

1. “Your codebase works. Your product explanation goes stale.”
2. “This skill turns the current repository into a living, visual product explanation.”
3. A before/after Mermaid flow.
4. Three outcomes: understand current behavior, separate proof from assumption, know where to investigate.
5. A five-minute install and first-run example.

Document these exact public install routes:

```bash
npx skills add joevilcai666/how-it-works-skill --skill how-it-works
```

```text
/plugin marketplace add joevilcai666/how-it-works-skill
/plugin install how-it-works@how-it-works-skill
```

Also document the Codex portable-plugin directory route and a manual copy route for generic Agent Skills clients. Disclose that third-party installers may have their own telemetry; the skill itself adds none, and manual installation remains available.

- [ ] **Step 4: Write this repository's own `HOW_IT_WORKS.md`**

Explain the install path, first-run updater, investigation workflow, evidence model, output, validation, and distribution. Use product language and three diagrams. Mark marketplace submission as not yet runtime-verified until Task 7 completes; do not present files or local tests as published-directory acceptance.

- [ ] **Step 5: Create community and release documents**

Use `SECURITY.md` for private vulnerability reporting without publishing a personal email. Use GitHub private vulnerability reporting as the primary path. In `CONTRIBUTING.md`, explain synthetic fixtures, no private examples, local checks, and compatibility-report expectations. Put only `0.1.0` current-release content in `CHANGELOG.md`.

- [ ] **Step 6: Create the distribution registry**

Add rows for:

- OpenAI public plugin directory;
- Anthropic official Claude plugin directory;
- `skills.sh` discovery and `npx skills` install;
- AgentSkill.sh GitHub import;
- SkillsMP policy review.

Each row must include status, source URL, permissions, release/tag, SHA-256 checksum, update route, removal route, and last policy review date. Use `planned` until the listing can be verified publicly. Mark a rejected platform with the specific criterion it failed instead of silently omitting it.

- [ ] **Step 7: Create the synthetic social preview**

Build a 1280×640 visual from simple vector shapes and synthetic text only: a dense code panel on the left, an arrow in the center, and a clear product map on the right. Keep all editable source in `assets/social-preview.svg`, export `assets/social-preview.png`, strip metadata, and verify dimensions and size in the test.

- [ ] **Step 8: Run docs, privacy, and full checks**

Run:

```bash
python3 -m unittest tests.test_public_docs -v
python3 scripts/check_repo.py
```

Expected: all required checks pass with no privacy findings.

- [ ] **Step 9: Commit the public-facing package**

```bash
git add README.md README.zh-CN.md HOW_IT_WORKS.md SECURITY.md CONTRIBUTING.md CHANGELOG.md docs assets/social-preview.svg assets/social-preview.png .github tests/test_public_docs.py
git commit -m "docs: add bilingual launch and contribution materials"
```

---

### Task 7: Verify clients, publish GitHub, and distribute one release

**Files:**

- Modify: `docs/distribution.md`
- Modify: `HOW_IT_WORKS.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Create: `docs/verification/v0.1.0.md`

**Interfaces:**

- Consumes: the exact release commit, local client installations, public GitHub repository, and marketplace account flows.
- Produces: public repository `joevilcai666/how-it-works-skill`, Git tag and release `v0.1.0`, verified install records, updated listing statuses, and immutable release checksums.

- [ ] **Step 1: Run the complete local release gate on a clean tree**

Run:

```bash
git status --short
python3 scripts/check_repo.py
.venv/bin/skills-ref validate skills/how-it-works
.venv/bin/skills-ref validate skills/how-it-works-setup
claude plugin validate --strict .
```

Expected: clean status before checks; all validators pass. If an official validator is unavailable, install it from its official source or record the exact environment limitation and do not publish until equivalent official validation runs.

- [ ] **Step 2: Install and test from local paths in each available client**

Verify:

- Codex loads both skills and runs onboarding against a temporary synthetic project.
- Claude Code validates the plugin, loads the main skill, reads the managed `AGENTS.md`, and respects the existing-`CLAUDE.md` import case.
- `npx skills add . --skill how-it-works` installs the generic skill into a temporary project.

For each client, run the same Acorn Tasks prompt and score the output with `evals/run_rubric.py`. Record client version, command, release commit, environment, output path, and result in `docs/verification/v0.1.0.md`.

- [ ] **Step 3: Commit the exact locally verified state**

Update `HOW_IT_WORKS.md` with the local client results and current evidence limits. Then run:

```bash
python3 scripts/check_repo.py
git add docs/verification/v0.1.0.md HOW_IT_WORKS.md
git commit -m "test: record v0.1.0 client verification"
```

Expected: the commit contains only synthetic verification evidence and the living-document refresh.

- [ ] **Step 4: Re-run privacy checks over the full history**

Run:

```bash
python3 scripts/privacy_scan.py --root . --history
git log --all --stat --oneline
git status --short
```

Expected: zero findings, only this synthetic repository's commits, and a clean worktree.

- [ ] **Step 5: Create and push the public GitHub repository**

Run:

```bash
gh repo create joevilcai666/how-it-works-skill --public --source=. --remote=origin --push --description "Turn any codebase into a living, visual product explanation."
gh repo edit joevilcai666/how-it-works-skill --enable-issues --add-topic agent-skills --add-topic agents-md --add-topic codebase-documentation --add-topic living-documentation --add-topic product-management --add-topic codex --add-topic claude-code --add-topic mermaid --add-topic ai-agents
```

Expected: GitHub reports the public repository URL and `git ls-remote origin main` resolves the release commit.

- [ ] **Step 6: Add the social preview and repository settings**

Upload `assets/social-preview.png` as the GitHub social preview. Enable private vulnerability reporting. Verify the About description, topics, license, README language links, Issues, and community profile on the public repository.

- [ ] **Step 7: Tag and publish the immutable release**

Run:

```bash
git tag -a v0.1.0 -m "How It Works Skill v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --title "How It Works Skill v0.1.0" --notes-file docs/releases/v0.1.0.md
release_workspace=$(mktemp -d)
release_zip_path="$release_workspace/how-it-works-skill-v0.1.0.zip"
git archive --format=zip --output="$release_zip_path" v0.1.0
shasum -a 256 "$release_zip_path"
```

Record the checksum in `docs/distribution.md` before the final documentation commit; add a second release asset only if a marketplace requires the ZIP.

- [ ] **Step 8: Submit to official directories**

Submit the same tagged package to the OpenAI public plugin directory and the repository to Anthropic's official Claude plugin directory. Do not accept expanded repository access, add an MCP server, or upload user repositories. If identity verification or marketplace terms require a human confirmation, stop at that exact screen and request only that action.

Record submission URL, submission date, status, requested permissions, and removal route in `docs/distribution.md`. “Submitted” is not “published”; verify the public listing before changing status to `published`.

- [ ] **Step 9: Add vetted third-party discovery channels**

Perform a current policy check, then:

- verify the GitHub skill appears on `skills.sh` and test the displayed `npx skills add` command;
- submit the GitHub repository to AgentSkill.sh and decline the optional webhook unless its payload and removal behavior pass review;
- submit to SkillsMP only if it exposes the GitHub source, release identity, permissions, update process, and removal process.

Do not upload a divergent `SKILL.md`. Record every accepted or rejected channel and reason in `docs/distribution.md`.

- [ ] **Step 10: Update living documentation with verified publication facts**

Update `HOW_IT_WORKS.md` and both README files so they distinguish local client verification, public GitHub availability, submitted listings, and published listings. Update the last-reviewed date and the 2–3 sentence product-owner summary.

- [ ] **Step 11: Run the final gate and publish the documentation update**

Run:

```bash
python3 scripts/check_repo.py
git diff --check
git status --short
```

Then commit and push only the verified documentation changes:

```bash
git add docs/distribution.md docs/verification/v0.1.0.md HOW_IT_WORKS.md README.md README.zh-CN.md
git commit -m "docs: record v0.1.0 verification and distribution"
git push origin main
```

Expected: all checks pass, the public repository shows the final commit, and listing statuses match what a user can actually access.

## Final Acceptance

- A new user can install one shared skill from GitHub in Codex, Claude Code, or a generic Agent Skills client.
- First invocation safely creates or updates root `AGENTS.md`; an existing root `CLAUDE.md` receives one `@AGENTS.md` import.
- A synthetic unfamiliar project produces a concise product-owner document with two to four valid Mermaid diagrams and explicit evidence levels.
- Re-running the skill updates current state without duplicating instructions or creating a change history.
- English and Chinese user requests keep their language.
- Local tests, official validators, client trials, privacy scans, and Git-history scans pass on the published commit.
- Public examples contain only synthetic content.
- GitHub and marketplace pages all identify the same repository, version, and checksum.
- `docs/distribution.md` distinguishes planned, submitted, published, rejected, and removed channels.
