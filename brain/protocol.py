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
    held: str | None
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
    held: str | None
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


class CraftAction(BaseModel):
    """Craft `count` of item `name`. Handles the crafting table for you: 2x2 recipes are
    made in inventory, and for 3x3 recipes it uses a nearby table or places one from your
    inventory automatically — never equip or place a table yourself. You must already have
    the ingredients — check inventory first."""
    action: Literal["craft"] = "craft"
    name: str = Field(description="exact item name, e.g. 'stick', 'crafting_table', 'wooden_pickaxe'")
    count: int = 1


class EquipAction(BaseModel):
    """Hold an item from your inventory in your main hand. Mining already equips the
    best tool by itself — use this only when you want to hold something specific."""
    action: Literal["equip"] = "equip"
    name: str = Field(description="exact item name as it appears in your inventory, e.g. 'wooden_pickaxe'")


Action = Union[ChatAction, GotoAction, CollectBlockAction, CraftAction, EquipAction]


# LLM structured output
class Decision(BaseModel):
    action: Action | None  # None = goal complete, stop the loop
    reason: str
    note: str | None  # facts worth remembering next session; None = nothing new
