# omniplan-ai-skill

Single-entry OmniPlan automation skill using a local Python CLI.

## Requirements

- macOS
- OmniPlan 4 (running with at least one open document)
- Python 3.11+
- Automation permission for your terminal app

## Run

No installation is required.

```bash
git clone git@github.com:xiahan4956/omniplan-ai-skill.git
cd omniplan-ai-skill
python3 scripts/omniplan_skill.py --help
```

## Commands

List documents:

```bash
python3 scripts/omniplan_skill.py documents list
```

Query tasks:

```bash
python3 scripts/omniplan_skill.py tasks query --keyword release --completed false --detail full
```

Get task by id:

```bash
python3 scripts/omniplan_skill.py tasks get <task_id>
```

Create task:

```bash
python3 scripts/omniplan_skill.py tasks create "Beta Launch" --task-type milestone --note "target this month"
```

Update task:

```bash
python3 scripts/omniplan_skill.py tasks update <task_id> --title "Updated title" --completed true
```

Delete task:

```bash
python3 scripts/omniplan_skill.py tasks delete <task_id>
```

## Notes

- This project no longer depends on `FastMCP` server registration.
- The recommended entrypoint is `scripts/omniplan_skill.py`, which avoids package installation.
- Core logic remains in `documents.py`, `tasks.py`, and `jxa.py`.
