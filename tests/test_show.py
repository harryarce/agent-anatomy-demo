from __future__ import annotations

import io
import tokenize
import unittest
from importlib import metadata

from textual.widgets import RichLog, Static

from anatomy import runner
from anatomy.common import load_report_replay
from anatomy.show import ANATOMY, EXHIBITS, ROOT, SCENES, AnatomyShow, load_exhibit, stack_report


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
    def test_opening_runs_raw_model_before_instructions(self) -> None:
        self.assertEqual(runner.BEAT_SEQUENCE[0], ["model", "instructions"])
        opening_demo = SCENES[1]
        self.assertEqual(opening_demo.organs, (2, 1))
        self.assertIn("raw model", opening_demo.safe_steps[0].label)
        self.assertEqual(load_report_replay("model").firing, ["Model", "Observability", "Metabolism"])

    def test_route_is_complete_and_numbered(self) -> None:
        self.assertEqual([scene.number for scene in SCENES], list(range(1, len(SCENES) + 1)))
        self.assertEqual(len(SCENES), 19)

        implemented = {number for number, _, available in ANATOMY if available}
        self.assertEqual(implemented, set(range(1, 17)))
        demonstrated = {number for scene in SCENES for number in scene.organs}
        self.assertEqual(demonstrated, implemented)

    def test_planning_and_beliefs_are_executable_scenes(self) -> None:
        planning = next(scene for scene in SCENES if scene.organs == (12,))
        beliefs = next(scene for scene in SCENES if scene.organs == (15,))

        self.assertTrue(planning.safe_steps)
        self.assertTrue(beliefs.safe_steps)
        self.assertIn("13", planning.safe_steps[0].args)
        self.assertIn("14", beliefs.safe_steps[0].args)

    def test_every_demo_step_uses_the_real_cli_contract(self) -> None:
        parser = runner.build_parser()
        for scene in SCENES:
            for demo_step in (*scene.safe_steps, *scene.live_steps):
                parsed = parser.parse_args(demo_step.args)
                self.assertIn(parsed.command, {"beat", "spine", "tools"})

    def test_spine_kill_expects_the_demonstrated_failure(self) -> None:
        kill_step = next(scene for scene in SCENES if scene.number == 12).safe_steps[0]
        resume_step = next(scene for scene in SCENES if scene.number == 13).safe_steps[0]

        self.assertEqual(kill_step.expected_exit_codes, (1,))
        self.assertIn(".anatomy-spine-checkpoint.json", kill_step.cleanup)
        self.assertIn(".anatomy-spine-checkpoint.json", resume_step.required_files)
        self.assertIs(resume_step.prepare_if_missing, kill_step)

    def test_show_command_selects_scene_and_live_mode(self) -> None:
        args = runner.build_parser().parse_args(["show", "--from", "19", "--live"])

        self.assertEqual(args.from_scene, 19)
        self.assertTrue(args.live)


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
        signature, _, _ = load_exhibit(EXHIBITS[18][0])

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


class StackReportTests(unittest.TestCase):
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
    @staticmethod
    def rendered_log(app: AnatomyShow) -> str:
        log = app.query_one("#console", RichLog)
        return "\n".join(line.text for line in log.lines)

    async def test_keyboard_navigation_and_mode_switch(self) -> None:
        app = AnatomyShow()

        async with app.run_test(size=(120, 40)) as pilot:
            self.assertEqual(app.scene_index, 0)
            self.assertFalse(app.live)

            await pilot.press("right")
            self.assertEqual(app.scene_index, 1)

            await pilot.press("r")
            self.assertTrue(app.live)

            await pilot.press("end")
            self.assertEqual(app.scene_index, len(SCENES) - 1)

    async def test_speaker_can_show_and_hide_code_exhibits(self) -> None:
        app = AnatomyShow(start_scene=2)

        async with app.run_test(size=(120, 40)) as pilot:
            self.assertIsNone(app.exhibit_index)

            await pilot.press("c")
            self.assertEqual(app.exhibit_index, 0)
            self.assertIn("CODE EXHIBIT", self.rendered_log(app))
            self.assertIn("DEVELOPER RECIPE", self.rendered_log(app))
            self.assertIn("instructions=", self.rendered_log(app))
            self.assertIn("COPILOT STUDIO", self.rendered_log(app))

            await pilot.press("c")
            self.assertIsNone(app.exhibit_index)
            self.assertNotIn("CODE EXHIBIT", self.rendered_log(app))

    async def test_navigation_hides_an_open_exhibit(self) -> None:
        app = AnatomyShow(start_scene=5)

        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.press("c")
            self.assertEqual(app.exhibit_index, 0)

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

    async def test_complete_anatomy_rail_names_all_registered_organs(self) -> None:
        app = AnatomyShow(start_scene=18)

        async with app.run_test(size=(120, 40)):
            rail = app.query_one("#anatomy", Static).render().plain
            for organ in runner.ORGANS:
                self.assertIn(organ.name.title(), rail)
            self.assertIn("16 / 16 RUNNABLE ONLINE", rail)

    async def test_planning_and_beliefs_run_inside_show(self) -> None:
        app = AnatomyShow(start_scene=16)

        async with app.run_test(size=(120, 40)):
            await app.action_run_demo()
            self.assertIn("Plan validation (before execution)", self.rendered_log(app))
            app.scene_index = 16
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
        app = AnatomyShow(start_scene=15)

        async with app.run_test(size=(120, 40)):
            await app.action_run_demo()

            rendered = self.rendered_log(app)
            self.assertIn("Nobody typed anything", rendered)
            self.assertIn("EVIDENCE COMPLETE", rendered)

    async def test_direct_spine_resume_stages_missing_checkpoint(self) -> None:
        checkpoint = ROOT / ".anatomy-spine-checkpoint.json"
        checkpoint.unlink(missing_ok=True)
        app = AnatomyShow(start_scene=13)

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


if __name__ == "__main__":
    unittest.main()