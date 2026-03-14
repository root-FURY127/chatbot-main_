from pydantic import BaseModel, EmailStr
from typing import Optional

class UserResponse(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    aadhaar: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None
    passport: Optional[str] = None
    driving_license: Optional[str] = None
    account_number: Optional[str] = None

class UserUpdate(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None