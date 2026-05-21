"""Create conversations and messages tables
Revision ID: 0002
Revises: 0001
Create Date: 2026-04-07
"""
from alembic import op
from rag.config.settings import get_settings

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    schema = get_settings().postgres_schema
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS {schema}.conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            metadata JSONB NOT NULL DEFAULT '{{}}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS {schema}.messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id UUID NOT NULL REFERENCES {schema}.conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            sources JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute(f"""
        CREATE INDEX IF NOT EXISTS messages_conversation_id_idx
            ON {schema}.messages (conversation_id, created_at)
    """)

def downgrade() -> None:
    schema = get_settings().postgres_schema
    op.execute(f"DROP TABLE IF EXISTS {schema}.messages")
    op.execute(f"DROP TABLE IF EXISTS {schema}.conversations")
