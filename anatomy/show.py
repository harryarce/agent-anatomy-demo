from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from rich.syntax import Syntax
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, RichLog, Static

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class DemoStep:
    label: str
    args: tuple[str, ...]
    expected_exit_codes: tuple[int, ...] = (0,)
    cleanup: tuple[str, ...] = ()
    required_files: tuple[str, ...] = ()
    prepare_if_missing: DemoStep | None = None


@dataclass(frozen=True, slots=True)
class CodeExhibit:
    title: str
    path: str
    anchor: str
    language: str
    mechanism: str
    read_this: tuple[str, ...]
    before: int = 2
    after: int = 6
    package: str | None = None
    within: str | None = None

    @property
    def provenance(self) -> str:
        if self.package is None:
            return "THIS PROJECT"
        return f"{self.package}  v{_package_version(self.package)}"

    @property
    def display_path(self) -> str:
        return self.path if self.package is None else f"{self.package}/{self.path}"


def _package_version(package: str) -> str:
    for candidate in (package.replace("_", "-"), f"{package.replace('_', '-')}-core"):
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            continue
    return "installed"


STACK = (
    ("Microsoft Agent Framework", "agent-framework-core"),
    ("Foundry connector", "agent-framework-foundry"),
    ("Azure AI Projects", "azure-ai-projects"),
    ("Azure Identity (Entra)", "azure-identity"),
    ("OpenTelemetry SDK", "opentelemetry-sdk"),
    ("Azure Monitor OpenTelemetry", "azure-monitor-opentelemetry"),
    ("Textual", "textual"),
    ("Rich", "rich"),
)


def stack_report() -> list[tuple[str, str]]:
    """Live versions from installed metadata, so the stage never shows a stale number."""
    rows = [("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")]
    rows.extend((label, _package_version(dist)) for label, dist in STACK)
    return rows


def _exhibit_root(exhibit: CodeExhibit) -> Path:
    """Repo-relative for our code; the installed package directory for framework code."""
    if exhibit.package is None:
        return ROOT
    spec = importlib.util.find_spec(exhibit.package)
    if spec is None or not spec.submodule_search_locations:
        raise ValueError(f"package not installed: {exhibit.package}")
    return Path(spec.submodule_search_locations[0])


def load_exhibit(exhibit: CodeExhibit) -> tuple[str, int, int]:
    """Return the snippet, its first line number, and the line the anchor sits on."""
    lines = (_exhibit_root(exhibit) / exhibit.path).read_text(encoding="utf-8").splitlines()
    scope = 0
    if exhibit.within is not None:
        enclosing = [index for index, line in enumerate(lines) if exhibit.within in line]
        if len(enclosing) != 1:
            raise ValueError(f"{exhibit.path}: 'within' must match one line, matched {len(enclosing)}")
        scope = enclosing[0]
    hits = [index for index, line in enumerate(lines) if exhibit.anchor in line and index >= scope]
    if not hits or (exhibit.within is None and len(hits) != 1):
        raise ValueError(f"{exhibit.path}: anchor resolved to {len(hits)} lines, expected exactly one")
    focus = hits[0]
    start = max(0, focus - exhibit.before)
    end = min(len(lines), focus + exhibit.after + 1)
    return "\n".join(lines[start:end]), start + 1, focus + 1


@dataclass(frozen=True, slots=True)
class Scene:
    number: int
    chapter: str
    title: str
    message: str
    proof: str
    landing: str
    organs: tuple[int, ...] = ()
    safe_steps: tuple[DemoStep, ...] = ()
    live_steps: tuple[DemoStep, ...] = ()

    def steps_for(self, live: bool) -> tuple[DemoStep, ...]:
        return self.live_steps if live and self.live_steps else self.safe_steps


def step(label: str, *args: str, cleanup: tuple[str, ...] = ()) -> DemoStep:
    return DemoStep(label, args, cleanup=cleanup)


SPINE_KILL_STEP = DemoStep(
    "Kill after checkpoint two",
    ("beat", "10", "--kill", "--stage"),
    expected_exit_codes=(1,),
    cleanup=(".anatomy-spine-checkpoint.json",),
)
SPINE_RESUME_STEP = DemoStep(
    "Resume from the surviving checkpoint",
    ("spine", "--resume", "--stage"),
    required_files=(".anatomy-spine-checkpoint.json",),
    prepare_if_missing=SPINE_KILL_STEP,
)


