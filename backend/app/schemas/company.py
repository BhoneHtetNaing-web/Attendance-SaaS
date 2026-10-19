from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    code: str = Field(min_length=2, max_length=50)
    phone: str | None = None
    email: str | None = None
    address: str | None = None

class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    code: str | None = Field(default=None, min_length=2, max_length=50)
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    is_active: bool | None = None

class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    phone: str | None
    email: str | None
    address: str | None
    is_active: bool
