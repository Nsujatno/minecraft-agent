How it works

The two services are deliberately ignorant of each other's job. The bot owns the game connection and knows nothing about the LLM. The brain owns all thinking and never touches mineflayer. They meet only at the protocol.

A round trip, following one chat message end to end:

1. You type in Minecraft. Mineflayer fires bot.on("chat") in events.ts, the perception layer. It builds a ChatEvent and hands it to link.emit().
2. brainLink.ts JSON-encodes it and pushes it to every connected brain. If no brain is connected, the event is dropped on the floor — the bot does not act on its own.
3. bot_link.py receives the line and hands it to event_adapter.validate_json(), which uses the type field as a discriminator to parse it into the right pydantic model. An event the brain doesn't recognize gets logged and skipped rather than crashing the loop.
4. The parsed event goes to agent.py, the policy layer. This is the only place that decides what to do. Today it's a few isinstance branches; at M2 it becomes the plan/act/reflect loop. It returns an Action or None.
5. For a normal chat line it calls llm.py, the only module that knows a model exists. Chatbot holds the rolling history and the call counter, and raises BudgetExceeded once you hit the cap instead of spending. The agent catches that and degrades to a chat line.
6. The action goes back over the socket as JSON, lands in brainLink.ts's onAction callback, and gets dispatched to actions.ts, which turns it into a real mineflayer call.

The reason agent.py and events.ts sit opposite each other in the table is that they're the two halves of the same seam: the bot decides what's worth reporting, the brain decides what's worth doing. Everything else is plumbing.

Registering a new event

Say you want the brain to know when the bot takes damage. Four files, one line-ish each, in this order:

1. bot/src/protocol.ts — declare it and add it to the union:
export type HealthEvent = { type: "health"; hp: number; food: number };
export type Event = ChatEvent | DeathEvent | HealthEvent;

2. bot/src/events.ts — emit it inside wire():
bot.on("health", () => {
  link.emit({ type: "health", hp: bot.health, food: bot.food });
});

3. brain/protocol.py — the mirror. The type literal must match the string exactly; that's what the discriminator keys on:
class HealthEvent(BaseModel):
    type: Literal["health"]
    hp: float
    food: float

Event = Annotated[Union[ChatEvent, DeathEvent, HealthEvent], Field(discriminator="type")]

4. brain/agent.py — decide what to do about it, in decide():
if isinstance(event, HealthEvent) and event.hp < 6:
    return ChatAction(message="I'm hurt!")

Then restart the brain. The bot hot-reloads under tsx watch; python main.py does not.

Two things worth knowing about that flow. If you do steps 1–2 but skip 3, nothing breaks loudly — the brain logs unknown event, ignoring and carries on, which is intentional (the bot can ship ahead of the brain) but does mean a typo in the type string looks like silence, not an error. And an event with no branch in decide() is simply ignored, which is exactly what bit you with death earlier.

Going the other direction — a new action, like goto — is the same shape reflected: add it to the Action union in both protocol files, add a case in actions.ts to execute it, and return it from agent.py.