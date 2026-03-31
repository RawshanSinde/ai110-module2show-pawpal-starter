# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

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
