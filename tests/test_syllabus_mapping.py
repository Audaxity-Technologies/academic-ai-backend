from app.ai.llm.syllabus_mapper import map_syllabus


syllabus_topics = [
    "ER Model",
    "Relational Model",
    "SQL",
    "Normalization",
    "Transactions",
    "Serializability",
    "Indexing",
    "Query Optimization"
]


lecture_notes = {
    "title": "Normalization and Functional Dependencies",

    "summary": (
        "The lecture explains functional dependencies, "
        "candidate keys, and database normalization."
    ),

    "key_concepts": [
        "Functional dependencies",
        "Candidate keys",
        "1NF",
        "2NF",
        "3NF",
        "BCNF"
    ],

    "notes": [
        {
            "heading": "Functional Dependencies",
            "content": (
                "Functional dependencies describe relationships "
                "between attributes in a relation."
            )
        },
        {
            "heading": "Normalization",
            "content": (
                "The lecture explains first normal form, "
                "second normal form, third normal form, "
                "and Boyce-Codd Normal Form."
            )
        }
    ]
}


result = map_syllabus(
    syllabus_topics,
    lecture_notes
)


print("\n===== SYLLABUS MAPPING RESULT =====\n")

print(result)