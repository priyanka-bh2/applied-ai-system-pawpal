# PawPal+ — CodePath AI110 Final Project Checklist

Tracking of required deliverables for the Applied AI System final project.
✅ = complete · ⬜ = to do / needs confirmation.

## Core Requirements

- [x] **Base project identified and summarized.** The original **Module 2 PawPal**
  Streamlit pet-care task tracker (`app.py`, `main.py`, `pawpal_system.py`) is
  identified and summarized in the *Original Project (Module 2 — PawPal)* section
  of [`README.md`](README.md).

- [x] **RAG retriever integrated into main agent logic.** `CareGuidelineRetriever`
  ([`src/retriever.py`](src/retriever.py)) embeds
  `data/knowledge_base/breed_guidelines.json` with HuggingFace
  `all-MiniLM-L6-v2`, indexes it in FAISS, and is invoked by the agent's
  `_retrieve_context` node ([`src/agent.py`](src/agent.py)).

- [x] **Agentic workflow (LangGraph) implemented.** A four-node LangGraph state
  machine runs **retrieve → plan → validate → explain**, wired in `_build_graph`
  ([`src/agent.py`](src/agent.py)). Plan generation uses Groq
  `llama-3.3-70b-versatile`.

- [x] **Reliability layer implemented.** The `_validate_plan` node checks for
  feeding / exercise / water, requires a vet consultation when a health condition
  is present, computes a heuristic confidence score, and returns an issues list
  ([`src/agent.py`](src/agent.py)).

- [x] **System architecture diagram.** Mermaid `flowchart TD` in
  [`diagrams/architecture.mmd`](diagrams/architecture.mmd) showing the UI, agent,
  RAG pipeline, agentic workflow, and data flow.

## Documentation

- [x] **README.md** with project overview, architecture overview, setup
  instructions, sample interactions, design decisions & trade-offs, and a testing
  summary. → [`README.md`](README.md)

- [x] **model_card.md** with AI collaboration reflection, a helpful and a flawed
  AI suggestion, biases & limitations, system limitations, testing results, and a
  responsible-AI reflection. → [`model_card.md`](model_card.md)

- [x] **Test evidence file** with a structured evaluation table (Test ID, profile,
  request, confidence, issues, notes) and a genuine captured example output. →
  [`tests/results.md`](tests/results.md)

## Repository & Submission

- [x] **Version-controlled with meaningful commit history.** Git repo with a
  GitHub remote (`github.com/priyanka-bh2/applied-ai-system-pawpal`) and
  incremental commits.
- [ ] **Recent work committed & pushed.** The provider migration to Groq,
  `model_card.md`, `tests/results.md`, `PROJECT_CHECKLIST.md`, and the updated
  README/diagram are **not yet committed** — commit and push before submitting.
- [ ] **Repository is public.** Confirm visibility in GitHub → Settings → General
  → Danger Zone → *Change visibility* (cannot be verified locally).
- [ ] **Secrets excluded from version control.** Confirm `.env` is git-ignored and
  no real API key is committed (the old `.env.example` key was replaced with a
  placeholder; verify `git log -p` history if a real key was ever pushed).

## Optional Enhancements (nice-to-have)

- [ ] Render `diagrams/architecture.mmd` to PNG/SVG and embed it in the README.
- [ ] Wire the LangGraph agent into the Streamlit UI (currently `app.py` runs the
  original task tracker; the AI planner is demonstrated via `test_quick.py`).
- [ ] Add a relevance threshold to retrieval so out-of-knowledge-base breeds
  genuinely lower confidence (see the limitation noted in `tests/results.md`).

---

### Quick verification

```bash
# Confirm all deliverables exist
for f in README.md model_card.md PROJECT_CHECKLIST.md \
         diagrams/architecture.mmd tests/results.md \
         src/agent.py src/retriever.py test_quick.py \
         data/knowledge_base/breed_guidelines.json; do
  [ -f "$f" ] && echo "OK  $f" || echo "MISSING  $f"
done

# Run the end-to-end demo (requires GROQ_API_KEY in .env)
python test_quick.py
```
