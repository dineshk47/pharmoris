from pydantic import BaseModel
from typing import Optional, List, Any

class DocumentCreate(BaseModel):
    title: str
    content: str

class DocumentOut(BaseModel):
    id: int
    title: str
    content: str
    score: Optional[float] = None

    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[DocumentOut]
