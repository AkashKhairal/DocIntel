from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger, JSON, func
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey(
        "organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="SET NULL"), nullable=True)
    drive_file_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    size = Column(BigInteger, nullable=True)
    drive_link = Column(String, nullable=True)
    doc_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), nullable=True)
