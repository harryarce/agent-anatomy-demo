# Agent Anatomy Lab

Agent Anatomy Lab assembles Ada, a Contoso refund agent, one capability at a time. The project contains 16 independently runnable organs, a 15-beat command-line story, and a 20-scene fullscreen presentation.

The demo is stage-safe by design: fresh local deterministic evidence is the default, remote Foundry inference is opt-in, and committed replay transcripts provide an offline fallback.

## Prerequisites

- Windows PowerShell
- Python 3.11
- Azure CLI and an authorized `az login` session only for `--remote` mode

## Quickstart

Run from the `agent-anatomy-lab` directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/setup_data.py
python -m anatomy preflight
python -m anatomy show
```

Warnings about Azure authentication, Foundry, or Application Insights are acceptable for the default local mode. Required local checks must pass.

If public PyPI downloads fail TLS negotiation in a Microsoft-managed environment where the Microsoft package feed is approved, use an explicit install-time index:

```powershell
.\.venv\Scripts\python.exe -m pip install --index-url https://packagefeedproxy.microsoft.io/pypi/simple -r requirements.txt
```

This leaves global package configuration unchanged and keeps TLS verification enabled. The mirror can lag public PyPI releases; a missing version is separate from a TLS failure.

## Execution Modes

| Mode | Command pattern | Behavior |
|---|---|---|
| Local deterministic | `python -m anatomy show` | Default. Runs fresh files, SQLite, guardrails, workflows, budgets, triggers, and checkpoints without contacting Foundry. |
| Remote LLM | `python -m anatomy show --remote` | Invokes `gpt-5.6-terra` for the Model scene and evidence-grounded synthesis elsewhere. Requires `az login`. |
| Replay | `python -m anatomy present --replay --reset` | Reads committed JSON transcripts for a frozen, offline scrolling presentation. |

Remote failures retain deterministic evidence and are labeled `DETERMINISTIC FALLBACK`. `--remote` and `--replay` are mutually exclusive.

## Show Controls

| Key | Action |
|---|---|
| `Left` / `Right` | Navigate scenes |
| `Space` | Run the current scene's evidence |
| `C` | Show, cycle, or hide the inline code exhibit |
| `X` | Expand or collapse the visible code exhibit |
| `R` | Switch between local deterministic and remote LLM mode |
| `Page Up` / `Page Down` | Scroll evidence or expanded code |
| `Home` / `End` | Jump to the first or final scene |
| `Esc` | Close expanded code or cancel the active command |
| `Q` | Exit |

Scene 20 displays the live dependency stack, public resources, the full repository URL, and a QR code for [github.com/harryarce/agent-anatomy-demo](https://github.com/harryarce/agent-anatomy-demo).

## Core commands

```powershell
# Inspect and validate
python -m anatomy list
python -m unittest discover -s tests
python -m anatomy preflight

# Present
python -m anatomy show
python -m anatomy show --remote
python -m anatomy show --from 14
python -m anatomy present --replay --reset

# Run focused evidence
python -m anatomy demo model --remote
python -m anatomy beat 0 --replay
python -m anatomy beat 10 --kill
python -m anatomy spine --resume
python -m anatomy tools --tool-search --replay
python -m anatomy beat 8 --autopsy knowledge

# Capture or resume
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

## More Documentation

- [examples/SAMPLE-REVIEW.md](examples/SAMPLE-REVIEW.md): official-source review of all 16 audience recipes, tested versions, and stage-simulation limitations
- [DEMO-SHOW.md](DEMO-SHOW.md): fullscreen controls, scene route, timings, and stage recovery
- [DEMO-RUNBOOK.md](DEMO-RUNBOOK.md): every command, expected evidence, and troubleshooting step
- [SPEAKER-ORGAN-TALK-TRACK.md](SPEAKER-ORGAN-TALK-TRACK.md): audience-facing narrative and landing lines
- [KNOWN-GAPS.md](KNOWN-GAPS.md): local implementations, simulations, and cloud boundaries
