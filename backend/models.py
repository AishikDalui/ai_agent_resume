from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class OTPRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=6, max_length=20)


class OTPVerify(BaseModel):
    email: EmailStr
    phone: str
    otp: str = Field(..., min_length=4, max_length=8)


class BookingOTPRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class BookingOTPVerify(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=8)


class BookingCreateEventRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    start_at: datetime
    duration_minutes: int = Field(default=30, ge=15, le=180)
    notes: str = Field(default="", max_length=1000)


class BookingCreateEventResponse(BaseModel):
    event_id: str
    event_link: str
    meet_link: str
    start_at: datetime
    end_at: datetime
    email_status: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=200)


class ResumeUploadResponse(BaseModel):
    message: str
    imagekit_url: str
    active_pdf_path: str
    extracted_chars: int


class ProjectItem(BaseModel):
    id: int
    title: str
    description: str
    image_url: str = ""
    image_file_id: str = ""
    project_link: str = ""
    sort_order: int


class SiteContentResponse(BaseModel):
    about_me: str
    contact_heading: str
    demo_video_url: str
    contact_message: str
    skills: list[str]
    projects: list[ProjectItem]


class AboutUpdateRequest(BaseModel):
    about_me: str = Field(..., min_length=20, max_length=5000)


class ContactUpdateRequest(BaseModel):
    contact_heading: str = Field(..., min_length=3, max_length=80)
    contact_message: str = Field(..., min_length=10, max_length=1200)


class DemoVideoUpdateRequest(BaseModel):
    demo_video_url: str = Field(..., min_length=10, max_length=1200)


class VoiceCallSettingsResponse(BaseModel):
    auto_call_enabled: bool
    auto_call_from_number: str


class VoiceCallSettingsUpdateRequest(BaseModel):
    auto_call_enabled: bool = False
    auto_call_from_number: str = Field(default="", max_length=40)


class SkillsUpdateRequest(BaseModel):
    skills: list[str] = Field(...)


class ProjectUpsertRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=160)
    description: str = Field(..., min_length=10, max_length=2000)
    image_url: str = Field(default="", max_length=800)
    image_file_id: str = Field(default="", max_length=200)
    project_link: str = Field(default="", max_length=1200)
    sort_order: int = Field(default=0, ge=0, le=100)


class ProjectImageUploadResponse(BaseModel):
    image_url: str
    image_file_id: str


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    reply: str
    created_at: datetime


class UserSheetEntry(BaseModel):
    name: str
    email: EmailStr
    phone: str
    created_at: datetime
