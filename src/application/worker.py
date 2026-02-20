import time
import traceback
import threading
from pathlib import Path
from src.domain.ports import JobRepositoryPort, RendererPort, UploaderPort


class QueueWorker:
    def __init__(self,
                 repo: JobRepositoryPort,
                 renderer: RendererPort,
                 uploader: UploaderPort,
                 temp_dir: Path,
                 logger_callback=None):
        self.repo = repo
        self.renderer = renderer
        self.uploader = uploader
        self.temp_dir = temp_dir
        self.log = logger_callback or print
        self._stop_event = threading.Event()

    def start_background(self):
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()

    def stop(self):
        self._stop_event.set()

    def _run_loop(self):
        self.log("Worker started. Waiting for jobs...")

        while not self._stop_event.is_set():
            job = None
            output_file = None

            try:
                job = self.repo.get_next_pending()
                if not job:
                    time.sleep(2)
                    continue

                self.log(f"Processing Job #{job.id}: {job.audio_path.name}")

                job.mark_processing()
                self.repo.update(job)

                output_file = self.temp_dir / f"render_{job.id}.mp4"

                self.log("   - Rendering video (FFmpeg)...")
                self.renderer.render(job.audio_path, job.image_path, output_file)

                self.log(f"   - ☁ Uploading to YouTube (Scheduled: {job.publish_at})...")

                video_id = self.uploader.upload(output_file, job)

                job.mark_completed(video_id)
                self.repo.update(job)
                self.log(f"   - DONE! Video ID: {video_id}")

            except RuntimeError as e:
                if str(e) == "YOUTUBE_QUOTA_EXCEEDED":
                    self.log("CRITICAL: YouTube Daily Quota Exceeded! Stopping worker.")
                    if job:
                        job.mark_failed("Quota Exceeded - Worker Stopped")
                        self.repo.update(job)

                    self._stop_event.set()
                    break

                self.log(f"   - RUNTIME ERROR: {e}")
                if job:
                    job.mark_failed(str(e))
                    self.repo.update(job)

            except Exception as e:
                self.log(f"   - UNEXPECTED ERROR: {e}")
                traceback.print_exc()
                if job:
                    job.mark_failed(str(e))
                    self.repo.update(job)
                time.sleep(5)

            finally:
                if output_file and output_file.exists():
                    try:
                        output_file.unlink()
                    except Exception as clean_err:
                        print(f"Failed to clean temp file: {clean_err}")