"""Transport: the websocket to the bot. Knows nothing about the LLM."""

import asyncio
import logging

import websockets
from pydantic import ValidationError

import config
from agent import Agent
from protocol import event_adapter

log = logging.getLogger(__name__)


async def _pump(ws, agent: Agent) -> None:
    async for raw in ws:
        try:
            event = event_adapter.validate_json(raw)
        except ValidationError:
            log.warning("unknown event, ignoring: %s", raw)  # bot may be ahead of us
            continue

        log.info("event: %s", event)
        # ponytail: awaited inline, so one LLM call at a time and events queue behind
        # it. asyncio.create_task per event if it ever feels laggy.
        action = await agent.decide(event)
        if action:
            await ws.send(action.model_dump_json())


async def run(agent: Agent) -> None:
    """Connect to the bot and pump events through the agent forever."""
    while True:
        try:
            async with websockets.connect(config.WS_URL) as ws:
                log.info("connected to bot at %s", config.WS_URL)
                await _pump(ws, agent)
        except (OSError, websockets.exceptions.ConnectionClosed):
            log.info("bot not up — retrying in %ss", config.RECONNECT_SECONDS)
            await asyncio.sleep(config.RECONNECT_SECONDS)
