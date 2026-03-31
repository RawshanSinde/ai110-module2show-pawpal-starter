# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three core actions a user should be able to perform in PawPal+:

1. **Add/manage a pet and owner profile** — The user enters basic information about themselves and their pet (e.g., owner name, pet name, species, age, and any special needs or constraints like limited mobility or medication schedules). This profile informs what tasks are relevant and what constraints the scheduler must respect.

2. **Add and edit care tasks** — The user creates tasks such as walks, feeding, medication, grooming, or enrichment activities. Each task has at minimum a duration (how long it takes) and a priority level (how critical it is that day). The user can also edit or remove existing tasks as their pet's needs change.

3. **Generate and view a daily care plan** — The user requests a daily schedule, and the app produces an ordered plan of tasks fitted within the owner's available time. The plan also explains why tasks were chosen and ordered as they were, helping the owner understand the tradeoffs the scheduler made.

**Object brainstorm — main classes, attributes, and methods:**

---

**Owner**
Represents the person caring for the pet.
- Attributes: `name` (str), `available_minutes` (int — total daily time budget), `preferences` (dict — e.g., preferred task times, categories to avoid)
- Methods:
  - `add_pet(pet)` — associate a pet with this owner
  - `get_available_time()` — return remaining schedulable minutes

---

**Pet**
Represents the animal being cared for.
- Attributes: `name` (str), `species` (str), `age` (int), `special_needs` (list[str] — e.g., "joint pain", "twice-daily insulin")
- Methods:
  - `has_special_needs()` → bool — whether the pet has any listed special needs
  - `get_task_list()` → list[Task] — return all tasks associated with this pet


The initial UML design centers on five classes that separate data, logic, and output into distinct responsibilities.

**Owner** holds the person's profile — their name, daily time budget (`available_minutes`), and scheduling preferences. It is the entry point for the system: it owns one or more pets and exposes how much time is actually available for scheduling.

**Pet** represents the animal and carries everything specific to it: species, age, and a list of special needs (e.g., medication, limited mobility). It is responsible for knowing whether special accommodations are needed and for returning the full list of tasks associated with it.

**Task** is the unit of work — a single care activity with a title, how long it takes, a priority level, a category (e.g., health, enrichment), whether it is required that day, and any notes. It knows how to describe itself and whether it should be treated as high priority.

**Scheduler** is the brain. It takes an owner, a pet, and the task list, then applies scheduling logic: ranking tasks by priority, checking whether each fits within the remaining time budget, producing a `DailyPlan`, and generating a natural-language explanation of the choices made.

**DailyPlan** is the output object. It holds the tasks that were scheduled, the ones that were skipped, the total time used, and an explanation string. It is responsible only for presenting results — not for making decisions.

**b. Design changes**

**c. UML Class Diagram**

See [pawpal_diagram.mmd](pawpal_diagram.mmd) for the full Mermaid class diagram.

Yes, three changes were made after reviewing the skeleton against the UML.

**1. Added `pets` list to `Owner` and `tasks` list to `Pet`.**
The UML arrows (`Owner --> 1..* Pet` and `Pet --> 0..* Task`) implied these relationships exist at runtime, but neither class had a backing list to store them. Without `self.pets = []` on `Owner`, calling `add_pet()` would have no place to append; without `self.tasks = []` on `Pet`, `get_task_list()` could never return anything meaningful. These lists make the relationships concrete rather than implied.

**2. Removed `available_minutes` from `Scheduler.__init__` and replaced it with `remaining_minutes`.**
The original skeleton passed `available_minutes` as a separate argument to `Scheduler`, duplicating the same value already stored on the `Owner` object. This created two sources of truth that could drift apart. Instead, `Scheduler` now reads the budget directly from `owner.available_minutes` at construction time and stores it as `self.remaining_minutes` — a counter that `fits_in_budget` can decrement as tasks are scheduled. This makes the time-tracking logic unambiguous and eliminates the redundancy.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four constraints:

1. **Time budget** — the owner's `available_minutes` is the hard outer limit. No task is scheduled if it would exceed the remaining minutes. This is checked on every task via `fits_in_budget()`, and a second pass runs after the initial greedy sort to fill any leftover time with tasks that were initially skipped.

