from app.ai.llm.syllabus_mapper import map_syllabus


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
        "atomicity and consistency. The instructor briefly mentions "
        "that indexing will be discussed in a future lecture."
    ),

    "key_concepts": [
        "Transactions",
        "Atomicity",
        "Consistency"
    ],

    "notes": [
        {
            "heading": "Transactions",
            "content": (
                "A transaction is a logical unit of database work. "
                "The lecture introduces the concept of transactions "
                "and discusses atomicity and consistency."
            )
        },
        {
            "heading": "Upcoming Topics",
            "content": (
                "Indexing will be discussed in a future lecture."
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