"""Initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-03-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False,
                  unique=True, index=True),
        sa.Column('active', sa.Boolean(), nullable=False,
                  server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey(
            'tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey(
            'tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey(
            'organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('email', sa.String(), nullable=False,
                  unique=True, index=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default=sa.text('true')),
        sa.Column('role', sa.String(), nullable=False,
                  server_default='viewer'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey(
            'tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey(
            'organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey(
            'users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('drive_file_id', sa.String(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('size', sa.BigInteger(), nullable=True),
        sa.Column('drive_link', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey(
            'documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey(
            'tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('qdrant_point_id', sa.String(), nullable=True, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    op.create_table(
        'queries',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey(
            'tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey(
            'users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('response', sa.JSON(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('token_usage', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    op.create_table(
        'usage_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey(
            'tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey(
            'users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('tokens_used', sa.Integer(),
                  nullable=False, server_default='0'),
        sa.Column('embedding_tokens', sa.Integer(),
                  nullable=False, server_default='0'),
        sa.Column('documents_indexed', sa.Integer(),
                  nullable=False, server_default='0'),
        sa.Column('queries_executed', sa.Integer(),
                  nullable=False, server_default='0'),
        sa.Column('storage_used', sa.BigInteger(),
                  nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey(
            'tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False, unique=True),
        sa.Column('rate_limit', sa.Integer(),
                  nullable=False, server_default='1000'),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )

    op.create_table(
        'google_integrations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey(
            'tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey(
            'users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('access_token', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=False),
        sa.Column('expiry', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scope', sa.String(), nullable=True),
        sa.Column('webhook_channel_id', sa.String(),
                  nullable=True, index=True),
        sa.Column('page_token', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )


def downgrade():
    op.drop_table('google_integrations')
    op.drop_table('api_keys')
    op.drop_table('usage_logs')
    op.drop_table('queries')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('users')
    op.drop_table('organizations')
    op.drop_table('tenants')
