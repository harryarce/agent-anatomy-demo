# Fullscreen Demo Show

This guide covers the keyboard-driven Agent Anatomy show. Run all commands from the `agent-anatomy-lab` directory in Windows PowerShell.

## Prepare

One-time setup:

```powershell
Set-Location C:\temp\source\agent-anatomy\agent-anatomy-lab
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/setup_data.py
```

Before each presentation:

```powershell
python -m pip check
python -m anatomy preflight
python -m unittest discover -s tests
```

Warnings for an unconfigured Foundry endpoint, model, or Application Insights connection are acceptable when using stage-safe mode. Required local data and replay checks must pass.

## Versions On Screen

The show never hardcodes a version number. Every version is read from installed package metadata at runtime:

- Scene 19 opens on a stack panel listing Python and every major dependency with its live version.

A test asserts that each `==` pin in `requirements.txt` matches the installed version, so the stack panel can never drift from what is actually installed.

Dependencies are pinned to the newest versions that satisfy the framework's own constraints:

| Package | Pin | Constraint that decides it |
|---|---|---|
| `agent-framework-foundry` | 1.11.0 | Latest release |
| `agent-framework-core` | 1.14.0 | Foundry requires `>=1.13.0,<2` |
| `azure-ai-projects` | 2.3.0 | Foundry requires `>=2.2.0,<2.4.0`, so 2.5.0 is **not** installable |
| `opentelemetry-sdk` | 1.43.0 | Azure Monitor 1.8.9 instrumentation caps it below 1.44 |
| `rich` / `textual` | 15.0.0 / 8.2.8 | Latest releases |

Do not blindly upgrade `azure-ai-projects` or `opentelemetry-sdk`; both are capped by upstream constraints and pip will refuse to resolve.

## Launch

Recommended stage-safe show:

```powershell
python -m anatomy show
```

The show opens on scene 1. It uses committed evidence for network-sensitive demonstrations and real local execution for the Spine checkpoint sequence.

Prefer live and local execution when Foundry is configured:

```powershell
python -m anatomy show --live
```

If a live command fails, the show labels the failure and runs that scene's stage-safe evidence. Press `R` at any time between demonstrations to switch modes.

Start from a specific scene:

```powershell
python -m anatomy show --from 13
```

Valid scene numbers are 1 through 19. Scene 12 starts the Spine kill/resume sequence.

If activating the virtual environment is blocked, launch it directly:

```powershell
.\.venv\Scripts\python.exe -m anatomy show
```

## Controls

| Key | Action |
|---|---|
| `Left` / `Right` | Previous or next scene |
| `Space` | Run the current scene's evidence |
| `C` | Show the next code exhibit, or hide it |
| `R` | Switch between stage-safe and live/local mode |
| `Home` / `End` | Jump to scene 1 or scene 19 |
| `Page Up` / `Page Down` | Scroll long evidence or code exhibits |
| `Esc` | Cancel the active command without starting a fallback |
| `Q` | Exit the show |

Wait for `EVIDENCE COMPLETE` before advancing. Presenter-only scenes do not run a command when `Space` is pressed.

## Code Exhibits

Every organ scene carries a code exhibit, hidden by default so the narrative stays clean. Press `C` to reveal it, press `C` again to advance when a scene has another exhibit, and continue until the exhibit closes.

Every snippet is application code from `examples/organ_recipes.py` or developer-owned configuration from `toolbox.add-tool.yaml`. The audience sees the public attachment point they can adapt, never internal framework implementation from `site-packages`.

Each exhibit shows the file path, a short recipe with line numbers and the decisive line marked, then three audience cues:

- `WHAT IT DOES` explains the code mechanism.
- `WHY IT MATTERS` connects the mechanism to dependable agent behavior.
- `COPILOT STUDIO` names the corresponding low-code component or configuration surface.

The headline exhibit is scene 18: `compose_agent`. Its `instructions`, `tools`, `context_providers`, and `middleware` arguments are the anatomy being assembled through public APIs. Open it and read the attachment points aloud.

