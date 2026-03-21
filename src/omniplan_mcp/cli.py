import argparse
import asyncio
import json
from typing import Any

from omniplan_mcp.documents import list_documents
from omniplan_mcp.tasks import create_task, delete_task, get_task, query_tasks, sort_tasks, update_task


def _print_json(result: Any) -> None:
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            print(result)
            return
        print(json.dumps(parsed, ensure_ascii=False))
        return
    print(json.dumps(result, ensure_ascii=False))


async def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "documents" and args.action == "list":
        _print_json(await list_documents())
        return 0

    if args.command == "tasks" and args.action == "query":
        _print_json(
            await query_tasks(
                keyword=args.keyword,
                task_type=args.task_type,
                completed=args.completed,
                due_before=args.due_before,
                due_after=args.due_after,
                limit=args.limit,
                detail=args.detail,
            )
        )
        return 0

    if args.command == "tasks" and args.action == "get":
        _print_json(await get_task(args.task_id))
        return 0

    if args.command == "tasks" and args.action == "create":
        _print_json(
            await create_task(
                title=args.title,
                parent_id=args.parent_id,
                task_type=args.task_type,
                note=args.note,
                manual_start_date=args.manual_start_date,
                manual_end_date=args.manual_end_date,
                sort_siblings=not args.no_sort,
            )
        )
        return 0

    if args.command == "tasks" and args.action == "update":
        _print_json(
            await update_task(
                task_id=args.task_id,
                title=args.title,
                note=args.note,
                completed=args.completed,
                manual_start_date=args.manual_start_date,
                manual_end_date=args.manual_end_date,
                sort_siblings=not args.no_sort,
            )
        )
        return 0

    if args.command == "tasks" and args.action == "sort":
        _print_json(await sort_tasks(parent_id=args.parent_id))
        return 0

    if args.command == "tasks" and args.action == "delete":
        _print_json(await delete_task(args.task_id))
        return 0

    raise ValueError("Unknown command.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omniplan-skill")
    sub = parser.add_subparsers(dest="command", required=True)

    docs = sub.add_parser("documents", help="OmniPlan documents commands")
    docs_sub = docs.add_subparsers(dest="action", required=True)
    docs_sub.add_parser("list", help="List open OmniPlan documents")

    tasks = sub.add_parser("tasks", help="OmniPlan task commands")
    tasks_sub = tasks.add_subparsers(dest="action", required=True)

    query = tasks_sub.add_parser("query", help="Query tasks")
    query.add_argument("--keyword")
    query.add_argument("--task-type", choices=["task", "group", "milestone", "hammock"])
    query.add_argument("--completed", type=lambda v: v.lower() in ("1", "true", "yes"))
    query.add_argument("--due-before")
    query.add_argument("--due-after")
    query.add_argument("--limit", type=int)
    query.add_argument("--detail", choices=["summary", "full"], default="summary")

    get_cmd = tasks_sub.add_parser("get", help="Get one task by id")
    get_cmd.add_argument("task_id")

    create_cmd = tasks_sub.add_parser("create", help="Create a task")
    create_cmd.add_argument("title")
    create_cmd.add_argument("--parent-id")
    create_cmd.add_argument("--task-type", choices=["task", "group", "milestone", "hammock"])
    create_cmd.add_argument("--note")
    create_cmd.add_argument("--manual-start-date")
    create_cmd.add_argument("--manual-end-date")
    create_cmd.add_argument("--no-sort", action="store_true", help="Skip auto-sort after creation")

    update_cmd = tasks_sub.add_parser("update", help="Update a task")
    update_cmd.add_argument("task_id")
    update_cmd.add_argument("--title")
    update_cmd.add_argument("--note")
    update_cmd.add_argument("--completed", type=lambda v: v.lower() in ("1", "true", "yes"))
    update_cmd.add_argument("--manual-start-date")
    update_cmd.add_argument("--manual-end-date")
    update_cmd.add_argument("--no-sort", action="store_true", help="Skip auto-sort after update")

    sort_cmd = tasks_sub.add_parser("sort", help="Sort children of a parent by start date")
    sort_cmd.add_argument("--parent-id", help="Parent task ID (omit for root)")

    delete_cmd = tasks_sub.add_parser("delete", help="Delete a task")
    delete_cmd.add_argument("task_id")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return asyncio.run(_dispatch(args))
    except Exception as exc:
        parser.exit(1, f"{exc}\n")

