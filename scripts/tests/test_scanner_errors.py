import os
from pathlib import Path
import tempfile
import unittest

from shell_support import BASH, run_shell


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = [ROOT / "skills" / name / "scripts/check.sh" for name in ("writing", "refine-requirements")]


@unittest.skipUnless(BASH, "需要 Bash")
class ScannerErrorTests(unittest.TestCase):
    def test_missing_input_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            for script in SCRIPTS:
                with self.subTest(script=script):
                    self.assertNotEqual(run_shell(script, Path(folder, "missing.md")).returncode, 0)

    def test_missing_ripgrep_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            document = Path(folder, "input.md")
            document.write_text("test", encoding="utf-8")
            env = dict(os.environ, PATH=folder)
            for script in SCRIPTS:
                with self.subTest(script=script):
                    self.assertNotEqual(run_shell(script, document, env=env).returncode, 0)
