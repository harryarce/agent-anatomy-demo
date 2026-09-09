from __future__ import annotations

import ast
import io
import tempfile
import tokenize
import unittest
from importlib import metadata
from pathlib import Path
from unittest.mock import patch

from textual.widgets import RichLog, Static

from anatomy import runner
from anatomy.common import load_report_replay
from anatomy.show import ANATOMY, EXHIBITS, ORGAN_FOCUS_BACKGROUND, ORGAN_HIGHLIGHTS, REPOSITORY_URL, ROOT, SCENES, AnatomyShow, CodeOverlay, DemoStep, ResultsOverlay, load_exhibit, repository_qr_text, stack_report
from agent_framework import Agent, InMemoryHistoryProvider, ToolApprovalMiddleware, Workflow
from examples import organ_recipes


def _code_density(snippet: str) -> float:
    """Share of non-blank lines carrying real tokens rather than docstring or comment prose."""
    populated = {index for index, line in enumerate(snippet.splitlines(), 1) if line.strip()}
    code: set[int] = set()
    try:
        for token in tokenize.generate_tokens(io.StringIO(snippet).readline):
            if token.type in (tokenize.NAME, tokenize.OP, tokenize.NUMBER):
                code.add(token.start[0])
    except (tokenize.TokenError, IndentationError):
        for index, line in enumerate(snippet.splitlines(), 1):
            stripped = line.strip()
            if stripped and not stripped.startswith(("#", '"""', "'''")) and any(c in stripped for c in "()=,"):
                code.add(index)
    return len(code & populated) / max(len(populated), 1)


class ShowRouteTests(unittest.TestCase):
    def test_organ_numbers_follow_first_demo_appearance(self) -> None:
        numbers = list(dict.fromkeys(number for scene in SCENES if scene.safe_steps for number in scene.organs))
        self.assertEqual(numbers, list(range(1, 17)))
        names = ["Model", "Instructions", "Knowledge", "Tools", "Memory", "Guardrails",
                 "Orchestration", "Identity", "Observability", "Metabolism", "Spine",
                 "Skills", "Learning", "Reflex Arc", "Planning", "Beliefs"]
        self.assertEqual([(number, name) for number, name, _ in ANATOMY], list(enumerate(names, 1)))
        for index, name in enumerate(names, 1):
            self.assertEqual(runner.ORGAN_BY_NAME[name.lower()].number, index)
        app = AnatomyShow(start_scene=2)
        self.assertIn("01  Model  FIRING", app._anatomy_text(SCENES[1]).plain)
        self.assertIn("02  Instructions", app._anatomy_text(SCENES[1]).plain)

    def test_every_organ_has_an_applicability_highlight(self) -> None:
        self.assertEqual(set(ORGAN_HIGHLIGHTS), set(range(1, 17)))
        for highlight in ORGAN_HIGHLIGHTS.values():
            self.assertTrue(highlight.role)
            self.assertTrue(highlight.use_it_to)
            self.assertTrue(highlight.enhancement)

    def test_opening_runs_model_and_instructions_as_separate_scenes(self) -> None:
        self.assertEqual(runner.BEAT_SEQUENCE[0], ["model", "instructions"])
        model_demo, instructions_demo = SCENES[1:3]
        self.assertEqual(model_demo.organs, (1,))
        self.assertEqual(instructions_demo.organs, (2,))
        self.assertEqual(model_demo.safe_steps[0].args[:2], ("demo", "model"))
        self.assertEqual(instructions_demo.safe_steps[0].args[:2], ("demo", "instructions"))
        self.assertEqual(load_report_replay("model").firing, ["Model"])
        self.assertEqual(load_report_replay("instructions").firing, ["Instructions"])

    def test_route_is_complete_and_numbered(self) -> None:
        self.assertEqual([scene.number for scene in SCENES], list(range(1, len(SCENES) + 1)))
        self.assertEqual(len(SCENES), 20)

        implemented = {number for number, _, available in ANATOMY if available}
        self.assertEqual(implemented, set(range(1, 17)))
        demonstrated = {number for scene in SCENES for number in scene.organs}
        self.assertEqual(demonstrated, implemented)

    def test_planning_and_beliefs_are_executable_scenes(self) -> None:
        planning = next(scene for scene in SCENES if scene.organs == (15,))
        beliefs = next(scene for scene in SCENES if scene.organs == (16,))

        self.assertTrue(planning.safe_steps)
        self.assertTrue(beliefs.safe_steps)
        self.assertIn("13", planning.safe_steps[0].args)
        self.assertIn("14", beliefs.safe_steps[0].args)

    def test_every_demo_step_uses_the_real_cli_contract(self) -> None:
        parser = runner.build_parser()
        for scene in SCENES:
            for demo_step in (*scene.safe_steps, *scene.live_steps):
                parsed = parser.parse_args(demo_step.args)
                self.assertIn(parsed.command, {"beat", "demo", "spine", "tools"})

    def test_spine_kill_expects_the_demonstrated_failure(self) -> None:
        kill_step = next(scene for scene in SCENES if scene.number == 13).safe_steps[0]
        resume_step = next(scene for scene in SCENES if scene.number == 14).safe_steps[0]

        self.assertEqual(kill_step.expected_exit_codes, (1,))
        self.assertIn(".anatomy-spine-checkpoint.json", kill_step.cleanup)
        self.assertIn(".anatomy-spine-checkpoint.json", resume_step.required_files)
        self.assertIs(resume_step.prepare_if_missing, kill_step)

    def test_show_command_selects_scene_and_remote_mode(self) -> None:
        args = runner.build_parser().parse_args(["show", "--from", "20", "--remote"])

        self.assertEqual(args.from_scene, 20)
        self.assertTrue(args.remote)

    def test_demo_defaults_local_and_rejects_conflicting_execution_modes(self) -> None:
        args = runner.build_parser().parse_args(["demo", "knowledge"])
        self.assertFalse(args.remote)
        self.assertFalse(args.replay)

        with self.assertRaises(SystemExit):
            runner.build_parser().parse_args(["demo", "knowledge", "--remote", "--replay"])


