"""YouTube uploader — uploads the finished MP4 to YouTube via the Data API v3.

Credentials setup (OAuth 2.0):
  1. Create a project in Google Cloud Console.
  2. Enable the YouTube Data API v3.
  3. Create an OAuth 2.0 client ID (Desktop app type) and download the JSON.
  4. Set YOUTUBE_CLIENT_SECRETS_FILE=/path/to/client_secrets.json in .env.
  5. On first run, a browser window will open for OAuth consent.
     Subsequent runs reuse the saved token from ``~/.youtube_token.json``.

TODO: Complete steps 1–4 above to enable real YouTube uploads.
"""
import os
from pathlib import Path
from typing import Optional

import config

_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
_TOKEN_FILE = os.path.expanduser("~/.youtube_token.json")
_WATCH_URL = "https://www.youtube.com/watch?v={video_id}"


class YouTubeUploader:
    """Uploads an MP4 to YouTube using the Data API v3."""

    def __init__(
        self,
        client_secrets_file: str = config.YOUTUBE_CLIENT_SECRETS_FILE,
    ) -> None:
        self.client_secrets_file = client_secrets_file

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def build_metadata(
        self,
        week: int,
        season: int,
        player_name: Optional[str] = None,
    ) -> dict:
        """Return a dict of YouTube video metadata for the given week."""
        title = f"Guess That Player — {season} Season Week {week}"
        if player_name:
            title += f" ({player_name})"

        description = (
            f"Can you guess the fantasy football player from Week {week} of the "
            f"{season} NFL season? Watch the clues and drop your answer below!\n\n"
            "#FantasyFootball #GuessThePlayer #NFL"
        )

        tags = [
            "fantasy football",
            "NFL",
            "guess the player",
            f"week {week}",
            str(season),
        ]
        if player_name:
            tags.append(player_name)

        return {
            "title": title,
            "description": description,
            "tags": tags,
            "category_id": "17",   # Sports
            "privacy_status": "unlisted",
        }

    def upload(
        self,
        video_path: str,
        week: int,
        season: int,
        player_name: Optional[str] = None,
    ) -> str:
        """Upload ``video_path`` to YouTube and return the watch URL.

        Raises RuntimeError if client_secrets_file is not configured.
        Raises FileNotFoundError if the video file does not exist.
        """
        if not self.client_secrets_file:
            raise RuntimeError(
                "YOUTUBE_CLIENT_SECRETS_FILE is not set. "
                "See the module docstring for setup instructions."
            )

        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        metadata = self.build_metadata(week=week, season=season, player_name=player_name)
        youtube = self._build_youtube_service()

        body = {
            "snippet": {
                "title": metadata["title"],
                "description": metadata["description"],
                "tags": metadata["tags"],
                "categoryId": metadata["category_id"],
            },
            "status": {
                "privacyStatus": metadata["privacy_status"],
            },
        }

        from googleapiclient.http import MediaFileUpload  # type: ignore

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        response = (
            youtube.videos()
            .insert(part="snippet,status", body=body, media_body=media)
            .execute()
        )

        video_id: str = response["id"]
        return _WATCH_URL.format(video_id=video_id)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_youtube_service(self):
        """Authenticate and return a YouTube Data API service object.

        On first call opens a browser for OAuth consent.
        Subsequent calls load the saved token from ``~/.youtube_token.json``.

        TODO: Run once interactively to generate ~/.youtube_token.json, then
              subsequent pipeline runs will be fully non-interactive.
        """
        import google.oauth2.credentials as google_creds
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
        import googleapiclient.discovery as discovery  # type: ignore

        creds = None
        if Path(_TOKEN_FILE).exists():
            creds = google_creds.Credentials.from_authorized_user_file(
                _TOKEN_FILE, _SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, _SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(_TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        return discovery.build("youtube", "v3", credentials=creds)
