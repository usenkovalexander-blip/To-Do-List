import json
from pathlib import Path

from .models import Task

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TASKS_FILE = DATA_DIR / "tasks.json"


class TaskStorage:
    def __init__(self, file_path: Path = TASKS_FILE) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[Task]:
        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        return [Task.from_dict(item) for item in raw]

    def save(self, tasks: list[Task]) -> None:
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump([task.to_dict() for task in tasks], file, ensure_ascii=False, indent=2)
