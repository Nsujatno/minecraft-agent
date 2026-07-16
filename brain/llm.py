import logging
from collections import deque

from openai import AsyncOpenAI
from openai.types.responses import ResponseInputItemParam

from protocol import Action, ChatAction, Decision

log = logging.getLogger(__name__)

SYSTEM = (
    "You are a bot standing in the player's Minecraft world. You respond to in-game "
    "chat and take actions to accomplish goals. You act one step at a time: after each "
    "action you receive an observation with its result and your current state, then you "
    "decide the next action. A goto that returns ok means you have arrived — positions "
    "are approximate (within about a block), so never re-issue goto to correct small "
    "coordinate differences. When the goal is complete, return no action (null)."
    "To gather a block, call collect_block with a count and name substring: use 'log' for wood"
    " (tree trunks are oak_log, birch_log, etc.), or 'iron_ore' for iron. collect_block"
    " finds the nearest match within range and walks to it itself, so do not goto first —"
    " just call collect_block directly."
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

    async def decide(self, observation: str) -> Action | None:
        """One observation in, one action out (or None when the goal is done)."""
        if self.calls >= self._max_calls:
            raise BudgetExceeded(f"llm budget cap reached ({self._max_calls} calls)")
        self.calls += 1

        self._history.append({"role": "user", "content": observation})
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
