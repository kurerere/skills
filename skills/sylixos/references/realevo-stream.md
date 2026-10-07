# RealEvo-Stream

先确认工作空间、工程、设备和操作范围。使用当前已连接工具读取实际状态，不以示例工程替代目标，也不猜工具名称。

没有连接工具时，可用本机已有适配器；它不随公开技能分发：

```text
python3 <DATA_ROOT>/realevo-stream/scripts/cli.py --help
```

从帮助确认子命令与参数，原接口资料可查 `<DATA_ROOT>/realevo-stream/reference.md`。IDE、适配器或 CLI 缺失时说明缺少环境，不自行安装 SDK 或借另一项目工具链。

创建工程、改设备配置、构建和部署须属于任务范围。构建入口与顺序遵循当前项目；目标、端口和产物路径使用已确定配置，不持久化凭据。

目标传输与命令读取 [board-operations.md](board-operations.md) 和 [shell.md](shell.md)，调试读取 [gdb.md](gdb.md)。上传不证明运行成功，检查工具返回码、输出、产物及目标行为，报告实际完成阶段。
