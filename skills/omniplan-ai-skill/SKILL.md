---
name: omniplan-ai-skill
description: Read and operate OmniPlan from a local Python CLI without MCP installation. Use when the user wants to list open OmniPlan documents, query tasks, or create/update/delete OmniPlan tasks on macOS.
---

# OmniPlan AI Skill

Use this skill when the user wants OmniPlan automation without MCP.

## Requirements

- macOS
- OmniPlan running with at least one open document
- Automation permission granted to the terminal app

## Default entrypoint

Run the wrapper script from the repo root:

```bash
python3 scripts/omniplan_skill.py --help
```

This wrapper adds `src/` to `sys.path`, so no installation is required.

## Commands

List open documents:

```bash
python3 scripts/omniplan_skill.py documents list
```

Query tasks:

```bash
python3 scripts/omniplan_skill.py tasks query --keyword gantt --detail full
```

Get one task:

```bash
python3 scripts/omniplan_skill.py tasks get <task_id>
```

Create a task:

```bash
python3 scripts/omniplan_skill.py tasks create "Beta Launch" --task-type milestone
```

Update a task:

```bash
python3 scripts/omniplan_skill.py tasks update <task_id> --title "Updated title"
```

Delete a task:

```bash
python3 scripts/omniplan_skill.py tasks delete <task_id>
```

## Notes

- The task commands always target the frontmost OmniPlan document.
- The CLI returns JSON. Summarize it for the user instead of dumping large raw payloads unless they explicitly ask for raw output.
- If OmniPlan access fails, check macOS Automation permission first.
