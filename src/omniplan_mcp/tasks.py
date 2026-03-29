import json
from typing import Optional
from omniplan_mcp.jxa import run_omnijs

def _doc_selector() -> str:
    """Returns JS expression to get the front document's root project."""
    return "const _proj = document.project;"


def _fmt_date() -> str:
    """JS helper to format dates as YYYY-MM-DD."""
    return """
function fmtDate(d) {
  if (!d) return null;
  var y = d.getFullYear();
  var m = ('0' + (d.getMonth() + 1)).slice(-2);
  var day = ('0' + d.getDate()).slice(-2);
  return y + '-' + m + '-' + day;
}
"""


def _task_to_obj() -> str:
    """JS helper function to serialize a Task to a plain object.

    Note: 'parent_id', 'outline_id', and 'depth' are NOT set here — callers must inject them
    after traversal, because OmniPlan Automation does not expose a task.parent property.
    """
    return _fmt_date() + """
function toSeconds(v) {
  if (v === null || v === undefined) return 0;
  if (typeof v === 'number') return v;
  if (typeof v === 'object') {
    if (typeof v.workSeconds === 'number') return v.workSeconds;
    if (typeof v.elapsedSeconds === 'number') return v.elapsedSeconds;
    if (typeof v.seconds === 'number') return v.seconds;
    if (typeof v.value === 'number') return v.value;
  }
  var n = Number(v);
  return isNaN(n) ? 0 : n;
}

function taskToObj(task, summary) {
  if (summary) {
    return {
      title: task.title || '',
      type: String(task.type).replace(/.*TaskType:\\s*/, '').replace('TaskType.', '').replace(']', '').trim(),
      start_date: fmtDate(task.startDate),
      end_date: fmtDate(task.endDate),
    };
  }

  var effort = toSeconds(task.effort);
  var effortDone = toSeconds(task.effortDone);
  var dur = task.duration;
  var durationDays = (dur && typeof dur === 'object' && typeof dur.workSeconds === 'number') ? Math.round(dur.workSeconds / 28800 * 10) / 10 : 0;
  var completionPct = effort > 0 ? Math.round((effortDone / effort) * 100) : 0;

  var obj = {
    id: String(task.uniqueID),
    title: task.title || '',
    type: String(task.type).replace(/.*TaskType:\\s*/, '').replace('TaskType.', '').replace(']', '').trim(),
    completed: effortDone >= effort && effort > 0,
    start_date: fmtDate(task.startDate),
    end_date: fmtDate(task.endDate),
    depth: 0,
    parent_id: null,
    outline_id: null,
  };

  if (!summary) {
    obj.note = task.note || '';
    obj.completion_pct = completionPct;
    obj.manual_start_date = fmtDate(task.manualStartDate);
    obj.manual_end_date = fmtDate(task.manualEndDate);
    obj.duration_days = durationDays;
    obj.effort_seconds = effort;
    obj.effort_done_seconds = effortDone;
  }

  return obj;
}
"""


async def query_tasks(
    keyword: Optional[str] = None,
    task_type: Optional[str] = None,
    completed: Optional[bool] = None,
    due_before: Optional[str] = None,
    due_after: Optional[str] = None,

    detail: Optional[str] = None,
) -> str:
    """Query tasks in an OmniPlan document with optional filters.

    Args:
        keyword: Filter by title or note containing this text (case-insensitive).
        task_type: One of: task, group, milestone, hammock.
        completed: True = completed only, False = incomplete only, None = all.
        due_before: ISO date string (e.g. 2025-12-31). Tasks ending before this date.
        due_after: ISO date string (e.g. 2025-01-01). Tasks ending after this date.

        detail: 'summary' (default) returns core fields only; 'full' returns all fields.
    """
    doc_sel = _doc_selector()
    task_to_obj = _task_to_obj()

    filters = []
    if keyword:
        kw = json.dumps(keyword.lower())
        filters.append(f"(t.title || '').toLowerCase().includes({kw}) || (t.note || '').toLowerCase().includes({kw})")
    if task_type:
        filters.append(f"String(t.type).indexOf({json.dumps(task_type)}) !== -1")
    if completed is True:
        filters.append("(t.effortDone >= t.effort && t.effort > 0)")
    elif completed is False:
        filters.append("!(t.effortDone >= t.effort && t.effort > 0)")
    if due_before:
        filters.append(f"t.endDate && t.endDate <= new Date({json.dumps(due_before + 'T23:59:59')})")
    if due_after:
        filters.append(f"t.endDate && t.endDate >= new Date({json.dumps(due_after + 'T00:00:00')})")

    filter_expr = " && ".join(filters) if filters else "true"

    script = f"""
{doc_sel}
{task_to_obj}

var _rootUID = String(_proj.actual.rootTask.uniqueID);

function flatten(task, parentId, parentOutlineId) {{
  var results = [];
  for (var _i = 0; _i < task.subtasks.length; _i++) {{
    var child = task.subtasks[_i];
    var idx = String(_i + 1);
    var outlineId = parentOutlineId ? (parentOutlineId + '.' + idx) : idx;
    results.push({{raw: child, parentId: parentId, outlineId: outlineId}});
    results = results.concat(flatten(child, String(child.uniqueID), outlineId));
  }}
  return results;
}}

var root = _proj.actual.rootTask;
var allPairs = flatten(root, _rootUID, '');
var filtered = allPairs.filter(function(p) {{ var t = p.raw; return {filter_expr}; }});
var sliced = filtered;
var summary = {json.dumps(detail != 'full')};
return sliced.map(function(p) {{
  var obj = taskToObj(p.raw, summary);
  obj.outline_id = p.outlineId;
  if (!summary) {{
    obj.parent_id = (p.parentId === _rootUID) ? null : p.parentId;
  }}
  return obj;
}});
"""
    result = await run_omnijs(script)
    return json.dumps(result)


