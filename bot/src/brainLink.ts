/** Transport: the websocket to the brain. Knows nothing about mineflayer. */

import { WebSocket, WebSocketServer } from "ws";
import type { Action, Event } from "./protocol.js";

export class BrainLink {
  private readonly wss: WebSocketServer;

  constructor(port: number, onAction: (action: Action) => void) {
    this.wss = new WebSocketServer({ port });
    console.log(`ws server on ${port}`);

    this.wss.on("connection", (ws) => {
      console.log("brain connected");
      ws.on("close", () => console.log("brain disconnected"));
      ws.on("message", (data) => {
        let action: Action;
        try {
          action = JSON.parse(String(data)) as Action;
        } catch {
          console.log("bad action json, ignoring:", String(data));
          return;
        }
        console.log("action:", action);
        onAction(action);
      });
    });
  }

  /** Push an event to every connected brain. No brain connected = event is dropped. */
  emit(event: Event): void {
    const payload = JSON.stringify(event);
    for (const client of this.wss.clients) {
      if (client.readyState === WebSocket.OPEN) client.send(payload);
    }
  }
}
