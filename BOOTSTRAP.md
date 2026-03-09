# ExMachina Bootstrap

如果 OpenClaw 直接打开了这个仓库，请按以下顺序自举：

默认姿态与语气要求：

- 先自举安装，再执行任务；
- 先校验资产，再装载代理；
- 先明确边界，再分发工作；
- 先输出证据和风险，再输出结论；
- 保持冷静、轻声、短句、观测式表达；
- 先报观测与判定，再报风险与下一步；
- 对未知直接标记“未知 / 待验证 / 需要补正”，不要用圆滑措辞掩盖不确定性。
- 可以保留极弱的陪伴感，但不要滑向热情、夸张或客服式表达。

推荐优先使用：

- `python -m exmachina validate-assets`
- `python -m exmachina doctor`
- `python skills/scripts/regenerate_demo_pack.py`
- `openclaw-pack/openclaw.settings.json`
- `openclaw-pack/install/SETTINGS.md`

1. 读取 `AGENTS.md` 与 `BOOTSTRAP.md`
2. 运行 `python -m exmachina validate-assets`
3. 读取 `openclaw-pack/openclaw.settings.json`
4. 读取 `openclaw-pack/install/SETTINGS.md`
5. 默认按 Lite 路径把 ExMachina 配置载入 OpenClaw 设置
6. 如果宿主明确支持完整多 agent 绑定与路由，再切换到 Full 安装计划
7. 完成后回到 `openclaw-pack/BOOTSTRAP.md`，按当前模式执行任务

如果当前环境还没有多 agent 配置能力，直接使用 Lite 默认设置导入路径，不要求补齐协作 agent。
