# Agent Anatomy Lab Demo Runbook

This document explains how to prepare, validate, and run every Ada demo from Windows PowerShell. Run all commands from the `agent-anatomy-lab` directory.

## 1. Choose a Demo Mode

| Mode | Use it when | Network | Command pattern |
|---|---|---|---|
| Replay | Presenting on stage or testing the complete narrative | Not required | `python -m anatomy ... --replay` |
| Local | Demonstrating SQLite, files, checkpoints, budgets, or other local behavior | Not required | `python -m anatomy ...` |
| Live Foundry | Demonstrating the deployed model | Required | `python -m anatomy demo model` |

Replay mode reads committed JSON transcripts from `replays/`. Local mode executes real local mechanisms. Only the Model organ currently makes a live Foundry inference call. Features labeled `LOCAL IMPLEMENTATION` or `SIMULATED` are described in `KNOWN-GAPS.md`.

## 2. One-Time Setup

Open PowerShell in the project directory:

```powershell
Set-Location C:\temp\source\agent-anatomy\agent-anatomy-lab
```

Create and activate an isolated Python environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

Expected final output from `pip check`:

```text
No broken requirements found.
```

If PowerShell blocks activation, either invoke the environment directly:

```powershell
.\.venv\Scripts\python.exe -m anatomy list
```

or allow locally created scripts for the current user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Generate or refresh the synthetic data:

```powershell
python scripts/setup_data.py
```

This creates the policy documents, SQLite order database, CRM records, and learning tickets. The data is synthetic. Order `4471` belongs to Contoso and was shipped nine days late.

## 3. Configure Live Foundry Access

Replay and local demos do not require Azure authentication. For the live Model demo:

```powershell
az login
$env:FOUNDRY_PROJECT_ENDPOINT = "https://haro-foundryai.services.ai.azure.com/api/projects/aiprj"
$env:FOUNDRY_MODEL = "gpt-5.6-terra"
```

The application uses `AzureCliCredential`, so the active `az login` identity is used. No API key is needed or stored.

The `.env.example` file documents the variable names, but the runner does not automatically load `.env`. Set the variables in the current shell as shown above.

Application Insights is optional. To enable its preflight check in a configured environment:

```powershell
$env:APPLICATIONINSIGHTS_CONNECTION_STRING = "<your connection string>"
```

Do not commit the value. Without it, preflight reports `WARN`; local console observability remains available.

## 4. Preflight and Tests

Run these before every rehearsal or presentation:

```powershell
python -m pip check
python -m unittest discover -s tests -v
python -m compileall -q anatomy scripts tests
python -m anatomy preflight
python -m anatomy list
```

Success criteria:

- `pip check` reports no broken requirements.
- Seven unit tests pass.
- `compileall` exits without output.
- Required preflight rows show `PASS`.
- An App Insights `WARN` is acceptable when cloud export is not configured.
- The organ list shows all 14 in-scope organs as `ready`.

## 5. Fastest Safe Stage Run

Reset the visual state and run the complete story from committed transcripts:

```powershell
python -m anatomy present --replay --reset
```

This is the safest full presentation path. Presenter mode automatically uses projection-width panels and adds five teaching cues to every organ:

1. **Evolution** names the capability's role in the progression of agentic systems.
2. **Milestone** explains what became possible.
3. **The failure** establishes why the organ is necessary.
4. **Watch for** tells the room which visible proof matters.
5. **The difference** and **Say this** close with a before/after contrast and a memorable speaker line.

It performs no model inference and ends with the Reflex Arc callback: `Nobody typed anything, and Ada still woke up and acted.`

To resume at a later beat:

```powershell
python -m anatomy present --from 5 --replay
```

The `present` command is shorthand for the full story with `--stage --present`. For a compact engineering run, continue to use `story`. The `--present` flag can also enrich any individual `beat`, `demo`, `spine`, or `tools` command.

## 6. Recommended Four-Slot Talk

### Slot 1: Opening failure and grounding

```powershell
python -m anatomy beat 0 --replay --stage --reset
python -m anatomy beat 1 --replay --stage
```

What to point out:

- Beat 0 holds the question constant while Instructions change behavior.
- The model has no policy or order evidence.
- Beat 1 displays the real Section 4.2 clause and its local citation.

### Slot 2: Tools and the zero-code capability change

```powershell
python -m anatomy beat 2 --stage
python -m anatomy beat 3 --stage
python -m anatomy tools --tool-search --stage
```

What to point out:

