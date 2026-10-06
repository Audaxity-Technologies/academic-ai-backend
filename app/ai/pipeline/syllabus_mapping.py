def calculate_coverage(mappings: list[dict]) -> float:
    """
    Calculate syllabus coverage from topic mappings.

    covered          = 1.0
    partially_covered = 0.5
    mentioned        = 0.0
    not_covered      = 0.0
    """

    if not mappings:
        return 0.0

    score = 0.0

    for mapping in mappings:
        status = mapping["status"]

        if status == "covered":
            score += 1.0

        elif status == "partially_covered":
            score += 0.5

    coverage = (score / len(mappings)) * 100

    return round(coverage, 2)