from sqlalchemy import Column, Integer, ForeignKey, String, JSON, DateTime, func
from app.db.base import Base


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="SET NULL"), nullable=True)
    question = Column(String, nullable=False)
    response = Column(JSON, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    token_usage = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
