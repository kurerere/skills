import os
from pathlib import Path
import shutil
import subprocess


def find_bash():
    configured = os.environ.get("SKILLS_TEST_BASH")
    if configured:
        return configured
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            candidate = Path(git).resolve().parent.parent / "bin/bash.exe"
            if candidate.is_file():
                return str(candidate)
    return shutil.which("bash")


BASH = find_bash()


def run_shell(script, *args, **kwargs):
    return subprocess.run([BASH, str(script), *map(str, args)], capture_output=True,
                          encoding="utf-8", **kwargs)
