from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

from enum import Enum


class LectureSourceType(str, Enum):
    AUDIO = "audio"
    TRANSCRIPT = "transcript"

class LectureStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class NoteStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"