from datetime import timedelta
from pathlib import Path
from typing import List, Tuple

from src.domain.entities import UploadJob, VideoMetadata
from src.application.dtos import CreateBatchDTO


class BatchScheduler:
    def __init__(self, repo):
        self.repo = repo

    def create_batch(self, dto: CreateBatchDTO) -> int:
        audio_files = sorted(list(dto.audio_folder.glob("*.mp3")))

        if not audio_files:
            raise ValueError(f"No .mp3 files found in {dto.audio_folder}")

        current_date = dto.start_date.replace(hour=12, minute=30, second=0)

        count = 0
        rotation_len = len(dto.preset_rotation) if dto.preset_rotation else 0

        for i, audio_path in enumerate(audio_files):
            if rotation_len > 0:
                settings = dto.preset_rotation[i % rotation_len]
                t_tmpl, d_tmpl, tags_tmpl = settings["title"], settings["desc"], settings["tags"]
            else:
                t_tmpl, d_tmpl, tags_tmpl = dto.title_template, dto.desc_template, dto.tags_template

            cover_image = self._resolve_cover_image(audio_path, dto.fallback_image)

            title, desc, tags = self._generate_metadata(
                audio_path.stem, t_tmpl, d_tmpl, tags_tmpl
            )

            job = UploadJob(
                audio_path=audio_path,
                image_path=cover_image,
                metadata=VideoMetadata(
                    title=title,
                    description=desc,
                    tags=tags,
                    category_id=dto.category_id
                ),
                publish_at=current_date
            )

            self.repo.add(job)

            current_date += timedelta(days=dto.upload_interval)
            count += 1

        return count

    def _resolve_cover_image(self, audio_path: Path, fallback: Path) -> Path:
        for ext in [".jpg", ".png", ".jpeg"]:
            potential_cover = audio_path.with_suffix(ext)
            if potential_cover.exists():
                return potential_cover
        return fallback

    def _generate_metadata(self, filename: str, t_tmpl: str, d_tmpl: str, tags_tmpl: str) -> Tuple[str, str, List[str]]:
        context = {
            "{filename}": filename
        }

        title = t_tmpl
        desc = d_tmpl or ""

        for key, val in context.items():
            title = title.replace(key, val)
            desc = desc.replace(key, val)

        # Обробка тегів
        raw_tags = tags_tmpl.split(",") if tags_tmpl else []
        processed_tags = []

        for t in raw_tags:
            t = t.strip()
            if not t: continue

            for key, val in context.items():
                t = t.replace(key, val)

            if len(t) > 100:
                t = t[:100]

            t = t.replace("<", "").replace(">", "")

            processed_tags.append(t)

        final_tags = []
        total_len = 0
        for tag in processed_tags:
            if total_len + len(tag) + 1 > 500:
                break
            final_tags.append(tag)
            total_len += len(tag) + 1

        return title, desc, final_tags