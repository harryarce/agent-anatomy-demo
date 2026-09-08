# Demo Code Reuse Research

Researched 2026-09-08. Recommendation: keep Microsoft Agent Framework as the runtime, reuse its native providers and middleware, and make every displayed capability produce inspectable evidence. Optimize for correctness, readability, reproducibility, and minimal dependencies before optimizing line count. No latency or cost improvement is claimed without measurements.

This is a research report, not an implemented upgrade. Stage code and dependency pins were not changed by this research. See [SAMPLE-REVIEW.md](SAMPLE-REVIEW.md) for the existing 16-organ audit and earlier test results.

**Current decision:** Keep Microsoft Agent Framework. Do not adopt Agent Governance Toolkit for now. Implement guardrails with native framework middleware, typed policy checks, and explicit tool approvals. Toolkit findings below are retained as deferred research, not an implementation recommendation.

## Highest-Priority Findings

1. **A constructor is not a guardrail implementation.** Our `add_guardrails` recipe accepts middleware but implements no policy. The stage guardrails are scripted. Show an actual denied tool invocation with a side-effect counter that remains zero, not just a printed refusal.
2. **The governance toolkit needs adaptation before use with this demo.** Its MAF input middleware attempts to assign `Message.text`; that property has no setter in our installed core 1.14.0. Its tool guard also handles `dict` but wraps other valid argument types as `{"_value": ...}`. Agent Framework accepts `BaseModel | Mapping`, so argument-based policy can receive the wrong shape. These shape mismatches were reproduced locally; the complete toolkit adapter was not installed or executed.
3. **Some upstream samples also overstate or simplify behavior.** The governance adapter's opening example passes `policy_directory` and `allowed_tools`, whereas its current factory requires `runtime`. Its customer-service example calls the policy adapter directly, not `Agent.run`. Agent Framework's expected-output evaluation sample uses word overlap, which is not a valid refund-policy correctness metric.
4. **Do not call best-effort limits a hard spend cap.** Agent Framework distinguishes model iterations, total calls per request, and lifetime calls per tool instance. Its sample explicitly warns that a parallel batch can overshoot the request call limit. Strict financial enforcement needs atomic reservations, bounded operations, and reconciliation.

## Repository Decisions

| Repository | Reuse Decision | Reason And Boundary |
| --- | --- | --- |
| [microsoft/agent-framework, Python][af] | Primary source | Native agents, tools, skills, memory, middleware, evaluation, workflows, and telemetry avoid unnecessary adapters. Pin both source and packages; `main` is not a released-version guarantee. |
| [microsoft/agent-governance-toolkit][agt] | Deferred; excluded from the implementation | User decision: stay with Agent Framework and do not adopt AGT for now. Compatibility findings below are reference material only. |
| [microsoft/PyRIT][pyrit] | Pre-demo adversarial assessment, not inline enforcement | Targets, attack strategies, scorers, and result storage can test leakage and policy bypass. Keep it in a separate environment; current docs recommend Python 3.13, while this demo uses 3.11. A passed attack suite is not a security guarantee. |
| [microsoft/agent-lightning][lightning] | Offstage research reference, not this demo's learning dependency | Current v1 is a rewritten RL stack with Trainer, API Gateway, and Rollout Controller; the documented setup includes CUDA, verl, and vLLM. Legacy APIs belong to the `v0.x` branch, not current `main`. Use small measured evaluations here instead. |
| [Presidio, formerly microsoft/presidio][presidio] | Optional PII detector/anonymizer | Microsoft-origin, but the repository now redirects to `data-privacy-stack/presidio`; do not describe it as currently Microsoft-owned. Detector quality is probabilistic and incomplete. Use a separate dependency/model setup and synthetic data. |

## Recommended Organ Implementations