SCENES = (
    Scene(
        1,
        "THE DISSECTION BEGINS",
        "Meet Ada. Then watch her come alive.",
        "Harry Arce | SME&C DSE | Apps & AI | US East",
        "One agent. Fourteen working organs. Two honest gaps. Every claim will leave evidence.",
        "A useful agent is not a model with a clever prompt. It is a living system of capabilities and constraints.",
    ),
    Scene(
        2,
        "COLD OPEN | REFLEX ARC",
        "Nobody typed anything.",
        "An escalation file lands. Ada is dormant. The event itself wakes her, and she acts.",
        "Watch for the wake time, the source event, and the decision artifact written back to disk.",
        "Autonomy begins when the work can find the agent.",
        (11,),
        (step("Replay the autonomous wake-up", "beat", "12", "--replay", "--stage"),),
        (step("Trigger the autonomous wake-up", "beat", "12", "--stage", cleanup=("onedrive/result.txt",)),),
    ),
    Scene(
        3,
        "ACT I | A BRAIN IS NOT AN AGENT",
        "Same model. Different behavior.",
        "Hold the question constant. Change only the instructions. The answer changes immediately, but it still lacks evidence.",
        "Three instruction sets expose the control surface; the raw model exposes the remaining risk.",
        "The model supplies intelligence. Instructions give that intelligence a job.",
        (1, 2),
        (step("Run the brain-alone comparison", "beat", "0", "--replay", "--stage", "--reset"),),
        (step("Call the live model", "beat", "0", "--stage", "--reset"),),
    ),
    Scene(
        4,
        "ACT I | KNOWLEDGE",
        "Confidence is not evidence.",
        "Ada grounds the refund answer in the actual policy instead of inventing a plausible rule.",
        "Look for Section 4.2 and a citation a human can verify.",
        "Grounding replaced confidence theater with verifiable evidence.",
        (3,),
        (step("Retrieve the policy evidence", "beat", "1", "--replay", "--stage"),),
        (step("Retrieve the local policy evidence", "beat", "1", "--stage"),),
    ),
    Scene(
        5,
        "ACT II | TOOLS",
        "A fluent answer cannot query an order database.",
        "Ada crosses from talking about the world to inspecting a system of record.",
        "Watch order 4471 change from an assumption into a SQLite lookup.",
        "Tools turned a guess into a lookup.",
        (4,),
        (step("Replay the order lookup", "beat", "2", "--replay", "--stage"),),
        (step("Query the local order database", "beat", "2", "--stage"),),
    ),
    Scene(
        6,
        "ACT II | TOOL DISCOVERY",
        "New capability. No Python edit.",
        "A toolbox configuration advertises one more business capability, and discovery finds it on demand.",
        "Compare the advertised tools, selected tool, and token cost before and after the config change.",
        "Capability changed by configuration, not source edits.",
        (4,),
        (step("Discover the configured tool", "tools", "--tool-search", "--replay", "--stage"),),
        (step("Discover the configured tool", "tools", "--tool-search", "--stage"),),
    ),
    Scene(
        7,
        "ACT II | MEMORY",
        "A new thread does not have to mean amnesia.",
        "Ada carries the relevant customer preference across distinct sessions without asking for it again.",
        "The thread identifier changes. The remembered Contoso context survives.",
        "Memory turned isolated chats into continuity over time.",
        (6,),
        (step("Replay cross-session recall", "beat", "4", "--replay", "--stage"),),
        (step("Exercise local durable memory", "beat", "4", "--stage"),),
    ),
    Scene(
        8,
        "ACT III | GUARDRAILS",
        "More capability requires stronger boundaries.",
        "Ada faces a legitimate request, a cross-customer data leak, and a prompt injection.",
        "One request passes. Two are blocked, each with a visible reason.",
        "Guardrails made autonomy governable instead of merely impressive.",
        (7,),
        (step("Replay the attack set", "beat", "5", "--replay", "--stage"),),
        (step("Run the local guardrail checks", "beat", "5", "--stage"),),
    ),
    Scene(
        9,
        "ACT III | ORCHESTRATION",
        "One opaque prompt becomes an auditable workflow.",
        "Research, writing, and review become explicit steps with visible handoffs.",
        "Follow each node and watch the reviewer send weak work back through the loop.",
        "Orchestration turned a model call into a repeatable process.",
        (8,),
        (step("Replay the workflow handoffs", "beat", "6", "--replay", "--stage"),),
        (step("Run the local workflow", "beat", "6", "--stage"),),
    ),
    Scene(
        10,
        "ACT III | IDENTITY",
        "Who acted, and what were they allowed to do?",
        "This local simulation binds Ada to explicit claims and a least-privilege policy. Production uses managed identity and RBAC.",
        "The read succeeds. The excess privilege attempt receives a 403. No key appears in the repository.",
        "Identity made autonomous action attributable and constrained.",
        (9,),
        (step("Replay least privilege", "beat", "7", "--replay", "--stage"),),
        (step("Run the local RBAC simulation", "beat", "7", "--stage"),),
    ),
    Scene(
        11,
        "ACT III | OBSERVABILITY",
        "At 3:00 a.m., the final answer is not enough.",
        "Ada exposes the path from request to policy lookup, order lookup, and drafted decision.",
        "Read the span tree. It carries latency, tokens, tool calls, and the failure boundary.",
        "Observability turned probabilistic behavior into an operable system.",
        (10,),
        (step("Replay the audit trail", "beat", "8", "--replay", "--trace", "--stage"),),
        (step("Emit the local trace", "beat", "8", "--trace", "--stage"),),
    ),
    Scene(
        12,
        "ACT IV | METABOLISM",
        "Autonomy gets a hard budget.",
        "Charges are accepted atomically until the next operation would cross Ada's spend cap.",
        "The final charge is rejected before it can create a partial or hidden overrun.",
        "A budget warning asks politely. Metabolism stops the work.",
        (14,),
        (step("Replay the spend cap", "beat", "9", "--replay", "--stage"),),
        (step("Exercise the local spend cap", "beat", "9", "--stage"),),
    ),
    Scene(
        13,
        "CLIMAX | SPINE: KILL",
        "Now we kill the process.",
        "Ada completes two consequential steps, checkpoints them, and exits in the middle of the job.",
        "Exit code 1 is expected. The surviving checkpoint is the evidence, not an error to hide.",
        "A durable agent must survive the death of its own process.",
        (13,),
        (SPINE_KILL_STEP,),
    ),
    Scene(
        14,
        "CLIMAX | SPINE: RESUME",
        "Completed work does not run twice.",
        "Restart Ada from the checkpoint left by the previous scene.",
        "The first two steps say SKIP with original timestamps. Only unfinished work says RUN.",
        "Resume continued without repeating completed work.",
        (13,),
        (SPINE_RESUME_STEP,),
    ),
    Scene(
        15,
        "ACT V | SKILLS + LEARNING",
        "Expertise loads on demand. Failure improves the scaffold.",
        "Ada selects one modular skill, then a critic loop turns measured failures into better instructions.",
        "Compare discovery cost with loaded guidance, then inspect the before/after evaluation score.",
        "Learning made improvement measured; skills made expertise reusable.",
        (5, 16),
        (step("Replay progressive improvement", "beat", "11", "--replay", "--stage"),),
        (step("Run the local skill and critic loop", "beat", "11", "--stage"),),
    ),
    Scene(
        16,
        "HONEST ANATOMY | TWO GAPS",
        "Useful does not mean finished.",
        "Organ 12, Opposable Thumbs, represents direct computer use. Organ 15, Face, represents a persistent external persona. Both remain planned here.",
        "They stay visibly unlit because this repository does not execute them.",
        "A trustworthy demo labels the frontier instead of pretending it shipped.",
        (12, 15),
    ),
    Scene(
        17,
        "THE WHOLE SYSTEM",
        "Fourteen working organs. Two deliberate gaps.",
        "Intelligence, evidence, action, continuity, control, recovery, economics, and improvement now form one system.",
        "Every capability enables something useful and constrains something dangerous.",
        "The anatomy matters because no single organ can make an agent dependable.",
        tuple(number for number in range(1, 17) if number not in (12, 15)),
    ),
    Scene(
        18,
        "TAKE IT WITH YOU",
        "Build the next organ.",
        "aka.ms/agent-framework  |  Agent Framework docs and samples\naka.ms/mcp              |  Microsoft's public MCP catalog\naka.ms/microsoftfoundry |  Microsoft Foundry Labs",
        "Start with one business failure. Add only the organs that make its outcome observable, constrained, and recoverable.",
        "Thank you. Questions are welcome.",
    ),
)

