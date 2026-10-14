# Distribution register

All channels remain `planned` until public verification.
This table records intended routes, not directory approval or current policy acceptance.
No marketplace policy review or account submission occurred in this documentation task.

Canonical source: [how-it-works-skill](https://github.com/joevilcai666/how-it-works-skill).

Planned release/tag: `v0.1.0`. Public tag and release archive remain `pending`.
The archive's SHA-256 remains `pending` until release preparation creates the immutable asset.
Never substitute a source-file hash or a current branch hash for that archive checksum.

| Channel | Status | Source URL | Permissions | Release/tag | SHA-256 | Update route | Removal route | Last policy review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI public plugin directory | planned | [Package and directory guidance](https://developers.openai.com/plugins/build/plugins) | Package declares Read and Write. No added server or repository upload. Directory requirements pending review | v0.1.0, pending | pending release archive | Submit the same tagged package after policy review. Verify listing update behavior | Request directory removal through its verified maintainer process. Process pending review | pending, not reviewed |
| Anthropic official Claude plugin directory | planned | [Official directory source](https://github.com/anthropics/claude-plugins-official) | Shared local skills. No added server or hook. Directory access requirements pending review | v0.1.0, pending | pending release archive | Submit canonical GitHub source. Verify official directory update process | Request removal through official directory maintainers. Process pending review | pending, not reviewed |
| skills.sh discovery and npx skills install | planned | [skills.sh](https://skills.sh/) | Installer access and telemetry require review. Skill adds no upload or telemetry | v0.1.0, pending | pending release archive | Verify source discovery and displayed install command. Verify version selection and refresh | Verify client uninstall and index removal processes before approval | pending, not reviewed |
| AgentSkill.sh GitHub import | planned | [AgentSkill.sh](https://agentskill.sh/) | GitHub source import only after review. Optional webhook remains disabled | v0.1.0, pending | pending release archive | Import canonical GitHub source only after policy review. Verify revision identity | Verify listing removal and any account revocation process before approval | pending, not reviewed |
| SkillsMP policy review | planned | [SkillsMP](https://skillsmp.com/) | Requested access and data policy remain unknown. Do not grant expanded repository access | v0.1.0, pending | pending release archive | Review source, release identity, permissions, and update process before submission | Verify a credible removal route before submission | pending, not reviewed |

The source URLs identify the planned channel or its reference. They are not verified directory entry URLs.
Each public directory entry must point to the same canonical repository, release, and archive checksum.
Task 7 performs public install checks and records verified directory entry URLs and review dates.

## Admission criteria

A marketplace must expose the public GitHub source and release identity.
It must describe requested permissions and provide a credible update and removal process.
It must not require user repository uploads, exclusive ownership, or an incompatible license.
Its package identity must permit the release checksum to be verified.

Keep a failed candidate in this table with status `rejected` and its exact failed criterion.
No candidate is rejected yet because the current policy reviews remain `pending`.
Do not infer acceptance from an install command, a manifest, or an accessible homepage.

## Record a verified stage

Record the public URL, date, release, archive checksum, actual requested permissions, update procedure, and removal procedure.
Distinguish a submitted request from an accepted directory entry and a successful client installation.
Retain `planned` until the claimed public stage is visible and reproducible.
Never upload a user's repository to demonstrate the skill.

Last register review: 2026-10-14. Channel policy reviews: `pending`.
