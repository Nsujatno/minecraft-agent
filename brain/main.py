import asyncio
import json
import os

import websockets
from dotenv import load_dotenv

load_dotenv("../.env")
URL = f"ws://127.0.0.1:{os.getenv('WS_PORT', '8080')}"


def decide(event):
    """Events in, actions out. M1 replaces this with an OpenAI tool-call."""
    if event.get("type") == "chat" and event["message"] == "ping":
        return {"action": "chat", "message": f"pong, {event['username']} — from the brain"}
    if event.get("type") == "death":
        return {"action": "chat", "message": "I died"}
    return None


async def main():
    while True:
        try:
            async with websockets.connect(URL) as ws:
                print(f"connected to bot at {URL}")
                async for raw in ws:
                    event = json.loads(raw)
                    print("event:", event)
                    action = decide(event)
                    if action:
                        print("action:", action)
                        await ws.send(json.dumps(action))
        except (OSError, websockets.exceptions.ConnectionClosed):
            print("bot not up — retrying in 2s")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
