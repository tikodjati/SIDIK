from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["admin", "distributor", "investigator"]
USERNAME_PATTERN = r"^[a-z0-9._-]{3,32}$"
PASSWORD_MIN = 10
PASSWORD_MAX = 256


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=PASSWORD_MAX)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: Role
    is_active: bool


class UserCreate(BaseModel):
    username: str = Field(pattern=USERNAME_PATTERN)
    full_name: str = Field(min_length=1, max_length=128)
    role: Role
    password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)


class UserActiveUpdate(BaseModel):
    is_active: bool


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=PASSWORD_MAX)
    new_password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)
