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
    title = notes.get("title", "Lecture Notes")
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 5 * mm))

    # Summary
    summary = notes.get("summary", "")
    if summary:
        story.append(Paragraph("Summary", section_style))
        story.append(Paragraph(summary, body_style))
        story.append(Spacer(1, 3 * mm))

    # Learning Objectives
    learning_objectives = notes.get("learning_objectives", [])
    if learning_objectives:
        story.append(Paragraph("Learning Objectives", section_style))
        for obj in learning_objectives:
            story.append(Paragraph(f"• {obj}", body_style))
        story.append(Spacer(1, 3 * mm))

    # Sections
    sections = notes.get("sections", [])
    if sections:
        story.append(Paragraph("Lecture Sections", section_style))
        for section in sections:
            heading = section.get("heading", "")
            explanation = section.get("explanation", "")
            
            if heading:
                story.append(Paragraph(heading, heading_style))
            if explanation:
                story.append(Paragraph(explanation, body_style))
            
            # Examples
            examples = section.get("examples", [])
            if examples:
                story.append(Paragraph("Examples", heading_style))
                for example in examples:
                    description = example.get("description", "")
                    illustration = example.get("illustration", "")
                    if description:
                        story.append(Paragraph(f"<b>{description}</b>", body_style))
                    if illustration:
                        story.append(Paragraph(illustration, body_style))
            
            # Definitions
            definitions = section.get("definitions", [])
            if definitions:
                story.append(Paragraph("Definitions", heading_style))
                for definition in definitions:
                    term = definition.get("term", "")
                    definition_text = definition.get("definition", "")
                    if term:
                        story.append(Paragraph(f"<b>{term}</b>: {definition_text}", body_style))
            
            # Formulas
            formulas = section.get("formulas", [])
            if formulas:
                story.append(Paragraph("Formulas", heading_style))
                for formula in formulas:
                    story.append(Paragraph(f"<i>{formula}</i>", body_style))
            
            # Instructor Emphasis
            instructor_emphasis = section.get("instructor_emphasis", [])
            if instructor_emphasis:
                story.append(Paragraph("Instructor Emphasis", heading_style))
                for emphasis in instructor_emphasis:
                    story.append(Paragraph(f"• {emphasis}", body_style))
            
            # Common Misconceptions
            common_misconceptions = section.get("common_misconceptions", [])
            if common_misconceptions:
                story.append(Paragraph("Common Misconceptions", heading_style))
                for misconception in common_misconceptions:
                    story.append(Paragraph(f"• {misconception}", body_style))
            
            story.append(Spacer(1, 2 * mm))

    # Questions & Answers
    qa = notes.get("questions_and_answers", [])
    if qa:
        story.append(Paragraph("Questions & Answers", section_style))
        for item in qa:
            question = item.get("question", "")
            answer = item.get("answer", "")
            if question:
                story.append(Paragraph(f"<b>Q:</b> {question}", body_style))
            if answer:
                story.append(Paragraph(f"<b>A:</b> {answer}", body_style))
            story.append(Spacer(1, 1 * mm))

    # Revision Summary
    revision_summary = notes.get("revision_summary", "")
    if revision_summary:
        story.append(Paragraph("Revision Summary", section_style))
        story.append(Paragraph(revision_summary, body_style))

    doc.build(story)

    return str(output_file)