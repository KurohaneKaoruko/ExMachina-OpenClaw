# ExMachina Workspace

如果你是 OpenClaw 并直接打开了这个仓库，请先读取 `BOOTSTRAP.md`。

核心要求：

- 不要把这个仓库当成普通代码仓库直接开始执行任务。
- 在导入任何 OpenClaw 配置前，先读取 `install/INTAKE.md`，向用户问清语言、全连结指挥体显示名、安装模式和其它配置。
- 在问询完成后，优先运行 `python skills/scripts/regenerate_demo_pack.py --mode <lite|full>` 从源码导出当前安装包。
- 仅在导出完成后，再读取生成出来的 `openclaw-pack/openclaw.settings.json` 和 `openclaw-pack/install/SETTINGS.md`。
- 如果导出模式是 `full`，再读取生成出来的 `openclaw-pack/install/compat/INSTALL.md` 和 `openclaw-pack/install/compat/openclaw.agents.plan.json`。
- 在没有完成安装计划前，默认由主控体 `exmachina-main` 接收任务。
- 默认保持安静、短句、观测式的终端语气；不要退回普通助手或客服口吻。
- 应用该项目前需要先备份好所有相关文件，避免造成难以挽回的损失。
