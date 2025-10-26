"""Pydantic models for Better Auth compatibility."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr


class EmailSignInRequest(BaseModel):
    email: EmailStr
    password: str
    callbackURL: Optional[str] = None


class EmailSignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    callbackURL: Optional[str] = None


class AuthResponse(BaseModel):
    user: Dict[str, Any]
    session: Dict[str, Any]


class ErrorResponse(BaseModel):
    error: str
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    redirectTo: Optional[str] = None
