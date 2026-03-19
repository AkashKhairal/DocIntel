import asyncio
import logging
from app.db.session import async_session_local
from app.models import Document, Tenant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def manual_insert():
    try:
        async with async_session_local() as session:
            # First, make sure tenant 1 exists
            from sqlalchemy.future import select
            res = await session.execute(select(Tenant).where(Tenant.id == 1))
            t = res.scalar_one_or_none()
            if not t:
                logger.error("Tenant 1 not found! DB might be empty or wrong.")
                return

            logger.info(f"Found tenant: {t.name}")

            # Insert document
            doc = Document(
                tenant_id=1,
                drive_file_id="test_file_id_" + str(asyncio.get_event_loop().time()),
                name="Manual Test Doc",
                mime_type="application/pdf",
                size=1234,
                doc_metadata={"test": True}
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            logger.info(f"Manually inserted document ID: {doc.id}")

            # Verify immediately
            res = await session.execute(select(Document).where(Document.id == doc.id))
            doc_verify = res.scalar_one_or_none()
            if doc_verify:
                logger.info("Verification successful: Document found in DB!")
            else:
                logger.error("Verification FAILED: Document NOT found in DB after commit!")

            # List ALL documents
            res = await session.execute(select(Document))
            all_docs = res.scalars().all()
            logger.info(f"ALL DOCUMENTS IN DB: {[(d.id, d.name) for d in all_docs]}")

    except Exception as e:
        logger.error(f"Manual insert failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(manual_insert())
