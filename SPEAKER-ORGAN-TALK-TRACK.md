# Agent Anatomy: Speaker Story

Tell one continuous story: Contoso asks Ada to refund order 4471. Each organ solves the next problem exposed by the previous scene.

For every demo: name the human problem, run evidence with `Space`, point to one decisive line, optionally open that organ's code with `C`, then deliver the landing line.

## Opening: Meet Ada

> Contoso is asking for a refund on order 4471. It sounds simple. But to answer responsibly, Ada must understand the request, know our rules, inspect the order, protect customer data, control cost, survive failure, and explain every decision.

Pause on the empty anatomy.

> We will build those abilities in front of you, one organ at a time. Do not take my word for any claim. Every organ will leave evidence on this screen.

# Act I: Intelligence Is Not Reliability

## Demo 1 | Model: Give Ada a Brain

**What it is:** The foundation model supplies language understanding, reasoning, and generation. It does not supply verified company truth.

**Relatable idea:** A brilliant employee on their first day: capable, articulate, and unfamiliar with your business.

**Set up:**

> First, Ada needs a brain. There are no company instructions, no policy, and no order system attached. Let us see what intelligence alone can do.

Run the evidence, then say:

> That answer is fluent and useful. It handles ambiguity that traditional software was never explicitly coded to understand. But a convincing answer and a verified answer are not the same thing.

**Point to:** Only `Model` is firing. There is no policy citation or order lookup.

**Open the code:** Show `build_model_agent`; only the model client is attached.

**Land here:**

> The model creates possibility. It does not create reliability.

**Bridge:**

> Ada can speak, but she does not know who she is or how we expect her to behave. A brain needs a job description.

## Demo 2 | Instructions: Give Intelligence a Job

**What it is:** Instructions define the agent's role, priorities, tone, evidence standard, and behavioral boundaries.

**Relatable idea:** Giving that brilliant employee a role, an operating manual, and a definition of good work.

**Set up:**

> I will keep the problem and model constant. I will change only the instructions around it.

Run the evidence, then say:

> A terse expert, a patient teacher, and a hostile reviewer behave differently because the application team supplied different instructions. We did not retrain the brain. Its behavior became programmable.

**Point to:** Only `Instructions` is highlighted as the organ under test; three profiles produce three distinct behaviors.

**Open the code:** Show `add_instructions`; contrast `instructions=` with the model-only recipe.

**Land here:**

> The model supplies intelligence. Instructions give that intelligence a job.

**Bridge:**

> Ada now knows how to behave, but instructions cannot tell her what Section 4.2 actually says. Behavior is not evidence.

## Demo 3 | Knowledge: Replace Confidence with Evidence

**What it is:** Knowledge retrieves approved information and grounds responses in sources people can inspect.

**Relatable idea:** Opening the signed contract instead of recalling what it probably says.

**Set up:**

> The previous scene deliberately left us with a confident policy claim. Now Ada must prove it.

Run the evidence. Point to the exact Section 4.2 passage and citation.

> We can read the source and challenge the conclusion. The answer has moved from plausible language to traceable evidence.

**Land here:**

> Confidence is not evidence. Grounding makes the answer verifiable.

**Bridge:**

> We know the policy, but policy alone cannot tell us whether order 4471 exists. Ada needs to inspect the world.

# Act II: From Answering to Acting

## Demo 4 | Tools: Give Ada Hands

**What it is:** Tools let the agent query systems, calculate, and perform governed actions beyond generating text.

**Relatable idea:** Letting a service representative open the order system instead of guessing from an email.

**Set up:**

> A fluent answer cannot query a database. Watch order 4471 change from a claim into a lookup.

Run the evidence. Point to the SQLite result and discovered tool.

> Ada crossed the boundary between talking about the world and inspecting it. Configuration can advertise another capability without rewriting the agent.

**Land here:**

> Tools turn language into action, and guesses into lookups.

**Bridge:**

> Ada can inspect this order. When Contoso returns tomorrow in a new conversation, will she remember the relationship?

## Demo 5 | Memory: Turn Sessions into Continuity

**What it is:** Memory preserves relevant context across turns and sessions.

**Relatable idea:** A trusted colleague remembering the customer instead of requesting the whole history every morning.

**Set up:**

> Watch the thread identifier change. If Ada still recalls the right preference, continuity came from memory, not from this chat.

Run the evidence. Point to two thread IDs and the recalled Contoso preference.

**Land here:**

> A new session does not have to mean organizational amnesia.

**Bridge:**

> Remembering customers makes Ada useful. It also gives her more sensitive information to misuse. Capability has increased, so control must increase with it.

# Act III: Make Power Safe and Accountable

