# Audience Code Review

Reviewed 2026-09-08 against [microsoft/agent-framework](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples), commit `a03bb909c694ad27f0b14d310d39e7f9e232ad39`.

Follow-up: [reuse research and prioritized implementation recommendations](REUSE-RESEARCH.md), including Agent Governance Toolkit compatibility findings and other Microsoft-origin projects.

## Version Boundary

- The demo's installed `agent-framework-core==1.14.0` and `agent-framework-foundry==1.11.0` passed all 53 recipe and show tests.
- A separate, isolated environment with core `1.16.0` and Foundry `1.11.0` passed 25 focused recipe, API, and code-exhibit tests. Packages installed successfully from `https://packagefeedproxy.microsoft.io/pypi/simple`, with TLS verification enabled.
- Public PyPI reported core `1.17.0` and Foundry `1.12.0` at review time. These are not the installed versions.
- Latest-release installation was attempted only in a temporary environment. The Microsoft feed listed versions only through core `1.16.0` and Foundry `1.11.0`; the public package CDN failed TLS handshakes from both pip and PowerShell. Public-latest runtime compatibility is therefore **not verified**.
- Requirements and the stage virtual environment were not upgraded. Upstream `main` samples can depend on APIs newer than a released package; use the pinned source links below and rerun tests before upgrading.

## What The Audience Is Seeing

[organ_recipes.py](organ_recipes.py) contains small attachment recipes, not the implementation behind the stage transcripts. `--remote` synthesizes the local transcript with a model; it does not execute these recipes. A successful stage run does not validate the recipes.

Passing a provider or middleware object is legitimate framework composition, but the passed object must actually implement retrieval, storage, authorization, or metering. Neither a parameter name nor a prompt supplies that implementation.

## All 16 Organs

