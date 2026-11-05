# 我的 Agent Skills

这里维护自己编写、或针对工作环境修改过的技能。Matt、飞书、Impeccable、Archify 等第三方原版继续从各自上游安装。

## 安装与更新

需要能访问这台 Git 服务器的网络。安装器会显示 `Develop` 和 `Sylixos` 两组，可按组或单项勾选。全局安装放在 `~/.agents/skills`，供 Claude Code、Codex 和 Zcode 使用：

```bash
npx skills add http://100.77.36.66:3000/wangjijie/skills.git -g -a claude-code codex zcode
```

跳过交互、安装 `develop` 组的五项技能：

```bash
npx skills add http://100.77.36.66:3000/wangjijie/skills.git -g -a claude-code codex zcode -s commit evidence-first-docs refine-requirements slim writing -y
```

跳过交互、安装 `sylixos` 组的两项技能：

```bash
npx skills add http://100.77.36.66:3000/wangjijie/skills.git -g -a claude-code codex zcode -s sylixos qemu-sylixos-ecs-usage -y
```

只查看分组和全部七项技能：

```bash
npx skills add http://100.77.36.66:3000/wangjijie/skills.git --list
```

分组由 [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) 声明，使用 skills CLI 1.7.1 的原生分组选择，无需环境变量。`-s` 接收技能名称，不接收组名；`-s sylixos` 只安装同名技能。使用 `-y` 而不指定 `-s` 会安装全部七项。已有安装保留，分组不改变技能名称、目录或安装后的调用方式。

更新已安装的全局技能：

```bash
npx skills update -g -y
```

这会同时检查其他来源的全局技能。只更新本仓库的一项可用 `npx skills update commit -g -y`；重新执行对应安装命令也可以同步选中的技能。以上命令按 skills CLI 1.7.1 验证，自建 Git URL 的来源和路径会记录在全局安装锁文件中。

skills CLI 已支持 Zcode。三个 Agent 共用同一份技能；如需补齐 Codex 的旧目录入口，可在仓库检出目录运行：

```bash
bash scripts/link-agents.sh
```

项目中不再保留这些技能的副本或链接。同名修改提交到本仓库，再更新全局安装。项目特有的地址、产物路径、构建命令、权限和验收约定留在项目配置或 `AGENTS.md` 中。

## 技能

| 分组 | 用途 | 技能 |
| --- | --- | --- |
| `develop` | 提交、写作、需求与文档纪律 | `commit`、`evidence-first-docs`、`writing`、`refine-requirements`、`slim` |
| `sylixos` | SylixOS 开发与 ECS QEMU 虚拟机管理 | `sylixos`、`qemu-sylixos-ecs-usage` |

`sylixos` 按任务读取专项参考，文档查询优先使用可用的 AcoHub MCP；本地资料用于离线、在线未覆盖或指定历史版本。在线片段不保证最新，需核对来源和版本。查询不触发部署或发布。旧的九个 SylixOS 相关入口已合并；旧安装的移除与新入口安装分开处理，不能假定 `npx skills update` 会删除旧名称。本机已完成迁移。

## 维护

每项技能放在 `skills/<name>/`，入口为 `SKILL.md`，随技能安装的脚本和参考资料使用相对路径。`<SKILL_DIR>` 指当前安装的 `SKILL.md` 所在目录。新增技能时，在 marketplace 清单中分配到一个组；每项技能恰好归属一组，并保持默认可发现。

`sylixos` 的手册索引映射见 [手册检索](skills/sylixos/references/docs.md)。已有资料继续放在原来的 `~/.agents/skill-data` 子目录，或由 `AGENTS_SKILL_DATA_DIR` 指定资料根目录，合并技能不重命名资料目录。RealEvo 原适配器仍位于 `<DATA_ROOT>/realevo-stream/scripts`。技能安装不会安装 IDE、MCP、SDK、调试器、手册或虚拟机。

`git-commit`、`ecsd-commit` 合并到 `commit`；需求完善技能使用 `refine-requirements` 并保持手动调用。移植历史经验须核对当前源码、SDK 和目标证据，不能把旧补丁作为通用默认值。

仓库不包含底层产品手册。个人检索流程和自写脚本在这里维护，第三方资料留在本地；原有素材保留各自许可。本仓库的来源记录见 [SOURCES.md](SOURCES.md)。

在装有 PyYAML 的 Python 环境中检查技能入口、名称、索引引用和分组完整性：

```bash
python3 scripts/validate.py
python3 -m unittest discover -s scripts/tests
```