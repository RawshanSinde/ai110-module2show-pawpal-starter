import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pawpal_system import Task, Pet


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
