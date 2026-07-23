from app.services.llm_service import complete

SYSTEM = (
    "You are a summarization agent. Summarize the earlier conversation in a few short "
    "sentences. Preserve every specific fact, name, price, and number exactly as stated."
)


async def summarize(messages: list[dict]) -> str:
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    return await complete(
        [{"role": "system", "content": SYSTEM}, {"role": "user", "content": transcript}]
    )
