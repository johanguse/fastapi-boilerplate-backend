"""Add fiscal tables for NFS-e management

Revision ID: add_fiscal_tables
Revises: 0b79c1911baa
Create Date: 2026-02-06

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_fiscal_tables'
down_revision: Union[str, None] = '0b79c1911baa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:  # noqa: PLR0915
    # Create user_tax_info table
    op.create_table(
        'user_tax_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('is_brazilian', sa.Boolean(), nullable=False),
        sa.Column('cpf_cnpj', sa.String(length=14), nullable=True),
        sa.Column('inscricao_municipal', sa.String(length=50), nullable=True),
        sa.Column('nif', sa.String(length=50), nullable=True),
        sa.Column('nif_exemption_code', sa.Integer(), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('number', sa.String(length=20), nullable=True),
        sa.Column('complement', sa.String(length=100), nullable=True),
        sa.Column('neighborhood', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('city_code', sa.Integer(), nullable=True),
        sa.Column('state', sa.String(length=2), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_user_tax_info_user_id', 'user_tax_info', ['user_id'])
    op.create_index('ix_user_tax_info_country', 'user_tax_info', ['country'])
    op.create_index('ix_user_tax_info_is_brazilian', 'user_tax_info', ['is_brazilian'])
    op.create_index('ix_user_tax_info_cpf_cnpj', 'user_tax_info', ['cpf_cnpj'])

    # Create nfse table
    op.create_table(
        'nfse',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tax_info_id', sa.Integer(), nullable=False),
        sa.Column('fiscal_nacional_id', sa.String(length=100), nullable=True),
        sa.Column('fiscal_nacional_reference', sa.String(length=100), nullable=False),
        sa.Column('stripe_invoice_id', sa.String(length=100), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(length=100), nullable=True),
        sa.Column('stripe_charge_id', sa.String(length=100), nullable=True),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('nfse_number', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('service_description', sa.Text(), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=True),
        sa.Column('value_brl', sa.Float(), nullable=False),
        sa.Column('value_usd', sa.Float(), nullable=True),
        sa.Column('original_amount', sa.Float(), nullable=True),
        sa.Column('original_currency', sa.String(length=3), nullable=True),
        sa.Column('currency_code', sa.String(length=3), nullable=True),
        sa.Column('exchange_rate', sa.Float(), nullable=True),
        sa.Column('iss_rate', sa.Float(), nullable=False),
        sa.Column('iss_value', sa.Float(), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=False),
        sa.Column('customer_country', sa.String(length=2), nullable=False),
        sa.Column('customer_document', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('pdf_path', sa.String(length=255), nullable=True),
        sa.Column('xml_path', sa.String(length=255), nullable=True),
        sa.Column('invoice_url', sa.Text(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tax_info_id'], ['user_tax_info.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fiscal_nacional_id'),
        sa.UniqueConstraint('fiscal_nacional_reference')
    )
    op.create_index('ix_nfse_user_id', 'nfse', ['user_id'])
    op.create_index('ix_nfse_tax_info_id', 'nfse', ['tax_info_id'])
    op.create_index('ix_nfse_stripe_invoice_id', 'nfse', ['stripe_invoice_id'])
    op.create_index('ix_nfse_stripe_payment_intent_id', 'nfse', ['stripe_payment_intent_id'])
    op.create_index('ix_nfse_stripe_charge_id', 'nfse', ['stripe_charge_id'])
    op.create_index('ix_nfse_transaction_type', 'nfse', ['transaction_type'])
    op.create_index('ix_nfse_nfse_number', 'nfse', ['nfse_number'])
    op.create_index('ix_nfse_status', 'nfse', ['status'])


def downgrade() -> None:
    op.drop_table('nfse')
    op.drop_table('user_tax_info')
