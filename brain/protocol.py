"""The bot<->brain contract. Mirror of bot/src/index.ts's emit()/action handler.

Keep the two sides in sync: this file is the interface, not the code around it.
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter

# --- events: bot -> brain ---


class ChatEvent(BaseModel):
    type: Literal["chat"]
    username: str
    message: str


class DeathEvent(BaseModel):
    type: Literal["death"]


Event = Annotated[Union[ChatEvent, DeathEvent], Field(discriminator="type")]
event_adapter: TypeAdapter[Event] = TypeAdapter(Event)


# --- actions: brain -> bot ---


class ChatAction(BaseModel):
    """Length and newlines are the bot's problem: actions.ts splits anything over
    Minecraft's 256-char cap across several messages."""

    action: Literal["chat"] = "chat"
    message: str


Action = ChatAction
