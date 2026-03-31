from pawpal_system import Owner, Pet, Task, Scheduler

# --- Owner ---
owner = Owner(name="Jordan", available_minutes=90, preferences={"avoid_category": "grooming"})

# --- Pets ---
dog = Pet(name="Biscuit", species="Dog", age=4, special_needs=["joint supplement"])
cat = Pet(name="Mochi", species="Cat", age=2, special_needs=[])

# --- Tasks added deliberately out of order (evening → afternoon → morning → unslotted) ---
dog.add_task(Task(
    title="Brush coat",
    duration_minutes=15,
    priority="low",
    category="grooming",
    is_required=False,
    notes="",
    time_of_day="evening",
    recurrence="weekly",
    recurrence_days=["tuesday", "friday"],
))
dog.add_task(Task(
    title="Vet check-up",
    duration_minutes=60,
    priority="high",
    category="health",
    is_required=True,
    notes="Annual appointment",
    time_of_day="afternoon",
    recurrence="one-time",
))
dog.add_task(Task(
    title="Joint supplement",
    duration_minutes=5,
    priority="high",
    category="health",
    is_required=True,
    notes="Mix into wet food",
    time_of_day="morning",
    recurrence="daily",
))
dog.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    category="exercise",
    is_required=True,
    notes="Keep to flat terrain due to joint supplement",
    time_of_day="morning",
    recurrence="daily",
))

cat.add_task(Task(
    title="Play session",
    duration_minutes=20,
    priority="medium",
    category="enrichment",
    is_required=False,
    notes="Wand toy preferred",
    time_of_day="afternoon",
    recurrence="daily",
))
cat.add_task(Task(
    title="Litter box cleaning",
    duration_minutes=10,
    priority="high",
    category="hygiene",
    is_required=True,
    notes="",
    time_of_day="morning",
    recurrence="daily",
))
cat.add_task(Task(
    title="Evening check-in",
    duration_minutes=5,
    priority="low",
    category="enrichment",
    is_required=False,
    notes="Settle before bed",
    time_of_day="evening",
    recurrence="daily",
))
# Intentionally no time_of_day to verify unslotted tasks sort last
cat.add_task(Task(
    title="Weigh-in",
    duration_minutes=5,
    priority="medium",
    category="health",
    is_required=False,
    notes="Track monthly weight",
    time_of_day=None,
    recurrence="daily",
))

# --- Deliberate conflicts for detect_time_conflicts demo ---
# Conflict A (same-pet): Biscuit gets a second required morning task
dog.add_task(Task(
    title="Teeth brushing",
    duration_minutes=10,
    priority="high",
    category="hygiene",
    is_required=True,
    notes="Clashes with morning walk",
    time_of_day="morning",       # <-- same slot as Morning walk & Joint supplement
    recurrence="daily",
))
# Conflict B (cross-pet required): Mochi also has a required morning task,
# so both Biscuit and Mochi have required tasks in morning simultaneously
# (Litter box cleaning already exists for Mochi in morning — no extra task needed)

# Mark Joint supplement already done to test filter_by_status
dog.tasks[1].mark_complete()   # Joint supplement (index 1 = Vet check-up after reorder)

# --- Register pets ---
owner.add_pet(dog)
owner.add_pet(cat)

DAY = "tuesday"
all_tasks = owner.get_all_tasks()
scheduler = Scheduler(owner=owner, tasks=all_tasks)

WIDTH = 52
DIV = "  " + "─" * (WIDTH - 4)


def task_row(task):
    marker = "[!]" if task.is_required else "   "
    pet_name = task.pet.name if task.pet else "?"
    done = " ✓" if task.completed else ""
    slot = task.time_of_day or "unslotted"
    return f"  {marker} {task.title:<24} {task.duration_minutes:>3} min  [{slot:<9}]  {pet_name}{done}"


# ── Section 1: raw insertion order ────────────────────────────────────────────
print("=" * WIDTH)
print("  RAW INSERTION ORDER")
print("=" * WIDTH)
for t in all_tasks:
    print(task_row(t))

# ── Section 2: sort_by_time ────────────────────────────────────────────────────
print()
print("=" * WIDTH)
print("  SORTED BY TIME SLOT  (sort_by_time)")
print("=" * WIDTH)
for t in scheduler.sort_by_time(all_tasks):
    print(task_row(t))

