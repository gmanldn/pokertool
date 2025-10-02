"""Utilities for capturing screenshots from a live Chrome tab via DevTools.

This module provides a light-weight bridge that connects to a Chrome
instance running with the remote debugging flag enabled
(`--remote-debugging-port=9222` by default). It retrieves a screenshot of the
active tab (or a tab matching a user supplied filter) and exposes it as a
NumPy array in BGR format so it can be consumed by OpenCV based pipelines.

The capture logic is intentionally conservative: it keeps a persistent
WebSocket connection while the scraper is active and automatically retries
if the connection drops. When Chrome is not available the module raises
`ChromeTabCaptureError`, allowing callers to gracefully fall back to other
capture strategies.
"""

from __future__ import annotations

import base64
import json
import logging
import threading
from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    import cv2  # type: ignore
except ImportError as exc:  # pragma: no cover - handled by scraper bootstrap
    cv2 = None  # type: ignore[assignment]
    _cv2_import_error = exc
else:
    _cv2_import_error = None

try:
    import requests
except ImportError as exc:  # pragma: no cover - handled by scraper bootstrap
    requests = None  # type: ignore[assignment]
    _requests_import_error = exc
else:
    _requests_import_error = None

try:
    import websocket
except ImportError as exc:  # pragma: no cover - handled by scraper bootstrap
    websocket = None  # type: ignore[assignment]
    _websocket_import_error = exc
else:
    _websocket_import_error = None

try:
    from Quartz import CoreGraphics as CG  # type: ignore
    QUARTZ_AVAILABLE = True
except ImportError as exc:  # pragma: no cover - optional
    CG = None  # type: ignore[assignment]
    QUARTZ_AVAILABLE = False
    _quartz_import_error = exc
else:
    _quartz_import_error = None


logger = logging.getLogger(__name__)


class ChromeTabCaptureError(RuntimeError):
    """Raised when Chrome tab capture cannot be initialised or executed."""


@dataclass
class ChromeTabCaptureConfig:
    """Configuration for the Chrome tab capture bridge."""

    host: str = "127.0.0.1"
    port: int = 9222
    target_filter: Optional[str] = None
    title_filter: Optional[str] = None
    screenshot_format: str = "png"
    screenshot_quality: Optional[int] = None


class ChromeTabCapture:
    """Capture screenshots from a Chrome tab using the DevTools protocol."""

    def __init__(self, config: Optional[ChromeTabCaptureConfig] = None) -> None:
        self.config = config or ChromeTabCaptureConfig()
        self._socket = None
        self._socket_url: Optional[str] = None
        self._message_id = 0
        self._lock = threading.Lock()

        if _requests_import_error:
            raise ChromeTabCaptureError(
                "The 'requests' package is required for Chrome tab capture"
            ) from _requests_import_error

        if _websocket_import_error:
            raise ChromeTabCaptureError(
                "The 'websocket-client' package is required for Chrome tab capture"
            ) from _websocket_import_error

        if _cv2_import_error:
            raise ChromeTabCaptureError(
                "OpenCV (cv2) is required to decode Chrome tab screenshots"
            ) from _cv2_import_error

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def capture(self) -> np.ndarray:
        """Capture a screenshot of the configured Chrome tab."""

        with self._lock:
            self._ensure_connection()
            payload = {
                "id": self._next_message_id(),
                "method": "Page.captureScreenshot",
                "params": {
                    "format": self.config.screenshot_format,
                    "fromSurface": True,
                },
            }

            if self.config.screenshot_quality is not None:
                payload["params"]["quality"] = self.config.screenshot_quality

            result = self._send(payload)

            image_b64 = result.get("data")
            if not image_b64:
                raise ChromeTabCaptureError("Chrome did not return screenshot data")

            image_bytes = base64.b64decode(image_b64)
            array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
            if image is None:
                raise ChromeTabCaptureError("Failed to decode screenshot data")

            return image

    def close(self) -> None:
        """Close the underlying DevTools WebSocket connection."""
        with self._lock:
            if self._socket is not None:
                try:
                    self._socket.close()
                finally:
                    self._socket = None
                    self._socket_url = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_connection(self) -> None:
        if self._socket and self._socket.connected:
            return

        self._socket_url = self._discover_websocket_url()
        try:
            self._socket = websocket.create_connection(self._socket_url, timeout=5)
        except Exception as exc:  # pragma: no cover - runtime issue
            raise ChromeTabCaptureError(
                f"Failed to connect to Chrome DevTools at {self._socket_url}: {exc}"
            ) from exc

        self._send({"id": self._next_message_id(), "method": "Page.enable"})

    def _discover_websocket_url(self) -> str:
        base_url = f"http://{self.config.host}:{self.config.port}"
        try:
            response = requests.get(f"{base_url}/json", timeout=2)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - runtime issue
            raise ChromeTabCaptureError(
                "Could not reach the Chrome DevTools HTTP endpoint. "
                "Ensure Chrome is running with '--remote-debugging-port=9222'."
            ) from exc

        targets = response.json()
        if not isinstance(targets, list) or not targets:
            raise ChromeTabCaptureError("No debuggable Chrome targets found")

        def is_match(target: dict) -> bool:
            if target.get("type") != "page":
                return False

            url = target.get("url", "").lower()
            title = target.get("title", "").lower()

            filter_url = self.config.target_filter
            filter_title = self.config.title_filter

            url_match = True
            title_match = True

            if filter_url:
                url_match = filter_url.lower() in url
            if filter_title:
                title_match = filter_title.lower() in title

            return url_match and title_match

        for target in targets:
            if is_match(target):
                ws_url = target.get("webSocketDebuggerUrl")
                if ws_url:
                    logger.debug("Using Chrome tab: %s", target.get("title", target.get("url")))
                    return ws_url

        # Fall back to the first page target when no filter matches
        for target in targets:
            if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                logger.debug(
                    "Falling back to first available Chrome tab: %s",
                    target.get("title", target.get("url")),
                )
                return target["webSocketDebuggerUrl"]

        raise ChromeTabCaptureError("No suitable Chrome page target was found")

    def _next_message_id(self) -> int:
        self._message_id += 1
        return self._message_id

    def _send(self, payload: dict) -> dict:
        if not self._socket:
            raise ChromeTabCaptureError("Chrome DevTools connection not established")

        try:
            self._socket.send(json.dumps(payload))
            while True:
                raw = self._socket.recv()
                if not raw:
                    raise ChromeTabCaptureError("Chrome DevTools socket closed unexpectedly")
                response = json.loads(raw)
                if "id" in response and response["id"] == payload["id"]:
                    if "error" in response:
                        raise ChromeTabCaptureError(
                            f"Chrome DevTools error: {response['error']}"
                        )
                    return response.get("result", {})
        except ChromeTabCaptureError:
            raise
        except Exception as exc:  # pragma: no cover - runtime issue
            self.close()
            raise ChromeTabCaptureError(f"Chrome DevTools communication failed: {exc}") from exc


