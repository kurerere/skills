#!/usr/bin/env bash
# 可选词句提示；按上下文判断，不按命中自动替换。
set -u
[ $# -gt 0 ] || { echo "用法: $0 <文件或目录>..." >&2; exit 2; }
command -v rg >/dev/null 2>&1 || { echo "需要 ripgrep (rg)" >&2; exit 127; }

scan() {
  rg "$@"
  local status=$?
  [ "$status" -le 1 ] || exit "$status"
}

echo "== 1. 可能需要展开的词语（准确术语可保留）"
scan -n '口径|抓手|赋能|闭环|维度|层面|机制|体系|进行[^行中]|物理上|一侧' "$@"

echo "== 2. 抽象用语（核对具体含义，不按白名单裁决）"
scan -n '门禁|契约' "$@"

echo "== 3. 判断与解释（核对依据及其支持范围）"
scan -n '这说明|这表明|(测试|结果|数据|实验)表明|可以看出|由此可见|显而易见|显然|意味着|充分(证明|体现)' "$@"

echo "== 4. 空转过渡与套话"
scan -n '在.*方面|对于.*而言|就.*而言|综上所述|值得注意的是|深入探讨' "$@"

echo "== 5. 感叹号、emoji、夸张词与伪量化"
scan -n '[!！?？]{2,}|[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]|非常|极其|颠覆|碾压|秒杀|震惊|炸裂|爆表|重磅|天花板|神器|拉满|起飞|(企业|工业|军工|毫?秒)级' "$@"

echo "== 6. 专有名词大小写（核对语境，保留代码与原始材料）"
scan -n -P '(?<![\w./-])(github|Github|postgresql|Postgresql|postgreSQL|nginx|NGINX|kubernetes|redis|REDIS|mysql|Mysql|MySql|MYSQL)(?![\w./-])' "$@"

exit 0
