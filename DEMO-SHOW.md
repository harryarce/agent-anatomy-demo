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
python -m unittest tests.test_organs tests.test_show
```

Warnings for an unconfigured Foundry endpoint, model, or Application Insights connection are acceptable when using stage-safe mode. Required local data and replay checks must pass.

## Versions On Screen

The show never hardcodes a version number. Every version is read from installed package metadata at runtime:

- Each framework code exhibit is labelled with its package and resolved version, for example `agent_framework  v1.14.0`.
- Scene 18 opens on a stack panel listing Python and every major dependency with its live version.

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

Valid scene numbers are 1 through 18. Scene 13 starts the Spine kill/resume climax.

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
| `Home` / `End` | Jump to scene 1 or scene 18 |
| `Esc` | Cancel the active command without starting a fallback |
| `Q` | Exit the show |

Wait for `EVIDENCE COMPLETE` before advancing. Presenter-only scenes do not run a command when `Space` is pressed.

## Code Exhibits

Every organ scene carries code exhibits, hidden by default so the narrative stays clean. Press `C` to reveal one, press `C` again to advance, and press `C` once more to hide them.

Exhibits are **paired**. Most organ scenes lead with the real Microsoft Agent Framework attachment point, then show how this project uses it:

| Label | Source |
|---|---|
| `agent_framework  v1.14.0` | The installed framework, read from `site-packages` at display time |
| `agent_framework_foundry  v…` | The installed Foundry connector (`FoundryChatClient`, `FoundryMemoryProvider`, `FoundryEvals`) |
| `THIS PROJECT` | Ada's own organ code in this repository |

Each exhibit shows the file path, the source with line numbers and the decisive line marked, then `WHAT IT DOES` and `WHY IT MATTERS`.

The headline exhibit is scene 3, exhibit 1: `BaseAgent.__init__`. Its parameter list — `instructions`, `tools`, `context_providers`, `middleware` — is literally the anatomy being dissected. Open it and read the parameter names aloud.

All exhibits are anchored to a line that must appear exactly once in its file, and a test asserts this, so a snippet can never drift from the code that actually ran.

For a nontechnical room, skip `C` entirely. For engineers, open the exhibit after the evidence runs so they see behavior first and mechanism second.

## Recommended 45-Minute Route

Navigate through all 18 scenes, but press `Space` only on the strongest evidence scenes below. This keeps the talk near 37 minutes and leaves approximately 8 minutes for questions.

| Scene | Moment | Run evidence? | Target |
|---|---|---:|---:|
| 1 | Introduction | No | 2 min |
| 2 | Reflex Arc cold open | Yes | 3 min |
| 3 | Brain alone: Instructions + Model | Yes | 4 min |
| 4 | Knowledge | Yes | 3 min |
| 5 | Tools | Yes | 3 min |
| 6-7 | Tool discovery + Memory | No; explain from the scene | 3 min |
| 8 | Guardrails | Yes | 3 min |
| 9-10 | Orchestration + Identity | No; explain from the scene | 3 min |
| 11 | Observability | Yes | 3 min |
| 12 | Metabolism | No; explain from the scene | 2 min |
| 13-14 | Spine kill + resume | Yes on both | 6 min |
| 15 | Skills + Learning | Yes | 3 min |
| 16-18 | Honest gaps, complete anatomy, resources | No | 2 min |

Do not attempt to read every output line. Point to the proof named under `WATCH FOR`, pause on the result, and close each scene by delivering the takeaway line shown at the bottom of the screen.

Adding one code exhibit per demonstrated organ costs roughly 30 seconds each. If you open exhibits on all seven evidence scenes, drop the optional explanations in scenes 6-7 and 9-10 to stay inside 45 minutes.

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
| Spine checkpoint is missing at scene 14 | Press `Space`; the show stages the expected kill before resuming |
| Terminal rendering is poor | Maximize the terminal and reduce its font size slightly |
| Fullscreen UI cannot run | Use `python -m anatomy present --replay --reset` |

The Spine kill intentionally returns exit code 1. In the show, this is displayed as `EXPECTED EXIT 1` and is part of the demonstration.

## Final Rehearsal

1. Maximize the terminal and confirm all 16 organ labels fit in the left rail.
2. Launch `python -m anatomy show` and practice the 45-minute route above.
3. Press `C` on scene 3 and confirm all three exhibits render without wrapping badly.
4. Confirm scene 2 reaches `EVIDENCE COMPLETE`.
5. Confirm scenes 13 and 14 display the expected kill followed by `SKIP` for completed steps.
6. Confirm scene 18 displays the live stack panel and the three public resource shortcuts.
7. Keep the scrolling fallback command in terminal history.

For individual organ commands and expected output, see [DEMO-RUNBOOK.md](DEMO-RUNBOOK.md). For concise speaking cues, see [DEMO-SCRIPT.md](DEMO-SCRIPT.md).