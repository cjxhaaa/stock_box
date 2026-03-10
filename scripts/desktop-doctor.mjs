import { spawnSync } from "node:child_process";
import os from "node:os";

const cargoBin = `${os.homedir()}/.cargo/bin`;
const env = {
  ...process.env,
  PATH: process.env.PATH ? `${cargoBin}:${process.env.PATH}` : cargoBin
};

const checks = [
  ["rustc", ["--version"]],
  ["cargo", ["--version"]],
  ["pnpm", ["--version"]],
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

const tauriInfo = spawnSync("pnpm", ["exec", "tauri", "info"], {
  encoding: "utf8",
  env,
  cwd: `${process.cwd()}/apps/client`
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
