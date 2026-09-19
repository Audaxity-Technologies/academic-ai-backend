from pathlib import Path

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)


def generate_pdf(notes: dict, output_path: str) -> str:

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=24,
        leading=30,
        spaceAfter=20,
    )

    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Heading2"],
        fontSize=16,
        leading=20,
        spaceBefore=15,
        spaceAfter=8,
    )

    heading_style = ParagraphStyle(
        "HeadingCustom",
        parent=styles["Heading3"],
        fontSize=13,
        leading=17,
        spaceBefore=10,
        spaceAfter=5,
    )

    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=16,
        spaceAfter=8,
    )

    story = []

    # Title
    story.append(
        Paragraph(
            notes.get("title", "Lecture Notes"),
            title_style,
        )
    )

    story.append(Spacer(1, 5 * mm))

    # Summary
    story.append(
        Paragraph("Summary", section_style)
    )

    story.append(
        Paragraph(
            notes.get("summary", ""),
            body_style,
        )
    )

    # Key concepts
    story.append(
        Paragraph("Key Concepts", section_style)
    )

    for concept in notes.get("key_concepts", []):
        story.append(
            Paragraph(
                f"• {concept}",
                body_style,
            )
        )

    # Notes
    story.append(
        Paragraph("Lecture Notes", section_style)
    )

    for note in notes.get("notes", []):

        story.append(
            Paragraph(
                note.get("heading", ""),
                heading_style,
            )
        )

        story.append(
            Paragraph(
                note.get("content", ""),
                body_style,
            )
        )

    doc.build(story)

    return str(output_file)