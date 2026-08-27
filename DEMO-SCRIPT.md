# Demo Script

For the full audience-facing narrative, run `python -m anatomy present --replay --reset`. The command embeds the historical framing, failure, proof to watch, before/after contrast, and landing line directly in the terminal UI.

| Beat | Command | Before line | Audience sees | Landing line | Target | Fallback |
|---|---|---|---|---|---|---|
| 0 | `python -m anatomy beat 0 --replay --present --reset` | "Same question, no organs." | Confident but wrong baseline plus instruction variants | "The model is the same; instructions changed behavior immediately." | 90s | `python -m anatomy demo instructions --replay --present` |
| 1 | `python -m anatomy beat 1 --replay --present` | "Now we demand evidence." | Section 4.2 citation from local policy | "Grounding replaced confidence theater with verifiable evidence." | 60s | `python -m anatomy demo knowledge --replay --present` |
| 2 | `python -m anatomy beat 2 --replay --present` | "Can she verify order 4471?" | Toolbox tools + SQLite order lookup | "Tools turned a guess into a lookup." | 60s | `python -m anatomy demo tools --replay --present` |
| 3 | `python -m anatomy beat 3 --replay --present` | "New need, no code edit." | Added tool appears in discovered list | "Capability changed by config, not source edits." | 45s | `python -m anatomy tools --replay --resume --present` |
| 5 | `python -m anatomy beat 5 --replay --present` | "Watch for a leak." | Guardrails block data leak and injection | "Guardrails showed exactly what was blocked and why." | 30s | `python -m anatomy demo guardrails --replay --present` |
| 8 | `python -m anatomy beat 8 --replay --trace --present` | "Prove what happened at 3am." | Local span tree with optional cloud WARN | "Local traces are enough when portals are slow." | 30s | `python -m anatomy demo observability --replay --present` |
| 10 | `python -m anatomy beat 10 --kill --present` then `python -m anatomy spine --resume --present` | "I will kill the process." | Deterministic checkpoint and resume timestamps | "Resume continued without re-running completed steps." | 90s | `python -m anatomy demo spine --replay --present` |
| 12 | `python -m anatomy beat 12 --replay --present` | "Nobody types anything." | Wake line from filesystem trigger | "Nobody typed anything, and Ada still woke up and acted." | 45s | `python -m anatomy demo reflex --replay --present` |