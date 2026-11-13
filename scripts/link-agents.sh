#!/usr/bin/env bash
set -euo pipefail

[ -n "${AGENTS_SKILLS_DIR:-}" ] || {
  printf '默认由 Magpie 管理技能。手工兼容链接需显式设置 AGENTS_SKILLS_DIR。\n' >&2
  exit 2
}
skill_root="$(cd -- "$AGENTS_SKILLS_DIR" && pwd -P)"
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
agent_home="${AGENTS_LINK_HOME:-$HOME}"
for agent in claude codex zcode; do
  destination="$agent_home/.$agent/skills"
  mkdir -p "$destination"
  for skill in "$skill_root"/*; do
    [[ -f "$skill/SKILL.md" ]] || continue
    name="${skill##*/}"
    [[ -f "$repo_root/skills/$name/SKILL.md" ]] || continue
    target="$destination/$name"
    if [[ -L "$target" ]]; then
      printf '保留现有链接：%s\n' "$target" >&2
    elif [[ -e "$target" ]]; then
      printf '保留现有目录，请先比较差异：%s\n' "$target" >&2
    else
      ln -s "$skill" "$target"
    fi
  done
done
