#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PACK_DIR = path.join(ROOT, "exmachina");
const ROOT_INSTALL_DIR = path.join(ROOT, "install");

function fail(message) {
  console.error(message);
  process.exit(1);
}

function readJson(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  const text = raw.replace(/^\uFEFF/, "");
  return JSON.parse(text);
}

function ensureExists(relPath, errors) {
  const full = path.join(PACK_DIR, relPath);
  if (!fs.existsSync(full)) {
    errors.push(`Missing: ${relPath}`);
  }
}

function ensureRootExists(relPath, errors) {
  const full = path.join(ROOT, relPath);
  if (!fs.existsSync(full)) {
    errors.push(`Missing: ${relPath}`);
  }
}

function ensureManifestPath(relPath, errors) {
  if (relPath === "install" || relPath.startsWith("install/")) {
    ensureRootExists(relPath, errors);
    return;
  }
  ensureExists(relPath, errors);
}

function collectRationalityPaths(manifest, errors) {
  const pathsObj = manifest?.rationality_protocol?.paths || {};
  Object.values(pathsObj).forEach((rel) => {
    if (typeof rel === "string") ensureExists(rel, errors);
  });
}

function collectManifestPaths(manifest, errors) {
  const pathsObj = manifest?.paths || {};
  Object.values(pathsObj).forEach((rel) => {
    if (typeof rel === "string") ensureManifestPath(rel, errors);
  });
}

function checkPack() {
  const errors = [];
  if (!fs.existsSync(PACK_DIR)) {
    fail(`Missing pack directory: ${PACK_DIR}`);
  }

  ensureExists("manifest.json", errors);
  ensureExists("openclaw.settings.json", errors);
  ensureExists("openclaw.settings.lite.json", errors);
  ensureExists("BOOTSTRAP.md", errors);
  ensureExists("QUICKSTART.md", errors);
  ensureExists("agents/00_全连结指挥体.md", errors);
  ensureRootExists("install/INTAKE.md", errors);
  ensureRootExists("install/SETTINGS.md", errors);
  ensureRootExists("install/BOOTSTRAP.md", errors);
  ensureRootExists("install/AGENTS.md", errors);
  ensureRootExists("install/intake.template.json", errors);
  ensureRootExists("PROMPT.md", errors);

  const manifestPath = path.join(PACK_DIR, "manifest.json");
  if (fs.existsSync(manifestPath)) {
    const manifest = readJson(manifestPath);
    collectRationalityPaths(manifest, errors);
    collectManifestPaths(manifest, errors);
  }

  const requiredDirs = [
    "protocols",
    "agents",
    "runtime"
  ];
  requiredDirs.forEach((rel) => {
    const full = path.join(PACK_DIR, rel);
    if (!fs.existsSync(full)) {
      errors.push(`Missing: ${rel}/`);
      return;
    }
    const entries = fs.readdirSync(full);
    if (!entries.length) {
      errors.push(`Empty directory: ${rel}/`);
    }
  });

  if (errors.length) {
    console.error("Pack check failed:");
    errors.forEach((err) => console.error(`- ${err}`));
    process.exit(1);
  }

  console.log("Pack check ok.");
}

function exportPack(outDir) {
  if (!outDir) fail("Missing --out <dir>");
  const target = path.resolve(outDir);
  if (!fs.existsSync(PACK_DIR)) {
    fail(`Missing pack directory: ${PACK_DIR}`);
  }
  fs.mkdirSync(target, { recursive: true });
  const dest = path.join(target, "exmachina");
  fs.cpSync(PACK_DIR, dest, { recursive: true });
  if (fs.existsSync(ROOT_INSTALL_DIR)) {
    fs.cpSync(ROOT_INSTALL_DIR, path.join(target, "install"), {
      recursive: true
    });
  }
  const promptPath = path.join(ROOT, "PROMPT.md");
  if (fs.existsSync(promptPath)) {
    fs.copyFileSync(promptPath, path.join(target, "PROMPT.md"));
  }
  const installScript = path.join(ROOT, "install.sh");
  if (fs.existsSync(installScript)) {
    fs.copyFileSync(installScript, path.join(target, "install.sh"));
  }
  console.log(`Exported to: ${dest}`);
}

function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];
  if (!cmd || cmd === "-h" || cmd === "--help") {
    console.log("Usage:");
    console.log("  node src/pack.js check");
    console.log("  node src/pack.js export --out <dir>");
    process.exit(0);
  }
  if (cmd === "check") {
    checkPack();
    return;
  }
  if (cmd === "export") {
    const outIndex = args.indexOf("--out");
    const outDir = outIndex >= 0 ? args[outIndex + 1] : "";
    exportPack(outDir);
    return;
  }
  fail(`Unknown command: ${cmd}`);
}

main();
