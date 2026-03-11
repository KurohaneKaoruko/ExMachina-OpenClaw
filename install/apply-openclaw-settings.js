#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const os = require("os");

const ROOT_DIR = path.resolve(__dirname, "..");
const INSTALL_DIR = path.join(ROOT_DIR, "install");

function fail(message) {
  console.error(message);
  process.exit(1);
}

function readJson(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  const text = raw.replace(/^\uFEFF/, "");
  return JSON.parse(text);
}

function writeJson(filePath, data) {
  const text = JSON.stringify(data, null, 2) + "\n";
  fs.writeFileSync(filePath, text, "utf8");
}

function expandHome(inputPath) {
  if (!inputPath || typeof inputPath !== "string") return inputPath;
  if (!inputPath.startsWith("~")) return inputPath;
  const home = os.homedir();
  if (inputPath === "~") return home;
  const trimmed = inputPath.slice(1);
  return path.join(home, trimmed.replace(/^[/\\]/, ""));
}

function normalizePath(inputPath, baseDir) {
  if (!inputPath) return inputPath;
  const expanded = expandHome(inputPath);
  if (!expanded) return expanded;
  if (path.isAbsolute(expanded)) return expanded;
  return path.resolve(baseDir, expanded);
}

function isPlaceholder(value) {
  return typeof value === "string" && value.includes("{{") && value.includes("}}");
}

function resolvePackOptions(packArg, langArg) {
  let packName = packArg || "exmachina";
  let langSuffix = "";

  if (langArg) {
    if (langArg === "en" || langArg === "en-US" || langArg === "en_US") {
      langSuffix = ".en";
      if (!packArg) packName = "exmachina-en";
    }
  }

  if (!langSuffix && packName.endsWith("-en")) {
    langSuffix = ".en";
  }

  return { packName, langSuffix };
}

function parseArgs(args) {
  const options = {
    mode: "",
    pack: "",
    lang: "",
    intake: "",
    target: "",
    dryRun: false,
    noBackup: false,
    allowMissing: false,
    help: false
  };

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    switch (arg) {
      case "--mode":
        options.mode = args[i + 1] || "";
        i += 1;
        break;
      case "--pack":
        options.pack = args[i + 1] || "";
        i += 1;
        break;
      case "--lang":
        options.lang = args[i + 1] || "";
        i += 1;
        break;
      case "--intake":
        options.intake = args[i + 1] || "";
        i += 1;
        break;
      case "--target":
        options.target = args[i + 1] || "";
        i += 1;
        break;
      case "--dry-run":
      case "--dryrun":
      case "--dry":
        options.dryRun = true;
        break;
      case "--no-backup":
        options.noBackup = true;
        break;
      case "--allow-missing":
        options.allowMissing = true;
        break;
      case "-h":
      case "--help":
        options.help = true;
        break;
      default:
        if (!arg.startsWith("-") && !options.target) {
          options.target = arg;
        }
        break;
    }
  }

  return options;
}

function applyTemplate(value, map) {
  if (typeof value === "string") {
    return value.replace(/\{\{\s*([A-Z0-9_]+)\s*\}\}/g, (match, key) => {
      if (Object.prototype.hasOwnProperty.call(map, key)) {
        return String(map[key]);
      }
      return match;
    });
  }
  if (Array.isArray(value)) {
    return value.map((item) => applyTemplate(item, map));
  }
  if (value && typeof value === "object") {
    const out = {};
    Object.entries(value).forEach(([key, val]) => {
      out[key] = applyTemplate(val, map);
    });
    return out;
  }
  return value;
}

function mergeObjects(base, override) {
  if (!base) return override;
  if (!override) return base;
  if (Array.isArray(base) || Array.isArray(override)) {
    return override;
  }
  if (typeof base !== "object" || typeof override !== "object") {
    return override;
  }
  const result = { ...base };
  Object.entries(override).forEach(([key, value]) => {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      result[key] = mergeObjects(base[key], value);
    } else {
      result[key] = value;
    }
  });
  return result;
}

