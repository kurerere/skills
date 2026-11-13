import os
from pathlib import Path
import tempfile
import unittest

from shell_support import BASH, run_shell


SCRIPT = Path(__file__).resolve().parents[1] / "link-agents.sh"


@unittest.skipUnless(BASH, "需要 Bash")
class LinkAgentTests(unittest.TestCase):
    def test_manual_source_is_required(self):
        env = os.environ.copy()
        env.pop("AGENTS_SKILLS_DIR", None)
        self.assertEqual(run_shell(SCRIPT, env=env).returncode, 2)

    def test_existing_entries_are_preserved_and_foreign_skills_are_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source"
            for name in ("coding", "commit", "writing", "foreign"):
                skill = source / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(name, encoding="utf-8")
            home = root / "home"
            targets = home / ".codex/skills"
            targets.mkdir(parents=True)
            own = root / "managed"
            own.mkdir()
            (targets / "coding").symlink_to(own, target_is_directory=True)
            (targets / "commit").mkdir()
            (targets / "commit/keep.txt").write_text("keep", encoding="utf-8")
            (targets / "writing").symlink_to(root / "gone", target_is_directory=True)
            env = dict(os.environ, AGENTS_SKILLS_DIR=source.as_posix(), AGENTS_LINK_HOME=home.as_posix())
            result = run_shell(SCRIPT, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((targets / "coding").resolve(), own.resolve())
            self.assertEqual((targets / "commit/keep.txt").read_text(), "keep")
            self.assertTrue((targets / "writing").is_symlink())
            self.assertFalse((targets / "writing").exists())
            self.assertFalse((targets / "foreign").exists())
            self.assertTrue((home / ".claude/skills/coding/SKILL.md").is_file())