# ── Section 3: filter_by_pet ───────────────────────────────────────────────────
print()
print("=" * WIDTH)
print("  FILTER BY PET: Biscuit  (filter_by_pet)")
print("=" * WIDTH)
biscuit_tasks = scheduler.filter_by_pet(all_tasks, "Biscuit")
for t in scheduler.sort_by_time(biscuit_tasks):
    print(task_row(t))

print()
print("=" * WIDTH)
print("  FILTER BY PET: Mochi  (filter_by_pet)")
print("=" * WIDTH)
mochi_tasks = scheduler.filter_by_pet(all_tasks, "Mochi")
for t in scheduler.sort_by_time(mochi_tasks):
    print(task_row(t))

# ── Section 4: filter_by_status ───────────────────────────────────────────────
print()
print("=" * WIDTH)
print("  INCOMPLETE TASKS ONLY  (filter_by_status, default)")
print("=" * WIDTH)
incomplete = scheduler.filter_by_status(all_tasks)
for t in scheduler.sort_by_time(incomplete):
    print(task_row(t))

print()
print("=" * WIDTH)
print("  ALL TASKS incl. completed  (filter_by_status include_completed=True)")
print("=" * WIDTH)
all_with_done = scheduler.filter_by_status(all_tasks, include_completed=True)
for t in scheduler.sort_by_time(all_with_done):
    print(task_row(t))

# ── Section 5: composed filter — Biscuit, incomplete, sorted ──────────────────
print()
print("=" * WIDTH)
print("  COMPOSED: Biscuit + incomplete + sorted by time")
print("=" * WIDTH)
composed = scheduler.filter_by_status(
    scheduler.filter_by_pet(all_tasks, "Biscuit")
)
for t in scheduler.sort_by_time(composed):
    print(task_row(t))

# ── Section 6: detect_time_conflicts in isolation ─────────────────────────────
print()
print("=" * WIDTH)
print("  TIME CONFLICT DETECTION  (detect_time_conflicts)")
print("=" * WIDTH)
time_warnings = scheduler.detect_time_conflicts(all_tasks)
if time_warnings:
    for w in time_warnings:
        print(f"  ! {w}")
else:
    print("  No time conflicts detected.")

# ── Section 7: full schedule ──────────────────────────────────────────────────
plan = scheduler.generate_plan(day_of_week=DAY)

print()
print("=" * WIDTH)
print(f"  TODAY'S SCHEDULE — {owner.name}  ({DAY.capitalize()})  [Section 7]")
print(f"  Budget: {owner.available_minutes} min  |  Used: {plan.total_duration} min")
print("=" * WIDTH)

if plan.conflicts:
    print(f"\n  CONFLICTS ({len(plan.conflicts)})")
    print(DIV)
    for c in plan.conflicts:
        print(f"  ! {c}")

for slot in ("morning", "afternoon", "evening", None):
    label = (slot or "flexible").upper()
    slot_tasks = [t for t in plan.scheduled_tasks if t.time_of_day == slot]
    if not slot_tasks:
        continue
    print(f"\n  {label}")
    print(DIV)
    for task in slot_tasks:
        marker = "[!]" if task.is_required else "   "
        pet_name = task.pet.name if task.pet else "?"
        recur = f" ({task.recurrence})" if task.recurrence != "one-time" else ""
        print(f"  {marker} {task.title:<24} {task.duration_minutes:>3} min  {pet_name}{recur}")

if plan.skipped_tasks:
    print(f"\n  SKIPPED")
    print(DIV)
    for task in plan.skipped_tasks:
        pet_name = task.pet.name if task.pet else "?"
        print(f"      {task.title:<24} {task.duration_minutes:>3} min  {pet_name}")

required_count = sum(1 for t in plan.scheduled_tasks if t.is_required)
optional_count = sum(1 for t in plan.scheduled_tasks if not t.is_required)
print(f"\n  [!] = required  |  avoid_category: {owner.preferences.get('avoid_category', 'none')}")
print("=" * WIDTH)
print(f"  {required_count} required  |  {optional_count} optional  |  {len(plan.skipped_tasks)} skipped")
print("=" * WIDTH)
print(f"\n  {plan.explanation}")
