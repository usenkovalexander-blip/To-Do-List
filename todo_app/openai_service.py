import os

from openai import OpenAI

MODEL = "gpt-5-mini"
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 1.0
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 500
DEFAULT_SYSTEM_MESSAGE = (
    "Ты — помощник для приложения управления задачами. "
    "Отвечай кратко, по делу и на русском языке."
)


class OpenAIService:
    def __init__(
        self,
        *,
        model: str = MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_message = system_message
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    @staticmethod
    def is_valid_temperature(value: float) -> bool:
        return MIN_TEMPERATURE <= value <= MAX_TEMPERATURE

    def get_temperature_notice(self) -> str | None:
        if self.model.startswith("gpt-5") and self.temperature != 1.0:
            return (
                f"Модель {self.model} в OpenAI API принимает только temperature=1. "
                f"Запрос отправлен с temperature=1 (введено: {self.temperature})."
            )
        return None

    def complete(self, user_query: str) -> str:
        request_kwargs: dict = {
            "model": self.model,
            "max_completion_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user_query},
            ],
        }

        if not self.model.startswith("gpt-5") or self.temperature == 1.0:
            request_kwargs["temperature"] = self.temperature

        response = self.client.chat.completions.create(**request_kwargs)
        return response.choices[0].message.content or ""
