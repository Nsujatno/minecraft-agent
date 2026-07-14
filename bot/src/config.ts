/** All env-derived settings. Nothing else reads process.env. */

import path from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";

const here = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(here, "../../.env") }); // shared with brain/

export const MC_HOST = process.env.MC_HOST ?? "127.0.0.1";
export const MC_PORT = Number(process.env.MC_PORT); // LAN port is random per session
export const MC_USERNAME = process.env.MC_USERNAME ?? "agent";
export const MC_VERSION = process.env.MC_VERSION || undefined; // undefined = autodetect

export const WS_PORT = Number(process.env.WS_PORT ?? 8080);
