from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, DirectoryPath, FilePath, field_validator

class CreateBatchDTO(BaseModel):
    audio_folder: DirectoryPath
    fallback_image: FilePath
    start_date: datetime
    upload_interval: int = Field(default=1, ge=1, description="Interval must be at least 1 day")

    title_template: Optional[str] = None
    desc_template: Optional[str] = None
    tags_template: Optional[str] = None

    preset_rotation: Optional[List[Dict[str, str]]] = None

    category_id: str = "10"

    class Config:
        frozen = True

    @field_validator('start_date')
    @classmethod
    def validate_date(cls, v: datetime) -> datetime:
        if v.date() < datetime.now().date():
            raise ValueError("Start date cannot be in the past.")
        return v