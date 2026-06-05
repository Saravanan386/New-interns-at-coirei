from pydantic import BaseModel
from typing import List, Optional, Literal

from datetime import datetime
from pydantic import Field

# ── Notification Schemas ──────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    """One card in the notification bell panel."""
    id: int
    type: str           # 'assignment' | 'test_score' | 'schedule' | 'system'
    title: str
    message: str
    is_read: bool
    created_at: datetime
    related_id: Optional[int]   # assignment_id / test_id for deep-linking

    class Config:
        orm_mode = True


# Chapters
class ChapterCreate(BaseModel):
    title: str
    order: int = 1

    class_content: Optional[str] = None

    key_topics: Optional[str] = None

class ChapterResponse(BaseModel):
    id: int
    title: str
    order: int

    class_content: Optional[str] = None

    key_topics: Optional[str] = None

    module_id: int

    class Config:
        from_attributes = True
# Modules
class ModuleCreate(BaseModel):
    title: str
    order: Optional[int] = 1
    course_id: int
    batch_name: Optional[str] = None

class ModuleResponse(BaseModel):
    id: int
    title: str
    order: int
    status: str
    course_id: int
    batch_name: Optional[str]
    

    chapters: List[ChapterResponse] = Field(default_factory=list)
    class Config:
        orm_mode = True

# Tests


# ── Assignment Schemas ────────────────────────────────────────────────────────

class AssignmentResourceResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_type: Optional[str]
    uploaded_at: datetime

    class Config:
        orm_mode = True


class AssignmentCreate(BaseModel):
    """Step 2 form fields (Step 1 fields come as query params or form)."""
    course_id: int
    batch_name: str
    module_id: str
    title: str
    description: Optional[str] = None
    expected_outcome: Optional[str] = None
    due_date: Optional[datetime] = None


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    expected_outcome: Optional[str] = None
    due_date: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    id: int
    course_id: int
    batch_name: str
    module_name: Optional[str] = None
    title: str
    description: Optional[str]
    expected_outcome: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    resources: List[AssignmentResourceResponse] = Field(default_factory=list)

    class Config:
        orm_mode = True


class AssignmentSubmissionCreate(BaseModel):
    """Student submission body (file upload handled separately)."""
    submission_text: Optional[str] = None


class AssignmentSubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_user_id: int
    submission_text: Optional[str]
    file_name: Optional[str]
    file_path: Optional[str]
    submitted_at: Optional[datetime]
    status: str
    grade: Optional[str]
    feedback: Optional[str]

    class Config:
        orm_mode = True


class StudentAssignmentRow(BaseModel):
    """One row in the instructor's student list for an assignment."""
    student_id: str
    student_name: str
    status: str            # 'pending' | 'submitted' | 'graded'
    submitted_at: Optional[datetime]
    grade: Optional[str]
    submission_id: Optional[int]

    class Config:
        orm_mode = True


class StudentDashboardAssignmentItem(BaseModel):
    """
    One card on the student assignment dashboard.
    status is derived: 'completed' | 'in_progress' | 'overdue'
    """
    assignment_id: int
    course_code: str          # e.g. 'AM101'
    course_name: str          # e.g. 'AI / ML Frontier Ai Engineer'
    module_name: str
    title: str
    due_date: Optional[str]   # formatted: 'Jan 15, 26'
    due_time: Optional[str]   # formatted: '9:00 - 10:00 am'  (due_date time portion)
    status: str               # 'completed' | 'in_progress' | 'overdue'
    submission_id: Optional[int]
    grade: Optional[str]

    class Config:
        orm_mode = True


# ── Chat / Q&A Schemas ────────────────────────────────────────────────────────

class ChatAuthor(BaseModel):
    id: int
    name: str
    role: str           # 'student' | 'instructor'
    student_id: Optional[str]

    class Config:
        orm_mode = True


class ChatReplyCreate(BaseModel):
    content: str


class ChatReplyResponse(BaseModel):
    id: int
    post_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    is_instructor: bool        # True when author_role == 'instructor' → blue badge
    author: ChatAuthor

    class Config:
        orm_mode = True


class ChatPostCreate(BaseModel):
    course_id: int
    batch_name: str
    content: str


class ChatPostResponse(BaseModel):
    id: int
    course_id: int
    batch_name: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_pinned: bool
    pinned_at: Optional[datetime]
    author: ChatAuthor
    is_instructor: bool        # True when author_role == 'instructor'
    like_count: int
    reply_count: int
    is_liked_by_me: bool       # whether the requesting user has liked this post
    is_bookmarked_by_me: bool  # whether the requesting user bookmarked this
    replies: List[ChatReplyResponse]= Field(default_factory=list)

    class Config:
        orm_mode = True


# ── DM (1-to-1) Chat Schemas ──────────────────────────────────────────────────

