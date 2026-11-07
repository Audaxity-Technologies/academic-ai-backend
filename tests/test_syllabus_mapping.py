from app.ai.pipeline.syllabus_mapping import process_syllabus_mapping

syllabus_topics = [
    "ER Model",
    "Relational Model",
    "SQL",
    "Transactions",
    "ACID Properties",
    "Serializability",
    "Indexing",
    "Query Optimization"
]
lecture_notes = {
    "title": "Introduction to Transactions",

    "summary": (
        "The lecture introduces database transactions and explains "
        "atomicity and consistency."
    ),

    "learning_objectives": [
        "Understand the concept of a database transaction",
        "Understand atomicity and consistency"
    ],

    "sections": [
        {
            "heading": "Transactions",
            "explanation": (
                "A transaction is a logical unit of database work. "
                "The lecture explains the purpose of transactions "
                "and discusses atomicity and consistency."
            ),
            "examples": [
                {
                    "description": "Transaction example",
                    "illustration": (
                        "A transaction performs a sequence of database "
                        "operations as one logical unit."
                    )
                }
            ],
            "definitions": [
                {
                    "term": "Transaction",
                    "definition": (
                        "A transaction is a logical unit of database work."
                    )
                }
            ],
            "formulas": [],
            "diagram": {
                "type": "none",
                "mermaid_code": None
            },
            "instructor_emphasis": [
                "Transactions should be treated as logical units of work."
            ],
            "common_misconceptions": []
        }
    ],

    "questions_and_answers": [],

    "revision_summary": (
        "A transaction is a logical unit of database work. "
        "The lecture discusses atomicity and consistency."
    )
}
def test_legacy_notes_mapper_demo_is_isolated(monkeypatch):
    from app.ai.pipeline import syllabus_mapping

    monkeypatch.setattr(syllabus_mapping, "map_syllabus", lambda *args, **kwargs: {
        "mappings": [],
    })
    result = process_syllabus_mapping(syllabus_topics=syllabus_topics, lecture_notes=lecture_notes)
    assert result == {"mappings": [], "coverage_percentage": 0.0}
