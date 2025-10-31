import os
import hashlib
import random
import logging
from typing import List, Sequence
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))


def _fallback_embedding(text: str, dim=EMBEDDING_DIM) -> List[float]:
    h = hashlib.sha256(text.encode()).digest()
    rnd = random.Random(int.from_bytes(h[:8], "big"))
    return [rnd.random() for _ in range(dim)]

async def get_embedding(text: str) -> List[float]:
    """Get embeddings for text, with fallback to deterministic random vectors."""
    if not text:
        raise ValueError("Cannot generate embedding for empty text")

    if OPENAI_API_KEY:
        try:
            import httpx
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            url = f"https://api.openai.com/v1/embeddings"
            payload = {"model": EMBEDDING_MODEL, "input": text}
            
            logging.info(f"Requesting embedding using model {EMBEDDING_MODEL}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(url, json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
                emb = data["data"][0]["embedding"]
                
                if len(emb) != EMBEDDING_DIM:
                    raise ValueError(f"Received embedding dimension {len(emb)} does not match expected {EMBEDDING_DIM}")
                
                logging.info("Successfully generated embedding using OpenAI API")
                return emb
        except httpx.HTTPError as e:
            logging.error(f"HTTP error during embedding request: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Error generating embedding: {str(e)}")
            raise
    else:
        logging.warning("OPENAI_API_KEY not set: using fallback embeddings (dev only)")
        try:
            emb = _fallback_embedding(text)
            logging.info("Generated fallback embedding")
            return emb
        except Exception as e:
            logging.error(f"Error generating fallback embedding: {str(e)}")
            raise