@dataclass
class ChromeWindowCaptureConfig:
    """Configuration for native Chrome window capture."""

    owner_name: str = "Google Chrome"
    title_filter: Optional[str] = None
    toolbar_height: int = 80
    crop_height: Optional[int] = None


class ChromeWindowCapture:
    """Capture Chrome window content without DevTools."""

    def __init__(self, config: Optional[ChromeWindowCaptureConfig] = None) -> None:
        if not QUARTZ_AVAILABLE:
            raise ChromeTabCaptureError(
                "pyobjc (Quartz) is required for Chrome window capture"
            ) from _quartz_import_error  # type: ignore[arg-type]

        self.config = config or ChromeWindowCaptureConfig()

    def capture(self) -> np.ndarray:
        window_info = self._find_window()
        if window_info is None:
            raise ChromeTabCaptureError("Chrome window not found for capture")

        window_id = window_info.get("kCGWindowNumber")
        if window_id is None:
            raise ChromeTabCaptureError("Chrome window has no identifier")

        image_ref = CG.CGWindowListCreateImage(
            CG.CGRectNull,
            CG.kCGWindowListOptionIncludingWindow,
            window_id,
            CG.kCGWindowImageDefault,
        )

        if image_ref is None:
            raise ChromeTabCaptureError("Failed to capture Chrome window image")

        width = CG.CGImageGetWidth(image_ref)
        height = CG.CGImageGetHeight(image_ref)
        data_provider = CG.CGImageGetDataProvider(image_ref)
        data = CG.CGDataProviderCopyData(data_provider)

        buffer = np.frombuffer(data, dtype=np.uint8)
        if buffer.size != width * height * 4:
            raise ChromeTabCaptureError("Unexpected image buffer size from Chrome window")

        image = buffer.reshape((height, width, 4))
        image = np.flipud(image)
        image = image[:, :, :3][:, :, ::-1]

        toolbar = max(self.config.toolbar_height, 0)
        if toolbar:
            image = image[toolbar:, :]

        if self.config.crop_height:
            image = image[: self.config.crop_height, :]

        return image

    def _find_window(self) -> Optional[dict]:
        options = CG.kCGWindowListOptionOnScreenOnly
        window_list = CG.CGWindowListCopyWindowInfo(options, CG.kCGNullWindowID)

        if not window_list:
            return None

        owner = self.config.owner_name.lower()
        title_filter = (self.config.title_filter or "").lower()

        for window in window_list:
            if window.get("kCGWindowLayer") != 0:
                continue

            if window.get("kCGWindowOwnerName", "").lower() != owner:
                continue

            title = window.get("kCGWindowName", "").lower()
            if title_filter and title_filter not in title:
                continue

            return window

        return None


__all__ = [
    "ChromeTabCapture",
    "ChromeTabCaptureConfig",
    "ChromeTabCaptureError",
    "ChromeWindowCapture",
    "ChromeWindowCaptureConfig",
]
