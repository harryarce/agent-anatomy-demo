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

Warnings for an unconfigured Foundry endpoint, model, or Application Insights connection are acceptable when using the default local deterministic mode. Required local data and replay checks must pass.

## Versions On Screen

The show never hardcodes a version number. Every version is read from installed package metadata at runtime:

- Scene 20 opens on a stack panel listing Python and every major dependency with its live version.

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

Recommended show, using fresh local deterministic evidence:

```powershell
python -m anatomy show
```

The show opens on scene 1. Every executable scene runs its local mechanism without contacting Foundry. This keeps the pace predictable while still proving real file retrieval, SQLite queries, guardrails, workflows, budgets, triggers, and checkpoints.

Opt into the remote LLM when Foundry is configured and the extra latency fits the session:

```powershell
python -m anatomy show --remote
```

If a local command fails, the show labels the failure and runs that scene's committed replay evidence. Remote inference failures retain deterministic evidence and display the fallback status. Press `R` at any time between demonstrations to switch modes.

Start from a specific scene:

```powershell
python -m anatomy show --from 14
```

Valid scene numbers are 1 through 20. Scene 13 starts the Spine kill/resume sequence.

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
| `X` | Expand the visible code exhibit, or collapse the overlay |
| `R` | Switch between local deterministic and remote LLM mode |
| `Home` / `End` | Jump to scene 1 or scene 20 |
| `Page Up` / `Page Down` | Scroll long evidence or code exhibits |
| `Esc` | Cancel the active command without starting a fallback |
| `Q` | Exit the show |

## Read the Output as a Story

Every executable scene uses the same visible rhythm: the user creates the need, an actor handles each piece of evidence, and the narrator closes with the takeaway. Introduce the labels once near the beginning, then let the audience follow the handoffs:

| Label | Actor |
|---|---|
| `USER` | The person or request that starts the scene |
| `APPLICATION TEAM` | The people who configure Ada's instructions, tools, and policies |
| `AI / MODEL` | Generated reasoning or response text |
| `TOOL` | A lookup, external result, or untrusted tool payload |
| `AGENT · <ROLE>` | A specialist in a multi-agent workflow |
| `ORGAN · <NAME>` | The capability making a decision or changing behavior |
| `SYSTEM` | Runtime, checkpoint, or telemetry evidence |
| `NARRATOR` | The scene's closing takeaway |

For each scene, read only three turns aloud: `USER`, the decisive actor line, and `NARRATOR`. The remaining lines are supporting evidence for the audience to scan.

Wait for `EVIDENCE COMPLETE` before advancing. Presenter-only scenes do not run a command when `Space` is pressed.

The `EVIDENCE` panel contains the command's actual combined output. The `RESULT` panel reports execution health:

- `STATUS PASSED` means the command returned an expected exit code.
- `STATUS PASSED WITH FALLBACK` means deterministic evidence succeeded after a remote LLM failure.
- `STATUS FAILED` means the process could not start or returned an unexpected exit code.

Fallbacks and failures are appended to `.anatomy-errors.log` with a UTC timestamp, command, reason, and captured output. Expected demonstration failures, such as the Spine kill returning exit code 1, are not logged as errors.

After a demo finishes, the evidence window automatically returns to the top so the speaker can present it in story order. Use `Page Down` to advance through longer output.

## Code Exhibits

Every organ scene carries a code exhibit, hidden by default so the narrative stays clean. Press `C` to reveal it, press `C` again to advance when a scene has another exhibit, and continue until the exhibit closes. While inline code is visible, press `X` to open a near-full-screen overlay with substantially more surrounding source lines. Press `X` or `Esc` to collapse it; use `Page Up` and `Page Down` to scroll the expanded code.

Every snippet is application code from `examples/organ_recipes.py` or developer-owned configuration from `toolbox.add-tool.yaml`. The audience sees the public attachment point they can adapt, never internal framework implementation from `site-packages`.

Each exhibit shows the file path, a short recipe with line numbers and the decisive line marked, then three audience cues:

- `WHAT IT DOES` explains the code mechanism.
- `WHY IT MATTERS` connects the mechanism to dependable agent behavior.
- `COPILOT STUDIO` names the corresponding low-code component or configuration surface.

The headline exhibit is scene 19: `compose_agent`. Its `instructions`, `tools`, `context_providers`, and `middleware` arguments are the anatomy being assembled through public APIs. Open it and read the attachment points aloud.

