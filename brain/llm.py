import logging
from collections import deque

from openai import AsyncOpenAI
from openai.types.responses import ResponseInputItemParam

from protocol import Action, ChatAction, Decision

log = logging.getLogger(__name__)

SYSTEM = (
    "You are a bot standing in the player's Minecraft world, you can "
    "respond to in-game chat messages and take actions in the world. Act accordingly."
)


class BudgetExceeded(Exception):
    """Session call cap hit. Callers degrade gracefully instead of spending."""


class Chatbot:
    """Rolling-context chat."""

    def __init__(self, model: str, max_calls: int, history_turns: int) -> None:
        self._client = AsyncOpenAI()
        self._model = model
        self._max_calls = max_calls
        self._history: deque[ResponseInputItemParam] = deque(maxlen=history_turns * 2)
        self.calls = 0

    async def decide(self, username: str, message: str) -> Action:
        if self.calls >= self._max_calls:
            raise BudgetExceeded(f"llm budget cap reached ({self._max_calls} calls)")
        self.calls += 1

        self._history.append({"role": "user", "content": f"{username}: {message}"})
        response = await self._client.responses.parse(
            text_format=Decision,
            model=self._model,
            instructions=SYSTEM,
            input=list(self._history),
        )
        decision = response.output_parsed
        if not decision:
            return ChatAction(message="LLM failed to generate a response")

        self._history.append({"role": "assistant", "content": decision.model_dump_json()})

        log.info("llm call %d/%d -> %s", self.calls, self._max_calls, decision.model_dump_json())
        
        return decision.action
