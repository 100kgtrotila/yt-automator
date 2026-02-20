from pathlib import Path
import socket

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import ResumableUploadError

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.domain.entities import UploadJob
from src.domain.ports import UploaderPort


class YouTubeUploader(UploaderPort):
    _SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    _API_SERVICE_NAME = "youtube"
    _API_VERSION = "v3"

    def __init__(self, secrets_file: Path, token_file: Path):
        self._secrets_file = secrets_file
        self._token_file = token_file
        self._service = None

    def _get_authenticated_service(self):
        if self._service:
            return self._service

        creds = None
        if self._token_file.exists():
            creds = Credentials.from_authorized_user_file(str(self._token_file), self._SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    print("  [Auth] Token expired and refresh failed. Re-authenticating...")
                    if self._token_file.exists():
                        self._token_file.unlink()
                    creds = None

            if not creds:
                if not self._secrets_file.exists():
                    raise FileNotFoundError(
                        f"CRITICAL: '{self._secrets_file}' not found! Download it from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self._secrets_file), self._SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self._token_file, "w") as token:
                token.write(creds.to_json())

        self._service = build(self._API_SERVICE_NAME, self._API_VERSION, credentials=creds)
        return self._service

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((HttpError, ResumableUploadError, socket.timeout))
    )
    def upload(self, video_path: Path, job: UploadJob) -> str:
        service = self._get_authenticated_service()

        title = job.metadata.title
        description = job.metadata.description
        tags = job.metadata.tags

        if len(title) > 100:
            title = title[:97] + "..."

        print(f"  [YouTube] Uploading: '{title}'")

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": job.metadata.category_id
            },
            "status": {
                "privacyStatus": job.metadata.privacy,
                "selfDeclaredMadeForKids": False
            }
        }

        try:
            if job.publish_at:
                body["status"]["privacyStatus"] = "private"
                body["status"]["publishAt"] = job.publish_at.isoformat() + "Z"

            media = MediaFileUpload(
                str(video_path),
                chunksize=1024 * 1024 * 5,
                resumable=True,
                mimetype="video/mp4"
            )

            request = service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Uploaded {int(status.progress() * 100)}%")

            return response.get("id")

        except ResumableUploadError as e:
            error_msg = f"Resumable Upload Failed: {e}"
            if hasattr(e, 'content') and e.content:
                error_msg += f" | Details: {e.content.decode('utf-8')}"

            if hasattr(e, 'resp') and e.resp.status in [403, 429]:
                raise RuntimeError("YOUTUBE_QUOTA_EXCEEDED")

            raise RuntimeError(error_msg)

        except HttpError as e:
            if e.resp.status in [403, 429]:
                reason = e.content.decode()
                if "quotaExceeded" in reason:
                    raise RuntimeError("YOUTUBE_QUOTA_EXCEEDED")
            raise e