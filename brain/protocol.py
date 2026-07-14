"""The bot<->brain contract. Mirror of bot/src/index.ts's emit()/action handler.

Keep the two sides in sync: this file is the interface, not the code around it.
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter, field_validator

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
    action: Literal["chat"] = "chat"
    message: str

    @field_validator("message")
    @classmethod
    def single_line(cls, v: str) -> str:
        """Minecraft chat is one line. (It also caps at 256 chars — the model is
        prompted to stay short rather than truncated here.)"""
        return v.replace("\n", " ").strip()


Action = ChatAction
