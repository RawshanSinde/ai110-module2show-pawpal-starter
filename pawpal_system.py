class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: dict):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences

    def add_pet(self, pet) -> None:
        pass

    def get_available_time(self) -> int:
        pass


class Pet:
    def __init__(self, name: str, species: str, age: int, special_needs: list):
        self.name = name
        self.species = species
        self.age = age
        self.special_needs = special_needs

    def has_special_needs(self) -> bool:
        pass

    def get_task_list(self) -> list:
        pass


class Task:
    def __init__(self, title: str, duration_minutes: int, priority: str, category: str, is_required: bool, notes: str):
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.category = category
        self.is_required = is_required
        self.notes = notes

    def is_high_priority(self) -> bool:
        pass

    def get_summary(self) -> str:
        pass


class DailyPlan:
    def __init__(self, scheduled_tasks: list, skipped_tasks: list, total_duration: int, explanation: str):
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.total_duration = total_duration
        self.explanation = explanation

    def get_summary(self) -> str:
        pass

    def display(self) -> None:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list, available_minutes: int):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks
        self.available_minutes = available_minutes

    def rank_tasks(self) -> list:
        pass

    def fits_in_budget(self, task: Task) -> bool:
        pass

    def generate_plan(self) -> DailyPlan:
        pass

    def explain_plan(self, plan: DailyPlan) -> str:
        pass
