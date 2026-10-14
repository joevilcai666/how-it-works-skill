# Security

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/joevilcai666/how-it-works-skill/security/advisories/new).
This is the primary report route after public repository setup enables it.
The route and response process remain unverified during release preparation.

If GitHub does not offer a private report, do not post the exploit or sensitive files in a public issue.
Open a public issue that asks the maintainers to enable private reporting, without vulnerability details.

Include the affected version, client version, expected boundary, and a minimal synthetic reproduction.
Describe the impact and which files or operations it affects.
Use placeholders for secrets and private content.
Do not attach a private repository, personal messages, or unredacted logs.

## Scope and support

Version `0.1.0` is the current local release candidate.
No earlier release has a support promise.
Report unsafe instruction edits, privacy scan bypasses, unintended external resource access, and permission violations.

The skill itself adds no telemetry, repository upload service, or remote execution endpoint.
The AI client enforces tool permissions and supplies its own data policy.
The privacy scanner detects known patterns. It does not prove that every sensitive fact is absent.

Maintainers will review a private report, reproduce it with synthetic inputs, and prepare a scoped correction.
No response-time guarantee exists for this volunteer project.