class CodeExhibitTests(unittest.TestCase):
    def test_every_exhibit_resolves_to_real_source(self) -> None:
        for scene_number, exhibits in EXHIBITS.items():
            for exhibit in exhibits:
                with self.subTest(scene=scene_number, path=exhibit.display_path):
                    snippet, start_line, focus_line = load_exhibit(exhibit)
                    self.assertIn(exhibit.anchor, snippet)
                    self.assertGreaterEqual(focus_line, start_line)
                    self.assertTrue(exhibit.read_this)

    def test_exhibits_are_developer_recipes_in_the_repository(self) -> None:
        for exhibits in EXHIBITS.values():
            for exhibit in exhibits:
                with self.subTest(path=exhibit.path):
                    self.assertTrue((ROOT / exhibit.path).exists())
                    self.assertEqual(exhibit.provenance, "DEVELOPER RECIPE")
                    self.assertNotIn("site-packages", exhibit.display_path)

    def test_whole_anatomy_recipe_names_every_attachment_point(self) -> None:
        signature, _, _ = load_exhibit(EXHIBITS[19][0])

        for parameter in ("instructions=", "tools=", "context_providers=", "middleware="):
            self.assertIn(parameter, signature)

    def test_python_snippets_are_mostly_code_not_docstrings(self) -> None:
        for scene_number, exhibits in EXHIBITS.items():
            for exhibit in exhibits:
                if exhibit.language != "python":
                    continue
                snippet, _, _ = load_exhibit(exhibit)
                with self.subTest(scene=scene_number, title=exhibit.title):
                    self.assertGreaterEqual(_code_density(snippet), 0.75)

    def test_python_snippets_are_complete_valid_python(self) -> None:
        for scene_number, exhibits in EXHIBITS.items():
            for exhibit in exhibits:
                if exhibit.language != "python":
                    continue
                snippet, _, _ = load_exhibit(exhibit)
                with self.subTest(scene=scene_number, title=exhibit.title):
                    ast.parse(snippet)

    def test_focus_line_is_code_rather_than_prose(self) -> None:
        for scene_number, exhibits in EXHIBITS.items():
            for exhibit in exhibits:
                if exhibit.language != "python":
                    continue
                snippet, start_line, focus_line = load_exhibit(exhibit)
                focus = snippet.splitlines()[focus_line - start_line].strip()
                with self.subTest(scene=scene_number, title=exhibit.title):
                    self.assertFalse(focus.startswith(("#", '"""', "'''")))
                    self.assertTrue(any(token in focus for token in "():=,"))

    def test_snippets_stay_within_a_readable_window(self) -> None:
        for exhibits in EXHIBITS.values():
            for exhibit in exhibits:
                snippet, _, _ = load_exhibit(exhibit)
                with self.subTest(title=exhibit.title):
                    self.assertLessEqual(len(snippet.splitlines()), 20)

    def test_expanded_exhibits_include_more_source_context(self) -> None:
        exhibit = EXHIBITS[2][0]
        inline, _, _ = load_exhibit(exhibit)
        expanded, _, _ = load_exhibit(exhibit, expanded=True)

        self.assertGreater(len(expanded.splitlines()), len(inline.splitlines()))

    def test_exhibits_are_attached_to_real_scenes(self) -> None:
        scene_numbers = {scene.number for scene in SCENES}

        self.assertTrue(set(EXHIBITS).issubset(scene_numbers))

    def test_every_demonstrated_organ_scene_has_an_exhibit(self) -> None:
        demo_scenes = {scene.number for scene in SCENES if scene.safe_steps}

        self.assertEqual(demo_scenes - set(EXHIBITS), set())

    def test_exhibits_include_copilot_studio_guidance(self) -> None:
        for scene_number, exhibits in EXHIBITS.items():
            for exhibit in exhibits:
                with self.subTest(scene=scene_number, title=exhibit.title):
                    self.assertTrue(exhibit.copilot_studio)


