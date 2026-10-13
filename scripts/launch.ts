// One-click start: asks for a Comfy API key on the first run, installs packages,
// starts the app, and opens it in the browser. start-windows.cmd and start-mac.command run this.
// Starting the app spends nothing; only "Make the film" spends credits.
import { spawn } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { createInterface } from "node:readline/promises";
import { fileURLToPath } from "node:url";

const APP_URL = "http://127.0.0.1:3000";
const KEYS_URL = "https://platform.comfy.org/profile/api-keys";
const ENV_FILE = ".env.local";
const KEY_LINE = /^COMFY_API_KEY=(.*)$/m;
const isWindows = process.platform === "win32";

process.chdir(fileURLToPath(new URL("..", import.meta.url)));

function openInBrowser(url: string) {
  const [cmd, args] = isWindows ? ["cmd", ["/c", "start", "", url]]
    : process.platform === "darwin" ? ["open", [url]]
    : ["xdg-open", [url]];
  spawn(cmd, args, { stdio: "ignore", detached: true }).unref();
}

async function isUp() {
  try {
    return (await fetch(APP_URL, { signal: AbortSignal.timeout(2000) })).ok;
  } catch {
    return false;
  }
}

function run(script: string[]) {
  // npm is npm.cmd on Windows, which Node only spawns through a shell.
  return spawn("npm", script, { stdio: "inherit", shell: isWindows });
}

function savedKey() {
  if (!existsSync(ENV_FILE)) return "";
  return readFileSync(ENV_FILE, "utf8").match(KEY_LINE)?.[1].trim() ?? "";
}

async function askForKey() {
  console.log("\nDreams Studio runs on Comfy Cloud with your own Comfy API key.");
  console.log(`Opening ${KEYS_URL} so you can create one.`);
  console.log(`The key stays on this computer, in ${ENV_FILE}.\n`);
  openInBrowser(KEYS_URL);
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  let key = "";
  while (!key) key = (await rl.question("Paste your key and press Enter: ")).trim();
  rl.close();
  const env = readFileSync(existsSync(ENV_FILE) ? ENV_FILE : ".env.example", "utf8");
  const line = `COMFY_API_KEY=${key}`;
  writeFileSync(ENV_FILE, KEY_LINE.test(env) ? env.replace(KEY_LINE, () => line) : `${env.trimEnd()}\n${line}\n`);
  console.log(`Saved your key to ${ENV_FILE}.\n`);
}

if (!savedKey()) await askForKey();

if (await isUp()) {
  console.log(`Dreams Studio is already running. Opening ${APP_URL}`);
  openInBrowser(APP_URL);
  process.exit(0);
}

if (!existsSync("node_modules")) {
  console.log("Installing packages (first run only, about a minute)...");
  const code = await new Promise<number | null>((done) => run(["ci"]).on("exit", done));
  if (code !== 0) throw new Error("npm ci failed. Check the messages above, then run this again.");
}

console.log("Starting Dreams Studio. Keep this window open; close it to stop the app.\n");
const app = run(["run", "dev"]);
app.on("exit", (code) => process.exit(code ?? 0));

for (let tries = 0; tries < 120; tries++) {
  if (await isUp()) {
    console.log(`\nDreams Studio is ready at ${APP_URL}`);
    openInBrowser(APP_URL);
    break;
  }
  await new Promise((r) => setTimeout(r, 1000));
}
