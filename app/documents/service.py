import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.documents.models import Document
from app.documents.schemas import DocumentCreate, DocumentOut, SearchRequest, SearchResponse
from app.utils.embeddings import get_embedding
from app.utils.audit import record_audit
from fastapi import HTTPException

class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(self, payload: DocumentCreate) -> DocumentOut:
        """Create a new document and compute its embedding."""
        doc = Document(title=payload.title, content=payload.content)
        
        emb_str = None
        try:
            embedding = await get_embedding(doc.content)
            if isinstance(embedding, (list, tuple)):
                try:
                    emb_str = '[' + ','.join(str(float(x)) for x in embedding) + ']'
                except Exception:
                    emb_str = '[' + ','.join(str(x) for x in embedding) + ']'
            else:
                emb_str = str(embedding)

            logging.info("✅ Embedding computed successfully (prepared as string)")
        except Exception as e:
            logging.error(f"Direct embedding computation failed: {str(e)}")
            try:
                from app.utils.tasks import precompute_embeddings
                precompute_embeddings.apply_async(kwargs={'limit': 1}, countdown=1)
                logging.info("Background embedding computation scheduled")
            except Exception as e:
                logging.error(f"Could not schedule background embedding computation: {str(e)}")
                doc.embedding = None

        try:
            if emb_str is not None:
                self.session.add(doc)
                await self.session.commit()
                await self.session.refresh(doc)

                try:
                    await self.session.execute(
                        text("UPDATE documents SET embedding = :emb::vector WHERE id = :id"),
                        {"emb": emb_str, "id": doc.id}
                    )
                    await self.session.commit()
                    await self.session.refresh(doc)
                    logging.info("Document saved and embedding updated via raw SQL")
                except Exception as e:
                    logging.error(f"Failed to update embedding via raw SQL: {str(e)}")
            else:
                self.session.add(doc)
                await self.session.commit()
                await self.session.refresh(doc)

            logging.info(f"Document saved successfully. Has embedding: {doc.embedding is not None}")
        except Exception as e:
            logging.error(f"Failed to save document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save document: {str(e)}")

        return DocumentOut.from_orm(doc)

    async def search_documents(self, req: SearchRequest) -> SearchResponse:
        """Search for documents using vector similarity with fallback to text search."""
        if not req.query:
            raise HTTPException(400, "query is required")

        try:
            query_embedding = await get_embedding(req.query)
        except Exception as e:
            raise HTTPException(500, f"Could not generate embedding for search query: {str(e)}")

        await record_audit(self.session, req.user_id, action="search_documents", 
                         metadata={"query_length": len(req.query)})

        try:
            results = await self._vector_search(query_embedding)
        except Exception as e:
            logging.error(f"Vector search failed: {str(e)}")
            results = await self._fallback_text_search(req.query)

        return SearchResponse(results=[DocumentOut(**r) for r in results])

    async def _vector_search(self, query_embedding: list) -> list:
        """Perform vector similarity search."""
        sql = text("""
            SELECT id, title, content, (embedding <=> :query_embedding::vector) as distance
            FROM documents
            WHERE embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT 3
        """)
        result = await self.session.execute(sql.bindparams(query_embedding=query_embedding))
        rows = result.fetchall()

        return [
            {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "score": float(row[3]) if row[3] is not None else None
            }
            for row in rows
        ]

    async def _fallback_text_search(self, query: str) -> list:
        """Perform text-based search as fallback."""
        sql = text("""
            SELECT id, title, content, 0 as distance
            FROM documents
            WHERE to_tsvector('english', content) @@ plainto_tsquery('english', :query)
            LIMIT 3
        """)
        result = await self.session.execute(sql.bindparams(query=query))
        rows = result.fetchall()

        return [
            {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "score": None
            }
            for row in rows
        ]