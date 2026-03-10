import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const cargoBin = `${os.homedir()}\\.cargo\\bin`;
const envPath = process.env.PATH ?? "";
const env = {
  ...process.env,
  PATH: envPath.includes(cargoBin) ? envPath : `${cargoBin};${envPath}`
};

const pnpmExecPath = process.env.npm_execpath;
const pnpmHome = process.env.PNPM_HOME;
const localAppData = process.env.LOCALAPPDATA;
const comSpec = process.env.ComSpec || "cmd.exe";

const pnpmCandidates = [];

if (pnpmExecPath) {
  pnpmCandidates.push({
    kind: "node",
    command: process.execPath,
    argsPrefix: [pnpmExecPath]
  });
}

if (pnpmHome) {
  pnpmCandidates.push({
    kind: "cmd",
    command: path.join(pnpmHome, "pnpm.cmd")
  });
}

if (localAppData) {
  pnpmCandidates.push({
    kind: "cmd",
    command: path.join(localAppData, "pnpm", "pnpm.cmd")
  });
}

pnpmCandidates.push({ kind: "cmd", command: "pnpm" });

function fail(message) {
  console.error(`[build:desktop:windows] ${message}`);
  process.exit(1);
}

function spawnPnpm(args) {
  let lastResult = null;

  for (const candidate of pnpmCandidates) {
    if (candidate.kind === "cmd" && candidate.command !== "pnpm") {
      if (!existsSync(candidate.command)) {
        continue;
      }
    }

    let result;
    if (candidate.kind === "node") {
      result = spawnSync(candidate.command, [...candidate.argsPrefix, ...args], {
        cwd: root,
        stdio: "inherit",
        shell: false,
        env
      });
    } else {
      result = spawnSync(
        comSpec,
        ["/d", "/s", "/c", candidate.command, ...args],
        {
          cwd: root,
          stdio: "inherit",
          shell: false,
          env
        }
      );
    }

    if (result.status === 0) {
      return;
    }

    lastResult = result;
  }

  fail(`command failed: pnpm ${args.join(" ")}`);
}

if (process.platform !== "win32") {
  fail("this script must be run on Windows (win32)");
}

spawnPnpm(["build:api-sidecar"]);
spawnPnpm(["--filter", "@stock-box/client", "tauri", "build", "--bundles", "msi,nsis"]);
