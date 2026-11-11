import requests
import streamlit as st
import hashlib
from html import escape
from typing import Any
import plotly.express as px

st.set_page_config(page_title="Job Match Hunter", layout="wide")
st.title("Job Match Hunter")

# Scope background styling to the third results row.
# Native st.columns(border=True) supplies the equal-height borders.
st.html("""
<style>
.st-key-requirements_grid [data-testid="stColumn"]:nth-child(1) {
    background-color: #dcfce7;
    color: #14532d;
    border-radius: 10px;
}
.st-key-requirements_grid [data-testid="stColumn"]:nth-child(2) {
    background-color: #fee2e2;
    color: #7f1d1d;
    border-radius: 10px;
}
</style>
""")


def make_pie_plot(met_requirements: list[str], unmet_requirements: list[str]):
    """Show the proportion of listed requirements that are met or unmet."""
    fig = px.pie(
        names=["Met", "Unmet"],
        values=[len(met_requirements), len(unmet_requirements)],
        color=["Met", "Unmet"],
        color_discrete_map={"Met": "#16a34a", "Unmet": "#dc2626"},
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
    background: str | None = None,
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
        label = category.capitalize() if category else "Unclassified"
        items.append(
            f'<li style="background:{bg};color:{fg};padding:10px 12px;'
            f'border-radius:6px;margin-bottom:8px;overflow-wrap:anywhere;">'
            f'<small><strong>{label}</strong></small><br>'
            f'{escape(requirement)}</li>'
        )
    body = (
        '<ul style="list-style:none;padding:0;margin:0;">'
        + "".join(items) + "</ul>"
        if items else "<p>No requirements listed.</p>"
    )
    card_style = (
        f"background:{colors[background][0]};color:{colors[background][1]};"
        if background else ""
    )
    st.html(
        f'<section style="'
        f'padding:20px;{card_style}">'
        f'<h3 style="color:inherit;margin-top:0;">{escape(title)}</h3>'
        f'{body}</section>'
    )


def render_prediction(result: dict[str, Any]) -> None:
    """Display the prediction in three full-width rows."""
    mandatory = set(result.get("mandatory_requirements") or [])
    optional = set(result.get("optional_requirements") or [])
    met = result.get("met_requirements") or []
    unmet = result.get("unmet_requirements") or []
    all_requirements = result.get("all_requirements") or []

    # Row 1: bordered outer grid with two borderless, vertically centered columns.
    with st.container(border=True):
        score_column, chart_column = st.columns(
            2, border=False, vertical_alignment="center"
        )
        with score_column:
            st.metric("Match score", f'{result["score"]:g}%')
            st.write(result.get("score_reason") or "No explanation provided.")
        with chart_column:
            if met or unmet:
                st.plotly_chart(
                    make_pie_plot(met, unmet),
                    use_container_width=True,
                )
            else:
                st.info("No requirements available for the chart.")

    st.caption("Requirement type: red = mandatory · green = optional")

    # Row 2: two bordered columns with matching heights.
    with st.container(border=True, key="coverage_grid"):
        met_column, unmet_column = st.columns(2, border=True)
        with met_column:
            requirement_card("Met requirements", met, mandatory, optional)
        with unmet_column:
            requirement_card("Unmet requirements", unmet, mandatory, optional)

    # Row 3: equal-height bordered columns with full-column backgrounds.
    with st.container(border=True, key="requirements_grid"):
        optional_column, mandatory_column = st.columns(2, border=True)
        with optional_column:
            requirement_card(
                "Optional requirements",
                [req for req in all_requirements if req in optional],
                mandatory, optional, background="optional",
            )
        with mandatory_column:
            requirement_card(
                "Mandatory requirements",
                [req for req in all_requirements if req in mandatory],
                mandatory, optional, background="mandatory",
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