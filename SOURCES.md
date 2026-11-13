# 来源与资料边界

个人技能整理自全局安装，以及 `_mksh`、`ecsd++`、`ecsd2`、`sbase`、`cmd_relic`、Node 等工作区中的自定义内容。

- `sylixos` 合并原 `ecs-docs`、`jsre-api`、`sylixos-usage`、`vsoa-docs`、`realevo-stream`、`sylixos-ext-skill`、`sylixos-gdb`、`sylixos-porting`、`armory-usage`。FTP/Telnet 脚本由原技能迁入，后续在本仓库维护。
- 底层 SylixOS、ECS、JSRE、VSOA、Armory 手册，以及 RealEvo 原适配器不进入公开仓库，原本地资料目录和许可信息保留。
- Node/V8/libuv 和 sbase/cmd_relic 的移植记录缺少随包发布的完整版本与原始验证资料，作为历史调查线索维护；不能据此声称当前方案已验证。
- GDB、Shell 和 Armory 中的项目特例作为有条件的参考保留，不是通用默认值。
- `commit` 合并原 `git-commit`、`ecsd-commit`；`refine-requirements` 原名 `features-full`；`slim-docs` 原名 `slim`。名称变化不代表安装器会自动删除旧入口。
- `coding` 以本地 `solid` 为底稿；外部来源见 [TDD 参考](skills/coding/references/tdd.md) 和 [DDD 参考](skills/coding/references/ddd.md)。
- `slim-code` 根据代码简化技能调研重新组织：读者负担与数据表示参考 [pstack](https://github.com/cursor/plugins/tree/main/pstack/skills)，消融方法参考 [antfu-simplify](https://github.com/antfu/skills/blob/main/skills/antfu-simplify/SKILL.md)，复用与行为保护参考 [Ponytail](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md)、[Anthropic code-simplifier](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-simplifier/agents/code-simplifier.md) 和 [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin/blob/main/skills/ce-simplify-code/SKILL.md)，死代码核对参考 [ECC refactor-clean](https://github.com/affaan-m/ECC/blob/main/commands/refactor-clean.md)。本技能自包含，不依赖安装这些来源。
- `tech-docs` 原名 `evidence-first-docs`，起于昇腾 310B CRI/CDI 挂载手册的返工。`writing` 的早期经验来自已发表文章与自造词较多稿件的比较。这些经历提供写作线索，不构成通用措辞规则。

Matt、飞书、Impeccable、Archify、shadcn 等第三方原版继续从原来源安装，不重复发布。`rag-smart-qa` 来源为本地 Hermes（AcoPilot 内置）技能库，不在本仓库维护，已安装的全局版本保留。

知识库原文和查询对比片段不进入公开仓库。资料查询方式以技能中的当前参考为准。
