# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Demo

### Owner & Pet Setup
Enter the owner's name, daily time budget, and pet profile. Saving creates the Owner and Pet objects and displays a confirmation banner.

<a href="/course_images/ai110/pawpal_owner_pet.png" target="_blank"><img src='/course_images/ai110/pawpal_owner_pet.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

### Adding & Managing Tasks
Tasks are added with a title, category, duration, priority, time slot, and required flag. The task list displays sorted by time slot with **Edit** and **Del** buttons on every row.

<a href="/course_images/ai110/pawpal_task_list.png" target="_blank"><img src='/course_images/ai110/pawpal_task_list.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

### Inline Task Editing
Clicking **Edit** on any row opens a pre-populated form directly below the task list. Changes are saved in-place without losing the rest of the schedule state. Clicking **Cancel** dismisses the form without making any changes.

<a href="/course_images/ai110/pawpal_edit_task.png" target="_blank"><img src='/course_images/ai110/pawpal_edit_task.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

### Schedule Output
Generating a schedule shows budget metrics, any detected conflicts as warnings, a ranked table of scheduled tasks, and a plain-English explanation of all scheduling decisions.

<a href="/course_images/ai110/pawpal_schedule.png" target="_blank"><img src='/course_images/ai110/pawpal_schedule.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

---

## Features

### Greedy budget scheduler with second-pass fill
`Scheduler.generate_plan()` builds a daily schedule in two passes. The first pass iterates through tasks in ranked order and greedily schedules any task that fits within the owner's remaining time budget. Tasks that are too large to fit are set aside. The second pass revisits those skipped tasks and schedules any that now fit in the leftover budget — ensuring short tasks deferred by an early large task are not permanently dropped.

### Multi-key task ranking
`Scheduler.rank_tasks()` sorts tasks by four keys applied in order of significance: (1) time slot — morning before afternoon before evening before unslotted; (2) required status — required tasks before optional ones within the same slot; (3) priority level — high before medium before low; (4) duration — shorter tasks first when all other keys tie, maximising the number of tasks that fit within a limited budget.

### Chronological slot sorting
`Scheduler.sort_by_time()` provides a lightweight sort by time slot only, preserving the original relative order of tasks that share a slot (stable sort). Used in the UI to display task lists in chronological order without mixing in priority or required-status as secondary keys.

### Composable task filtering
Three filters can be chained in any combination:
- `filter_by_status(tasks, include_completed)` — returns incomplete tasks by default; pass `include_completed=True` for a history view.
- `filter_by_pet(tasks, pet_name)` — narrows the list to a single named pet (case-insensitive). Tasks without a pet backref are always excluded.
- `filter_tasks(day_of_week, pet, include_completed)` — the main filter used by `generate_plan`. Applies recurrence rules, delegates to the two filters above, and soft-drops any optional task whose category matches the owner's `avoid_category` preference.

### Automatic task recurrence
Tasks support three recurrence modes: `one-time`, `daily`, and `weekly` (with a `recurrence_days` list). When `mark_complete()` is called on a `daily` or `weekly` task, a fresh incomplete copy is automatically added to the pet's task list so the next occurrence is ready without any manual intervention. The completed original is retained as a history record.

### Inline task editing and deletion
Every task row in the UI includes **Edit** and **Del** buttons. Clicking Edit stores a reference to the task object in session state and renders a pre-populated form inline — no page navigation required. Saving mutates the task object in-place so the updated values are immediately reflected in the task list and any subsequent schedule generation. Clicking Del removes the task from the pet's task list entirely and refreshes the view. If the task being deleted was also open in the edit form, the form is dismissed automatically.

