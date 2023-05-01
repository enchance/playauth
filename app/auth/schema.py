from pydantic import BaseModel
from uuid import UUID


class AccountResponse(BaseModel):
    id: UUID
    display: str
    email: str