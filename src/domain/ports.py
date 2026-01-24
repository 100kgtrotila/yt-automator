from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from .entities import UploadJob


class JobRepositoryPort(ABC):
    @abstractmethod
    def add(self, job: UploadJob) -> int: ...

    @abstractmethod
    def get_next_pending(self) -> Optional[UploadJob]: ...

    @abstractmethod
    def update(self, job: UploadJob): ...


class RendererPort(ABC):
    @abstractmethod
    def render(self, audio: Path, image: Path, output: Path) -> Path: ...


class UploaderPort(ABC):
    @abstractmethod
    def upload(self, video_path: Path, job: UploadJob) -> str: ...