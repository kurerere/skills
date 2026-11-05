import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("validate_skills", ROOT / "scripts/validate.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class SkillGroupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.manifest = {"plugins": [
            {"name": "develop", "source": "./", "skills": ["./skills/commit"]},
            {"name": "sylixos", "source": "./", "skills": ["./skills/sylixos"]},
        ]}
        for name in ("commit", "sylixos"):
            folder = self.root / "skills" / name
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test skill\n---\n")

    def inspect(self):
        folder = self.root / ".claude-plugin"
        folder.mkdir(exist_ok=True)
        (folder / "marketplace.json").write_text(json.dumps(self.manifest))
        return validator.inspect(self.root)

    def test_each_visible_skill_belongs_to_one_group(self):
        self.assertEqual(self.inspect(), [])

    def test_skill_cannot_be_in_two_groups(self):
        self.manifest["plugins"][1]["skills"].append("./skills/commit")
        self.assertTrue(self.inspect())

    def test_new_skill_must_be_assigned_to_a_group(self):
        self.manifest["plugins"][1]["skills"] = []
        self.assertTrue(self.inspect())

    def test_group_cannot_reference_missing_skill(self):
        self.manifest["plugins"][0]["skills"].append("./skills/missing")
        self.assertTrue(self.inspect())

    def test_group_source_must_stay_inside_repository(self):
        self.manifest["plugins"][0]["source"] = "./../outside"
        self.assertTrue(self.inspect())

    def test_internal_skill_is_allowed(self):
        path = self.root / "skills/sylixos/SKILL.md"
        path.write_text(path.read_text().replace("description: Test skill", "description: Test skill\nmetadata:\n  internal: true"))
        self.assertEqual(self.inspect(), [])


if __name__ == "__main__":
    unittest.main()
