from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class AdminCreate(BaseModel):
    company_id: UUID
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr | None = None
    password: str = Field(min_length=12, max_length=128)

class AdminUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=12, max_length=128)
    is_active: bool | None = None

class AdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID | None
    username: str
    email: str | None
    role: str
    is_active: bool
