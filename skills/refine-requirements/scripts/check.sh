#!/usr/bin/env bash
# 可选提示扫描；只识别词句和示例格式，不判定需求是否正确。
set -u
[ $# -gt 0 ] || { echo "用法: $0 <需求文档>..." >&2; exit 2; }
command -v rg >/dev/null 2>&1 || { echo "需要 ripgrep (rg)" >&2; exit 127; }

scan() {
  rg "$@"
  local status=$?
  [ "$status" -le 1 ] || exit "$status"
}

echo "== 1. 可能含糊的目标（准确术语或已有定义可保留）"
scan -n '灵活|易用|友好|足够|适当|合理|尽快|快速|高效|稳定|健壮|可扩展|安全|直观|尽量|最大限度地|等等|诸如此类|以及/或者|和/或|必要时|视情况而定|正常|良好|完善|优化' "$@"
scan -n -i -w 'flexible|easy|sufficient|adequate|user-friendly|usable|appropriate|fast|quickly|robust|scalable|secure|intuitive|minimize|maximize|portable|lightweight|efficient|seamless|etc\.?|and/or|if required|as appropriate|if possible|when necessary' "$@"

echo "== 2. 比较、范围与条件（核对是否可判定，不强求数字）"
scan -n '更快|更小|更好|所有|任何|从不|总是|唯一|如果可能|酌情|在需要时' "$@"

echo "== 3. 示例编号中未见状态标记（项目其他格式可忽略）"
scan -n -P '^(?!\s*\|).*\b(FR|BR)-\d+\b(?!.*\[(已定|自由|待问)\])' "$@"
scan -n -P '^(?!\s*\|).*\bQ-\d+\b(?!.*\[待问\])' "$@"

echo "== 4. 示例假设中未见“若不成立”（核对是否已说明影响）"
scan -n -P '^(?!\s*\|).*\bA-\d+\b(?!.*若不成立)' "$@"

exit 0
