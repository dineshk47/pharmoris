from functools import lru_cache
from app.utils.embeddings import get_embedding

@lru_cache(maxsize=1000)
async def get_cached_embedding(text: str) -> list:
    return await get_embedding(text)