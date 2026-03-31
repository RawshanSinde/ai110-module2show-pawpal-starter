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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
