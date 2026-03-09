# ExMachina Bootstrap

如果 OpenClaw 直接打开了这个仓库，请按以下顺序自举：

1. 读取 `AGENTS.md`、`SOUL.md`、`TOOLS.md`
2. 运行 `python -m exmachina validate-assets`
3. 读取 `openclaw-pack/install/INSTALL.md`
4. 读取 `openclaw-pack/install/openclaw.agents.plan.json`
5. 默认按 Lite 路径装配 `exmachina-main` 单 agent 入口
6. 如果宿主明确支持完整多 agent 绑定与路由，再切换到 Full 安装计划
7. 完成后回到 `openclaw-pack/BOOTSTRAP.md`，按当前模式执行任务

如果当前环境还没有多 agent 配置能力，直接使用 Lite 默认路径，不要求补齐协作 agent。
