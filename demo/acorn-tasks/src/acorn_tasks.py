"""A fictional, process-local task inbox with no external effects."""


class TaskInbox:
    def __init__(self):
        self._tasks = {}

    def submit(self, title):
        title = title.strip()
        if not title:
            raise ValueError("A task title is required")
        task_id = f"task-{len(self._tasks) + 1:03d}"
        self._tasks[task_id] = {"id": task_id, "title": title, "status": "pending"}
        return dict(self._tasks[task_id])

    def complete(self, task_id):
        task = self._tasks[task_id]
        task["status"] = "complete"
        return dict(task)

    def list_tasks(self):
        return [dict(task) for task in self._tasks.values()]
