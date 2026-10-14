# Symptom-first diagnosis

Start with the observable symptom.
Identify the smallest boundary that can explain that symptom.
Treat a likely cause as a hypothesis until evidence supports it.
Use this table format in `HOW_IT_WORKS.md`:

| what the user sees | likely boundary | evidence to inspect | safest change | proof |
| --- | --- | --- | --- | --- |
| A saved task disappears after restart | Durable storage or restore path | Save result, store record, restart trace, and restore test | Correct the proven save or restore boundary | Create a task, restart, and observe the same task |
| A task appears twice | Event handling or identity checks | Duplicate event input, task identifiers, and stored effects | Correct duplicate handling at the proven boundary | Repeat the same event and observe one task |
| A result exists locally but never arrives | Permission or external delivery boundary | Permission state, send response, and real-channel receipt | Correct the failed permission or delivery step | Observe the real recipient's result in the authorized channel |
| A canceled request later changes the result | Cancellation or late-result boundary | State transitions, callback timing, and persisted effects | Correct the proven cancellation check | Cancel, deliver a late result, and observe no forbidden effect |

The examples are synthetic. Include rows only for relevant product behavior.
Replace each generic evidence item with the project's actual source or evidence link.

## Keep diagnosis separate from implementation

Describe what the user sees before technical details.
Distinguish confirmed causes from likely causes.
Name the evidence that can resolve each hypothesis.
Write the safest change as a recommendation unless the task includes an implemented fix.
A request to explain the product does not authorize the proposed fix.

Define proof as an observable result at the failed boundary.
A passing local test with a mock provider cannot prove a real recipient's delivery.
Check restart, duplicate events, late results, cancellation, and missing permission when those paths exist.
State “not applicable” or “unknown” when a path does not exist or lacks evidence.
Do not add agent loops, recovery mechanisms, or platform permissions that the product does not contain.
