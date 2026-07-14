# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An autonomous Minecraft agent: a Node/Mineflayer bot that joins a Java Edition world as a normal
player, driven by a Python "brain" that does the LLM thinking. See `PRD.md` for goals and milestones
(currently between M0 and M1), `info.md` for a walkthrough of a message's round trip.

## Running it

Both services read the same root `.env` (copy from `.env.example`). `MC_PORT` changes every time you
re-open the world to LAN — update it before each session.

```bash
cd bot && npm install && npm run dev        # tsx watch, hot-reloads
cd brain && pip install -r requirements.txt && python main.py   # no reload, restart by hand
```

Bot first: it's the WebSocket *server*; the brain is the client and retries until it's up.
`npm run typecheck` in `bot/`. No test suite yet — verify by typing in in-game chat (`ping` is a
free liveness check that spends no tokens).

## Architecture

Two services that are deliberately ignorant of each other's job. The bot owns the game connection and
knows nothing about the LLM; the brain owns all thinking and never touches mineflayer. They meet only
at the protocol.

| Layer | Bot (TypeScript) | Brain (Python) |
|---|---|---|
| contract | `protocol.ts` | `protocol.py` |
| transport | `brainLink.ts` (WS server) | `bot_link.py` (WS client) |
| perception | `events.ts` | — |
| policy | — | `agent.py` (the only place that decides) |
| model | — | `llm.py` (the only module that knows a model exists) |
| execution | `actions.ts` | — |
| config | `config.ts` | `config.py` (only readers of env) |

**The two protocol files are the interface and must stay in sync by hand.** The `type` / `action`
string literals are the discriminators — a typo there fails silently (the brain logs
`unknown event, ignoring` and carries on, by design, so the bot can ship ahead of the brain).

Adding an event: declare it in `protocol.ts` + add to the `Event` union → emit it in `events.ts` →
mirror the model in `protocol.py` + add to the `Event` union → branch on it in `Agent.decide()`.
An event with no branch in `decide()` is silently ignored. Adding an action is the same shape
reflected: both `Action` unions, a case in `actions.ts`, returned from `agent.py`.

## Constraints worth respecting

- **Cost control is a product requirement, not a nicety.** `Chatbot` enforces a hard per-session call
  cap and raises `BudgetExceeded`; callers degrade to a chat line rather than spend. Keep thinking
  event-driven — never a per-tick or timer-based LLM call.
- Events are pumped and awaited one at a time in `bot_link._pump` (see the `ponytail:` comment) — one
  LLM call in flight, events queue behind it.
- If no brain is connected, events are dropped. The bot never acts on its own.
