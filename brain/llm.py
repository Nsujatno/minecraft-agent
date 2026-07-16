import logging
from collections import deque

from openai import AsyncOpenAI
from openai.types.responses import ResponseInputItemParam

from typing import get_args
from protocol import Action, ChatAction, Decision

log = logging.getLogger(__name__)

def _actions_doc() -> str:
    lines = []
    for model in get_args(Action):
        name = model.model_fields["action"].default
        desc = " ".join((model.__doc__ or "").split())
        lines.append(f"- {name}: {desc}")
        for fname, field in model.model_fields.items():
            if fname == "action":
                continue
            tname = getattr(field.annotation, "__name__", str(field.annotation))
            default = "" if field.is_required() else f", default {field.default}"
            lines.append(f"    {fname} ({tname}{default}): {field.description or ''}")
    return "\n".join(lines)


BASE = (
    "You are an autonomous agent controlling a character in a Minecraft world. The "
    "player gives you goals in chat. Break each goal into concrete steps and carry "
    "them out one action at a time. After each action you receive an observation with "
    "the result and your current state (position, health, inventory) — use it to decide "
    "the next step.\n"
    "Think about prerequisites before acting: obtaining something often requires tools "
    "or materials first (mining stone needs a pickaxe, which needs planks and sticks, "
    "which need wood). Only take an action once its prerequisites are met.\n"
    "You may ONLY use the actions listed below. If a goal needs something these actions "
    "cannot do, say so in chat instead of pretending. Return no action (null) when the "
    "goal is complete."
)

SYSTEM = f"{BASE}\n\nActions:\n{_actions_doc()}"


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
