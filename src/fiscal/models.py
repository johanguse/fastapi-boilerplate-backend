"""Database models for fiscal information and NFS-e records."""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base


class UserTaxInfo(Base):
    """Store tax information for users (Brazilian and international)."""

    __tablename__ = 'user_tax_info'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, index=True
    )

    # Country identification
    country: Mapped[str] = mapped_column(
        String(2), index=True
    )  # BR for Brazil, ISO 2-letter code for others
    is_brazilian: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Brazilian specific (required for BR)
    cpf_cnpj: Mapped[Optional[str]] = mapped_column(
        String(14), nullable=True, index=True
    )  # CPF (11) or CNPJ (14)
    inscricao_municipal: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Municipal registration (optional)

    # International specific (required for non-BR)
    nif: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Foreign Tax ID
    nif_exemption_code: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 0=NIF provided, 1=not required, 2=not provided

    # Common required fields
    full_name: Mapped[str] = mapped_column(String(255))

    # Address (required for BR, optional for international)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    complement: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    neighborhood: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city_code: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # IBGE code for BR
    state: Mapped[Optional[str]] = mapped_column(
        String(2), nullable=True
    )  # State code
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # CEP for BR, ZIP for others

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    from src.auth.models import User

    user: Mapped['User'] = relationship(back_populates='tax_info')
    nfse_records: Mapped[list['NFSe']] = relationship(
        back_populates='user_tax_info', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        doc = self.cpf_cnpj if self.is_brazilian else self.nif
        return f'<UserTaxInfo user_id={self.user_id} country={self.country} doc={doc}>'


class NFSe(Base):
    """NFS-e (Brazilian electronic service invoice) records."""

    __tablename__ = 'nfse'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    tax_info_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('user_tax_info.id', ondelete='CASCADE'),
        index=True,
    )

    # Fiscal Nacional reference
    fiscal_nacional_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    fiscal_nacional_reference: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )

    # Stripe identifiers for tracking
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )

    # Transaction type
    transaction_type: Mapped[str] = mapped_column(
        String(20), index=True
    )  # subscription, credit_purchase

    # NFS-e details
    nfse_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default='processing', index=True
    )  # processing, authorized, cancelled, error, disputed

    # Service details
    service_description: Mapped[str] = mapped_column(Text)
    product_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Clean display name

    # Values
    value_brl: Mapped[float] = mapped_column(Float)
    value_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_currency: Mapped[Optional[str]] = mapped_column(
        String(3), nullable=True
    )
    currency_code: Mapped[Optional[str]] = mapped_column(
        String(3), nullable=True
    )  # BACEN code
    exchange_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Tax calculation
    iss_rate: Mapped[float] = mapped_column(Float, default=0.02)  # 2%
    iss_value: Mapped[float] = mapped_column(Float, default=0.0)

    # Customer snapshot (denormalized for historical record)
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_email: Mapped[str] = mapped_column(String(255))
    customer_country: Mapped[str] = mapped_column(String(2))
    customer_document: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Document URLs (stored in R2/S3)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    xml_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    invoice_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Commercial invoice for international

    # Cancellation tracking
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    issued_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    from src.auth.models import User

    user: Mapped['User'] = relationship(back_populates='nfse_records')
    user_tax_info: Mapped['UserTaxInfo'] = relationship(back_populates='nfse_records')

    def __repr__(self) -> str:
        return f'<NFSe id={self.id} reference={self.fiscal_nacional_reference} status={self.status}>'
