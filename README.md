# Agent Anatomy Lab

Ada is assembled on stage as one agent with independently runnable organs.

For the fullscreen presentation, start with [DEMO-SHOW.md](DEMO-SHOW.md). For every individual demo command, expected output, and detailed recovery step, see [DEMO-RUNBOOK.md](DEMO-RUNBOOK.md).

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/setup_data.py
python -m anatomy preflight
python -m anatomy show
```

`show` is the recommended audience experience: a 20-scene fullscreen terminal deck with organ vitals, keyboard navigation, executable evidence, local-to-replay recovery, and per-organ developer recipes. Each recipe shows how to attach the organ through public Agent Framework APIs and names the corresponding Copilot Studio component. Press `Space` to run a scene, `C` to show or cycle the inline recipe, `X` to expand or collapse it, `Left`/`Right` to navigate, and `R` to switch between local deterministic and remote LLM execution.

The default executes fresh local deterministic logic: files, SQLite, guardrails, workflows, budgets, checkpoints, and a clearly labeled Model baseline. It does not contact Foundry. Use `python -m anatomy show --remote` when authentic LLM synthesis is worth the additional latency. The scrolling replay command remains the universal fallback.

The recommended 45-minute route runs selected evidence while presenting the remaining scenes without execution. See [DEMO-SHOW.md](DEMO-SHOW.md#recommended-45-minute-route) for timings.

Scene 20 includes a QR code linking to [harryarce/agent-anatomy-demo](https://github.com/harryarce/agent-anatomy-demo).

## Core commands

```powershell
python -m anatomy list
python -m anatomy show
python -m anatomy show --remote
python -m anatomy show --from 14
python -m anatomy demo model --remote
python -m anatomy beat 1 --remote
python -m anatomy present --replay --reset
python -m anatomy beat 0 --replay
python -m anatomy beat 3 --replay
python -m anatomy beat 10 --kill
python -m anatomy spine --resume
python -m anatomy tools --tool-search --replay
python -m anatomy beat 8 --autopsy knowledge
python -m anatomy demo model --record
python -m anatomy story --from 5 --replay
```

## Beat table

| Beat | Organ(s) | Why it exists |
|---|---|---|
| 0 | Model, then Instructions | Raw baseline followed by behavior control |
| 1 | Knowledge | Citation-backed policy clause replaces guess |
| 2 | Tools | Order lookup proves 4471 facts |
| 3 | Tools (add-tool) | New capability from toolbox config only |
| 4 | Memory | Recall across distinct sessions |
| 5 | Guardrails | Blocks data leak and prompt injection |
| 6 | Orchestration | Visible multi-step workflow handoff |
| 7 | Identity | SIMULATED least-privilege/RBAC narrative |
| 8 | Observability | Local span tree + optional cloud export warning |
| 9 | Metabolism | Hard spend cap stop |
| 10 | Spine | Deterministic kill/resume checkpoints |
| 11 | Skills + Learning | Progressive disclosure + before/after improvement |
| 12 | Reflex Arc | Event wakes Ada with no human prompt |
| 13 | Planning | Goal decomposition after event-driven wake |
| 14 | Beliefs | World state update and future decision impact |

Notes:
- Cloud-only features remain honest gaps and are labeled LOCAL IMPLEMENTATION or SIMULATED.
- Remote model calls use `AzureCliCredential` from the active `az login` session; no API keys are written to repo files.
