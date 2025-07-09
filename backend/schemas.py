from pydantic import BaseModel, EmailStr
import enum,datetime
from typing import Optional

class UserRole(str, enum.Enum):
    student = 'student'
    lecturer = "lecturer"
    admin = "admin"

# ---------- User Schemas ----------
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str
    student_id: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    student_id: Optional[str] = None
    class Config:
        from_attributes = True

class UserUpdate(UserBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    student_id: Optional[str] = None
    class Config:
        from_attributes = True

# ---------- Course Schemas ----------

class CourseBase(BaseModel):
    title: str
    code: str

class CourseCreate(CourseBase):
    lecturer_id: int

class CourseResponse(CourseBase):
    id: int
    lecturer_id: int

    class Config:
        from_attributes = True

# ----- Review Schemas -----

class ReviewBase(BaseModel):
    txt:str
    code:str

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: int
    student_id: int
    student_name: str
    course_title: str
    clean_text: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class SentimentSummary(BaseModel):
    course_id: int
    positive: int
    negative: int
    neutral: int
    total: int
    sentiment_distribution: dict