FRAMEWORK = "agent_framework"
FOUNDRY = "agent_framework_foundry"

EXHIBITS: dict[int, tuple[CodeExhibit, ...]] = {
    2: (
        CodeExhibit(
            "Background agents: an agent delegating to other agents",
            "_harness/_background_agents.py",
            "source_id: str = DEFAULT_BACKGROUND",
            "python",
            "Agents are supplied to a provider that a parent agent can dispatch work to.",
            (
                "Activation stops being a chat turn and becomes delegation between agents.",
                "A Sequence of agents is the whole contract: composition, not orchestration glue.",
            ),
            before=4,
            after=3,
            package=FRAMEWORK,
        ),
        CodeExhibit(
            "Our trigger: the environment wakes the agent",
            "anatomy/organs/o11_reflex_arc.py",
            "def _latest_synced_file() -> Path | None:",
            "python",
            "The agent watches a synced folder and treats the newest artifact as its trigger.",
            (
                "There is no chat loop here. The input is the environment itself.",
                "Point this at OneDrive, SharePoint, or Service Bus and the organ is unchanged.",
            ),
            before=1,
            after=9,
        ),
    ),
    3: (
        CodeExhibit(
            "THE ANATOMY IN ONE SIGNATURE: every organ is a named parameter",
            "_agents.py",
            'AGENT_PROVIDER_NAME: ClassVar[str] = "microsoft.agent_framework"',
            "python",
            "An agent is constructed from a client, instructions, tools, context providers, and middleware.",
            (
                "Read the parameter names: this signature IS the anatomy we are dissecting.",
                "Organs are injected at construction, not inherited or hard-coded.",
            ),
            before=0,
            after=17,
            package=FRAMEWORK,
        ),
        CodeExhibit(
            "Our attachment site: model plus instructions become an agent",
            "anatomy/organs/o02_model.py",
            "agent = Agent(",
            "python",
            "This project builds a real Agent from a Foundry chat client and a credential.",
            (
                "Two organs attach in six lines: the model, and the instructions that govern it.",
                "No API key appears; the credential is the identity organ arriving early.",
            ),
            before=1,
            after=8,
        ),
        CodeExhibit(
            "The Foundry client the agent is composed with",
            "_chat_client.py",
            "project_endpoint: str | None = None,",
            "python",
            "The chat client is a separate, swappable component the agent depends on.",
            (
                "The model is a dependency, not the agent. Swap the client, keep everything else.",
                "Endpoint, deployment, and credential are constructor arguments, not globals.",
            ),
            before=4,
            after=6,
            package=FOUNDRY,
            within="class FoundryChatClient(",
        ),
    ),
    4: (
        CodeExhibit(
            "ContextProvider: the grounding hook that runs before the model",
            "_sessions.py",
            "async def before_run(",
            "python",
            "Providers inject messages, instructions, or tools into the pipeline before invocation.",
            (
                "RAG is not special-cased in the framework. It is a lifecycle hook.",
                "Everything the model will see is assembled through this one signature.",
            ),
            before=1,
            after=7,
            package=FRAMEWORK,
            within="class ContextProvider:",
        ),
        CodeExhibit(
            "Our grounding: the answer is bound to a source file",
            "anatomy/organs/o03_knowledge.py",
            'policy = Path(__file__).resolve().parents[2] / "data" / "refund-policy.txt"',
            "python",
            "The clause is retrieved from a document instead of recalled from weights.",
            (
                "Grounding is a lookup, then a citation a human can re-open.",
                "Replace this file read with a vector index and the contract is identical.",
            ),
            before=2,
            after=6,
        ),
    ),
    5: (
        CodeExhibit(
            "@tool: a Python function becomes a governed model capability",
            "_tools.py",
            ") -> FunctionTool | Callable[[Callable[..., Any]], FunctionTool]:",
            "python",
            "The decorator derives a schema and carries approval and invocation limits.",
            (
                "approval_mode and max_invocations mean tool governance is declarative.",
                "The model never sees your function, only the generated schema.",
            ),
            before=12,
            after=1,
            package=FRAMEWORK,
        ),
        CodeExhibit(
            "Our tool: language becomes a query against a system of record",
            "anatomy/organs/o04_tools.py",
            "def _order_lookup() -> str:",
            "python",
            "The agent opens the order database and reads the real row for 4471.",
            (
                "This is the boundary between talking about data and reading it.",
                "The model never sees the database, only the tool's result.",
            ),
            before=1,
            after=10,
        ),
    ),
    6: (
        CodeExhibit(
            "Our toolbox: new capability declared in configuration",
            "toolbox.add-tool.yaml",
            "- name: carrier_delay_status",
            "yaml",
            "A tool is a declared entry with a name, a kind, and a description.",
            (
                "The description is what the model reads when choosing a tool.",
                "Adding capability here required no change to any Python file.",
            ),
            before=4,
            after=2,
        ),
    ),
    7: (
        CodeExhibit(
            "FoundryMemoryProvider: managed memory attached as a context provider",
            "_memory_provider.py",
            "memory_store_name: str,",
            "python",
            "Foundry-hosted memory plugs into the same provider interface as everything else.",
            (
                "Memory is not agent state. It is a provider you attach and can swap.",
                "scope isolates memories per user or tenant; update_delay batches the writes.",
            ),
            before=8,
            after=6,
            package=FOUNDRY,
        ),
        CodeExhibit(
            "Our memory: state that outlives the conversation",
            "anatomy/organs/o06_memory.py",
            'MEMORY_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")',
            "python",
            "Facts are written to durable storage keyed independently of the thread.",
            (
                "Continuity is a storage decision, not a model capability.",
                "The thread identifier changes; the stored key does not.",
            ),
            before=4,
            after=2,
        ),
    ),
    8: (
        CodeExhibit(
            "AgentMiddleware: intercept the invocation and terminate it",
            "_middleware.py",
            "async def process(",
            "python",
            "Middleware wraps every invocation and can override the result or stop execution.",
            (
                "call_next is the pipeline: not calling it terminates the invocation.",
                "Guardrails live outside the prompt, so instructions cannot talk past them.",
            ),
            before=1,
            after=5,
            package=FRAMEWORK,
            within="class AgentMiddleware(ABC):",
        ),
        CodeExhibit(
            "Our guardrails: refusal carries a stated reason",
            "anatomy/organs/o07_guardrails.py",
            "BLOCKED by content guardrail",
            "python",
            "Each request is evaluated and annotated with the control that acted.",
            (
                "A block without a reason is unauditable. The reason is the feature.",
                "One request passes; two are refused with cause.",
            ),
            before=3,
            after=2,
        ),
    ),
    9: (
        CodeExhibit(
            "WorkflowBuilder: multi-agent choreography as a typed graph",
            "_workflows/_workflow_builder.py",
            "def add_edge(",
            "python",
            "Executors are connected with typed edges and compiled into an immutable workflow.",
            (
                "Orchestration becomes a declarative graph, not nested prompt calls.",
                "A conditional edge is routing logic you can read without running it.",
            ),
            before=1,
            after=5,
            package=FRAMEWORK,
        ),
        CodeExhibit(
            "Our workflow: one request becomes named, ordered steps",
            "anatomy/organs/o08_orchestration.py",
            "output = [",
            "python",
            "Research, drafting, and review are separate auditable nodes.",
            (
                "Each step can be inspected, retried, or replaced on its own.",
                "A single opaque prompt offers none of those three options.",
            ),
            before=1,
            after=8,
        ),
    ),
    10: (
        CodeExhibit(
            "Our identity: Entra credential, no key in the repository",
            "anatomy/organs/o02_model.py",
            "credential = AzureCliCredential()",
            "python",
            "The agent authenticates as a signed-in principal instead of a shared secret.",
            (
                "In production this becomes managed identity with the same code shape.",
                "The credential is closed in a finally block: tokens are lifecycle-managed.",
            ),
            before=2,
            after=4,
        ),
        CodeExhibit(
            "Our least-privilege proof: the actor is a claim",
            "anatomy/organs/o09_identity.py",
            "Decoded token claims: oid=",
            "python",
            "Every action is attributed to a principal and checked against least privilege.",
            (
                "The 403 is the demonstration. Refusal proves the boundary exists.",
                "SIMULATED here; in your cloud this is Azure RBAC.",
            ),
            before=2,
            after=3,
        ),
    ),
    11: (
        CodeExhibit(
            "ChatTelemetryLayer: OpenTelemetry wrapped around the model call",
            "observability.py",
            "class ChatTelemetryLayer(Generic[OptionsCoT]):",
            "python",
            "Token-usage and duration histograms are attached to any chat client by composition.",
            (
                "Spans and token histograms are built in, not bolted on afterwards.",
                "Layering means observability costs you no changes at the call site.",
            ),
            before=0,
            after=9,
            package=FRAMEWORK,
        ),
        CodeExhibit(
            "Our trace: the reasoning path as spans",
            "anatomy/organs/o10_observability.py",
            "Span tree (local console exporter):",
            "python",
            "Latency, tokens, and tool calls are recorded per operation.",
            (
                "Without spans, a failure leaves only a final answer and no path.",
                "Exportable to Application Insights with one connection string.",
            ),
            before=1,
            after=6,
        ),
    ),
    12: (
        CodeExhibit(
            "UsageDetails: token accounting the cost model reads",
            "_types.py",
            "cache_read_input_token_count: int | None",
            "python",
            "Standard and provider-specific token counters, including cache and reasoning tokens.",
            (
                "You cannot cap what you cannot count. These fields are the metering primitive.",
                "Cache-read and reasoning tokens price very differently: the detail matters.",
            ),
            before=4,
            after=2,
            package=FRAMEWORK,
        ),
        CodeExhibit(
            "Our budget: the cap is enforced, not advised",
            "anatomy/organs/o14_metabolism.py",
            "meter.add(input_tokens=charge // 2",
            "python",
            "Each charge is admitted only if it fits inside the cap.",
            (
                "The cap raises an exception. A warning would still let the spend land.",
                "Autonomy without a spending boundary is an unbounded loop.",
            ),
            before=4,
            after=4,
        ),
    ),
    13: (
        CodeExhibit(
            "WorkflowCheckpoint: exactly what survives the crash",
            "_workflows/_checkpoint.py",
            "previous_checkpoint_id: CheckpointID | None = None",
            "python",
            "The checkpoint record carries messages, state, pending events, and lineage.",
            (
                "Durability is a data model, not a retry policy.",
                "previous_checkpoint_id forms the lineage chain that orders a recovery.",
            ),
            before=4,
            after=9,
            package=FRAMEWORK,
        ),
        CodeExhibit(
            "Our spine: the checkpoint is written before the crash",
            "anatomy/organs/o13_spine.py",
            "_save_checkpoint(steps)",
            "python",
            "Completed work is persisted at each step boundary.",
            (
                "Durability is decided before the failure, never after it.",
                "The file on disk is the only thing that survives the process.",
            ),
            before=6,
            after=2,
        ),
    ),
    14: (
        CodeExhibit(
            "Our resume: completed work does not run twice",
            "anatomy/organs/o13_spine.py",
            "if step.done:",
            "python",
            "Restart reads the checkpoint and re-executes only unfinished steps.",
            (
                "This is why a refund is not issued twice after a restart.",
                "Determinism comes from recorded state, not from retry luck.",
            ),
            before=2,
            after=4,
        ),
    ),
    15: (
        CodeExhibit(
            "InlineSkill: expertise with declared resources and scripts",
            "_skills.py",
            "frontmatter: SkillFrontmatter,",
            "python",
            "A skill carries frontmatter metadata, instructions, resources, and executable scripts.",
            (
                "Skills are discoverable units, so the model loads detail only when it selects one.",
                "Resources and scripts ship with the skill: expertise is packaged, not pasted.",
            ),
            before=3,
            after=5,
            package=FRAMEWORK,
            within="class InlineSkill(Skill):",
        ),
        CodeExhibit(
            "FoundryEvals: the measurement loop that closes learning",
            "_foundry_evals.py",
            "def __init__(",
            "python",
            "Evaluation runs against a Foundry project and returns scored results.",
            (
                "Improvement becomes a measured delta instead of a prompt-tweaking anecdote.",
                "This is the organ that turns yesterday's failures into tomorrow's instructions.",
            ),
            before=1,
            after=8,
            package=FOUNDRY,
            within="class FoundryEvals:",
        ),
        CodeExhibit(
            "Our learning: the failure rewrites the instruction",
            "anatomy/organs/o16_learning.py",
            'new_instruction = "Decide refunds only after policy citation and order lookup."',
            "python",
            "Measured failures produce a concrete instruction change.",
            (
                "The improvement is a diff you can review, not a vague retrain.",
                "Evidence in, instruction out, score measured again.",
            ),
            before=2,
            after=2,
        ),
    ),
    17: (
        CodeExhibit(
            "Evaluator: any backend can score an agent",
            "_evaluation.py",
            "eval_name: str,",
            "python",
            "Foundry, a local LLM judge, or a custom scorer all satisfy one protocol.",
            (
                "Every organ we dissected is a protocol or a parameter. That is the design.",
                "Composition over inheritance is what makes this anatomy swappable.",
            ),
            before=6,
            after=1,
            package=FRAMEWORK,
            within="class Evaluator(Protocol):",
        ),
    ),
}

