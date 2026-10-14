# Evidence rules

Classify each important behavior claim with the evidence that supports it.
These levels describe separate evidence types. They are not automatic promotions.
Use the user's language for labels, but preserve the distinction between all four types.

| Evidence level | Required evidence | Permitted claim | Limit |
| --- | --- | --- | --- |
| code verified | Inspect the executable path, its callers, configuration, and relevant boundaries | The code implements this behavior under these conditions | Does not prove execution or delivery |
| test verified | Record a relevant test command, revision, environment, assertions, and result | This scenario passed in this test environment | Synthetic fixtures and mocks prove only their scoped scenario |
| runtime verified | Record an actual execution with its revision, environment, input class, and observable effects | This behavior occurred in this environment | Does not prove other environments, later revisions, or user acceptance |
| user accepted | Record explicit user acceptance with date, scenario, version, and scope | The user accepted this result within this scope | Does not prove unrelated flows or later changes |

## Record claims precisely

Use a compact table for important claims:

| Current behavior | Evidence level | Source and revision | Environment or scope | Missing proof |
| --- | --- | --- | --- | --- |
| Task save path exists | code verified | Source link at analyzed revision | Local code inspection | No executed save result |
| Restart restores a task | test verified | Test report and command at analyzed revision | Synthetic local store | No deployed restart evidence |

Record the analyzed commit and relevant uncommitted changes.
Use “revision unavailable” when no revision exists.
Use evidence dates when they help the reader judge freshness.
Do not copy secrets, personal messages, tokens, or sensitive records into evidence links or excerpts.

Separate these effects:

- Implementation from execution.
- Generated output from saved output.
- Saved output from external delivery.
- Delivery from user acceptance.
- Mock services from real integrations.
- Historical operation from the current revision.

Never claim that a passing build proves a real integration.
A build proves only the build result in its recorded environment.
A model's “done” statement, directory name, or installed dependency does not prove a visible effect.

## Missing-evidence language

State what is known, what is missing, and the smallest useful check.
Examples:

- “The code includes the send path. No real-channel delivery evidence is available.”
- “The local test passed with a mock provider. A real provider response remains unverified.”
- “The deployment file declares a worker. No evidence shows that this worker runs.”
- “Runtime evidence refers to an earlier revision. Current behavior remains code verified.”
- “No user acceptance record is available for this flow.”

Name the command, observation, or user decision that can resolve the gap.
Keep proposed checks separate from checks you actually executed.
Never label a proposal, assumption, mock result, or absent result as runtime verified.
