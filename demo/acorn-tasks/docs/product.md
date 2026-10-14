# Acorn Tasks product requirements

Revision: `synthetic-v1`.

Acorn Tasks lets a fictional user keep a small task list in one process.
The service accepts a nonempty title and returns a pending task with a local identifier.
It removes spaces at the start and end of the title.
The service marks a known task complete and returns the current task.
The service lists tasks in submission order, including complete tasks.

An empty title produces an error and no task.
An unknown task identifier produces an error and no state change.
Repeated completion keeps one complete task.
Repeated submission creates separate tasks, even with the same title.
The caller cannot change stored tasks through returned data.

All tasks exist in process memory. A new process starts with no tasks.
The product has no agent workflow, long-term memory, cancellation, authentication,
permission prompt, delivery channel, or retry scheduler.
These requirements do not promise production readiness or user acceptance.
