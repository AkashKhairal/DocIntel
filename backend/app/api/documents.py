from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_tenant_context
from app.db.session import get_db
from app.models.document import Document
from rag.retriever import delete_by_file_id

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/")
async def list_documents(tenant_context=Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    q = await db.execute(
        text("SELECT * FROM documents WHERE tenant_id = :tenant_id ORDER BY created_at DESC"),
        {"tenant_id": tenant_context["tenant_id"]},
    )
    docs = q.mappings().all()
    return {"total": len(docs), "documents": docs}


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, tenant_context=Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc or doc.tenant_id != tenant_context["tenant_id"]:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete vector store entries in Qdrant by file id
    try:
        if doc.drive_file_id:
            delete_by_file_id(doc.drive_file_id)
    except Exception as e:
        # log and continue with document deletion to avoid stale DB state
        import logging
        logging.getLogger(__name__).warning(
            f"Qdrant cleanup failed for document {doc_id} drive_file_id={doc.drive_file_id}: {e}")

    await db.delete(doc)
    await db.commit()

    return {"status": "deleted", "document_id": doc_id}
