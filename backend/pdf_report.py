"""
pdf_report.py
─────────────
Generates a professional session report PDF using ReportLab.
Used by the FastAPI /sessions/{session_id}/report endpoint.
"""

import io
import json
from datetime import datetime
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart


# ── Colour palette ────────────────────────────────────────────────────────────
PRIMARY      = colors.HexColor("#1E3A5F")   # dark navy
ACCENT       = colors.HexColor("#2E86AB")   # teal
SUCCESS      = colors.HexColor("#28A745")
WARNING      = colors.HexColor("#FFC107")
DANGER       = colors.HexColor("#DC3545")
LIGHT_GRAY   = colors.HexColor("#F5F7FA")
MID_GRAY     = colors.HexColor("#DEE2E6")
TEXT_DARK    = colors.HexColor("#212529")
TEXT_MUTED   = colors.HexColor("#6C757D")


def score_color(score: float) -> colors.Color:
    if score >= 85:  return SUCCESS
    if score >= 70:  return ACCENT
    if score >= 55:  return WARNING
    return DANGER


def score_label(score: float) -> str:
    if score >= 85:  return "Excellent"
    if score >= 70:  return "Good"
    if score >= 55:  return "Needs Work"
    return "Poor"


# ── Style helpers ─────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["cover_title"] = ParagraphStyle(
        "cover_title", parent=base["Title"],
        fontSize=26, textColor=colors.white,
        spaceAfter=6, alignment=TA_CENTER, fontName="Helvetica-Bold"
    )
    styles["cover_sub"] = ParagraphStyle(
        "cover_sub", parent=base["Normal"],
        fontSize=12, textColor=colors.HexColor("#BDD5EA"),
        alignment=TA_CENTER, spaceAfter=4
    )
    styles["section_heading"] = ParagraphStyle(
        "section_heading", parent=base["Heading1"],
        fontSize=14, textColor=PRIMARY,
        spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold",
        borderPad=0
    )
    styles["sub_heading"] = ParagraphStyle(
        "sub_heading", parent=base["Heading2"],
        fontSize=11, textColor=ACCENT,
        spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold"
    )
    styles["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontSize=9.5, textColor=TEXT_DARK,
        leading=14, spaceAfter=4
    )
    styles["muted"] = ParagraphStyle(
        "muted", parent=base["Normal"],
        fontSize=8.5, textColor=TEXT_MUTED, leading=12
    )
    styles["rec_item"] = ParagraphStyle(
        "rec_item", parent=base["Normal"],
        fontSize=9.5, textColor=TEXT_DARK,
        leading=14, leftIndent=12, spaceAfter=3
    )
    styles["footer"] = ParagraphStyle(
        "footer", parent=base["Normal"],
        fontSize=7.5, textColor=TEXT_MUTED,
        alignment=TA_CENTER
    )
    return styles


# ── Score bar (drawn inline as a mini table) ──────────────────────────────────
def score_bar_table(dimension: str, score: float) -> Table:
    """Returns a table row showing dimension label, filled bar, and score."""
    bar_width = 120
    filled = int((score / 100) * bar_width)
    col = score_color(score)

    d = Drawing(bar_width, 10)
    d.add(Rect(0, 0, bar_width, 10, fillColor=MID_GRAY, strokeColor=None))
    d.add(Rect(0, 0, filled, 10, fillColor=col, strokeColor=None))

    score_text = f"{score:.1f}"
    label_text = score_label(score)

    data = [[
        Paragraph(dimension.capitalize(), ParagraphStyle("dim", fontSize=9, textColor=TEXT_DARK, fontName="Helvetica")),
        d,
        Paragraph(f"<b>{score_text}</b>", ParagraphStyle("sc", fontSize=9, textColor=col, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
        Paragraph(label_text, ParagraphStyle("lb", fontSize=8, textColor=TEXT_MUTED, alignment=TA_RIGHT)),
    ]]
    t = Table(data, colWidths=[80, 125, 35, 55])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# ── Cover page ────────────────────────────────────────────────────────────────
def cover_elements(styles, session_data: dict, story: list):
    # Navy banner
    banner_data = [[Paragraph("FluentAI", styles["cover_title"])]]
    banner = Table(banner_data, colWidths=[160*mm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(banner)

    sub_data = [[Paragraph("Audio Fluency Evaluation Report", styles["cover_sub"])]]
    sub_banner = Table(sub_data, colWidths=[160*mm])
    sub_banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
    ]))
    story.append(sub_banner)
    story.append(Spacer(1, 20))

    # Session metadata card
    sid       = session_data.get("session_id", "—")
    aid       = session_data.get("audio_id", "—")
    duration  = session_data.get("duration", 0)
    mins, secs = divmod(int(duration), 60)
    generated  = datetime.now().strftime("%d %b %Y, %I:%M %p")
    speakers   = list(session_data.get("scores_per_speaker", {}).keys())

    meta = [
        ["Session ID",  str(sid),         "Audio ID",    str(aid)],
        ["Duration",    f"{mins}m {secs}s","Generated",   generated],
        ["Speakers",    ", ".join(speakers), "Status",    "Completed"],
    ]
    mt = Table(meta, colWidths=[45*mm, 55*mm, 30*mm, 45*mm])
    mt.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_GRAY),
        ("BACKGROUND",   (0, 0), (0, -1), PRIMARY),
        ("BACKGROUND",   (2, 0), (2, -1), PRIMARY),
        ("TEXTCOLOR",    (0, 0), (0, -1), colors.white),
        ("TEXTCOLOR",    (2, 0), (2, -1), colors.white),
        ("FONTNAME",     (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",     (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("GRID",         (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("ROWBACKGROUNDS",(0, 0),(-1,-1), [LIGHT_GRAY, colors.white, LIGHT_GRAY]),
    ]))
    story.append(mt)
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GRAY))


