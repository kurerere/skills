# 来源与整理说明

个人技能整理自全局安装，以及 `_mksh`、`ecsd++`、`ecsd2`、`sbase`、`cmd_relic`、Node 等工作区中的自定义内容。

- `sylixos` 合并原 `ecs-docs`、`jsre-api`、`sylixos-usage`、`vsoa-docs`、`realevo-stream`、`sylixos-ext-skill`、`sylixos-gdb`、`sylixos-porting`、`armory-usage`。主入口路由到专项参考，FTP/Telnet 自写脚本原样迁移。
- 底层 SylixOS、ECS、JSRE、VSOA、Armory 手册，以及 RealEvo 原适配器不进入公开仓库，原本地资料目录和许可信息保留。
- Node/V8/libuv 和 sbase/cmd_relic 的移植记录缺少随包发布的完整版本与原始验证资料，作为历史调查线索维护；不能据此声称当前方案已验证。
- GDB、Shell 和 Armory 的项目特例改为有条件的参考。当前项目负责目标地址、架构、构建命令、产物布局与验收标准。
- 中文提交技能采用个人 `commit`，尊重用户已选暂存范围；不保留旧技能的模型署名或固定正文要求。
- `coding` 以本地 `solid` 为底稿，按行为变更、缺陷修复、重构和领域规则重组。TDD 与 DDD 的外部来源见 [TDD 参考](skills/coding/references/tdd.md) 和 [DDD 参考](skills/coding/references/ddd.md)。
- 需求完善技能 `features-full` 改名为 `refine-requirements`，保持手动调用，在 `.requirements/REQ-<主题>.md` 维护主干意图、使用者与边界，细化需求由代码与测试承载；不自动展开设计、任务与验证文档。
- 文档技能 `tech-docs`（原 `evidence-first-docs`）起于一次昇腾 310B CRI/CDI 挂载手册的三轮返工。保留事实有据、读者能执行和交付自查的意图，按文档类型选择内容，不把当时的步骤与骨架作为固定流程。
- 写作技能 `writing` 与 `tech-docs` 分工：前者管准确、具体、自然的表达，后者管工程依据与读者任务。早期规则来自已发表文章与自造词较多稿件的比较；现保留“表达有落点、润色不改事实”的意图，词频和扫描只作提示，不用固定白名单代替语境判断。

Matt、飞书、Impeccable、Archify、shadcn 等第三方原版继续从原来源安装，不重复发布。`rag-smart-qa` 来源为本地 Hermes（AcoPilot 内置）技能库，不在本仓库维护，已安装的全局版本保留。

文档入口经 AcoHub MCP 与本地切片抽样比较后采用在线优先、本地回退。在线覆盖更广，部分精确 API 查询仍依赖本地；知识库原文和对比片段不进入公开仓库。
