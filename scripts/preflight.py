import importlib
import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

from rich.console import Console
from rich.table import Table

REQUIRED_IMPORTS = ("agent_framework", "azure.ai.projects", "azure.identity", "opentelemetry", "rich")
ORGAN_MODULES = (
    "anatomy.organs.o01_instructions",
    "anatomy.organs.o02_model",
    "anatomy.organs.o03_knowledge",
    "anatomy.organs.o04_tools",
    "anatomy.organs.o05_skills",
    "anatomy.organs.o06_memory",
    "anatomy.organs.o07_guardrails",
    "anatomy.organs.o08_orchestration",
    "anatomy.organs.o09_identity",
    "anatomy.organs.o10_observability",
    "anatomy.organs.o11_reflex_arc",
    "anatomy.organs.o13_spine",
    "anatomy.organs.o14_metabolism",
    "anatomy.organs.o16_learning",
)
REQUIRED_REPLAYS = (
    "instructions",
    "model",
    "knowledge",
    "tools",
    "skills",
    "memory",
    "guardrails",
    "orchestration",
    "identity",
    "observability",
    "reflex_arc",
    "spine",
    "metabolism",
    "learning",
)


def _run(command: list[str]) -> bool:
    try:
        executable = shutil.which(command[0])
        if executable is None:
            return False
        resolved = [executable, *command[1:]]
        if os.name == "nt" and executable.lower().endswith((".cmd", ".bat")):
            resolved = ["cmd.exe", "/d", "/c", *resolved]
        result = subprocess.run(resolved, capture_output=True, text=True, check=False)
        return result.returncode == 0
    except OSError:
        return False


def _check_order_db(path: Path) -> bool:
    try:
        with sqlite3.connect(path) as conn:
            row = conn.execute(
                "SELECT customer, days_late FROM orders WHERE order_id = 4471"
            ).fetchone()
        return bool(row and row[0] == "Contoso" and row[1] == 9)
    except sqlite3.Error:
        return False


def _tool_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- name:"):
            count += 1
    return count


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    checks: list[tuple[str, str, bool, str]] = []

    checks.append(("optional", "az login session", _run(["az", "account", "show"]), "Needed for live cloud demos."))
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
    model = os.getenv("FOUNDRY_MODEL", os.getenv("FOUNDRY_MODEL_NAME", ""))
    checks.append(("optional", "Foundry endpoint configured", bool(endpoint), endpoint or "missing"))
    checks.append(("optional", "Foundry model configured", bool(model), model or "missing"))

    toolbox_file = root / "toolbox.yaml"
    checks.append(("optional", "toolbox.yaml present", toolbox_file.exists(), str(toolbox_file)))
    checks.append(("required", "toolbox.yaml tool entries", _tool_count(toolbox_file) >= 2, "at least two tools declared"))
    checks.append(("required", "toolbox.before.yaml present", (root / "toolbox.before.yaml").exists(), "beat 2 baseline"))
    checks.append(("required", "toolbox.add-tool.yaml present", (root / "toolbox.add-tool.yaml").exists(), "beat 3 add-tool config"))
    checks.append(
        (
            "optional",
            "App Insights configured",
            bool(os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.getenv("APPINSIGHTS_CONNECTIONSTRING")),
            "Set APPLICATIONINSIGHTS_CONNECTION_STRING for cloud export.",
        )
    )

    for module in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module)
            checks.append(("required", f"Import {module}", True, "available"))
        except ImportError as exc:
            checks.append(("required", f"Import {module}", False, str(exc)))

    for module_name in ORGAN_MODULES:
        try:
            module = importlib.import_module(module_name)
            attrs_ok = all(hasattr(module, attr) for attr in ("STORY_BEAT", "FAILURE_IT_FIXES", "LANDING_LINE", "run"))
            checks.append(("required", f"Organ constants {module_name}", attrs_ok, "STORY_BEAT/FAILURE_IT_FIXES/LANDING_LINE/run"))
        except Exception as exc:
            checks.append(("required", f"Organ constants {module_name}", False, str(exc)))

    data_checks = [
        ("required", "refund-policy.txt", (root / "data" / "refund-policy.txt").exists(), "required local policy text"),
        ("required", "refund-policy.pdf", (root / "data" / "refund-policy.pdf").exists(), "required local binary policy"),
        ("required", "crm.json", (root / "data" / "crm.json").exists(), "required customer file"),
        ("required", "tickets/failures.json", (root / "data" / "tickets" / "failures.json").exists(), "required learning tickets"),
    ]
    checks.extend(data_checks)

    orders_db = root / "data" / "orders.db"
    checks.append(("required", "orders.db seed", _check_order_db(orders_db), "order 4471 / Contoso / 9 days late"))

    for replay_name in REQUIRED_REPLAYS:
        replay = root / "replays" / f"{replay_name}.json"
        try:
            json.loads(replay.read_text(encoding="utf-8"))
            checks.append(("required", f"Replay {replay_name}", True, str(replay)))
        except (OSError, ValueError) as exc:
            checks.append(("required", f"Replay {replay_name}", False, str(exc)))

    table = Table(title="Agent Anatomy preflight")
    table.add_column("Check")
    table.add_column("Result")
    table.add_column("Detail")
    required_pass = True
    for level, name, passed, detail in checks:
        if level == "required":
            result = "PASS" if passed else "FAIL"
            row_style = "green" if passed else "red"
            required_pass = required_pass and passed
        else:
            result = "PASS" if passed else "WARN"
            row_style = "green" if passed else "yellow"
        table.add_row(name, result, detail, style=row_style)
    Console().print(table)
    return 0 if required_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
