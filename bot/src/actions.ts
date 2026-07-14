/** Executors: an action from the brain -> a thing the bot does in the world.
 *
 * New skills (goto, mineBlocks, getInventory...) land here, one case each.
 */

import type { Bot } from "mineflayer";
import type { Action } from "./protocol.js";

export function execute(bot: Bot, action: Action): void {
  switch (action.action) {
    case "chat":
      bot.chat(action.message);
      return;
    default:
      console.log("unknown action, ignoring:", action);
  }
}
