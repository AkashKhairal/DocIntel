import asyncio
import logging
import pytest
from app.db.session import async_session_local
from app.models import Tenant, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_db():
    try:
        async with async_session_local() as session:
            # Check tenants
            from sqlalchemy import text
            res = await session.execute(text("SELECT count(*) FROM tenants"))
            count = res.scalar()
            logger.info(f"Tenants in DB: {count}")

            # Check documents
            res = await session.execute(text("SELECT count(*) FROM documents"))
            doc_count = res.scalar()
            logger.info(f"Documents in DB (raw SQL): {doc_count}")

            # Check via ORM
            from sqlalchemy.future import select
            res = await session.execute(select(Document))
            docs = res.scalars().all()
            logger.info(f"Documents in DB (ORM): {len(docs)}")

    except Exception as e:
        logger.error(f"DB Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_db())
