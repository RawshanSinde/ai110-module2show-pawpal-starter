import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pawpal_system import Task, Pet, Owner, Scheduler


def make_task(title="Test Task", duration=10, priority="medium"):
    return Task(
        title=title,
        duration_minutes=duration,
        priority=priority,
        category="health",
        is_required=False,
        notes=""
    )


# --- Task Completion ---

def test_task_starts_incomplete():
    task = make_task()
    assert task.completed == False

def test_mark_complete_changes_status():
    task = make_task()
    task.mark_complete()
    assert task.completed == True

def test_mark_complete_is_idempotent():
    task = make_task()
    task.mark_complete()
    task.mark_complete()
    assert task.completed == True


# --- Task Addition ---

def test_new_pet_has_no_tasks():
    pet = Pet(name="Biscuit", species="Dog", age=3, special_needs=[])
    assert len(pet.get_task_list()) == 0

def test_adding_one_task_increases_count():
    pet = Pet(name="Biscuit", species="Dog", age=3, special_needs=[])
    pet.add_task(make_task())
    assert len(pet.get_task_list()) == 1

def test_adding_multiple_tasks_increases_count():
    pet = Pet(name="Biscuit", species="Dog", age=3, special_needs=[])
    pet.add_task(make_task("Walk"))
    pet.add_task(make_task("Feed"))
    pet.add_task(make_task("Groom"))
    assert len(pet.get_task_list()) == 3

def test_added_task_is_retrievable():
    pet = Pet(name="Biscuit", species="Dog", age=3, special_needs=[])
    task = make_task("Morning walk")
    pet.add_task(task)
    assert pet.get_task_list()[0].title == "Morning walk"


# --- Helpers for Scheduler tests ---

def make_slotted_task(title, slot, duration=10, priority="medium", required=False):
    return Task(
        title=title,
        duration_minutes=duration,
        priority=priority,
        category="health",
        is_required=required,
        notes="",
        time_of_day=slot,
    )

def make_scheduler(tasks, available_minutes=480):
    owner = Owner(name="Alex", available_minutes=available_minutes, preferences={})
    return Scheduler(owner=owner, tasks=tasks)


# --- Sorting Correctness ---

def test_sort_morning_before_afternoon_before_evening():
    tasks = [
        make_slotted_task("Evening med", "evening"),
        make_slotted_task("Afternoon walk", "afternoon"),
        make_slotted_task("Morning feed", "morning"),
    ]
    result = make_scheduler(tasks).sort_by_time(tasks)
    slots = [t.time_of_day for t in result]
    assert slots == ["morning", "afternoon", "evening"]

def test_sort_unslotted_tasks_come_last():
    tasks = [
        make_slotted_task("No slot", None),
        make_slotted_task("Morning feed", "morning"),
        make_slotted_task("Evening med", "evening"),
    ]
    result = make_scheduler(tasks).sort_by_time(tasks)
    assert result[-1].time_of_day is None

def test_sort_same_slot_preserves_original_order():
    tasks = [
        make_slotted_task("First morning", "morning"),
        make_slotted_task("Second morning", "morning"),
        make_slotted_task("Third morning", "morning"),
    ]
    result = make_scheduler(tasks).sort_by_time(tasks)
    assert [t.title for t in result] == ["First morning", "Second morning", "Third morning"]

def test_sort_already_ordered_is_unchanged():
    tasks = [
        make_slotted_task("Feed", "morning"),
        make_slotted_task("Walk", "afternoon"),
        make_slotted_task("Meds", "evening"),
        make_slotted_task("Misc", None),
    ]
    result = make_scheduler(tasks).sort_by_time(tasks)
    assert [t.time_of_day for t in result] == ["morning", "afternoon", "evening", None]

def test_sort_single_task_returns_single_task():
    tasks = [make_slotted_task("Only task", "afternoon")]
    result = make_scheduler(tasks).sort_by_time(tasks)
    assert len(result) == 1
    assert result[0].title == "Only task"


# --- Recurrence Logic ---

def make_recurring_task(title="Daily Feed", recurrence="daily", days=None):
    return Task(
        title=title,
        duration_minutes=10,
        priority="medium",
        category="feeding",
        is_required=True,
        notes="",
        recurrence=recurrence,
        recurrence_days=days or [],
    )

