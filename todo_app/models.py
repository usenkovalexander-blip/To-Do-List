from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class Task:
    title: str
    description: str = ""
    due_date: str | None = None
    status: TaskStatus = TaskStatus.ACTIVE
    id: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        raw_id = data.get("id", 0)
        if isinstance(raw_id, int):
            task_id = raw_id
        elif isinstance(raw_id, str) and raw_id.isdigit():
            task_id = int(raw_id)
        else:
            task_id = 0

        return cls(
            id=task_id,
            title=data["title"],
            description=data.get("description", ""),
            due_date=data.get("due_date"),
            status=TaskStatus(data.get("status", TaskStatus.ACTIVE.value)),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )
