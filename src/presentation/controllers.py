from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.application.dtos import CreateBatchDTO
from src.application.presets import Preset
from src.infrastructure.ioc_container import Container


class BatchController:
    def __init__(self, container: Container):
        self.scheduler = container.scheduler
        self.presets = container.preset_manager
        self.worker = container.worker
        self.container = container

    def generate_batch(self, form_data: Dict) -> int:
        try:
            start_date = datetime.strptime(form_data['start_date'], "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid Date format. Use YYYY-MM-DD")

        folder = form_data.get('folder')
        cover = form_data.get('cover')

        if not folder or not cover:
            raise ValueError("Please select both MP3 Folder and Cover Image.")

        preset_rotation = form_data.get('preset_rotation')

        dto = CreateBatchDTO(
            audio_folder=Path(folder),
            fallback_image=Path(cover),
            start_date=start_date,
            upload_interval=int(form_data.get('interval', 1)),
            title_template=form_data.get('title'),
            desc_template=form_data.get('desc'),
            tags_template=form_data.get('tags'),
            preset_rotation=preset_rotation
        )

        return self.scheduler.create_batch(dto)

    def get_preset_names(self) -> List[str]:
        return self.presets.get_all_names()

    def load_preset(self, name: str) -> Optional[Preset]:
        return self.presets.get_preset(name)

    def save_preset(self, name: str, data: Dict):
        preset = Preset(
            title_template=data['title'],
            desc_template=data['desc'],
            tags_template=data['tags']
        )
        self.presets.save_preset(name, preset)

    def delete_preset(self, name: str):
        self.presets.delete_preset(name)

    def start_worker(self):
        self.worker.start_background()

    def stop_worker(self):
        self.worker.stop()

    def set_logger(self, callback):
        self.worker.log = callback