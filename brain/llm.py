import logging
from collections import deque
from pathlib import Path

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
    "goal is complete.\n"
    "Set `note` when you learn a durable fact you'd want on your next life — a recipe you "
    "had to look up, an assumption that turned out wrong, where something is. Keep it one "
    "short line. Leave it null for anything that expires (your inventory, your position, "
    "what you're doing right now) or that you already know from your notes."
)

SYSTEM = f"{BASE}\n\nActions:\n{_actions_doc()}"

MEMORY_FILE = Path(__file__).parent.parent / "state" / "memory.txt"
MAX_NOTES = 50  # oldest first eviction


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
        self._notes: deque[str] = deque(
            MEMORY_FILE.read_text(encoding="utf-8").splitlines() if MEMORY_FILE.exists() else [],
            maxlen=MAX_NOTES,
        )

    def _remember(self, note: str) -> None:
        note = " ".join(note.split())
        if not note or note in self._notes:
            return
        self._notes.append(note)
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text("\n".join(self._notes), encoding="utf-8")
        log.info("noted: %s", note)

    async def decide(self, observation: str) -> Action | None:
        """One observation in, one action out (or None when the goal is done)."""
        if self.calls >= self._max_calls:
            raise BudgetExceeded(f"llm budget cap reached ({self._max_calls} calls)")
        self.calls += 1

        notes = "\n".join(f"- {n}" for n in self._notes)
        self._history.append({"role": "user", "content": observation})
        response = await self._client.responses.parse(
            text_format=Decision,
            model=self._model,
            instructions=f"{SYSTEM}\n\nYour notes (facts you learned earlier):\n{notes}" if notes else SYSTEM,
            input=list(self._history),
        )
        decision = response.output_parsed
        if not decision:
            return ChatAction(message="LLM failed to generate a response")

        if decision.note:
            self._remember(decision.note)
        self._history.append({"role": "assistant", "content": decision.model_dump_json()})

        u = response.usage
        log.info("llm call %d/%d [tokens in=%s out=%s total=%s] -> %s",
                 self.calls, self._max_calls,
                 u and u.input_tokens, u and u.output_tokens, u and u.total_tokens,
                 decision.model_dump_json())

        return decision.action