class RecipeApiTests(unittest.TestCase):
    def test_model_and_instructions_recipes_are_separate_framework_agents(self) -> None:
        model_agent = organ_recipes.build_model_agent(object())
        instructed_agent = organ_recipes.add_instructions(object())

        self.assertIsInstance(model_agent, Agent)
        self.assertNotIn("instructions", model_agent.default_options)
        self.assertIsInstance(instructed_agent, Agent)
        self.assertIn("verified policy", instructed_agent.default_options["instructions"])

    def test_screenshot_recipes_accept_framework_provider_and_middleware(self) -> None:
        memory_agent = organ_recipes.add_memory(object(), InMemoryHistoryProvider())
        guarded_agent = organ_recipes.add_guardrails(object(), ToolApprovalMiddleware())

        self.assertIsInstance(memory_agent, Agent)
        self.assertIsInstance(guarded_agent, Agent)

    def test_workflow_and_checkpoint_recipes_use_framework_workflows(self) -> None:
        agents = [Agent(client=object(), name=name) for name in ("researcher", "writer", "reviewer")]
        reviewed = organ_recipes.build_reviewed_workflow(*agents)
        with tempfile.TemporaryDirectory() as directory:
            checkpointed = organ_recipes.build_checkpointed_workflow(*agents, Path(directory))

        self.assertIsInstance(reviewed, Workflow)
        self.assertIsInstance(checkpointed, Workflow)

    def test_observability_recipe_calls_public_configuration_api(self) -> None:
        with patch.object(organ_recipes, "configure_otel_providers") as configure:
            organ_recipes.enable_observability()

        configure.assert_called_once_with(env_file_path=".env")


class StackReportTests(unittest.TestCase):
    def test_repository_qr_encodes_the_documented_github_url(self) -> None:
        rendered = repository_qr_text().plain

        self.assertEqual(REPOSITORY_URL, "https://github.com/harryarce/agent-anatomy-demo")
        self.assertIn("SCAN TO OPEN REPO", rendered)
        self.assertLessEqual(max(map(len, rendered.splitlines())), 37)
        self.assertGreater(rendered.count("█") + rendered.count("▀") + rendered.count("▄"), 200)

    def test_stack_reports_resolved_versions(self) -> None:
        rows = dict(stack_report())

        self.assertIn("Python", rows)
        for label in ("Microsoft Agent Framework", "Foundry connector", "Rich", "Textual"):
            with self.subTest(label=label):
                self.assertIn(label, rows)
                self.assertNotEqual(rows[label], "installed")
                self.assertRegex(rows[label], r"^\d+\.\d+")

    def test_pinned_requirements_match_installed_versions(self) -> None:
        pins = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

        for line in (entry.strip() for entry in pins):
            if not line or "==" not in line:
                continue
            distribution, pinned = line.split("==", 1)
            with self.subTest(distribution=distribution):
                self.assertEqual(metadata.version(distribution), pinned)


