import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const apiDir = path.join(root, "apps", "api");
const sidecarEntry = path.join(apiDir, "app_sidecar.py");
const distDir = path.join(apiDir, "dist");
const tauriBinDir = path.join(root, "apps", "client", "src-tauri", "binaries");
const sidecarBaseName = "stock-box-api-sidecar";

function fail(message) {
  console.error(`[build:api-sidecar] ${message}`);
  process.exit(1);
}

function run(command, args, cwd = root) {
  const result = spawnSync(command, args, { cwd, stdio: "inherit", shell: false });
  if (result.status !== 0) {
    fail(`command failed: ${command} ${args.join(" ")}`);
  }
}

if (!existsSync(sidecarEntry)) {
  fail(`entry script not found: ${sidecarEntry}`);
}

// Ensure the API virtual environment is present and dependencies are installed.
run("uv", ["sync", "--project", apiDir], root);

const pyInstallerArgs = [
  "run",
  "--project",
  apiDir,
  "--with",
  "pyinstaller",
  "pyinstaller",
  "--noconfirm",
  "--clean",
  "--onefile",
  "--distpath",
  distDir,
  "--workpath",
  path.join(apiDir, "build"),
  "--specpath",
  apiDir,
  "--name",
  sidecarBaseName,
  sidecarEntry
];

// Build a standalone API executable via the API project's uv environment.
run("uv", pyInstallerArgs, root);

const sourceExecutable = path.join(
  distDir,
  `${sidecarBaseName}${os.platform() === "win32" ? ".exe" : ""}`
);

if (!existsSync(sourceExecutable)) {
  fail(`sidecar executable not generated: ${sourceExecutable}`);
}

mkdirSync(tauriBinDir, { recursive: true });
const targetExecutable = path.join(
  tauriBinDir,
  `${sidecarBaseName}${os.platform() === "win32" ? ".exe" : ""}`
);
copyFileSync(sourceExecutable, targetExecutable);

console.log(`[build:api-sidecar] generated: ${targetExecutable}`);
