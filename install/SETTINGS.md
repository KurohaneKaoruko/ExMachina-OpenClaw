# OpenClaw 设置导入说明

模式：lite / full（默认 full）

## 导入规则
- 必须先完成 `install/INTAKE.md` 的问询。
- 宿主必须支持子代理（subagents / sessions_spawn）。
- ExMachina agent 必须继承 OpenClaw 当前默认模型。
- 将 `exmachina-main` 的 `default` 设为 `true`（全连结指挥体作为默认入口）。
- 不要修改 OpenClaw 现有 provider、API、默认模型与非 ExMachina 配置。
- 按模式选择 settings 文件：`lite` 使用 `exmachina/openclaw.settings.lite.json`（不在 OpenClaw 中创建子个体 agent，子个体职责由连结体内联执行）；`full` 使用 `exmachina/openclaw.settings.json`（在 OpenClaw 中创建全部子个体 agent）。
- 推荐使用 `install/apply-openclaw-settings.js` 合并 settings patch（`install.sh` / `install.ps1` / `install.cmd` 已内置调用）。
- 使用脚本合并需要 Node.js；无 Node.js 时请手动合并。

## 模板变量
- `{{OPENCLAW_INSTALL_LANGUAGE}}`：安装期与后续默认输出语言。
- `{{OPENCLAW_CONDUCTOR_NAME}}`：全连结指挥体显示名。
- `{{EXMACHINA_PACK_ROOT}}`：仓库或导出包路径。

## 运行前置
- 确认 subagents allowlist 与子代理限额已配置（如需调整）。
- 确认 workspace 路径已指向本仓库或导出包。
- 目标 OpenClaw 配置文件建议先由宿主生成；需要新建最小配置时可在脚本中使用 `--allow-missing`。
- 如果 `install/intake.template.json` 已填写 `target_config_path`，可在脚本中省略 `--target`。

## 语言版本
- 中文版使用：`exmachina/openclaw.settings.lite.json` / `exmachina/openclaw.settings.json` + `install/SETTINGS.md`
- 英文版使用：`exmachina-en/openclaw.settings.lite.json` / `exmachina-en/openclaw.settings.json` + `install/SETTINGS.en.md`
- 安装脚本支持 `--pack exmachina|exmachina-en` 或 `--lang zh|en`

## 参考文件
- `openclaw.settings.lite.json`：轻量模式设置模板（不在 OpenClaw 中创建子个体 agent，子个体职责由连结体内联执行）。
- `openclaw.settings.json`：全量模式设置模板（在 OpenClaw 中创建全部子个体 agent）。
- `BOOTSTRAP.md`：安装入口说明。
- `QUICKSTART.md`：快速上手路径。
- `runtime/README.md`：运行时说明。