| Organ | Best-Fit Reuse Or Design | Evidence Required Before Showing It |
| --- | --- | --- |
| Instructions | Keep `Agent(instructions=...)`; compare two instruction sets on the same inputs and model configuration. | Actual responses, model/deployment identity, and a reproducible test case; no enforcement claim. |
| Model | Keep the native Foundry client and explicit demo credential. Reuse clients within their owned lifetime. | A real response and reported usage; distinguish deterministic fallback from live inference. |
| Knowledge | Adapt the framework's [Azure AI Search context-provider samples][search] for the optional cloud path; use the existing policy file for the local path. | Retrieved passage, source identifier, and an independently checked policy citation. Retrieval must be authorized for the caller. |
| Tools | Keep typed `@tool` functions; use a real [MCP transport][mcp] for remote tools, not a parsed display list. | A newly registered tool actually executes. A repository spy proves the tool received validated arguments. |
| Skills | Retain the corrected `SkillsProvider.from_paths` plus selective read-only approvals. | Metadata first, actual instruction body only when loaded, and script execution blocked until approved. Reserve provider tool names to prevent local name collisions. |
| Memory | Replace the generic attachment example with [FileMemoryProvider over FileSystemAgentFileStore][memory], using a stable scope derived from authenticated tenant/user identity. | Write in session A, reconstruct the agent/provider, recall in fresh session B, and prove user C cannot retrieve it. Default session scope is not cross-session memory. |
| Guardrails | Use native `FunctionMiddleware` enforcing trusted customer scope and refund limits before `call_next`, plus `ToolApprovalMiddleware` for approval-required tools. Reuse the framework's [tool-boundary pattern][atr], without requiring its external detector dependency. No AGT integration. | Allowed action executes once; forbidden action and malformed arguments execute zero times; missing trusted identity and policy evaluation errors fail closed. |
| Orchestration | Use typed review decisions and [conditional workflow edges][routing], plus [approval requests][approval] for sensitive actions. | Rejection cannot reach the refund executor; approval takes the intended branch. A reviewer at the end of a sequence is insufficient. |
| Identity | Keep authentication separate from authorization; inject trusted caller identity at the host, never from model-selected arguments. | An authorized call succeeds and an unauthorized call is denied by the actual protected resource. Otherwise label the evidence simulated. |
| Observability | Reuse [native framework OpenTelemetry instrumentation][otel] with one configured console or local exporter. | Collected agent/model/tool spans with correlated IDs; no hard-coded trace tree. Keep sensitive content capture off by default. |
| Reflex Arc | Keep the event handler separate from its host trigger; reuse [framework hosting examples][hosting] when adding a real service. | A real incoming event invokes the handler. Re-delivery is deduplicated, and invalid or unauthenticated events are rejected. |
| Planning | Retain the structured `ExecutionPlan` and deterministic validator. Optionally add [TodoProvider][todos] for visible progress across turns. | Inspect the actual plan/store; reject missing dependencies and cycles. A completed todo is not proof that an external action succeeded. |
| Spine | Reuse [FileCheckpointStorage and resume][checkpoint], coupled to idempotency keys in the business operation. | Restart with new workflow objects, resume persisted state, and prove no duplicate refund. Checkpointing alone is not exactly-once execution. |
| Metabolism | Add native [iteration and tool limits][limits] as best-effort loop controls; keep strict money accounting application-owned. | Parallel-call and repeated-session tests; reserved plus spent totals never exceed the declared hard budget if that claim is made. |
| Beliefs | Keep typed application state plus a context provider; store evidence, revision, and effective time. Do not invent a native Beliefs API. | New evidence changes a derived conclusion while immutable refund policy and customer isolation remain intact. |
| Learning | Reuse [LocalEvaluator, evaluate_agent, and custom evaluators][evaluation] to score baseline/candidate on held-out refund cases. | Actual per-case decisions and aggregate results; reject safety regressions and persist only an approved version. Do not use keyword overlap or fixed before/after counts as quality evidence. |

## Deferred Governance Toolkit Findings

Reviewed [maf_adapter.py][agt-adapter] at commit `675a556798d0fe1bbae1955325fa79dccb747810`.

- `MAFKernel(runtime=...)` accepts an ACS runtime. `as_runtime_middleware()` evaluates input; `as_capability_guard()` evaluates tool calls. Register both if both boundaries must be governed. `wrap(agent)` returns the original agent unchanged.
- `create_governance_middleware(runtime=..., ...)` composes these layers and optional auditing/anomaly detection. Its stale module-level usage example is not the current signature.
- `RuntimeGovernanceMiddleware` reads the final message, not the entire conversation or every retrieved document. It assigns `last_msg.text` before replacing `contents`; the read-only property in core 1.14.0 makes the transform path refuse the request. This is a fail-closed availability/compatibility problem, not evidence of a successful redaction or a bypass.
- `CapabilityGuardMiddleware` normalizes only `dict`. Convert Pydantic models with `model_dump()` and support general mappings before evaluating argument-field policies. Do not infer an exploitable bypass from this shape mismatch without the actual policy and runtime.
- Both middleware objects retain their own `_v5_ctx`, with timestamp-derived session IDs, rather than deriving one shared state from the actual framework session. Validate session scoping, combined accounting, and concurrent calls before reusing instances across users.
- Input audit entries include a message preview; tool completion entries can include result previews. Do not attach an audit sink to real customer data without a redaction/minimization policy.
- The [customer-service example][agt-demo] evaluates two prompts directly through the kernel. It is not evidence of an end-to-end MAF tool call. The [adapter scenario tests][agt-tests] exercise continuations with scripted policies and synthetic contexts; add real SDK Message and BaseModel cases.
- AGT's [limitations][agt-limits] distinguish action governance from reasoning/content safety, OS isolation, knowledge provenance, and outcome verification. OWASP category mapping is not proof of complete protection or certified compliance.
- The native ACS/Rego path introduces runtime and policy-engine prerequisites. Verify package availability and the chosen Windows setup independently before committing it to the stage environment.