# ── Speaker score section ─────────────────────────────────────────────────────
def speaker_score_section(styles, speaker: str, speaker_data: dict, story: list):
    scores = speaker_data.get("scores", {})
    recs   = speaker_data.get("recommendations", [])
    overall = scores.get("overall", 0)

    story.append(Spacer(1, 10))

    # Speaker header bar
    header_data = [[
        Paragraph(f"Speaker: {speaker}", ParagraphStyle(
            "spk_hdr", fontSize=12, textColor=colors.white,
            fontName="Helvetica-Bold", leftIndent=6)),
        Paragraph(f"Overall: {overall:.1f} / 100  |  {score_label(overall)}", ParagraphStyle(
            "spk_ovr", fontSize=10, textColor=colors.white,
            fontName="Helvetica", alignment=TA_RIGHT, rightIndent=6)),
    ]]
    ht = Table(header_data, colWidths=[95*mm, 75*mm])
    ht.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), ACCENT),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(KeepTogether([ht]))
    story.append(Spacer(1, 8))

    # Score bars
    dimensions = ["fluency", "clarity", "confidence", "grammar", "pronunciation", "communication"]
    story.append(Paragraph("Score Breakdown", styles["sub_heading"]))
    for dim in dimensions:
        val = scores.get(dim, 0)
        story.append(score_bar_table(dim, val))
    story.append(Spacer(1, 8))

    # Recommendations
    if recs:
        story.append(Paragraph("Improvement Recommendations", styles["sub_heading"]))
        for i, rec in enumerate(recs, 1):
            story.append(Paragraph(f"{i}.  {rec}", styles["rec_item"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY))


# ── Progress trend section ────────────────────────────────────────────────────
def progress_section(styles, progress_data: Optional[list], story: list):
    """
    progress_data: list of dicts like
      [{"session_name": "Session 1", "overall": 72.0, "fluency": 68, ...}, ...]
    If None/empty, show a placeholder.
    """
    story.append(PageBreak())
    story.append(Paragraph("Progress Trend", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 8))

    if not progress_data or len(progress_data) < 2:
        story.append(Paragraph(
            "Progress trends will appear here once the student completes more than one session. "
            "Scores are tracked across fluency, clarity, confidence, grammar, pronunciation, "
            "and communication.",
            styles["body"]
        ))
        story.append(Spacer(1, 10))

        # Placeholder table showing what will appear
        ph_data = [["Session", "Fluency", "Clarity", "Confidence", "Grammar", "Pronunciation", "Overall"]]
        ph_data.append(["Session 1", "—", "—", "—", "—", "—", "—"])
        ph_data.append(["Session 2", "—", "—", "—", "—", "—", "—"])
        pt = Table(ph_data, colWidths=[35*mm, 22*mm, 22*mm, 25*mm, 22*mm, 30*mm, 22*mm])
        pt.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
            ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
            ("GRID",          (0, 0), (-1, -1), 0.4, MID_GRAY),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(pt)
        return

    # Build progress table from real data
    dims = ["fluency", "clarity", "confidence", "grammar", "pronunciation", "overall"]
    hdr  = ["Session"] + [d.capitalize() for d in dims]
    rows = [hdr]
    for p in progress_data:
        row = [p.get("session_name", "—")]
        for d in dims:
            v = p.get(d)
            row.append(f"{v:.1f}" if v is not None else "—")
        rows.append(row)

    col_w = [40*mm] + [21*mm] * len(dims)
    pt = Table(rows, colWidths=col_w)
    pt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.4, MID_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(pt)


# ── Main generator function ───────────────────────────────────────────────────
def generate_session_report(session_data: dict, progress_data: Optional[list] = None) -> bytes:
    """
    session_data: the full JSON returned by /upload endpoint
    progress_data: optional list of past session score dicts for trend table
    Returns: PDF as bytes (for FastAPI StreamingResponse)
    """
    buf    = io.BytesIO()
    W, H   = A4
    margin = 18 * mm

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=margin, bottomMargin=margin + 6,
        title="FluentAI Session Report",
        author="FluentAI System"
    )

    styles = build_styles()
    story  = []

    # 1. Cover / metadata
    cover_elements(styles, session_data, story)
    story.append(Spacer(1, 16))

    # 2. Scores per speaker
    story.append(Paragraph("Speaker Evaluations", styles["section_heading"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))

    speakers = session_data.get("scores_per_speaker", {})
    for speaker_label, speaker_data in speakers.items():
        speaker_score_section(styles, speaker_label, speaker_data, story)

    story.append(Spacer(1, 10))

    # 3. Progress trend (new page)
    progress_section(styles, progress_data, story)

    # 4. Footer note
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Generated by FluentAI  |  {datetime.now().strftime('%d %b %Y %H:%M')}  |  "
        "Scores are AI-generated and intended for formative feedback only.",
        styles["footer"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = {
        "session_id": 25, "audio_id": 25, "duration": 68.376,
        "scores_per_speaker": {
            "SPEAKER_00": {
                "scores": {
                    "fluency": 80, "clarity": 81.2, "confidence": 76.2,
                    "grammar": 100, "pronunciation": 76.9,
                    "communication": 83, "overall": 82.9
                },
                "recommendations": [
                    "Work on steadying your speaking pace — record yourself and review the playback.",
                    "Focus on stressed syllables and connected speech for clearer pronunciation."
                ]
            }
        }
    }
    pdf_bytes = generate_session_report(sample)
    with open("session_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"PDF written: {len(pdf_bytes):,} bytes")