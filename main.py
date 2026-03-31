from pawpal_system import Owner, Pet, Task, Scheduler

# --- Owner ---
owner = Owner(name="Jordan", available_minutes=90, preferences={"avoid_category": "grooming"})

# --- Pets ---
dog = Pet(name="Biscuit", species="Dog", age=4, special_needs=["joint supplement"])
cat = Pet(name="Mochi", species="Cat", age=2, special_needs=[])

# --- Tasks for Biscuit ---
dog.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    category="exercise",
    is_required=True,
    notes="Keep to flat terrain due to joint supplement"
))
dog.add_task(Task(
    title="Joint supplement",
    duration_minutes=5,
    priority="high",
    category="health",
    is_required=True,
    notes="Mix into wet food"
))
dog.add_task(Task(
    title="Brush coat",
    duration_minutes=15,
    priority="low",
    category="grooming",
    is_required=False,
    notes=""
))

# --- Tasks for Mochi ---
cat.add_task(Task(
    title="Play session",
    duration_minutes=20,
    priority="medium",
    category="enrichment",
    is_required=False,
    notes="Wand toy preferred"
))
cat.add_task(Task(
    title="Litter box cleaning",
    duration_minutes=10,
    priority="high",
    category="hygiene",
    is_required=True,
    notes=""
))

# --- Register pets with owner ---
owner.add_pet(dog)
owner.add_pet(cat)

# --- Build schedule from all tasks ---
all_tasks = owner.get_all_tasks()
scheduler = Scheduler(owner=owner, pet=dog, tasks=all_tasks)
plan = scheduler.generate_plan()

# --- Print Today's Schedule ---
def print_schedule(owner, plan):
    scheduled_set = set(id(t) for t in plan.scheduled_tasks)
    width = 40

    print("=" * width)
    print(f"        Today's Schedule — {owner.name}")
    print(f"        Budget: {owner.available_minutes} min  |  Used: {plan.total_duration} min")
    print("=" * width)

    required_count = optional_count = 0

    for pet in owner.pets:
        print(f"\n  {pet.name.upper()} ({pet.species})")
        print("  " + "─" * (width - 4))
        pet_tasks = sorted(pet.get_task_list(), key=lambda t: (not t.is_required))
        for task in pet_tasks:
            if id(task) in scheduled_set:
                marker = "[!]" if task.is_required else "   "
                print(f"  {marker} {task.title:<22} {task.duration_minutes:>3} min  {task.category}")
                if task.is_required:
                    required_count += 1
                else:
                    optional_count += 1

    if plan.skipped_tasks:
        print(f"\n  SKIPPED")
        print("  " + "─" * (width - 4))
        for task in plan.skipped_tasks:
            print(f"      {task.title:<22} {task.duration_minutes:>3} min  {task.category}")

    print(f"\n  [!] = required task\n")
    print("=" * width)
    print(f"  {required_count} required  |  {optional_count} optional  |  {len(plan.skipped_tasks)} skipped")
    print("=" * width)

print_schedule(owner, plan)
