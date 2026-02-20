from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VideoMetadata:
    title: str
    description: str
    tags: list[str]
    category_id: str = "10"
    privacy: str = "private"


@dataclass
class UploadJob:
    audio_path: Path
    image_path: Path
    metadata: VideoMetadata
    publish_at: datetime
    id: Optional[int] = None
    status: JobStatus = JobStatus.PENDING
    remote_video_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def mark_processing(self):
        self.status = JobStatus.PROCESSING

    def mark_completed(self, remote_id: str):
        self.status = JobStatus.COMPLETED
        self.remote_video_id = remote_id
        self.error_message = None

    def mark_failed(self, error: str):

        self.status = JobStatus.FAILED
        self.error_message = str(error)