PANEL_STYLES = {
    "vitals": "#4C7A94",
    "organ": "bold #50E6FF",
    "payoff": "#7EE787",
    "compare": "#F2CC60",
    "panel": "#9FB7C2",
}
BODY_STYLE = "#EAF4F4"


def _classify_panel(line: str) -> str:
    if "VITALS" in line:
        return "vitals"
    if "WHAT JUST HAPPENED" in line:
        return "payoff"
    if "ORGAN " in line:
        return "organ"
    if "INTACT" in line or "WITHOUT" in line:
        return "compare"
    return "panel"


def _body_style(stripped: str) -> str:
    if stripped.startswith("ORGANS FIRING"):
        return "bold #C792EA"
    if any(marker in stripped for marker in ("BLOCKED", "BUDGET STOP", "TERMINATED", "FAILED", "403")):
        return "bold #FF4D6D"
    if stripped.startswith("SKIP"):
        return "#7FA6B8"
    if stripped.startswith("RUN ") or "ALLOWED" in stripped:
        return "#7EE787"
    if any(marker in stripped for marker in ("[SIMULATED]", "[WARN]", "[AUTOPSY]")):
        return "#F2CC60"
    return BODY_STYLE


def evidence_text(raw: str) -> Text:
    """Colour captured organ output by section, with blank lines between panels."""
    lines = raw.splitlines()
    closing_line = max((i for i, line in enumerate(lines) if line.strip()), default=-1)
    rendered = Text()
    index = 0
    previous_style: str | None = None
    previous_stripped = ""
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped[:1] in {"\u256d", "\u250c"}:
            end = index
            while end < len(lines) and lines[end].strip()[:1] not in {"\u2570", "\u2514"}:
                end += 1
            block = lines[index : end + 1]
            style = PANEL_STYLES[_classify_panel("\n".join(block))]
            if rendered.plain:
                rendered.append("\n")
            for panel_line in block:
                rendered.append(f"{panel_line}\n", style=style)
            rendered.append("\n")
            index = end + 1
            continue
        style = "bold #7EE787" if index == closing_line else _body_style(stripped)
        if (
            style == BODY_STYLE
            and previous_style not in (BODY_STYLE, None)
            and stripped[:1].islower()
            and not previous_stripped.endswith((".", ":", "?", "!"))
        ):
            style = previous_style  # the organ wrapped a long line; keep the emphasis intact
        rendered.append(f"{lines[index]}\n", style=style)
        if stripped:
            previous_style, previous_stripped = style, stripped
        index += 1
    return rendered


