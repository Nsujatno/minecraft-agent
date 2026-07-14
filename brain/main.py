"""Entrypoint: wire the pieces together and run."""

import asyncio
import logging

import bot_link
import config
from agent import Agent
from llm import Chatbot


def main() -> None:
    print("Running ", config.OPENAI_MODEL)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    chatbot = Chatbot(config.OPENAI_MODEL, config.MAX_LLM_CALLS, config.HISTORY_TURNS)
    asyncio.run(bot_link.run(Agent(chatbot)))


if __name__ == "__main__":
    main()
