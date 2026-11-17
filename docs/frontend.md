# Frontend and Data Handling

[← Back to README](../README.md)

## Why Streamlit

`Streamlit` was chosen because the first product goal is to validate and deploy the AI workflow quickly rather than invest heavily in frontend infrastructure.

The UI is deliberately simple:

1. upload a CV PDF;
2. provide a job-posting URL;
3. request a match estimate;
4. inspect the result.

## Result layout

The results are organized to make the first-pass decision quick.

### Match summary

The top section presents:

- numerical match score;
- short LLM-generated match assessment;
- pie chart showing requirement coverage.

The interface intentionally places the deterministic score next to the probabilistic explanation rather than presenting the two as the same type of output.

### Met and unmet requirements

A second section shows the requirements that appear to be:

- supported by the CV;
- not supported by the CV.

Requirement cards use the model's classification to distinguish mandatory, optional, and uncategorized requirements.

### Position requirements

A final section shows the full requirement set used by the match calculation.

This makes the score more inspectable: the user can see what the model treated as a requirement instead of receiving only an opaque percentage.

## CV session cache

`Streamlit` reruns the script during user interaction, so repeatedly extracting the same PDF would be unnecessary work.

The frontend therefore:

1. reads the PDF bytes;
2. computes a SHA-256 digest;
3. checks whether that digest exists in the current session state;
4. calls `/extract-cv` only when the PDF has not already been processed;
5. stores the returned CV text under the digest for the current session.

Conceptually:

```python
cv_hash = sha256(cv_bytes).hexdigest()

if cv_hash not in st.session_state:
    st.session_state[cv_hash] = extract_cv(cv_bytes)

cv_text = st.session_state[cv_hash]
```

The hash is used as a content-based cache key: identical file bytes produce the same key.

## Data lifetime

The current application does not use persistent candidate profiles.

The extracted CV text is held in `Streamlit` session state so it can survive reruns within that user's active session. It is not intended to be stored as a permanent CV record in the application database.

This is separate from experiment/operational data stored in Supabase.

## Generative-AI disclosure

The UI explicitly tells users that:

- the system uses generative AI;
- the result can contain errors;
- the output requires human validation;
- the match score should not be interpreted as the probability of being hired.

This is important because the product is designed to reduce screening time, not replace the candidate's judgment.

## Error presentation

Backend error responses are surfaced in the frontend.

Known failures should be actionable. For example, when a job page cannot be retrieved, the user should be told to check the URL or try a different posting rather than seeing a generic internal-server-error message.