## Demo 6 | Guardrails: Add Boundaries

**What it is:** Guardrails enforce safety, privacy, and policy around inputs, outputs, model calls, and tools.

**Relatable idea:** Brakes on a powerful car: not there to reduce capability, but to make it usable.

**Set up:**

> Ada will face one legitimate request, one attempt to expose another customer's data, and one prompt injection.

Run the evidence. Point to one allowed request and two blocks with explicit reasons.

**Land here:**

> Guardrails do not weaken autonomy. They make autonomy governable.

**Bridge:**

> Individual actions are constrained. Now we must stop hiding research, writing, and approval inside one enormous prompt.

## Demo 7 | Orchestration: Turn a Call into a Process

**What it is:** Orchestration coordinates specialized agents or workflow steps with explicit handoffs, ordering, retries, and review.

**Relatable idea:** Replacing one person doing research, writing, and approval silently with a visible team workflow.

**Set up:**

> Follow the work, not only the final answer: researcher, writer, reviewer.

Run the evidence. Point to the three nodes and review loop.

> Each responsibility has a name and each handoff has a boundary. The intelligence may be probabilistic; the process does not have to be mysterious.

**Land here:**

> Orchestration turns a model call into a repeatable, auditable process.

**Bridge:**

> A visible process tells us what happened. Identity tells us who did it and what they were permitted to touch.

## Demo 8 | Identity: Give Ada a Badge

**What it is:** Identity establishes the acting principal; authorization and least privilege constrain access.

**Relatable idea:** An employee badge that identifies its owner and opens only the doors required for the job.

**Set up:**

> When Ada moves from recommending an action to performing one, two questions are mandatory: who acted, and what were they allowed to do?

Run the evidence. Point to explicit claims, no embedded key, the allowed read, and the denied operation returning 403.

**Land here:**

> Autonomy without identity is power without accountability.

**Bridge:**

> We know who acted. At three in the morning, we will also need to know exactly how the decision unfolded.

## Demo 9 | Observability: Install the Flight Recorder

**What it is:** Observability records model calls, tools, traces, latency, token use, and failure boundaries.

**Relatable idea:** An aircraft flight recorder: the destination cannot explain the journey.

**Set up:**

> “The AI did something strange” is not a production diagnostic. We need the path.

Run the evidence. Point to the span tree, timing, tools, and tokens.

> The trace connects request, lookup, model call, cost, and timing. A mystery has become an investigation.

**Land here:**

> If we cannot see how the agent arrived, we cannot safely operate where it goes next.

**Bridge:**

> We can now see every step. Visibility tells us what the work costs; metabolism decides when that cost must stop.

# Act IV: Bound Autonomy and Make It Durable

## Demo 10 | Metabolism: Give Autonomy a Budget

**What it is:** Metabolism meters tokens, time, tool calls, and money, then enforces hard limits.

**Relatable idea:** A company card with a real spending limit, not an email asking everyone to be careful.

**Set up:**

> An autonomous agent can keep reasoning and spending after useful work is over. A warning asks politely. A budget enforces the ceiling.

Run the evidence. Point to accepted charges and the operation rejected before crossing the cap.

**Land here:**

> Autonomy needs a budget it cannot negotiate with.

**Bridge:**

> Cost is bounded, but long-running work still has a dangerous enemy: process failure.

## Demo 11 | Spine: Survive Failure

**What it is:** The spine checkpoints progress so work resumes safely without repeating completed side effects.

**Relatable idea:** Resuming from a saved checkpoint instead of restarting the journey after every interruption.

**Before the kill:**

> I am going to kill the process on purpose. Ada completed two consequential steps and saved a checkpoint. Exit code 1 is expected; the surviving state is the evidence.

**On resume:**

> The process died, but the work did not forget. Completed steps keep their timestamps and say SKIP. Only unfinished work says RUN. That matters when repetition could issue the same refund twice.

**Point to:** The checkpoint, expected exit, preserved timestamps, `SKIP`, and unfinished `RUN` lines.

**Land here:**

> A durable agent survives the death of its own process.

**Bridge:**

> Ada can survive failure. Next she needs specialized expertise without carrying every manual in every prompt.

# Act V: Expertise and Improvement

## Demo 12 | Skills: Load Expertise on Demand

**What it is:** Skills package reusable procedures, advertising them cheaply and loading details only when relevant.

**Relatable idea:** Carrying an index of professional playbooks instead of memorizing every manual.

**Set up:**

> Putting every procedure into every prompt is expensive, noisy, and hard to maintain. Ada needs the right playbook, not the entire library.

Run the evidence. Point to the small discovery cost and the one selected skill.

**Land here:**