| Organ | Correct Mechanism | Review Result And Official Reference |
| --- | --- | --- |
| Instructions | `Agent(instructions=...)` | Correct behavioral guidance, not enforcement. [Getting started](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/01-get-started). |
| Model | Client passed to `Agent` | Correct; caller configures endpoint, deployment, and credentials. [Provider samples](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/providers). |
| Knowledge | Retrieval context provider, or a supported retrieval tool | Correct attachment, not a retriever implementation. Citations need validation. [Azure AI Search](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/context_providers/azure_ai_search). |
| Tools | `@tool` and `tools=[...]`; MCP for remote tools | Function recipe is valid. `max_invocations=1` is the instance lifetime, not a per-run quota. The demo YAML only illustrates metadata and is not an SDK registration format. [Tool samples](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/tools), [MCP samples](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/mcp). |
| Skills | `SkillsProvider.from_paths(...)` in `context_providers` | **Corrected:** previously just a `FunctionTool`. Added required frontmatter to three packages, read-only approval middleware, and session-aware invocation. Provider advertises metadata, then exposes loading/resource/script tools. [File-based skills](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/skills/file_based_skill/file_based_skill.py), [selective approval](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/skills/skills_auto_approval/skills_auto_approval.py). |
| Memory | Context provider plus persistent, user-scoped backing store | Attachment is valid; in-memory conversation history is not cross-session memory. Caller must enforce tenant/user isolation. [File memory](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/context_providers/file_memory_provider.py), [Foundry memory](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/context_providers/azure_ai_foundry_memory.py). |
| Guardrails | Agent, chat, and function middleware at the relevant boundary | **Corrected:** accepts the public middleware union, rather than implying all checks wrap only an agent run. No PII filter or authorization policy is implemented by this constructor. [Middleware](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/middleware), [tool-boundary validation](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/middleware/atr_validation_middleware.py). |
| Orchestration | `WorkflowBuilder`, executors, edges | Valid sequential handoff; a reviewer at the end is not an enforced approval gate. Add typed decisions and conditional edges for rework/rejection. [Control flow](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/03-workflows/control-flow). |
| Identity | Entra credential on the service client plus resource authorization | **Corrected:** closes owned inference/project clients on success or failure. `DefaultAzureCredential` does not establish a unique per-agent identity, tool permissions, or RBAC. Choose a specific credential for production. [Foundry provider samples](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/providers), [identity guidance](https://learn.microsoft.com/azure/developer/python/sdk/authentication/overview). |
| Observability | Framework instrumentation and OpenTelemetry configuration | Public configuration call is correct. Exporter setup and emitted spans must be tested separately; printed trace strings are not traces. [Observability samples](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/observability). |
| Reflex Arc | Host event subscription invokes an agent | Handler is valid, but does not install a trigger. Host owns authentication, schema validation, deduplication, retries, and idempotency. [Hosting samples](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/04-hosting). |
| Planning | Structured model output followed by deterministic validation | **Corrected:** no required planning tool. Pydantic defines the plan; host rejects empty plans, duplicates, missing dependencies, cycles, and out-of-order dependencies. Business feasibility and authorization remain separate. [Structured output](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/providers/openai/client_with_structured_output.py). |
| Spine | Checkpoint storage, workflow resume, idempotent side effects | Builder and resume API are valid. **Corrected:** no-output resumes are not indexed as if finished. Checkpoints do not guarantee exactly-once external side effects. [Checkpoint/resume](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/03-workflows/checkpoint/checkpoint_with_resume.py). |
| Metabolism | Per-operation chat/function middleware with application accounting | **Corrected:** attach checks at model/tool boundaries. This is not an implemented hard dollar cap. Reserve budget, bound output, account for concurrency, and reconcile actual usage; a prompt or post-call meter cannot prevent all overspend. [Chat middleware](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/middleware/chat_middleware.py), [invocation limits](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/tools/function_invocation_configuration.py). |
| Beliefs | Application state through a context provider and validated update path | Not a native `Beliefs` API. A tool is one update mechanism, not a requirement. Enforce provenance, authorization, versioning, and policy invariants outside prompts. [Workflow state](https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/03-workflows/state-management/state_with_agents.py). |
| Learning | Evaluation and controlled scaffold updates outside inference | Recipe selects a higher-scoring string; it neither trains nor publishes anything. Use held-out cases, safety gates, human approval, and versioning. [Evaluation samples](https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/evaluation). |

## Copilot Studio Is Not One API Surface

- [Standard-harness generative orchestration](https://learn.microsoft.com/microsoft-copilot-studio/advanced-generative-actions) selects topics, tools, agents, and knowledge. Topics and flows can express deterministic business sequences. This is not equivalent to Python `WorkflowBuilder` or checkpoint resume.
- The [GitHub Copilot harness](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/overview) has a different authoring surface with Build, Preview, Evaluate, and Monitor. Its documented tools/skills distinction must not be collapsed into tools alone. Do not imply Python `SkillsProvider` or a portable SKILL.md import contract without confirming support in that authoring experience.
- [Memory (preview)](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/memory-overview) applies to the GitHub Copilot harness. It is per user, expires after 28 days of inactivity, and is disabled in group chats and Teams channels. It is not a general durable business-record database.
- [Event triggers](https://learn.microsoft.com/microsoft-copilot-studio/authoring-triggers-about) require explicit setup and careful connection identity selection; do not present them as automatically inheriting an end user's permissions.
- Studio analytics/capacity controls are not proof of a synchronous per-run dollar cap. Dataverse records plus idempotent actions are application designs, not built-in Agent Framework checkpoint compatibility.

## Remaining Stage-Demo Limitations

These were reviewed but deliberately not rewritten during the audience-code correction:

- Skills lists filenames and fixed token counts; it does not use the native provider. Native loading is exercised in the recipe tests instead.
- Guardrails, orchestration, planning, and the displayed span tree are scripted examples, not executed policy checks, a conditional workflow, a planner, or collected spans.
- Memory overwrites its sample preference and recalls from the same dictionary; two printed thread IDs do not prove independent-session retrieval.
- Beliefs writes fixed updates, including a lowered customer threshold; it does not evaluate evidence, preserve version history, or demonstrate a downstream policy engine. Learned beliefs must not silently override approved policy.
- Learning uses fixed before/after counts; it does not evaluate ticket correctness or persist an instruction update.
- Tool configuration changes only the advertised list in the local demo; it does not register or execute the newly listed tool.
- Identity is simulated; counting environment-file names is not a secret scan. The local reflex example polls a file when invoked, not an installed watcher. The local spine persists step markers, not a framework workflow or financial side effect.

## Verification

Run from the lab directory:

```powershell
.\.venv\Scripts\python -m unittest tests.test_recipes tests.test_show
```

The recipe tests use the real installed SDK for skill discovery, progressive disclosure, and its model/tool loop with mocked inference. They also test approval scope, planning contracts and rejection cases, middleware attachment, client cleanup on failure, checkpoint no-output handling, and candidate selection. Model quality, cloud RBAC, actual exporter delivery, and end-to-end Copilot Studio behavior are not verified by these offline tests.