from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    capacity: int
    remaining: int
    model_config = ConfigDict(from_attributes=True)


class EnrollmentOut(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_name: str
    created_at: datetime


class SelectionResponse(BaseModel):
    status: Literal["selected", "queued", "already_enrolled", "full", "rejected"]
    message: str
    job_id: str | None = None


class JobStatus(BaseModel):
    job_id: str
    status: str
    message: str | None = None
    course_id: int | None = None


class DeviceInfo(BaseModel):
    device_id: str
    last_seen: int
    request_count: int
