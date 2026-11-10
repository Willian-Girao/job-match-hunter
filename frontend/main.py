import requests
import streamlit as st

st.title("Job Match Hunter")

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
                response = requests.post(
                    "http://127.0.0.1:8000/predict",
                    files={
                        "cv_file": (
                            uploaded_cv.name,
                            uploaded_cv.getvalue(),
                            "application/pdf",
                        )
                    },
                    data={"jd_url": jd_url},
                    timeout=120,
                )
                response.raise_for_status()

            for key, value in response.json().items():
                if isinstance(value, list):
                    text = "\n".join(str(item) for item in value)
                elif value is None:
                    text = "Not provided"
                else:
                    text = str(value)

                st.text_area(
                    label=key.replace("_", " ").capitalize(),
                    value=text,
                    disabled=True,
                    key=f"result_{key}",
                )

        except requests.RequestException as exc:
            st.error(f"Could not complete the prediction: {exc}")