async def get_task(
    task_id: str,
) -> str:
    """Get full details of a single task by its unique ID.

    Args:
        task_id: The uniqueID of the task.
    """
    doc_sel = _doc_selector()
    task_to_obj = _task_to_obj()

    script = f"""
{doc_sel}
{task_to_obj}

var _rootUID = String(_proj.actual.rootTask.uniqueID);

function findById(task, id, parentId, outlineId) {{
  if (String(task.uniqueID) === id) return {{task: task, parentId: parentId, outlineId: outlineId}};
  for (var _i = 0; _i < task.subtasks.length; _i++) {{
    var child = task.subtasks[_i];
    var idx = String(_i + 1);
    var childOutlineId = outlineId ? (outlineId + '.' + idx) : idx;
    var found = findById(child, id, String(task.uniqueID), childOutlineId);
    if (found) return found;
  }}
  return null;
}}

var found = findById(_proj.actual.rootTask, {json.dumps(task_id)}, null, '');
if (!found) throw new Error('Task not found: {task_id}');
var obj = taskToObj(found.task);
obj.parent_id = (found.parentId === _rootUID || found.parentId === null) ? null : found.parentId;
obj.outline_id = found.outlineId || null;
return obj;
"""
    result = await run_omnijs(script)
    return json.dumps(result)


async def create_task(
    title: str,
    parent_id: Optional[str] = None,
    task_type: Optional[str] = None,
    note: Optional[str] = None,
    manual_start_date: Optional[str] = None,
    manual_end_date: Optional[str] = None,
    sort_siblings: bool = True,
) -> str:
    """Create a new task in an OmniPlan document.

    Args:
        title: Task title.
        parent_id: uniqueID of the parent task. If omitted, adds to root.
        task_type: One of: task, group, milestone, hammock. Defaults to task.
        note: Optional task description.
        manual_start_date: ISO date string for manual start.
        manual_end_date: ISO date string for manual end.
        sort_siblings: If True, sort siblings by startDate after creation.
    """
    doc_sel = _doc_selector()
    task_to_obj = _task_to_obj()

    set_type = f"newTask.type = TaskType.{task_type};" if task_type else ""
    set_note = f"newTask.note = {json.dumps(note)};" if note else ""
    set_start = f"newTask.manualStartDate = new Date({json.dumps(manual_start_date)});" if manual_start_date else ""
    set_end = f"newTask.manualEndDate = new Date({json.dumps(manual_end_date)});" if manual_end_date else ""

    script = f"""
{doc_sel}
{task_to_obj}

function findById(task, id, outlineId) {{
  if (String(task.uniqueID) === id) return {{task: task, outlineId: outlineId}};
  for (var _i = 0; _i < task.subtasks.length; _i++) {{
    var child = task.subtasks[_i];
    var idx = String(_i + 1);
    var childOutlineId = outlineId ? (outlineId + '.' + idx) : idx;
    var found = findById(child, id, childOutlineId);
    if (found) return found;
  }}
  return null;
}}

var parentId = {json.dumps(parent_id)};
var parentFound = parentId ? findById(_proj.actual.rootTask, parentId, '') : null;
var parent = parentFound ? parentFound.task : _proj.actual.rootTask;
if (parentId && !parentFound) throw new Error('Parent task not found: ' + parentId);
var parentOutlineId = parentFound ? parentFound.outlineId : '';

var newTask = parent.addSubtask();
newTask.title = {json.dumps(title)};
{set_type}
{set_note}
{set_start}
{set_end}

var obj = taskToObj(newTask);
obj.parent_id = parentId;
var newTaskIndex = parent.subtasks.indexOf(newTask) + 1;
obj.outline_id = parentOutlineId ? (parentOutlineId + '.' + String(newTaskIndex)) : String(newTaskIndex);
return obj;
"""
    result = await run_omnijs(script)
    if sort_siblings:
        await sort_tasks(parent_id=parent_id)
    return json.dumps(result)


