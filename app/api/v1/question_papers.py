import hashlib
import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path as PathParam, UploadFile
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.dependencies.auth import get_current_user
from app.database.dependencies.database import get_db
from app.models.user import User
from app.rag.service import answer_question
from app.schemas.search import RAGResponse
from app.schemas.question_paper import PaperAnalysis, PaperDetail, PaperSummary
from app.services.course_service import CourseService
from app.services.question_paper_service import QuestionPaperService, analyze_papers

router = APIRouter(prefix="/question-papers", tags=["Past papers"])
logger = logging.getLogger(__name__)
UPLOAD_DIR = Path("uploads/question-papers")
MAX_UPLOAD = 20 * 1024 * 1024


@router.post("", response_model=PaperDetail, status_code=201)
def upload(course_id: UUID = Form(...), file: UploadFile = File(...),
           exam_year: int | None = Form(None, ge=1900, le=2100), native_pdf: bool = Form(False),
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    CourseService(db).get_course_for_user(course_id, user)
    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() != ".pdf" or len(filename) > 255:
        raise HTTPException(422, "Choose a PDF question paper.")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"{uuid4().hex}.pdf"
    try:
        size = 0
        digest = hashlib.sha256()
        with path.open("xb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD:
                    raise HTTPException(413, "Question papers must be at most 20 MiB.")
                digest.update(chunk)
                buffer.write(chunk)
        if not size:
            raise HTTPException(422, "The PDF is empty.")
        return QuestionPaperService(db, user).create(
            course_id, path, filename, exam_year, native_pdf, digest.hexdigest()
        )
    except IntegrityError as exc:
        db.rollback()
        path.unlink(missing_ok=True)
        if getattr(getattr(exc.orig, "diag", None), "constraint_name", None) == "uq_question_papers_owner_digest":
            raise HTTPException(409, "This PDF is already in your question library.") from exc
        raise
    except HTTPException:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    except ValidationError as exc:
        db.rollback()
        path.unlink(missing_ok=True)
        raise HTTPException(502, "Question extraction returned an invalid response.") from exc
    except ValueError as exc:
        db.rollback()
        path.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        db.rollback()
        path.unlink(missing_ok=True)
        logger.warning("Question paper extraction failed for course %s (%s)", course_id, type(exc).__name__)
        raise HTTPException(502, "Question paper extraction failed. Try again.") from exc
    finally:
        file.file.close()


@router.get("", response_model=list[PaperSummary])
def list_papers(course_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return QuestionPaperService(db, user).list_papers(course_id)


@router.get("/analysis", response_model=PaperAnalysis)
def analysis(course_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return analyze_papers(QuestionPaperService(db, user).list_papers(course_id))


@router.get("/{paper_id}", response_model=PaperDetail)
def paper(paper_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return QuestionPaperService(db, user).get_paper(paper_id)


@router.get("/{paper_id}/file")
def original(paper_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    paper = QuestionPaperService(db, user).get_paper(paper_id)
    path = Path(paper.storage_path).resolve()
    if not path.is_relative_to(UPLOAD_DIR.resolve()) or not path.is_file():
        raise HTTPException(404, "Original question paper not found")
    return FileResponse(path, filename=paper.filename, media_type="application/pdf")



@router.post("/{paper_id}/questions/{index}/explanation", response_model=RAGResponse)
def explain(paper_id: UUID, index: int = PathParam(ge=0), db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    paper = QuestionPaperService(db, user).get_paper(paper_id)
    if index >= len(paper.questions):
        raise HTTPException(404, "Question not found")
    try:
        return answer_question(
            db, paper.questions[index]["text"][:1000], paper.course_id,
            style="Show a worked solution to this practice question when supported by course passages.",
        )
    except Exception as exc:
        db.rollback()
        logger.warning("Past-paper explanation failed for %s (%s)", paper_id, type(exc).__name__)
        raise HTTPException(502, "Could not generate a course-backed explanation.") from exc


@router.delete("/{paper_id}", status_code=204)
def remove(paper_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    paper = QuestionPaperService(db, user).get_paper(paper_id, check_course=False)
    path = Path(paper.storage_path).resolve()
    db.delete(paper)
    db.commit()
    if path.is_relative_to(UPLOAD_DIR.resolve()):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove stored file for question paper %s", paper_id)
