from pathlib import Path

from src.application.scheduler import BatchScheduler
from src.application.worker import QueueWorker
from src.application.presets import PresetManager
from src.infrastructure.db.repository import SqliteRepository
from src.infrastructure.ffmpeg.renderer import FFmpegRenderer
from src.infrastructure.youtube.uploader import YouTubeUploader


class Container:
    def __init__(self):
        self.root_path = Path.cwd()
        self.data_dir = self.root_path / "data"
        self.output_dir = self.root_path / "output"
        self.bin_dir = self.root_path / "bin"

        self._ensure_directories()

        self.repo = SqliteRepository(f"sqlite:///{self.data_dir}/queue.db")

        ffmpeg_bin = self._get_ffmpeg_path()
        self.renderer = FFmpegRenderer(ffmpeg_bin=ffmpeg_bin)

        self.uploader = YouTubeUploader(
            secrets_file=self.root_path / "client_secrets.json",
            token_file=self.root_path / "token.json"
        )

        self.preset_manager = PresetManager(self.data_dir / "presets.json")

        self.scheduler = BatchScheduler(self.repo)

        self.worker = QueueWorker(
            repo=self.repo,
            renderer=self.renderer,
            uploader=self.uploader,
            temp_dir=self.output_dir
        )

    def _ensure_directories(self):
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def _get_ffmpeg_path(self):
        local_ffmpeg = self.bin_dir / "ffmpeg.exe"
        if local_ffmpeg.exists():
            return str(local_ffmpeg)
        return "ffmpeg"