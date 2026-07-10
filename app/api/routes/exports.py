import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.export_job import ExportJobCreate, ExportJobOut
from app.services.export_service import (
    ExportJobNotFoundError,
    ListNotOwnedError,
    create_export_job,
    get_export_job,
)
from app.workers.export_worker import run_export

router = APIRouter(tags=["exports"])


@router.post(
    "/lists/{list_id}/export",
    response_model=ExportJobOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_export_route(
    list_id: uuid.UUID,
    data: ExportJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExportJobOut:
    try:
        job = create_export_job(db, current_user.id, list_id, data.format)
    except ListNotOwnedError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found") from None

    # Returns immediately — the actual file generation happens after the
    # response is sent, per the task's "accept the request immediately" requirement.
    background_tasks.add_task(run_export, job.id)
    return job


@router.get("/exports/{job_id}", response_model=ExportJobOut)
def get_export_status_route(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExportJobOut:
    try:
        return get_export_job(db, current_user.id, job_id)
    except ExportJobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found") from None


@router.get("/exports/{job_id}/download")
def download_export_route(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    try:
        job = get_export_job(db, current_user.id, job_id)
    except ExportJobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found") from None

    if job.status != "completed" or not job.file_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Export is not ready (status: {job.status})",
        )

    media_type = "application/json" if job.format == "json" else "text/csv"
    return FileResponse(
        path=job.file_path,
        media_type=media_type,
        filename=f"export_{job.list_id}.{job.format}",
    )