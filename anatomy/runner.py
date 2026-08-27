import argparse
import asyncio
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from anatomy.banner import firing_line, organ_banner, payoff, vitals_panel
from anatomy.common import DEFAULT_QUESTION, RunReport, save_report_replay
from anatomy.presentation import difference_panel, teaching_intro
from scripts.preflight import main as preflight_main

console = Console()
STATE_PATH = Path(".anatomy-state.json")
QUESTION = DEFAULT_QUESTION


@dataclass(frozen=True, slots=True)
class Organ:
    number: int
    name: str
    beat: int
    status: str
    maturity: str
    module: str


ORGANS = (
    Organ(1, "instructions", 0, "ready", "GA", "anatomy.organs.o01_instructions"),
    Organ(2, "model", 0, "ready", "GA", "anatomy.organs.o02_model"),
    Organ(3, "knowledge", 1, "ready", "GA", "anatomy.organs.o03_knowledge"),
    Organ(4, "tools", 2, "ready", "GA", "anatomy.organs.o04_tools"),
    Organ(5, "skills", 11, "ready", "PREVIEW", "anatomy.organs.o05_skills"),
    Organ(6, "memory", 4, "ready", "LOCAL IMPLEMENTATION", "anatomy.organs.o06_memory"),
    Organ(7, "guardrails", 5, "ready", "LOCAL IMPLEMENTATION", "anatomy.organs.o07_guardrails"),
    Organ(8, "orchestration", 6, "ready", "LOCAL IMPLEMENTATION", "anatomy.organs.o08_orchestration"),
    Organ(9, "identity", 7, "ready", "SIMULATED", "anatomy.organs.o09_identity"),
    Organ(10, "observability", 8, "ready", "LOCAL IMPLEMENTATION", "anatomy.organs.o10_observability"),
    Organ(11, "reflex arc", 12, "ready", "LOCAL IMPLEMENTATION", "anatomy.organs.o11_reflex_arc"),
    Organ(13, "spine", 10, "ready", "LOCAL IMPLEMENTATION", "anatomy.organs.o13_spine"),
    Organ(14, "metabolism", 9, "ready", "LOCAL IMPLEMENTATION", "anatomy.organs.o14_metabolism"),
    Organ(16, "learning", 11, "ready", "LOCAL IMPLEMENTATION", "anatomy.organs.o16_learning"),
)

ORGAN_BY_NAME = {organ.name: organ for organ in ORGANS}
ORGAN_ALIASES = {
    "reflex": "reflex arc",
    "reflex_arc": "reflex arc",
}
BEAT_SEQUENCE = {
    0: ["instructions", "model"],
    1: ["knowledge"],
    2: ["tools"],
    3: ["tools"],
    4: ["memory"],
    5: ["guardrails"],
    6: ["orchestration"],
    7: ["identity"],
    8: ["observability"],
    9: ["metabolism"],
    10: ["spine"],
    11: ["skills", "learning"],
    12: ["reflex arc"],
}


def load_state() -> set[str]:
    if not STATE_PATH.exists():
        return set()
    try:
        return set(json.loads(STATE_PATH.read_text(encoding="utf-8"))["active"])
    except (OSError, ValueError, KeyError, TypeError):
        return set()


def save_state(active: set[str]) -> None:
    STATE_PATH.write_text(json.dumps({"active": sorted(active)}, indent=2), encoding="utf-8")


def show_list() -> None:
    table = Table(title="Ada's organs")
    for heading in ("Organ", "Name", "Beat", "Status", "Maturity"):
        table.add_column(heading)
    for organ in ORGANS:
        table.add_row(f"{organ.number:02d}", organ.name.title(), str(organ.beat), organ.status, organ.maturity)
    console.print(table)


def _import_runner(organ: Organ) -> Callable[..., Awaitable[RunReport]]:
    module = importlib.import_module(organ.module)
    return getattr(module, "run")


def _usage_line(report: RunReport) -> str:
    usage = report.usage
    return f"Tokens: {usage.total_tokens:,} · Est. cost: ${usage.estimated_cost_usd:.4f} · Latency: {usage.latency_seconds:.1f}s"


