# Agent Anatomy Organs & Microsoft Stack Integration

This document maps each agent anatomy organ to specific Microsoft Agent Framework, Azure AI Foundry, and Copilot Studio components.

## New Organs: Planning & Beliefs

### o12: Planning (Beat 13)

**Industry Concept:** Multi-step reasoning, goal decomposition, structured planning

**What it demonstrates:**
- Agents break complex problems into measurable sub-steps before execution
- Each sub-step is checkable and can fail independently
- A plan preview shows dependencies and expected causality before execution

**Microsoft Stack Integration:**

| Component | Role | Example |
|-----------|------|---------|
| **Agent Framework** | Core orchestration | `Agent.run()` with plan-aware instructions |
| **Structured Prompting** | Plan generation | System prompt: "Before acting, decompose into steps with dependencies" |
| **Agent Tools** | Sub-step execution | Tool definitions that map to planned sub-goals |
| **Power Automate (Copilot Studio)** | Parallelization | Parallel branches for independent sub-goals (e.g., verify order + check policy concurrently) |
| **Azure AI Foundry** | Model selection | Use gpt-4o for complex decomposition, gpt-4-turbo for execution |
| **OpenTelemetry Spans** | Audit trail | One span per sub-goal with parent-child relationships |

**Copilot Studio Implementation:**
```
Topic: Refund Escalation
├─ Topic Call: Create Plan
│  └─ Parse JSON output: [subgoal1, subgoal2, subgoal3]
├─ Topic Call: Execute Subgoal 1 (parallel with 2, 3 if independent)
├─ Topic Call: Execute Subgoal 2
├─ Topic Call: Execute Subgoal 3
└─ Topic Call: Compose Response
```

**Code Pattern (Agent Framework):**
```python
async def handle_escalation_with_planning(client, order_id):
    agent = Agent(
        client=client,
        instructions=(
            "For order escalations:\n"
            "1. Decompose into: Verify → CheckPolicy → Decide → Compose\n"
            "2. Show the plan before executing\n"
            "3. Report status of each step"
        ),
        tools=[verify_order_tool, check_policy_tool, decide_tool]
    )
    plan = await agent.run(f"Handle escalation for order {order_id}")
    return plan
```

**Demo Value:**
- Shows visible decision boundaries separate from execution
- Shows how planning can reduce errors compared with a single opaque action
- Planning cascade: complex → sub-steps → measurable outcomes

---

### o15: Beliefs (Beat 14)

**Industry Concept:** World state representation, context model, persistent fact store, knowledge base

**What it demonstrates:**
- Agents maintain explicit beliefs about customers, policies, and environment
- Belief updates cascade through future decisions
- Facts are queryable and auditable (not hidden in weights)

**Microsoft Stack Integration:**

| Component | Role | Example |
|-----------|------|---------|
| **Agent Framework** | Core integration | `Agent.context_providers` load beliefs before reasoning |
| **Azure Table Storage** | Persistent fact store | Row key: `customer#Contoso`, columns: `tier`, `approval_rate`, `disputes` |
| **Foundry Memory Service** | Semantic retrieval | Query: "What is Contoso's customer tier?" → retrieves from memory |
| **Copilot Studio** | Belief UI & updates | Power Automate action: "Update Customer Belief" |
| **Power Query** | Belief analytics | Track how belief updates change decision thresholds over time |
| **Application Insights** | Belief audit log | Custom telemetry: `belief.updated` events with before/after values |

**Copilot Studio Implementation:**
```
Topic: Refund Decision
├─ Retrieve Customer Beliefs
│  ├─ Call Power Automate: Get Beliefs from Table Storage
│  └─ Log: "Loaded Contoso tier=standard-trusted, approval_rate=0.75"
├─ Decision Engine
│  ├─ IF approval_rate > 0.70 AND days_late >= 4: auto-approve
│  └─ ELSE: require-review
├─ Post-Interaction Learning
│  └─ Call Power Automate: Update Beliefs
│     ├─ Update approval_rate: 0.75 → 0.78 (based on satisfaction)
│     └─ Log: "Updated Contoso for next interaction"
└─ Return Response
```

**Code Pattern (Agent Framework with Foundry Memory):**
```python
from azure.ai.projects.models import BlobStorageConnection
from azure.ai.projects.aio import AIProjectClient

async def handle_with_beliefs(client, customer_id, order_id):
    # Load world state
    beliefs = await foundry_client.memory.retrieve(f"customer#{customer_id}")
    
    # Build agent with belief context
    agent = Agent(
        client=client,
        instructions=f"""
        Current beliefs about {customer_id}:
        - Tier: {beliefs.tier}
        - Historical approval rate: {beliefs.approval_rate}
        
        Use these beliefs to inform decision thresholds.
        After deciding, explain how beliefs shaped the outcome.
        """,
        context_providers=[beliefs_provider],
        tools=[update_beliefs_tool]
    )
    
    response = await agent.run(f"Handle order {order_id} for {customer_id}")
    
    # Persist belief updates
    await foundry_client.memory.save(f"customer#{customer_id}", response.updated_beliefs)
    
    return response
```

**Demo Value:**
- Shows agent learning across sessions (not just within chat)
- Proves explicit beliefs > implicit weights (interpretable, auditable)
- Demonstrates belief cascade: one fact update → multiple downstream impacts