If adoption is reconsidered later, test allowed lookup; cross-customer lookup denied; over-limit refund denied; malformed arguments denied; input transform reaches the actual model request; denied tool has zero side effects; policy errors fail closed; and session/concurrent-budget isolation. No toolkit adoption work is planned now.

## Implementation Order

1. Native Agent Framework guardrails with real allow/deny evidence, trusted customer scope, and explicit tool approvals. No Agent Governance Toolkit dependency or adapter.
2. Real scoped file memory across reconstructed agents and separate sessions.
3. Conditional review/approval plus persisted workflow resume and idempotent business operations.
4. Collected telemetry and measured baseline/candidate evaluation.
5. Optional PII detection and offstage PyRIT assessment. Keep heavyweight training and mesh infrastructure out of the core presentation.

## Audience-Code Standard

- Display the deciding code, not only the constructor wiring. Keep short exhibits linked to a complete runnable implementation.
- One assertion should substantiate each claim: zero denied side effects, persisted recall, rejected workflow branch, collected spans, or measured score.
- Use deterministic fake inference for offline contract tests; clearly label live model quality and cloud authorization as separate verification.
- Hoist immutable policy/rule loading and reusable clients out of hot paths; scope mutable state by run/user. Measure cold and warm timings before claiming performance gains.
- Preserve schemas and validate arguments structurally. Avoid converting structured policy inputs into an untyped string except for explicitly labeled content scanning.
- Do not equate Python middleware with a Copilot Studio capability. Studio mappings require separate product documentation and tenant verification.
- Preserve required licenses/notices when copying upstream source. Links and independently implemented adaptations are preferable to copying a whole sample tree.

## Verification Boundary

This pass read upstream sources and ran focused, network-free probes against installed core 1.14.0. The probes confirmed FileMemoryProvider, TodoProvider, LocalEvaluator, and invocation-limit APIs exist; reproduced the read-only Message.text assignment failure; and confirmed that the adapter's normalization loses named fields for a valid BaseModel argument object. These are not end-to-end AGT results.

No AGT, Presidio, PyRIT, or Lightning dependencies were installed. No cloud calls, red-team campaigns, performance benchmarks, or new learning evaluations were run. Earlier results remain 53 recipe/show tests on core 1.14.0 / Foundry 1.11.0 and 25 focused tests on core 1.16.0 / Foundry 1.11.0. Public-latest core 1.17.0 / Foundry 1.12.0 remains unverified as documented in the earlier review.

[af]: https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python
[agt]: https://github.com/microsoft/agent-governance-toolkit/tree/675a556798d0fe1bbae1955325fa79dccb747810
[pyrit]: https://github.com/microsoft/PyRIT/blob/main/doc/index.md
[lightning]: https://github.com/microsoft/agent-lightning/blob/main/README.md
[presidio]: https://github.com/data-privacy-stack/presidio/tree/a7b17c75f3098b92b369f0b01855519f1cd5e8cc
[search]: https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/context_providers/azure_ai_search
[mcp]: https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/mcp
[memory]: https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/context_providers/file_memory_provider.py
[atr]: https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/middleware/atr_validation_middleware.py
[routing]: https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/03-workflows/control-flow/switch_case_edge_group.py
[approval]: https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/tools/tool_approval_middleware.py
[otel]: https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/observability/README.md
[hosting]: https://github.com/microsoft/agent-framework/tree/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/04-hosting
[todos]: https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/context_providers/todo_provider.py
[checkpoint]: https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/03-workflows/checkpoint/checkpoint_with_resume.py
[limits]: https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/tools/control_total_tool_executions.py
[evaluation]: https://github.com/microsoft/agent-framework/blob/a03bb909c694ad27f0b14d310d39e7f9e232ad39/python/samples/02-agents/evaluation/evaluate_with_expected.py
[agt-adapter]: https://github.com/microsoft/agent-governance-toolkit/blob/675a556798d0fe1bbae1955325fa79dccb747810/agent-governance-python/agent-os/src/agent_os/integrations/maf_adapter.py
[agt-demo]: https://github.com/microsoft/agent-governance-toolkit/blob/675a556798d0fe1bbae1955325fa79dccb747810/examples/maf-integration/02-customer-service/python/main.py
[agt-tests]: https://github.com/microsoft/agent-governance-toolkit/blob/675a556798d0fe1bbae1955325fa79dccb747810/agent-governance-python/agt-policies/tests/scenarios/test_maf_adapter_scenarios.py
[agt-limits]: https://github.com/microsoft/agent-governance-toolkit/blob/675a556798d0fe1bbae1955325fa79dccb747810/docs/LIMITATIONS.md