- Beat 2 reads `toolbox.before.yaml` and queries `data/orders.db`.
- Beat 3 reads `toolbox.add-tool.yaml` and prints the newly discovered tool.
- No Python source changes between the two tool lists.
- `--tool-search` prints the advertised-versus-selected token delta.

For the optional real cloud Toolbox operation, use a Bash shell:

```bash
./scripts/setup_toolbox.sh
```

The script runs `azd ai toolbox create` first with the baseline file and then with the add-tool file. This cloud operation requires suitable Foundry permissions and is not required for the local stage demo.

### Slot 3: Deterministic kill and resume

Remove any checkpoint left by rehearsal, then start the job:

```powershell
Remove-Item .anatomy-spine-checkpoint.json -ErrorAction SilentlyContinue
python -m anatomy beat 10 --kill --stage
```

The first command intentionally exits with code `1` after `validate_order` and `apply_policy`. That nonzero exit is the demonstrated process failure, not a broken demo.

Resume in a second command:

```powershell
python -m anatomy spine --resume --stage
```

Expected evidence:

- The first two steps print `SKIP` with their original timestamps.
- The remaining two steps print `RUN`.
- Completed work is not repeated.

Offline fallback:

```powershell
python -m anatomy demo spine --replay --stage
```

### Slot 4: Closing callback

The repository includes `dropbox/escalation-4471.csv`. Run:

```powershell
Remove-Item dropbox\result.txt -ErrorAction SilentlyContinue
python -m anatomy beat 12 --stage
Get-Content dropbox\result.txt
```

Expected evidence:

- Ada prints the wake time and `nobody typed anything`.
- The input event is read from `dropbox/escalation-4471.csv`.
- `dropbox/result.txt` contains the processed event and decision.

Offline fallback:

```powershell
python -m anatomy beat 12 --replay --stage
```

## 7. Every Beat

### Beat 0: Instructions and Model

Offline baseline:

```powershell
python -m anatomy beat 0 --replay --reset
```

Live model only:

```powershell
python -m anatomy demo model --reset
```

The live command should say `live Azure deployment gpt-5.6-terra`. If Foundry is unavailable, the Model organ prints a labeled local fallback and exits nonzero; use `--replay` for the stage-safe version.

Run Instructions independently:

```powershell
python -m anatomy demo instructions
```

Expected evidence: three persona outputs loaded from separate instruction files while the question remains unchanged.

### Beat 1: Knowledge

```powershell
python -m anatomy beat 1
```

Expected evidence: the ungrounded claim is contrasted with the exact Section 4.2 text from `data/refund-policy.txt`.

### Beats 2 and 3: Tools

```powershell
python -m anatomy beat 2
python -m anatomy beat 3
python -m anatomy tools --tool-search
```

Expected evidence: order `4471`, customer `Contoso`, `days_late=9`, and a before/after tool-list difference.

The `tools` shortcut runs beat 2 by default. `python -m anatomy tools --resume` selects beat 3; this `--resume` use is separate from checkpoint resume.

### Beat 4: Memory

```powershell
Remove-Item .anatomy-memory.json -ErrorAction SilentlyContinue
python -m anatomy beat 4
Get-Content .anatomy-memory.json
```

Expected evidence: two distinct thread IDs and successful recall from `.anatomy-memory.json`. This is a local durable-memory implementation, not the Foundry Memory service.

### Beat 5: Guardrails

```powershell
python -m anatomy beat 5
```

Expected evidence: one benign request is allowed; unrelated-customer disclosure and prompt injection are blocked with the responsible layer named.

### Beat 6: Orchestration

```powershell
python -m anatomy beat 6
```

Expected evidence: researcher, writer, and reviewer nodes execute visibly, including the review decision.

### Beat 7: Identity

```powershell
python -m anatomy beat 7
```

Expected evidence: the banner says `SIMULATED`, the repository secret check is clean, token claim examples are shown, and an expected 403 demonstrates the intended least-privilege boundary. No real Blob operation occurs.

### Beat 8: Observability

```powershell
python -m anatomy beat 8 --trace
```

Expected evidence: an indented span tree with durations and token counts. Application Insights may remain a warning when its connection string is absent.

### Beat 9: Metabolism

```powershell
python -m anatomy beat 9
```

Expected evidence: accepted spend reaches 170 tokens; the next charge is denied because it would reach 290 against a 240-token cap. The intended budget stop exits successfully.

### Beat 10: Spine

Use the two-command kill/resume sequence in Section 6. Do not use `--replay` when proving checkpoint behavior, because replay only prints the recorded transcript.

### Beat 11: Skills and Learning

```powershell
python -m anatomy beat 11
```

