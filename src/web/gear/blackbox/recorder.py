"""
Console Blackbox - "The Flight Recorder"

Records browser console logs and errors during scraping sessions.
Useful for debugging "silent" failures where JS crashes but page loads.
"""

import time
from dataclasses import dataclass

from playwright.async_api import ConsoleMessage, Error, Page


@dataclass
class LogEntry:
    timestamp: float
    type: str  # 'console' or 'error'
    level: str  # 'log', 'warning', 'error', 'debug'
    text: str
    location: str | None = None


class ConsoleBlackbox:
    """
    Flight Recorder for Browser Console and Error events.
    Attaches to a page and passively records logs.
    """

    def __init__(self):
        self.logs: list[LogEntry] = []
        self._start_time = time.time()

    def attach(self, page: Page):
        """Wire up listeners to the page."""
        page.on("console", self._handle_console)
        page.on("pageerror", self._handle_page_error)
        # Optional: Capture failed network requests (4xx/5xx) if not handled elsewhere
        # page.on("requestfailed", self._handle_request_failed)

    async def _handle_console(self, msg: ConsoleMessage):
        """Handle console.* calls."""
        try:
            # Use msg.args to extract complex objects if necessary,
            # but text is usually sufficient for logging.
            text = msg.text
            location = (
                f"{msg.location['url']}:{msg.location['lineNumber']}"
                if msg.location["url"]
                else None
            )

            entry = LogEntry(
                timestamp=time.time(),
                type="console",
                level=msg.type,
                text=text,
                location=location,
            )
            self.logs.append(entry)
        except Exception:
            pass  # Never crash the recorder

    async def _handle_page_error(self, error: Error):
        """Handle uncaptured exceptions in the window context."""
        entry = LogEntry(
            timestamp=time.time(),
            type="page_error",
            level="error",
            text=str(error) + "\n" + str(error.stack),
            location=None,
        )
        self.logs.append(entry)

    def get_logs(self) -> list[dict]:
        """Export logs in a serializable format."""
        return [
            {
                "time_offset_ms": int((log.timestamp - self._start_time) * 1000),
                "type": log.type,
                "level": log.level,
                "text": log.text,
                "location": log.location,
            }
            for log in self.logs
        ]