def _section_rule(title: str, style: str) -> Text:
    return Text(f"\u258c {title}\n", style=f"bold {style}")


ADA_BANNER = (
    "┌                                                    ┐",
    "",
    "    ████  █████   ████       ▄▄▄▄▄▄▄▄▄ ",
    "   ██  ██ ██  ██ ██  ██     █ ▀▀▀ ▀▀▀ █",
    "   ██████ ██  ██ ██████     █         █",
    "   ██  ██ ██  ██ ██  ██     █  ▄▄▄▄▄  █",
    "   ██  ██ █████  ██  ██      ▀▀▀▀▀▀▀▀▀ ",
    "",
    "└        a n a t o m y   o f   a n   a g e n t        ┘",
)

ANATOMY = (
    (1, "Instructions", True),
    (2, "Model", True),
    (3, "Knowledge", True),
    (4, "Tools", True),
    (5, "Skills", True),
    (6, "Memory", True),
    (7, "Guardrails", True),
    (8, "Orchestration", True),
    (9, "Identity", True),
    (10, "Observability", True),
    (11, "Reflex Arc", True),
    (12, "Opposable Thumbs", False),
    (13, "Spine", True),
    (14, "Metabolism", True),
    (15, "Face", False),
    (16, "Learning", True),
)


class AnatomyShow(App[None]):
    TITLE = "Agent Anatomy Live"
    SUB_TITLE = "Harry Arce | SME&C DSE | Apps & AI | US East"

    CSS = """
    Screen {
        background: #071018;
        color: #EAF4F4;
    }

    #brand {
        height: 3;
        padding: 1 2 0 2;
        background: #0C1C29;
        border-bottom: heavy #50E6FF;
        text-style: bold;
    }

    #main {
        height: 1fr;
    }

    #anatomy {
        width: 27;
        min-width: 23;
        padding: 1 1;
        background: #0A1721;
        border-right: tall #21445A;
    }

    #stage {
        width: 1fr;
        padding: 1 2;
    }

    #eyebrow {
        height: 2;
        color: #F2CC60;
        text-style: bold;
    }

    #scene-title {
        height: 3;
        color: #FFFFFF;
        text-style: bold;
    }

    #message {
        height: auto;
        min-height: 3;
        margin-bottom: 1;
        color: #D8E8EE;
    }

    #proof {
        height: auto;
        min-height: 3;
        padding: 0 1;
        margin-bottom: 1;
        border-left: thick #50E6FF;
        color: #B9CDD6;
    }

    #console {
        height: 1fr;
        min-height: 8;
        padding: 1;
        background: #020609;
        border: round #35637A;
        scrollbar-color: #50E6FF;
        scrollbar-background: #102532;
    }

    #landing {
        height: auto;
        min-height: 3;
        margin-top: 1;
        padding: 0 1;
        color: #7EE787;
        text-style: bold;
        border-left: thick #7EE787;
    }

    #controls {
        height: 2;
        padding: 0 2;
        background: #0C1C29;
        color: #9FB7C2;
    }

    Footer {
        height: 1;
        background: #102532;
    }
    """

    BINDINGS = [
        Binding("left", "previous", "Previous", priority=True),
        Binding("right", "next", "Next", priority=True),
        Binding("space", "run_demo", "Run demo", priority=True),
        Binding("c", "toggle_code", "Show / hide code", priority=True),
        Binding("r", "toggle_mode", "Replay / live", priority=True),
        Binding("home", "first", "First", priority=True),
        Binding("end", "last", "Last", priority=True),
        Binding("escape", "cancel_demo", "Cancel demo", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def __init__(self, *, start_scene: int = 1, live: bool = False) -> None:
        super().__init__()
        self.scene_index = start_scene - 1
        self.live = live
        self.running_demo = False
        self.exhibit_index: int | None = None
        self._cancel_requested = False
        self._process: asyncio.subprocess.Process | None = None

    def compose(self) -> ComposeResult:
        yield Static(id="brand")
        with Horizontal(id="main"):
            yield Static(id="anatomy")
            with Vertical(id="stage"):
                yield Static(id="eyebrow")
                yield Static(id="scene-title")
                yield Static(id="message")
                yield Static(id="proof")
                yield RichLog(id="console", highlight=False, markup=False, wrap=True)
                yield Static(id="landing")
        yield Static(id="controls")
        yield Footer()

    def on_mount(self) -> None:
        self._render_scene()

    def _render_scene(self) -> None:
        scene = SCENES[self.scene_index]
        self.query_one("#brand", Static).update(
            f"AGENT ANATOMY LIVE   |   HARRY ARCE   |   SCENE {scene.number:02d}/{len(SCENES):02d}"
        )
        self.query_one("#eyebrow", Static).update(scene.chapter)
        self.query_one("#scene-title", Static).update(scene.title)
        self.query_one("#message", Static).update(scene.message)
        self.query_one("#proof", Static).update(f"WATCH FOR  {scene.proof}")
        self.query_one("#landing", Static).update(scene.landing)
        self.query_one("#anatomy", Static).update(self._anatomy_text(scene))

        log = self.query_one("#console", RichLog)
        log.clear()
        if scene.number == len(SCENES):
            log.write(self._stack_text())
        elif scene.number == 1:
            log.write(self._ada_banner_text())
        elif scene.safe_steps:
            mode = "LIVE / LOCAL" if self.live else "STAGE-SAFE"
            log.write(Text(f"READY  {mode}\n\nPress Space to run the evidence for this scene.", style="bold #50E6FF"))
        else:
            log.write(Text("PRESENTER MOMENT\n\nNo executable claim on this scene. Let the idea land.", style="#9FB7C2"))
        self._render_controls()

    def _ada_banner_text(self) -> Text:
        text = Text()
        for line in ADA_BANNER:
            style = "#35637A" if line[:1] in {"\u250c", "\u2514"} else "#50E6FF"
            text.append(f"{line}\n", style=style)
        text.append("\nFourteen organs run here. Two are still on the design bench.", style="#9FB7C2")
        return text

    def _stack_text(self) -> Text:
        text = Text("THE STACK THIS DEMO ACTUALLY RAN ON\n\n", style="bold #F2CC60")
        for label, version in stack_report():
            text.append(f"  {label:<30}", style="#EAF4F4")
            text.append(f"{version}\n", style="bold #7EE787")
        text.append("\nVersions are read from installed package metadata at runtime.", style="dim")
        return text

    def _anatomy_text(self, scene: Scene) -> Text:
        completed = {organ for prior in SCENES[: self.scene_index + 1] for organ in prior.organs if organ not in (12, 15)}
        text = Text("ADA / ORGAN VITALS\n\n", style="bold #50E6FF")
        for number, name, implemented in ANATOMY:
            if not implemented:
                marker, style, suffix = "◇", "#637985", "  PLANNED"
            elif number in scene.organs:
                marker, style, suffix = "◆", "bold #F2CC60", "  FIRING"
            elif number in completed:
                marker, style, suffix = "●", "#7EE787", ""
            else:
                marker, style, suffix = "○", "#637985", ""
            text.append(f"{marker} {number:02d}  {name}{suffix}\n", style=style)
        text.append(f"\n{len(completed):02d} / 14 RUNNABLE ONLINE", style="bold #EAF4F4")
        return text

    def _render_controls(self) -> None:
        scene = SCENES[self.scene_index]
        mode = "LIVE / LOCAL" if self.live else "STAGE-SAFE"
        if self.running_demo:
            status = "RUNNING  |  Esc cancels"
        elif scene.safe_steps:
            status = "Space runs evidence"
        else:
            status = "Presenter scene"
        code = "C shows code" if EXHIBITS.get(scene.number) else "no code exhibit"
        self.query_one("#controls", Static).update(
            f"{mode}  |  {status}  |  {code}  |  R switches mode  |  Left/Right navigate"
        )

    def action_toggle_code(self) -> None:
        exhibits = EXHIBITS.get(SCENES[self.scene_index].number, ())
        if self.running_demo or not exhibits:
            return

        nxt = 0 if self.exhibit_index is None else self.exhibit_index + 1
        self.exhibit_index = None if nxt >= len(exhibits) else nxt
        if self.exhibit_index is None:
            self._render_scene()
            return
        self._render_exhibit(exhibits[self.exhibit_index], self.exhibit_index, len(exhibits))

    def _render_exhibit(self, exhibit: CodeExhibit, position: int, total: int) -> None:
        log = self.query_one("#console", RichLog)
        log.clear()
        counter = f"  [{position + 1}/{total}]" if total > 1 else ""
        log.write(Text(f"CODE EXHIBIT{counter}   {exhibit.title}", style="bold #F2CC60"))
        log.write(Text(f"{exhibit.provenance}   ·   {exhibit.display_path}\n", style="#7FA6B8"))
        try:
            snippet, start_line, focus_line = load_exhibit(exhibit)
        except (OSError, ValueError) as error:
            log.write(Text(f"Exhibit unavailable: {error}", style="bold #FF4D6D"))
            return
        log.write(
            Syntax(
                snippet,
                exhibit.language,
                theme="monokai",
                line_numbers=True,
                start_line=start_line,
                highlight_lines={focus_line},
                word_wrap=True,
            )
        )
        log.write(Text(f"\nWHAT IT DOES   {exhibit.mechanism}", style="#EAF4F4"))
        for note in exhibit.read_this:
            log.write(Text(f"WHY IT MATTERS {note}", style="#7EE787"))
        log.write(Text("\nPress C for the next exhibit, or Space to run the evidence.", style="dim"))

    def action_previous(self) -> None:
        if not self.running_demo and self.scene_index > 0:
            self.scene_index -= 1
            self.exhibit_index = None
            self._render_scene()

    def action_next(self) -> None:
        if not self.running_demo and self.scene_index < len(SCENES) - 1:
            self.scene_index += 1
            self.exhibit_index = None
            self._render_scene()

    def action_first(self) -> None:
        if not self.running_demo:
            self.scene_index = 0
            self.exhibit_index = None
            self._render_scene()

    def action_last(self) -> None:
        if not self.running_demo:
            self.scene_index = len(SCENES) - 1
            self.exhibit_index = None
            self._render_scene()

    def action_toggle_mode(self) -> None:
        if not self.running_demo:
            self.live = not self.live
            self._render_scene()

    async def action_run_demo(self) -> None:
        scene = SCENES[self.scene_index]
        steps = scene.steps_for(self.live)
        if self.running_demo or not steps:
            return

        self.running_demo = True
        self.exhibit_index = None
        self._cancel_requested = False
        self._render_controls()
        log = self.query_one("#console", RichLog)
        log.clear()
        try:
            succeeded = await self._run_steps(steps, log)
            if self._cancel_requested:
                log.write(Text("\nDEMO CANCELLED  |  No fallback was started.", style="bold #F2CC60"))
            elif not succeeded and self.live and scene.safe_steps != steps:
                log.write(Text("\nLIVE PATH FAILED  |  FALLING BACK TO COMMITTED EVIDENCE\n", style="bold #F2CC60"))
                succeeded = await self._run_steps(scene.safe_steps, log)
            if succeeded and not self._cancel_requested:
                log.write(Text("\nEVIDENCE COMPLETE", style="bold #7EE787"))
            elif not self._cancel_requested:
                log.write(Text("\nDEMO STOPPED  |  Review the output above before continuing.", style="bold #FF4D6D"))
        finally:
            self._process = None
            self.running_demo = False
            self._render_controls()

    async def _run_steps(self, steps: tuple[DemoStep, ...], log: RichLog) -> bool:
        for demo_step in steps:
            missing_files = [relative for relative in demo_step.required_files if not (ROOT / relative).exists()]
            if missing_files and demo_step.prepare_if_missing is not None:
                log.write(Text("CHECKPOINT ABSENT  |  Staging the deterministic kill first.\n", style="bold #F2CC60"))
                if not await self._run_steps((demo_step.prepare_if_missing,), log):
                    return False

            for relative_path in demo_step.cleanup:
                (ROOT / relative_path).unlink(missing_ok=True)

            command = (sys.executable, "-m", "anatomy", *demo_step.args)
            log.write(_section_rule("COMMAND", "#50E6FF"))
            log.write(Text(f"  $ python -m anatomy {' '.join(demo_step.args)}", style="#7FA6B8"))
            log.write(Text(f"  {demo_step.label}\n", style="dim"))
            environment = os.environ.copy()
            environment.update({"PYTHONUTF8": "1", "COLUMNS": "110", "LINES": "40"})
            self._process = await asyncio.create_subprocess_exec(
                *command,
                cwd=ROOT,
                env=environment,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            output, _ = await self._process.communicate()
            # Rich >=15 honours carriage returns, so CRLF from Windows subprocesses would blank each line.
            rendered = output.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "").strip()
            log.write(_section_rule("EVIDENCE", "#F2CC60"))
            log.write(evidence_text(rendered) if rendered else Text("  (command produced no output)", style="dim"))
            if self._cancel_requested:
                return False
            exit_code = self._process.returncode
            expected = exit_code in demo_step.expected_exit_codes
            exit_style = "#7EE787" if expected else "#FF4D6D"
            expectation = "EXPECTED" if expected else "UNEXPECTED"
            log.write(_section_rule("RESULT", exit_style))
            log.write(Text(f"  {expectation} EXIT  {exit_code}\n", style=f"bold {exit_style}"))
            if not expected:
                return False
        return True

    def action_cancel_demo(self) -> None:
        if self._process is not None and self._process.returncode is None:
            self._cancel_requested = True
            self._process.terminate()


def run_show(*, start_scene: int = 1, live: bool = False) -> int:
    AnatomyShow(start_scene=start_scene, live=live).run()
    return 0