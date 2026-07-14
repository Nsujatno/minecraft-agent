/**
 * The bot<->brain contract. Mirror of brain/protocol.py.
 *
 * Keep the two sides in sync: this file is the interface, not the code around it.
 */

// --- events: bot -> brain ---

export type ChatEvent = { type: "chat"; username: string; message: string };
export type DeathEvent = { type: "death" };

export type Event = ChatEvent | DeathEvent;

// --- actions: brain -> bot ---

export type ChatAction = { action: "chat"; message: string };

export type Action = ChatAction;
