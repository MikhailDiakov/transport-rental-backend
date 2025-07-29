from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.models.role import RoleEnum
from app.schemas.validators import (
    validate_password_complexity,
    validate_username_length,
)


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("username")
    def username_length(cls, v: str) -> str:
        return validate_username_length(v)

    @field_validator("password")
    def password_complexity(cls, v):
        return validate_password_complexity(v)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    role_id: Optional[int]

    model_config = dict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None
    confirm_password: Optional[str] = None

    @field_validator("new_password")
    def password_complexity(cls, v):
        if v is None:
            return v
        return validate_password_complexity(v)

    @model_validator(mode="after")
    def passwords_match(cls, values):
        if values.new_password or values.confirm_password:
            if values.new_password != values.confirm_password:
                raise ValueError("Passwords do not match")
            if not values.old_password:
                raise ValueError("Old password is required to change password")
        return values


class AdminUserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[RoleEnum] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    def password_complexity(cls, v: str) -> str:
        return validate_password_complexity(v)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
