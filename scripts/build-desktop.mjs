import { spawnSync } from "node:child_process";
import os from "node:os";
import process from "node:process";

const root = process.cwd();
const cargoBin = `${os.homedir()}/.cargo/bin`;
const env = {
  ...process.env,
  PATH: process.env.PATH ? `${cargoBin}:${process.env.PATH}` : cargoBin
};

function fail(message) {
  console.error(`[build:desktop] ${message}`);
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

run("pnpm", ["build:api-sidecar"]);

const tauriBuildArgs = ["--filter", "@stock-box/client", "tauri", "build"];

if (process.platform === "linux") {
  // AppImage requires linuxdeploy; build deb/rpm by default for better portability.
  tauriBuildArgs.push("--bundles", "deb,rpm");
}

run("pnpm", tauriBuildArgs);
