/** Executors: an action from the brain -> a thing the bot does in the world.
 *
 * New skills (goto, mineBlocks, getInventory...) land here, one case each.
 */

import type { Bot } from "mineflayer";
import type { Block } from "prismarine-block";
import type { Action } from "./protocol.js";
import pathfinderPkg from "mineflayer-pathfinder";
import { Vec3 } from "vec3";

const { goals } = pathfinderPkg;

/** Place a crafting table from inventory onto open ground next to the bot. */
async function placeCraftingTable(bot: Bot): Promise<Block> {
  const held = bot.inventory.items().find((i) => i.name === "crafting_table");
  if (!held) throw new Error("no crafting_table in inventory to place");
  await bot.equip(held, "hand");

  const base = bot.entity.position.floored();
  for (const d of [new Vec3(1, 0, 0), new Vec3(-1, 0, 0), new Vec3(0, 0, 1), new Vec3(0, 0, -1)]) {
    const target = base.plus(d); // cell to fill, at foot level
    const ref = bot.blockAt(target.plus(new Vec3(0, -1, 0))); // solid block under it
    if (bot.blockAt(target)?.boundingBox !== "empty" || ref?.boundingBox !== "block") continue;
    await bot.lookAt(target.offset(0.5, 0.5, 0.5));
    await bot.placeBlock(ref, new Vec3(0, 1, 0));
    const placed = bot.blockAt(target);
    if (placed?.name === "crafting_table") return placed;
  }
  throw new Error("couldn't place crafting table — no clear spot next to me");
}

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
    case "goto": {
      try {
        await bot.pathfinder.goto(new goals.GoalNear(action.x, action.y, action.z, 1));
      } catch (err) {
        // a newer goto superseded this one; not a real failure
        if ((err as Error).name === "GoalChanged") return;
        throw err;
      }
      return;
    }
    case "collect_block": {
      const count = Math.min(action.count ?? 1, 64);
      let collected = 0;
      for (let i = 0; i < count; i++) {
        const block = bot.findBlock({
          matching: (b) => b.name.includes(action.name),
          maxDistance: 64,
        });
        if (!block) break; // none left in range
        await bot.pathfinder.goto(
          new goals.GoalGetToBlock(block.position.x, block.position.y, block.position.z),
        );
        await bot.tool.equipForBlock(block); // dig uses whatever is held; no-op if already best
        await bot.dig(block);
        collected++;
      }
      if (collected === 0) throw new Error(`no ${action.name} within range`);
      return;
    }
    case "craft": {
      const item = bot.registry.itemsByName[action.name];
      if (!item) throw new Error(`unknown item: ${action.name}`);

      // 2x2 recipes craft in inventory (no table); 3x3 need a crafting table nearby.
      const tableId = bot.registry.blocksByName.crafting_table?.id;
      let table = tableId ? bot.findBlock({ matching: tableId, maxDistance: 32 }) : null;
      let recipe = bot.recipesFor(item.id, null, 1, table ?? null)[0];

      // place crafting table from inventory if needed
      if (!recipe && !table && bot.recipesFor(item.id, null, 1, true).length) {
        table = await placeCraftingTable(bot);
        recipe = bot.recipesFor(item.id, null, 1, table)[0];
      }
      if (!recipe) {
        // list every recipe's ingredients
        const all = bot.recipesAll(item.id, null, table ?? true);
        if (!all.length) throw new Error(`no recipe for ${action.name}`);
        const opts = [...new Set(all.map((r) =>
          r.delta.filter((d) => d.count < 0)
            .map((d) => `${-d.count} ${bot.registry.items[d.id]?.name ?? d.id}`)
            .join(" + "),
        ))];
        const table_ = all[0]!.requiresTable ? "; needs a crafting table nearby" : "";
        throw new Error(`can't craft ${action.name} yet — need one of: ${opts.join(" | ")}${table_}`);
      }

      if (recipe.requiresTable && table) {
        await bot.pathfinder.goto(new goals.GoalGetToBlock(table.position.x, table.position.y, table.position.z));
        table = bot.blockAt(table.position); // re-fetch after moving
      }
      await bot.craft(recipe, action.count, recipe.requiresTable ? table ?? undefined : undefined);
      return;
    }
    case "equip": {
      const item = bot.inventory.items().find((i) => i.name === action.name);
      if (!item) throw new Error(`no ${action.name} in inventory`);
      await bot.equip(item, "hand");
      return;
    }
    default:
      console.log("unknown action, ignoring:", action);
  }
}
