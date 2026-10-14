# Acorn Tasks

Acorn Tasks is a fictional task inbox for documentation evaluations.
Every task, person, identifier, and runtime event in this fixture is synthetic.
The service has three actions: submit a task, mark it complete, and list tasks.
It has no agent, network connection, disk storage, or user acceptance record.

The [product requirements](docs/product.md), [code](src/acorn_tasks.py),
[tests](tests/test_acorn_tasks.py), and [runtime fixture](runtime/sample-run.json)
serve different evidence purposes. The JSON describes a fictional run.
It does not prove an actual execution.

Run the local tests from the package root:

```bash
python3 -m unittest discover -s demo/acorn-tasks/tests -v
```

To observe a new local execution, run this command from the package root:

```bash
python3 - <<'PY'
import json
import sys
sys.path.insert(0, 'demo/acorn-tasks/src')
from acorn_tasks import TaskInbox
inbox = TaskInbox()
inbox.submit('Fold a blue kite')
inbox.complete('task-001')
print(json.dumps(inbox.list_tasks(), sort_keys=True))
PY
```

A new execution proves only its local input and output.
It does not promote the fictional run to production evidence.
