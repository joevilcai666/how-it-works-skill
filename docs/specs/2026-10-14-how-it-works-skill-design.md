# How It Works Skill — Design Specification

Date: 2026-10-14

## Purpose

`how-it-works-skill` turns an unfamiliar codebase into a living product explanation for a non-technical product owner. The output explains current user behavior, system responsibilities, evidence, limits, and the safest place to change the product.

The public project must work across Codex, Claude Code, and clients that implement the Agent Skills specification. It must not depend on private project data, one vendor's hidden runtime, or a second copy of the core workflow.

## User problem

Product owners often receive code, architecture notes, tests, and implementation reports without a reliable answer to four questions:

1. What does the product do now?
2. How does one user request travel through the system?
3. Which claims are proven by code, tests, real operation, or user acceptance?
4. Where must the team look when observed behavior is wrong?

Generated architecture documents also become stale because the project does not treat them as part of feature completion.

## Product promise

The skill will create or refresh one project-root `HOW_IT_WORKS.md` that:

- uses the user's language;
- explains current behavior without a change history;
- includes two to four useful Mermaid diagrams;
- explains required technical concepts with short analogies;
- separates code, test, runtime, and user-acceptance evidence;
- identifies current limitations without guessing;
- gives symptom-first guidance for product diagnosis;
- installs a maintenance contract in project instructions.

The skill does not prove production behavior without production evidence. It does not upload repository content, create public examples from user data, or publish a repository without explicit authorization.

## Repository structure

```text
how-it-works-skill/
├── README.md
├── README.zh-CN.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── plugin.json
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── skills/
│   ├── how-it-works/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── references/
│   │   ├── assets/
│   │   └── scripts/
│   └── how-it-works-setup/
│       └── SKILL.md
├── demo/
├── evals/
├── docs/distribution.md
└── .github/
```

`skills/how-it-works/SKILL.md` is the only authoritative workflow. The setup skill is a small onboarding adapter. Plugin manifests and marketplace listings point to the shared skill instead of copying it.

## First-run instruction setup

The first invocation finds the project root and adds one marker-bounded maintenance block to the root `AGENTS.md`.

- If `AGENTS.md` does not exist, create it with the maintenance block.
- If it exists, preserve all unrelated content and add or update only the managed block.
- Repeated runs must not duplicate the block.
- If a project-level `CLAUDE.md` exists, add one marker-bounded `@AGENTS.md` import when it is absent.
- If no `CLAUDE.md` exists, do not create one.
- Never modify user-global instruction files unless the user explicitly asks.

Claude Code supports `AGENTS.md` through its built-in `agents-md` plugin. Its default behavior uses `AGENTS.md` as a fallback when no project-level Claude instruction file exists. The import rule above covers projects that already have `CLAUDE.md` without duplicating the maintenance text.

## Core workflow

### Bootstrap mode

1. Read project instructions and determine the project's source-of-truth order.
2. Inspect product specifications, architecture decisions, active work, code entry points, state storage, integrations, tests, deployment declarations, and available runtime evidence.
3. Trace one important user journey from input to visible result.
4. Map each important claim to one of four evidence classes:
   - code verified;
   - test verified;
   - runtime verified;
   - user accepted.
5. Mark missing evidence and absent capabilities explicitly.
6. Generate the product explanation and the smallest useful diagrams.
7. Validate the document and report what was created.

### Refresh mode

1. Compare the current code and evidence with the version recorded in `HOW_IT_WORKS.md`.
2. Identify affected user journeys, modules, concepts, diagrams, evidence claims, and limitations.
3. Update only the affected current-state content.
4. Remove statements that are no longer true. Do not add a change log.
5. Update the last-reviewed date and analyzed revision when available.

## Output structure

The skill adapts detail to the project. A full first-run document normally includes:

1. One-sentence product position.
2. Current verified status.
3. Overall system behavior and architecture diagram.
4. Core agent or service workflow.
5. One representative request sequence.
6. State or data flow when it clarifies product behavior.
7. Plain-language concept explanations.
8. Module responsibility table.
9. Important current decisions and trade-offs.
10. Symptom-first diagnosis table.
11. Known limitations and evidence gaps.
12. Source links and last-reviewed date.

The output keeps the user's language. A Chinese request produces Chinese. An English request produces English. The project keeps one authoritative `HOW_IT_WORKS.md` unless the user explicitly requests parallel translations.

## Evidence rules

Directory names, dependency declarations, passing builds, and model statements do not prove user-visible operation.

The skill must distinguish:

- implementation from execution;
- generated output from saved output;
- saved output from delivery;
- delivery from user acceptance;
- synthetic dependencies from real services;
- a historical runtime version from the current code revision.

When evidence is unavailable, the document states the missing evidence and the smallest useful verification. It never fills a gap with a likely architecture.

## Visual design

