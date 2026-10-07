#!/usr/bin/env bash
set -euo pipefail

skill_root="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
for agent in claude codex zcode; do
  destination="$HOME/.$agent/skills"
  mkdir -p "$destination"
  for skill in "$skill_root"/*; do
    [[ -f "$skill/SKILL.md" ]] || continue
    name="${skill##*/}"
    target="$destination/$name"
    if [[ -L "$target" ]]; then
      ln -sfn "$skill" "$target"
    elif [[ -e "$target" ]]; then
      printf '保留现有目录，请先比较差异：%s\n' "$target" >&2
    else
      ln -s "$skill" "$target"
    fi
  done
done
