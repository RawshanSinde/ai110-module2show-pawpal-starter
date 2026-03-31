from collections import defaultdict

TIME_OF_DAY_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, None: 3}

# Reasonable per-slot caps (minutes). Used only for conflict detection.
SLOT_CAPACITY_MINUTES = {"morning": 120, "afternoon": 180, "evening": 90}


class Task:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str,
        category: str,
        is_required: bool,
        notes: str,
        time_of_day: str = None,
        recurrence: str = "one-time",
        recurrence_days: list = None,
    ):
        """Initialize a care task with timing, priority, slot, and recurrence metadata."""
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority.lower()
        self.category = category
        self.is_required = is_required
        self.notes = notes
        self.completed = False
        self.time_of_day = time_of_day          # "morning" | "afternoon" | "evening" | None
        self.recurrence = recurrence            # "one-time" | "daily" | "weekly"
        self.recurrence_days = [d.lower() for d in (recurrence_days or [])]
        self.pet = None                         # set by Pet.add_task()

    def is_active_today(self, day_of_week: str = None) -> bool:
        """Return True if this task should appear in today's schedule.

        Rules by recurrence type:
          - "one-time": active only if not yet completed.
          - "daily":    always active.
          - "weekly":   active when ``day_of_week`` matches one of
                        ``recurrence_days`` (case-insensitive). If no day is
                        provided the task is treated as active to avoid
                        silently dropping it.
        """
        if self.recurrence == "one-time":
            return not self.completed
        if self.recurrence == "daily":
            return True
        if self.recurrence == "weekly" and day_of_week:
            return day_of_week.lower() in self.recurrence_days
        return True

    def mark_complete(self) -> None:
        """Mark this task as completed.

        For recurring tasks (daily or weekly), automatically registers a fresh
        copy on the same pet so the next occurrence is ready to schedule.
        The completed original is kept in the task list as a history record.
        """
        self.completed = True
        if self.recurrence in ("daily", "weekly") and self.pet is not None:
            next_occurrence = Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                category=self.category,
                is_required=self.is_required,
                notes=self.notes,
                time_of_day=self.time_of_day,
                recurrence=self.recurrence,
                recurrence_days=list(self.recurrence_days),
            )
            self.pet.add_task(next_occurrence)

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is high."""
        return self.priority == "high"

    def get_summary(self) -> str:
        """Return a formatted one-line description of the task."""
        required_label = "required" if self.is_required else "optional"
        slot = f", {self.time_of_day}" if self.time_of_day else ""
        recur = f", {self.recurrence}" if self.recurrence != "one-time" else ""
        summary = f"[{self.priority.upper()}] {self.title} ({self.duration_minutes} min, {self.category}{slot}{recur}, {required_label})"
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
        """Append a task to this pet's task list and record the pet reference on the task."""
        task.pet = self
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
    def __init__(
        self,
        scheduled_tasks: list,
        skipped_tasks: list,
        total_duration: int,
        explanation: str,
        conflicts: list = None,
    ):
        """Store the results of a scheduling run, including scheduled/skipped tasks and conflicts."""
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.total_duration = total_duration
        self.explanation = explanation
        self.conflicts = conflicts or []

    def get_summary(self) -> str:
        """Return a multi-line string showing scheduled, skipped, and conflict counts."""
        lines = [
            f"Scheduled: {len(self.scheduled_tasks)} tasks ({self.total_duration} min)",
            f"Skipped:   {len(self.skipped_tasks)} tasks",
        ]
        if self.conflicts:
            lines.append(f"Conflicts: {len(self.conflicts)}")
        return "\n".join(lines)

    def display(self) -> None:
        """Print the full daily plan to the terminal."""
        print("=== Daily Care Plan ===")
        print(self.get_summary())
        if self.conflicts:
            print("\nConflicts detected:")
            for c in self.conflicts:
                print(f"  ! {c}")
        print("\nScheduled tasks:")
        for task in self.scheduled_tasks:
            print(f"  - {task.get_summary()}")
        if self.skipped_tasks:
            print("\nSkipped tasks:")
            for task in self.skipped_tasks:
                print(f"  - {task.get_summary()}")
        print(f"\nReason: {self.explanation}")