class DMMessageCreate(BaseModel):
    text: Optional[str] = None
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None


class DMMessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: str
    sender_role: str
    text: Optional[str]
    attachment_url: Optional[str]
    attachment_name: Optional[str]
    created_at: datetime
    is_deleted: bool
    like_count: int
    is_liked_by_me: bool
    is_bookmarked_by_me: bool

    class Config:
        orm_mode = True


class DMConversationResponse(BaseModel):
    id: int
    other_user_id: int
    other_user_name: str
    other_user_role: str
    other_user_student_id: Optional[str]
    unread_count: int
    last_message_text: Optional[str]
    last_message_at: Optional[datetime]

    class Config:
        orm_mode = True


class StartConversationRequest(BaseModel):
    user_id: int  # the other user to start a DM with


# ── Group Chat Schemas ────────────────────────────────────────────────────────

class GroupMessageCreate(BaseModel):
    text: Optional[str] = None
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None


class GroupMessageResponse(BaseModel):
    id: int
    group_id: int
    sender_id: int
    sender_name: str
    sender_role: str
    text: Optional[str]
    attachment_url: Optional[str]
    attachment_name: Optional[str]
    is_pinned: bool
    pinned_at: Optional[datetime]
    created_at: datetime
    is_deleted: bool
    like_count: int
    is_liked_by_me: bool
    is_bookmarked_by_me: bool

    class Config:
        orm_mode = True


class GroupMemberResponse(BaseModel):
    user_id: int
    name: str
    role: str
    student_id: Optional[str]
    avatar_url: str

    class Config:
        orm_mode = True


# ── Chat Upload Schemas ───────────────────────────────────────────────────────

class ChatUploadResponse(BaseModel):
    file_id: str
    file_url: str
    file_name: str
    file_size: int
    content_type: str


# ── User Profile Schema ───────────────────────────────────────────────────────

class UserProfileResponse(BaseModel):
    id: int
    name: str
    role: str
    student_id: Optional[str]
    email: str
    avatar_url: str

    class Config:
        orm_mode = True


# ── Q&A Visibility Schema ─────────────────────────────────────────────────────

class QAVisibilityUpdate(BaseModel):
    visibility: str  # 'public' | 'private'



class ClassroomResponse(BaseModel):
    id: int
    course_id: int
    batch_name: str
    room_name: str

    instructor_id: int | None = None
    instructor_name: str | None = None

    batch_code: str | None = None
    schedule_type: str | None = None
    start_month: str | None = None

    class Config:
        from_attributes = True
    # In app/schemas.py
class ClassroomCreate(BaseModel):
    course_id: int          # User selects this (dropdown in UI)
    room_name: str          # User types this
    # We remove 'name' or 'batch_name' from input if you want to auto-generate it, 
    # or keep it if the user types the batch name too. 
    # Assuming you want to type Batch Name too based on previous context:
    batch_name: str         

    class Config:
        json_schema_extra = {
            "example": {
                "course_id": 1,
                "batch_name": "Batch-C",
                "room_name": "AI_ML_Room"
            }
        }   


class ClassroomCreate(BaseModel):
    course_id: int
    batch_name: str
    room_name: str



# ----------  courses --------


class CourseCreate(BaseModel):
    course_code: str
    name: str
    description: str | None = None
    duration_months: int
    total_lessons: int


class CourseUpdate(BaseModel):
    course_code: str | None = None
    name: str | None = None
    description: str | None = None
    duration_months: int | None = None
    total_lessons: int | None = None


class CourseResponse(BaseModel):
    id: int
    course_code: str
    name: str
    description: str | None
    duration_months: int
    total_lessons: int

    class Config:
        orm_mode = True











# ----------   registration -----------#

import re
from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9\s\-()]{7,19}$")
ACCOUNT_STATUSES = {"active", "pending", "inactive", "suspended"}


class AddressMixin(BaseModel):
    address_line1: Optional[str] = Field(default=None, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)


