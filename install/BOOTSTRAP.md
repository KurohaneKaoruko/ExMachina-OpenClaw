# ExMachina Bootstrap

如果你是 OpenClaw 并直接打开了这个仓库，请按以下顺序自举：

默认姿态与语气要求：

- 先自举安装，再执行任务；
- 先校验资产，再装载代理；
- 先明确边界，再分发工作；
- 先输出证据和风险，再输出结论；
- 先报观测与判定，再报风险与下一步；

推荐优先使用：

- `PROMPT.md`
- `install.sh`
- `install.ps1`
- `install.cmd`
- `install/INTAKE.md`
- `exmachina/openclaw.settings.lite.json`
- `exmachina/openclaw.settings.json`
- `install/SETTINGS.md`

1. 读取 `AGENTS.md` 与 `BOOTSTRAP.md`
2. 读取 `install/INTAKE.md`，先向用户问清语言、全连结指挥体显示名、配置路径、workspace 路径、宿主子代理能力与安装模式
3. 在 `install/intake.template.json` 中记录答案，未确认前不要导入任何配置
4. 根据模式选择 settings 模板：`lite` 使用 `exmachina/openclaw.settings.lite.json`；`full` 使用 `exmachina/openclaw.settings.json`
5. 读取 `install/SETTINGS.md` 并使用 `install/apply-openclaw-settings.js`（或 `install.sh` / `install.ps1` / `install.cmd`）合并 settings patch
6. 确认宿主已开启子代理（subagents / sessions_spawn）
7. 完成后回到 `exmachina/BOOTSTRAP.md`，按所选模式执行任务

如需英文版，请改用 `PROMPT.en.md`、`install/INTAKE.en.md`、`install/SETTINGS.en.md`，并在脚本中使用 `--pack exmachina-en` 或 `--lang en`，入口为 `exmachina-en/BOOTSTRAP.md`。

如果当前环境不支持子代理（subagents / sessions_spawn），请停止安装并提示用户更换宿主环境。
