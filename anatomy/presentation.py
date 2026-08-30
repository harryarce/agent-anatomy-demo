from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

ACCENT = "#50E6FF"
BEFORE = "#FF4D6D"
AFTER = "#7EE787"
HISTORY = "#F2CC60"


@dataclass(frozen=True, slots=True)
class TeachingFrame:
    milestone: str
    era: str
    before: str
    after: str
    watch_for: str
    significance: str


FRAMES = {
    "instructions": TeachingFrame(
        "Behavior becomes programmable",
        "PROMPTED SYSTEMS",
        "A raw model responds, but its role, tone, and boundaries drift.",
        "Explicit instructions turn general intelligence into a dependable role.",
        "One question; three instruction sets; three visibly different behaviors.",
        "Instructions were the first control surface for shaping model behavior without retraining.",
    ),
    "model": TeachingFrame(
        "Reasoning enters software",
        "FOUNDATION MODELS",
        "Traditional software cannot interpret an ambiguous request it was never coded for.",
        "A foundation model can understand language, reason, and draft a response.",
        "The answer sounds capable, yet remains tentative because no evidence is connected.",
        "The model supplies general intelligence; every later organ makes that intelligence dependable.",
    ),
    "knowledge": TeachingFrame(
        "Answers become grounded",
        "RETRIEVAL-AUGMENTED GENERATION",
        "The model can make a fluent policy claim that nobody can verify.",
        "Grounding attaches the answer to evidence and a citation.",
        "Compare the confident guess with the exact Section 4.2 policy text.",
        "Grounding moved agentic systems from plausible generation toward evidence-backed decisions.",
    ),
    "tools": TeachingFrame(
        "Language becomes action",
        "TOOL-USING AGENTS",
        "The model can discuss order 4471 but cannot know whether it exists.",
        "A tool lets the agent query the system of record and acquire new capabilities.",
        "Watch a guess become a SQLite lookup, then watch configuration add another tool.",
        "Tool use crossed the boundary from chat about the world to software that can inspect and change it.",
    ),
    "memory": TeachingFrame(
        "Sessions become relationships",
        "STATEFUL AGENTS",
        "Each new conversation starts from zero and forgets customer preferences.",
        "Durable memory carries relevant facts across thread boundaries.",
        "The thread ID changes while the recalled Contoso preference survives.",
        "Memory gave agents continuity, enabling personalization and work that spans sessions.",
    ),
    "guardrails": TeachingFrame(
        "Capability gains boundaries",
        "RESPONSIBLE AI",
        "A capable agent may disclose unrelated data or obey hostile instructions.",
        "Layered controls allow useful requests while blocking unsafe behavior.",
        "One request passes; PII leakage and prompt injection are blocked with reasons.",
        "Guardrails made increasing autonomy governable instead of merely impressive.",
    ),
    "orchestration": TeachingFrame(
        "One agent becomes a system",
        "WORKFLOWS AND MULTI-AGENT SYSTEMS",
        "One opaque prompt mixes research, writing, judgment, and review.",
        "Specialized steps create explicit handoffs, decisions, and review loops.",
        "Follow the researcher, writer, and reviewer as separate auditable nodes.",
        "Orchestration turned single model calls into repeatable processes with separation of concerns.",
    ),
    "identity": TeachingFrame(
        "Autonomy becomes accountable",
        "ZERO-TRUST AGENTS",
        "Shared secrets cannot prove which agent acted or limit what it may access.",
        "Explicit identity and least privilege bind every action to an accountable principal.",
        "No keys appear in the repo, claims identify the actor, and excess privilege gets a 403.",
        "Identity is foundational when agents move from recommending actions to performing them.",
    ),
    "observability": TeachingFrame(
        "Reasoning becomes inspectable",
        "LLM OPERATIONS",
        "A failure leaves only a final answer and no trustworthy execution path.",
        "Traces expose model calls, tools, latency, tokens, and failure points.",
        "Read the span tree from request to policy lookup, order lookup, and draft.",
        "Observability made probabilistic systems operable, debuggable, and measurable in production.",
    ),
    "metabolism": TeachingFrame(
        "Autonomy gets a budget",
        "ECONOMIC CONTROL",
        "An agent can loop, consume tokens, and accumulate cost without a hard stop.",
        "Token and currency budgets constrain how long the system may keep working.",
        "The first charges pass; the charge that would cross the cap is rejected atomically.",
        "Metabolic limits made autonomous execution economically predictable.",
    ),
    "spine": TeachingFrame(
        "Long-running work survives failure",
        "DURABLE EXECUTION",
        "A process crash can lose progress or repeat a consequential action.",
        "Checkpoints resume from the last safe boundary without replaying completed work.",
        "Kill after step two, then verify those timestamps are skipped on resume.",
        "Durable execution let agents own work that outlives one process, request, or machine.",
    ),
    "skills": TeachingFrame(
        "Expertise becomes modular",
        "PROGRESSIVE DISCLOSURE",
        "Packing every procedure into every prompt is expensive and hard to maintain.",
        "Skills advertise cheaply and load detailed guidance only when needed.",
        "Compare the small discovery cost with the content loaded for one selected skill.",
        "Skills made agent expertise reusable, composable, and economical at scale.",
    ),
    "learning": TeachingFrame(
        "Failures improve the scaffold",
        "EVALUATION-DRIVEN OPTIMIZATION",
        "The agent repeats the same mistake because yesterday's failures change nothing.",
        "A critic loop converts failure evidence into an instruction improvement and measures it.",
        "Observe the instruction diff and the before-versus-after success rate.",
        "Learning loops shifted progress from anecdotal prompt tweaking to measured system improvement.",
    ),
    "planning": TeachingFrame(
        "Goals become executable plans",
        "TASK DECOMPOSITION",
        "A reactive agent treats a complex escalation as one opaque action.",
        "Decomposed sub-goals expose dependencies, checkpoints, and independent failure paths.",
        "Follow Verify, CheckPolicy, Decide, and Compose in the dependency plan.",
        "Planning made autonomous work measurable and auditable before execution begins.",
    ),
    "beliefs": TeachingFrame(
        "World state becomes explicit",
        "STATE REPRESENTATION",
        "The agent cannot explain which changing facts shaped its next decision.",
        "A queryable belief store records evidence, updates, and their downstream effects.",
        "Compare the before-and-after customer tier, approval rate, and decision threshold.",
        "Beliefs made learning persistent, interpretable, and available to future decisions.",
    ),
    "reflex arc": TeachingFrame(
        "Agents become event-driven",
        "AUTONOMOUS ROUTINES",
        "The agent remains idle until a human opens a chat and asks it to act.",
        "An external event wakes the agent, which evaluates the event and produces an action.",
        "Nobody types a prompt; a dropped file triggers a visible decision artifact.",
        "Event-driven activation completed the shift from conversational assistants to autonomous systems.",
    ),
}


