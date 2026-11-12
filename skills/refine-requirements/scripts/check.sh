#!/usr/bin/env bash
# 需求文档自查：扫描 references/rules.md 里能机械判断的几条。用法：bash check.sh <需求文档>...
# 命中后按 rules.md 逐处判断：给出数字、补上标记，或改写句子。
set -u
[ $# -gt 0 ] || { echo "用法: $0 <需求文档>..." >&2; exit 2; }

echo "== 1. 禁用词（不给数字就不能用）"
rg -n '灵活|易用|友好|足够|适当|合理|尽快|快速|高效|稳定|健壮|可扩展|安全|直观|尽量|最大限度地|等等|诸如此类|以及/或者|和/或|必要时|视情况而定|正常|良好|完善|优化' "$@"
rg -n -i -w 'flexible|easy|sufficient|adequate|user-friendly|usable|appropriate|fast|quickly|robust|scalable|secure|intuitive|minimize|maximize|portable|lightweight|efficient|seamless|etc\.?|and/or|if required|as appropriate|if possible|when necessary' "$@"

echo "== 2. 比较级、全称词与逃逸条款（核对是否给了数字或条件）"
rg -n '更快|更小|更好|所有|任何|从不|总是|唯一|如果可能|酌情|在需要时' "$@"

echo "== 3. 需求、边界和问题条目缺三态标记"
rg -n -P '^(?!\s*\|).*\b(FR|BR)-\d+\b(?!.*\[(已定|自由|待问)\])' "$@"
rg -n -P '^(?!\s*\|).*\bQ-\d+\b(?!.*\[待问\])' "$@"

echo "== 4. 假设缺“若不成立”"
rg -n -P '^(?!\s*\|).*\bA-\d+\b(?!.*若不成立)' "$@"

exit 0