All exhibits are anchored to a line that must appear exactly once in its file, and a test asserts this, so a snippet can never drift from the code that actually ran.

For a nontechnical room, skip `C` entirely. For engineers, open the exhibit after the evidence runs so they see behavior first and mechanism second.

## Recommended 45-Minute Route

Navigate through all 20 scenes, but press `Space` only where the table says to run evidence. This route targets 41 minutes and preserves approximately 4 minutes for transitions or questions.

| Scene | Moment | Run evidence? | Target |
|---|---|---:|---:|
| 1 | Introduction | No | 2 min |
| 2 | Model alone | Yes | 2 min |
| 3 | Instructions change behavior | Yes | 2 min |
| 4 | Knowledge | Yes | 3 min |
| 5 | Tools | Yes | 3 min |
| 6-7 | Tool discovery + Memory | No; explain from the scene | 3 min |
| 8 | Guardrails | Yes | 3 min |
| 9-10 | Orchestration + Identity | No; explain from the scene | 3 min |
| 11 | Observability | Yes | 3 min |
| 12 | Metabolism | No; explain from the scene | 2 min |
| 13-14 | Spine kill + resume | Yes on both | 6 min |
| 15 | Skills + Learning | No; explain from the scene | 3 min |
| 16 | Reflex Arc | Yes | 3 min |
| 17 | Planning | Yes | 2 min |
| 18 | Beliefs | Yes | 2 min |
| 19-20 | Complete anatomy + resources | No | 2 min |

Scene 20 places a scannable QR code for [github.com/harryarce/agent-anatomy-demo](https://github.com/harryarce/agent-anatomy-demo) in the top-right resource panel. Leave this scene visible during questions so attendees can take the runnable demo with them.

Do not attempt to read every output line. Point to the proof named under `WATCH FOR`, pause on the result, and close each scene by delivering the takeaway line shown at the bottom of the screen.

Adding one code exhibit per demonstrated organ costs roughly 30 seconds each. Open scenes 2 and 3 to emphasize the Model/Instructions separation; for a 45-minute slot, also open scenes 5, 17, and 18, then use scene 19 to show all attachment points together.

## Remote LLM Mode

Authenticate and set the current shell variables before launch:

```powershell
az login
$env:FOUNDRY_PROJECT_ENDPOINT = "https://<resource>.services.ai.azure.com/api/projects/<project>"
$env:FOUNDRY_MODEL = "<deployment-name>"
python -m anatomy preflight
python -m anatomy show --remote
```

Remote mode sends each organ's deterministic evidence to Foundry for a grounded synthesis; the Model scene invokes the configured deployment directly. Local mechanisms remain the source of truth and survive inference failures. Press `R` to return immediately to local deterministic mode. Use `--replay` only when you want the committed, frozen transcript instead of fresh execution.

## Recovery

| Situation | Recovery |
|---|---|
| A remote scene fails | Let its deterministic evidence or committed replay fallback finish |
| A command appears stuck | Press `Esc`, then press `R` to select local deterministic mode and rerun with `Space` |
| The show exits | Relaunch with `python -m anatomy show --from <scene>` |
| Spine checkpoint is missing at scene 14 | Press `Space`; the show stages the expected kill before resuming |
| Terminal rendering is poor | Maximize the terminal and reduce its font size slightly |
| Fullscreen UI cannot run | Use `python -m anatomy present --replay --reset` |

The Spine kill intentionally returns exit code 1. In the show, this is displayed as `EXPECTED EXIT 1` and is part of the demonstration.

## Final Rehearsal

1. Maximize the terminal and confirm all 16 organ labels fit in the left rail.
2. Launch `python -m anatomy show` and practice the 45-minute route above.
3. Confirm scene 2 runs only Model evidence and scene 3 runs only Instructions evidence; press `C` on each to verify separate recipes.
4. Confirm scene 16 reaches `EVIDENCE COMPLETE` in local deterministic mode.
5. Confirm scenes 13 and 14 display the expected kill followed by `SKIP` for completed steps.
6. Confirm scenes 17 and 18 run Planning and Beliefs evidence and expose their code exhibits.
7. Confirm scene 20 displays the live stack panel and the three public resource shortcuts.
8. Keep the scrolling fallback command in terminal history.

For individual organ commands and expected output, see [DEMO-RUNBOOK.md](DEMO-RUNBOOK.md). For concise speaking cues, see [DEMO-SCRIPT.md](DEMO-SCRIPT.md).