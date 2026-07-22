"""LLM agent that decides what to do from an event.

The act->observe->re-decide loop lives here: a user message starts an LLM-driven
loop, each ActionResult feeds the next step, and it ends when the LLM returns no
action (goal done) or the per-request step cap trips.
"""

import logging

import config
from llm import BudgetExceeded, Chatbot
from protocol import Action, ActionResult, ChatAction, ChatEvent, DeathEvent, Event

log = logging.getLogger(__name__)


def _describe_state(s: ActionResult | ChatEvent) -> str:
    inv = ", ".join(f"{n} x{c}" for n, c in s.inventory.items()) or "empty"
    return (f"position {s.x:.0f} {s.y:.0f} {s.z:.0f}, "
            f"health {s.health:.0f}, food {s.food:.0f}, "
            f"holding {s.held or 'nothing'}, inventory: {inv}")


def _describe(r: ActionResult) -> str:
    if r.ok:
        return f"[observation] action {r.action} ok. {_describe_state(r)}"
    # create a note when an action fails
    return (f"[observation] action {r.action} failed: {r.error}. {_describe_state(r)}\n"
            "This failure taught you something. Set `note` to the general rule it revealed "
            "(a recipe, a prerequisite, a wrong assumption) so you never retry this mistake.")


class Agent:
    def __init__(self, chatbot: Chatbot) -> None:
        self._chatbot = chatbot
        self._active = False  # mid-loop, driven by the LLM?
        self._steps = 0

    async def decide(self, event: Event) -> Action | None:
        if isinstance(event, DeathEvent):
            return ChatAction(message="I died")

        if isinstance(event, ChatEvent):
            if event.message == "ping":  # free liveness check, spends no tokens
                return ChatAction(message=f"pong, {event.username}")
            if event.message == "nida":
                return ChatAction(message="is the goat")
            # a user message starts a fresh LLM-driven loop
            self._active = True
            self._steps = 0
            obs = f"{event.username}: {event.message}\n[your state] {_describe_state(event)}"
            return await self._think(obs)

        if isinstance(event, ActionResult):
            if not self._active:  # result of a one-off canned action; no follow-up
                return None
            self._steps += 1
            if self._steps >= config.MAX_STEPS:
                self._active = False
                return ChatAction(message="stopping — that took too many steps")
            return await self._think(_describe(event))

        return None

    async def _think(self, observation: str) -> Action | None:
        try:
            action = await self._chatbot.decide(observation)
        except BudgetExceeded as e:
            log.warning("%s", e)
            self._active = False
            return ChatAction(message=f"({e})")
        if action is None:  # LLM says the goal is complete
            self._active = False
        return action