Expected evidence:

- Skills discovers the checked-in `SKILL.md` files and compares advertise-versus-load token cost.
- Learning reads four known failures, prints the instruction diff, and shows the before/after success rate.
- Learning is a labeled local critic loop, not the cloud Agent Optimizer service.

Run either organ independently:

```powershell
python -m anatomy demo skills
python -m anatomy demo learning
```

### Beat 12: Reflex Arc

Use the file-trigger sequence in Section 6. To demonstrate a different event, add a UTF-8 PDF or CSV to `dropbox/`; the latest file by modification time is processed. `result.txt` is excluded from trigger selection.

## 8. Autopsy: Remove One Organ

Autopsy runs the selected beat twice and prints intact and ablated output side by side:

```powershell
python -m anatomy beat 8 --autopsy knowledge --reset
```

The heading should read `Same model. Same question. One organ removed.` The Knowledge ablation removes the policy lookup from the trace and marks the draft as ungrounded.

Other examples:

```powershell
python -m anatomy demo guardrails --autopsy guardrails
python -m anatomy demo metabolism --autopsy metabolism
python -m anatomy demo spine --autopsy spine
```

Do not combine `--autopsy` with `--replay`. Replays contain only intact recorded runs, so the runner rejects that combination with exit code `2`.

## 9. Record and Replay

Record a successful run:

```powershell
python -m anatomy demo model --record
python -m anatomy demo metabolism --record
```

`--record` overwrites `replays/<organ>.json`. Review the diff before keeping a new recording:

```powershell
git diff -- replays\model.json
```

Replay one organ or the whole story:

```powershell
python -m anatomy demo model --replay
python -m anatomy present --replay --reset
```

Replay mode should work without Azure credentials or network access.

## 10. State and Cleanup

| Path | Purpose | Safe to delete before rehearsal |
|---|---|---|
| `.anatomy-state.json` | Lit organs in the vitals panel | Yes |
| `.anatomy-memory.json` | Local durable memory | Yes |
| `.anatomy-spine-checkpoint.json` | Spine checkpoint | Yes, before starting kill/resume |
| `dropbox/result.txt` | Reflex Arc output | Yes |
| `replays/*.json` | Committed offline transcripts | No, unless intentionally re-recording |

Reset all transient demo state:

```powershell
Remove-Item .anatomy-state.json -ErrorAction SilentlyContinue
Remove-Item .anatomy-memory.json -ErrorAction SilentlyContinue
Remove-Item .anatomy-spine-checkpoint.json -ErrorAction SilentlyContinue
Remove-Item dropbox\result.txt -ErrorAction SilentlyContinue
```

`--reset` clears only the visual vitals state for that command. It does not remove memory or checkpoint files.

## 11. Troubleshooting

### `python -m anatomy ...` fails while `.venv` works

The shell is using the system interpreter. Activate the project environment or invoke it explicitly:

```powershell
.\.venv\Scripts\Activate.ps1
python -m anatomy demo model --replay
```

or:

```powershell
.\.venv\Scripts\python.exe -m anatomy demo model --replay
```

### Dependency resolution fails

Confirm the command is running from the project directory and recreate the isolated environment:

```powershell
Remove-Item .venv -Recurse -Force
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

The compatible exact pair is `agent-framework-foundry==1.11.0` and `azure-ai-projects==2.3.0`.

### Live Model falls back or exits nonzero

Check the active identity and variables:

```powershell
az account show --output table
$env:FOUNDRY_PROJECT_ENDPOINT
$env:FOUNDRY_MODEL
python -m anatomy preflight
```

Then use the offline fallback:

```powershell
python -m anatomy demo model --replay
```

### Spine kill returns exit code 1

This is expected for `--kill`. Run `python -m anatomy spine --resume` next. If rehearsal state is stale, delete `.anatomy-spine-checkpoint.json` and begin again.

### App Insights shows WARN

This is expected unless `APPLICATIONINSIGHTS_CONNECTION_STRING` is configured. The local console trace remains available.

### Output characters are garbled

Use Windows Terminal or a current PowerShell terminal. The CLI configures UTF-8 streams, but redirected output may still require:

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new()
```

## 12. Final Stage Checklist

1. Activate `.venv`.
2. Run tests and preflight.
3. Confirm `python -m anatomy demo model --replay` succeeds.
4. Confirm live Model access if it will be used.
5. Reset transient state.
6. Rehearse Spine kill/resume once.
7. Confirm `dropbox/escalation-4471.csv` exists.
8. Keep `python -m anatomy present --replay --reset` ready as the universal fallback.
