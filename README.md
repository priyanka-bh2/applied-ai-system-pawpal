# PawPal+ 🐾 — Breed-Aware AI Pet Care Planner

PawPal+ is an applied AI system that generates personalized, breed-aware daily
care plans for pets using retrieval-augmented generation (RAG), a LangGraph
agent, and a Groq-hosted LLM — with built-in validation and transparent
reasoning.

---

## Original Project (Module 2 — PawPal)

The original **PawPal** was a Streamlit-based pet care task tracker. Owners could
register their pets and manually schedule recurring care tasks (walks, feeding,
grooming) with times, priorities, and due dates, backed by simple
`Owner` / `Pet` / `Task` / `Scheduler` data models. It organized care that the
owner already knew how to give — but it offered no guidance on *what* good care
for a given pet should actually look like. That original tracker still lives in
this repo (`app.py`, `main.py`, `pawpal_system.py`).

---

## PawPal+ Overview (Applied AI System)

**What it does.** PawPal+ takes a pet profile (name, breed, age, weight, health
conditions) plus a free-text request and produces a structured daily care plan
covering feeding, hydration, exercise, grooming, health monitoring, and mental
stimulation. It retrieves breed-specific guidelines from a knowledge base, drafts
a plan with an LLM, validates that the plan covers essential needs, assigns a
confidence score, and finally explains *why* each recommendation matters —
citing the retrieved guidelines.

**Why it matters.** New pet owners often don't know how much exercise a Siberian
Husky needs, how often a Poodle should be groomed, or which conditions a breed is
prone to. PawPal+ turns that scattered, breed-specific knowledge into a concrete
daily routine, and — crucially — shows its reasoning and flags gaps rather than
producing an opaque, unverifiable answer. It structures care with transparent,
citable justification.

---

## Architecture Overview

PawPal+ is built as a **LangGraph agent** wrapping a **RAG pipeline**. At startup,
the `CareGuidelineRetriever` loads breed guidelines from
`data/knowledge_base/breed_guidelines.json`, embeds them locally with
**HuggingFace `sentence-transformers/all-MiniLM-L6-v2`**, and indexes the vectors
in a **FAISS** store for fast similarity search. Each request flows through a
four-node LangGraph workflow:

1. **retrieve** — pull the most relevant breed/age guidelines from FAISS.
2. **plan** — generate a structured daily care plan with the **Groq LLM**
   (`llama-3.3-70b-versatile`), grounded in the retrieved context.
3. **validate** — check that the plan covers feeding, exercise, and water, flag a
   vet consultation for pets with health conditions, and compute a confidence
   score with a list of any issues found.
4. **explain** — describe why each task matters for this specific breed and age,
   citing the retrieved guidelines.

The full system diagram is in [`diagrams/architecture.mmd`](diagrams/architecture.mmd)
(Mermaid `flowchart TD`). Data flow: **User → Agent → Retriever → FAISS → LLM plan
→ Validator → Explanation → User.**

---

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/priyanka-bh2/applied-ai-system-pawpal.git
   cd applied-ai-system-pawpal
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   > The first install downloads the `all-MiniLM-L6-v2` embedding model and its
   > PyTorch dependency (a few hundred MB); subsequent runs use the local cache.

