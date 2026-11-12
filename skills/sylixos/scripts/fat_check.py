"""只读检查 FAT32 启动分区镜像，或生成修正保留位后的副本。

用法：
  python3 fat_check.py check <分区镜像> [--offset 字节] [--path /BOOT.BIN ...]
  python3 fat_check.py fix <分区镜像> <输出镜像> [--offset 字节]

check 不修改输入；fix 只写新文件：清零全部 FAT 表项的高 4 位保留位，并以第一份 FAT 为准同步其余副本。
"""
import argparse
import hashlib
import struct
import sys

MASK = 0x0FFFFFFF
EOC_MIN = 0x0FFFFFF8
BAD = 0x0FFFFFF7


class Volume:
    def __init__(self, data, offset=0):
        self.data = data
        self.offset = offset
        bpb = data[offset:offset + 512]
        if len(bpb) < 512:
            raise ValueError("镜像太小，读不到引导扇区")
        (self.bytes_per_sector, self.sectors_per_cluster, self.reserved, self.num_fats) = struct.unpack_from("<HBHB", bpb, 11)
        self.fat_sectors = struct.unpack_from("<I", bpb, 36)[0]
        self.root_cluster = struct.unpack_from("<I", bpb, 44)[0]
        total16, = struct.unpack_from("<H", bpb, 19)
        total32, = struct.unpack_from("<I", bpb, 32)
        fat16_size, = struct.unpack_from("<H", bpb, 22)
        if not self.bytes_per_sector or not self.sectors_per_cluster or fat16_size or not self.fat_sectors:
            raise ValueError("不是 FAT32 引导扇区（BPB 字段不符）")
        self.total_sectors = total32 or total16
        self.cluster_size = self.bytes_per_sector * self.sectors_per_cluster
        self.fat_bytes = self.fat_sectors * self.bytes_per_sector
        self.fat_start = offset + self.reserved * self.bytes_per_sector
        self.data_start = self.fat_start + self.num_fats * self.fat_bytes
        data_sectors = self.total_sectors - (self.reserved + self.num_fats * self.fat_sectors)
        self.cluster_count = data_sectors // self.sectors_per_cluster
        self.entries = min(self.fat_bytes // 4, self.cluster_count + 2)

    def fat(self, index=0):
        start = self.fat_start + index * self.fat_bytes
        return list(struct.unpack_from(f"<{self.entries}I", self.data, start))

    def cluster(self, number):
        start = self.data_start + (number - 2) * self.cluster_size
        return self.data[start:start + self.cluster_size]

    def chain(self, start, fat):
        """沿链行走，返回 (簇列表, 断点说明或 None)。表项按低 28 位解释。"""
        clusters, seen, current = [], set(), start
        while True:
            if current < 2 or current >= self.cluster_count + 2:
                return clusters, f"簇号 {current:#x} 越界"
            if current in seen:
                return clusters, f"簇 {current} 处成环"
            seen.add(current)
            clusters.append(current)
            value = fat[current] & MASK
            if value >= EOC_MIN:
                return clusters, None
            if value <= 1 or value == BAD:
                return clusters, f"簇 {current} 的表项为 {fat[current]:#010x}，链中断"
            current = value


def strict_break(volume, start, fat):
    """模拟按 32 位整值判断的 bootloader：返回能读出的簇数和第一个非法表项。"""
    count, current = 0, start
    while 2 <= current < volume.cluster_count + 2 and count <= volume.cluster_count:
        count += 1
        raw = fat[current]
        if raw >= EOC_MIN and raw <= MASK:
            return count, None
        if raw > MASK or raw <= 1 or raw == BAD or raw >= volume.cluster_count + 2:
            return count, (current, raw)
        current = raw
    return count, (current, None)


def dir_entries(volume, fat, cluster):
    clusters, _ = volume.chain(cluster, fat)
    raw = b"".join(volume.cluster(c) for c in clusters)
    long_parts = []
    for pos in range(0, len(raw), 32):
        entry = raw[pos:pos + 32]
        if entry[0] == 0:
            return
        if entry[0] == 0xE5:
            long_parts = []
            continue
        attr = entry[11]
        if attr == 0x0F:
            chars = entry[1:11] + entry[14:26] + entry[28:32]
            long_parts.insert(0, chars.decode("utf-16-le", "ignore").split("\x00")[0].rstrip("\uffff"))
            continue
        if attr & 0x08:
            long_parts = []
            continue
        base = entry[0:8].decode("ascii", "replace").rstrip()
        ext = entry[8:11].decode("ascii", "replace").rstrip()
        short = f"{base}.{ext}" if ext else base
        name = "".join(long_parts) or short
        long_parts = []
        hi, = struct.unpack_from("<H", entry, 20)
        lo, = struct.unpack_from("<H", entry, 26)
        size, = struct.unpack_from("<I", entry, 28)
        yield name, short, (hi << 16) | lo, size, bool(attr & 0x10)


def find(volume, fat, path):
    cluster = volume.root_cluster
    parts = [p for p in path.strip("/").split("/") if p]
    for depth, part in enumerate(parts):
        for name, short, start, size, is_dir in dir_entries(volume, fat, cluster):
            if part.lower() in (name.lower(), short.lower()):
                if depth == len(parts) - 1:
                    return start, size
                if not is_dir:
                    raise ValueError(f"{part} 不是目录")
                cluster = start
                break
        else:
            raise ValueError(f"找不到 {path}")
    raise ValueError("路径为空")


def check(volume, paths):
    fats = [volume.fat(i) for i in range(volume.num_fats)]
    main = fats[0]
    reserved = [i for i in range(2, volume.entries) if main[i] & ~MASK & 0xFFFFFFFF]
    print(f"FAT32：每簇 {volume.cluster_size} 字节，{volume.cluster_count} 簇，{volume.num_fats} 份 FAT")
    print(f"保留位非零的表项：{len(reserved)}" + (f"，前几项 {reserved[:8]}" if reserved else ""))
    for index in range(1, len(fats)):
        diff = [i for i in range(volume.entries) if fats[index][i] != main[i]]
        print(f"FAT#{index + 1} 与 FAT#1 不同的表项：{len(diff)}" + (f"，前几项 {diff[:8]}" if diff else ""))
    problems = bool(reserved) or any(fats[i] != main for i in range(1, len(fats)))
    for path in paths:
        start, size = find(volume, main, path)
        clusters, broken = volume.chain(start, main)
        needed = -(-size // volume.cluster_size) if size else 0
        content = b"".join(volume.cluster(c) for c in clusters)[:size]
        print(f"\n{path}：起始簇 {start}，大小 {size} 字节，需要 {needed} 簇")
        print(f"  按低 28 位沿链：{len(clusters)} 簇" + (f"，{broken}" if broken else "，链完整"))
        count, bad = strict_break(volume, start, main)
        if bad:
            cluster, raw = bad
            readable = min(count * volume.cluster_size, size)
            raw_text = f"{raw:#010x}" if raw is not None else "越界"
            print(f"  按 32 位整值判断：第 {count} 簇（簇号 {cluster}）表项 {raw_text} 非法，约读到 {readable} 字节后截断")
            problems = True
        else:
            print("  按 32 位整值判断：可完整读出")
        if broken or len(clusters) < needed:
            problems = True
        else:
            print(f"  按掩码重建 SHA-256：{hashlib.sha256(content).hexdigest()}")
    return 1 if problems else 0


def fix(volume, output):
    data = bytearray(volume.data)
    clean = [value & MASK for value in volume.fat(0)]
    packed = struct.pack(f"<{volume.entries}I", *clean)
    for index in range(volume.num_fats):
        start = volume.fat_start + index * volume.fat_bytes
        data[start:start + len(packed)] = packed
    with open(output, "xb") as file:
        file.write(data)
    print(f"已写出修正副本 {output}；写回前先对副本运行 check 并比对启动文件哈希")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check a FAT32 boot partition image read-only, or write a repaired copy.")
    sub = parser.add_subparsers(dest="mode", required=True)
    check_parser = sub.add_parser("check", help="report reserved bits, FAT copy mismatches and file chains")
    check_parser.add_argument("image")
    check_parser.add_argument("--offset", type=int, default=0, help="partition start offset in bytes (default: 0)")
    check_parser.add_argument("--path", action="append", default=[], help="file to trace, e.g. /BOOT.BIN; repeatable")
    fix_parser = sub.add_parser("fix", help="write a copy with reserved bits cleared and FAT copies synced from FAT#1")
    fix_parser.add_argument("image")
    fix_parser.add_argument("output", help="new file; refuses to overwrite")
    fix_parser.add_argument("--offset", type=int, default=0, help="partition start offset in bytes (default: 0)")
    args = parser.parse_args(argv)
    try:
        with open(args.image, "rb") as file:
            volume = Volume(file.read(), args.offset)
        if args.mode == "check":
            return check(volume, args.path)
        return fix(volume, args.output)
    except (OSError, ValueError, struct.error) as error:
        print(f"fat_check: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
