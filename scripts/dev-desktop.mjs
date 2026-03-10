import { spawn } from "node:child_process";
import net from "node:net";
import os from "node:os";
import process from "node:process";

const root = process.cwd();
const cargoBin = `${os.homedir()}/.cargo/bin`;
const isLinuxDesktop = process.platform === "linux";
const env = {
  ...process.env,
  PATH: process.env.PATH ? `${cargoBin}:${process.env.PATH}` : cargoBin,
  ...(isLinuxDesktop && !process.env.WEBKIT_DISABLE_DMABUF_RENDERER
    ? { WEBKIT_DISABLE_DMABUF_RENDERER: "1" }
    : {})
};

const tasks = [];

function isPortBusy(port, host = "127.0.0.1") {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", (error) => {
      if (error.code === "EADDRINUSE") {
        resolve(true);
        return;
      }
      resolve(false);
    });
    server.once("listening", () => {
      server.close(() => resolve(false));
    });
    server.listen(port, host);
  });
}

function run(command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    stdio: "inherit",
    shell: false,
    env
  });
  tasks.push(child);
  child.on("exit", (code) => {
    if (code !== 0) {
      shutdown(code ?? 1);
    }
  });
  return child;
}

function shutdown(code = 0) {
  for (const task of tasks) {
    if (!task.killed) {
      task.kill("SIGTERM");
    }
  }
  process.exit(code);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

const conflicts = [];
if (await isPortBusy(8000)) {
  conflicts.push("127.0.0.1:8000 is already in use by the API service");
}
if (await isPortBusy(5173)) {
  conflicts.push("127.0.0.1:5173 is already in use by the Vite dev server");
}

if (conflicts.length > 0) {
  console.error("[dev:desktop] Cannot start because required ports are busy:");
  for (const conflict of conflicts) {
    console.error(`- ${conflict}`);
  }
  console.error("[dev:desktop] Stop the existing process on those ports and run `pnpm dev:desktop` again.");
  process.exit(1);
}

run("bash", ["-lc", "cd apps/api && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"], root);
run("bash", ["-lc", "cd apps/client && pnpm tauri dev"], root);
