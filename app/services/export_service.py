import uuid

from sqlalchemy.orm import Session

from app.models.export_job import ExportJob
from app.models.list import List

MAX_PAGE_SIZE = 100


class ExportJobNotFoundError(Exception):
    pass


class ListNotOwnedError(Exception):
    pass


def _assert_list_owned(db: Session, owner_id: uuid.UUID, list_id: uuid.UUID) -> None:
    exists = (
        db.query(List.id)
        .filter(List.id == list_id, List.owner_id == owner_id)
        .first()
    )
    if exists is None:
        raise ListNotOwnedError()


def create_export_job(
    db: Session, owner_id: uuid.UUID, list_id: uuid.UUID, format: str
) -> ExportJob:
    _assert_list_owned(db, owner_id, list_id)

    job = ExportJob(
        user_id=owner_id,
        list_id=list_id,
        status="pending",
        format=format,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_export_job(db: Session, owner_id: uuid.UUID, job_id: uuid.UUID) -> ExportJob:
    # user_id lives directly on export_jobs — no join needed to enforce "only the requester's own jobs."
    job = (
        db.query(ExportJob)
        .filter(ExportJob.id == job_id, ExportJob.user_id == owner_id)
        .first()
    )
    if job is None:
        raise ExportJobNotFoundError()
    return job