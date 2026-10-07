# Node Armory 脚本布局参考

这是旧 Node 工程的入口记录，只有当前项目仍提供这些脚本时使用。具体参数、输出路径、支持架构与执行顺序须读当前脚本，不承诺历史默认值或文件大小。

| 项目脚本 | 调查用途 |
| --- | --- |
| scripts/armory/release-check-version.sh | 版本、元数据和标签冲突检查 |
| scripts/armory/release-bump-version.sh | 版本变更及其文件范围 |
| scripts/armory/armory-package.sh | strip、归档、解包检查与元数据生成 |
| scripts/armory/armory-publish.sh | 发布入口、配置修改和失败处理 |
| scripts/armory/release.sh | 组合流程；检查是否自动提交、创建标签或发布 |
| scripts/sylixos/build.sh | 当前工程的构建入口之一，先核对项目约定 |

项目若提供 docs/agents/sylixos-build-verification.md 和目标测试指南，按其检查当前产物。Node 版本输出只覆盖加载与启动，仍需与本次改动相关的功能验证。
