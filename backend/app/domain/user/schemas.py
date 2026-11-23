from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    business_id: int
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    full_name: str = Field(
        min_length=1,
        max_length=150,
    )


class UserApiCreate(BaseModel):
    email: EmailStr
    # Compatibilidad con clientes previos; se ignora al invitar trabajadores.
    # El invitado establece su propia contraseña desde el correo.
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str = Field(
        min_length=1,
        max_length=150,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class UserRead(BaseModel):
    id: int
    business_id: int
    role: str
    email_verified: bool
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class WorkerStatusUpdate(BaseModel):
    is_active: bool

    model_config = ConfigDict(extra="forbid")
