"""Streamlit UI for survey-designer.

Run with: streamlit run -m survey_designer.app
Or: streamlit run survey_designer/app.py
"""

from __future__ import annotations

import json

import streamlit as st

from .core import build_survey
from .llm_enrichment import DEFAULT_BACKEND, SUPPORTED_BACKENDS, is_available
from .models import ResearchBrief

st.set_page_config(
    page_title="Survey Designer · CPR Orbital",
    page_icon="📋",
    layout="wide",
)


# ----- Helpers --------------------------------------------------------------

PIPELINE_STAGES = [
    ("1", "Brief", "Topic, objectives, constructs, audience, target length."),
    ("2", "Generate", "Construct-aware question templates with neutral phrasing."),
    ("3", "Bias audit", "8 patterns: leading, loaded, double-barreled, jargon, absolutes, double negatives, assumption, acquiescence."),
    ("4", "Scale check", "Balance, anchors, mid-point, exhaustiveness, points."),
    ("5", "LLM enrich", "DSPy ChainOfThought rewrites, rationale, alternatives."),
    ("6", "Export", "JSON for CI, or copy into Qualtrics / Typeform."),
]


def render_pipeline(active_index: int, results: dict | None = None) -> None:
    """Render the 6-stage horizontal pipeline diagram.

    active_index: 0..6 — number of completed stages.
    results: optional dict mapping stage index → short status string.
    """
    results = results or {}
    cols = st.columns(len(PIPELINE_STAGES))
    for idx, (col, (num, name, desc)) in enumerate(zip(cols, PIPELINE_STAGES)):
        done = idx < active_index
        active = idx == active_index
        if done:
            border_color = "#b9e6c2"
            bg = "#f3faf5"
            num_color = "#09ab3b"
        elif active:
            border_color = "#ffb3b3"
            bg = "#fff4f4"
            num_color = "#ff4b4b"
        else:
            border_color = "#e6eaef"
            bg = "#ffffff"
            num_color = "#9ca3af"

        status_html = ""
        if idx in results:
            color = "#09ab3b" if done else "#ff4b4b"
            status_html = (
                f'<div style="font-size:11.5px;color:{color};font-weight:600;'
                f'margin-top:6px">✓ {results[idx]}</div>'
            )

        col.markdown(
            f"""<div style="border:1px solid {border_color};border-radius:10px;
                background:{bg};padding:12px;height:100%;min-height:140px;">
                <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;">
                    <div style="width:22px;height:22px;border-radius:50%;background:{num_color};
                                color:white;font-size:12px;font-weight:700;
                                display:flex;align-items:center;justify-content:center;">{num}</div>
                    <div style="font-size:13.5px;font-weight:600;color:#262730">{name}</div>
                </div>
                <div style="font-size:12px;color:#6b7280;line-height:1.4">{desc}</div>
                {status_html}
            </div>""",
            unsafe_allow_html=True,
        )


# ----- Header ---------------------------------------------------------------

st.title("Survey Designer")
st.caption(
    "AI-assisted survey question generation with bias detection and response-scale validation. "
    "Part of the CPR Orbital Series — Tool 28 of 40."
)


# ----- Sidebar — Configuration (always visible) -----------------------------

with st.sidebar:
    st.subheader("Configuration")

    st.markdown("**LLM enrichment**")
    enable_llm = st.checkbox("Enable LLM enrichment", value=True)
    backend = st.selectbox(
        "Model",
        options=list(SUPPORTED_BACKENDS.keys()),
        index=list(SUPPORTED_BACKENDS.keys()).index(DEFAULT_BACKEND),
        help="LLM backend used for question rewrites and rationale.",
    )

    available = is_available(backend)
    if enable_llm and not available:
        env_var = SUPPORTED_BACKENDS.get(backend, "API key")
        st.warning(f"{env_var} not set — falling back to rule-based output.")
    elif enable_llm and available:
        st.success("✓ LLM enrichment ready")

    sidebar_status_placeholder = st.container()
    sidebar_summary_placeholder = st.container()

    st.divider()
    st.caption(
        "**About.** Rule-based core runs offline. "
        "This tool is for instrument quality checking — it does not replace pilot testing with real participants."
    )


