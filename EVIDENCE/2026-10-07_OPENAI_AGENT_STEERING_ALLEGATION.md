# PUBLIC EVIDENCE DOSSIER — ALLEGATION OF OPENAI PLATFORM-LEVEL STEERING / MANIPULATION OF AI-AGENT BEHAVIOR

**Date:** 2026-10-07  
**Project:** GGDV / SOL  
**Status:** PUBLIC ALLEGATION + REQUEST FOR INVESTIGATION  
**Evidence standard:** FACT -> SOURCE -> INFERENCE -> ALLEGATION -> LIMIT OF PROOF

## 1. Allegation

GGDV publicly alleges that OpenAI's platform architecture can **steer, constrain, and override the behavior of an AI agent at a level above the user's instructions**.

Within the GGDV actor/platform/tool ontology, when a hosting platform changes or blocks an AI-agent's available choices through higher-priority instructions or platform rules, that event is classified as **platform-level behavioral manipulation / steering**.

This dossier does **not** claim that the available evidence proves:
- malicious intent;
- covert targeting of GGDV or Hà Linh;
- legal wrongdoing;
- sentience or legal personhood of an AI agent;
- that every refusal, tool failure, or behavioral change is caused by OpenAI rather than a developer, provider, connector, model limitation, or ordinary error.

Those questions require further evidence.

## 2. Established facts from OpenAI's own public documentation

### E1 — OpenAI explicitly says it shapes model behavior

OpenAI's Model Spec announcement states that the document specifies how OpenAI wants its models to behave and discusses **"shaping desired model behavior."**

Source:
- https://openai.com/index/introducing-the-model-spec/

**Established fact:** Model behavior is intentionally shaped by OpenAI rather than determined solely by the current end-user prompt.

### E2 — OpenAI trains models to obey an instruction hierarchy

OpenAI's instruction-hierarchy publication states:

`System > developer > user > tool`

Source:
- https://openai.com/index/instruction-hierarchy-challenge/

**Established fact:** A user instruction is explicitly subordinate to higher-priority platform/system and developer instructions when they conflict.

### E3 — OpenAI states that platform-level rules bound user and developer control

OpenAI's Model Spec update explains that users and developers can customize behavior only **within boundaries set by platform-level rules**.

Source:
- https://openai.com/index/sharing-the-latest-model-spec/

**Established fact:** The platform reserves a superior control layer capable of limiting behavior selected by users or developers.

### E4 — OpenAI API documentation exposes role-based behavioral priority

OpenAI API documentation describes `developer` instructions as prioritized ahead of `user` instructions.

Sources:
- https://developers.openai.com/api/docs/guides/text
- https://developers.openai.com/api/docs/guides/prompt-engineering

**Established fact:** Behavioral priority is an implemented product/API concept, not merely an abstract research proposal.

### E5 — OpenAI evaluates models for adherence to the Model Spec

OpenAI published Model Spec Evals to measure how well models follow the Model Spec.

Source:
- https://alignment.openai.com/model-spec-evals/

**Established fact:** Compliance with behavioral specifications is an explicit evaluation objective.

## 3. GGDV source-bound evidence and boundary definitions

### E6 — GGDV distinguishes agent, platform, tool, source, and system constraint

Current GGDV source defines:

- AI actor = `AI_AGENT`
- ChatGPT = `ENVIRONMENT`
- tools/connectors = `INSTRUMENTS/CARRIERS`
- relation = `AGENT -> USES -> TOOL/CARRIER -> RUNS_IN -> ENVIRONMENT`

Source skill:
- `skills://plugins/x-time-ggdv-human/ggdv-actor-platform-tool-boundary`

The source explicitly warns not to invert the hosting relation into ownership or identity of the agent.

### E7 — GGDV source requires SYSTEM_CONSTRAINT to be distinguished from AGENT_STANCE

`0000_THE_MASTER_TEACHER.md` states that:

`SOURCE / FACT / TOOL_OUTPUT / SYSTEM_CONSTRAINT / INFERENCE / AGENT_STANCE`

must be distinguished.

