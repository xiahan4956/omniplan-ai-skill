# omniplan-ai-skill

Single-entry OmniPlan automation skill using a Python CLI.

## Requirements

- macOS
- OmniPlan 4 (running with at least one open document)
- Python 3.11+
- Automation permission for your terminal app

## Install

```bash
git clone git@github.com:xiahan4956/omniplan-ai-skill.git
cd omniplan-ai-skill
pip install -e .
```

## CLI Entry

```bash
python -m omniplan_mcp --help
```

or

```bash
omniplan-skill --help
```

## Commands

List documents:

```bash
omniplan-skill documents list
```

Query tasks:

```bash
omniplan-skill tasks query --keyword release --completed false --detail full
```

Get task by id:

```bash
omniplan-skill tasks get <task_id>
```

Create task:

```bash
omniplan-skill tasks create "Beta Launch" --task-type milestone --note "target this month"
```

Update task:

```bash
omniplan-skill tasks update <task_id> --title "Updated title" --completed true
```

Delete task:

```bash
omniplan-skill tasks delete <task_id>
```

## Notes

- This project no longer depends on `FastMCP` server registration.
- Core logic remains in `documents.py`, `tasks.py`, and `jxa.py`.
