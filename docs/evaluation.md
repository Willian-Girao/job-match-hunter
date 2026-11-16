# Model, Prompt, and Match Evaluation

[← Back to README](../README.md)

## Evaluation philosophy

The project uses experimentation to answer architectural questions instead of assuming that the first reasonable design is correct.

The initial MVP was deliberately small:

> Can an affordable, off-the-shelf language model extract structured data from a CV or job description?

The answer was yes. More importantly, the MVP exposed the questions that drove the next stage: prompt design, schema design, model selection, evaluation methodology, error propagation, and the eventual architecture change.

## Component-level benchmark

The original pipeline had three LLM tasks:

1. JD parsing;
2. CV parsing;
3. CV–JD match estimation.

The initial evaluation plan considered scoring only the final match result, but that would make failures difficult to diagnose. The project therefore moved to component-level evaluation first, followed by end-to-end evaluation.

### Test data

A small synthetic benchmark was created for both CVs and JDs at three difficulty levels:

- **easy** — explicit sections and straightforward extraction;
- **medium** — information distributed between sections and prose;
- **hard** — denser layouts or more ambiguous natural-language requirements.

The harder JDs also included realistic ways of expressing optionality, such as “preferred”, “nice to have”, and “is a plus”.

### Ground truth and annotation

For the benchmark, human review is the source of truth.

Because the model/prompt/input combinations generated too many outputs for practical first-pass manual scoring, a stronger LLM was used as an annotator to produce:

- a quality score from 0–100;
- a reason for the score.

The automated judgment was then manually reviewed against the original CV/JD and model output. The LLM judge accelerated evaluation; it did not replace human validation.

## Model filtering

The first candidate pool contained roughly 25 models selected from OpenRouter using constraints relevant to the application, including:

- text input;
- acceptable input/output pricing;
- support for required request parameters;
- structured-output support;
- zero-data-retention availability.

Benchmark results were recorded in Supabase.

The main comparison dimensions were:

1. **output quality**
2. **latency**
3. **cost**

Additional metadata included token usage, errors, finish reason, prompt version, schema version, input, and model.

A latency target of roughly five seconds was used during the initial screening because the product is intended to make job filtering feel faster than manually reading and evaluating a vacancy.

## Prompt engineering strategy

Prompts were treated as experimental artifacts rather than hard-coded strings.

The initial progression was:

1. a minimal persona/task prompt;
2. a more explicit instruction prompt;
3. a richer prompt with a few-shot example.

Observed failures were recorded and used to create revised versions.

Examples of prompt-related issues discovered during evaluation included:

- unsupported information;
- missing explicitly listed technical skills;
- duplicate entries;
- acronyms replacing complete names;
- incorrect interpretation of date ranges ending in “Present”;
- few-shot examples accidentally teaching unsupported reinterpretation.

The resulting process was:

> start small → observe failure modes → add only instructions that correct real failures → re-evaluate

This was useful because prompt length itself has a cost. The objective was not “most detailed prompt wins”; it was the smallest prompt that reliably produced the desired behavior.

## Task-specific results

One important result was that apparently similar extraction tasks did **not** favor the same configuration.

### CV parsing

The best trade-off between score, latency, and cost was:

- model: `openai/gpt-4.1-nano`
- prompt: `cv_01_persona.txt`
- schema: `01_cv_parsing.json`

### JD parsing

The strongest output quality across the test inputs was:

- model: `inception/mercury-2.5`
- prompt: `jd_03_persona_fewshot.txt`
- schema: `01_jd_parsing.json`

This showed that model and prompt choice should be treated as task-specific.

The JD task benefited more from few-shot behavior because job descriptions often express requirement importance indirectly (“preferred”, “plus”, “nice to have”, etc.), while CV extraction was generally less ambiguous.

## Why separate extraction was not kept in the matching path

The structured parsing benchmark also exposed a limitation of the original system design.

No tested configuration eliminated extraction errors. Common failures included:

- creating unsupported information;
- missing explicit information;
- incorrect duration estimates.

The goal of separate CV/JD parsing had been to make the final comparison easier and more deterministic. In practice, the structured representations were themselves imperfect and still contained natural language.

This meant the system would have had to solve both:

1. extraction reliability;
2. semantic equivalence between two independently generated representations.

That motivated a new experiment.

## Raw CV + raw JD match experiment

The revised approach provides the extracted raw text from both documents directly to one match model.

For the first match experiment:

- `openai/gpt-4.1-nano` was fixed as the model;
- one difficult CV and one real job description were used;
- a human-generated expected output served as the comparison target;
- prompt versions were iteratively refined based on observed failures.

The early prompt variants commonly:

- treated role-description prose as formal requirements;
- misclassified mandatory vs optional requirements;
- created unsupported `met` entries.

Later prompts added only the rules that corrected those failures. The resulting prompt produced behavior close enough to the intended output to proceed with application development.

A larger second round of match benchmarking remains planned.

## Resulting design principle

The benchmark changed the architecture:

> Preserve full CV/JD context for the semantic comparison, constrain the LLM output, then use deterministic application code for arithmetic and presentation.

This reduced the number of LLM calls and removed a layer of error propagation while keeping the output machine-readable.

## Evaluation work still to do

The current benchmark is useful but intentionally small. Before treating the model choice as broadly robust, the next evaluation round should include:

- more CV formats and seniority levels;
- more industries and JD styles;
- more job sites;
- more candidate–vacancy match levels;
- repeated runs where stochastic variation matters;
- explicit error categories for requirement extraction and requirement matching;
- end-to-end comparison across multiple model candidates.
