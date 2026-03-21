"""Telegram review bot — sends the weekly video for human approval.

Usage:
  1. Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID in .env (or environment).
  2. Call send_video_for_review() to upload the MP4 to your Telegram chat.
  3. Call poll_for_approval() to wait for the reviewer to reply "approve"
     or "reject" in the same chat.

TODO: Set TELEGRAM_TOKEN to your BotFather token.
TODO: Set TELEGRAM_CHAT_ID to the numeric ID of the review chat.
"""
import time
from typing import Optional

import requests

import config

_TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


class TelegramBot:
    """Thin wrapper around the Telegram Bot API for video review."""

    def __init__(
        self,
        token: str = config.TELEGRAM_TOKEN,
        chat_id: str = config.TELEGRAM_CHAT_ID,
    ) -> None:
        self.token = token
        self.chat_id = chat_id

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def send_video_for_review(self, video_path: str, caption: str = "") -> int:
        """Upload ``video_path`` to the review chat and return the message_id.

        Raises RuntimeError if token or chat_id are not configured.
        """
        self._validate_credentials()

        url = _TELEGRAM_API.format(token=self.token, method="sendVideo")
        with open(video_path, "rb") as fh:
            response = requests.post(
                url,
                data={"chat_id": self.chat_id, "caption": caption},
                files={"video": fh},
                timeout=120,
            )
        response.raise_for_status()
        data = response.json()
        return data["result"]["message_id"]

    def poll_for_approval(
        self,
        message_id: int,
        timeout_s: float = 3600.0,
        poll_interval_s: float = 5.0,
    ) -> Optional[bool]:
        """Wait for a reply to ``message_id`` containing "approve" or "reject".

        Returns:
            True  — reviewer replied "approve" (case-insensitive)
            False — reviewer replied "reject" (case-insensitive)
            None  — timeout expired with no recognised reply

        The poll uses long-polling via getUpdates.
        """
        deadline = time.monotonic() + timeout_s
        offset: Optional[int] = None

        while True:
            updates = self._get_updates(offset=offset)
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                reply_to = msg.get("reply_to_message", {})
                if reply_to.get("message_id") != message_id:
                    continue
                text = msg.get("text", "").strip().lower()
                if text == "approve":
                    return True
                if text == "reject":
                    return False

            if time.monotonic() >= deadline:
                break
            if updates:
                continue
            time.sleep(min(poll_interval_s, max(0.0, deadline - time.monotonic())))

        return None

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _validate_credentials(self) -> None:
        if not self.token:
            raise RuntimeError(
                "TELEGRAM_TOKEN is not set. "
                "Add it to your .env file or environment variables."
            )
        if not self.chat_id:
            raise RuntimeError(
                "TELEGRAM_CHAT_ID is not set. "
                "Add it to your .env file or environment variables."
            )

    def _get_updates(self, offset: Optional[int] = None) -> list[dict]:
        """Fetch pending updates from Telegram (getUpdates)."""
        url = _TELEGRAM_API.format(token=self.token, method="getUpdates")
        params: dict = {"timeout": 0}
        if offset is not None:
            params["offset"] = offset
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("result", [])
