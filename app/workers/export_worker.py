import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.database import SessionLocal
from app.models.export_job import ExportJob
from app.models.item import Item

EXPORTS_DIR = Path("/code/exports")


def run_export(job_id: uuid.UUID) -> None:
    """
    Own DB session, In-process background task: if the server restarts mid-export,
    the job stays stuck at "processing" forever.
    """
    db = SessionLocal()
    try:
        job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
        if job is None:
            return

        job.status = "processing"
        db.commit()

        try:
            items = db.query(Item).filter(Item.list_id == job.list_id).all()

            EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
            file_name = f"{job.id}.{job.format}"
            file_path = EXPORTS_DIR / file_name

            if job.format == "json":
                payload = [
                    {
                        "id": str(item.id),
                        "title": item.title,
                        "status": item.status,
                        "created_at": item.created_at.isoformat(),
                    }
                    for item in items
                ]
                file_path.write_text(json.dumps(payload, indent=2))
            else:  # csv
                with file_path.open("w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["id", "title", "status", "created_at"])
                    for item in items:
                        writer.writerow(
                            [item.id, item.title, item.status, item.created_at.isoformat()]
                        )

            job.status = "completed"
            job.file_path = str(file_path)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as e:
            db.rollback()
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()