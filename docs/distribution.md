# Distribution register

The public [GitHub repository](https://github.com/joevilcai666/how-it-works-skill) and
[v0.1.0 release](https://github.com/joevilcai666/how-it-works-skill/releases/tag/v0.1.0) are available.
Public GitHub installs passed in isolated Codex, Claude Code, and generic installer configurations.
No official directory submission or directory approval exists in this record.
An install result does not prove a directory entry or a successful document run.

## Immutable release identity

- Release/tag: `v0.1.0`.
- Release commit: `071d6ca2bf04f3af694de6343016e1e335c2bd76`.
- Annotated tag object: `11cf7132911bb76ed3e42995d81eda5f61192f29`.
- Archive command: `git archive --format=zip --output=how-it-works-skill-v0.1.0.zip v0.1.0`.
- Archive SHA-256: `7efa657e5d4b70789e246045523096bad78d92e0bf6510bf7344aa7a5a5555a3`.

Two local archive runs produced identical bytes. The archive contains 94 entries.
The extracted archive passed the privacy scanner.
No submission received the archive, so the release has no extra ZIP asset.
GitHub's automatic source ZIP uses a different archive format. Do not compare its hash with the local archive hash above.
The tag remains on the release commit. Later documentation commits on `main` do not move the tag.

## Channel status

Each row refers to the canonical release identity above.
A planned or rejected channel has no verified release entry or checksum at that channel.
The Status column uses exactly one value: `planned`, `submitted`, `published`, `listed`, `rejected`, or `removed`.
`listed` means that a public discovery page exists. It does not mean audited directory acceptance or verified release identity.

| Channel | Status | Source URL | Permissions | Release/tag | SHA-256 | Update route | Removal route | Last policy review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GitHub repository and release | published | [Repository](https://github.com/joevilcai666/how-it-works-skill), [release](https://github.com/joevilcai666/how-it-works-skill/releases/tag/v0.1.0) | Public synthetic package only. Read and Write capabilities describe local agent work. No added MCP server or hook | v0.1.0 | Canonical archive hash above | Publish a new tag for package changes. Keep v0.1.0 fixed | Maintainer controls repository and release availability. Client removal commands appear below | 2026-10-14 |
| OpenAI public plugin directory | planned | [Submission portal](https://platform.openai.com/plugins), [official flow](https://developers.openai.com/plugins/deploy/submission) | Portal requires an eligible organization role and verified developer identity. Neither account condition was verified. No ZIP upload or expanded access | Target v0.1.0. No directory entry | Unverified at channel | Official guide requires another ZIP for metadata or skill updates | Portal removal controls remain unverified because account access did not complete | 2026-10-14 |
| Anthropic official Claude plugin directory | planned | [Official directory](https://github.com/anthropics/claude-plugins-official), [developer portal](https://claude.ai/directory/manage) | Official flow requires a paid Claude plan and an eligible account or organization role. Anonymous portal access showed sign-in. No GitHub access grant | Target v0.1.0. No directory entry | Unverified at channel | Official guide describes tracked branch commits, scans, and version publication | Official guide describes withdrawal or delisting in the developer portal. No account-side removal action ran | 2026-10-14 |
| skills.sh discovery and npx skills install | listed | [Skill page](https://skills.sh/joevilcai666/how-it-works-skill/how-it-works), [CLI source](https://github.com/vercel-labs/skills) | Public source clone and project-local skill copy. First trial disabled telemetry. A second public install used normal anonymous install telemetry. Page visibility does not prove audit acceptance. No account connection | Install files matched v0.1.0. Discovery page visible on 2026-10-14 | Unverified at index | `npx skills update` refreshes client files. Official FAQ describes discovery from install telemetry | `npx skills remove how-it-works` removes client files. [Author requests](https://skills.sh/contact) use a PR for hide or redirect rules | 2026-10-14 |
| AgentSkill.sh GitHub import | planned | [Import page](https://agentskill.sh/submit), [privacy](https://agentskill.sh/privacy), [terms](https://agentskill.sh/terms) | Public GitHub import is documented. Account SSO includes profile and email data. No account connection or webhook | Target v0.1.0. No entry verified | Unverified at channel | Import page describes daily source sync and direct-URL resubmission | Privacy policy provides a contact route for account and associated data deletion. Listing-specific removal remains unverified | 2026-10-14 |
| SkillsMP | rejected | [FAQ](https://skillsmp.com/docs/faq), [terms](https://skillsmp.com/terms), [privacy](https://skillsmp.com/privacy) | Public GitHub index. No account connection, source upload, or extra permission | Target v0.1.0. No indexed version verified | Unverified at channel | FAQ describes daily GitHub sync. Manual `/submit` returned 404 | Privacy policy provides a data-deletion contact. No explicit listing-removal process verified | 2026-10-14 |

## Publication evidence and remaining boundaries

GitHub reports a public repository, default branch `main`, MIT license, Issues, and the nine planned topics.
Its private vulnerability reporting endpoint reports `enabled: true`.
The community profile reports 85 percent and detects the README, license, contribution file, and PR template.
The repository includes three issue forms. GitHub's profile endpoint did not classify an issue template.
There is no separate project homepage.

The 1280×640 social preview file exists in the public repository.
Its SHA-256 is `7d22dca47525e636d4344eed127fcc3414dadc4e1c2ab3009f41d39a7a7fc809`.
Upload to GitHub's social preview setting remains unverified.
The supported [GitHub settings procedure](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview) requires an authenticated Settings page.
The available UI reported a locked computer. Browser actions also failed or timed out.

Direct source checks on 2026-10-14 confirmed the [skill page](https://skills.sh/joevilcai666/how-it-works-skill/how-it-works)
and [repository page](https://skills.sh/joevilcai666/how-it-works-skill).
The skill page contains the main skill and points to the canonical GitHub repository.
The repository page lists `how-it-works`.
These observations prove public discovery only. No indexed tag, commit, or archive checksum is verified.
Page visibility does not prove completed security audits, marketplace approval, or user acceptance.
This record makes no verified install-count or ranking claim.
The earlier check returned 404. The current direct pages show asynchronous discovery after that check.
The cached reader still returned the earlier 404, so the current result uses direct source pages.

OpenAI's current official flow uses a ZIP upload at its submission portal.
The UI attempt failed before an authenticated portal or a submission form opened.
Developer identity, organization access, terms, automated package checks, and publication remain unverified.
The [desktop-only guide](https://developers.openai.com/plugins/deploy/desktop-only) requires `requires_local_executor: true` for skills that require desktop execution.
The tagged manifest does not declare that field. Directory eligibility remains unverified.
Resolve any required metadata in a separately reviewed version. Do not change the released tag.
Do not mark this channel submitted from the existence of a ZIP.

Anthropic's [current submission guide](https://clau.de/plugin-directory-submission) directs authors to the developer portal.
It says the earlier Console submission form is unsupported.
The guide requires a paid plan and places organization ownership on the first submitting organization.
Directory terms require the publisher's review before submission.
No account login, organization selection, terms acceptance, or submission occurred.

AgentSkill.sh documents GitHub import and an optional push webhook.
Its terms prohibit accounts created by bots and grant a display/distribution license for submitted content.
Human account and terms review remain necessary before import. No webhook exists for this task.
The current review did not verify immutable tag selection or listing-specific removal.

SkillsMP confirms public GitHub sources and repository licenses.
The review did not find release/checksum identity or an explicit listing-removal process.
These missing admission criteria prevent proactive submission.
Automatic third-party indexing can still occur without a submission. This record does not verify such indexing.

## Client update and removal

These commands apply to the configuration where the user installed the package:

| Client route | Update | Remove |
| --- | --- | --- |
| Codex repository marketplace | `codex plugin marketplace upgrade how-it-works-skill`. A tag-pinned source remains on that tag | `codex plugin remove how-it-works@how-it-works-skill`, then `codex plugin marketplace remove how-it-works-skill` |
| Claude repository marketplace | `claude plugin marketplace update how-it-works-skill`, then `claude plugin update how-it-works@how-it-works-skill` | `claude plugin uninstall how-it-works@how-it-works-skill`, then `claude plugin marketplace remove how-it-works-skill` |
| npx skills | `npx skills update` | `npx skills remove how-it-works` |
| Manual copy | Replace the complete skill directory from a reviewed release | Remove the installed skill directory |

The CLI help and vendor documents support these commands.
Isolated Codex and Claude plugin removal and marketplace removal exited 0.
The isolated npx main-skill removal exited 0 and left its installed directory absent.
This release verification did not execute an update against a newer release.
See [client commands and evidence limits](verification/v0.1.0.md).

Last register review: 2026-10-14.
