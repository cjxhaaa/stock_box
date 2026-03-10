import { spawnSync } from "node:child_process";
import os from "node:os";
import process from "node:process";

const root = process.cwd();
const cargoBin = `${os.homedir()}\\.cargo\\bin`;
const envPath = process.env.PATH ?? "";
const env = {
  ...process.env,
  PATH: envPath.includes(cargoBin) ? envPath : `${cargoBin};${envPath}`
};

function fail(message) {
  console.error(`[build:desktop:windows] ${message}`);
  process.exit(1);
}

function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: root,
    stdio: "inherit",
    shell: false,
    env
  });

  if (result.status !== 0) {
    fail(`command failed: ${command} ${args.join(" ")}`);
  }
}

if (process.platform !== "win32") {
  fail("this script must be run on Windows (win32)");
}

run("pnpm", ["build:api-sidecar"]);
run("pnpm", ["--filter", "@stock-box/client", "tauri", "build", "--bundles", "msi,nsis"]);
