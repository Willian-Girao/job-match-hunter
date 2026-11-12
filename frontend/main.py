import requests
import streamlit as st
import hashlib
from html import escape
from typing import Any
import plotly.express as px

st.set_page_config(page_title="Job Match Hunter", layout="wide")
st.title("Job Match Hunter")
st.info(
    "Job Match Hunter uses generative AI to compare your curriculum vitae (CV) with a job description (JD) "
    "and help you identify relevant positions. Its analysis may contain errors "
    "and should be reviewed by a person. The match score reflects the system’s "
    "assessment of alignment with the job requirements; it does not estimate "
    "your chances of being hired."
)

# The third row uses one section with a responsive two-column card list.
st.html("""
<style>
.position-requirements-list {
    column-count: 2;
    column-gap: 12px;
}
.position-requirements-list > li {
    break-inside: avoid;
    page-break-inside: avoid;
    margin: 0 0 8px;
    display: flow-root;
}
@media (max-width: 640px) {
    .position-requirements-list {
        column-count: 1;
    }
}
</style>
""")


def make_pie_plot(met_requirements: list[str], unmet_requirements: list[str]):
    """Show the proportion of listed requirements that are met or unmet."""
    fig = px.pie(
        names=["Met", "Unmet"],
        values=[len(met_requirements), len(unmet_requirements)],
        title="Requirement coverage",
    )
    fig.update_traces(textinfo="percent+value")
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=340)
    return fig


def requirement_card(
    title: str,
    requirements: list[str],
    mandatory: set[str],
    optional: set[str],
    two_columns: bool = False,
) -> None:
    """Render requirement content inside its bordered Streamlit column."""
    colors = {
        "mandatory": ("#fee2e2", "#7f1d1d"),
        "optional": ("#dcfce7", "#14532d"),
    }
    items = []
    for requirement in requirements:
        # Membership uses exact strings; mandatory takes precedence if in both.
        category = (
            "mandatory" if requirement in mandatory
            else "optional" if requirement in optional
            else None
        )
        bg, fg = colors.get(category, ("#f1f5f9", "#0f172a"))
        items.append(
            f'<li style="background:{bg};color:{fg};padding:10px 12px;'
            f'border:1px solid {fg}33;border-radius:6px;'
            f'margin-bottom:8px;overflow-wrap:anywhere;">'
            f'{escape(requirement)}</li>'
        )
    list_class = ' class="position-requirements-list"' if two_columns else ""
    body = (
        f'<ul{list_class} style="list-style:none;padding:0;margin:0;">'
        + "".join(items) + "</ul>"
        if items else "<p>No requirements listed.</p>"
    )
    st.html(
        '<section style="padding:20px;">'
        f'<h3 style="color:inherit;margin-top:0;">{escape(title)}</h3>'
        f'{body}</section>'
    )


def render_prediction(result: dict[str, Any]) -> None:
    """Display the prediction in three full-width rows.
    """
    mandatory = set(result.get("mandatory") or [])
    optional = set(result.get("optional") or [])
    met = result.get("met") or []
    unmet = result.get("unmet") or []
    jd_requirements = result.get("jd_requirements") or []

    # Row 1: bordered outer grid with two borderless, vertically centered columns.
    st.caption("The match score is calculated by dividing the number of requirements met by the CV by the total number of mandatory and uncategorized requirements in the job description.")

    with st.container(border=True):
        score_column, chart_column = st.columns(
            2, border=False, vertical_alignment="center"
        )
        with score_column:
            st.metric("Match score", f'{result["score"]:g}%')
            evaluation = result.get("match_evaluation") or "No explanation provided."
            st.html(
                '<p style="text-align: justify; white-space: pre-wrap;">'
                f"{escape(evaluation)}"
                "</p>"
            )
        with chart_column:
            if met or unmet:
                st.plotly_chart(
                    make_pie_plot(met, unmet),
                    width='stretch',
                )
            else:
                st.info("No requirements available for the chart.")

    # Row 2: two bordered columns with matching heights.
    st.caption("Requirement type: red = mandatory · green = optional · no color = uncategorized")

    with st.container(border=True, key="coverage_grid"):
        met_column, unmet_column = st.columns(2, border=False)
        with met_column:
            requirement_card(
                "Met requirements",
                met,
                mandatory,
                optional
            )
        with unmet_column:
            requirement_card(
                "Unmet requirements",
                unmet,
                mandatory,
                optional
            )

    # Row 3: one full-width section, with all unique requirements.
    # Keep source order and include mandatory/optional items missing from jd_requirements.
    position_requirements = list(dict.fromkeys(
        jd_requirements
        + (result.get("mandatory") or [])
        + (result.get("optional") or [])
    ))
    with st.container(border=True, key="requirements_grid"):
        requirement_card(
            "Position requirements",
            position_requirements,
            mandatory,
            optional,
            two_columns=True,
        )


with st.form("prediction_form"):
    uploaded_cv = st.file_uploader(
        "Upload your CV",
        type=["pdf"],
    )

    jd_url = st.text_input(
        "Job description URL",
        placeholder="https://example.com/job",
    )

    submitted = st.form_submit_button("estimate match")

if submitted:
    jd_url = jd_url.strip()

    if uploaded_cv is None:
        st.error("Please upload your CV as a PDF.")
    elif not jd_url.startswith("https://"):
        st.error("Please enter a URL starting with https://.")
    else:
        try:
            with st.spinner("Estimating match..."):
                cv_bytes = uploaded_cv.getvalue()

                # Identify the file by its content, rather than its filename.
                cv_hash = hashlib.sha256(cv_bytes).hexdigest()

                # This dictionary belongs to the current Streamlit session.
                if "cv_text_cache" not in st.session_state:
                    st.session_state["cv_text_cache"] = {}

                cv_cache = st.session_state["cv_text_cache"]

                # Extract only if this PDF has not been processed in this session.
                if cv_hash not in cv_cache:
                    extraction_response = requests.post(
                        "http://127.0.0.1:8000/extract-cv",
                        files={
                            "cv_file": (
                                uploaded_cv.name,
                                cv_bytes,
                                "application/pdf",
                            )
                        },
                        timeout=30,
                    )
                    extraction_response.raise_for_status()

                    # Cache only after extraction succeeds.
                    cv_cache[cv_hash] = extraction_response.json()["text"]

                # Every prediction uses the previously extracted text.
                response = requests.post(
                    "http://127.0.0.1:8000/predict",
                    json={
                        "cv_text": cv_cache[cv_hash],
                        "jd_url": jd_url,
                    },
                    timeout=120,
                )
                response.raise_for_status()

            st.session_state["prediction_result"] = response.json()

        except requests.RequestException as exc:
            st.error(f"Could not complete the prediction: {exc}")

# Retain the latest successful result across Streamlit reruns.
if "prediction_result" in st.session_state:
    render_prediction(st.session_state["prediction_result"])

st.divider()
st.caption(
    "Privacy: CV text and analysis results are held temporarily in your app session to support repeated "
    "comparisons. AI requests are routed through OpenRouter to providers configured for [zero data retention](https://openrouter.ai/docs/guides/features/zdr), with "
    "no routine storage of prompts or responses after processing and no use for model training. Exceptions "
    "described in OpenRouter’s policy apply."
)