function resolveAgentContainer(config) {
  if (Array.isArray(config.agents)) {
    return { type: "agents-array", list: config.agents, setList: (list) => { config.agents = list; } };
  }
  if (config.agents && Array.isArray(config.agents.list)) {
    return { type: "agents.list", list: config.agents.list, setList: (list) => { config.agents.list = list; } };
  }
  if (config.agents && Array.isArray(config.agents.entries)) {
    return { type: "agents.entries", list: config.agents.entries, setList: (list) => { config.agents.entries = list; } };
  }
  if (Array.isArray(config.agent_list)) {
    return { type: "agent_list", list: config.agent_list, setList: (list) => { config.agent_list = list; } };
  }
  if (Array.isArray(config.agentList)) {
    return { type: "agentList", list: config.agentList, setList: (list) => { config.agentList = list; } };
  }
  if (config.agents && typeof config.agents === "object" && !Array.isArray(config.agents)) {
    const entries = Object.entries(config.agents).filter(([key, value]) => {
      if (key === "list" || key === "entries") return false;
      return value && typeof value === "object" && (value.id || value.name);
    });
    if (entries.length) {
      return { type: "agents-map", map: config.agents, setMap: (map) => { config.agents = map; } };
    }
  }
  if (!config.agents || typeof config.agents !== "object" || Array.isArray(config.agents)) {
    config.agents = {};
  }
  config.agents.list = Array.isArray(config.agents.list) ? config.agents.list : [];
  return { type: "agents.list", list: config.agents.list, setList: (list) => { config.agents.list = list; } };
}

