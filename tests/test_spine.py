from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path

from anatomy.organs import o13_spine


class SpineCheckpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path(".anatomy-spine-checkpoint.json")
        if self.path.exists():
            self.path.unlink()

    def tearDown(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def test_kill_then_resume_does_not_rerun_completed_steps(self) -> None:
        first = asyncio.run(
            o13_spine.run(
                question="q",
                replay=False,
                record=False,
                trace=False,
                stage=False,
                autopsy="",
                beat=10,
                kill=True,
                resume=False,
                tool_search=False,
            )
        )
        self.assertEqual(first.status, "fail")
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        done_count = len([step for step in payload["steps"] if step["done"]])
        self.assertGreaterEqual(done_count, 2)

        second = asyncio.run(
            o13_spine.run(
                question="q",
                replay=False,
                record=False,
                trace=False,
                stage=False,
                autopsy="",
                beat=10,
                kill=False,
                resume=True,
                tool_search=False,
            )
        )
        self.assertEqual(second.status, "ok")
        self.assertTrue(any(line.startswith("SKIP") for line in second.output))


if __name__ == "__main__":
    unittest.main()