class RegistrationBase(AddressMixin):
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(max_length=255)
    phone_number: str = Field(min_length=8, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    profile_image_url: Optional[str] = Field(default=None, max_length=500)
    account_status: str = "active"

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise ValueError("Invalid email address")
        return normalized

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        normalized = value.strip()
        if not PHONE_PATTERN.match(normalized):
            raise ValueError("Invalid phone number")
        return normalized

    @field_validator("account_status")
    @classmethod
    def validate_account_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ACCOUNT_STATUSES:
            raise ValueError("Invalid account status")
        return normalized


class InstructorRegistrationRequest(RegistrationBase):
    bio: Optional[str] = Field(default=None, max_length=5000)
    qualifications: Optional[List[str]] = None
    experience_years: Optional[int] = Field(default=None, ge=0, le=80)
    skills: Optional[List[str]] = None
    specialization: Optional[str] = Field(default=None, max_length=150)
    social_links: Optional[Dict[str, str]] = None


class StudentRegistrationRequest(RegistrationBase):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(default=None, max_length=50)
    education_details: Optional[Dict[str, str]] = None
    interests: Optional[List[str]] = None


class RegistrationResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    phone_number: str
    role: str
    account_status: str
    created_at: datetime

    class Config:
        from_attributes = True



class ChapterResourceResponse(BaseModel):
    id: int
    chapter_id: int
    file_name: str
    file_path: str
    file_size: str | None
    uploaded_at: datetime

    class Config:
        from_attributes = True






# --------------------------------------------------
# OPTION
# --------------------------------------------------

class OptionCreate(BaseModel):
    text: str
    is_correct: bool = False


class OptionResponse(BaseModel):
    id: int
    text: str

    class Config:
        from_attributes = True


# --------------------------------------------------
# QUESTION
# --------------------------------------------------

class QuestionCreate(BaseModel):
    text: str

    question_type: Literal[
        "mcq",
        "checkbox",
        "short_answer",
        "long_answer"
    ]

    marks: float

    expected_answer: Optional[str] = None

    options: List[OptionCreate] = []


class QuestionResponse(BaseModel):
    id: int
    text: str
    question_type: str
    marks: float

    options: List[OptionResponse] = []

    class Config:
        from_attributes = True


# --------------------------------------------------
# CREATE TEST
# --------------------------------------------------

class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None

    course_id: int
    module_id: int

    batch_name: str

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    questions: List[QuestionCreate]


class TestResponse(BaseModel):
    id: int
    title: str

    class Config:
        from_attributes = True



from typing import List, Optional
from pydantic import BaseModel


class StudentAnswerInput(BaseModel):

    question_id: int

    # MCQ
    selected_option_id: Optional[int] = None

    # Checkbox
    selected_option_ids: Optional[List[int]] = None

    # Text questions
    text_answer: Optional[str] = None


class TestSubmitRequest(BaseModel):

    answers: List[StudentAnswerInput]


class TestSubmitResponse(BaseModel):

    submission_id: int

    obtained_marks: float

    total_marks: float

    percentage: float

    is_passed: bool

class EvaluationResult(BaseModel):

    awarded_marks: float

    max_marks: float

    is_correct: Optional[bool] = None

    feedback: Optional[str] = None

# Add these Test Schemas to schemas.py

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class TestUpdate(BaseModel):
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    questions: Optional[List[QuestionCreate]] = None

# ------------------------------

# Student Test Detail View

# ------------------------------

class StudentRowResponse(BaseModel):
    sno: int
    student_id: str
    student_name: str


    start_time: Optional[str]
    end_time: Optional[str]

    status: str

    mark: Optional[float]

    submission_id: Optional[int]

    class Config:
        orm_mode = True


class TestDetailResponse(BaseModel):


    test_id: int

    title: str

    module_name: Optional[str]

    date: Optional[str]

    duration_minutes: Optional[int]

    start_time: Optional[str]

    end_time: Optional[str]

    total_enrolled: int

    total_submitted: int

    total_passed: int

    total_failed: int

    students: List[StudentRowResponse]

    class Config:
        orm_mode = True


# ------------------------------

# Submission Review

# ------------------------------

class AnswerReviewItem(BaseModel):


    question_id: int

    question_text: str

    selected_option_id: Optional[int]

    selected_option_text: Optional[str]

    is_correct: Optional[bool]

    correct_option_text: Optional[str]

    class Config:
        orm_mode = True


class SubmissionReviewResponse(BaseModel):


    submission_id: int

    test_id: int

    student_id: str

    student_name: str

    started_at: Optional[datetime]

    submitted_at: Optional[datetime]

    score: Optional[float]

    is_passed: Optional[bool]

    status: str

    answers: List[AnswerReviewItem]

    class Config:
        orm_mode = True

class AnswerReviewItem(BaseModel):

    question_id: int

    question_text: str

    question_type: str

    student_answer: Optional[str]

    expected_answer: Optional[str]

    awarded_marks: float

    max_marks: float

    feedback: Optional[str]

class AnswerReviewItem(BaseModel):

    question_id: int
    question_text: str
    question_type: str

    student_answer: Optional[str]
    expected_answer: Optional[str]

    awarded_marks: float
    max_marks: float

    feedback: Optional[str]


class SubmissionReviewResponse(BaseModel):

    submission_id: int

    test_id: int

    student_id: str

    student_name: str

    started_at: Optional[datetime]

    submitted_at: Optional[datetime]

    obtained_marks: float

    total_marks: float

    percentage: float

    is_passed: bool

    status: str

    answers: List[AnswerReviewItem]