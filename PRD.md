# PRD: Autonomous Minecraft AI Agent

## Overview

An AI-driven Minecraft bot you can spawn into your Java Edition world. In Phase 1 you command it via
in-game chat and it performs actions (move, mine, report inventory). In Phase 2 it becomes an
**autonomous, goal-directed agent** that perceives the world, plans, acts, and reflects on its own.

For-fun MVP that doubles as a resume project. Priorities: a working, impressive demo fast; a clean
architecture that can grow the "brain"; and strict cost control (no runaway LLM bills).

**Core story:** a `plan → act → observe → reflect` agent loop driving a real game character.

## Goals

- Spawn a bot into your world and command it in natural language via in-game chat.
- Reliable core skills: navigation, mining/collecting, inventory/status reporting.
- An autonomous goal-directed loop that pursues a high-level goal without step-by-step commands.
- Persistence so the agent remembers its goal/base across restarts.
- Hard cost ceilings and an instant kill-switch.

## Non-Goals (MVP)

- Bedrock Edition support.
- Server-side mods (Fabric/Forge).
- Long-term vector memory / learned-skill library (Voyager-style) — future Phase 3.
- Public/multiplayer server deployment with real Microsoft auth.

## Decisions

| Area | Decision |
|------|----------|
| Platform | Java Edition + **Mineflayer** (headless protocol client; joins as a normal player, no world mods) |
| Architecture | **Two services**: Node bot (Mineflayer) + **Python brain** (LLM / planning / memory) |
| IPC | **WebSocket**, Node bot is the server, Python connects as client. Bidirectional: Python sends actions, bot pushes live events |
| LLM | **OpenAI**, cheapest **mini/nano tier** (e.g. `gpt-4o-mini`; confirm current model/price at build time). Event-driven calls, not fast-timer |
| Phase 1 input | **In-game chat** → brain interprets → bot acts → replies in chat |
| Skills (MVP) | Movement/navigation, mine & collect blocks, inventory/status reporting, place/build & craft (**build/craft = stretch**) |
| Autonomy model | **Goal-directed planner**: decompose goal → execute → check → replan. Idles until given a goal |
| Memory | **Working memory (in-context) + small JSON state file** (base coords, current goal, progress). No DB |
| Test server | **Open to LAN** now (offline-mode, no auth, no install, fixed port); migrate to local **Paper** in Phase 3 for unattended runs |
| Guardrails (MVP) | **Chat kill-switch / stop** + **LLM budget cap** (max calls/session, min interval between calls). Geo-fence & no-grief deferred |

## Architecture

```
  Minecraft world (Open to LAN, offline-mode, fixed port)
        ▲  plays as a normal player
        │
  ┌─────┴───────────────┐        WebSocket         ┌───────────────────────────┐
  │  Node bot service   │◄────── actions ──────────│   Python brain service    │
  │  (Mineflayer)       │                          │                           │
  │  - connect / login  │──────► events ──────────►│  - OpenAI client (tools)  │
  │  - skill executors  │  (chat, damage, arrived, │  - planner / agent loop   │
  │  - pathfinder       │   inventory, tick)       │  - working memory + state │
  │  - WS server        │                          │  - budget / kill-switch   │
  └─────────────────────┘                          └───────────────────────────┘
```

- **Node bot** owns the game connection and low-level skill execution; exposes a typed action API and
  streams events. Knows nothing about the LLM.
- **Python brain** owns all thinking: interpreting chat, calling the LLM with skills as tools,
  running the autonomous loop, persisting state. Talks only to the WebSocket contract.
- The **WebSocket contract (action + event schema) is the real interface** — designed first and
  versioned so both sides build independently.

## WebSocket contract (v0 sketch)

**Actions (brain → bot)**, each with an `id` for correlation:
`goto{x,y,z}`, `comeToPlayer{name}`, `follow{name}`, `stop`, `mineBlocks{blockType,count}`,
`getInventory`, `getStatus`, `chat{message}`, `placeBlock{blockType,x,y,z}` (stretch),
`craft{item,count}` (stretch).

**Events (bot → brain)**:
`ready`, `chat{username,message}`, `actionResult{id,ok,detail}`, `arrived`, `health{hp,food}`,
`damaged{by}`, `inventory{items[]}`, `blockMined{type,pos}`, `error{message}`, and a throttled
`perception{pos,nearbyEntities,timeOfDay}` snapshot.

## Milestones

**M0 — Skeleton & handshake.** Bot connects to the LAN world and stands in-game; WS server up; Python
client connects; round-trip a `chat` action. Done when a chat line in-game prints as an event in Python.

**M1 — Phase 1 command bot.** Movement (come/follow/goto/stop via `mineflayer-pathfinder`), mining
(find + mine N + collect drops), inventory/status. Brain: chat → OpenAI tool-call → dispatch → reply
in chat. Kill-switch (`stop` aborts current action + queue). Budget cap (max calls/session + min
interval). Done when "bot, mine 10 oak logs and come back" works end-to-end.

**M2 — Phase 2 autonomous goal loop (centerpiece).** Agent loop: goal → LLM decomposes → execute →
observe → reflect/replan on failure → repeat. Working memory summarized into prompt; JSON state file
persists base coords, goal, progress across restarts. Idles without spinning the LLM. Done when it
autonomously pursues "gather wood and build a small shelter before night," surviving a `stop` and a
restart without amnesia.

**M3 — Stretch / polish.** Build & craft skills; migrate to local Paper server; geo-fence/leash and
no-grief guardrails. Later (Phase 3): long-term vector memory / learned-skill library.

## Tech stack

- **Node bot:** `mineflayer`, `mineflayer-pathfinder` (nav + block-breaking; `mineflayer-baritone` a
  fancier alt), `ws`, TypeScript.
- **Python brain:** `openai`, `websockets`, `pydantic` (validate the contract), `python-dotenv`.

## Cost controls

- Event-driven thinking only — no per-tick LLM calls; the loop calls the model on new goals, action
  completions, or notable events, with a minimum seconds-between-calls floor.
- Hard per-session call cap; log estimated token spend per call.
- Mini/nano tier for all MVP decisions; reserve flagship escalation for later.

## Success criteria

- Phase 1: natural-language chat commands reliably drive movement, mining, and status reporting.
- Phase 2: the bot pursues a high-level goal end-to-end, replans on failure, and resumes after a
  restart from its state file.
- A full autonomous session stays within the budget cap with no runaway spend.

## Open items to confirm at build time

- Exact current cheapest OpenAI model name/price (mini vs nano).
- Minecraft/Mineflayer version compatibility (pin the bot to your client version).
- TypeScript vs plain JS for the bot (assumed TypeScript).
