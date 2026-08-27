# Agent Anatomy Lab

Ada is assembled on stage as one agent with independently runnable organs.

For setup, every demo command, expected output, stage sequencing, and recovery steps, see [DEMO-RUNBOOK.md](DEMO-RUNBOOK.md).

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/setup_data.py
python -m anatomy preflight
python -m anatomy present --replay --reset
```

`present` is the recommended audience experience. Every organ is introduced with its place in agent evolution, the failure it fixes, what to watch, a before/after contrast, and a speaker-ready landing line.

## Core commands

```powershell
python -m anatomy list
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
| 0 | Instructions + Model | Opening failure: confident but wrong policy claim |
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

Notes:
- Cloud-only features remain honest gaps and are labeled LOCAL IMPLEMENTATION or SIMULATED.
- Live model calls use `AzureCliCredential` from the active `az login` session; no API keys are written to repo files.