async def update_task(
    task_id: str,
    title: Optional[str] = None,
    note: Optional[str] = None,
    completed: Optional[bool] = None,
    manual_start_date: Optional[str] = None,
    manual_end_date: Optional[str] = None,
    sort_siblings: bool = True,
) -> str:
    """Update an existing task. Only provided fields are changed.

    Args:
        task_id: The uniqueID of the task.
        title: New title.
        note: New note text.
        completed: True to mark complete, False to mark incomplete.
        manual_start_date: ISO date string, or empty string to clear.
        manual_end_date: ISO date string, or empty string to clear.
    """
    doc_sel = _doc_selector()
    task_to_obj = _task_to_obj()

    updates = []
    if title is not None:
        updates.append(f"task.title = {json.dumps(title)};")
    if note is not None:
        updates.append(f"task.note = {json.dumps(note)};")
    if completed is True:
        updates.append("if (task.effort > 0) { task.effortDone = task.effort; }")
    elif completed is False:
        updates.append("task.effortDone = 0;")
    if manual_start_date == "":
        updates.append("task.manualStartDate = null;")
    elif manual_start_date is not None:
        updates.append(f"task.manualStartDate = new Date({json.dumps(manual_start_date)});")
    if manual_end_date == "":
        updates.append("task.manualEndDate = null;")
    elif manual_end_date is not None:
        updates.append(f"task.manualEndDate = new Date({json.dumps(manual_end_date)});")

    if not updates:
        return json.dumps({"error": "No fields to update."})

    update_block = "\n".join(updates)

    script = f"""
{doc_sel}
{task_to_obj}

var _rootUID = String(_proj.actual.rootTask.uniqueID);

function findById(task, id, parentId, outlineId) {{
  if (String(task.uniqueID) === id) return {{task: task, parentId: parentId, outlineId: outlineId}};
  for (var _i = 0; _i < task.subtasks.length; _i++) {{
    var child = task.subtasks[_i];
    var idx = String(_i + 1);
    var childOutlineId = outlineId ? (outlineId + '.' + idx) : idx;
    var found = findById(child, id, String(task.uniqueID), childOutlineId);
    if (found) return found;
  }}
  return null;
}}

var found = findById(_proj.actual.rootTask, {json.dumps(task_id)}, null, '');
if (!found) throw new Error('Task not found: {task_id}');
var task = found.task;

{update_block}

var obj = taskToObj(task);
obj.parent_id = (found.parentId === _rootUID || found.parentId === null) ? null : found.parentId;
obj.outline_id = found.outlineId || null;
return obj;
"""
    result = await run_omnijs(script)
    if sort_siblings:
        parent_id_for_sort = result.get("parent_id") if isinstance(result, dict) else None
        await sort_tasks(parent_id=parent_id_for_sort)
    return json.dumps(result)


