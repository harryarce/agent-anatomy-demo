from __future__ import annotations

import asyncio
import importlib
import io
import json
import unittest
from argparse import Namespace
from unittest.mock import patch
from pathlib import Path

from rich.console import Console

from anatomy import runner
from anatomy.presentation import FRAMES, difference_panel, teaching_intro


ORGAN_MODULES = (
    "anatomy.organs.o01_instructions",
    "anatomy.organs.o02_model",
    "anatomy.organs.o03_knowledge",
    "anatomy.organs.o04_tools",
    "anatomy.organs.o05_skills",
    "anatomy.organs.o06_memory",
    "anatomy.organs.o07_guardrails",
    "anatomy.organs.o08_orchestration",
    "anatomy.organs.o09_identity",
    "anatomy.organs.o10_observability",
    "anatomy.organs.o11_reflex_arc",
    "anatomy.organs.o13_spine",
    "anatomy.organs.o14_metabolism",
    "anatomy.organs.o16_learning",
)


class OrganMetadataTests(unittest.TestCase):
    def test_every_organ_has_a_teaching_frame(self) -> None:
        self.assertEqual(set(FRAMES), {organ.name for organ in runner.ORGANS})

    def test_teaching_frame_makes_the_difference_explicit(self) -> None:
        intro = teaching_intro("knowledge", 3, 1, "claims had no grounding")
        difference = difference_panel("knowledge", "Grounding changed the answer.")
        presenter_console = Console(record=True, width=100, color_system=None, file=io.StringIO())
        presenter_console.print(intro)
        presenter_console.print(difference)
        rendered = presenter_console.export_text()

        self.assertIn("WHY THIS ORGAN EXISTS", rendered)
        self.assertIn("WITHOUT THIS ORGAN", rendered)
        self.assertIn("WITH THIS ORGAN", rendered)

    def test_present_command_defaults_to_full_story(self) -> None:
        args = runner.build_parser().parse_args(["present", "--replay"])

        self.assertEqual(args.command, "present")
        self.assertEqual(args.from_beat, 0)
        self.assertTrue(args.replay)

    def test_constants_and_run_exist(self) -> None:
        for module_name in ORGAN_MODULES:
            module = importlib.import_module(module_name)
            self.assertTrue(hasattr(module, "STORY_BEAT"), module_name)
            self.assertTrue(hasattr(module, "FAILURE_IT_FIXES"), module_name)
            self.assertTrue(hasattr(module, "LANDING_LINE"), module_name)
            self.assertTrue(hasattr(module, "run"), module_name)

    def test_model_replay_is_loadable_without_cloud(self) -> None:
        module = importlib.import_module("anatomy.organs.o02_model")
        report = asyncio.run(
            module.run(
                question="q",
                replay=True,
                record=False,
                trace=False,
                stage=False,
                autopsy="",
                beat=None,
                kill=False,
                resume=False,
                tool_search=False,
            )
        )
        self.assertEqual(report.organ, "model")
        self.assertTrue(report.output)

    def test_autopsy_runs_intact_and_ablated_variants(self) -> None:
        args = Namespace(
            reset=True,
            replay=False,
            record=False,
            trace=False,
            stage=False,
            autopsy="knowledge",
            kill=False,
            resume=False,
            tool_search=False,
        )
        calls: list[str] = []

        async def fake_run(**options):
            calls.append(options["autopsy"])
            return runner.RunReport(
                organ="observability",
                status="ok",
                firing=["Observability"],
                output=[options["autopsy"] or "intact"],
                payoff=["compared"],
                landing_line="done",
            )

        with patch.object(runner, "_import_runner", return_value=fake_run):
            status = asyncio.run(runner._run_one("observability", args, beat=8))

        self.assertEqual(status, 0)
        self.assertEqual(calls, ["", "knowledge"])


class LocalScenarioDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_replays_exist_for_every_organ(self) -> None:
        replay_names = (
            "instructions",
            "model",
            "knowledge",
            "tools",
            "skills",
            "memory",
            "guardrails",
            "orchestration",
            "identity",
            "observability",
            "reflex_arc",
            "spine",
            "metabolism",
            "learning",
        )
        for replay_name in replay_names:
            payload = json.loads((self.root / "replays" / f"{replay_name}.json").read_text(encoding="utf-8"))
            self.assertTrue(payload)

    def test_reflex_arc_processes_drop_event(self) -> None:
        module = importlib.import_module("anatomy.organs.o11_reflex_arc")
        result_path = self.root / "dropbox" / "result.txt"
        result_path.unlink(missing_ok=True)
        report = asyncio.run(
            module.run(
                question="",
                replay=False,
                record=False,
                trace=False,
                stage=False,
                autopsy="",
                beat=12,
                kill=False,
                resume=False,
                tool_search=False,
            )
        )
        self.assertEqual(report.status, "ok")
        self.assertIn("order 4471", result_path.read_text(encoding="utf-8"))
        result_path.unlink()

    def test_metabolism_budget_stop_is_success(self) -> None:
        module = importlib.import_module("anatomy.organs.o14_metabolism")
        report = asyncio.run(
            module.run(
                question="",
                replay=False,
                record=False,
                trace=False,
                stage=False,
                autopsy="",
                beat=9,
                kill=False,
                resume=False,
                tool_search=False,
            )
        )
        self.assertEqual(report.status, "ok")
        self.assertTrue(any(line.startswith("BUDGET STOP:") for line in report.output))
        self.assertLessEqual(report.usage.total_tokens, 240)
        self.assertLessEqual(report.usage.estimated_cost_usd, 0.020)


if __name__ == "__main__":
    unittest.main()