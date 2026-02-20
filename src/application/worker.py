import time
import traceback
import threading
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Optional

from src.domain.ports import JobRepositoryPort, RendererPort, UploaderPort
from src.domain.entities import UploadJob


class JobEvent(Enum):
    WORKER_STARTED = auto()
    WORKER_STOPPED = auto()
    JOB_STARTED = auto()
    JOB_RENDERING = auto()
    JOB_UPLOADING = auto()
    JOB_COMPLETED = auto()
    JOB_FAILED = auto()
    QUOTA_EXCEEDED = auto()


# Callback type aliases
LogCallback = Callable[[str], None]
StatusCallback = Callable[[JobEvent, Optional[UploadJob], Optional[dict[str, Any]]], None]


def _noop_log(msg: str) -> None:
    pass


def _noop_status(event: JobEvent, job: Optional[UploadJob] = None, extra: Optional[dict[str, Any]] = None) -> None:
    pass


class QueueWorker:
    def __init__(
        self,
        repo: JobRepositoryPort,
        renderer: RendererPort,
        uploader: UploaderPort,
        temp_dir: Path,
        logger_callback: Optional[LogCallback] = None,
        status_callback: Optional[StatusCallback] = None,
    ) -> None:
        self.repo: JobRepositoryPort = repo
        self.renderer: RendererPort = renderer
        self.uploader: UploaderPort = uploader
        self.temp_dir: Path = temp_dir
        self.log: LogCallback = logger_callback or _noop_log
        self.on_status: StatusCallback = status_callback or _noop_status
        self._stop_event: threading.Event = threading.Event()

    def start_background(self) -> None:
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()

    def stop(self) -> None:
        self._stop_event.set()

    def is_running(self) -> bool:
        return not self._stop_event.is_set()

    def _emit(self, event: JobEvent, job: Optional[UploadJob] = None, **extra: Any) -> None:
        self.on_status(event, job, extra if extra else None)

    def _run_loop(self) -> None:
        self.log("Worker started. Waiting for jobs...")
        self._emit(JobEvent.WORKER_STARTED)

        while not self._stop_event.is_set():
            job: Optional[UploadJob] = None
            output_file: Optional[Path] = None

            try:
                job = self.repo.get_next_pending()
                if not job:
                    time.sleep(2)
                    continue

                self.log(f"Processing Job #{job.id}: {job.audio_path.name}")
                self._emit(JobEvent.JOB_STARTED, job)

                job.mark_processing()
                self.repo.update(job)

                output_file = self.temp_dir / f"render_{job.id}.mp4"

                self.log("   - Rendering video (FFmpeg)...")
                self._emit(JobEvent.JOB_RENDERING, job)
                self.renderer.render(job.audio_path, job.image_path, output_file)

                self.log(f"   - Uploading to YouTube (Scheduled: {job.publish_at})...")
                self._emit(JobEvent.JOB_UPLOADING, job)

                video_id: str = self.uploader.upload(output_file, job)

                job.mark_completed(video_id)
                self.repo.update(job)
                self.log(f"   - DONE! Video ID: {video_id}")
                self._emit(JobEvent.JOB_COMPLETED, job, video_id=video_id)

            except RuntimeError as e:
                if str(e) == "YOUTUBE_QUOTA_EXCEEDED":
                    self.log("CRITICAL: YouTube Daily Quota Exceeded! Stopping worker.")
                    if job:
                        job.mark_failed("Quota Exceeded - Worker Stopped")
                        self.repo.update(job)
                    self._emit(JobEvent.QUOTA_EXCEEDED, job)
                    self._stop_event.set()
                    break

                self.log(f"   - RUNTIME ERROR: {e}")
                if job:
                    job.mark_failed(str(e))
                    self.repo.update(job)
                    self._emit(JobEvent.JOB_FAILED, job, error=str(e))

            except Exception as e:
                self.log(f"   - UNEXPECTED ERROR: {e}")
                self.log(traceback.format_exc())
                if job:
                    job.mark_failed(str(e))
                    self.repo.update(job)
                    self._emit(JobEvent.JOB_FAILED, job, error=str(e))
                time.sleep(5)

            finally:
                if output_file and output_file.exists():
                    try:
                        output_file.unlink()
                    except Exception as clean_err:
                        self.log(f"Failed to clean temp file: {clean_err}")

        self.log("Worker stopped.")
        self._emit(JobEvent.WORKER_STOPPED)