function applySettings({ config, settings, intake, packRoot, mode }) {
  if (!settings || typeof settings !== "object") {
    throw new Error("Missing settings content.");
  }
  if (!intake || typeof intake !== "object") {
    throw new Error("Missing intake content.");
  }

  const templateVars = settings.template_variables || {};
  const defaults = {
    OPENCLAW_INSTALL_LANGUAGE: templateVars.OPENCLAW_INSTALL_LANGUAGE?.default || "zh-CN",
    OPENCLAW_CONDUCTOR_NAME: templateVars.OPENCLAW_CONDUCTOR_NAME?.default || "ExMachina Controller",
    EXMACHINA_PACK_ROOT: templateVars.EXMACHINA_PACK_ROOT?.default || packRoot
  };

  const installLanguage = !isPlaceholder(intake.install_language)
    ? (intake.install_language || defaults.OPENCLAW_INSTALL_LANGUAGE)
    : defaults.OPENCLAW_INSTALL_LANGUAGE;
  const conductorName = !isPlaceholder(intake.conductor_name)
    ? (intake.conductor_name || defaults.OPENCLAW_CONDUCTOR_NAME)
    : defaults.OPENCLAW_CONDUCTOR_NAME;

  let workspaceRoot = intake.workspace_root || defaults.EXMACHINA_PACK_ROOT;
  if (isPlaceholder(workspaceRoot)) {
    workspaceRoot = packRoot;
  }

  const templateMap = {
    OPENCLAW_INSTALL_LANGUAGE: installLanguage,
    OPENCLAW_CONDUCTOR_NAME: conductorName,
    EXMACHINA_PACK_ROOT: workspaceRoot
  };

  const settingsPatch = settings?.settings_patch || {};
  const templatedPatch = applyTemplate(settingsPatch, templateMap);
  const patchAgents = templatedPatch?.agents?.list;
  if (!Array.isArray(patchAgents) || patchAgents.length === 0) {
    throw new Error("Settings patch does not include agents list.");
  }

  if (templatedPatch && typeof templatedPatch === "object") {
    const patchAgentsContainer = templatedPatch.agents;
    if (patchAgentsContainer && typeof patchAgentsContainer === "object") {
      const { list, entries, ...agentMeta } = patchAgentsContainer;
      if (Object.keys(agentMeta).length) {
        if (Array.isArray(config.agents)) {
          config.agents = { list: config.agents };
        } else if (!config.agents || typeof config.agents !== "object") {
          config.agents = {};
        }
        config.agents = mergeObjects(config.agents, agentMeta);
      }
    }
    const patchTop = { ...templatedPatch };
    delete patchTop.agents;
    if (Object.keys(patchTop).length) {
      config = mergeObjects(config, patchTop);
    }
  }

  const newAgents = patchAgents.map((agent) => {
    if (agent && typeof agent === "object" && agent.id && agent.id.startsWith("exmachina-")) {
      return { ...agent, workspace: workspaceRoot };
    }
    return agent;
  });

  const container = resolveAgentContainer(config);
  let added = 0;
  let updated = 0;
  let total = 0;

  if (container.map) {
    newAgents.forEach((agent) => {
      if (!agent || !agent.id) return;
      const existing = container.map[agent.id];
      if (existing) {
        container.map[agent.id] = mergeObjects(existing, agent);
        updated += 1;
      } else {
        container.map[agent.id] = agent;
        added += 1;
      }
    });
    Object.values(container.map).forEach((agent) => {
      if (!agent || !agent.id || !agent.id.startsWith("exmachina-")) return;
      if (agent.id === "exmachina-main") {
        agent.default = true;
        return;
      }
      if (agent.default === true) {
        agent.default = false;
      }
    });
    total = Object.values(container.map).filter((agent) => agent && agent.id).length;
    container.setMap(container.map);
  } else {
    const list = container.list;
    const indexById = new Map();
    list.forEach((agent, index) => {
      if (agent && agent.id) {
        indexById.set(agent.id, index);
      }
    });
    newAgents.forEach((agent) => {
      if (!agent || !agent.id) return;
      const existingIndex = indexById.get(agent.id);
      if (existingIndex === undefined) {
        list.push(agent);
        indexById.set(agent.id, list.length - 1);
        added += 1;
        return;
      }
      const existing = list[existingIndex];
      const merged = mergeObjects(existing, agent);
      list[existingIndex] = merged;
      updated += 1;
    });
    list.forEach((agent) => {
      if (!agent || !agent.id || !agent.id.startsWith("exmachina-")) return;
      if (agent.id === "exmachina-main") {
        agent.default = true;
        return;
      }
      if (agent.default === true) {
        agent.default = false;
      }
    });
    total = list.length;
    container.setList(list);
  }

  if (Object.prototype.hasOwnProperty.call(config, "default_entry_agent_id")) {
    config.default_entry_agent_id = "exmachina-main";
  }
  if (Object.prototype.hasOwnProperty.call(config, "default_agent_id")) {
    config.default_agent_id = "exmachina-main";
  }
  if (Object.prototype.hasOwnProperty.call(config, "defaultAgentId")) {
    config.defaultAgentId = "exmachina-main";
  }
  if (Object.prototype.hasOwnProperty.call(config, "default_agent")) {
    const current = config.default_agent;
    if (typeof current === "string" && current.startsWith("agent:")) {
      config.default_agent = "agent:exmachina-main";
    } else {
      config.default_agent = "exmachina-main";
    }
  }

  return {
    config,
    report: {
      added,
      updated,
      total,
      mode,
      container: container.type
    }
  };
}

function ensureRequiredValue(value, label) {
  if (!value || isPlaceholder(value)) {
    fail(`Missing required value: ${label}. Update intake file first.`);
  }
}

