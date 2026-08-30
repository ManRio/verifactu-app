from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class BusinessBase(BaseModel):
    legal_name: str = Field(min_length=1, max_length=150)
    tax_id: str = Field(min_length=1, max_length=20)
    trade_name: str | None = Field(default=None, max_length=150)
    address: str = Field(min_length=1, max_length=255)
    postal_code: str = Field(min_length=1, max_length=10)
    city: str = Field(min_length=1, max_length=100)
    province: str = Field(min_length=1, max_length=100)
    country_code: str = Field(default="ES", min_length=2, max_length=2)


class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BaseModel):
    legal_name: str | None = Field(default=None, min_length=1, max_length=150)
    tax_id: str | None = Field(default=None, min_length=1, max_length=20)
    trade_name: str | None = Field(default=None, max_length=150)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    postal_code: str | None = Field(default=None, min_length=1, max_length=10)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    province: str | None = Field(default=None, min_length=1, max_length=100)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)

class BusinessRead(BusinessBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)