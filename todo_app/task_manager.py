from .models import Task, TaskStatus
from .storage import TaskStorage


class TaskManager:
    def __init__(self, storage: TaskStorage | None = None) -> None:
        self.storage = storage or TaskStorage()
        self.tasks = self.storage.load()
        self._migrate_legacy_ids()

    def _migrate_legacy_ids(self) -> None:
        if not any(task.id == 0 for task in self.tasks):
            return

        for index, task in enumerate(self.tasks, start=1):
            task.id = index
        self._persist()

    def _next_id(self) -> int:
        if not self.tasks:
            return 1
        return max(task.id for task in self.tasks) + 1

    def _persist(self) -> None:
        self.storage.save(self.tasks)

    def add(self, title: str, description: str = "", due_date: str | None = None) -> Task:
        task = Task(
            id=self._next_id(),
            title=title,
            description=description,
            due_date=due_date,
        )
        self.tasks.append(task)
        self._persist()
        return task

    def get(self, task_id: int) -> Task | None:
        return next((task for task in self.tasks if task.id == task_id), None)

    def update(
        self,
        task_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        clear_due_date: bool = False,
    ) -> Task | None:
        task = self.get(task_id)
        if task is None:
            return None

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if clear_due_date:
            task.due_date = None
        elif due_date is not None:
            task.due_date = due_date

        self._persist()
        return task

    def set_status(self, task_id: int, status: TaskStatus) -> Task | None:
        task = self.get(task_id)
        if task is None:
            return None

        task.status = status
        self._persist()
        return task

    def delete(self, task_id: int) -> bool:
        task = self.get(task_id)
        if task is None:
            return False

        self.tasks.remove(task)
        self._persist()
        return True

    def list_tasks(self, status_filter: str = "all") -> list[Task]:
        if status_filter == "all":
            return list(self.tasks)
        if status_filter == "active":
            return [task for task in self.tasks if task.status == TaskStatus.ACTIVE]
        if status_filter == "completed":
            return [task for task in self.tasks if task.status == TaskStatus.COMPLETED]
        return list(self.tasks)
