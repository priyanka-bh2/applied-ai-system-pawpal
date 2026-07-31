# Model Card — PawPal+ 🐾

**System:** PawPal+, a breed-aware AI pet care planner
**Stack:** RAG (HuggingFace `all-MiniLM-L6-v2` + FAISS) · LangGraph agent · Groq LLM (`llama-3.3-70b-versatile`)
**Purpose:** Generate structured, breed-aware daily pet care plans with validation, confidence scoring, and cited reasoning.

---

## AI Collaboration

I used AI tools throughout the project as collaborators rather than autopilots.

- **Architecture design.** I used conversational LLMs (Gemini, then Claude, then
  Groq-hosted models) to think through the system shape — how to combine a RAG
  retriever with a multi-step agent, and how to separate plan generation from
  validation and explanation. The four-node design (retrieve → plan → validate →
  explain) came out of that back-and-forth.
- **Writing code.** AI assistance (including Copilot-style inline completion) sped
  up boilerplate: the LangGraph node wiring, the FAISS retriever setup, prompt
  templates, and the formatted test harness (`test_quick.py`).
- **Debugging.** AI was most valuable when interpreting real error output — a
  deprecated embedding model returning `404 NOT_FOUND`, a missing `faiss` module,
  a macOS OpenMP conflict, and provider authentication/quota errors. I fed the
  actual tracebacks in and used the suggestions as leads, verifying each fix
  against a real run rather than trusting it blindly.

**Guardrail on myself:** every AI-suggested change was validated by running the
system end-to-end. Several confident-sounding suggestions (e.g., specific model
IDs) were wrong and only surfaced as errors when executed — which is exactly why
I treated "it runs and produces correct output" as the acceptance test.

---

## Helpful AI Suggestion

**Suggestion:** Model the agent as an explicit **LangGraph** state machine and
run **local HuggingFace embeddings + a free hosted LLM** instead of a fully paid
API pipeline.

**Why it helped:**

- **Reliability.** Making validation and confidence scoring a *first-class node*
  rather than a buried prompt instruction meant the system could independently
  check its own output (feeding / exercise / water coverage, vet reminders for
  health conditions) and surface omissions instead of silently passing incomplete
  plans. The workflow became inspectable — I could reason about each stage in
  isolation.
- **Development speed.** Local embeddings are free, offline, and deterministic, so
  I could iterate on retrieval without worrying about API keys, rate limits, or
  cost per run. Only the plan/explanation steps hit a hosted model, which
  shortened the debug loop dramatically. The modular graph also made it trivial to
  swap the LLM provider without touching the RAG layer.

This suggestion improved both the *trustworthiness* of the output and the *speed*
at which I could develop and test it.

---

## Flawed AI Suggestion

**Suggestion:** Build the plan-generation step on a paid frontier API — first
Google Gemini, then Anthropic Claude.

**Why it was flawed:**

- The **Gemini** path hit `RESOURCE_EXHAUSTED` (free-tier quota of 0 for content
  generation on the project) and deprecated embedding-model IDs.
- The **Claude** path authenticated correctly but returned
  *"Your credit balance is too low to access the Anthropic API"* — a hard billing
  wall.

Both were technically reasonable suggestions, but **not sustainable** for a
course project that graders need to reproduce for free: the code was correct, yet
the system could not complete a single end-to-end run without a funded account.

**Why migrating to Groq was better:** Groq's free tier serves a capable open model
(`llama-3.3-70b-versatile`) with no credit card, at high speed. After the
migration, `test_quick.py` ran fully end-to-end and produced a complete, validated
care plan at **$0**. The migration also confirmed the architecture was cleanly
decoupled — swapping providers touched only `src/agent.py`, `.env`, and
`requirements.txt`, never the RAG or workflow logic.

**Lesson:** "the code is correct" is not the same as "the system works." Provider
constraints (quota, billing) are part of system design, and choosing a
reproducible, free provider was the right call for this context.

