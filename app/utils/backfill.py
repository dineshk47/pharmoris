import os
from typing import Optional, List, Tuple
from sqlalchemy import text
from app.db.initdb import engine
from app.utils.embeddings import get_embedding
from sqlalchemy.ext.asyncio import AsyncConnection
import logging

logger = logging.getLogger(__name__)

async def update_document_embeddings(
    conn: AsyncConnection,
    batch_size: int = 10,
    limit: Optional[int] = None
) -> Tuple[int, List[int]]:
    """Update embeddings for documents where they are NULL.
    
    Args:
        conn: SQLAlchemy async connection
        batch_size: How many documents to process per batch
        limit: Optional maximum number of documents to process
    
    Returns:
        Tuple of (success_count, failed_ids)
    """
    success_count = 0
    failed_ids = []
    
    # Select ids and content for documents missing embeddings
    sel_sql = "SELECT id, content FROM documents WHERE embedding IS NULL LIMIT :limit"
    while True:
        params = {"limit": limit or batch_size}
        result = await conn.execute(text(sel_sql), params)
        rows = result.fetchall()
        if not rows:
            logger.info("No more documents with null embeddings.")
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
                success_count += 1
                logger.info(f"Updated embedding for doc id={doc_id}")
            except Exception as e:
                logger.error(f"Failed to compute/update embedding for id={doc_id}: {e}")
                failed_ids.append(doc_id)
                
        if limit and (success_count + len(failed_ids)) >= limit:
            break
            
    return success_count, failed_ids