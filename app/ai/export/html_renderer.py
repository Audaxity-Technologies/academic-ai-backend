from pathlib import Path
from typing import Dict


def render_html(notes: Dict, output_path: str) -> str:
    """Render notes JSON to a self-contained interactive HTML file."""
    
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- KaTeX for math rendering -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
    
    <!-- Mermaid for diagrams -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.0/mermaid.min.js"></script>
    
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
            background: #f9f9f9;
        }}
        
        h1 {{
            text-align: center;
            color: #1a1a1a;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 2rem;
            font-style: italic;
        }}
        
        .summary {{
            background: #e8f4f8;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            border-left: 4px solid #007acc;
        }}
        
        .learning-objectives {{
            background: #fff3cd;
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            border-left: 4px solid #ffc107;
        }}
        
        .learning-objectives h3 {{
            margin-top: 0;
            color: #856404;
        }}
        
        .learning-objectives ul {{
            margin-bottom: 0;
        }}
        
        details {{
            background: white;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        summary {{
            padding: 1rem 1.5rem;
            cursor: pointer;
            font-weight: 600;
            color: #007acc;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            transition: background 0.2s;
        }}
        
        summary:hover {{
            background: #e9ecef;
        }}
        
        .section-content {{
            padding: 1.5rem;
        }}
        
        .explanation {{
            margin-bottom: 1.5rem;
            line-height: 1.8;
        }}
        
        .examples {{
            background: #f0f7ff;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            border-left: 3px solid #007acc;
        }}
        
        .examples h4 {{
            margin-top: 0;
            color: #007acc;
        }}
        
        .definitions {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
        }}
        
        .definitions h4 {{
            margin-top: 0;
            color: #495057;
        }}
        
        .definition-item {{
            margin-bottom: 0.5rem;
        }}
        
        .definition-item strong {{
            color: #007acc;
        }}
        
        .formulas {{
            background: #fff5f5;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            border-left: 3px solid #e53e3e;
        }}
        
        .formulas h4 {{
            margin-top: 0;
            color: #e53e3e;
        }}
        
        .formula-item {{
            font-family: 'Courier New', monospace;
            background: white;
            padding: 0.5rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }}
        
        .diagram {{
            margin: 1rem 0;
            text-align: center;
        }}
        
        .diagram pre {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
        }}
        
        .instructor-emphasis {{
            background: #d4edda;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            border-left: 3px solid #28a745;
        }}
        
        .instructor-emphasis h4 {{
            margin-top: 0;
            color: #155724;
        }}
        
        .instructor-emphasis ul {{
            margin-bottom: 0;
        }}
        
        .common-misconceptions {{
            background: #f8d7da;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
            border-left: 3px solid #dc3545;
        }}
        
        .common-misconceptions h4 {{
            margin-top: 0;
            color: #721c24;
        }}
        
        .common-misconceptions ul {{
            margin-bottom: 0;
        }}
        
        .qa-section {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin-top: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .qa-section h2 {{
            color: #007acc;
            border-bottom: 2px solid #007acc;
            padding-bottom: 0.5rem;
        }}
        
        .qa-item {{
            margin: 1rem 0;
            padding-bottom: 1rem;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .qa-item:last-child {{
            border-bottom: none;
        }}
        
        .qa-question {{
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 0.5rem;
        }}
        
        .qa-answer {{
            color: #666;
            margin-left: 1rem;
        }}
        
        .revision-summary {{
            background: #e2e3e5;
            padding: 1.5rem;
            border-radius: 8px;
            margin-top: 2rem;
            border-left: 4px solid #6c757d;
        }}
        
        .revision-summary h2 {{
            color: #495057;
            margin-top: 0;
        }}
        
        .revision-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #007acc;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            transition: background 0.2s;
            z-index: 1000;
        }}
        
        .revision-toggle:hover {{
            background: #0056b3;
        }}
        
        .revision-mode .explanation,
        .revision-mode .examples,
        .revision-mode .definitions,
        .revision-mode .formulas,
        .revision-mode .diagram {{
            display: none;
        }}
        
        .revision-mode .section-content {{
            padding: 1rem;
        }}
        
        .revision-mode details {{
            background: #fff3cd;
        }}
        
        .revision-mode summary {{
            background: #ffe69c;
        }}
    </style>
</head>
<body>
    <button class="revision-toggle" onclick="toggleRevisionMode()">Toggle Revision Mode</button>
    
    <h1>{title}</h1>
    <div class="subtitle">Lecture Notes</div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>{summary}</p>
    </div>
    
    <div class="learning-objectives">
        <h3>Learning Objectives</h3>
        <ul>
            {learning_objectives}
        </ul>
    </div>
    
    <h2>Lecture Sections</h2>
    {sections}
    
    <div class="qa-section">
        <h2>Questions & Answers</h2>
        {qa}
    </div>
    
    <div class="revision-summary">
        <h2>Revision Summary</h2>
        <p>{revision_summary}</p>
    </div>
    
    <script>
        // Initialize Mermaid
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        
        // Render KaTeX
        document.addEventListener("DOMContentLoaded", function() {{
            renderMathInElement(document.body, {{
                delimiters: [
                    {{left: '$$', right: '$$', display: true}},
                    {{left: '$', right: '$', display: false}}
                ]
            }});
        }});
        
        // Toggle revision mode
        function toggleRevisionMode() {{
            document.body.classList.toggle('revision-mode');
            const button = document.querySelector('.revision-toggle');
            if (document.body.classList.contains('revision-mode')) {{
                button.textContent = 'Exit Revision Mode';
            }} else {{
                button.textContent = 'Toggle Revision Mode';
            }}
        }}
    </script>
</body>
</html>"""
    
    # Extract data
    title = notes.get("title", "Lecture Notes")
    summary = notes.get("summary", "No summary available.")
    learning_objectives = notes.get("learning_objectives", [])
    sections = notes.get("sections", [])
    qa = notes.get("questions_and_answers", [])
    revision_summary = notes.get("revision_summary", "No revision summary available.")
    
    # Build learning objectives HTML
    lo_html = "\n".join(f"            <li>{obj}</li>" for obj in learning_objectives)
    if not lo_html:
        lo_html = "            <li>No learning objectives specified.</li>"
    
    # Build sections HTML
    sections_html = ""
    for section in sections:
        heading = section.get("heading", "Untitled Section")
        explanation = section.get("explanation", "")
        examples = section.get("examples", [])
        definitions = section.get("definitions", [])
        formulas = section.get("formulas", [])
        diagram = section.get("diagram", {})
        instructor_emphasis = section.get("instructor_emphasis", [])
        common_misconceptions = section.get("common_misconceptions", [])
        
        section_html = f"""    <details>
        <summary>{heading}</summary>
        <div class="section-content">
            <div class="explanation">
                {explanation}
            </div>
"""
        
        # Examples
        if examples:
            examples_html = "            <div class=\"examples\">\n                <h4>Examples</h4>\n"
            for example in examples:
                description = example.get("description", "")
                illustration = example.get("illustration", "")
                examples_html += f"                <p><strong>{description}</strong></p>\n"
                if illustration:
                    examples_html += f"                <p>{illustration}</p>\n"
            examples_html += "            </div>\n"
            section_html += examples_html
        
        # Definitions
        if definitions:
            definitions_html = "            <div class=\"definitions\">\n                <h4>Definitions</h4>\n"
            for definition in definitions:
                term = definition.get("term", "")
                definition_text = definition.get("definition", "")
                definitions_html += f"                <div class=\"definition-item\"><strong>{term}:</strong> {definition_text}</div>\n"
            definitions_html += "            </div>\n"
            section_html += definitions_html
        
        # Formulas
        if formulas:
            formulas_html = "            <div class=\"formulas\">\n                <h4>Formulas</h4>\n"
            for formula in formulas:
                formulas_html += f"                <div class=\"formula-item\">{formula}</div>\n"
            formulas_html += "            </div>\n"
            section_html += formulas_html
        
        # Diagram
        if diagram and diagram.get("type") != "none":
            mermaid_code = diagram.get("mermaid_code", "")
            if mermaid_code:
                diagram_html = f"""            <div class="diagram">
                <h4>Diagram</h4>
                <pre class="mermaid">{mermaid_code}</pre>
            </div>
"""
                section_html += diagram_html
        
        # Instructor emphasis
        if instructor_emphasis:
            emphasis_html = "            <div class=\"instructor-emphasis\">\n                <h4>Instructor Emphasis</h4>\n                <ul>\n"
            for emphasis in instructor_emphasis:
                emphasis_html += f"                    <li>{emphasis}</li>\n"
            emphasis_html += "                </ul>\n            </div>\n"
            section_html += emphasis_html
        
        # Common misconceptions
        if common_misconceptions:
            misconceptions_html = "            <div class=\"common-misconceptions\">\n                <h4>Common Misconceptions</h4>\n                <ul>\n"
            for misconception in common_misconceptions:
                misconceptions_html += f"                    <li>{misconception}</li>\n"
            misconceptions_html += "                </ul>\n            </div>\n"
            section_html += misconceptions_html
        
        section_html += "        </div>\n    </details>\n"
        sections_html += section_html
    
    # Build Q&A HTML
    qa_html = ""
    if qa:
        for item in qa:
            question = item.get("question", "")
            answer = item.get("answer", "")
            qa_html += f"""    <div class="qa-item">
        <div class="qa-question">Q: {question}</div>
        <div class="qa-answer">A: {answer}</div>
    </div>
"""
    else:
        qa_html = "    <p>No questions and answers available.</p>"
    
    # Fill template
    html_content = html_template.format(
        title=title,
        summary=summary,
        learning_objectives=lo_html,
        sections=sections_html,
        qa=qa_html,
        revision_summary=revision_summary
    )
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding="utf-8")
    
    print(f"[HTML] Rendered notes to {output_path}")
    
    return str(output_path)