class Scheduler:
    def __init__(self, owner: Owner, tasks: list):
        """Initialize the scheduler with an owner and the full task list."""
        self.owner = owner
        self.tasks = tasks
        self.remaining_minutes = owner.available_minutes

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_by_status(self, tasks: list, include_completed: bool = False) -> list:
        """Return tasks filtered by completion status.

        By default only incomplete tasks are returned.  Pass
        ``include_completed=True`` to include tasks that have already been
        marked done (e.g. to build a history view).
        """
        if include_completed:
            return list(tasks)
        return [t for t in tasks if not t.completed]

    def filter_by_pet(self, tasks: list, pet_name: str) -> list:
        """Return only the tasks that belong to the pet with the given name.

        Comparison is case-insensitive so "biscuit" matches "Biscuit".
        Tasks whose ``pet`` backref is unset are always excluded.
        """
        name = pet_name.lower()
        return [t for t in tasks if t.pet is not None and t.pet.name.lower() == name]

    def filter_tasks(
        self,
        day_of_week: str = None,
        pet: Pet = None,
        include_completed: bool = False,
    ) -> list:
        """
        Return tasks that are active today, optionally narrowed by pet and
        completion status. Soft-drops avoided-category tasks unless required.

        Delegates completion and pet filtering to filter_by_status /
        filter_by_pet so both entry-points stay consistent.
        """
        tasks = self.filter_by_status(self.tasks, include_completed)
        if pet is not None:
            tasks = self.filter_by_pet(tasks, pet.name)
        avoid = self.owner.preferences.get("avoid_category", "").lower()
        result = []
        for task in tasks:
            if not task.is_active_today(day_of_week):
                continue
            if avoid and task.category.lower() == avoid and not task.is_required:
                continue
            result.append(task)
        return result

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def sort_by_time(self, tasks: list) -> list:
        """Sort tasks by time_of_day slot only (morning → afternoon → evening → unslotted).

        Tasks sharing the same slot keep their original relative order (stable sort).
        Use this when you need a pure chronological view without priority or required-status
        mixed into the ordering.
        """
        return sorted(tasks, key=lambda t: TIME_OF_DAY_ORDER.get(t.time_of_day, 3))

    def rank_tasks(self, tasks: list) -> list:
        """Return tasks sorted by the full scheduling priority order.

        Sort key (most- to least-significant):
          1. Time slot  — morning before afternoon before evening before unslotted.
          2. Required   — required tasks before optional ones within the same slot.
          3. Priority   — high before medium before low.
          4. Duration   — shorter tasks first when everything else ties, maximising
                          the number of tasks that fit in the remaining budget.

        This ordering is used by ``generate_plan`` to decide which tasks get
        scheduled first when the owner's time budget is limited.
        """
        return sorted(
            tasks,
            key=lambda t: (
                TIME_OF_DAY_ORDER.get(t.time_of_day, 3),
                not t.is_required,
                Task.PRIORITY_ORDER.get(t.priority, 99),
                t.duration_minutes,
            ),
        )

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, tasks: list) -> list:
        """
        Return a list of human-readable conflict descriptions.

        Checks:
          1. Required tasks whose total duration exceeds the time budget.
          2. Per-slot overruns against SLOT_CAPACITY_MINUTES caps.
          3. Duplicate task titles for the same pet.
          4. Time conflicts: tasks scheduled in the same slot that would
             require simultaneous execution (delegates to detect_time_conflicts).
        """
        conflicts = []

        # 1. Required tasks exceed total budget
        required_total = sum(t.duration_minutes for t in tasks if t.is_required)
        if required_total > self.owner.available_minutes:
            conflicts.append(
                f"Required tasks total {required_total} min but budget is only "
                f"{self.owner.available_minutes} min — some required tasks will be skipped."
            )

        # 2. Per-slot capacity overrun
        for slot, cap in SLOT_CAPACITY_MINUTES.items():
            slot_tasks = [t for t in tasks if t.time_of_day == slot]
            slot_total = sum(t.duration_minutes for t in slot_tasks)
            if slot_total > cap:
                conflicts.append(
                    f"Slot conflict in '{slot}': {slot_total} min assigned "
                    f"but slot capacity is {cap} min."
                )

        # 3. Duplicate task titles per pet
        seen = set()
        for task in tasks:
            pet_name = task.pet.name if task.pet else "unknown"
            key = (pet_name, task.title.lower())
            if key in seen:
                conflicts.append(
                    f"Duplicate task '{task.title}' found for {pet_name}."
                )
            else:
                seen.add(key)

        # 4. Same-slot time conflicts
        conflicts.extend(self.detect_time_conflicts(tasks))

        return conflicts

    def detect_time_conflicts(self, tasks: list) -> list:
        """
        Lightweight same-slot conflict detection. Never raises — always returns
        a (possibly empty) list of warning strings.

        Two conflict patterns are checked per named slot:

        a) Same-pet overlap: a single pet has more than one task in the slot.
           An animal cannot physically be in two activities simultaneously.

        b) Cross-pet required overlap: multiple pets each have at least one
           required task in the same slot. The owner cannot attend to two
           animals' required needs at the exact same time.
        """
        warnings = []

        # Group tasks by slot, skip unslotted (None) tasks — no overlap possible
        by_slot = defaultdict(list)
        for task in tasks:
            if task.time_of_day is not None:
                by_slot[task.time_of_day].append(task)

        for slot, slot_tasks in by_slot.items():

            # a) Same-pet overlap
            by_pet = defaultdict(list)
            for task in slot_tasks:
                pet_name = task.pet.name if task.pet else "unknown"
                by_pet[pet_name].append(task)

            for pet_name, pet_tasks in by_pet.items():
                if len(pet_tasks) > 1:
                    titles = " and ".join(f"'{t.title}'" for t in pet_tasks)
                    warnings.append(
                        f"WARNING [{slot}] Same-pet overlap for {pet_name}: "
                        f"{titles} are both scheduled at the same time."
                    )

            # b) Cross-pet required overlap
            pets_with_required = [
                pet_name
                for pet_name, pet_tasks in by_pet.items()
                if any(t.is_required for t in pet_tasks)
            ]
            if len(pets_with_required) > 1:
                pet_list = " and ".join(sorted(pets_with_required))
                warnings.append(
                    f"WARNING [{slot}] Cross-pet required overlap: "
                    f"{pet_list} both have required tasks at the same time."
                )

        return warnings

    # ------------------------------------------------------------------
    # Budget helpers
    # ------------------------------------------------------------------

    def fits_in_budget(self, task: Task) -> bool:
        """Return True if the task's duration fits within the remaining time budget."""
        return task.duration_minutes <= self.remaining_minutes

    # ------------------------------------------------------------------
    # Plan generation
    # ------------------------------------------------------------------

    def generate_plan(self, day_of_week: str = None) -> DailyPlan:
        """
        Build and return a DailyPlan for the given day.

        Steps:
          1. Filter tasks (recurrence, completion, preferences).
          2. Detect conflicts on the filtered set.
          3. Greedy schedule in ranked order (slot → required → priority → duration).
          4. Second pass: fill leftover budget with any tasks that now fit.
        """
        self.remaining_minutes = self.owner.available_minutes

        active_tasks = self.filter_tasks(day_of_week=day_of_week)
        conflicts = self.detect_conflicts(active_tasks)
        ranked = self.rank_tasks(active_tasks)

        scheduled = []
        skipped = []
        for task in ranked:
            if self.fits_in_budget(task):
                scheduled.append(task)
                self.remaining_minutes -= task.duration_minutes
            else:
                skipped.append(task)

        # Second pass: fill remaining budget with skipped tasks that now fit
        still_skipped = []
        for task in skipped:
            if self.fits_in_budget(task):
                scheduled.append(task)
                self.remaining_minutes -= task.duration_minutes
            else:
                still_skipped.append(task)

        total_duration = self.owner.available_minutes - self.remaining_minutes
        explanation = self._build_explanation(scheduled, still_skipped)
        return DailyPlan(scheduled, still_skipped, total_duration, explanation, conflicts)

    def explain_plan(self, plan: DailyPlan) -> str:
        """Return a natural-language explanation of the scheduling decisions in a plan."""
        return self._build_explanation(plan.scheduled_tasks, plan.skipped_tasks)

    def _build_explanation(self, scheduled: list, skipped: list) -> str:
        """Build a plain-English explanation of the scheduling outcome.

        Describes how many required tasks were prioritised, names each skipped
        task along with its duration and the minutes left when it was dropped,
        and closes with a minutes-used summary. Used by both ``generate_plan``
        and ``explain_plan`` so the wording is always consistent.
        """
        parts = []
        required_scheduled = [t for t in scheduled if t.is_required]
        if required_scheduled:
            parts.append(f"{len(required_scheduled)} required task(s) prioritized.")
        if skipped:
            detail = ", ".join(
                f"{t.title} ({t.duration_minutes} min)" for t in skipped
            )
            parts.append(
                f"Skipped due to time constraints "
                f"({self.remaining_minutes} min left): {detail}."
            )
        else:
            parts.append("All tasks fit within the available time budget.")
        used = self.owner.available_minutes - self.remaining_minutes
        parts.append(f"{used} of {self.owner.available_minutes} minutes used.")
        return " ".join(parts)
