import asyncio

from app.services.llm_service import complete

SYSTEM = (
    "You are a grader. Given a question, an expected answer, and a candidate answer, "
    "reply with a single number from 0 to 5 for how well the candidate matches the "
    "expected answer. Reply with the number only."
)


async def score(question: str, expected: str, candidate: str) -> float:
    prompt = f"Question: {question}\nExpected: {expected}\nCandidate: {candidate}"
    raw = await complete(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    )
    try:
        return float(raw.strip().split()[0])
    except (ValueError, IndexError):
        return 0.0


if __name__ == "__main__":
    print(asyncio.run(score("2+2?", "4", "It is 4")))