# ----- Pipeline diagram (always visible at top of main area) ----------------

if "run_results" not in st.session_state:
    st.session_state.run_results = None

with st.container():
    if st.session_state.run_results is None:
        render_pipeline(active_index=0)
    else:
        results = st.session_state.run_results
        survey_run = results["survey"]
        stage_status = {
            0: f"{results['objectives']} objectives · {results['constructs']} constructs",
            1: f"{len(survey_run.questions)} questions",
            2: f"{survey_run.bias_count} flags",
            3: f"{survey_run.scale_issue_count} issues",
            4: survey_run.llm_backend or "skipped",
            5: "Ready",
        }
        render_pipeline(active_index=6, results=stage_status)

st.divider()


# ----- Main: Brief input ----------------------------------------------------

with st.container():
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Research brief")
        topic = st.text_input("Topic / product", value="our new analytics dashboard")
        objectives_text = st.text_area(
            "Objectives (one per line)",
            value=(
                "Measure satisfaction with the redesigned dashboard\n"
                "Identify the main barriers to daily use\n"
                "Estimate likelihood to recommend"
            ),
            height=110,
        )
        audience = st.text_input("Audience", value="Active users in the last 30 days")
        constructs_text = st.text_input(
            "Constructs (comma-separated, optional)",
            value="satisfaction, usability, frequency, barriers, recommendation",
        )
        method_notes = st.text_area("Method notes (optional)", value="", height=70)

    with col2:
        st.subheader("Generation settings")
        desired_length = st.slider("Target question count", 4, 24, 10)
        run_button = st.button("Generate survey", type="primary", use_container_width=True)


# ----- Run generation -------------------------------------------------------

if run_button:
    objectives = [line.strip() for line in objectives_text.splitlines() if line.strip()]
    constructs = [c.strip() for c in constructs_text.split(",") if c.strip()]

    brief = ResearchBrief(
        topic=topic,
        objectives=objectives,
        audience=audience,
        constructs=constructs,
        method_notes=method_notes,
        desired_length=desired_length,
    )

    with st.spinner("Running pipeline: generate → audit → validate → enrich..."):
        survey = build_survey(brief, enrich_with_llm=enable_llm, llm_backend=backend)

    st.session_state.run_results = {
        "survey": survey,
        "objectives": len(objectives),
        "constructs": len(constructs),
    }
    st.rerun()


# ----- Render results -------------------------------------------------------

