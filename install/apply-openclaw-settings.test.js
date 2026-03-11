const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { applySettings } = require("./apply-openclaw-settings");

function readJson(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  const text = raw.replace(/^\uFEFF/, "");
  return JSON.parse(text);
}

const fixturesDir = path.join(__dirname, "fixtures");
const settings = readJson(path.join(fixturesDir, "settings.sample.json"));
const intakeBase = readJson(path.join(fixturesDir, "intake.sample.json"));
const config = readJson(path.join(fixturesDir, "openclaw.sample.json"));

const packRoot = path.resolve(__dirname, "..");
const intake = {
  ...intakeBase,
  workspace_root: packRoot
};

const { config: merged } = applySettings({
  config,
  settings,
  intake,
  packRoot,
  mode: "full"
});

const list = merged.agents.list;
const main = list.find((agent) => agent.id === "exmachina-main");
assert(main, "exmachina-main should exist");
assert.strictEqual(main.default, true, "exmachina-main should be default");
assert.strictEqual(main.name, "ExMachina Controller", "conductor name should be applied");
assert.strictEqual(main.workspace, packRoot, "workspace should be normalized");
assert.strictEqual(main.identity.theme, "Install language: en-US", "template variables should be applied");

const support = list.find((agent) => agent.id === "exmachina-link-security");
assert(support, "exmachina-link-security should exist");
assert.strictEqual(support.default, false, "support agent should not be default");
assert.strictEqual(support.identity.theme, "New security body", "support theme should be updated");

assert.strictEqual(merged.default_entry_agent_id, "exmachina-main", "default entry id should be updated");
assert.strictEqual(merged.default_agent, "agent:exmachina-main", "default_agent should be updated");
assert.strictEqual(
  merged.agents.defaults.subagents.maxSpawnDepth,
  2,
  "agents.defaults.subagents should be merged"
);

console.log("apply-openclaw-settings.test.js: ok");

const mapConfig = {
  default_agent: "agent:exmachina-security",
  agents: {
    legacy: {
      id: "legacy",
      name: "Legacy Agent",
      default: true
    }
  }
};

const { config: mergedMap } = applySettings({
  config: mapConfig,
  settings,
  intake,
  packRoot,
  mode: "full"
});

assert(mergedMap.agents["exmachina-main"], "map container should include exmachina-main");
assert.strictEqual(
  mergedMap.agents["exmachina-main"].default,
  true,
  "exmachina-main should be default in map container"
);
assert.strictEqual(
  mergedMap.default_agent,
  "agent:exmachina-main",
  "default_agent should be updated in map container"
);
assert.strictEqual(
  mergedMap.agents.defaults.subagents.maxSpawnDepth,
  2,
  "agents.defaults.subagents should be merged in map container"
);

