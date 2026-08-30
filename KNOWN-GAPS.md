# Known gaps

- Toolbox authoring via Azure SDK is cloud-only in this repo stage; local toolbox behavior is demonstrated from checked-in YAML and labeled LOCAL IMPLEMENTATION where needed.
- Foundry Memory service integration is not invoked; local durable memory uses `.anatomy-memory.json` and is labeled LOCAL IMPLEMENTATION.
- Blob RBAC live enforcement for Identity is not executed locally; the full flow is labeled SIMULATED.
- Application Insights exporter requires a real connection string; when absent, preflight reports WARN and console tracing remains available.
- Agent Optimizer service is not called; Learning uses a local critic loop and is labeled LOCAL IMPLEMENTATION.
- Planning produces and validates a local execution plan; it does not claim that the displayed sub-goals have already run.
- Beliefs uses `.anatomy-beliefs.json` for the demo; production should use a governed store such as Dataverse, Azure Table Storage, or a Foundry memory capability.
