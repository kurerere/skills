# 我的 Agent Skills

这里维护自己编写或针对工作环境修改过的技能。第三方原版继续从上游安装，不在本仓库重复发布。

技能清单与分组见 [marketplace 清单](.claude-plugin/marketplace.json)，具体用法见各技能的 `SKILL.md`。仓库协作约定见 [AGENTS.md](AGENTS.md)，来源与未随包分发的资料见 [SOURCES.md](SOURCES.md)。

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

`-s` 接收技能名，不接收组名。各项技能可独立安装。

更新已安装的全局技能：

```bash
npx skills update -g -y
```

这会同时检查其他来源的全局技能。重新执行带 `-s <技能名>` 的安装命令可同步选中技能。skills CLI 示例沿用 1.7.1 的用法，执行前以本机 `--help` 为准。

[旧入口链接脚本](scripts/link-agents.sh) 供手工兼容旧安装，不用于 Magpie 管理的环境。使用时显式指定源目录；已有目录和链接会保留，差异需另行处理：

```bash
AGENTS_SKILLS_DIR=/绝对路径/skills bash scripts/link-agents.sh
```

## 维护

技能修改集中到本仓库，再更新全局安装，不在使用项目里另留副本。项目特有的地址、构建命令、权限与验收约定留在项目配置或 `AGENTS.md` 中。

技能安装不包含 IDE、MCP、SDK、调试器、产品手册或虚拟机。SylixOS 本地资料位置与查询入口见 [手册检索](skills/sylixos/references/docs.md)，更新技能不迁移这些外部资料。

验证命令见 [协作约定](AGENTS.md)。校验需 PyYAML；扫描相关测试需 Bash 和 ripgrep。Windows 可用 `SKILLS_TEST_BASH` 指定 Bash 路径。缺少依赖可能导致测试跳过，需检查测试摘要。
