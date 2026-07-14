"""OpenAI access. The only module that knows a model exists."""

import logging
from collections import deque

from openai import AsyncOpenAI
from openai.types.responses import ResponseInputItemParam

log = logging.getLogger(__name__)

SYSTEM = (
    "You are a bot standing in the player's Minecraft world, talking in in-game chat. "
    "Reply in one sentence no matter what. Plain text, no markdown."
)


class BudgetExceeded(Exception):
    """Session call cap hit. Callers degrade gracefully instead of spending."""


class Chatbot:
    """Rolling-context chat. No persistent memory — that's M2's state file."""

    def __init__(self, model: str, max_calls: int, history_turns: int) -> None:
        self._client = AsyncOpenAI()
        self._model = model
        self._max_calls = max_calls
        self._history: deque[ResponseInputItemParam] = deque(maxlen=history_turns * 2)
        self.calls = 0

    async def reply(self, username: str, message: str) -> str:
        if self.calls >= self._max_calls:
            raise BudgetExceeded(f"llm budget cap reached ({self._max_calls} calls)")
        self.calls += 1

        self._history.append({"role": "user", "content": f"{username}: {message}"})
        response = await self._client.responses.create(
            model=self._model,
            instructions=SYSTEM,
            input=list(self._history),
        )
        reply = response.output_text.strip()
        self._history.append({"role": "assistant", "content": reply})

        log.info("llm call %d/%d -> %s", self.calls, self._max_calls, reply)
        return reply
