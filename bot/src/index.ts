/** Entrypoint: wire the pieces together and run. */

import mineflayer from "mineflayer";
import { execute } from "./actions.js";
import { BrainLink } from "./brainLink.js";
import * as config from "./config.js";
import { wire, snapshot } from "./events.js";
import { Movements, pathfinder } from "mineflayer-pathfinder";
import { plugin as tool } from "mineflayer-tool";

const bot = mineflayer.createBot({
  host: config.MC_HOST,
  port: config.MC_PORT,
  username: config.MC_USERNAME,
  auth: "offline",
  version: config.MC_VERSION,
});

bot.loadPlugin(pathfinder)
bot.loadPlugin(tool)
bot.once("spawn", () => bot.pathfinder.setMovements(new Movements(bot)));

const link = new BrainLink(config.WS_PORT, async (action) => {
  let ok = true;
  let error: string | undefined;
  try {
    await execute(bot, action);
  } catch (err) {
    ok = false;
    error = (err as Error).message;
    console.log("action failed:", error);
  }
  link.emit({
    type: "action_result",
    action: action.action,
    ok,
    error,
    ...snapshot(bot),
  });
});
wire(bot, link);
