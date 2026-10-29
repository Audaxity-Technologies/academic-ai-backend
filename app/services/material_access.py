"""Shared access rules for notes, original transcripts, and file downloads."""
from fastapi import HTTPException
from app.core.constants import NoteStatus, UserRole
from app.services.course_service import CourseService


def authorize_note(db, user, note, *, write=False):
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    course = CourseService(db).get_course_for_user(note.lecture.course_id, user)
    if write and (user.role != UserRole.TEACHER or course.teacher_id != user.id):
        raise HTTPException(status_code=403, detail="Only the course teacher can review notes")
    if user.role == UserRole.STUDENT and note.status != NoteStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Note not found")
    return note
