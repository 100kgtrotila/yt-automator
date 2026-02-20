import subprocess
import logging
from pathlib import Path
from src.domain.ports import RendererPort


class FFmpegRenderer(RendererPort):
    def __init__(self, ffmpeg_bin: str = "ffmpeg"):
        self._bin = ffmpeg_bin

    def render(self, audio: Path, image: Path, output: Path) -> Path:
        filter_complex = (
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"
        )

        cmd = [
            self._bin, "-y",
            "-loop", "1",
            "-i", str(image),
            "-i", str(audio),
            "-vf", filter_complex,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-f", "mp4",
            str(output)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode("utf-8") if e.stderr else str(e)
            raise RuntimeError(f"FFmpeg render error: {error_msg}")