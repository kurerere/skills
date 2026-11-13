import shutil
import tempfile
import unittest
from pathlib import Path
from shell_support import BASH, run_shell


SCRIPT = Path(__file__).resolve().parents[2] / "skills/refine-requirements/scripts/check.sh"


def scan(text):
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as file:
        file.write(text + "\n")
    try:
        output = run_shell(SCRIPT, file.name, check=True).stdout
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


@unittest.skipUnless(BASH and shutil.which("rg"), "需要 Bash 和 ripgrep")
class RefineCheckTests(unittest.TestCase):
    def test_possible_vague_targets(self):
        self.assertTrue(scan("系统应快速响应")[1])
        self.assertTrue(scan("The API should be robust")[1])
        self.assertFalse(scan("系统应在 200 ms 内返回")[1])

    def test_missing_tri_state(self):
        self.assertTrue(scan("- **FR-01** 当上游返回 5xx 时，系统应重试")[3])
        self.assertFalse(scan("- **FR-01 [已定]** 当上游返回 5xx 时，系统应重试")[3])
        self.assertFalse(scan("| FR-01 | 重试上限 | 已定 |")[3])
        self.assertTrue(scan("- **Q-01** 上限是否可配置")[3])

    def test_assumption_needs_consequence(self):
        self.assertTrue(scan("- **A-01** 假设上游支持幂等键。")[4])
        self.assertFalse(scan("- **A-01** 假设上游支持幂等键。若不成立：会重复写入。")[4])


if __name__ == "__main__":
    unittest.main()
