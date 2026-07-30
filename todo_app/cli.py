import os
import sys
from datetime import datetime

from .models import Task, TaskStatus
from .openai_service import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_SYSTEM_MESSAGE,
    DEFAULT_TEMPERATURE,
    MAX_TEMPERATURE,
    MIN_TEMPERATURE,
    MODEL,
    OpenAIService,
)
from .task_manager import TaskManager


def print_header(title: str) -> None:
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def read_line(prompt: str, *, required: bool = True, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    while True:
        value = input(f"{prompt}{suffix}: ").strip()
        if not value and default is not None:
            return default
        if value or not required:
            return value
        print("Поле обязательно для заполнения.")


def read_float(prompt: str, default: float) -> float:
    while True:
        raw = read_line(prompt, required=False, default=str(default))
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            print("Введите число, например 0.7")


def read_int(prompt: str, default: int) -> int:
    while True:
        raw = read_line(prompt, required=False, default=str(default))
        try:
            return int(raw)
        except ValueError:
            print("Введите целое число, например 500")


def read_temperature(prompt: str, default: float) -> float:
    while True:
        value = read_float(prompt, default)
        if OpenAIService.is_valid_temperature(value):
            return value
        print(f"Temperature должна быть от {MIN_TEMPERATURE} до {MAX_TEMPERATURE}")


def read_due_date() -> str | None:
    raw = read_line("Срок выполнения (ГГГГ-ММ-ДД, Enter — без срока)", required=False)
    if not raw:
        return None

    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return raw
    except ValueError:
        print("Неверный формат даты. Срок не установлен.")
        return None


def format_task(task: Task, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else ""
    status_label = "выполнена" if task.status == TaskStatus.COMPLETED else "активна"
    due = task.due_date or "не указан"
    description = task.description or "—"
    return (
        f"{prefix}[{task.id}] {task.title}\n"
        f"   Описание: {description}\n"
        f"   Срок: {due} | Статус: {status_label}"
    )


def print_tasks(tasks: list[Task]) -> None:
    if not tasks:
        print("\nЗадач не найдено.")
        return

    print()
    for index, task in enumerate(tasks, start=1):
        print(format_task(task, index))
        print("-" * 40)


def select_task(manager: TaskManager) -> Task | None:
    raw = read_line("ID задачи")
    if not raw:
        return None

    try:
        task_id = int(raw)
    except ValueError:
        print("ID должен быть числом.")
        return None

    task = manager.get(task_id)
    if task is None:
        print("Задача не найдена.")
    return task


def print_startup_config() -> None:
    print_header("Параметры OpenAI API")
    print(f"Модель (фиксирована): {MODEL}")
    print(f"Temperature: {DEFAULT_TEMPERATURE} (диапазон {MIN_TEMPERATURE}–{MAX_TEMPERATURE})")
    print(f"Max_tokens: {DEFAULT_MAX_TOKENS}")
    print(f"Системные инструкции: {DEFAULT_SYSTEM_MESSAGE}")


def init_openai_service() -> OpenAIService | None:
    print_startup_config()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\nOPENAI_API_KEY не найден в .env")
        api_key = read_line("OPENAI API Key", required=False)
        if not api_key:
            print("\nAI-помощник будет недоступен без API ключа.")
            return None

    return OpenAIService(api_key=api_key)


def read_ai_request_params(service: OpenAIService) -> None:
    temperature = read_temperature("Temperature", service.temperature)
    max_tokens = read_int("Max_tokens", service.max_tokens)

    service.temperature = temperature
    service.max_tokens = max_tokens


def send_ai_request(service: OpenAIService, user_query: str) -> None:
    notice = service.get_temperature_notice()
    if notice:
        print(f"\n{notice}")

    print("\nОтправка запроса к OpenAI...")
    try:
        answer = service.complete(user_query)
        print_header("Ответ модели")
        print(answer)
    except Exception as error:
        print(f"\nОшибка OpenAI API: {error}")


def handle_add(manager: TaskManager) -> None:
    print_header("Добавление задачи")
    title = read_line("Название")
    description = read_line("Описание", required=False)
    due_date = read_due_date()
    task = manager.add(title, description, due_date)
    print(f"\nЗадача добавлена: {task.title} [ID: {task.id}]")


def handle_list(manager: TaskManager) -> None:
    print_header("Список задач")
    print("Фильтр: 1 — все, 2 — активные, 3 — выполненные")
    choice = read_line("Выберите фильтр", required=False, default="1")

    filters = {"1": "all", "2": "active", "3": "completed"}
    status_filter = filters.get(choice, "all")
    print_tasks(manager.list_tasks(status_filter))


def handle_edit(manager: TaskManager) -> None:
    print_header("Редактирование задачи")
    task = select_task(manager)
    if task is None:
        return

    print(format_task(task))
    title = read_line("Новое название (Enter — без изменений)", required=False)
    description = read_line("Новое описание (Enter — без изменений)", required=False)
    due_raw = read_line(
        "Новый срок (ГГГГ-ММ-ДД, Enter — без изменений, '-' — удалить срок)",
        required=False,
    )

    clear_due_date = due_raw == "-"
    due_date = None
    if due_raw and due_raw != "-":
        try:
            datetime.strptime(due_raw, "%Y-%m-%d")
            due_date = due_raw
        except ValueError:
            print("Неверный формат даты. Срок не изменён.")
            due_date = None
            clear_due_date = False

    manager.update(
        task.id,
        title=title or None,
        description=description if description else None,
        due_date=due_date,
        clear_due_date=clear_due_date,
    )
    print("\nЗадача обновлена.")


def handle_status(manager: TaskManager) -> None:
    print_header("Изменение статуса")
    task = select_task(manager)
    if task is None:
        return

    print(format_task(task))
    print("1 — активная, 2 — выполненная")
    choice = read_line("Новый статус", required=False, default="1")
    status = TaskStatus.COMPLETED if choice == "2" else TaskStatus.ACTIVE
    manager.set_status(task.id, status)
    print("\nСтатус обновлён.")


def handle_delete(manager: TaskManager) -> None:
    print_header("Удаление задачи")
    task = select_task(manager)
    if task is None:
        return

    confirm = read_line(f"Удалить «{task.title}»? (y/n)", required=False, default="n")
    if confirm.lower() in {"y", "yes", "д", "да"}:
        manager.delete(task.id)
        print("\nЗадача удалена.")
    else:
        print("\nУдаление отменено.")


def handle_ai_assist(service: OpenAIService | None, manager: TaskManager) -> None:
    if service is None:
        print("\nOpenAI не настроен. Укажите API ключ в .env или при запуске.")
        return

    print_header("Запрос к AI-помощнику")
    read_ai_request_params(service)

    query = read_line("Запрос для модели")
    if not query:
        return

    tasks = manager.list_tasks("all")
    context = "\n".join(
        f"- {task.title}: {task.description or 'без описания'}, "
        f"срок {task.due_date or 'не указан'}, статус {task.status.value}"
        for task in tasks
    ) or "Список задач пуст."

    enriched_query = f"{query}\n\nТекущие задачи пользователя:\n{context}"
    send_ai_request(service, enriched_query)


def print_menu() -> None:
    print_header("To-Do List")
    print("1. Добавить задачу")
    print("2. Показать задачи")
    print("3. Редактировать задачу")
    print("4. Изменить статус")
    print("5. Удалить задачу")
    print("6. Спросить AI-помощника")
    print("0. Выход")


def run() -> None:
    print_header("Создание и управление списком задач")
    service = init_openai_service()
    manager = TaskManager()

    try:
        while True:
            print_menu()
            choice = read_line("Выберите действие", required=False, default="0")

            actions = {
                "1": lambda: handle_add(manager),
                "2": lambda: handle_list(manager),
                "3": lambda: handle_edit(manager),
                "4": lambda: handle_status(manager),
                "5": lambda: handle_delete(manager),
                "6": lambda: handle_ai_assist(service, manager),
                "0": lambda: sys.exit(0),
            }

            action = actions.get(choice)
            if action is None:
                print("\nНеизвестная команда.")
                continue

            action()
    except KeyboardInterrupt:
        print("\n\nВыход из приложения.")
        sys.exit(0)


if __name__ == "__main__":
    run()
