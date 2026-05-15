from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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
    order: Optional[int] = 1

class ChapterResponse(BaseModel):
    id: int
    title: str
    order: int
    module_id: int

    class Config:
        orm_mode = True

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
    
    chapters: List[ChapterResponse] = []

    class Config:
        orm_mode = True

# Tests
class OptionCreate(BaseModel):
    text: str
    is_correct: bool = False

class OptionResponse(BaseModel):
    id: int
    text: str
    is_correct: bool

    class Config:
        orm_mode = True

class QuestionCreate(BaseModel):
    text: str
    options: List[OptionCreate]

class QuestionResponse(BaseModel):
    id: int
    text: str
    options: List[OptionResponse]

    class Config:
        orm_mode = True

class TestCreate(BaseModel):
    title: str
    course_id: int
    batch_name: str
    module_name: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    questions: Optional[List[QuestionCreate]] = None

class TestUpdate(BaseModel):
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    questions: Optional[List[QuestionCreate]] = None

class TestResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    course_id: int
    batch_name: str
    module_name: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime
    
    questions: List[QuestionResponse] = []

    class Config:
        orm_mode = True


# ── Submission Schemas ───────────────────────────────────────────────────────

class StudentAnswerCreate(BaseModel):
    """One answer entry when a student submits a test."""
    question_id: int
    selected_option_id: Optional[int] = None   # null = skipped


class TestSubmitRequest(BaseModel):
    """Body for POST /tests/{test_id}/submit"""
    answers: List[StudentAnswerCreate]


# ── Instructor View Schemas ──────────────────────────────────────────────────

class StudentRowResponse(BaseModel):
    """One row in the instructor's student table."""
    sno: int
    student_id: str           # e.g. 'BT011'
    student_name: str
    start_time: Optional[str]  # formatted string or '---'
    end_time: Optional[str]    # formatted string or '---'
    status: str                # 'submitted' | 'not_attended' | 'in_progress'
    mark: Optional[float]      # score (0–100) or null
    submission_id: Optional[int]

    class Config:
        orm_mode = True


class TestDetailResponse(BaseModel):
    """Full instructor real-time view for GET /tests/{test_id}/details"""
    test_id: int
    title: str
    module_name: str
    date: Optional[str]          # formatted date string
    duration_minutes: Optional[int]
    start_time: Optional[str]
    end_time: Optional[str]
    total_enrolled: int
    total_submitted: int
    total_passed: int
    total_failed: int
    students: List[StudentRowResponse]


# ── Submission Review Schemas ────────────────────────────────────────────────

class AnswerReviewItem(BaseModel):
    """Per-question review row for GET /tests/{test_id}/submission/{id}"""
    question_id: int
    question_text: str
    selected_option_id: Optional[int]
    selected_option_text: Optional[str]
    is_correct: Optional[bool]
    correct_option_text: Optional[str]

    class Config:
        orm_mode = True


class SubmissionReviewResponse(BaseModel):
    """Full review of one student's submission."""
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
    module_name: str
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
    module_name: str
    title: str
    description: Optional[str]
    expected_outcome: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    resources: List[AssignmentResourceResponse] = []

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
    replies: List[ChatReplyResponse] = []

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
