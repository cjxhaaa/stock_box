import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";

const cargoBin = path.join(os.homedir(), ".cargo", "bin");
const pathSeparator = path.delimiter;
const currentPath = process.env.PATH ?? "";
const env = {
  ...process.env,
  PATH: currentPath.includes(cargoBin)
    ? currentPath
    : currentPath
      ? `${cargoBin}${pathSeparator}${currentPath}`
      : cargoBin
};

const isWindows = process.platform === "win32";
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

if (isWindows) {
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
}

pnpmCandidates.push({ kind: isWindows ? "cmd" : "direct", command: "pnpm" });

function spawnPnpm(args, options) {
  let lastResult = null;
  for (const candidate of pnpmCandidates) {
    if ((candidate.kind === "cmd" || candidate.kind === "direct") && candidate.command !== "pnpm") {
      if (!existsSync(candidate.command)) {
        continue;
      }
    }

    if (candidate.kind === "node") {
      const result = spawnSync(candidate.command, [...candidate.argsPrefix, ...args], options);
      if (result.status === 0) {
        return result;
      }
      lastResult = result;
      continue;
    }

    if (candidate.kind === "cmd") {
      const result = spawnSync(
        comSpec,
        ["/d", "/s", "/c", candidate.command, ...args],
        options
      );
      if (result.status === 0) {
        return result;
      }
      lastResult = result;
      continue;
    }

    const result = spawnSync(candidate.command, args, options);
    if (result.status === 0) {
      return result;
    }
    lastResult = result;
  }

  return lastResult ?? { status: 1 };
}

const checks = [
  ["rustc", ["--version"]],
  ["cargo", ["--version"]]
];

let failed = false;

for (const [command, args] of checks) {
  const result = spawnSync(command, args, { encoding: "utf8", env });
  if (result.status === 0) {
    process.stdout.write(`${command}: ${result.stdout.trim()}\n`);
  } else {
    failed = true;
    process.stdout.write(`${command}: missing\n`);
  }
}

const pnpmResult = spawnPnpm(["--version"], { encoding: "utf8", env });
if (pnpmResult.status === 0) {
  process.stdout.write(`pnpm: ${pnpmResult.stdout.trim()}\n`);
} else {
  failed = true;
  process.stdout.write("pnpm: missing\n");
}

const tauriInfo = spawnPnpm(["exec", "tauri", "info"], {
  encoding: "utf8",
  env,
  cwd: path.join(process.cwd(), "apps", "client")
});

if (tauriInfo.status === 0) {
  const info = tauriInfo.stdout;
  const missingGtk = info.includes("webkit2gtk-4.1: not installed");
  const missingRsvg = info.includes("rsvg2: not installed");
  if (missingGtk || missingRsvg) {
    failed = true;
    process.stdout.write("tauri-prereqs: missing\n");
    process.stdout.write(
      "linux-hint: sudo apt install libwebkit2gtk-4.1-dev librsvg2-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev\n"
    );
  } else {
    process.stdout.write("tauri-prereqs: ok\n");
  }
} else {
  failed = true;
  process.stdout.write("tauri-prereqs: tauri info failed\n");
}

process.exit(failed ? 1 : 0);
