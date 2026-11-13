# 我的 Agent Skills

这里维护自己编写、或针对工作环境修改过的技能。Matt、飞书、Impeccable、Archify 等第三方原版继续从各自上游安装。

## 安装与更新

默认由 Magpie Library 管理技能。在 Library 的安装界面选择本仓库 `kurerere/skills`，按需安装并选择使用它的 Agent。技能内容和入口交给 Magpie 维护，不另建 `.agents/skills` 副本或手工覆盖 Agent 的技能链接。

查看分发状态、更新某项技能并重新同步入口：

```bash
magpie library
magpie library skill update coding
magpie library sync
```

`magpie library skill update` 不带名称时更新所有来自 GitHub 的技能；本机有改动的技能默认保留，先比较差异再决定是否覆盖。设置某项技能分发给哪些 Agent：

```bash
magpie library skill agents coding claude,codex
```

旧版 `~/.agents/skills` 安装可用 `magpie library skill hand-over <技能名>` 交给 Library 管理。迁移前核对来源与本地改动；安装、更新和移除旧名称分别处理，不能假定同步会自动移除旧技能。

### 未使用 Magpie 的环境

可选用 skills CLI；同一环境中的同名技能只用一种方式管理。安装全部技能或只安装一项：

```bash
npx skills add kurerere/skills -g -a claude-code codex zcode
npx skills add kurerere/skills -g -a claude-code codex zcode -s sylixos -y
```

查看分组与技能：

```bash
npx skills add kurerere/skills --list
```

分组由 [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) 声明。`-s` 接收技能名，不接收组名；当前共七项技能，支持逐项安装。入口和所需资源随各技能一起分发，不要求其他技能位于相邻目录。

更新已安装的全局技能：

```bash
npx skills update -g -y
```

这会同时检查其他来源的全局技能。重新执行带 `-s <技能名>` 的安装命令可同步选中技能。skills CLI 示例沿用 1.7.1 的用法，执行前以本机 `--help` 为准。

`scripts/link-agents.sh` 仅供旧安装手工补入口，不用于 Magpie 管理的环境。它要求显式给出源目录，只处理本仓库维护的技能，保留所有已有目录和链接（包括失效链接）：

```bash
AGENTS_SKILLS_DIR=/绝对路径/skills bash scripts/link-agents.sh
```

项目中不再保留这些技能的副本或链接。同名修改提交到本仓库，再更新全局安装。项目特有的地址、产物路径、构建命令、权限和验收约定留在项目配置或 `AGENTS.md` 中。

## 技能

| 分组 | 用途 | 技能 |
| --- | --- | --- |
| `develop` | 编码、提交、写作、需求与文档纪律 | `coding`、`commit`、`tech-docs`、`writing`、`refine-requirements`、`slim-docs` |
| `sylixos` | SylixOS 开发、板卡操作、移植与调试 | `sylixos` |

`sylixos` 按任务读取专项参考，文档查询优先使用可用的 AcoHub MCP；本地资料用于离线、在线未覆盖或指定历史版本。在线片段不保证最新，需核对来源和版本。查询不触发部署或发布。

## 维护

每项技能放在 `skills/<name>/`，入口为 `SKILL.md`，随技能安装的脚本和参考资料使用技能目录内的相对路径。`<SKILL_DIR>` 指当前安装的 `SKILL.md` 所在目录。其他技能只能从当前环境提供的位置按需读取，不能假设相邻安装。新增技能时，在 marketplace 清单中分配到一个组；每项技能恰好归属一组，并保持默认可发现。

`sylixos` 的手册索引映射见 [手册检索](skills/sylixos/references/docs.md)。已有资料继续放在原来的 `~/.agents/skill-data` 子目录，或由 `AGENTS_SKILL_DATA_DIR` 指定资料根目录，合并技能不重命名资料目录。RealEvo 原适配器仍位于 `<DATA_ROOT>/realevo-stream/scripts`。技能安装不会安装 IDE、MCP、SDK、调试器、手册或虚拟机。

`git-commit`、`ecsd-commit` 合并到 `commit`；`refine-requirements` 保持手动调用，主干需求维护在 `.requirements/REQ-<主题>.md`，主题较多时由同目录的 `README.md` 提供索引。REQ 记录目标、使用者与关键边界，细化需求由代码与测试承载。移植历史经验须核对当前源码、SDK 和目标证据，不能把旧补丁作为通用默认值。

仓库不包含底层产品手册。个人检索流程和自写脚本在这里维护，第三方资料留在本地；原有素材保留各自许可。本仓库的来源记录见 [SOURCES.md](SOURCES.md)。

在装有 PyYAML 的 Python 环境中检查技能入口、名称、独立安装的资源引用和分组完整性，并测试随技能分发的脚本。扫描脚本需要 Bash 和 ripgrep；Windows 测试优先识别 Git Bash，也可用 `SKILLS_TEST_BASH` 指定 Bash 路径。缺少依赖时相关测试会跳过，需核对测试摘要。

```bash
python3 scripts/validate.py
python3 -m unittest discover -s scripts/tests
```
