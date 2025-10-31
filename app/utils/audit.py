import os
import hmac
import hashlib
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.documents.models import AuditLog
from app.db.initdb import AsyncSessionLocal
from dotenv import load_dotenv

load_dotenv()
HMAC_KEY = os.getenv("HMAC_KEY", "replace_with_secure_key")

def hash_user_id(user_id: str) -> str:
    if not user_id:
        return ""
    return hmac.new(HMAC_KEY.encode(), user_id.encode(), hashlib.sha256).hexdigest()

async def record_audit(session: AsyncSession, user_id: Optional[str], action: str, metadata: Optional[Dict[str, Any]] = None):
    hashed = hash_user_id(user_id) if user_id else ""
    log = AuditLog(hashed_user_id=hashed, action=action, metadata=metadata or {})
    session.add(log)
    await session.commit()
