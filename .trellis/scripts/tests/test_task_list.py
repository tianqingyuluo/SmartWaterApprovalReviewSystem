from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class TaskListTests(unittest.TestCase):
    def test_mine_filter_finds_matching_child_when_parent_is_different_assignee(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            trellis = repo / ".trellis"
            tasks = trellis / "tasks"
            scripts = trellis / "scripts"
            tasks.mkdir(parents=True)

            (trellis / ".developer").write_text(
                "name=ymx545\ninitialized_at=2026-04-27T00:00:00\n",
                encoding="utf-8",
            )

            self._write_task(
                tasks / "parent-task",
                {
                    "id": "parent",
                    "name": "parent",
                    "title": "Parent",
                    "status": "planning",
                    "assignee": "other",
                    "priority": "P0",
                    "children": ["child-task"],
                    "parent": None,
                    "package": None,
                },
            )
            self._write_task(
                tasks / "child-task",
                {
                    "id": "child",
                    "name": "child",
                    "title": "Child",
                    "status": "planning",
                    "assignee": "ymx545",
                    "priority": "P1",
                    "children": [],
                    "parent": "parent-task",
                    "package": None,
                },
            )

            self._copy_scripts(scripts)

            result = subprocess.run(
                [sys.executable, str(scripts / "task.py"), "list", "--mine"],
                cwd=repo,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            self.assertIn("child-task/", result.stdout)
            self.assertNotIn("parent-task/", result.stdout)
            self.assertIn("Total: 1 task(s)", result.stdout)

    def _copy_scripts(self, target: Path) -> None:
        import shutil

        shutil.copytree(REPO_ROOT / ".trellis" / "scripts", target)

    def _write_task(self, task_dir: Path, data: dict) -> None:
        task_dir.mkdir(parents=True)
        (task_dir / "task.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