class ShowInteractionTests(unittest.IsolatedAsyncioTestCase):
    async def test_scene_heading_shows_organ_without_act_prefix(self) -> None:
        app = AnatomyShow(start_scene=6)
        async with app.run_test(size=(120, 40)) as pilot:
            heading = app.query_one("#eyebrow", Static)
            self.assertEqual(heading.render().plain, "TOOL DISCOVERY")
            self.assertIn("ACT II: ACTING AND REMEMBERING", app.query_one("#brand", Static).render().plain)

            app.scene_index = 11
            app._render_scene()
            await pilot.pause()
            self.assertEqual(heading.render().plain, "METABOLISM")
            await pilot.press("home")
            self.assertEqual(heading.render().plain, "THE DISSECTION BEGINS")
            await pilot.press("end")
            self.assertEqual(heading.render().plain, "TAKE IT WITH YOU")

    async def test_title_bar_highlights_current_act_next_to_scene(self) -> None:
        app = AnatomyShow(start_scene=9)
        async with app.run_test(size=(80, 30)) as pilot:
            await pilot.pause()
            brand = app.query_one("#brand", Static)
            title = brand.render()
            self.assertIn("SCENE 09/20   |   ACT III: CONTROL AND VISIBILITY", title.plain)
            highlight = title.get_style_at_offset(title.plain.index("ACT III"))
            self.assertEqual(highlight.background.hex, "#F2CC60")
            self.assertTrue(highlight.bold)
            self.assertGreaterEqual(brand.content_size.height, 2)

            await pilot.press("right", "right", "right")
            self.assertIn("ACT IV: LIMITS AND RECOVERY", brand.render().plain)
            await pilot.press("home")
            self.assertNotIn("ACT IV", brand.render().plain)

    @staticmethod
    def rendered_log(app: AnatomyShow) -> str:
        log = app.query_one("#console", RichLog)
        return "\n".join(line.text for line in log.lines)

    async def test_keyboard_navigation_and_mode_switch(self) -> None:
        app = AnatomyShow()

        async with app.run_test(size=(120, 40)) as pilot:
            self.assertEqual(app.scene_index, 0)
            self.assertFalse(app.remote)

            await pilot.press("right")
            self.assertEqual(app.scene_index, 1)

            await pilot.press("r")
            self.assertTrue(app.remote)

            await pilot.press("end")
            self.assertEqual(app.scene_index, len(SCENES) - 1)

    async def test_model_and_instructions_have_separate_code_exhibits(self) -> None:
        app = AnatomyShow(start_scene=2)

        async with app.run_test(size=(120, 40)) as pilot:
            self.assertIsNone(app.exhibit_index)

            await pilot.press("c")
            self.assertEqual(app.exhibit_index, 0)
            self.assertIsInstance(app.screen, CodeOverlay)
            self.assertIn("CODE EXHIBIT", self.rendered_log(app))
            self.assertIn("DEVELOPER RECIPE", self.rendered_log(app))
            self.assertIn("build_model_agent", self.rendered_log(app))
            self.assertNotIn("instructions=", self.rendered_log(app))
            self.assertIn("COPILOT STUDIO", self.rendered_log(app))
            self.assertIn("ORGAN FOCUS", self.rendered_log(app))
            focus_backgrounds = {
                segment.style.bgcolor.triplet.hex
                for line in app.screen.query_one("#expanded-code", RichLog).lines
                for segment in line
                if segment.style and segment.style.bgcolor and segment.style.bgcolor.triplet
            }
            self.assertIn(ORGAN_FOCUS_BACKGROUND.lower(), focus_backgrounds)

            await pilot.press("c")
            await pilot.pause()
            self.assertIsNone(app.exhibit_index)
            self.assertNotIsInstance(app.screen, CodeOverlay)
            self.assertNotIn("CODE EXHIBIT", self.rendered_log(app))

            await pilot.press("right")
            await pilot.press("c")
            self.assertIsInstance(app.screen, CodeOverlay)
            self.assertIn("add_instructions", self.rendered_log(app))
            self.assertIn("instructions=", self.rendered_log(app))

    async def test_x_expands_and_collapses_the_current_code_exhibit(self) -> None:
        app = AnatomyShow(start_scene=2)

        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("c")
            inline_lines = len(app.query_one("#console", RichLog).lines)

            self.assertIsInstance(app.screen, CodeOverlay)
            expanded_log = app.screen.query_one("#expanded-code", RichLog)
            self.assertGreater(len(expanded_log.lines), inline_lines)
            await pilot.pause()
            self.assertEqual(expanded_log.scroll_y, 0)
            self.assertGreater(expanded_log.max_scroll_y, 0)
            await pilot.press("pagedown")
            await pilot.pause()
            self.assertGreater(expanded_log.scroll_y, 0)

            await pilot.press("x")
            await pilot.pause()
            self.assertNotIsInstance(app.screen, CodeOverlay)
            self.assertEqual(app.exhibit_index, 0)

            await pilot.press("x")
            await pilot.pause()
            self.assertEqual(app.screen.query_one("#expanded-code", RichLog).scroll_y, 0)
            await pilot.press("escape")
            await pilot.pause()
            self.assertNotIsInstance(app.screen, CodeOverlay)

    async def test_x_expands_and_collapses_completed_results(self) -> None:
        app = AnatomyShow(start_scene=2)

        async with app.run_test(size=(100, 30)) as pilot:
            await app.action_run_demo()
            inline_results = self.rendered_log(app)
            self.assertIn("EVIDENCE COMPLETE", inline_results)
            inline_firing_styles = [
                segment.style
                for line in app.query_one("#console", RichLog).lines
                if "ORGANS FIRING" in line.text
                for segment in line
                if segment.text.strip()
            ]

            self.assertIsInstance(app.screen, ResultsOverlay)
            expanded_log = app.screen.query_one("#expanded-results", RichLog)
            self.assertIn("EVIDENCE COMPLETE", "\n".join(line.text for line in expanded_log.lines))
            await pilot.pause()
            self.assertEqual(expanded_log.scroll_y, 0)
            self.assertGreater(expanded_log.max_scroll_y, 0)
            await pilot.press("pagedown")
            await pilot.pause()
            self.assertGreater(expanded_log.scroll_y, 0)
            expanded_firing_styles = [
                segment.style
                for line in expanded_log.lines
                if "ORGANS FIRING" in line.text
                for segment in line
                if segment.text.strip()
            ]
            self.assertTrue(inline_firing_styles)
            self.assertEqual(expanded_firing_styles, inline_firing_styles)

            await pilot.press("x")
            await pilot.pause()
            self.assertNotIsInstance(app.screen, ResultsOverlay)

            await pilot.press("x")
            await pilot.pause()
            self.assertEqual(app.screen.query_one("#expanded-results", RichLog).scroll_y, 0)
            await pilot.press("escape")
            await pilot.pause()
            self.assertNotIsInstance(app.screen, ResultsOverlay)

    async def test_each_opening_organ_has_a_prominent_applicability_spotlight(self) -> None:
        app = AnatomyShow(start_scene=2)

        async with app.run_test(size=(120, 40)) as pilot:
            model_role = app.query_one("#organ-role", Static).render().plain
            self.assertIn("MODEL  ·  THE BRAIN", model_role)
            self.assertIn("USE IT TO", model_role)
            self.assertIn("ADDS TO THE AGENT", model_role)

            await pilot.press("right")
            instructions_role = app.query_one("#organ-role", Static).render().plain
            self.assertIn("INSTRUCTIONS  ·  THE JOB DESCRIPTION", instructions_role)
            self.assertIn("Define role, priorities, tone, and boundaries.", instructions_role)

    async def test_model_and_instructions_run_as_separate_evidence(self) -> None:
        app = AnatomyShow(start_scene=2)

        async with app.run_test(size=(120, 40)) as pilot:
            await app.action_run_demo()
            model_evidence = self.rendered_log(app)
            self.assertIn("ORGANS FIRING:  Model", model_evidence)
            self.assertNotIn("ORGANS FIRING:  Instructions", model_evidence)

            await pilot.press("x")
            await pilot.press("right")
            await app.action_run_demo()
            instruction_evidence = self.rendered_log(app)
            self.assertIn("ORGANS FIRING:  Instructions", instruction_evidence)
            self.assertNotIn("ORGANS FIRING:  Model", instruction_evidence)

    async def test_navigation_after_collapsing_hides_an_open_exhibit(self) -> None:
        app = AnatomyShow(start_scene=5)

        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("c")
            self.assertEqual(app.exhibit_index, 0)

            await pilot.press("x")
            await pilot.press("right")
            self.assertIsNone(app.exhibit_index)
            self.assertNotIn("CODE EXHIBIT", self.rendered_log(app))

    async def test_opening_scene_shows_the_ada_banner_only(self) -> None:
        app = AnatomyShow()

        async with app.run_test(size=(120, 40)) as pilot:
            opening = self.rendered_log(app)
            self.assertIn("a n a t o m y", opening)
            self.assertIn("Sixteen organs run here", opening)

            await pilot.press("right")
            self.assertNotIn("a n a t o m y", self.rendered_log(app))

    async def test_opening_banner_fits_laptop_terminals_without_scrolling(self) -> None:
        for size in ((100, 24), (120, 30), (140, 40)):
            with self.subTest(size=size):
                app = AnatomyShow()
                async with app.run_test(size=size) as pilot:
                    await pilot.pause()
                    log = app.query_one("#console", RichLog)
                    self.assertEqual(log.max_scroll_y, 0)
                    self.assertEqual(log.max_scroll_x, 0)
                    self.assertLessEqual(len(log.lines), log.scrollable_content_region.height)
                    self.assertLessEqual(app.query_one("#landing").region.bottom, size[1] - 3)
                    self.assertTrue(app.query_one("#stage").has_class("opening"))

                    await pilot.press("right")
                    self.assertFalse(app.query_one("#stage").has_class("opening"))
                    self.assertEqual(app.query_one("#scene-title").size.height, 3)

                    await pilot.press("home")
                    await pilot.pause()
                    self.assertEqual(log.max_scroll_y, 0)

    async def test_complete_anatomy_rail_names_all_registered_organs(self) -> None:
        app = AnatomyShow(start_scene=19)

        async with app.run_test(size=(120, 40)):
            rail = app.query_one("#anatomy", Static).render().plain
            for organ in runner.ORGANS:
                self.assertIn(organ.name.title(), rail)
            self.assertIn("16 / 16 RUNNABLE ONLINE", rail)

    async def test_repository_qr_appears_only_on_scene_twenty(self) -> None:
        app = AnatomyShow(start_scene=19)

        async with app.run_test(size=(120, 35)) as pilot:
            qr_panel = app.query_one("#repo-qr", Static)
            self.assertFalse(qr_panel.display)

            await pilot.press("right")
            self.assertTrue(qr_panel.display)
            self.assertIn("SCAN TO OPEN REPO", qr_panel.render().plain)
            self.assertGreater(qr_panel.region.x, 70)
            self.assertLessEqual(qr_panel.region.y, 5)
            self.assertLessEqual(qr_panel.region.bottom, 35)
            self.assertIn(REPOSITORY_URL, SCENES[-1].message)

    async def test_planning_and_beliefs_run_inside_show(self) -> None:
        app = AnatomyShow(start_scene=17)

        async with app.run_test(size=(120, 40)):
            await app.action_run_demo()
            self.assertIn("Plan validation (before execution)", self.rendered_log(app))
            app.screen.dismiss()
            app.scene_index = 17
            app._render_scene()
            await app.action_run_demo()
            self.assertIn("Contoso_auto_approve_days_late", self.rendered_log(app))

    async def test_completed_demo_scrolls_output_back_to_top(self) -> None:
        app = AnatomyShow(start_scene=2)

        async with app.run_test(size=(80, 20)) as pilot:
            await app.action_run_demo()
            await pilot.pause()

            log = app.query_one("#console", RichLog)
            self.assertGreater(log.max_scroll_y, 0)
            self.assertEqual(log.scroll_y, 0)

    async def test_stage_safe_reflex_arc_runs_inside_show(self) -> None:
        app = AnatomyShow(start_scene=16)

        async with app.run_test(size=(120, 40)):
            await app.action_run_demo()

            rendered = self.rendered_log(app)
            self.assertIn("Nobody typed anything", rendered)
            self.assertIn("EVIDENCE COMPLETE", rendered)

    async def test_direct_spine_resume_stages_missing_checkpoint(self) -> None:
        checkpoint = ROOT / ".anatomy-spine-checkpoint.json"
        checkpoint.unlink(missing_ok=True)
        app = AnatomyShow(start_scene=14)

        try:
            async with app.run_test(size=(120, 40)):
                await app.action_run_demo()

                rendered = self.rendered_log(app)
                self.assertIn("CHECKPOINT ABSENT", rendered)
                self.assertIn("EXPECTED EXIT  1", rendered)
                self.assertIn("SKIP validate_order", rendered)
                self.assertIn("EVIDENCE COMPLETE", rendered)
        finally:
            checkpoint.unlink(missing_ok=True)

    async def test_unexpected_exit_is_visible_and_persisted(self) -> None:
        app = AnatomyShow(start_scene=2)
        with tempfile.TemporaryDirectory() as temporary_directory:
            error_log = Path(temporary_directory) / "errors.log"
            with patch("anatomy.show.ERROR_LOG", error_log):
                async with app.run_test(size=(120, 40)):
                    succeeded = await app._run_steps(
                        (DemoStep("Force a command failure", ("not-a-command",)),),
                        app.query_one("#console", RichLog),
                    )

                    rendered = self.rendered_log(app)
                    self.assertFalse(succeeded)
                    self.assertIn("STATUS  FAILED", rendered)
                    self.assertIn("UNEXPECTED EXIT", rendered)
                    self.assertIn("ERROR LOG  errors.log", rendered)
                    persisted = error_log.read_text(encoding="utf-8")
                    self.assertIn("not-a-command", persisted)
                    self.assertIn("captured output", persisted)

    async def test_deterministic_fallback_is_visible_and_persisted(self) -> None:
        app = AnatomyShow(start_scene=2)
        with tempfile.TemporaryDirectory() as temporary_directory:
            error_log = Path(temporary_directory) / "errors.log"
            process = unittest.mock.AsyncMock()
            process.communicate.return_value = (b"DETERMINISTIC FALLBACK\nlocal evidence retained", None)
            process.returncode = 0
            with (
                patch("anatomy.show.ERROR_LOG", error_log),
                patch("anatomy.show.asyncio.create_subprocess_exec", return_value=process),
            ):
                async with app.run_test(size=(120, 40)):
                    succeeded = await app._run_steps(
                        (DemoStep("Force an LLM fallback", ("beat", "1")),),
                        app.query_one("#console", RichLog),
                    )

                    rendered = self.rendered_log(app)
                    self.assertTrue(succeeded)
                    self.assertIn("STATUS  PASSED WITH FALLBACK", rendered)
                    self.assertIn("ERROR LOG  errors.log", rendered)
                    self.assertIn("DEGRADED", error_log.read_text(encoding="utf-8"))

    async def test_remote_mode_is_explicit_in_the_spawned_command(self) -> None:
        app = AnatomyShow(start_scene=2, remote=True)
        process = unittest.mock.AsyncMock()
        process.communicate.return_value = (b"remote evidence", None)
        process.returncode = 0

        with patch("anatomy.show.asyncio.create_subprocess_exec", return_value=process) as create_process:
            async with app.run_test(size=(120, 40)):
                await app.action_run_demo()

        command = create_process.call_args.args
        self.assertIn("--remote", command)


if __name__ == "__main__":
    unittest.main()