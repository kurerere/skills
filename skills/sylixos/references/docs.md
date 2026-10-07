# 手册检索

先按问题选择资料，不同时加载所有产品手册。`<DATA_ROOT>` 定义见主入口，产品资料不随公开技能分发。

| 问题 | 资料目录 | 旧目录回退（首选目录不存在时） |
| --- | --- | --- |
| SylixOS 编程、内核 API 与 Shell 命令 | `<DATA_ROOT>/sylixos-usage/programming` | `<DATA_ROOT>/sylixos-docs/references` |
| SylixOS 环境、文件系统、磁盘、网络、用户与资源配置 | `<DATA_ROOT>/sylixos-usage/system` | `<DATA_ROOT>/sylixos-sysusage/references` |
| ECS 容器、镜像、网络与隔离 | `<DATA_ROOT>/ecs-docs/references` | 无 |
| JSRE 接口与示例 | `<DATA_ROOT>/jsre-api/references` | 无 |
| VSOA 服务、RPC、发布订阅与语言 API | `<DATA_ROOT>/vsoa-docs/references` | 无 |
| Armory 使用、配置、包管理与 API | `<DATA_ROOT>/armory-usage/references` | `<DATA_ROOT>/armory-docs/references` |

先确认目录存在，通过对应 sitemap.md 或 rg 搜索问题关键词，只读相关章节。跨产品问题分别查询，保留各自版本与限制，不把不同版本拼成统一结论。

回答保留原资料的参数、返回值、条件与示例，注明来源章节和版本；版本未知时说明。资料与当前 SDK 或输出不同，记录差异，不仅凭手册认定当前环境支持某功能。

缺少资料时说明缺失。可用已配置的 RAG MCP 或产品官方文档补充，并交代适用边界；不预设知识库、不编造章节、不批量复制手册到公开仓库。整理或更新用户已有资料须在任务范围内。
