/** Perception: mineflayer events -> protocol events on the wire.
 *
 * New things the brain should know about land here, one listener each.
 */

import type { Bot } from "mineflayer";
import type { BrainLink } from "./brainLink.js";

export function wire(bot: Bot, link: BrainLink): void {
  bot.once("spawn", () => {
    const { x, y, z } = bot.entity.position;
    console.log(`spawned at ${x.toFixed(1)} ${y.toFixed(1)} ${z.toFixed(1)}`);
    bot.chat("agent online");
  });

  bot.on("chat", (username, message) => {
    if (username === bot.username) return; // don't echo ourselves into the brain
    console.log(`<${username}> ${message}`);
    link.emit({ type: "chat", username, message });
  });

  bot.on("death", () => {
    console.log(`${bot.username} died`);
    link.emit({ type: "death" });
  });

  // local-only: the brain has no say in these
  bot.on("kicked", (reason) => console.log("kicked:", reason));
  bot.on("error", (err) => console.log("error:", err.message));
}
