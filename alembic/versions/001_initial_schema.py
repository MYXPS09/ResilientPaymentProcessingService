"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-05-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('payments',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('payment_num', sa.String(length=64), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('gateway_ref', sa.String(length=128), nullable=True),
        sa.Column('gateway_status', sa.String(length=32), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('payer_name', sa.String(length=128), nullable=True),
        sa.Column('payer_email', sa.String(length=128), nullable=True),
        sa.Column('payer_phone', sa.String(length=32), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('webhook_received_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('modified_by', sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_idempotency_key'), 'payments', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_payments_payment_num'), 'payments', ['payment_num'], unique=True)

    op.create_table('payment_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('payment_id', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('from_status', sa.String(length=32), nullable=True),
        sa.Column('to_status', sa.String(length=32), nullable=True),
        sa.Column('gateway_ref', sa.String(length=128), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('modified_by', sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_events_payment_id'), 'payment_events', ['payment_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_payment_events_payment_id'), table_name='payment_events')
    op.drop_table('payment_events')
    op.drop_index(op.f('ix_payments_payment_num'), table_name='payments')
    op.drop_index(op.f('ix_payments_idempotency_key'), table_name='payments')
    op.drop_table('payments')
