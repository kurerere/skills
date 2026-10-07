---
name: realevo-stream
description: 操作已配置的 RealEvo-Stream 工作空间、工程、设备、构建与部署；优先使用当前环境提供的工具，保留用户的目标配置和项目构建约定。
---

# RealEvo-Stream

先确认当前任务对应的工作空间、工程和操作范围。使用已连接的 RealEvo-Stream 工具获取实际状态；不能把示例工程或其他项目当作当前目标。

没有连接工具时，可以使用本机已有的命令行适配器。它不随公开技能分发，路径为 `<DATA_ROOT>/realevo-stream/scripts/cli.py`；`DATA_ROOT` 使用 `AGENTS_SKILL_DATA_DIR`，未设置时为 `~/.agents/skill-data`。

```text
python3 <DATA_ROOT>/realevo-stream/scripts/cli.py --help
```

从帮助中确认实际支持的子命令及参数，不猜工具名称。CLI 或 IDE 不存在时，说明缺少的环境；不要临时安装 SDK 或改用其他项目的工具链。

- 查询与配置分开处理。创建、安装、修改设备、构建或部署必须属于当前任务范围。
- 构建入口和执行顺序以项目 `AGENTS.md`、Makefile 或已有工程配置为准。
- 目标地址、端口、账号和产物路径从本次任务或当前项目配置读取，不持久化凭据。
- 获取实际工具结果，检查返回码、输出和预期产物。上传成功不能代替目标程序运行验证。
- SylixOS 目标命令与传输遵循 `$sylixos-ext-skill`；远程调试按 `$sylixos-gdb` 执行。

需要原接口说明时读取本机 `<DATA_ROOT>/realevo-stream/reference.md`，按需查看相关命令。交付时报告实际执行的操作、结果和仍缺少的环境或验证。