---

## Biases & Limitations

- **Limited breed coverage.** The knowledge base (`breed_guidelines.json`)
  contains only **10 popular breeds** (Golden Retriever, Labrador, German
  Shepherd, French Bulldog, Siberian Husky, Poodle, Beagle, Yorkshire Terrier,
  Boxer, Australian Shepherd). Mixed breeds and the many breeds outside this list
  fall back to generic guidance, which lowers plan specificity and confidence.
- **US-centric assumptions.** Care recommendations reflect general US pet-care
  norms (feeding products, vet-visit cadence, climate expectations) and may not
  transfer to other regions or care philosophies.
- **Not veterinary advice.** PawPal+ is an informational planning aid, **not a
  substitute for professional veterinary care**. For any health concern it should
  defer to a licensed veterinarian, and the validator deliberately requires a vet
  consultation to be mentioned whenever a health condition is present.

---

## System Limitations

- **No image-based breed detection.** Breed must be entered manually as text;
  there is no vision component to identify a breed from a photo.
- **No real-time context.** The system does not integrate weather, location, or
  seasonal data, so it cannot adjust exercise recommendations for heat, cold, or
  local conditions.
- **Heuristic confidence scores.** The confidence value is a rule-based deduction
  (start at 1.0; subtract for missing required elements or missing retrieved
  context), **not a calibrated probability**. It signals plan *completeness*, not
  the statistical likelihood of correctness.
- **Single knowledge source.** Retrieval draws only from the curated JSON file; it
  cannot consult external or updated veterinary literature at runtime.

---

## Testing Results

- **End-to-end test.** `test_quick.py` exercises the entire pipeline — local
  embedding + FAISS retrieval → Groq plan generation → validation → explanation —
  for a sample pet, and prints the plan, confidence score, issues, and
  explanation.
- **A concrete validator catch.** In a real run for *Buddy* (Golden Retriever, 3y),
  the LLM's plan covered feeding and exercise thoroughly but **omitted any water
  recommendation**. The validation node detected the gap, added
  `"Missing water recommendation"` to the issues list, and **reduced confidence
  from 1.0 to 0.9** rather than passing the plan as complete. This directly drove a
  fix: the generation prompt now explicitly requires a hydration section.
- **Overall behavior.** Across test cases, most generated plans are complete and
  well-grounded in the retrieved breed guidelines; when an element is missing, the
  validator reliably flags it and the confidence score adjusts downward. The
  system fails *loudly and transparently* rather than silently, which is the
  intended behavior.

---

## Responsible AI Reflection

**What I learned about building reliable AI systems:**

- **Guardrails matter more than raw model quality.** The single most valuable
  component was the validation node. An LLM will confidently produce a plausible
  but incomplete plan; an independent checker that verifies essential elements and
  scores completeness is what makes the output trustworthy.
- **RAG grounds and constrains generation.** Retrieving breed-specific guidelines
  before generating kept plans anchored to real, citable information and reduced
  free-form hallucination.
- **Transparency is a feature, not decoration.** The explanation node and the
  cited reasoning let a user (or grader) *audit* why each recommendation was made,
  which is essential for a system giving care advice.

**How I would improve it further:**

- **Broader, structured knowledge base** — more breeds, mixed-breed handling, and
  regionally-aware guidance to reduce US-centric bias.
- **Human-in-the-loop review** — allow a user or expert to approve, edit, or
  reject a plan before it's finalized, especially for pets with health conditions.
- **Better evaluation** — replace the heuristic confidence score with calibrated
  metrics, add a labeled test suite that measures plan completeness and factual
  grounding against expert references, and track validator catch-rates over time.
- **Richer context** — optional image-based breed detection and weather/seasonal
  awareness to tailor exercise and care to real conditions.

The core takeaway: a reliable applied-AI system is less about the biggest model
and more about the scaffolding around it — grounded retrieval, explicit
validation, transparent reasoning, and honest limitations.
