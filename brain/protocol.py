"""The bot<->brain contract. Mirror of bot/src/index.ts's emit()/action handler.

Keep the two sides in sync: this file is the interface, not the code around it.
"""

from typing import Literal, Union

from pydantic import BaseModel, TypeAdapter, Field

# --- events: bot -> brain ---


class ChatEvent(BaseModel):
    type: Literal["chat"]
    username: str
    message: str
    x: float
    y: float
    z: float
    health: float
    food: float
    inventory: dict[str, int]


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
    inventory: dict[str, int]


Event = Union[ChatEvent, DeathEvent, ActionResult]
event_adapter: TypeAdapter[Event] = TypeAdapter(Event)


# --- actions: brain -> bot ---


class ChatAction(BaseModel):
    """Say something to the player in in-game chat."""

    action: Literal["chat"] = "chat"
    message: str


class GotoAction(BaseModel):
    """Walk to approximately (x, y, z). Arriving within about a block is success."""
    action: Literal["goto"] = "goto"
    x: int
    y: int
    z: int


class CollectBlockAction(BaseModel):
    """Mine up to `count` of the nearest blocks whose name contains `name`.
    Finds and walks to each block automatically — do NOT goto first."""
    action: Literal["collect_block"] = "collect_block"
    name: str = Field(description="block-name substring, e.g. 'log' for wood, 'iron_ore' for iron")
    count: int = 1


Action = Union[ChatAction, GotoAction, CollectBlockAction]


# LLM structured output
class Decision(BaseModel):
    action: Action | None  # None = goal complete, stop the loop
    reason: str