### Four-check conflict detection
`Scheduler.detect_conflicts()` runs automatically inside `generate_plan()` and returns plain-English warning strings rather than raising exceptions, so the schedule is always produced even when problems are found:
1. **Budget overrun** — required tasks whose combined duration exceeds the owner's daily time budget.
2. **Slot capacity** — a named slot (morning / afternoon / evening) whose total assigned minutes exceeds a per-slot cap.
3. **Duplicate titles** — the same task title registered more than once for the same pet.
4. **Time conflicts** (via `detect_time_conflicts()`) — flags same-pet slot overlap (one animal cannot physically be in two activities at once) and cross-pet required overlap (the owner cannot attend to two animals' required needs simultaneously).

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

The `Scheduler` class (`pawpal_system.py`) goes beyond a simple priority sort. The following features were added in Phase 3:

### Time-slot sorting
Every task carries an optional `time_of_day` value — `"morning"`, `"afternoon"`, `"evening"`, or `None` (unslotted). `sort_by_time()` orders any task list chronologically by slot while preserving the original relative order within each slot. `rank_tasks()` layers required-status, priority, and duration on top of this slot order and is used internally by `generate_plan`.

### Filtering
Two composable filter methods let you narrow a task list before scheduling or display:

- `filter_by_status(tasks, include_completed=False)` — returns only incomplete tasks by default; pass `include_completed=True` for a history view.
- `filter_by_pet(tasks, pet_name)` — returns tasks belonging to a single named pet (case-insensitive). Both methods can be chained: `filter_by_status(filter_by_pet(all_tasks, "Biscuit"))`.

The main `filter_tasks()` method delegates to both and also applies recurrence rules and the owner's `avoid_category` preference.

### Recurring tasks
Tasks support three recurrence modes set via the `recurrence` parameter:

| Value | Behaviour |
|---|---|
| `"one-time"` | Scheduled until completed, then removed from future plans. |
| `"daily"` | Active every day. |
| `"weekly"` | Active only on days listed in `recurrence_days` (e.g. `["tuesday", "friday"]`). |

When a `daily` or `weekly` task is marked complete via `mark_complete()`, a fresh copy is automatically added to the pet's task list so the next occurrence is ready without any manual intervention.

### Conflict detection
`detect_conflicts()` runs automatically inside `generate_plan()` and checks four conditions, returning plain-English warning strings rather than raising exceptions:

1. **Budget overrun** — required tasks whose total duration exceeds `available_minutes`.
2. **Slot capacity** — a named slot (morning/afternoon/evening) whose total task time exceeds a reasonable per-slot cap.
3. **Duplicate titles** — the same task title added twice for the same pet.
4. **Time conflicts** (via `detect_time_conflicts()`) — two patterns:
   - *Same-pet overlap*: a single pet has more than one task in the same slot.
   - *Cross-pet required overlap*: two different pets both have required tasks in the same slot, meaning the owner would need to be in two places at once.

All warnings appear in `DailyPlan.conflicts` and are printed at the top of the schedule output.

## Testing PawPal

### Running the tests

```bash
python3 -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The test suite (23 tests) verifies three areas of core scheduling behavior:

| Area | Tests | What is verified |
|---|---|---|
| **Task completion** | 3 | Tasks start incomplete; `mark_complete` flips the flag; calling it twice is safe. |
| **Task addition** | 4 | New pets start with no tasks; adding tasks increases the count; tasks are retrievable by index. |
| **Sorting correctness** | 5 | Tasks sort morning → afternoon → evening → unslotted; same-slot tasks preserve insertion order; single-task and already-sorted inputs are stable. |
| **Recurrence logic** | 6 | Completing a `daily` task adds a fresh incomplete copy to the pet; the original is kept as history; `one-time` tasks do not spawn copies; completing without a pet set does not raise. |
| **Conflict detection** | 5 | Same-pet tasks in the same slot are flagged; different slots are not; cross-pet required overlap is flagged; optional overlap is not; unslotted tasks are never flagged. |

### Confidence Level

★★★★☆ (4 / 5)

The core scheduling behaviors — sorting, recurrence, and conflict detection — are well covered and all 23 tests pass. The rating stops short of 5 stars because the following areas are not yet tested: budget-constrained scheduling (greedy pass + second-pass fill), the `avoid_category` owner preference filter, `weekly` recurrence day matching, and the full `generate_plan` integration path. Adding tests for those scenarios would bring confidence to 5 stars.