async def sort_tasks(
    parent_id: Optional[str] = None,
) -> str:
    """Sort short-duration tasks and milestones by startDate ascending.

    Only sorts milestones and tasks with duration <= 2 days. Long tasks
    and groups (with subtrees, custom colors) are left untouched.
    Uses delete-and-recreate only for the short tasks.

    Args:
        parent_id: uniqueID of the parent whose children to sort.
                   If omitted, sorts root-level tasks.
    """
    doc_sel = _doc_selector()
    task_to_obj = _task_to_obj()

    script = f"""
{doc_sel}
{task_to_obj}

function findById(task, id) {{
  if (String(task.uniqueID) === id) return task;
  for (var _i = 0; _i < task.subtasks.length; _i++) {{
    var found = findById(task.subtasks[_i], id);
    if (found) return found;
  }}
  return null;
}}

var TWO_DAYS_MS = 2 * 24 * 60 * 60 * 1000;

function isSortable(task) {{
  var typeStr = String(task.type).replace(/.*TaskType:\\s*/, '').replace('TaskType.', '').replace(']', '').trim();
  if (typeStr === 'milestone') return true;
  if (task.subtasks.length > 0) return false; // groups/parents stay
  var startMs = task.startDate ? task.startDate.getTime() : null;
  var endMs = task.endDate ? task.endDate.getTime() : null;
  if (startMs && endMs && (endMs - startMs) <= TWO_DAYS_MS) return true;
  return false;
}}

var parentId = {json.dumps(parent_id)};
var parent = parentId ? findById(_proj.actual.rootTask, parentId) : _proj.actual.rootTask;
if (parentId && !parent) throw new Error('Parent task not found: ' + parentId);

var childCount = parent.subtasks.length;
if (childCount === 0) return {{sorted: 0, message: 'No children to sort.'}};

// Separate into fixed (stay in place) and sortable (milestones/short tasks)
var fixed = []; // {{index, startMs}}
var sortable = []; // {{snapshot, startMs}}
for (var _i = 0; _i < childCount; _i++) {{
  var task = parent.subtasks[_i];
  var startMs = task.startDate ? task.startDate.getTime() : null;
  if (isSortable(task)) {{
    var typeStr = String(task.type).replace(/.*TaskType:\\s*/, '').replace('TaskType.', '').replace(']', '').trim();
    sortable.push({{
      title: task.title || '',
      type: typeStr,
      note: task.note || '',
      effort: task.effort,
      effortDone: task.effortDone,
      manualStartMs: task.manualStartDate ? task.manualStartDate.getTime() : null,
      manualEndMs: task.manualEndDate ? task.manualEndDate.getTime() : null,
      startMs: startMs,
      origIndex: _i
    }});
  }} else {{
    fixed.push({{index: _i, startMs: startMs}});
  }}
}}

if (sortable.length === 0) return {{sorted: 0, message: 'No sortable tasks found.', changed: false}};

// Check if sortable tasks are already in correct chronological order BEFORE sorting
var alreadySorted = true;
for (var _i = 0; _i < sortable.length - 1; _i++) {{
  var da = sortable[_i].startMs !== null ? sortable[_i].startMs : Infinity;
  var db = sortable[_i + 1].startMs !== null ? sortable[_i + 1].startMs : Infinity;
  if (da > db) {{ alreadySorted = false; break; }}
}}
// Also check they were already at the end (after all fixed tasks)
if (alreadySorted && sortable.length > 0 && fixed.length > 0) {{
  var lastFixedIdx = fixed[fixed.length - 1].index;
  var firstSortableIdx = sortable[0].origIndex;
  if (firstSortableIdx < lastFixedIdx) alreadySorted = false;
}}
if (alreadySorted) return {{sorted: sortable.length, message: 'Already sorted.', changed: false}};

// Sort sortable tasks by startDate
sortable.sort(function(a, b) {{
  var da = a.startMs !== null ? a.startMs : Infinity;
  var db = b.startMs !== null ? b.startMs : Infinity;
  return da - db;
}});

// Delete sortable tasks (in reverse index order to avoid shifting)
var sortableIndices = sortable.map(function(s) {{ return s.origIndex; }});
sortableIndices.sort(function(a, b) {{ return b - a; }}); // reverse
for (var _i = 0; _i < sortableIndices.length; _i++) {{
  parent.subtasks[sortableIndices[_i]].remove();
}}

// Recreate sortable tasks in sorted order (appended to end)
var created = [];
for (var _i = 0; _i < sortable.length; _i++) {{
  var snap = sortable[_i];
  var t = parent.addSubtask();
  t.title = snap.title;
  if (snap.type === 'milestone') t.type = TaskType.milestone;
  if (snap.effort > 0) t.effort = snap.effort;
  if (snap.effortDone > 0) t.effortDone = snap.effortDone;
  if (snap.manualStartMs) t.manualStartDate = new Date(snap.manualStartMs);
  if (snap.manualEndMs) t.manualEndDate = new Date(snap.manualEndMs);
  if (snap.note) t.note = snap.note;
  created.push({{
    title: t.title,
    start_date: fmtDate(t.startDate)
  }});
}}

return {{sorted: created.length, fixed: fixed.length, changed: true, tasks: created}};
"""
    result = await run_omnijs(script)
    return json.dumps(result)


async def delete_task(
    task_id: str,
) -> str:
    """Delete a task by its unique ID.

    Args:
        task_id: The uniqueID of the task to delete.
    """
    doc_sel = _doc_selector()

    script = f"""
{doc_sel}

function findById(task, id) {{
  if (String(task.uniqueID) === id) return task;
  for (const child of task.subtasks) {{
    const found = findById(child, id);
    if (found) return found;
  }}
  return null;
}}

const task = findById(_proj.actual.rootTask, {json.dumps(task_id)});
if (!task) throw new Error('Task not found: {task_id}');
const title = task.title;
task.remove();
return {{ deleted: true, id: {json.dumps(task_id)}, title: title }};
"""
    result = await run_omnijs(script)
    return json.dumps(result)