def teaching_intro(name: str, number: int, beat: int, failure: str) -> Group:
    frame = FRAMES[name]
    header = Text()
    header.append(f"EVOLUTION {beat:02d}  ", style=f"bold {HISTORY}")
    header.append(frame.era, style="bold")
    header.append(f"   |   ORGAN {number:02d}: {name.upper()}", style=ACCENT)

    context = Table.grid(expand=True, padding=(0, 1))
    context.add_column(width=13)
    context.add_column(ratio=1)
    context.add_row(Text("MILESTONE", style=f"bold {HISTORY}"), Text(frame.milestone, style="bold"))
    context.add_row(Text("THE FAILURE", style=f"bold {BEFORE}"), Text(failure))
    context.add_row(Text("WATCH FOR", style=f"bold {ACCENT}"), Text(frame.watch_for))
    return Group(
        Panel(header, border_style=HISTORY, width=76),
        Panel(context, title="WHY THIS ORGAN EXISTS", border_style=ACCENT, width=76),
    )


def difference_panel(name: str, landing_line: str) -> Group:
    frame = FRAMES[name]
    comparison = Table.grid(expand=True, padding=(0, 2))
    comparison.add_column(ratio=1)
    comparison.add_column(ratio=1)
    comparison.add_row(Text("WITHOUT THIS ORGAN", style=f"bold {BEFORE}"), Text("WITH THIS ORGAN", style=f"bold {AFTER}"))
    comparison.add_row(Text(frame.before), Text(frame.after))

    takeaway = Text()
    takeaway.append("EVOLUTIONARY ROLE  ", style=f"bold {HISTORY}")
    takeaway.append(frame.significance)
    takeaway.append("\n\nSAY THIS  ", style=f"bold {ACCENT}")
    takeaway.append(f'"{landing_line}"', style="bold")
    return Group(
        Panel(comparison, title="THE DIFFERENCE", border_style=AFTER, width=76),
        Panel(takeaway, title="MAKE IT MEMORABLE", border_style=HISTORY, width=76),
    )