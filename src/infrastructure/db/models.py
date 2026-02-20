from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from src.domain.entities import JobStatus

Base = declarative_base()


class JobModel(Base):
    __tablename__ = 'upload_queue'

    id = Column(Integer, primary_key=True)
    audio_path = Column(String, nullable=False)
    image_path = Column(String, nullable=False)

    title = Column(String)
    description = Column(Text)
    tags = Column(String)
    publish_at = Column(DateTime)

    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    remote_video_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)