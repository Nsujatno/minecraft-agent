import dotenv from "dotenv";
import mineflayer from "mineflayer";
import { WebSocketServer, WebSocket } from "ws";

dotenv.config({ path: "../.env" });

const bot = mineflayer.createBot({
  host: "127.0.0.1",
  port: Number(process.env.MC_PORT),
  username: process.env.MC_USERNAME ?? "agent",
  auth: "offline",
  version: process.env.MC_VERSION,
});

const wss = new WebSocketServer({ port: Number(process.env.WS_PORT ?? 8080) });
console.log(`ws server on ${Number(process.env.WS_PORT ?? 8080)}`);

// sends event to the brain through the websocket
function emit(event: Record<string, unknown>) {
  const payload = JSON.stringify(event);
  for (const client of wss.clients) {
    if (client.readyState === WebSocket.OPEN) client.send(payload);
  }
}

wss.on("connection", (ws) => {
  console.log("brain connected");
  ws.on("close", () => console.log("brain disconnected"));
  ws.on("message", (data) => {
    const action = JSON.parse(String(data));
    console.log("action:", action);
    if (action.action === "chat") bot.chat(action.message);
  });
});

bot.once("spawn", () => {
  const { x, y, z } = bot.entity.position;
  console.log(`spawned at ${x.toFixed(1)} ${y.toFixed(1)} ${z.toFixed(1)}`);
  bot.chat("agent online");
});

bot.on("chat", (username, message) => {
  if (username === bot.username) return;
  console.log(`<${username}> ${message}`);
  emit({ type: "chat", username, message });
});

bot.on("death", () => {
  emit({ type: "death" })
});

bot.on("kicked", (reason) => console.log("kicked:", reason));
bot.on("error", (err) => console.log("error:", err.message));