3. **Configure your API key.** Copy the example env file and add a **free** Groq
   API key from [console.groq.com/keys](https://console.groq.com/keys):
   ```bash
   cp .env.example .env
   # then edit .env:
   # GROQ_API_KEY=gsk_your_key_here
   ```

4. **Run it.**
   - **AI care planner (PawPal+ demo, end-to-end):**
     ```bash
     python test_quick.py
     ```
   - **Original task tracker (Module 2 Streamlit UI):**
     ```bash
     streamlit run app.py
     ```

   `test_quick.py` is the entry point that exercises the RAG + LangGraph + Groq
   agent; `app.py` / `main.py` run the original manual task tracker.

---

## Sample Interactions

### Example 1 — Buddy (Golden Retriever, 3y, 30 kg, no health conditions)

**Input:**
```python
pet_profile = {
    "name": "Buddy",
    "breed": "Golden Retriever",
    "age": 3,
    "weight_kg": 30,
    "health_conditions": [],
}
user_request = "Create a daily care plan"
```

**Output (abridged):**
```text
📋 Validated Care Plan — Buddy, 3-year-old Golden Retriever

1. Feeding Schedule
   - Breakfast: 1.5 cups high-quality dog food @ 7:00 AM
   - Dinner:    1.5 cups high-quality dog food @ 6:00 PM
2. Exercise (60–90 min/day)
   - Morning walk/run 30 min, afternoon fetch 30 min, evening walk 30 min
3. Grooming
   - Brush 2–3x/week (double coat); bathe monthly; weekly ear cleaning
4. Health Monitoring
   - Bi-annual vet checkups; watch for hip/elbow dysplasia signs
5. Mental Stimulation
   - Training 15–20 min 3x/week; puzzle toys; weekly dog-park socialization

🎯 Confidence: ██████████████████░░  90%
⚠️ Issues:
   ❌ Missing water recommendation   →   confidence reduced to 0.90

💡 Explanation
   Feeding portions are controlled because Golden Retrievers are prone to
   obesity ("Prone to obesity - measure portions"). The 60–90 min exercise
   target follows the breed's high-energy requirement, and bi-annual vet
   checkups address the breed's risk of hip dysplasia and heart conditions.
```

This is a real run captured during testing — the validator correctly detected
that the draft plan never mentioned water and lowered the confidence score
accordingly. (The prompt has since been updated to always include a hydration
section; see *Testing & Reliability*.)

### Example 2 — Max (senior Labrador Retriever, 10y, 32 kg, arthritis)

**Input:**
```python
pet_profile = {
    "name": "Max",
    "breed": "Labrador Retriever",
    "age": 10,
    "weight_kg": 32,
    "health_conditions": ["arthritis"],
}
user_request = "Create a gentle daily care plan suitable for a senior dog"
```

**Output (abridged):**
```text
📋 Validated Care Plan — Max, 10-year-old Labrador Retriever (arthritis)

1. Feeding Schedule
   - 2 measured meals; senior/joint-support formula; avoid weight gain
2. Hydration
   - Fresh water available at all times; refresh 2–3x daily
3. Exercise (LOW IMPACT — modified for arthritis)
   - Two 15–20 min flat, gentle leash walks instead of runs
   - Swimming encouraged for joint-friendly movement; no jumping/stairs
4. Grooming
   - Regular brushing; check joints/paws while grooming
5. Health Monitoring
   - Vet consultation for arthritis management (pain relief, joint supplements)
   - Monitor mobility, stiffness after rest, and appetite daily

🎯 Confidence: ████████████████████  100%
⚠️ Issues:
   ✅ No issues found!

💡 Explanation
   Exercise is reduced to low-impact walks and swimming because high-intensity
   activity aggravates arthritis in a senior dog; the plan flags a vet
   consultation for pain management, which the validator requires whenever a
   health condition is present.
```

*(Example 2 is representative output illustrating how the agent adapts to age and
health conditions — reduced-impact exercise plus a vet reminder — and passes
validation at full confidence.)*

---

## Design Decisions & Trade-offs

- **Local HuggingFace embeddings over a hosted embedding API.** Embeddings run
  entirely on-device with `all-MiniLM-L6-v2`. This makes retrieval **free,
  offline-capable, and deterministic** — the same guideline text always produces
  the same vectors — with no dependency on an external embedding service or its
  rate limits and billing.

- **Groq free tier over paid Gemini/Claude.** Only the plan-generation and
  explanation steps call a hosted LLM, and Groq's free tier serves a capable
  open model (`llama-3.3-70b-versatile`) at high speed with no cost. This keeps
  the whole system runnable end-to-end for **$0**, which matters for a course
  project and for reproducibility by graders. (The project was migrated across
  providers — Gemini → Claude → Groq — which validated that the RAG and
  LangGraph layers are cleanly decoupled from the model provider.)

- **LangGraph for multi-step reasoning.** Modeling the workflow as explicit
  nodes (retrieve → plan → validate → explain) makes each stage **inspectable and
  independently debuggable**, and makes the reliability layer (validation +
  confidence) a first-class node rather than an afterthought buried in a single
  prompt.

- **Trade-offs & limitations.** The knowledge base covers **10 breeds** and
  reflects **US-centric** general care assumptions. Recommendations are
  informational and **not a substitute for professional veterinary advice** —
  the system is designed to *surface* care structure and flag gaps, not to
  diagnose or treat.

---

## Testing & Reliability Summary

Reliability is enforced by the **validation node**, which independently checks
each generated plan for essential elements — **feeding, exercise, and water** —
requires a **vet consultation** to be mentioned whenever the pet has a health
condition, and computes a **confidence score** (starting at 1.0 and deducting for
each missing element or missing context) alongside a concrete list of issues.

**A real finding during testing:** in the Buddy run above, the LLM's initial plan
thoroughly covered feeding and exercise but **never mentioned water**. The
validator caught the omission, added `"Missing water recommendation"` to the
issues list, and **reduced the confidence score from 1.0 to 0.9** — a concrete
demonstration of the guardrail working rather than silently passing an incomplete
plan. That finding drove a fix: the plan-generation prompt now explicitly
instructs the model to always include a hydration/water recommendation.

Overall, `test_quick.py` exercises the full pipeline end-to-end and confirms the
system **behaves as expected and transparently surfaces missing elements** rather
than presenting incomplete plans as complete. The combination of grounded
retrieval, explicit validation, confidence scoring, and cited explanations makes
the output both useful and auditable.
