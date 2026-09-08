from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from agent_framework import (
    ChatMiddleware,
    ChatResponse,
    Content,
    FileSkillsSource,
    FunctionMiddleware,
    Message,
    SessionContext,
    SkillsProvider,
    SkillsSourceContext,
)
from agent_framework.foundry import FoundryChatClient

from examples import organ_recipes as recipes


ROOT = Path(__file__).resolve().parents[1]


class RecipeBehaviorTests(unittest.IsolatedAsyncioTestCase):
    async def test_native_skills_discover_packages_and_load_real_instructions(self) -> None:
        agent = recipes.add_skill(object(), ROOT / "skills")
        skills = await FileSkillsSource(ROOT / "skills").get_skills(SkillsSourceContext(agent=agent))
        self.assertEqual(
            {skill.frontmatter.name for skill in skills},
            {"house-style", "pdf-summary", "triage-checklist"},
        )
        provider = next(item for item in agent.context_providers if isinstance(item, SkillsProvider))
        context = SessionContext(input_messages=[])
        await provider.before_run(agent=agent, session=agent.create_session(), context=context, state={})
        self.assertIn("triage-checklist", "\n".join(context.instructions))
        self.assertNotIn("Confirm order existence", "\n".join(context.instructions))
        loader = next(item for item in context.tools if item.name == "load_skill")
        contents = await loader.invoke(arguments={"skill_name": "triage-checklist"})
        self.assertIn("Confirm order existence", "".join(item.text or "" for item in contents))

    async def test_native_skill_tool_executes_in_framework_loop_without_network(self) -> None:
        client = FoundryChatClient(
            project_endpoint="https://example.invalid/api/projects/demo",
            model="offline",
            credential=MagicMock(),
        )
        first = ChatResponse(messages=Message("assistant", [Content.from_function_call(
            call_id="load-triage", name="load_skill", arguments={"skill_name": "triage-checklist"}
        )]))
        second = ChatResponse(messages=Message("assistant", ["Checklist loaded."]))
        try:
            with patch.object(client, "_inner_get_response", AsyncMock(side_effect=[first, second])) as infer:
                async with recipes.add_skill(client, ROOT / "skills") as agent:
                    result = await recipes.run_skill(agent, "Triage this escalation.")
                self.assertEqual(result, "Checklist loaded.")
                self.assertEqual(infer.await_count, 2)
                messages = infer.call_args.kwargs["messages"]
                tool_text = "\n".join(
                    str(content.result) for message in messages for content in message.contents
                    if content.type == "function_result"
                )
                self.assertIn("Confirm order existence", tool_text)
        finally:
            await client.client.close()
            await client.project_client.close()

    def test_read_only_approval_does_not_approve_scripts_or_hosted_tools(self) -> None:
        rule = SkillsProvider.read_only_tools_auto_approval_rule
        self.assertTrue(rule(Content.from_function_call(call_id="read", name="load_skill")))
        self.assertFalse(rule(Content.from_function_call(call_id="execute", name="run_skill_script")))
        self.assertFalse(rule(Content.from_function_call(
            call_id="remote", name="load_skill", additional_properties={"server_label": "untrusted"}
        )))

    async def test_run_skill_does_not_report_pending_approval_as_success(self) -> None:
        agent = MagicMock(run=AsyncMock(return_value=MagicMock(user_input_requests=[object()])))
        with self.assertRaisesRegex(RuntimeError, "explicit host approval"):
            await recipes.run_skill(agent, "Run a script.")
        agent.run.assert_awaited_once_with("Run a script.", session=agent.create_session.return_value)

    def test_planner_uses_structured_output_without_a_planning_tool(self) -> None:
        agent = recipes.add_planning(object())
        self.assertIs(agent.default_options["response_format"], recipes.ExecutionPlan)
        self.assertFalse(agent.default_options.get("tools"))

    async def test_plan_validation_rejects_invalid_dependencies_and_empty_plans(self) -> None:
        first = {"name": "verify", "depends_on": [], "success_condition": "Order verified"}
        second = {"name": "decide", "depends_on": ["verify"], "success_condition": "Policy checked"}
        agent = MagicMock(run=AsyncMock(return_value=MagicMock(value={"steps": [first, second]})))
        self.assertEqual(len((await recipes.create_plan(agent, "Refund request")).steps), 2)
        for steps in ([], [second, first], [first, first], [{**first, "depends_on": ["verify"]}]):
            with self.subTest(steps=steps):
                agent.run.return_value.value = {"steps": steps}
                with self.assertRaises(ValueError):
                    await recipes.create_plan(agent, "Refund request")

    def test_budget_wires_both_operation_boundaries(self) -> None:
        model_budget = MagicMock(spec=ChatMiddleware)
        tool_budget = MagicMock(spec=FunctionMiddleware)
        with patch.object(recipes, "Agent") as construct:
            recipes.add_budget(object(), model_budget, tool_budget)
        self.assertEqual(construct.call_args.kwargs["middleware"], [model_budget, tool_budget])

    async def test_identity_closes_clients_when_agent_fails(self) -> None:
        client = MagicMock()
        client.client.close = AsyncMock()
        client.project_client.close = AsyncMock()
        running_agent = MagicMock(run=AsyncMock(side_effect=RuntimeError("inference failed")))
        context_agent = MagicMock()
        context_agent.__aenter__ = AsyncMock(return_value=running_agent)
        context_agent.__aexit__ = AsyncMock(return_value=False)
        with (
            patch.object(recipes, "FoundryChatClient", return_value=client),
            patch.object(recipes, "DefaultAzureCredential") as credential,
            patch.object(recipes, "Agent", return_value=context_agent),
        ):
            with self.assertRaisesRegex(RuntimeError, "inference failed"):
                await recipes.run_with_identity("https://example.invalid", "offline", "test")
            credential.return_value.__aexit__.assert_awaited_once()
        client.client.close.assert_awaited_once()
        client.project_client.close.assert_awaited_once()

    async def test_resume_handles_missing_terminal_output(self) -> None:
        workflow = MagicMock(run=AsyncMock(return_value=MagicMock(get_outputs=lambda: [])))
        with self.assertRaisesRegex(RuntimeError, "no terminal output"):
            await recipes.resume_workflow(workflow, "checkpoint")
        workflow.run.assert_awaited_once_with(checkpoint_id="checkpoint")

    def test_learning_selects_candidate_without_publishing_it(self) -> None:
        evaluator = MagicMock(current="baseline")
        evaluator.score_current.return_value = 0.8
        for score, expected in ((0.9, "candidate"), (0.8, "baseline"), (0.7, "baseline")):
            evaluator.score.return_value = score
            self.assertEqual(recipes.promote_instruction("candidate", evaluator), expected)
            self.assertEqual(evaluator.current, "baseline")