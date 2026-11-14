# 我的 Agent Skills

本仓库维护自己编写或针对工作环境修改过的 Agent 技能；第三方原版仍从上游安装，不在这里重复发布。

- **技能清单与分组**：见 [marketplace 清单](.claude-plugin/marketplace.json)，具体用法看各技能目录下的 `SKILL.md`
- **协作与验证约定**：见 [AGENTS.md](AGENTS.md)
- **来源与资料边界**：见 [SOURCES.md](SOURCES.md)

## 安装与更新

使用 skills CLI 安装（`-s` 只接收技能名，不接收组名；每项技能均可独立安装）：

```bash
# 安装全部技能
npx skills add kurerere/skills -g -a claude-code codex zcode

# 仅安装指定技能
npx skills add kurerere/skills -g -a claude-code codex zcode -s sylixos -y

# 查看分组与技能列表
npx skills add kurerere/skills --list
```

更新已安装的全局技能：

```bash
npx skills update -g -y
```

该命令会一并检查其他来源的全局技能；只想同步指定技能时，重新执行带 `-s <技能名>` 的安装命令即可。示例基于 skills CLI 1.7.1 的用法，执行前以本机 `--help` 为准。

如需手工创建软链接，可使用 [scripts/link-agents.sh](scripts/link-agents.sh)（同一环境中的同名技能只用一种方式管理）。执行前需显式指定源目录；脚本会保留已有的目录和链接，存在差异时需另行处理：

```bash
AGENTS_SKILLS_DIR=/绝对路径/skills bash scripts/link-agents.sh
```

## 维护与校验

- **修改集中管理**：对技能的改动统一在本仓库完成，再更新全局安装，不要在使用这些技能的项目里另留副本。项目特有的地址、构建命令、权限与验收约定，留在对应项目的配置或 `AGENTS.md` 中。
- **外部环境与资料**：技能安装不包含 IDE、MCP、SDK、调试器、产品手册或虚拟机。SylixOS 本地资料的位置与查询入口见 [手册检索](skills/sylixos/references/docs.md)，更新技能不会迁移这些外部资料。
- **本地校验**：验证命令见 [AGENTS.md](AGENTS.md)。校验依赖 PyYAML，扫描相关测试还需要 Bash 和 ripgrep（Windows 下可用 `SKILLS_TEST_BASH` 指定 Bash 路径）。缺少依赖时部分测试会跳过，运行后注意查看测试摘要。
