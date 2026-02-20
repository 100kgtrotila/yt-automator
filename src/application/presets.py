import json
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel

class Preset(BaseModel):
    title_template: str
    desc_template: str
    tags_template: str

class PresetManager:
    def __init__(self, storage_path: Path):
        self.path = storage_path
        self._presets: Dict[str, Preset] = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for name, fields in data.items():
                    self._presets[name] = Preset(**fields)
        except Exception as e:
            print(f"Error loading presets: {e}")

    def save_preset(self, name: str, preset: Preset):
        self._presets[name] = preset
        self._flush()

    def delete_preset(self, name: str):
        if name in self._presets:
            del self._presets[name]
            self._flush()

    def get_preset(self, name: str) -> Optional[Preset]:
        return self._presets.get(name)

    def get_all_names(self) -> list[str]:
        return list(self._presets.keys())

    def _flush(self):
        data = {name: p.model_dump() for name, p in self._presets.items()}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)