class Task:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, title: str, duration_minutes: int, priority: str, category: str, is_required: bool, notes: str):
        """Initialize a care task with its title, timing, priority, and metadata."""
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority.lower()
        self.category = category
        self.is_required = is_required
        self.notes = notes
        self.completed = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is high."""
        return self.priority == "high"

    def get_summary(self) -> str:
        """Return a formatted one-line description of the task."""
        required_label = "required" if self.is_required else "optional"
        summary = f"[{self.priority.upper()}] {self.title} ({self.duration_minutes} min, {self.category}, {required_label})"
        if self.notes:
            summary += f" — {self.notes}"
        return summary


class Pet:
    def __init__(self, name: str, species: str, age: int, special_needs: list):
        """Initialize a pet with its profile and an empty task list."""
        self.name = name
        self.species = species
        self.age = age
        self.special_needs = special_needs
        self.tasks = []

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def has_special_needs(self) -> bool:
        """Return True if this pet has any listed special needs."""
        return len(self.special_needs) > 0

    def get_task_list(self) -> list:
        """Return the full list of tasks associated with this pet."""
        return self.tasks


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: dict):
        """Initialize an owner with their time budget, preferences, and an empty pet list."""
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences
        self.pets = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_available_time(self) -> int:
        """Return the owner's total daily time budget in minutes."""
        return self.available_minutes

    def get_all_tasks(self) -> list:
        """Return a combined list of tasks across all of the owner's pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_task_list())
        return all_tasks


class DailyPlan:
    def __init__(self, scheduled_tasks: list, skipped_tasks: list, total_duration: int, explanation: str):
        """Store the results of a scheduling run, including scheduled and skipped tasks."""
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.total_duration = total_duration
        self.explanation = explanation

    def get_summary(self) -> str:
        """Return a two-line string showing scheduled and skipped task counts."""
        lines = [
            f"Scheduled: {len(self.scheduled_tasks)} tasks ({self.total_duration} min)",
            f"Skipped:   {len(self.skipped_tasks)} tasks",
        ]
        return "\n".join(lines)

    def display(self) -> None:
        """Print the full daily plan to the terminal."""
        print("=== Daily Care Plan ===")
        print(self.get_summary())
        print("\nScheduled tasks:")
        for task in self.scheduled_tasks:
            print(f"  - {task.get_summary()}")
        if self.skipped_tasks:
            print("\nSkipped tasks:")
            for task in self.skipped_tasks:
                print(f"  - {task.get_summary()}")
        print(f"\nReason: {self.explanation}")


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list):
        """Initialize the scheduler with an owner, a primary pet, and the full task list."""
        self.owner = owner
        self.pet = pet
        self.tasks = tasks
        self.remaining_minutes = owner.available_minutes

    def rank_tasks(self) -> list:
        """Sort tasks by required status, then priority level, then shortest duration."""
        return sorted(
            self.tasks,
            key=lambda t: (not t.is_required, Task.PRIORITY_ORDER.get(t.priority, 99), t.duration_minutes)
        )

    def fits_in_budget(self, task: Task) -> bool:
        """Return True if the task's duration fits within the remaining time budget."""
        return task.duration_minutes <= self.remaining_minutes

    def generate_plan(self) -> DailyPlan:
        """Build and return a DailyPlan by scheduling tasks within the owner's time budget."""
        self.remaining_minutes = self.owner.available_minutes
        scheduled = []
        skipped = []

        for task in self.rank_tasks():
            if self.fits_in_budget(task):
                scheduled.append(task)
                self.remaining_minutes -= task.duration_minutes
            else:
                skipped.append(task)

        total_duration = self.owner.available_minutes - self.remaining_minutes
        explanation = self.explain_plan_text(scheduled, skipped)
        return DailyPlan(scheduled, skipped, total_duration, explanation)

    def explain_plan(self, plan: DailyPlan) -> str:
        """Return a natural-language explanation of the scheduling decisions in a plan."""
        return self.explain_plan_text(plan.scheduled_tasks, plan.skipped_tasks)

    def explain_plan_text(self, scheduled: list, skipped: list) -> str:
        """Build an explanation string from lists of scheduled and skipped tasks."""
        parts = []
        required_scheduled = [t for t in scheduled if t.is_required]
        if required_scheduled:
            parts.append(f"{len(required_scheduled)} required task(s) were prioritized first.")
        if skipped:
            skipped_titles = ", ".join(t.title for t in skipped)
            parts.append(f"Skipped due to time constraints: {skipped_titles}.")
        else:
            parts.append("All tasks fit within the available time budget.")
        parts.append(f"{self.owner.available_minutes - self.remaining_minutes} of {self.owner.available_minutes} minutes used.")
        return " ".join(parts)
