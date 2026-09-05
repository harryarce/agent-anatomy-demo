from __future__ import annotations

import asyncio
import importlib
import io
import json
import unittest
from argparse import Namespace
from unittest.mock import AsyncMock, patch
from pathlib import Path

from rich.console import Console

from anatomy import runner
from anatomy.banner import ORGANS as BANNER_ORGANS
from anatomy.common import RunReport, attributed_story, load_report_replay
from anatomy.presentation import FRAMES, difference_panel, teaching_intro
from scripts.preflight import ORGAN_MODULES as PREFLIGHT_MODULES
from scripts.preflight import REQUIRED_REPLAYS


ORGAN_MODULES = tuple(organ.module for organ in runner.ORGANS)


class OrganMetadataTests(unittest.TestCase):
    def test_story_transcript_attributes_user_model_and_tool_actors(self) -> None:
        model_report = RunReport("model", "ok", [], ["A grounded answer.\nWith evidence."], [], "done")
        tool_report = RunReport("tools", "ok", [], ["SQLite lookup: order 4471"], [], "done")

        self.assertEqual(attributed_story(model_report)[0][0], "USER")
        self.assertEqual(attributed_story(model_report)[1][0], "AI / MODEL")
        self.assertEqual(attributed_story(model_report)[2][0], "AI / MODEL")
        self.assertEqual(attributed_story(tool_report)[1][0], "TOOL")

    def test_instruction_story_shows_the_profile_owner_and_model_effect(self) -> None:
        report = load_report_replay("instructions")
        story = attributed_story(report)

        self.assertIn(
            ("APPLICATION TEAM", "Application team configures 'terse expert': 'Be concise, cite policy, and avoid unsupported claims.'"),
            story,
        )
        self.assertIn(
            ("AI / MODEL", "Ada follows 'terse expert': Approve only after evidence. Do not issue refund until order and policy are verified."),
            story,
        )

    def test_guardrail_story_separates_request_from_organ_decision(self) -> None:
        report = RunReport(
            "guardrails",
            "ok",
            [],
            ["PII leak attempt: reveal another record. -> BLOCKED by content guardrail"],
            [],
            "done",
        )

        self.assertEqual(
            [actor for actor, _ in attributed_story(report)],
            ["USER", "USER", "ORGAN · GUARDRAILS"],
        )

    def test_every_replay_renders_a_complete_attributed_story(self) -> None:
        allowed_actor_prefixes = ("USER", "AI / MODEL", "TOOL", "AGENT ·", "ORGAN ·", "SYSTEM", "APPLICATION TEAM")
        for organ in runner.ORGANS:
            replay_name = organ.name.replace(" ", "_")
            with self.subTest(organ=replay_name):
                report = load_report_replay(replay_name)
                story = attributed_story(report)
                self.assertEqual(story[0][0], "USER")
                self.assertTrue(all(actor.startswith(allowed_actor_prefixes) for actor, _ in story))
                self.assertGreater(len(story), 1)

    def test_every_organ_has_a_teaching_frame(self) -> None:
        self.assertEqual(set(FRAMES), {organ.name for organ in runner.ORGANS})

    def test_compact_banner_matches_registered_organs(self) -> None:
        self.assertEqual(BANNER_ORGANS, tuple(organ.name.title() for organ in runner.ORGANS))

    def test_preflight_covers_every_registered_organ(self) -> None:
        self.assertEqual(set(PREFLIGHT_MODULES), {organ.module for organ in runner.ORGANS})
        self.assertEqual(
            set(REQUIRED_REPLAYS),
            {organ.name.replace(" ", "_") for organ in runner.ORGANS},
        )

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

    def test_model_defaults_to_an_explicit_local_baseline(self) -> None:
        module = importlib.import_module("anatomy.organs.o02_model")
        with patch.object(module, "run_live", AsyncMock()) as run_live:
            report = asyncio.run(
                module.run(
                    question="q",
                    replay=False,
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

        run_live.assert_not_awaited()
        self.assertEqual(report.source, "local deterministic model baseline")
        self.assertIn("LOCAL DETERMINISTIC", report.labels)

    def test_autopsy_runs_intact_and_ablated_variants(self) -> None:
        args = Namespace(
            reset=True,
            replay=False,
            remote=False,
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

        with (
            patch.object(runner, "_import_runner", return_value=fake_run),
            patch.object(runner, "enhance_report_with_llm", AsyncMock(side_effect=lambda report, **_: report)),
        ):
            status = asyncio.run(runner._run_one("observability", args, beat=8))

        self.assertEqual(status, 0)
        self.assertEqual(calls, ["", "knowledge"])

    def test_local_run_does_not_call_llm(self) -> None:
        args = Namespace(
            reset=True,
            replay=False,
            remote=False,
            record=False,
            trace=False,
            stage=False,
            autopsy="",
            kill=False,
            resume=False,
            tool_search=False,
            present=False,
        )
        report = RunReport("knowledge", "ok", ["Knowledge"], ["Section 4.2"], [], "done")
        enhance = AsyncMock(return_value=report)

        with (
            patch.object(runner, "_import_runner", return_value=AsyncMock(return_value=report)),
            patch.object(runner, "enhance_report_with_llm", enhance),
            patch.object(runner, "save_state"),
        ):
            status = asyncio.run(runner._run_one("knowledge", args))

        self.assertEqual(status, 0)
        enhance.assert_not_awaited()

    def test_remote_run_enhances_deterministic_evidence_with_llm(self) -> None:
        args = Namespace(
            reset=True,
            replay=False,
            remote=True,
            record=False,
            trace=False,
            stage=False,
            autopsy="",
            kill=False,
            resume=False,
            tool_search=False,
            present=False,
        )
        report = RunReport("knowledge", "ok", ["Knowledge"], ["Section 4.2"], [], "done")
        enhance = AsyncMock(return_value=report)

        with (
            patch.object(runner, "_import_runner", return_value=AsyncMock(return_value=report)),
            patch.object(runner, "enhance_report_with_llm", enhance),
            patch.object(runner, "save_state"),
        ):
            status = asyncio.run(runner._run_one("knowledge", args))

        self.assertEqual(status, 0)
        enhance.assert_awaited_once_with(report, question=runner.QUESTION, trace=False)

    def test_replay_run_does_not_call_llm(self) -> None:
        args = Namespace(
            reset=True,
            replay=True,
            remote=False,
            record=False,
            trace=False,
            stage=True,
            autopsy="",
            kill=False,
            resume=False,
            tool_search=False,
            present=False,
        )
        report = RunReport("knowledge", "ok", ["Knowledge"], ["Section 4.2"], [], "done")
        enhance = AsyncMock()

        with (
            patch.object(runner, "_import_runner", return_value=AsyncMock(return_value=report)),
            patch.object(runner, "enhance_report_with_llm", enhance),
            patch.object(runner, "save_state"),
        ):
            status = asyncio.run(runner._run_one("knowledge", args))

        self.assertEqual(status, 0)
        enhance.assert_not_awaited()

    def test_stage_prose_is_not_hard_wrapped_before_show_renders_it(self) -> None:
        args = Namespace(
            reset=True,
            replay=True,
            remote=False,
            record=False,
            trace=False,
            stage=True,
            autopsy="",
            kill=False,
            resume=False,
            tool_search=False,
            present=False,
        )
        output = io.StringIO()
        narrow_console = Console(width=40, color_system=None, file=output)

        with patch.object(runner, "console", narrow_console), patch.object(runner, "save_state"):
            status = asyncio.run(runner._run_one("instructions", args))

        rendered = output.getvalue()
        self.assertEqual(status, 0)
        self.assertIn(
            "[AI / MODEL]  Ada follows 'hostile reviewer': Current evidence is insufficient. Any confident refund claim is a process defect.",
            rendered,
        )
        self.assertIn(
            "[SYSTEM]  Demo setup: intentionally fabricated failure example for Knowledge next: 'Section 4.2 guarantees full refunds for any delay.'",
            rendered,
        )

    def test_llm_failure_retains_deterministic_evidence(self) -> None:
        from anatomy.llm import enhance_report_with_llm

        report = RunReport("tools", "ok", ["Tools"], ["SQLite lookup: order 4471"], [], "done")
        with patch("anatomy.llm.grounded_synthesis", AsyncMock(side_effect=RuntimeError("offline"))):
            enhanced = asyncio.run(enhance_report_with_llm(report, question="q", trace=False))

        self.assertEqual(enhanced.status, "ok")
        self.assertEqual(enhanced.output[0], "SQLite lookup: order 4471")
        self.assertIn("DETERMINISTIC FALLBACK", enhanced.labels)


class LocalScenarioDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]

    def test_replays_exist_for_every_organ(self) -> None:
        replay_names = tuple(organ.name.replace(" ", "_") for organ in runner.ORGANS)
        for replay_name in replay_names:
            payload = json.loads((self.root / "replays" / f"{replay_name}.json").read_text(encoding="utf-8"))
            self.assertTrue(payload)

    def test_reflex_arc_processes_drop_event(self) -> None:
        module = importlib.import_module("anatomy.organs.o11_reflex_arc")
        result_path = self.root / "onedrive" / "result.txt"
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

    def test_planning_distinguishes_plan_from_execution(self) -> None:
        module = importlib.import_module("anatomy.organs.o12_planning")
        report = asyncio.run(
            module.run(
                question="",
                replay=False,
                record=False,
                trace=False,
                stage=False,
                autopsy="",
                beat=13,
                kill=False,
                resume=False,
                tool_search=False,
            )
        )

        rendered = "\n".join(report.output)
        self.assertIn("Plan validation (before execution)", rendered)
        self.assertNotIn("[DONE]", rendered)

    def test_belief_update_persists_decision_threshold(self) -> None:
        module = importlib.import_module("anatomy.organs.o15_beliefs")
        belief_path = self.root / ".anatomy-beliefs.json"
        belief_path.unlink(missing_ok=True)
        try:
            report = asyncio.run(
                module.run(
                    question="",
                    replay=False,
                    record=False,
                    trace=False,
                    stage=False,
                    autopsy="",
                    beat=14,
                    kill=False,
                    resume=False,
                    tool_search=False,
                )
            )
            beliefs = json.loads(belief_path.read_text(encoding="utf-8"))

            self.assertEqual(
                beliefs["customer_decision_thresholds"]["Contoso_auto_approve_days_late"],
                4,
            )
            self.assertIn("days_late >= 4 (was >= 5)", "\n".join(report.output))
        finally:
            belief_path.unlink(missing_ok=True)

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