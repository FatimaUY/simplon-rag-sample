"""fix_uuid_types
Revision ID: 6a6d4579355d
Revises: 0002
Create Date: 2026-04-07 17:51:58.489805
"""
from typing import Sequence, Union
from alembic import op
from rag.config.settings import get_settings

revision: str = '6a6d4579355d'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    schema = get_settings().postgres_schema
    op.drop_index('document_chunks_embedding_idx', table_name='document_chunks', schema=schema)
    op.drop_index('messages_conversation_id_idx', table_name='messages', schema=schema)

def downgrade() -> None:
    schema = get_settings().postgres_schema
    op.create_index('messages_conversation_id_idx', 'messages', ['conversation_id', 'created_at'], schema=schema)
    op.create_index('document_chunks_embedding_idx', 'document_chunks', ['embedding'], schema=schema,
        postgresql_ops={'embedding': 'vector_cosine_ops'},
        postgresql_with={'m': '16', 'ef_construction': '64'},
        postgresql_using='hnsw')