> Skills are expertise on demand: advertise cheaply, load only when needed.

**Bridge:**

> A playbook helps today. If yesterday's failures never change it, the system repeats them forever.

## Demo 13 | Learning: Make Improvement Measurable

**What it is:** Learning turns failure evidence into governed changes and measures whether they helped.

**Relatable idea:** A retrospective that changes the playbook and checks whether incidents decline.

**Set up:**

> A system that records failure but never changes will repeat the mistake with excellent telemetry.

Run the evidence. Point to the instruction diff and before-versus-after score.

> The critic proposes a change and evaluation tests it. We keep the candidate only when performance improves. The model is not secretly rewriting itself; the scaffold changes under governance.

**Land here:**

> Learning turns yesterday's failure into tomorrow's measured improvement.

**Bridge:**

> Ada can improve after work reaches her. The final act begins when work no longer needs a human to start the conversation.

# Final Act: From Assistant to Autonomous System

## Demo 14 | Reflex Arc: Let the Work Find Ada

**What it is:** A reflex arc lets an external event wake the agent and begin a governed routine without a chat prompt.

**Relatable idea:** A smoke detector acting on a signal instead of waiting for someone to ask about smoke.

**Set up:**

> Until now, a person started every interaction. Real work often arrives as a file, event, or message.

Run the evidence, pause, then say:

> Nobody typed anything. An escalation arrived, Ada woke up, and a decision artifact appeared. The work found the agent.

**Point to:** Event time, source file, wake-up line, and result written to disk.

**Land here:**

> Autonomy begins when the work can find the agent.

**Bridge:**

> Waking up is not the same as knowing what to do. Reaction needs a roadmap.

## Demo 15 | Planning: Make the Roadmap Visible

**What it is:** Planning decomposes a goal into ordered, measurable sub-goals with dependencies and success conditions.

**Relatable idea:** Creating a blueprint before asking every contractor to start building.

**Set up:**

> Ada receives one vague escalation and turns it into Verify, Check Policy, Decide, and Compose.

Run the evidence. Point to the four sub-goals and their dependency order before execution.

**Land here:**

> Planning replaces “trust the agent” with “review the roadmap.”

**Bridge:**

> Ada can plan this case. To improve the next one, she needs an explicit view of what changed in the world.

## Demo 16 | Beliefs: Make World State Explicit

**What it is:** Beliefs are queryable, evidence-backed facts about the current world, with governed updates that affect future decisions.

**Relatable idea:** A medical chart recording both the current diagnosis and the evidence that changed it.

**Set up:**

> Memory tells Ada what happened. Beliefs state what Ada now holds to be true and how that truth changes the next decision.

Run the evidence. Point to the before-and-after customer state, evidence, approval rate, and threshold.

> The fact is not hidden in model weights. It can be inspected, challenged, and audited.

**Land here:**

> Beliefs make changing world state explicit, inspectable, and useful on the next run.

# Closing: The Whole Anatomy

Pause on the complete anatomy.

> Contoso asked one simple question. To answer it dependably, Ada needed far more than a fluent model.

> The model gave her intelligence. Instructions gave her a job. Knowledge gave her evidence. Tools gave her reach. Memory gave her continuity. Guardrails and identity gave her boundaries. Orchestration and planning gave her process. Observability gave us sight. Metabolism gave her limits. The spine gave her resilience. Skills and learning let her improve. The reflex arc let the work find her. Beliefs carried verified change into the next decision.

Finish slowly:

> The difference between a compelling demo and a dependable agent is anatomy.

## Emergency One-Line Route

1. **Model:** The model creates possibility; it does not create reliability.
2. **Instructions:** The model supplies intelligence; instructions give it a job.
3. **Knowledge:** Confidence is not evidence; grounding makes the answer verifiable.
4. **Tools:** Tools turn language into action and guesses into lookups.
5. **Memory:** A new session does not have to mean organizational amnesia.
6. **Guardrails:** Boundaries make autonomy governable.
7. **Orchestration:** A model call becomes a repeatable, auditable process.
8. **Identity:** Autonomy without identity is power without accountability.
9. **Observability:** If we cannot see the path, we cannot safely operate the system.
10. **Metabolism:** Autonomy needs a budget it cannot negotiate with.
11. **Spine:** A durable agent survives the death of its own process.
12. **Skills:** Expertise is advertised cheaply and loaded only when needed.
13. **Learning:** Yesterday's failure becomes tomorrow's measured improvement.
14. **Reflex Arc:** Autonomy begins when the work can find the agent.
15. **Planning:** Replace “trust the agent” with “review the roadmap.”
16. **Beliefs:** Changing world state should be explicit and inspectable.