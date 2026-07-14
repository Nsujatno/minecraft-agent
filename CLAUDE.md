# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## What this is

An autonomous Minecraft agent: a Node/Mineflayer bot that joins a Java Edition world as a normal
player, driven by a Python "brain" that does the LLM thinking. See `PRD.md` for goals and milestones
(currently between M0 and M1), `info.md` for a walkthrough of a message's round trip.

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
