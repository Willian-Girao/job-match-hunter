# Backend and API Design

[← Back to README](../README.md)

## Overview

The backend is implemented with FastAPI and separates ingestion, model interaction, score calculation, and HTTP error handling.

The high-level processing path is:

1. extract CV text from the uploaded PDF;
2. retrieve and clean the job-description webpage;
3. combine CV text, JD text, prompt, and output schema;
4. verify that the request fits the selected model's context window;
5. request a structured LLM response;
6. compute the match percentage deterministically;
7. return the structured result to the frontend.

## LLM client

The application uses the OpenAI Python client as an API-format client and points it at OpenRouter's OpenAI-compatible base URL.

Conceptually:

```text
application
    ↓
LLM client abstraction
    ↓
OpenAI-compatible client
    ↓
OpenRouter
    ↓
selected model provider
```

Using OpenRouter during experimentation made it possible to compare models from multiple providers through a common interface.

The rest of the application should depend on the application's own LLM-client interface rather than on OpenRouter-specific details wherever possible.

## Provider constraints

The application requires model/provider routes that support the parameters used by the request.

Provider routing also requires **zero data retention (ZDR)** because CVs can contain personal information.

The relevant request policy is conceptually:

```python
extra_body={
    "provider": {
        "require_parameters": True,
        "zdr": True,
    }
}
```

This is a routing requirement, not a claim that the LLM output is always correct or that the system provides a general privacy guarantee beyond the configured provider behavior.

## Structured output

The match model returns data constrained by a JSON Schema.

The current logical fields are:

```text
match_evaluation
jd_requirements
mandatory
optional
met
unmet
```

The purpose of structured output is not only presentation. It creates a stable contract between the probabilistic model and deterministic application code.

### Scoring

The model identifies requirements and whether they are supported by the CV.

The application computes:

```python
match_score = len(met) / len(jd_requirements)
```

The prompt/schema rules are designed so that `met` and `unmet` are populated from the same requirement universe represented by `jd_requirements`.

This means:

- semantic comparison is probabilistic;
- arithmetic is deterministic.

## API endpoints

### `POST /extract-cv`

Purpose:

- receive a CV PDF;
- extract its text;
- return the text to the frontend.

This endpoint is separate because users are expected to reuse the same CV while testing several job postings.

### `POST /predict`

Purpose:

- receive CV text and a job-posting URL;
- retrieve and clean the job-description text;
- request the LLM comparison;
- compute the score;
- return the match analysis.

The separation avoids re-running PDF extraction for every job URL.

## Context validation

Before a model request is sent, the application tokenizes the messages and schema and checks the total against the selected model's context length.

This catches oversized CV/JD combinations before they become provider-side failures.

## Error handling

The API uses centralized exception handling so endpoint code can allow unexpected failures to propagate to one place.

The current design distinguishes between:

### Expected external failures

Example: the supplied job URL cannot be retrieved.

These should:

- return a specific HTTP status (for example, 502 for a job-description retrieval failure);
- return a useful frontend message;
- avoid being treated as an internal application defect.

### Unexpected application failures

Unexpected errors can be:

- assigned a request identifier;
- logged to Supabase with debugging information;
- returned to the client as a safe generic response.

This gives the user a useful message without exposing stack traces while still making operational failures diagnosable.

## Supabase

Supabase has been used for two different engineering purposes:

1. **experiment tracking** — model, prompt, schema, input, latency, cost, error, output, ground truth, score, and related metadata;
2. **operational error analysis** — unexpected backend failures.

Candidate CV content is not intended to be stored as persistent application data in the current version.