2. **Priority and required status** — tasks are ranked by `is_required` first, then by `priority` level (high → medium → low), then by shortest duration. Required tasks are treated as non-negotiable: a required task will always be scheduled before any optional task of equal or lower priority.

3. **Owner preferences** — the `avoid_category` preference in `owner.preferences` causes optional tasks in that category to be filtered out entirely before scheduling begins. A grooming-averse owner will never see optional grooming tasks in their plan, even if time allows.

4. **Time of day (slot)** — tasks with a `time_of_day` value ("morning", "afternoon", "evening") sort before unslotted tasks, and morning slots sort before afternoon, which sorts before evening. This ensures the schedule reads in a natural daily order rather than purely by priority.

The constraints were prioritized in this order — time, then required status, then priority, then slot — because they reflect real-world urgency. Running out of time is a hard physical constraint that cannot be worked around, so it governs everything. Within that limit, a pet's medical or safety needs (required tasks) matter more than convenience-based priorities set by the owner. Preferences like `avoid_category` come next because they reflect the owner's judgment about what is reasonable on a given day. Slot ordering is last because it is purely cosmetic — it affects readability of the schedule, not whether tasks get done.

**b. Tradeoffs**

The scheduler uses a **greedy algorithm**: it ranks all tasks once by slot → required status → priority → shortest duration, then schedules them in that order until the time budget runs out. A second pass then fills any leftover minutes with tasks that were initially skipped.

The tradeoff is **speed and simplicity over optimal packing**. A greedy approach does not guarantee the best possible combination of tasks — for example, it might schedule a 30-minute optional task early and leave only 25 minutes for a 28-minute required task that arrives later in the sorted order. An optimal solution would require evaluating all possible subsets (a knapsack-style search), which becomes exponentially expensive as the task list grows.

This tradeoff is reasonable for a pet care scheduler because the task lists are small — a typical owner manages fewer than 20 tasks across one or two pets. At that scale, the greedy result and the optimal result are almost always identical, and the cases where they differ (a required task getting bumped) are caught and surfaced explicitly by the conflict detection system rather than silently dropped. The owner sees a warning and can adjust. Simplicity and predictability matter more here than mathematical optimality: the schedule needs to be readable and explainable, not just maximally packed.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI throughout the project across several distinct phases rather than just for one type of task.

During the **review and audit phase**, I asked the AI to read `pawpal_system.py` and list the core behaviors worth verifying before writing any tests. This surfaced behaviors I had implemented but hadn't consciously catalogued — like the second-pass budget fill in `generate_plan` and the silent no-op when `mark_complete` is called on a task with no pet set. Having those behaviors named explicitly made it much easier to write targeted tests.

During the **test generation phase**, I gave the AI a specific list of three behaviors and asked it to generate tests for each one. Being specific about what to test (sorting correctness, recurrence logic, conflict detection) produced more useful output than asking broadly — the AI wrote tests that matched the actual method signatures rather than generic unit tests.

During the **UI and display phase**, I asked the AI to update `app.py` to use `Scheduler` methods in the display logic and use Streamlit components like `st.success`, `st.warning`, and `st.metric`. The prompt that worked best here was combining the *what* (use these methods, use these components) with the *why* (make the output look professional).

For the **UML reconciliation**, the most useful prompt was asking the AI to compare the diagram directly against the final code and list every gap. That framing — "does this still match?" — produced a specific diff rather than a general redraw.

**b. Judgment and verification**

When the AI updated the task list display to use `sort_by_time()`, it initially kept `st.table` as the rendering component. I didn't accept that as the final version because `st.table` is fully static — there is no way to attach Edit or Delete buttons to its rows. I pushed back and asked for a per-row layout using `st.columns`, which is what made the edit and delete interaction possible. I verified the change worked by running the app and confirming the buttons appeared on each task row and that clicking Edit opened the inline form with pre-populated values.

I also cross-checked the generated tests manually before running them. For the recurrence tests in particular, I read through `mark_complete()` in `pawpal_system.py` to confirm that the `if self.pet is not None` guard was actually there before writing the test that verifies it doesn't raise — I didn't want to write a test for behavior I had assumed rather than read.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers five areas across 23 tests:

