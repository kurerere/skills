# 我的 Agent Skills

这里维护自己编写、或针对工作环境修改过的技能。Matt、飞书、Impeccable、Archify 等第三方原版继续从各自上游安装。

## 安装与更新

需要能访问这台 Git 服务器的网络。全局安装到 `~/.agents/skills`，供 Claude Code 和 Codex 使用：

```bash
npx skills add http://100.77.36.66:3000/wangjijie/skills.git -g -a claude-code codex -s '*' -y
```

只安装某个技能时，把 `'*'` 换成名称，例如 `commit` 或 `shuorenhua`。查看仓库中的技能：

```bash
npx skills add http://100.77.36.66:3000/wangjijie/skills.git --list
```

更新已安装的全局技能：

```bash
npx skills update -g -y
```

这会同时检查其他来源的全局技能。只更新本仓库的一项可用 `npx skills update commit -g -y`；重新执行安装命令也可以同步本仓库的全部技能。以上命令按 skills CLI 1.7.1 验证，自建 Git URL 的来源和路径会记录在全局安装锁文件中。

skills CLI 目前没有 zcode 适配。它可以共用同一份目录；在仓库检出目录运行下面的脚本，也会补齐 Codex 的旧目录入口：

```bash
bash scripts/link-agents.sh
```

项目中不再保留这些技能的副本或链接。同名修改提交到本仓库，再更新全局安装。项目特有的地址、产物路径、构建命令、权限和验收约定留在项目配置或 `AGENTS.md` 中。

## 技能

| 用途 | 技能 |
| --- | --- |
| 提交、写作与需求 | `commit`、`shuorenhua`、`features-full` |
| Unix 命令行工具移植 | `sylixos-cli-workflow` |
| 构建、部署与调试 | `sylixos-ext-skill`、`sylixos-gdb`、`qemu-sylixos-ecs-usage` |
| 移植经验 | `sylixos-porting`、`sylixos-socket-porting` |
| Armory | `armory-usage` |
| 文档查询与工具接口 | `ecs-docs`、`jsre-api`、`sylixos-usage`、`vsoa-docs`、`realevo-stream` |

## 维护

每项技能放在 `skills/<name>/`，入口为 `SKILL.md`，随技能安装的脚本和参考资料使用相对路径。`<SKILL_DIR>` 指当前安装的 `SKILL.md` 所在目录。

文档查询技能不附带产品手册。将已有资料放到 `~/.agents/skill-data/<skill-name>/references`，或设置 `AGENTS_SKILL_DATA_DIR` 指向自己的资料根目录，再按索引定位具体章节。资料放在技能目录之外，`npx skills update` 不会覆盖它们。RealEvo-Stream 的原工具适配器保留在 `<DATA_ROOT>/realevo-stream/scripts`，不随公开仓库分发。工具型技能仍依赖对应 IDE、MCP、工具链或虚拟机环境，安装技能不会安装这些产品。历史移植经验要先核对当前 SDK 和板卡，不能把某次错误码映射当作通用规则。

`git-commit`、`ecsd-commit` 合并到 `commit`。sbase/cmd_relic 的规划和实现约定合并到 `sylixos-cli-workflow`。

仓库不包含底层产品手册。个人检索流程和自写脚本在这里维护，第三方资料留在本地；原有素材保留各自许可。本仓库的来源记录见 [SOURCES.md](SOURCES.md)。

在装有 PyYAML 的 Python 环境中检查技能入口、名称和索引引用：

```bash
python3 scripts/validate.py
```

Armory 手册与发布流程合并到 `armory-usage`；SylixOS 两套手册通过 `sylixos-usage/programming`、`sylixos-usage/system` 分别检索，兼容原资料目录。
