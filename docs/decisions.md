# Engineering Decisions

[← Back to README](../README.md)

This page records the decisions that most changed the system and the reasoning behind them.

## 1. Start with a feasibility MVP

**Question:** Can an affordable off-the-shelf LLM extract useful structured data from CVs and job descriptions?

**Decision:** Build a command-line MVP before building the product.

**Why:** The primary uncertainty was model capability, not UI or deployment.

**Outcome:** Feasibility was validated, and the MVP exposed the next engineering questions organically.

---

## 2. Convert PDFs to text before model calls

**Decision:** Extract PDF text before inference rather than relying on each model/provider's native document handling.

**Why:**

- every benchmarked model receives the same input;
- provider-specific PDF behavior does not confound model comparison;
- text input is cheaper and easier to inspect;
- PDF parsing becomes a separately testable component.

---

## 3. Treat prompts and schemas as versioned artifacts

**Decision:** Keep prompts and JSON Schemas versioned rather than embedding them invisibly inside application code.

**Why:** Both prompt instructions and schema descriptions materially changed model outputs during benchmarking.

**Lesson:** In an LLM system, the schema can be part of the behavioral specification, not merely an output datatype.

---

## 4. Evaluate components before the full pipeline

**Initial idea:** Score only the final match result.

**Problem:** A bad final result would not reveal whether the CV parser, JD parser, or matcher failed.

**Decision:** Create small annotated test sets for CV and JD parsing, evaluate those components independently, then evaluate the match task.

**Why:** AI-system failures need to be diagnosable.

---

## 5. Use automated annotation to accelerate—not replace—human review

**Decision:** Use a stronger LLM to create first-pass quality scores and explanations for large benchmark result sets.

**Why:** The model × prompt × input combinations were too numerous for efficient first-pass manual review.

**Safeguard:** Manually validate the judge's reasoning against the original input and generated output.

**Lesson:** An LLM judge is an evaluation tool, not ground truth.

---

## 6. Do not assume one model or prompt is best for every task

**Observation:** CV and JD extraction favored different configurations.

- CV extraction: `openai/gpt-4.1-nano` + `cv_01_persona.txt`
- JD extraction: `inception/mercury-2.5` + `jd_03_persona_fewshot.txt`

**Lesson:** Even similar LLM tasks can have different ambiguity profiles and therefore different optimal prompt/model choices.

---

## 7. Abandon separate CV/JD parsing in the deployed match path

**Original design:**

```text
CV → structured CV
JD → structured JD
structured CV + structured JD → match
```

**Problem:** Extraction errors and lost context propagated into the final comparison. The structured values were also still natural language, so deterministic semantic matching remained difficult.

**Revised design:**

```text
raw CV text + raw JD text → structured match result
```

**Why it won:**

- preserves full context;
- removes one layer of error propagation;
- removes the need to reconcile independently generated wording;
- reduces LLM calls;
- lowers latency and cost;
- still produces machine-readable output for deterministic scoring.

This was one of the most important architecture changes in the project.

---

## 8. Separate semantic reasoning from arithmetic

**Decision:** Let the LLM decide whether CV evidence supports a requirement, but compute the final percentage in normal Python code.

**Why:** Semantic equivalence is a language-understanding problem; counting matched requirements is not.

**Result:** The system keeps probabilistic work where it is needed and deterministic work where it is possible.

---

## 9. Use OpenRouter as a model gateway

**Decision:** Use an OpenAI-compatible client with OpenRouter as the base endpoint.

**Why:**

- one interface for many providers;
- useful during model benchmarking;
- easier model switching;
- centralized usage/cost information;
- provider filtering for required features.

**Design consideration:** Keep provider-specific concerns behind the application's LLM-client abstraction so the rest of the system is not unnecessarily coupled to OpenRouter.

---

## 10. Require zero-data-retention routing

**Decision:** Restrict model routing to provider endpoints supporting ZDR.

**Why:** CVs contain personal information.

This is one part of the privacy design; it does not remove the need to reason separately about frontend state, logs, error data, and any future persistent storage.

---

## 11. Cache CV extraction in the user session

**Observation:** A user is likely to upload one CV and compare it against several job postings.

**Decision:** Hash the PDF bytes and cache extracted CV text in Streamlit session state.

**Why:** Avoid repeated PDF parsing without introducing persistent candidate storage.

---

## 12. Centralize unexpected API errors

**Decision:** Use FastAPI-level error handling for unexpected exceptions while handling known external failures explicitly.

**Why:**

- endpoint logic stays simpler;
- unexpected failures become consistently observable;
- users receive safe, predictable responses;
- known failures such as an inaccessible job URL can receive specific guidance instead of a generic 500.

---

## 13. Optimize for a portfolio that demonstrates engineering judgment

The goal is not to maximize the number of AI techniques used.

The project deliberately avoids adding RAG, agents, fine-tuning, vector databases, or other components unless the problem provides evidence that they are useful.

The portfolio value comes from being able to explain:

- what uncertainty each experiment addressed;
- why an architecture was changed;
- what was measured;
- what failed;
- which responsibilities belong to the model versus deterministic software;
- how the system behaves when external dependencies fail.
