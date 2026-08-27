from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

ACCENT = "#50E6FF"
DANGER = "#FF4D6D"
ORGANS = (
    "Instructions", "Model", "Knowledge", "Tools", "Skills", "Memory",
    "Guardrails", "Orchestration", "Identity", "Observability", "Reflex Arc",
    "Opposable Th.", "Spine", "Metabolism", "Face", "Learning",
)


def prognosis(count: int) -> str:
    if count <= 2:
        return "CRITICAL"
    if count <= 5:
        return "POOR"
    if count <= 8:
        return "GUARDED"
    if count <= 12:
        return "STABLE"
    return "HEALTHY"


def vitals_panel(active: set[str], *, stage: bool = False) -> Panel:
    grid = Table.grid(expand=True)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    cells = []
    for organ in ORGANS:
        lit = organ in active
        cells.append(Text(("● " if lit else "○ ") + organ, style=ACCENT if lit else "dim"))
    while len(cells) % 3:
        cells.append(Text(""))
    for index in range(0, len(cells), 3):
        grid.add_row(*cells[index:index + 3])
    grid.add_row("", "", "")
    grid.add_row(Text(f"PROGNOSIS:  {prognosis(len(active))}", style="bold"), "", "")
    return Panel(
        grid,
        title=f"ADA · VITALS ── {len(active)} / 16 ORGANS",
        border_style=ACCENT,
        width=76 if stage else 68,
    )


def organ_banner(number: int, name: str, status: str) -> Panel:
    title = Text(f"ORGAN {number:02d} · {name.upper()}", style="bold")
    title.append(f"   [{status}]")
    return Panel(title, border_style=ACCENT, width=68)


def firing_line(firing: list[str]) -> Text:
    return Text(f"ORGANS FIRING:  {' · '.join(firing)}")


def payoff(lines: list[str], usage: str) -> Panel:
    body = Group(*(Text(line) for line in lines), Text(usage, style="dim"))
    return Panel(body, title="WHAT JUST HAPPENED", border_style=ACCENT, width=68)


def failure_card(message: str, missing_organ: str, next_command: str) -> Panel:
    body = Text(f"✖ FAILED\n  {message}\n\nMISSING ORGAN:  {missing_organ}\nNEXT:           {next_command}")
    return Panel(body, border_style=DANGER, width=68)
