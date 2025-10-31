import os
import asyncio
from sqlalchemy import text
from app.db.initdb import engine
from app.utils.embeddings import get_embedding
from dotenv import load_dotenv

load_dotenv()
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "10"))

async def fill_embeddings(limit=None):
    async with engine.begin() as conn:
        # Select ids and content for documents missing embeddings
        sel_sql = "SELECT id, content FROM documents WHERE embedding IS NULL LIMIT :limit"
        while True:
            params = {"limit": limit or BATCH_SIZE}
            result = await conn.execute(text(sel_sql), params)
            rows = result.fetchall()
            if not rows:
                print("No more documents with null embeddings.")
                break
            for row in rows:
                doc_id = row[0]
                content = row[1]
                try:
                    emb = await get_embedding(content)
                    if isinstance(emb, (list, tuple)):
                        emb_str = '[' + ','.join(str(float(x)) for x in emb) + ']'
                    else:
                        emb_str = str(emb)
                    upd_sql = text("UPDATE documents SET embedding = :emb::vector WHERE id = :id")
                    await conn.execute(upd_sql, {"emb": emb_str, "id": doc_id})
                    print(f"Updated embedding for doc id={doc_id}")
                except Exception as e:
                    print(f"Failed to compute/update embedding for id={doc_id}: {e}")
            if limit:
                break

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', '-n', type=int, default=None)
    args = parser.parse_args()
    asyncio.run(fill_embeddings(limit=args.limit))
