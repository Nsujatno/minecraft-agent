"""LLM agent that decides what to do from an event"""

import logging

from llm import BudgetExceeded, Chatbot
from protocol import Action, ChatAction, ChatEvent, DeathEvent, Event

log = logging.getLogger(__name__)


class Agent:
    def __init__(self, chatbot: Chatbot) -> None:
        self._chatbot = chatbot

    async def decide(self, event: Event) -> Action | None:
        """Event in, action (or nothing) out. M2 makes this a plan/act/reflect loop."""
        if isinstance(event, DeathEvent):
            return ChatAction(message="I died")

        if isinstance(event, ChatEvent):
            if event.message == "ping":  # free liveness check, spends no tokens
                return ChatAction(message=f"pong, {event.username}")
            if event.message == "nida":
                return ChatAction(message="is the goat")
            try:
                return await self._chatbot.decide(event.username, event.message)
            except BudgetExceeded as e:
                log.warning("%s", e)
                return ChatAction(message=f"({e})")

        return None