All exhibits are anchored to a line that must appear exactly once in its file, and a test asserts this, so a snippet can never drift from the code that actually ran.

For a nontechnical room, skip `C` entirely. For engineers, open the exhibit after the evidence runs so they see behavior first and mechanism second.

## Recommended 45-Minute Route

Navigate through all 19 scenes, but press `Space` only where the table says to run evidence. This route targets 41 minutes and preserves approximately 4 minutes for transitions or questions.

| Scene | Moment | Run evidence? | Target |
|---|---|---:|---:|
| 1 | Introduction | No | 2 min |
| 2 | Brain alone: Instructions + Model | Yes | 4 min |
| 3 | Knowledge | Yes | 3 min |
| 4 | Tools | Yes | 3 min |
| 5-6 | Tool discovery + Memory | No; explain from the scene | 3 min |
| 7 | Guardrails | Yes | 3 min |
| 8-9 | Orchestration + Identity | No; explain from the scene | 3 min |
| 10 | Observability | Yes | 3 min |
| 11 | Metabolism | No; explain from the scene | 2 min |
| 12-13 | Spine kill + resume | Yes on both | 6 min |
| 14 | Skills + Learning | No; explain from the scene | 3 min |
| 15 | Reflex Arc | Yes | 3 min |
| 16 | Planning | Yes | 2 min |
| 17 | Beliefs | Yes | 2 min |
| 18-19 | Complete anatomy + resources | No | 2 min |

Do not attempt to read every output line. Point to the proof named under `WATCH FOR`, pause on the result, and close each scene by delivering the takeaway line shown at the bottom of the screen.

Adding one code exhibit per demonstrated organ costs roughly 30 seconds each. For a 45-minute slot, open exhibits only on scenes 2, 4, 16, and 17; use scene 18 to show all attachment points together.

## Live Foundry Mode

Authenticate and set the current shell variables before launch:

```powershell
az login
$env:FOUNDRY_PROJECT_ENDPOINT = "https://<resource>.services.ai.azure.com/api/projects/<project>"
$env:FOUNDRY_MODEL = "<deployment-name>"
python -m anatomy preflight
python -m anatomy show --live
```

Only the Model organ requires Foundry inference. Local demonstrations such as SQLite lookup, files, guardrails, budgets, and checkpoints do not require network access.

## Recovery

| Situation | Recovery |
|---|---|
| A live scene fails | Let its automatic stage-safe fallback finish |
| A command appears stuck | Press `Esc`, then press `R` and rerun with `Space` |
| The show exits | Relaunch with `python -m anatomy show --from <scene>` |
| Spine checkpoint is missing at scene 13 | Press `Space`; the show stages the expected kill before resuming |
| Terminal rendering is poor | Maximize the terminal and reduce its font size slightly |
| Fullscreen UI cannot run | Use `python -m anatomy present --replay --reset` |

The Spine kill intentionally returns exit code 1. In the show, this is displayed as `EXPECTED EXIT 1` and is part of the demonstration.

## Final Rehearsal

1. Maximize the terminal and confirm all 16 organ labels fit in the left rail.
2. Launch `python -m anatomy show` and practice the 45-minute route above.
3. Press `C` on scene 2 and confirm the developer recipe and `COPILOT STUDIO` explanation render without wrapping badly.
4. Confirm scene 15 reaches `EVIDENCE COMPLETE` without relying on filesystem timing in stage-safe mode.
5. Confirm scenes 12 and 13 display the expected kill followed by `SKIP` for completed steps.
6. Confirm scenes 16 and 17 run Planning and Beliefs evidence and expose their code exhibits.
7. Confirm scene 19 displays the live stack panel and the three public resource shortcuts.
8. Keep the scrolling fallback command in terminal history.

For individual organ commands and expected output, see [DEMO-RUNBOOK.md](DEMO-RUNBOOK.md). For concise speaking cues, see [DEMO-SCRIPT.md](DEMO-SCRIPT.md).