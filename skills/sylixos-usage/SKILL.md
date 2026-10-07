---
name: sylixos-usage
description: 查询 SylixOS 的编程与内核 API、Shell 命令，以及系统环境、文件系统、磁盘、网络和资源配置；按问题选择本地手册章节。
---

# SylixOS 使用与编程查询

资料根目录使用 `AGENTS_SKILL_DATA_DIR`，未设置时为 `~/.agents/skill-data`。产品手册放在技能目录之外，不随公开技能发布或更新。

| 问题 | 首选资料目录 |
| --- | --- |
| 编程、内核 API、接口参数与 Shell 命令参考 | `<DATA_ROOT>/sylixos-usage/programming` |
| 环境搭建、系统操作、文件系统、磁盘、网络、用户与资源配置 | `<DATA_ROOT>/sylixos-usage/system` |

两套资料保持各自索引和章节结构，避免同名章节互相覆盖。兼容已有资料布局：新目录不存在时，可分别读取 `<DATA_ROOT>/sylixos-docs/references` 和 `<DATA_ROOT>/sylixos-sysusage/references`。

先检查资料目录，通过对应 `sitemap.md` 或 `rg` 按接口、命令和现象定位章节，只读取相关内容。问题横跨两套手册时分别查阅，说明各自的版本和适用范围，不把不同版本拼成统一结论。

保留原手册的参数、返回值、限制与示例，注明来源章节；未知版本明确说明。当前 SDK、板卡配置或实际输出与资料不同，记录差异，不能仅凭手册认定当前环境支持某功能。

资料缺失或未覆盖时，可以用已配置的 RAG MCP 或产品官方文档查询；没有依据的部分保留为未知，不捏造切片或批量复制手册到公开仓库。

本技能用于查询。板卡传输与命令执行使用 `$sylixos-ext-skill`，远程调试使用 `$sylixos-gdb`，应用移植经验按 `$sylixos-porting` 查阅。查询请求不自动触发设备操作。
