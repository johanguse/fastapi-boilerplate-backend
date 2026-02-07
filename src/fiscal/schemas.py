"""Pydantic schemas for fiscal/tax endpoints."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserTaxInfoBase(BaseModel):
    """Base schema for user tax information."""

    country: str = Field(..., min_length=2, max_length=2)
    full_name: str = Field(..., min_length=1, max_length=255)

    # Brazilian specific
    cpf_cnpj: Optional[str] = None
    inscricao_municipal: Optional[str] = None

    # International specific
    nif: Optional[str] = None
    nif_exemption_code: Optional[int] = Field(None, ge=0, le=2)

    # Address
    address: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    city_code: Optional[int] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class UserTaxInfoCreate(UserTaxInfoBase):
    """Schema for creating user tax information."""

    pass


class UserTaxInfoUpdate(UserTaxInfoBase):
    """Schema for updating user tax information."""

    country: Optional[str] = Field(None, min_length=2, max_length=2)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)


class UserTaxInfoResponse(UserTaxInfoBase):
    """Schema for tax information response."""

    id: int
    user_id: int
    is_brazilian: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class NFSeBase(BaseModel):
    """Base schema for NFS-e records."""

    status: str
    nfse_number: Optional[str] = None
    service_description: str
    product_name: Optional[str] = None
    value_brl: float
    value_usd: Optional[float] = None
    customer_name: str
    customer_email: EmailStr
    customer_country: str


class NFSeResponse(NFSeBase):
    """Schema for NFS-e response."""

    id: int
    user_id: int
    fiscal_nacional_reference: str
    transaction_type: str
    issued_at: Optional[str] = None
    created_at: str
    updated_at: str
    pdf_path: Optional[str] = None
    xml_path: Optional[str] = None
    invoice_url: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class NFSeListResponse(BaseModel):
    """Schema for listing NFS-e records."""

    items: list[NFSeResponse]
    total: int
    page: int
    page_size: int


class BrazilianCity(BaseModel):
    """Schema for Brazilian city from IBGE API."""

    id: int
    nome: str
    microrregiao: dict
    regiao_imediata: dict


class BrazilianState(BaseModel):
    """Schema for Brazilian state."""

    code: str
    name: str
