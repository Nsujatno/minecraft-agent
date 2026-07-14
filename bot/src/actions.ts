/** Executors: an action from the brain -> a thing the bot does in the world.
 *
 * New skills (goto, mineBlocks, getInventory...) land here, one case each.
 */

import type { Bot } from "mineflayer";
import type { Action } from "./protocol.js";

const CHAT_LIMIT = 256; // minecraft drops anything longer
const CHAT_GAP_MS = 300; // vanilla kicks for chat spam; don't fire them all at once

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Split a long line into <=limit chunks, breaking on spaces where it can. */
export function chunk(message: string, limit = CHAT_LIMIT): string[] {
  const out: string[] = [];
  let line = "";

  for (let word of message.split(/\s+/).filter(Boolean)) {
    while (word.length > limit) {
      // a single word longer than the whole limit: hard-cut it
      if (line) (out.push(line), (line = ""));
      out.push(word.slice(0, limit));
      word = word.slice(limit);
    }
    if (!line) line = word;
    else if (line.length + 1 + word.length <= limit) line += ` ${word}`;
    else (out.push(line), (line = word));
  }

  if (line) out.push(line);
  return out;
}

export async function execute(bot: Bot, action: Action): Promise<void> {
  switch (action.action) {
    case "chat": {
      const parts = chunk(action.message);
      for (const [i, part] of parts.entries()) {
        if (i > 0) await sleep(CHAT_GAP_MS);
        bot.chat(part);
      }
      return;
    }
    default:
      console.log("unknown action, ignoring:", action);
  }
}
