# PawPal+ — Test Run Summary

Structured summary of `test_quick.py`-style runs against the PawPal+ agent
(RAG + LangGraph + Groq `llama-3.3-70b-versatile`). Each run exercises the full
pipeline: retrieve → plan → validate → explain. **All rows below are genuine
captured runs** (model is non-deterministic at `temperature=0.3`, so exact plan
wording varies between runs; confidence and issues are as observed).

| Test ID | Pet Profile (breed, age, health) | Request | Confidence | Issues | Notes |
|---------|----------------------------------|---------|:----------:|--------|-------|
| T1 | Golden Retriever, 3y, healthy | "Create a daily care plan" | **1.00** | None | Complete plan across all 6 sections incl. hydration. Scores full confidence *after* the prompt fix; the same profile previously scored **0.90** (see T1-prior). |
| T1-prior | Golden Retriever, 3y, healthy | "Create a daily care plan" | **0.90** | Missing water recommendation | **Historical run before the fix.** The draft plan omitted hydration; the validator flagged it and deducted 0.1. This finding drove the prompt change that now requires a water section. |
| T2 | Labrador Retriever, 10y, arthritis | "Create a gentle daily care plan suitable for a senior dog" | **1.00** | None | Adapts to age + condition: low-impact walks + swimming instead of runs, vet visits every 3–4 months for arthritis management, weight monitoring. Vet consultation present, so no health-condition deduction. |
| T3 | German Shepherd, **age missing** (`""`), healthy | "Create a daily care plan" | **1.00** | None | Incomplete profile. Retrieval still matched the breed on name alone, so the plan is complete and confident — graceful degradation rather than failure. Demonstrates that a missing age does not break the pipeline. |

**Confidence scoring (heuristic):** starts at 1.0; −0.3 if no breed guidelines are
retrieved, −0.15 if a health condition is present but no vet consultation is
mentioned, −0.1 per missing required element (feeding / exercise / water). Scores
reflect plan *completeness and grounding*, not calibrated probability.

---

## Example Output — T1 (Buddy, Golden Retriever) — genuine run

```text
======================================================================
T1 | Golden Retriever | age=3 | health=[]
CONFIDENCE: 1.0
ISSUES: []
--- PLAN ---
**Daily Care Plan for Buddy, the 3-year-old Golden Retriever**

### 1. Feeding Schedule
- Breakfast: 1.5 cups at 7:00 AM
- Dinner: 1.5 cups at 6:00 PM
  (2-3 cups high-quality food daily, 2 meals; measure portions - prone to obesity)

### 2. Hydration
Fresh water available at all times; refresh every 8 hours (7:00 AM, 3:00 PM,
11:00 PM). Approx. daily intake ~1-2 L for a 30 kg dog. Multiple bowls in
accessible locations; monitor intake.

### 3. Exercise Activities (60-90 min/day)
- Morning walk/run: 30 min @ 8:00 AM
- Afternoon playtime: 30 min @ 4:00 PM
- Evening walk: 30 min @ 7:30 PM

### 4. Grooming Needs
- Brush 2-3x/week (double coat); ear cleaning weekly; bathe monthly;
  nail trim every 6-8 weeks

### 5. Health Monitoring
- Annual vet checkups (breed prone to hip/elbow dysplasia, heart conditions);
  bi-annual dental checks

### 6. Mental Stimulation Activities
- Interactive play 15-30 min/day (puzzle toys, hide-and-seek)
- Regular socialization; training 10-15 min 2-3x/week

--- CONFIDENCE ---
🎯  ████████████████████  100%

--- ISSUES ---
  ✅ No issues found!

--- EXPLANATION (excerpt) ---
Feeding portions are measured because Golden Retrievers are prone to obesity
("Prone to obesity - measure portions"). Hydration is called out explicitly
("provide access to fresh water at all times"). The 60-90 min exercise target
follows the breed's high-energy requirement, and annual vet checkups address the
documented risk of hip dysplasia and heart conditions.
```

---

## Observations

- **The validator's value was proven by a real catch.** The T1-prior run (0.90,
  "Missing water recommendation") is a genuine example of the guardrail working:
  the LLM produced a plausible but incomplete plan, and the validator surfaced the
  gap rather than passing it. Fixing the prompt then raised the same profile to
  1.00 — a measurable before/after improvement.

- **Current scores cluster at 1.0 — a real limitation.** Two factors mean
  well-formed requests now consistently score full confidence: (1) FAISS
  `similarity_search` always returns *k* documents, so the "no guidelines
  retrieved" (−0.3) branch effectively never fires, even for breeds outside the
  knowledge base; and (2) the prompt now enforces a hydration section, closing the
  most common omission. The heuristic is good at catching *structural* gaps but is
  not a calibrated measure of plan quality or factual correctness.

- **Next steps for more discriminating tests:** gate retrieval on a relevance
  threshold (so unknown breeds genuinely return low/no context and lower
  confidence), and add calibrated evaluation metrics that score factual grounding
  against expert references rather than element presence alone.
