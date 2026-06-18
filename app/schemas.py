from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Auth Schemas
class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

# Settings Schemas
class UserSettingsOut(BaseModel):
    id: int
    user_id: int
    default_provider: str
    default_model: str
    fallback_enabled: bool
    theme: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserSettingsUpdate(BaseModel):
    default_provider: Optional[str] = None
    default_model: Optional[str] = None
    fallback_enabled: Optional[bool] = None
    theme: Optional[str] = None

# Chat Schemas
class ChatSessionCreate(BaseModel):
    title: str = Field(default="New Chat", max_length=255)

class ChatSessionOut(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    role: str
    content: str
    provider: Optional[str] = None
    model: Optional[str] = None

class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    user_id: int
    role: str
    content: str
    provider: Optional[str] = None
    model: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessagePostRequest(BaseModel):
    session_id: int
    content: str
    provider: str  # "auto" or provider name
    model: str     # "auto" or model name

class ChatResponse(BaseModel):
    model_config = {
        "protected_namespaces": ()
    }
    answer: str
    provider_used: str
    model_used: str
    fallback_used: bool
    response_time_ms: int
    tokens_input: int
    tokens_output: int
    chat_message_id: int

# Image Schemas
class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    provider: str = Field(default="pollinations")
    model: str = Field(default="flux")

class ImageGenerationOut(BaseModel):
    id: int
    user_id: int
    provider: str
    model: str
    prompt: str
    image_url_or_path: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Usage / Logs Schemas
class AIUsageLogOut(BaseModel):
    id: int
    user_id: int
    provider: str
    model: str
    status: str
    error_message: Optional[str]
    tokens_input: int
    tokens_output: int
    response_time_ms: int
    fallback_used: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UsageSummaryOut(BaseModel):
    total_chats: int
    total_messages: int
    total_requests: int
    total_images: int
    most_used_provider: Optional[str]
    fallback_count: int
    avg_response_time_ms: float
    provider_usage: Dict[str, int]
    daily_usage: List[Dict[str, Any]]
