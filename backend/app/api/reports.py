from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportRead
from app.services.file_storage import delete_file, save_file, validate_and_read

router = APIRouter(prefix="/reports", tags=["Reports"])

CATEGORIES = [
    "Blood Test",
    "Thyroid",
    "Urine Test",
    "Lipid Profile",
    "Diabetes",
    "Liver / Kidney",
    "Vitamin",
    "Other",
]


@router.post(
    "/upload", response_model=ReportRead, status_code=status.HTTP_201_CREATED
)
def upload_report(
    file: UploadFile = File(...),
    category: str = Form("Other"),
    report_date: date | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if category not in CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category",
        )

    # Validation: type, size, asli content
    content, file_type = validate_and_read(file)

    # Disk par save (user ke private folder mein)
    stored_filename = save_file(current_user.id, content, file_type)

    report = Report(
        user_id=current_user.id,
        original_filename=Path(file.filename or "report").name[:255],
        stored_filename=stored_filename,
        file_type=file_type,
        file_size=len(content),
        category=category,
        report_date=report_date,
    )

    try:
        db.add(report)
        db.commit()
        db.refresh(report)
    except Exception:
        # Database fail hua to disk se file bhi hata do
        db.rollback()
        delete_file(current_user.id, stored_filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the report",
        )

    return report


@router.get("/categories", response_model=list[str])
def list_categories(current_user: User = Depends(get_current_user)):
    return CATEGORIES


@router.get("", response_model=list[ReportRead])
def list_reports(
    category: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Sirf current user ki reports
    query = select(Report).where(Report.user_id == current_user.id)

    if category:
        query = query.where(Report.category == category)
    if search:
        query = query.where(Report.original_filename.ilike(f"%{search}%"))

    query = query.order_by(Report.uploaded_at.desc())
    return db.scalars(query).all()


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # id AUR user_id dono match hone chahiye
    report = db.scalar(
        select(Report).where(
            Report.id == report_id, Report.user_id == current_user.id
        )
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    delete_file(current_user.id, report.stored_filename)
    db.delete(report)
    db.commit()