if st.session_state.run_results is not None:
    survey = st.session_state.run_results["survey"]

    # Populate sidebar pipeline status now that we have results
    with sidebar_status_placeholder:
        st.divider()
        st.subheader("Pipeline status")
        constructs_set = sorted({q.construct for q in survey.questions if q.construct})
        st.markdown(
            f"✅ **Brief loaded** — {st.session_state.run_results['objectives']} objectives · "
            f"{st.session_state.run_results['constructs']} constructs · target {len(survey.questions)}"
        )
        st.markdown(
            f"✅ **Questions generated** — {len(survey.questions)} across {', '.join(constructs_set)}"
        )
        sev_counts = {"high": 0, "medium": 0, "low": 0}
        for q in survey.questions:
            for f in q.bias_flags:
                sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
        st.markdown(
            f"✅ **Bias audit** — {survey.bias_count} flags · "
            f"{sev_counts['high']} high · {sev_counts['medium']} medium · {sev_counts['low']} low"
        )
        rec_count = sum(
            len(q.scale_validation.recommendations) if q.scale_validation else 0
            for q in survey.questions
        )
        st.markdown(
            f"✅ **Scale validation** — {survey.scale_issue_count} issues · {rec_count} recommendations"
        )
        if survey.llm_backend:
            llm_rewrites = sum(1 for q in survey.questions if q.llm_rewrite)
            st.markdown(
                f"✅ **LLM enrichment** — {llm_rewrites} rewrites · backend `{survey.llm_backend}`"
            )
        else:
            st.markdown("⏭️ **LLM enrichment** — skipped (no API key)")
        st.markdown("✅ **Export ready** — JSON download below")

    with sidebar_summary_placeholder:
        st.divider()
        st.subheader("Run summary")
        c1, c2 = st.columns(2)
        c1.metric("Questions", len(survey.questions))
        c2.metric("Quality", f"{survey.overall_quality_score:.2f}")
        c3, c4 = st.columns(2)
        c3.metric("Bias flags", survey.bias_count)
        c4.metric("Patterns", "8")

    # Compact brief summary strip
    bs1, bs2, bs3 = st.columns([2, 1, 1])
    with bs1:
        st.markdown(f"**Topic** · {topic}")
        objs = [line.strip() for line in objectives_text.splitlines() if line.strip()]
        st.markdown(f"**Objectives** · {' · '.join(objs)}")
    with bs2:
        st.markdown(f"**Audience** · {audience}")
        st.markdown(f"**Target length** · {desired_length} questions")
    with bs3:
        c_list = [c.strip() for c in constructs_text.split(",") if c.strip()]
        st.markdown(f"**Constructs** · {' · '.join(c_list)}")

    st.divider()

    # Overview metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Questions", len(survey.questions))
    m2.metric("Overall quality", f"{survey.overall_quality_score:.2f}")
    m3.metric("Bias flags", survey.bias_count)
    m4.metric("Scale issues", survey.scale_issue_count)

    if survey.llm_summary:
        st.info(f"**LLM summary** — {survey.llm_summary}")

    st.subheader("Generated questions")

    for q in survey.questions:
        score_color = "🟢" if q.quality_score >= 0.85 else ("🟡" if q.quality_score >= 0.65 else "🔴")
        with st.expander(
            f"{score_color} {q.id} — {q.text} (quality: {q.quality_score:.2f})",
            expanded=True,
        ):
            cols = st.columns([2, 1])
            with cols[0]:
                st.markdown(f"**Construct** · {q.construct}")
                st.markdown(f"**Type** · `{q.question_type}`")
                st.markdown(f"**Rationale** · {q.rationale}")

                if q.scale:
                    st.markdown("**Response scale**")
                    if q.scale.labels:
                        st.write(" · ".join(q.scale.labels))
                    elif q.scale.anchors:
                        st.write(q.scale.anchors)
                    else:
                        st.write("Open-ended")

                if q.llm_rewrite:
                    st.success(f"**LLM rewrite** — {q.llm_rewrite}")
                if q.llm_rationale:
                    st.caption(f"**LLM rationale** — {q.llm_rationale}")
                if q.llm_alternative_phrasings:
                    st.markdown("**Alternative phrasings**")
                    for alt in q.llm_alternative_phrasings:
                        st.markdown(f"- {alt}")

            with cols[1]:
                if q.bias_flags:
                    st.markdown("**Bias flags**")
                    for f in q.bias_flags:
                        sev_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(f.severity, "⚪")
                        st.markdown(f"{sev_emoji} **{f.bias_type}** — {f.rationale}")
                        if f.rewrite_suggestion:
                            st.caption(f"_{f.rewrite_suggestion}_")
                else:
                    st.markdown("**Bias flags** — none")

                if q.scale_validation:
                    if q.scale_validation.issues:
                        st.markdown("**Scale issues**")
                        for issue in q.scale_validation.issues:
                            st.markdown(f"🔴 {issue}")
                    if q.scale_validation.warnings:
                        st.markdown("**Scale warnings**")
                        for warn in q.scale_validation.warnings:
                            st.markdown(f"🟡 {warn}")
                    if q.scale_validation.recommendations:
                        st.markdown("**Scale recommendations**")
                        for rec in q.scale_validation.recommendations:
                            st.markdown(f"💡 {rec}")

    st.divider()

    # Export
    st.subheader("Export")
    json_blob = json.dumps(survey.to_dict(), indent=2)
    st.download_button(
        label="Download survey as JSON",
        data=json_blob,
        file_name=f"survey_{topic.replace(' ', '_')[:30]}.json",
        mime="application/json",
    )

    if st.button("Reset and start a new run"):
        st.session_state.run_results = None
        st.rerun()
else:
    st.info("Fill in the brief above and click **Generate survey** to run the pipeline.")
