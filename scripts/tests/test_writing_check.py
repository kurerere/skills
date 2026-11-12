import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "skills/writing/scripts/check.sh"


def scan(text):
    """运行 check.sh，返回 {段号: 命中行列表}。"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as file:
        file.write(text + "\n")
    try:
        output = subprocess.run(["bash", str(SCRIPT), file.name], capture_output=True, text=True, check=True).stdout
    finally:
        Path(file.name).unlink()
    hits, section = {}, None
    for line in output.splitlines():
        if line.startswith("== "):
            section = int(line[3])
            hits[section] = []
        elif section is not None:
            hits[section].append(line)
    return hits


@unittest.skipUnless(shutil.which("rg"), "需要 ripgrep")
class WritingCheckTests(unittest.TestCase):
    def assertHit(self, text, section):
        self.assertTrue(scan(text)[section], f"第 {section} 段应命中：{text}")

    def assertMiss(self, text, section):
        self.assertFalse(scan(text)[section], f"第 {section} 段不应命中：{text}")

    def test_prints_all_six_sections(self):
        self.assertEqual(sorted(scan("正常的一句话。")), [1, 2, 3, 4, 5, 6])

    def test_jargon(self):
        self.assertHit("这是一个完整的闭环", 1)
        self.assertMiss("把缓存大小设为 64 MB", 1)

    def test_gate_and_contract(self):
        self.assertHit("加上交付前门禁", 2)

    def test_explanation_without_data(self):
        for text in ("这说明系统很稳定", "测试表明性能良好", "可以看出存在泄漏"):
            self.assertHit(text, 3)
        for text in ("接口说明如下", "运行单元测试验证行为"):
            self.assertMiss(text, 3)

    def test_filler(self):
        self.assertHit("综上所述，方案可行", 4)

    def test_exaggeration_and_emoji(self):
        for text in ("性能非常好", "延迟秒级", "效果炸裂", "完成了✅", "真的吗？？"):
            self.assertHit(text, 5)
        self.assertMiss("p99 为 38 ms", 5)

    def test_wrong_product_case(self):
        for text in ("用 github 管理代码", "部署 Mysql 实例", "改用 redis 缓存"):
            self.assertHit(text, 6)
        for text in ("用 GitHub 管理代码", "部署 MySQL 实例", "见 https://github.com/x", "路径 /etc/nginx/nginx.conf"):
            self.assertMiss(text, 6)


if __name__ == "__main__":
    unittest.main()
