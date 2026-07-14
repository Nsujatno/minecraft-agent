/** Entrypoint: wire the pieces together and run. */

import mineflayer from "mineflayer";
import { execute } from "./actions.js";
import { BrainLink } from "./brainLink.js";
import * as config from "./config.js";
import { wire } from "./events.js";
import { Movements, pathfinder } from "mineflayer-pathfinder";

const bot = mineflayer.createBot({
  host: config.MC_HOST,
  port: config.MC_PORT,
  username: config.MC_USERNAME,
  auth: "offline",
  version: config.MC_VERSION,
});

bot.loadPlugin(pathfinder)
bot.once("spawn", () => bot.pathfinder.setMovements(new Movements(bot)));

const link = new BrainLink(config.WS_PORT, (action) => {
  execute(bot, action).catch((err) => console.log("action failed:", err.message));
});
wire(bot, link);
