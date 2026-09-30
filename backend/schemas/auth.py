from typing import Optional
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    email: str
    role: str = Field(..., description="'teacher' or 'student' (or uppercase TEACHER / STUDENT)")
    student_id: Optional[str] = None
    authenticated: bool = True
    created_at: Optional[str] = None

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, description="User full name")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=4, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")
    role: str = Field(..., description="Target role: 'teacher' or 'student'")
    student_id: Optional[str] = Field(None, description="Optional custom student ID e.g. STU001")

class LoginRequest(BaseModel):
    email: Optional[str] = Field(None, description="User email or Student ID / Teacher ID")
    identifier: Optional[str] = Field(None, description="User email or Student ID / Teacher ID")
    password: str = Field(..., description="User password")
    role: Optional[str] = Field(None, description="Target role: 'teacher' or 'student'")

class LoginResponse(BaseModel):
    token: str
    user_id: str
    name: str
    role: str
    authenticated: bool = True
    user: UserProfile
    message: str = "Authentication successful"
