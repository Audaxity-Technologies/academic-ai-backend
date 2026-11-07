import argparse
import sys
from pathlib import Path

from app.ai.syllabus.structurer import parse_syllabus


def render_markdown(hierarchy, report):
    lines = [f"# {hierarchy.subject_name or 'Syllabus'}", ""]
    if hierarchy.course_code:
        lines.extend([f"Course code {hierarchy.course_code}", ""])

    def label(node):
        prefix = f"{node.number} " if node.number else ""
        pages = f" (pp. {', '.join(map(str, node.pages))})" if node.pages else ""
        return f"{prefix}{node.title}{pages}"

    def render_topics(topics, depth=0):
        for topic in topics:
            lines.append(f"{'  ' * depth}- {label(topic)}")
            render_topics(topic.subtopics, depth + 1)

    for unit in hierarchy.units:
        lines.extend([f"## {label(unit)}", ""])
        render_topics(unit.topics)
        lines.append("")
    lines.extend(["## Parsing report", "",
                  f"{report.pages_processed} pages, {report.units} unit{'' if report.units == 1 else 's'}, "
                  f"{report.topics} topics, {report.subtopics} "
                  f"subtopic{'' if report.subtopics == 1 else 's'}.",
                  f"Review required: {'yes' if report.needs_review else 'no'}", ""])
    if report.ocr_pages:
        lines.append(f"OCR pages: {', '.join(map(str, report.ocr_pages))}")
    if report.empty_pages:
        lines.append(f"Empty pages: {', '.join(map(str, report.empty_pages))}")
    lines.extend(f"- {warning}" for warning in report.warnings)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Extract and review an academic syllabus")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("syllabus_output"))
    parser.add_argument("--native-pdf", action="store_true",
                        help="Use the PDF text layer and optional OCR without the Docling layout model")
    args = parser.parse_args()
    try:
        hierarchy, report, extracted = parse_syllabus(args.input, native_pdf=args.native_pdf)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        files = {
            "parsed_syllabus.json": hierarchy.model_dump_json(indent=2),
            "parsed_syllabus.md": render_markdown(hierarchy, report),
            "parsing_report.json": report.model_dump_json(indent=2),
            "extracted_preview.txt": extracted["raw_text"][:12000],
        }
        for name, content in files.items():
            (args.output_dir / name).write_text(content, encoding="utf-8")
    except Exception as exc:
        print(f"Parsing failed: {exc}", file=sys.stderr)
        return 1
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

