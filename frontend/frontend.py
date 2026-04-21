import streamlit as st
import requests
import plotly.graph_objects as go

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO

API_URL = "http://127.0.0.1:8000"

# ─── CONFIG ──────────────────────────────────────
st.set_page_config(
    page_title="FluentAI Speech Analysis Dashboard",
    layout="wide"
)

# ─── SESSION ─────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "Upload"

# ─── GLOBAL CSS ──────────────────────────────────
st.markdown("""
<style>
:root {
    --bg:#1a1f2e;
    --surface:#1e2538;
    --border:#2a3147;
    --accent:#5ee7b0;
    --text:#e2e8f0;
}
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg);
    color: var(--text);
}
.topnav {
    display: flex;
    gap: 20px;
    padding: 12px 20px;
    border-bottom: 1px solid #2a3147;
    margin-bottom: 20px;
}
.topnav div.stButton > button {
    background: transparent !important;
    border: none !important;
    color: #9ca3af !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 6px 0 !important;
    box-shadow: none !important;
}
.topnav div.stButton > button:hover {
    background: transparent !important;
    color: #e2e8f0 !important;
}
.topnav div.stButton > button:active,
.topnav div.stButton > button:focus,
.topnav div.stButton > button:focus-visible {
    background: transparent !important;
    color: #5ee7b0 !important;
    border-bottom: 2px solid #5ee7b0 !important;
    outline: none !important;
    box-shadow: none !important;
}
button[kind="secondary"] {
    background: transparent !important;
}
.block-container {
    padding-top: 1rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─── NAVBAR ──────────────────────────────────────
menu_items = [
    ("Upload", "Upload"),
    ("Recording", "Sessions"),
    ("Transcripts", "Transcripts"),
    ("Analysis", "Analytics"),
    ("Reports", "Session Detail"),
    ("Preferences", "Notifications"),
]

st.markdown('<div class="topnav">', unsafe_allow_html=True)
cols = st.columns(len(menu_items))

for i, (label, key) in enumerate(menu_items):
    with cols[i]:
        if st.button(label, key=key, use_container_width=True):
            st.session_state["page"] = key
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)


# ─── RECOMMENDATION FUNCTION (ADDED) ───
def get_recommendations(fluency, clarity, confidence, grammar):
    tips = []

    if fluency < 70:
        tips.append("Improve fluency by practicing continuous speaking without pauses.")

    if clarity < 70:
        tips.append("Work on pronunciation and articulation for better clarity.")

    if confidence < 70:
        tips.append("Reduce filler words and maintain consistent speech pace.")

    if grammar < 80:
        tips.append("Focus on sentence structure and grammar correctness.")

    if not tips:
        tips.append("Excellent performance! Keep maintaining your speaking skills.")

    return tips


# PDF FUNCTION 
def generate_pdf(speaker_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []
    elements.append(Paragraph("<b>FluentAI Speech Analysis Report</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    for speaker in speaker_data:

        fluency = speaker.get("fluency")
        clarity = speaker.get("clarity")
        confidence = speaker.get("confidence")
        grammar = speaker.get("grammar")

        overall_score = round((fluency + clarity + confidence + grammar) / 4, 2)

        elements.append(Paragraph(
            f"<b>Speaker: {speaker.get('speaker_label')}</b>",
            styles["Heading2"]
        ))
        elements.append(Spacer(1, 10))

        table_data = [
            ["Metric", "Score"],
            ["Fluency", fluency],
            ["Clarity", clarity],
            ["Confidence", confidence],
            ["Grammar", grammar],
            ["Overall Score", overall_score]
        ]

        table = Table(table_data, colWidths=[200, 100])

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e2538")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#f4f6f8")),

            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#5ee7b0")),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 10))

        # ─── RECOMMENDATIONS IN PDF ───
        recommendations = get_recommendations(fluency, clarity, confidence, grammar)

        elements.append(Paragraph("<b>Recommendations:</b>", styles["Heading3"]))
        for tip in recommendations:
            elements.append(Paragraph(f"• {tip}", styles["Normal"]))

        elements.append(Spacer(1, 25))

    doc.build(elements)
    buffer.seek(0)
    return buffer

menu = st.session_state["page"]

# ─── HEADER ──────────────────────────────────────
def page_header(title, subtitle=""):
    st.markdown(f"""
    <h2>{title}</h2>
    <p style="color:#64748b;">{subtitle}</p>
    """, unsafe_allow_html=True)

# ─── PAGES ───────────────────────────────────────

# ================== UPLOAD ==================
if menu == "Upload":
    page_header("🎙️ Upload Audio", "Analyse a new speech recording")

    file = st.file_uploader("Upload file", type=["wav", "mp3"])

    if file:
        if st.button("Analyse Recording"):
            with st.spinner("Processing..."):
                res = requests.post(f"{API_URL}/upload", files={"file": file})

            if res.status_code == 200:
                st.success("Upload successful")
                st.session_state["session_id"] = res.json()["session_id"]
            else:
                st.error("Upload failed")

# ================== SESSIONS ==================
elif menu == "Sessions":
    page_header("🕐 Recordings")

    res = requests.get(f"{API_URL}/sessions")
    if res.status_code == 200:
        sessions = res.json()

        if not sessions:
            st.info("No sessions found.")
        else:
            for s in sessions:
                if st.button(s["session_name"], key=s["session_id"]):
                    st.session_state["session_id"] = s["session_id"]

    else:
        st.error("Failed to fetch sessions.")

# ================== TRANSCRIPTS ==================
elif menu == "Transcripts":
    page_header("📄 Transcripts")

    sid = st.session_state.get("session_id")

    if not sid:
        st.warning("Select a session first")
    else:
        res = requests.get(f"{API_URL}/sessions/{sid}/segments")

        if res.status_code == 200:
            segments = res.json()

            if not segments:
                st.info("No transcript available.")
            else:
                for seg in segments:
                    st.write(seg["text"])
        else:
            st.error("Failed to load transcripts.")

# ================== ANALYTICS ==================
elif menu == "Analytics":
    page_header("〰 Analysis")
    st.info("Analytics dashboard coming soon.")


# ================== REPORT ==================
elif menu == "Session Detail":
    page_header("📊 Reports")

    sid = st.session_state.get("session_id")

    if not sid:
        st.warning("Select a session first")
    else:
        st.write(f"Report for session {sid}")

        res = requests.get(f"{API_URL}/sessions/{sid}/scores")

        if res.status_code == 200:
            data = res.json()

            if not data:
                st.info("No report data available.")
            else:

                pdf_file = generate_pdf(data)

                st.download_button(
                    label="📄 Download Report as PDF",
                    data=pdf_file,
                    file_name=f"session_{sid}_report.pdf",
                    mime="application/pdf"
                )

                for speaker in data:
                    st.markdown(f"### Speaker {speaker.get('speaker_label', '?')}")

                    fluency = float(speaker.get("fluency", 0))
                    clarity = float(speaker.get("clarity", 0))
                    confidence = float(speaker.get("confidence", 0))
                    grammar = float(speaker.get("grammar", 0))

                    # OVERALL SCORE
                    overall_score = round((fluency + clarity + confidence + grammar) / 4, 2)

                    score_col1, score_col2 = st.columns([1, 5])

                    with score_col1:
                        st.markdown(f"""
                        <div style="
                            background:#1e2538;
                            padding:15px;
                            border-radius:12px;
                            text-align:center;
                            border:1px solid #2a3147;
                            margin-bottom:10px;
                        ">
                            <div style="font-size:12px;color:#9ca3af;">Overall Score</div>
                            <div style="font-size:28px;font-weight:bold;color:#5ee7b0;">
                                {overall_score}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    metrics = ["Fluency", "Clarity", "Confidence", "Grammar"]
                    values = [fluency, clarity, confidence, grammar]

                    radar_fig = go.Figure()
                    radar_fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]],
                        theta=metrics + [metrics[0]],
                        fill='toself',
                        line=dict(color="#5ee7b0")
                    ))

                    radar_fig.update_layout(
                        polar=dict(
                            bgcolor="#1e2538",
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100],
                                gridcolor="#2a3147"
                            )
                        ),
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)"
                    )

                    pie_fig = go.Figure(data=[go.Pie(
                        labels=metrics,
                        values=values,
                        hole=0.4
                    )])

                    pie_fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.plotly_chart(radar_fig, use_container_width=True)

                    with col2:
                        st.plotly_chart(pie_fig, use_container_width=True)
# ================== NOTIFICATIONS ==================
elif menu == "Notifications":
    page_header("⚙ Preferences")

    user_id = st.number_input("User ID", value=1)

    if st.button("Load Notifications"):
        res = requests.get(f"{API_URL}/notifications/{user_id}")

        if res.status_code == 200:
            notifications = res.json()

            if not notifications:
                st.info("No notifications.")
            else:
                for n in notifications:
                    st.write(n["message"])
        else:
            st.error("Failed to fetch notifications.")