def test_completing_daily_task_adds_new_task_to_pet():
    pet = Pet(name="Biscuit", species="Dog", age=3, special_needs=[])
    task = make_recurring_task()
    pet.add_task(task)
    task.mark_complete()
    assert len(pet.get_task_list()) == 2

def test_completing_daily_task_new_copy_is_incomplete():
    pet = Pet(name="Biscuit", species="Dog", age=3, special_needs=[])
    task = make_recurring_task()
    pet.add_task(task)
    task.mark_complete()
    new_task = pet.get_task_list()[1]
    assert new_task.completed == False

def test_completing_daily_task_original_stays_complete():
    pet = Pet(name="Biscuit", species="Dog", age=3, special_needs=[])
    task = make_recurring_task()
    pet.add_task(task)
    task.mark_complete()
    assert pet.get_task_list()[0].completed == True

def test_completing_daily_task_new_copy_preserves_title():
    pet = Pet(name="Biscuit", species="Dog", age=3, special_needs=[])
    task = make_recurring_task("Morning Feed")
    pet.add_task(task)
    task.mark_complete()
    assert pet.get_task_list()[1].title == "Morning Feed"

def test_completing_one_time_task_does_not_add_new_task():
    pet = Pet(name="Biscuit", species="Dog", age=3, special_needs=[])
    task = make_recurring_task(recurrence="one-time")
    pet.add_task(task)
    task.mark_complete()
    assert len(pet.get_task_list()) == 1

def test_completing_daily_task_without_pet_does_not_raise():
    task = make_recurring_task()
    # pet is not set — should silently no-op, not raise
    task.mark_complete()
    assert task.completed == True


# --- Conflict Detection: Duplicate Slot ---

def make_pet_with_tasks(pet_name, task_specs):
    """task_specs: list of (title, slot, required)"""
    pet = Pet(name=pet_name, species="Dog", age=3, special_needs=[])
    tasks = []
    for title, slot, required in task_specs:
        t = Task(
            title=title,
            duration_minutes=10,
            priority="medium",
            category="health",
            is_required=required,
            notes="",
            time_of_day=slot,
        )
        pet.add_task(t)
        tasks.append(t)
    return pet, tasks

def test_same_pet_two_tasks_same_slot_flagged():
    _, tasks = make_pet_with_tasks("Biscuit", [
        ("Walk", "morning", False),
        ("Feed", "morning", False),
    ])
    scheduler = make_scheduler(tasks)
    conflicts = scheduler.detect_time_conflicts(tasks)
    assert any("Same-pet overlap" in c and "Biscuit" in c for c in conflicts)

def test_same_pet_tasks_different_slots_not_flagged():
    _, tasks = make_pet_with_tasks("Biscuit", [
        ("Walk", "morning", False),
        ("Feed", "afternoon", False),
    ])
    scheduler = make_scheduler(tasks)
    conflicts = scheduler.detect_time_conflicts(tasks)
    assert not any("Same-pet overlap" in c for c in conflicts)

def test_cross_pet_required_same_slot_flagged():
    _, tasks1 = make_pet_with_tasks("Biscuit", [("Feed", "morning", True)])
    _, tasks2 = make_pet_with_tasks("Mittens", [("Meds", "morning", True)])
    all_tasks = tasks1 + tasks2
    scheduler = make_scheduler(all_tasks)
    conflicts = scheduler.detect_time_conflicts(all_tasks)
    assert any("Cross-pet required overlap" in c for c in conflicts)

def test_cross_pet_optional_same_slot_not_flagged():
    _, tasks1 = make_pet_with_tasks("Biscuit", [("Walk", "morning", False)])
    _, tasks2 = make_pet_with_tasks("Mittens", [("Play", "morning", False)])
    all_tasks = tasks1 + tasks2
    scheduler = make_scheduler(all_tasks)
    conflicts = scheduler.detect_time_conflicts(all_tasks)
    assert not any("Cross-pet required overlap" in c for c in conflicts)

def test_unslotted_tasks_never_flagged_as_conflicts():
    _, tasks = make_pet_with_tasks("Biscuit", [
        ("Task A", None, True),
        ("Task B", None, True),
    ])
    scheduler = make_scheduler(tasks)
    conflicts = scheduler.detect_time_conflicts(tasks)
    assert conflicts == []