1. **Task completion** — that tasks start incomplete, that `mark_complete` flips the flag, and that calling it twice is safe (idempotency). These matter because the filter logic in `filter_by_status` depends entirely on `task.completed` being accurate.

2. **Task addition** — that new pets start with an empty task list, that adding tasks increments the count correctly, and that the task object is retrievable. These verify that the `pet.add_task()` and `pet.get_task_list()` contract holds before any scheduling logic runs on top of it.

3. **Sorting correctness** — that `sort_by_time()` returns morning before afternoon before evening before unslotted, that tasks sharing a slot preserve their original order (stable sort), and that edge cases like a single task or an already-sorted list don't change anything. Sorting is the foundation of the ranked schedule display — if it's wrong, every schedule output is wrong.

4. **Recurrence logic** — that completing a daily task adds a fresh incomplete copy to the pet's task list, that the original is retained as history, that one-time tasks don't spawn copies, and that completing a task without a pet set doesn't raise. Recurrence is the highest-risk behavior in the system because it mutates state as a side effect of marking completion — a subtle bug here would silently corrupt the task list.

5. **Conflict detection** — that same-pet slot overlap is flagged, that different-slot tasks are not flagged, that cross-pet required overlap is caught, that optional overlap is not, and that unslotted tasks are never flagged. Conflict detection is what makes the scheduler trustworthy: without it, invalid schedules would be presented to the user without any indication that something is wrong.

**b. Confidence**

I would rate my confidence at **4 out of 5**. The behaviors I tested are the most critical ones — sorting, recurrence mutation, and conflict detection — and all 23 tests pass cleanly. I'm confident those paths work correctly.

The gap that keeps me from 5 stars: I haven't tested `generate_plan` end-to-end, which is where sorting, filtering, conflict detection, and budget scheduling all interact. A bug in the composition of those steps would not be caught by the individual unit tests. I also haven't tested the `avoid_category` preference filter, weekly recurrence day matching, or the second-pass fill logic in isolation.

Edge cases I would test next with more time:
- A required task whose duration alone exceeds the entire budget — it should be skipped with a conflict warning, not crash.
- The second-pass fill: a task that is too large in pass one but fits exactly in the leftover budget after smaller tasks are scheduled.
- `weekly` recurrence with an empty `recurrence_days` list — the current code falls through to `return True`, which is probably a bug.
- Completing a daily task multiple times in sequence — each call spawns a new copy, so the task list grows unboundedly.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the conflict detection system. It was the part of the project where the design decision — returning warning strings instead of raising exceptions — had the most visible impact on user experience. Because `detect_conflicts()` never crashes the scheduler, the app always produces a plan even when the input is flawed, and the user sees exactly what went wrong in plain English. That felt like a real design choice rather than just implementation work.

The UML reconciliation was also satisfying. Going back to the original diagram, comparing it line by line against the final code, and producing an updated version that accurately reflected six classes and their actual relationships gave me a clear picture of how much the design had evolved during the build.

**b. What you would improve**

If I had another iteration, I would redesign the session state management in `app.py`. Right now, saving a new owner and pet resets the entire state — any tasks already added are lost. For a real app this would be a critical bug: a user who accidentally hits "Save Owner & Pet" twice loses all their work. I would add a confirmation step or separate the owner/pet profile from the task list so they can be updated independently.

I would also add `weekly` recurrence support to the UI. The backend fully supports `recurrence="weekly"` with a `recurrence_days` list, but the add task form in `app.py` has no way to set recurrence mode or specify which days. That's a significant feature gap between what the system can do and what the interface exposes.

**c. Key takeaway**

The most important thing I learned is that **a clean class boundary is worth more than a clever algorithm**. The reason the scheduler was relatively easy to build incrementally — adding sorting, then filtering, then conflict detection without breaking earlier work — was that `Scheduler`, `Task`, `Pet`, and `DailyPlan` each had a single clear responsibility from the start. When I needed to add a new method, I knew exactly which class it belonged to. When I needed to write a test, I knew exactly what I was testing.

Working with AI reinforced this: the AI was most useful when I asked it to work within an existing boundary ("add these methods to Scheduler", "update the display in app.py to use Scheduler's methods"). The moments where output needed the most correction were when the boundary was blurry — early in the project, before the class responsibilities were fully settled.
