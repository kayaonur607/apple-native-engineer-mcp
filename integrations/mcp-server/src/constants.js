/**
 * Identity shared by the server, the CLI and the diagnostics tool.
 *
 * Kept in its own module so `environment.js` can report the server name without
 * importing `server.js` (which would make the graph circular: server → tools →
 * environment → server).
 */

export const SERVER_NAME = "apple-native-engineer";
export const SERVER_VERSION = "2.5.1";