---

## Complete Organ Stack Mapping

### Core Organs (Brain)
| Organ | Beat | Microsoft Stack |
|-------|------|-----------------|
| Instructions | 0 | Agent Framework system prompt + Copilot Studio topic instructions |
| Model | 0 | Foundry model deployment + LLM routing (gpt-4o, Phi-3, Mixtral) |
| **Planning** | **13** | **Structured prompting + Power Automate workflow orchestration** |

### Perception Organs (Eyes/Ears)
| Organ | Beat | Microsoft Stack |
|-------|------|-----------------|
| Knowledge | 1 | Azure AI Search (vector/semantic search) + Azure Blob Storage (docs) |
| Tools | 2 | Agent Framework function calling + Copilot Studio Power Automate actions |
| Memory | 4 | Foundry Memory service + Azure Cosmos DB (durable key-value) |
| Guardrails | 5 | Azure AI Content Safety + Foundry guardrails middleware |
| **Beliefs** | **14** | **Azure Table Storage + Foundry Memory + Copilot Studio facts** |

### Action Organs (Arms/Legs)
| Organ | Beat | Microsoft Stack |
|-------|------|-----------------|
| Tools | 2 | Power Automate connectors (365, SQL, SAP, ServiceNow, etc.) |
| Identity | 7 | Azure Managed Identity + RBAC role assignments |

### Meta Organs (Heart/Nervous System)
| Organ | Beat | Microsoft Stack |
|-------|------|-----------------|
| Orchestration | 6 | Power Automate workflow editor + Copilot Studio topic routing |
| Observability | 8 | Application Insights + OpenTelemetry SDK + AI Services diagnostics |
| Metabolism | 9 | Foundry token tracking + Budget middleware + Quota enforcement |
| Spine | 10 | Durable Functions (checkpoints) + Table Storage (state) |
| Reflex Arc | 12 | Event Grid triggers + Azure Functions + Copilot Studio autonomous agents |
| **Planning** | **13** | **Workflow sequencing + sub-step telemetry** |
| **Beliefs** | **14** | **Persistent fact store + belief query layer** |

### Learning Organs (Improvement)
| Organ | Beat | Microsoft Stack |
|-------|------|-----------------|
| Skills | 11 | Copilot Studio plugin marketplace + custom MCP tools |
| Learning | 11 | Agent Optimizer + fine-tuning pipeline (SFT/DPO/RFT) |

---

## Recommended Demo Sequence with Planning & Beliefs

```
Beat 0:  Instructions        ← Safe start
         + Model             (Agent Framework LLM core)

Beat 1:  Knowledge           (AI Search grounding)
Beat 2:  Tools               (Power Automate connectors)
Beat 3:  Tools (add-tool)    (Config-driven toolbox)
Beat 4:  Memory              (Durable session store)
Beat 5:  Guardrails          (Content Safety + safety middleware)
Beat 6:  Orchestration       (Power Automate workflow)
Beat 7:  Identity            (Managed Identity RBAC)
Beat 8:  Observability       (App Insights + OpenTelemetry)
Beat 9:  Metabolism          (Token budget enforcement)
Beat 10: Spine               (Durable Functions checkpoints)
Beat 11: Skills + Learning   (Agent Optimizer + MCP)
Beat 12: Reflex Arc          ← Autonomous event wake (filesystem trigger)
Beat 13: Planning            ← NEW: Goal decomposition post-wake
         (now with visible plan before execution)
Beat 14: Beliefs             ← NEW: World state cascade & learning
         (now showing belief→decision impact for next interaction)
```

---

## Key Differentiators: Planning & Beliefs vs. Existing Organs

| Capability | Without Planning | With Planning |
|-----------|-----------------|---------------|
| Decision transparency | Black box: "approve" | White box: "approve because [4 sub-steps all passed]" |
| Error recovery | Fail entire call | Fail sub-step 2, retry, skip step 3 if independent |
| Audit trail | Single response entry | Tree of sub-goal entries with timestamps |
| Stakeholder confidence | "Trust the model" | "See the roadmap; each checkpoint is reviewable" |

| Capability | Without Beliefs | With Beliefs |
|-----------|-----------------|-------------|
| Cross-session learning | Repeated work | Learn once, apply always |
| Interpretability | "Model decided X" | "Customer tier is Y, so threshold is Z" |
| Fact freshness | Stale (re-embed docs) | Fresh (query live fact store) |
| Audit compliance | Implicit reasoning | Explicit belief log with change history |

---

## Implementation Checklist for Production

- [ ] **Planning**: Implement goal_decomposer tool returning JSON with dependencies
- [ ] **Planning**: Add span telemetry per sub-goal in observability middleware
- [ ] **Beliefs**: Provision Azure Table Storage or Cosmos DB for belief facts
- [ ] **Beliefs**: Create Foundry Memory service integration for semantic retrieval
- [ ] **Beliefs**: Add belief update tool that logs to Application Insights
- [ ] **Integration**: Wire Planning output as input to Beliefs context providers
- [ ] **Observability**: Create Application Insights custom metric: "beliefs_updated_count" and "belief_impact_on_decision"
- [ ] **Testing**: Verify belief updates persist across process restarts (table storage durability)
- [ ] **Deployment**: Package as azd modules with IaC (Bicep/Terraform)
