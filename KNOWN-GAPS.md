# Known gaps

- Audience code has been reviewed against official Agent Framework samples. See [the versioned sample review](examples/SAMPLE-REVIEW.md) for all 16 mappings, tested versions, and remaining stage-simulation limitations. Developer recipes are separate from local stage implementations.

- Remote demos use Foundry to synthesize deterministic organ evidence, but the local mechanisms are not replaced by model-generated simulations. Remote access is opt-in with `--remote`; the default makes no Foundry call. If Foundry is unavailable, reports retain their evidence and are labeled `DETERMINISTIC FALLBACK`.
- Toolbox authoring via Azure SDK is cloud-only in this repo stage; local toolbox behavior is demonstrated from checked-in YAML and labeled LOCAL IMPLEMENTATION where needed.
- Foundry Memory service integration is not invoked; local durable memory uses `.anatomy-memory.json` and is labeled LOCAL IMPLEMENTATION.
- Blob RBAC live enforcement for Identity is not executed locally; the full flow is labeled SIMULATED.
- Application Insights exporter requires a real connection string; when absent, preflight reports WARN and console tracing remains available.
- Agent Optimizer service is not called; the local Learning transcript uses fixed before/after scores, not an executed critic or measured evaluation.
- The local Planning transcript displays a fixed plan and dependency labels. The developer recipe separately requests structured model output and validates dependency ordering; the stage transcript does not execute it.
- Beliefs uses `.anatomy-beliefs.json` for the demo; production should use a governed store such as Dataverse, Azure Table Storage, or a Foundry memory capability.