async def _run_one(organ_name: str, args: argparse.Namespace, *, beat: int | None = None) -> int:
    resolved = ORGAN_ALIASES.get(organ_name, organ_name)
    organ = ORGAN_BY_NAME.get(resolved)
    if organ is None:
        console.print(f"[bold red]Unknown organ:[/] {organ_name}")
        return 2

    active = set() if args.reset else load_state()
    runner = _import_runner(organ)
    present = getattr(args, "present", False)
    story_beat = organ.beat if beat is None else beat
    module = importlib.import_module(organ.module)
    failure = str(getattr(module, "FAILURE_IT_FIXES"))
    run_options = dict(
        question=QUESTION,
        replay=args.replay,
        record=args.record,
        trace=args.trace,
        stage=args.stage,
        autopsy=args.autopsy,
        beat=beat,
        kill=getattr(args, "kill", False),
        resume=getattr(args, "resume", False),
        tool_search=getattr(args, "tool_search", False),
    )
    if args.autopsy and args.replay:
        console.print("[bold red]--autopsy requires a live/local run; committed replays contain only the intact run.[/]")
        return 2

    if args.autopsy:
        intact_options = dict(run_options)
        intact_options["autopsy"] = ""
        intact = await runner(**intact_options)
        ablated = await runner(**run_options)
        console.print(vitals_panel(active, stage=args.stage))
        if present:
            console.print(teaching_intro(organ.name, organ.number, story_beat, failure))
        console.print(organ_banner(organ.number, organ.name, organ.maturity))
        console.print("\n[bold]Same model. Same question. One organ removed.[/]\n")
        console.print(
            Columns(
                [
                    Panel("\n".join(intact.output), title="INTACT", border_style="#50E6FF", expand=True),
                    Panel(
                        "\n".join(ablated.output),
                        title=f"WITHOUT {args.autopsy.upper()}",
                        border_style="#FF4D6D",
                        expand=True,
                    ),
                ],
                expand=True,
                equal=True,
            )
        )
        console.print(payoff(ablated.payoff, _usage_line(ablated)))
        if present:
            console.print(difference_panel(organ.name, ablated.landing_line))
        else:
            console.print(f"[bold]{ablated.landing_line}[/]")
        return 0

    report = await runner(**run_options)

    canonical_name = organ.name.title()
    active.add(canonical_name)
    console.print(vitals_panel(active, stage=args.stage))
    if present:
        console.print(teaching_intro(organ.name, organ.number, story_beat, failure))
    banner_status = organ.maturity
    if report.labels:
        labels = [label for label in report.labels if label and label != organ.maturity]
        if labels:
            banner_status = f"{banner_status} · {' · '.join(labels)}"
    console.print(organ_banner(organ.number, organ.name, banner_status))
    console.print()
    console.print(firing_line(report.firing))
    console.print()
    for line in report.output:
        console.print(line)
    console.print(payoff(report.payoff, _usage_line(report)))
    if present:
        console.print(difference_panel(organ.name, report.landing_line))
    else:
        console.print(f"[bold]{report.landing_line}[/]")

    if args.record:
        path = save_report_replay(report)
        console.print(f"[dim]Recorded replay:[/] {path}")

    save_state(active)
    return 0 if report.status == "ok" else 1


async def run_beat(args: argparse.Namespace) -> int:
    if args.beat not in BEAT_SEQUENCE:
        console.print(f"[bold red]Unknown beat:[/] {args.beat}")
        return 2
    status = 0
    for organ_name in BEAT_SEQUENCE[args.beat]:
        run_status = await _run_one(organ_name, args, beat=args.beat)
        status = max(status, run_status)
    return status


async def run_story(args: argparse.Namespace) -> int:
    beats = [beat for beat in sorted(BEAT_SEQUENCE) if beat >= args.from_beat]
    status = 0
    for beat in beats:
        console.rule(f"BEAT {beat}")
        beat_args = argparse.Namespace(**vars(args))
        beat_args.beat = beat
        run_status = await run_beat(beat_args)
        status = max(status, run_status)
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m anatomy")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")
    subparsers.add_parser("preflight")

    beat = subparsers.add_parser("beat")
    beat.add_argument("beat", type=int)

    story = subparsers.add_parser("story")
    story.add_argument("--from", dest="from_beat", type=int, default=0)

    present = subparsers.add_parser("present", help="run the full story with audience-facing teaching frames")
    present.add_argument("--from", dest="from_beat", type=int, default=0)

    show = subparsers.add_parser("show", help="launch the fullscreen, keyboard-driven live presentation")
    show.add_argument("--from", dest="from_scene", type=int, choices=range(1, 19), default=1)
    show.add_argument("--live", action="store_true", help="prefer live and local execution over committed evidence")

    demo = subparsers.add_parser("demo")
    demo.add_argument("organ")

    spine = subparsers.add_parser("spine")
    tools = subparsers.add_parser("tools")

    for target in (demo, beat, story, present, spine, tools):
        target.add_argument("--replay", action="store_true")
        target.add_argument("--record", action="store_true")
        target.add_argument("--trace", action="store_true")
        target.add_argument("--stage", action="store_true")
        target.add_argument(
            "--present",
            action="store_true",
            help="add speaker guidance, before/after contrast, and evolutionary context",
        )
        target.add_argument("--reset", action="store_true")
        target.add_argument("--autopsy", type=str, default="")
        target.add_argument("--kill", action="store_true")
        target.add_argument("--resume", action="store_true")
        target.add_argument("--tool-search", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "list":
        show_list()
        return 0
    if args.command == "preflight":
        return preflight_main()
    if args.command == "demo":
        return asyncio.run(_run_one(args.organ, args))
    if args.command == "beat":
        return asyncio.run(run_beat(args))
    if args.command == "story":
        return asyncio.run(run_story(args))
    if args.command == "present":
        args.present = True
        args.stage = True
        return asyncio.run(run_story(args))
    if args.command == "show":
        from anatomy.show import run_show

        return run_show(start_scene=args.from_scene, live=args.live)
    if args.command == "spine":
        return asyncio.run(_run_one("spine", args, beat=10))
    if args.command == "tools":
        beat = 3 if args.resume else 2
        return asyncio.run(_run_one("tools", args, beat=beat))
    return 2
