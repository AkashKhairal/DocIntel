from sqlalchemy import Column, Integer, ForeignKey, String, BigInteger, DateTime, func
from app.db.base import Base


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String, nullable=False)
    tokens_used = Column(Integer, default=0)
    embedding_tokens = Column(Integer, default=0)
    documents_indexed = Column(Integer, default=0)
    queries_executed = Column(Integer, default=0)
    storage_used = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
