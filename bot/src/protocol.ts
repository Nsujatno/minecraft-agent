/**
 * The bot<->brain contract. Mirror of brain/protocol.py.
 *
 * Keep the two sides in sync: this file is the interface, not the code around it.
 */

// --- events: bot -> brain ---

export type ChatEvent = {
  type: "chat";
  username: string;
  message: string;
  x: number;
  y: number;
  z: number;
  health: number;
  food: number;
  inventory: { [name: string]: number };
};
export type DeathEvent = { type: "death" };

// result of executing an action, feeds back to brain to decide next step
export type ActionResult = {
  type: "action_result";
  action: string;
  ok: boolean;
  error?: string;
  x: number;
  y: number;
  z: number;
  health: number;
  food: number;
  inventory: { [item: string]: number };
};

export type Event = ChatEvent | DeathEvent | ActionResult;

// --- actions: brain -> bot ---

export type ChatAction = { action: "chat"; message: string };
export type GotoAction = { action: "goto"; x: number; y: number; z: number };
export type CollectBlockAction = { action: "collect_block"; name: string; count?: number };

export type Action = ChatAction | GotoAction | CollectBlockAction;
