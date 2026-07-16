"""The bot<->brain contract. Mirror of bot/src/index.ts's emit()/action handler.

Keep the two sides in sync: this file is the interface, not the code around it.
"""

from typing import Literal, Union

from pydantic import BaseModel, TypeAdapter

# --- events: bot -> brain ---


class ChatEvent(BaseModel):
    type: Literal["chat"]
    username: str
    message: str


class DeathEvent(BaseModel):
    type: Literal["death"]


class ActionResult(BaseModel):
    """Result of an executed action, fed back so the agent can decide the next
    step. Carries self-state so it doubles as perception."""

    type: Literal["action_result"]
    action: str
    ok: bool
    error: str | None = None
    x: float
    y: float
    z: float
    health: float
    food: float


Event = Union[ChatEvent, DeathEvent, ActionResult]
event_adapter: TypeAdapter[Event] = TypeAdapter(Event)


# --- actions: brain -> bot ---


class ChatAction(BaseModel):
    """Length and newlines are the bot's problem: actions.ts splits anything over
    Minecraft's 256-char cap across several messages."""

    action: Literal["chat"] = "chat"
    message: str


class GotoAction(BaseModel):
    action: Literal["goto"] = "goto"
    x: int
    y: int
    z: int


Action = Union[ChatAction, GotoAction]


# LLM structured output
class Decision(BaseModel):
    action: Action | None  # None = goal complete, stop the loop
    reason: str
