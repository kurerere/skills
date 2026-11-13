import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "skills/sylixos/scripts/fat_check.py"
SPEC = importlib.util.spec_from_file_location("sylixos_fat", SCRIPT)
fat_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fat_check)

SECTOR = 512
RESERVED = 32
FAT_SECTORS = 1
TOTAL = 160
PAYLOAD = bytes(range(256)) * 6  # 1536 字节，占 3 簇


def make_image():
    """构造最小 FAT32 分区：每簇 1 扇区，根目录在簇 2，BOOT.BIN 占簇 3→4→5。"""
    image = bytearray(TOTAL * SECTOR)
    struct.pack_into("<HBHB", image, 11, SECTOR, 1, RESERVED, 2)
    struct.pack_into("<I", image, 32, TOTAL)
    struct.pack_into("<I", image, 36, FAT_SECTORS)
    struct.pack_into("<I", image, 44, 2)
    fat = [0x0FFFFFF8, 0x0FFFFFFF, 0x0FFFFFFF, 4, 5, 0x0FFFFFFF] + [0] * 122
    for index in range(2):
        struct.pack_into("<128I", image, (RESERVED + index * FAT_SECTORS) * SECTOR, *fat)
    data = (RESERVED + 2 * FAT_SECTORS) * SECTOR
    entry = bytearray(32)
    entry[0:11] = b"BOOT    BIN"
    entry[11] = 0x20
    struct.pack_into("<H", entry, 26, 3)
    struct.pack_into("<I", entry, 28, len(PAYLOAD))
    image[data:data + 32] = entry
    image[data + SECTOR:data + 4 * SECTOR] = PAYLOAD
    return image


def set_entry(image, cluster, value, fat_index=0):
    struct.pack_into("<I", image, (RESERVED + fat_index * FAT_SECTORS) * SECTOR + cluster * 4, value)


class FatCheckTests(unittest.TestCase):
    def run_check(self, image, *paths):
        with tempfile.NamedTemporaryFile(delete=False) as file:
            file.write(image)
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                args = ["check", file.name] + [arg for path in paths for arg in ("--path", path)]
                code = fat_check.main(args)
        finally:
            Path(file.name).unlink()
        return code, output.getvalue()

    def test_clean_image_passes_and_hash_matches_file(self):
        code, output = self.run_check(make_image(), "/boot.bin")
        self.assertEqual(code, 0)
        self.assertIn("保留位非零的表项：0", output)
        self.assertIn(hashlib.sha256(PAYLOAD).hexdigest(), output)

    def test_truncated_image_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code, output = self.run_check(make_image()[:35 * SECTOR], "/BOOT.BIN")
        self.assertNotEqual(code, 0)
        self.assertNotIn("可完整读出", output)
        self.assertNotIn("SHA-256", output)

    def test_fat_must_cover_declared_clusters(self):
        image = make_image()
        struct.pack_into("<I", image, 32, 200)
        image.extend(bytes(40 * SECTOR))
        with self.assertRaises(ValueError):
            fat_check.Volume(image)

    def test_invalid_geometry_is_rejected(self):
        for offset, fmt, value in ((11, "<H", 0), (13, "<B", 3), (16, "<B", 0), (44, "<I", 150)):
            image = make_image()
            struct.pack_into(fmt, image, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                fat_check.Volume(image)

    def test_negative_partition_offset_is_rejected(self):
        with self.assertRaises(ValueError):
            fat_check.Volume(make_image(), -1)

    def test_out_of_range_chain_is_reported(self):
        image = make_image()
        set_entry(image, 3, 150)
        code, output = self.run_check(image, "/BOOT.BIN")
        self.assertEqual(code, 1)
        self.assertIn("越界", output)
        self.assertNotIn("SHA-256", output)

    def test_short_cluster_read_cannot_pass(self):
        volume = fat_check.Volume(make_image())
        read_cluster = volume.cluster
        volume.cluster = lambda number: read_cluster(number) if number == 2 else b""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertNotEqual(fat_check.check(volume, ["/BOOT.BIN"]), 0)
        self.assertNotIn("可完整读出", output.getvalue())
        self.assertNotIn("SHA-256", output.getvalue())

    def test_invalid_image_cannot_produce_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder, "in.img"), Path(folder, "out.img")
            source.write_bytes(make_image()[:35 * SECTOR])
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(fat_check.main(["fix", str(source), str(target)]), 2)
            self.assertFalse(target.exists())

    def test_reserved_bits_break_strict_reader_but_masked_chain_is_intact(self):
        image = make_image()
        set_entry(image, 4, 0xF0000005)
        code, output = self.run_check(image, "/BOOT.BIN")
        self.assertEqual(code, 1)
        self.assertIn("保留位非零的表项：1", output)
        self.assertIn("约读到 1024 字节后截断", output)
        self.assertIn(hashlib.sha256(PAYLOAD).hexdigest(), output)

    def test_fat_copy_mismatch_is_reported(self):
        image = make_image()
        set_entry(image, 10, 7, fat_index=1)
        code, output = self.run_check(image)
        self.assertEqual(code, 1)
        self.assertIn("FAT#2 与 FAT#1 不同的表项：1", output)

    def test_free_entry_inside_chain_is_a_break(self):
        image = make_image()
        set_entry(image, 4, 0)
        code, output = self.run_check(image, "/BOOT.BIN")
        self.assertEqual(code, 1)
        self.assertIn("链中断", output)

    def test_fix_writes_clean_copy_and_keeps_input(self):
        image = make_image()
        set_entry(image, 4, 0xF0000005)
        set_entry(image, 10, 7, fat_index=1)
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder, "in.img"), Path(folder, "out.img")
            source.write_bytes(image)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(fat_check.main(["fix", str(source), str(target)]), 0)
                self.assertEqual(fat_check.main(["fix", str(source), str(target)]), 2)
            self.assertEqual(source.read_bytes(), bytes(image))
            code, output = self.run_check(target.read_bytes(), "/BOOT.BIN")
        self.assertEqual(code, 0, output)


if __name__ == "__main__":
    unittest.main()
