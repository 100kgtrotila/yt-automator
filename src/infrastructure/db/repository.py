from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.domain.ports import JobRepositoryPort
from src.domain.entities import UploadJob, VideoMetadata, JobStatus
from src.infrastructure.db.models import Base, JobModel
from pathlib import Path


class SqliteRepository(JobRepositoryPort):
    def __init__(self, db_path: str):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add(self, job: UploadJob) -> int:
        session = self.Session()
        model = JobModel(
            audio_path=str(job.audio_path),
            image_path=str(job.image_path),
            title=job.metadata.title,
            description=job.metadata.description,
            tags=",".join(job.metadata.tags),
            publish_at=job.publish_at,
            status=job.status
        )
        session.add(model)
        session.commit()
        job_id = model.id
        session.close()
        return job_id

    def get_next_pending(self):
        session = self.Session()
        model = session.query(JobModel) \
            .filter(JobModel.status == JobStatus.PENDING) \
            .order_by(JobModel.publish_at) \
            .first()

        if not model:
            session.close()
            return None

        entity = UploadJob(
            id=model.id,
            audio_path=Path(model.audio_path),
            image_path=Path(model.image_path),
            metadata=VideoMetadata(
                title=model.title,
                description=model.description,
                tags=model.tags.split(",") if model.tags else []
            ),
            publish_at=model.publish_at,
            status=model.status,
            error_message=model.error_message
        )
        session.close()
        return entity

    def update(self, job: UploadJob):
        session = self.Session()
        model = session.query(JobModel).get(job.id)
        if model:
            model.status = job.status
            model.remote_video_id = job.remote_video_id
            model.error_message = job.error_message
            session.commit()
        session.close()