from app.services.llm_service import complete

SYSTEM = (
    "You are a summarization agent. Condense the conversation into three concise "
    "sentences, preserving names, numbers, and decisions."
)


async def summarize(messages: list[dict]) -> str:
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    return await complete(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": transcript}]
    )