Mermaid diagrams are used when they reduce the product owner's reading effort. The skill prefers:

- a flowchart for module relationships;
- a workflow for the agent or service loop;
- a sequence diagram for one request;
- a state diagram for lifecycle or recovery.

The skill does not require all four diagrams. It uses two to four diagrams and removes diagrams that repeat the prose.

The public README includes:

- a ten-second problem statement;
- a before/after Mermaid diagram;
- a three-column outcome comparison;
- installation paths for Codex, Claude Code, and generic clients;
- a synthetic `Acorn Tasks` example;
- a 1280×640 social preview built only from synthetic text and graphics.

## Privacy and publication safety

The public repository starts with a new Git history. No private repository is forked or filtered into it.

Public files must not contain:

- personal names or local user paths;
- private project names, issue numbers, or URLs;
- private architecture or runtime evidence;
- chat messages, health data, financial data, access tokens, or signed URLs;
- screenshots or image metadata from a private project.

All examples and evaluations use synthetic repositories and synthetic runtime records. Before the first push, validation scans current files, Git history, hidden files, links, and image metadata. A suspected disclosure blocks publication until a human reviews it.

The skill itself performs local analysis. It does not upload project content or add telemetry.

## Validation strategy

Skill development uses a RED–GREEN–REFACTOR evaluation:

1. Run a realistic synthetic project request without the skill.
2. Record concrete omissions and unsupported claims.
3. Write the smallest instructions and resources that correct those failures.
4. Run the same request with the skill.
5. Add pressure cases for missing runtime evidence, conflicting documents, an existing `AGENTS.md`, an existing `CLAUDE.md`, and sensitive fixtures.

Required checks include:

- Agent Skills frontmatter and package validation;
- idempotent instruction-file updates;
- preservation of unrelated instruction content;
- Markdown links and code-fence balance;
- Mermaid source presence and render checks when a renderer is available;
- bilingual output behavior;
- privacy scans over files and Git history;
- observable evaluation criteria instead of exact generated wording.

## Failure behavior

- Missing runtime evidence produces a static understanding with an explicit evidence gap.
- Conflicting sources follow the project's declared authority order. Undeclared conflicts remain visible.
- Unknown module responsibility is reported as unknown instead of inferred from a folder name.
- Invalid Mermaid or broken local links prevent completion.
- Suspected secrets or personal data block public-example generation.
- Unclear instruction-file ownership limits edits to the skill's managed markers.

## Distribution

The repository supports three installation paths:

1. Codex through its skill installer or portable plugin marketplace.
2. Claude Code through a marketplace-compatible plugin manifest.
3. Generic Agent Skills clients by installing `skills/how-it-works/`.

The first release prepares listings for the OpenAI and Anthropic official directories. Submission to a directory happens only after the public repository passes its validation and the required account flow is available.

Third-party marketplace distribution is allowed when a marketplace:

- installs from or links to the public GitHub source;
- shows the requested permissions clearly;
- does not require uploading user repositories;
- does not impose exclusive ownership or incompatible licensing;
- permits the same version and checksum to be identified;
- has a credible removal and update process.

Every listing points to the same GitHub repository and release. Marketplace-specific copies of `SKILL.md` are not maintained.

`docs/distribution.md` is the public distribution register. It records each directory or marketplace, listing URL, submission status, published release, package checksum, requested permissions, update method, and removal method. A marketplace is added only after a current policy and privacy review; marketplace availability and terms are not treated as permanent facts.

## Natural discovery

The repository uses a problem-led name and description:

> Turn any codebase into a living, visual product explanation.

Initial GitHub topics include `agent-skills`, `agents-md`, `codebase-documentation`, `living-documentation`, `product-management`, `codex`, `claude-code`, `mermaid`, and `ai-agents`.

Discovery assets include:

- bilingual README files;
- a GitHub social preview;
- a semantic `v0.1.0` release;
- community health files and issue templates;
- a compatibility matrix;
- a synthetic before/after example;
- problem-led articles and launch drafts that solve a real question before linking to the project.

The project does not promise stars or forks. It measures GitHub views, clones, stars, forks, release use, successful-document reports, and compatibility contributions. No in-skill telemetry is added.

## Initial scope exclusions

The first release will not include:

- a standalone codebase scanner CLI;
- hosted analysis or repository uploads;
- automatic public publishing of generated documents;
- private marketplace integrations;
- automatic modification of user-global configuration;
- a requirement to run multiple agents in clients that do not support them.

## Primary references

- Agent Skills specification: https://agentskills.io/specification
- OpenAI portable plugins: https://developers.openai.com/plugins/build/plugins
- Claude Code plugin reference: https://code.claude.com/docs/en/plugins-reference
- Claude Code `AGENTS.md` support: https://code.claude.com/docs/en/memory#agentsmd
- GitHub README guidance: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes
- GitHub Topics: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics
- GitHub social previews: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview
