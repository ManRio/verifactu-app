from pydantic import BaseModel, EmailStr, Field

from app.domain.business.schemas import BusinessCreate


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class RegistrationUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    full_name: str = Field(
        min_length=1,
        max_length=150,
    )


class RegistrationRequest(BaseModel):
    business: BusinessCreate
    user: RegistrationUserCreate


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegistrationPendingRead(BaseModel):
    message: str
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class OperationMessage(BaseModel):
    message: str
