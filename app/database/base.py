from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.user import User
from app.models.course import Course
from app.models.syllabus import SyllabusTopic
from app.models.lecture import Lecture
from app.models.transcript import Transcript
from app.models.note import Note