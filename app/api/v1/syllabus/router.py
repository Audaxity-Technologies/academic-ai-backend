import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.syllabus.parser import FORMATS, MAX_BYTES, SyllabusParser
from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.syllabus import SyllabusTopic
from app.models.syllabus_document import SyllabusDocument
from app.models.syllabus_unit import SyllabusUnit
from app.models.user import User
from app.schemas.syllabus_document import (
    ParsedSyllabusResponse, SyllabusDocumentResponse, SyllabusHierarchy,
    SyllabusTopicNodeResponse, SyllabusUnitResponse,
)
from app.services.course_service import CourseService
from app.services.syllabus_document_service import DocumentConflict, SyllabusDocumentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/syllabus", tags=["Syllabus"])
course_router = APIRouter(prefix="/courses", tags=["Syllabus"])
UPLOAD_DIR = Path("uploads/syllabi")


@course_router.post("/{course_id}/syllabus/upload", response_model=SyllabusDocumentResponse, status_code=201)
def upload(course_id: UUID, file: UploadFile = File(...),
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return store_upload(course_id, file, db, user)


@router.post("/upload", response_model=SyllabusDocumentResponse, status_code=201)
def legacy_upload(course_id: UUID = Form(...), file: UploadFile = File(...),
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return store_upload(course_id, file, db, user)


def store_upload(course_id, file, db, user):
    CourseService(db).get_course(course_id, user)
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in FORMATS or len(filename) > 255:
        raise HTTPException(422, "Choose a PDF, DOCX, or TXT file with a valid filename.")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"{uuid4().hex}{suffix}"
    try:
        with path.open("xb") as buffer:
            size = 0
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(413, "Syllabus files must be at most 50 MiB.")
                buffer.write(chunk)
        SyllabusParser().validate(path)
        return SyllabusDocumentService(db).upload_document(course_id, path, filename)
    except ValueError as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    finally:
        file.file.close()


def get_document(db, user, document_id, *, write=False):
    document = db.get(SyllabusDocument, document_id)
    if document is None:
        raise HTTPException(404, "Syllabus version not found.")
    course_service = CourseService(db)
    if write or not document.confirmed_at:
        course_service.get_course(document.course_id, user)
    else:
        course_service.get_course_for_user(document.course_id, user)
    return document


@course_router.get("/{course_id}/syllabus/versions", response_model=list[SyllabusDocumentResponse])
def versions(course_id: UUID, offset: int = Query(0, ge=0),
             limit: int | None = Query(None, ge=1, le=200),
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.core.constants import UserRole

    CourseService(db).get_course_for_user(course_id, user)
    stmt = select(SyllabusDocument).where(SyllabusDocument.course_id == course_id)
    if user.role != UserRole.TEACHER:
        stmt = stmt.where(SyllabusDocument.confirmed_at.is_not(None))
    return db.scalars(stmt.order_by(SyllabusDocument.version.desc()).offset(offset).limit(limit)).all()


def preview_data(document):
    if document.hierarchy is None:
        raise HTTPException(409, "Parse the syllabus to generate a preview.")
    report = document.parsing_report
    return {"document": document, "hierarchy": document.hierarchy,
            "total_topics": report["topics"] + report["subtopics"]}


@router.post("/{document_id}/parse", response_model=ParsedSyllabusResponse)
def parse(document_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    document = get_document(db, user, document_id, write=True)
    try:
        SyllabusDocumentService(db).parse(document)
    except DocumentConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, document.parsing_error or "Invalid syllabus structure.") from exc
    except Exception as exc:
        raise HTTPException(502, "Syllabus extraction failed. See the parsing status.") from exc
    return preview_data(document)


@router.get("/{document_id}", response_model=SyllabusDocumentResponse)
def details(document_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_document(db, user, document_id)


@router.get("/{document_id}/preview", response_model=ParsedSyllabusResponse)
def preview(document_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return preview_data(get_document(db, user, document_id))


@router.put("/{document_id}/preview", response_model=ParsedSyllabusResponse)
def edit(document_id: UUID, hierarchy: SyllabusHierarchy,
         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    document = get_document(db, user, document_id, write=True)
    try:
        SyllabusDocumentService(db).save_draft(document, hierarchy)
    except ValueError as exc:
        raise HTTPException(409 if document.confirmed_at else 422, str(exc)) from exc
    return preview_data(document)


@router.post("/{document_id}/confirm", response_model=SyllabusDocumentResponse)
def confirm(document_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    document = get_document(db, user, document_id, write=True)
    try:
        SyllabusDocumentService(db).confirm(document)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        logger.exception("Syllabus activation failed for %s", document_id)
        db.rollback()
        raise HTTPException(502, "Syllabus activation failed. Retry confirmation.") from exc
    return document


@router.get("/{document_id}/units", response_model=list[SyllabusUnitResponse])
def units(document_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_document(db, user, document_id)
    return db.scalars(select(SyllabusUnit).where(
        SyllabusUnit.syllabus_document_id == document_id
    ).order_by(SyllabusUnit.position)).all()


@router.get("/units/{unit_id}/topics", response_model=list[SyllabusTopicNodeResponse])
@router.get("/units/{unit_id}/subtopics", response_model=list[SyllabusTopicNodeResponse], include_in_schema=False)
def topics(unit_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    unit = db.get(SyllabusUnit, unit_id)
    if unit is None:
        raise HTTPException(404, "Syllabus unit not found.")
    get_document(db, user, unit.syllabus_document_id)
    return db.scalars(select(SyllabusTopic).where(
        SyllabusTopic.syllabus_unit_id == unit_id
    ).order_by(SyllabusTopic.position)).all()

