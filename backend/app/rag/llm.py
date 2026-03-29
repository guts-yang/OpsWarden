import httpx
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)


async def generate_answer(question: str, context_docs: list[dict]) -> str | None:
    settings = get_settings()
    if not settings.DEEPSEEK_API_KEY:
        return None

    context = "\n\n".join([
        f"问题：{doc['question']}\n解决方案：{doc['solution']}"
        for doc in context_docs
    ])

    messages = [
        {
            "role": "system",
            "content": (
                "你是一名专业的IT运维助手。根据以下知识库内容，简洁准确地回答用户的问题。"
                "如果知识库中有直接相关的解决方案，请基于该方案作答。"
                "回答时使用中文，语气专业友好，不要复述用户的问题，直接给出答案。\n\n"
                f"知识库内容：\n{context}"
            ),
        },
        {"role": "user", "content": question},
    ]

    try:
        async with httpx.AsyncClient(timeout=settings.DEEPSEEK_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.DEEPSEEK_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
                json={
                    "model": settings.DEEPSEEK_MODEL,
                    "messages": messages,
                    "temperature": settings.DEEPSEEK_TEMPERATURE,
                    "max_tokens": settings.DEEPSEEK_MAX_TOKENS,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"DeepSeek API error: {e}")
        return None
