"""Result interpretation and follow-up suggestions (initial structure)."""

import json


async def interpret_stream(question: str, data: list[dict]):
    """Generator placeholder for interpretation streaming."""
    total = len(data)
    payload = {
        "question": question,
        "total_records": total,
        "sample": data[:3],
    }
    text = (
        "Preliminary analysis: "
        f"the query returned {total} record(s). "
        "Integrate the generative model here to interpret the data in natural language."
    )

    yield text + "\n"
    yield json.dumps(payload, ensure_ascii=False)


def suggest_followups(_: str, data: list[dict]) -> list[str]:
    """Generate contextual follow-up suggestions based on query results."""
    if not data:
        return [
            "Do you want to try a question with a different time period?",
            "Do you want to filter by product category?",
            "Do you want to see the same data by state?",
        ]

    return [
        "Do you want to segment this result by state?",
        "Do you want to compare this metric with the previous period?",
        "Do you want to detail the top items that most contribute to this result?",
    ]