function createBackupPath(targetPath) {
  const base = `${targetPath}.exmachina.bak`;
  if (!fs.existsSync(base)) return base;
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  return `${targetPath}.exmachina.${stamp}.bak`;
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log("Usage:");
    console.log("  node install/apply-openclaw-settings.js --mode lite|full --pack exmachina|exmachina-en --lang zh|en --intake <path> --target <openclaw-config>");
    console.log("  node install/apply-openclaw-settings.js --mode full --pack exmachina --target ~/.openclaw/openclaw.json");
    console.log("");
    console.log("Options:");
    console.log("  --dry-run        Print summary without writing the file");
    console.log("  --no-backup      Skip backup creation");
    console.log("  --allow-missing  Create a minimal config if the target does not exist");
    process.exit(0);
  }

  const { packName, langSuffix } = resolvePackOptions(options.pack, options.lang);
  const packRoot = path.join(ROOT_DIR, packName);
  if (!fs.existsSync(packRoot)) {
    fail(`Missing pack directory: ${packRoot}`);
  }

  const intakePath = options.intake || path.join(INSTALL_DIR, `intake.template${langSuffix}.json`);
  if (!fs.existsSync(intakePath)) {
    fail(`Missing intake file: ${intakePath}`);
  }

  const intake = readJson(intakePath);

  const mode = options.mode || intake.install_mode || "full";
  if (mode !== "lite" && mode !== "full") {
    fail(`Unknown mode: ${mode}`);
  }
  if (options.mode && intake.install_mode && intake.install_mode !== mode) {
    console.warn(`Warning: intake mode is ${intake.install_mode}, but CLI mode is ${mode}. Using CLI mode.`);
  }

  if (intake.host_supports_multi_agent === false) {
    fail("Host does not support subagents (sessions_spawn). Aborting.");
  }

  const settingsFile = path.join(packRoot, mode === "lite" ? "openclaw.settings.lite.json" : "openclaw.settings.json");
  if (!fs.existsSync(settingsFile)) {
    fail(`Missing settings file: ${settingsFile}`);
  }

  const settings = readJson(settingsFile);

  const targetPathRaw = options.target || intake.target_config_path;
  ensureRequiredValue(targetPathRaw, "target_config_path");

  const workspaceRaw = intake.workspace_root || settings?.template_variables?.EXMACHINA_PACK_ROOT?.default || packRoot;
  const workspaceRoot = normalizePath(isPlaceholder(workspaceRaw) ? packRoot : workspaceRaw, ROOT_DIR);
  ensureRequiredValue(workspaceRoot, "workspace_root");

  const conductorNameRaw = intake.conductor_name || settings?.template_variables?.OPENCLAW_CONDUCTOR_NAME?.default;
  ensureRequiredValue(conductorNameRaw, "conductor_name");
  const installLanguageRaw = intake.install_language || settings?.template_variables?.OPENCLAW_INSTALL_LANGUAGE?.default || "zh-CN";
  ensureRequiredValue(installLanguageRaw, "install_language");

  const targetPath = normalizePath(targetPathRaw, ROOT_DIR);
  if (!fs.existsSync(targetPath)) {
    if (!options.allowMissing) {
      fail(`Target config not found: ${targetPath}. Use --allow-missing to create a minimal config.`);
    }
  }

  const config = fs.existsSync(targetPath) ? readJson(targetPath) : {};

  const { config: merged, report } = applySettings({
    config,
    settings,
    intake: {
      ...intake,
      workspace_root: workspaceRoot,
      conductor_name: conductorNameRaw,
      install_language: installLanguageRaw
    },
    packRoot: workspaceRoot,
    mode
  });

  console.log("ExMachina settings apply summary:");
  console.log(`- Mode: ${mode}`);
  console.log(`- Pack: ${packName}`);
  console.log(`- Target: ${targetPath}`);
  console.log(`- Agents added: ${report.added}`);
  console.log(`- Agents updated: ${report.updated}`);
  console.log(`- Agent total: ${report.total}`);
  if (report.container) {
    console.log(`- Agent container: ${report.container}`);
  }

  if (options.dryRun) {
    console.log("Dry run: no file written.");
    return;
  }

  const targetDir = path.dirname(targetPath);
  if (targetDir) {
    fs.mkdirSync(targetDir, { recursive: true });
  }

  if (fs.existsSync(targetPath) && !options.noBackup) {
    const backupPath = createBackupPath(targetPath);
    fs.copyFileSync(targetPath, backupPath);
    console.log(`Backup created: ${backupPath}`);
  }

  writeJson(targetPath, merged);
  console.log(`Updated OpenClaw config: ${targetPath}`);
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    fail(error?.message || String(error));
  }
}

module.exports = {
  applySettings,
  applyTemplate,
  resolveAgentContainer
};