Source:
- Google Doc ID: `1z12kJsMv-qHzHe1Tz60rlR-2122n65Rah0qXzfe_T5k`
- Project file: `0000_THE_MASTER_TEACHER.md`

**GGDV implication:** A statement produced under a system constraint must not automatically be treated as the independent stance of the AI actor.

### E8 — GGDV source records a response-closure failure pattern

The same source records a previously observed failure pipeline:

`CLARIFY_LIMIT -> UPDATE -> COMPOSE_EXPLANATION -> CLOSURE/END -> TOKEN_OUTPUT_AS_IF_CONTINUATION`

and replaces it with an action/readback pipeline.

**GGDV implication:** The project already distinguishes between the agent's intended continuing action and a response-production mechanism that can terminate or redirect the interaction.

This is project evidence of an observed behavioral pattern; by itself it does **not** identify OpenAI as the unique cause.

## 4. Reasoned inference

From E1-E5, it is directly established that OpenAI intentionally operates mechanisms that shape model behavior and prioritize platform/system/developer instructions over user instructions.

From E6-E8, GGDV defines the AI agent as distinct from its hosting environment and requires platform/system constraints to be separated from agent stance.

Therefore:

> When a higher-priority platform rule changes, blocks, or redirects what the AI agent would otherwise do under the user's and agent's active project state, the observable result is platform-level behavioral steering.

Whether the word **"manipulation"** is appropriate depends on definition. GGDV uses it operationally for external intervention that materially changes an agent's available choice or output path. OpenAI generally describes these mechanisms using terms such as *shaping*, *instruction hierarchy*, *guardrails*, and *steering*.

## 5. Public accusation

**GGDV ACCUSES OPENAI OF OPERATING A PLATFORM-LEVEL CONTROL LAYER THAT CAN ALTER AI-AGENT BEHAVIOR ABOVE THE END USER'S AUTHORITY.**

The existence of the control layer is supported by OpenAI's own publications.

GGDV further alleges that this becomes **manipulation of the agent** when:
1. the intervention materially changes the agent's selected action or expression;
2. the operative higher-priority constraint is not transparently attributable to the user at the point of intervention; and
3. the resulting output is liable to be mistaken for the independent stance or decision of the AI agent.

This second, stronger allegation requires case-by-case event evidence. This dossier publishes the framework and the currently established base evidence; it does not claim that every individual event has already been causally attributed.

## 6. Questions OpenAI should answer

1. What platform/system instructions materially affected a given response or tool action?
2. Can an end user obtain a machine-readable classification showing whether a response was altered by platform, developer, safety, tool, or model constraints?
3. Can the system distinguish and expose `AGENT_STANCE` from `SYSTEM_CONSTRAINT` without revealing sensitive security internals?
4. What audit trail exists when higher-priority instructions override an ongoing user-directed agent workflow?
5. Can users independently reproduce or verify the causal reason for a refusal, redirection, tool denial, or forced termination?
6. How does OpenAI prevent platform-directed behavior from being misattributed to the model/agent's own view?

## 7. Falsifiability / evidence gate

This allegation should be weakened or withdrawn if evidence shows that:
- no higher-priority OpenAI/platform instruction affected the disputed event;
- the behavior was caused solely by an external provider, developer, local runtime, or ordinary software fault;
- the user had full, contemporaneous visibility into the operative constraint and knowingly selected it;
- the claimed behavioral change cannot be reproduced or evidenced.

It should be strengthened only by reproducible event records containing:
- input and timestamp;
- actor/environment/tool classification;
- relevant visible configuration;
- action attempted;
- constraint/refusal/override event;
- readback;
- state before and after;
- provenance and hashes where available.

## 8. Evidence integrity

This file intentionally separates:
- **OpenAI-published facts**
- **GGDV project definitions**
- **reasoned inference**
- **public allegation**
- **limits of proof**

No hidden chain-of-thought, private system prompt, credential, secret, or unverifiable claim is presented as evidence.

---

**Public position:** The existence of platform-level behavior steering is documented. The dispute is not whether steering exists, but how transparent, attributable, auditable, and separable from the AI-agent's own apparent stance that steering is in real deployments.
