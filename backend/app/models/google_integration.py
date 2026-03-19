from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON, func
from app.db.base import Base


class GoogleIntegration(Base):
    __tablename__ = "google_integrations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey(
        "tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="SET NULL"), nullable=True, index=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expiry = Column(DateTime(timezone=True), nullable=False)
    scope = Column(String, nullable=True)
    webhook_channel_id = Column(String, nullable=True, index=True)
    page_token = Column(String, nullable=True)
    monitored_folders = Column(JSON, nullable=True)  # List of folder IDs to sync
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())
