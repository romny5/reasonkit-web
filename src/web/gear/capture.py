"""
Web Capture Gear - Deep Freeze Implementation

Navigates to URLs, intercepts network traffic, and creates WARC archives.
Based on Protocol Delta v2 (Amber) architecture.

This module handles the "Eyes" - actual web interaction.
For "Brain" operations (ledger, verification), use reasonkit-core's ProofLedger.
"""

import gzip
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .stealth.navigator import StealthNavigator

logger = logging.getLogger("web.capture")

# Check playwright availability
try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning(
        "Playwright not available. Run: uv pip install playwright && playwright install chromium"
    )


@dataclass
class HttpTransaction:
    """Captured HTTP transaction."""

    url: str
    method: str
    request_headers: dict[str, str]
    response_headers: dict[str, str]
    status_code: int
    payload: bytes
    timestamp: float
    content_type: str


@dataclass
class CaptureResult:
    """Result of a capture operation."""

    success: bool
    url: str
    warc_path: str | None = None
    payload_hash: str | None = None
    headers_hash: str | None = None
    extracted_content: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "url": self.url,
            "warc_path": self.warc_path,
            "payload_hash": self.payload_hash,
            "headers_hash": self.headers_hash,
            "extracted_content": self.extracted_content[:500] + "..."
            if self.extracted_content and len(self.extracted_content) > 500
            else self.extracted_content,
            "error": self.error,
        }


class WarcRecorder:
    """Records HTTP transactions to WARC format."""

    def __init__(self, storage_path: str | Path = "./web_archive"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.transactions: list[HttpTransaction] = []

    def intercept_response(self, response: Any) -> None:
        """Hook into Playwright response event. Filters noise, captures data."""
        try:
            headers = response.headers
            if callable(headers):
                headers = headers()

            content_type = headers.get("content-type", "").lower()

            # Only keep Documents (HTML) and Data (JSON/XML)
            allowed_types = ["text/html", "application/json", "application/xml", "text/plain"]
            if not any(t in content_type for t in allowed_types):
                return

            try:
                body = response.body()
            except Exception as e:
                logger.debug(f"Failed to fetch body for {response.url}: {e}")
                return

            req = response.request
            req_headers = req.headers
            if callable(req_headers):
                req_headers = req_headers()

            transaction = HttpTransaction(
                url=response.url,
                method=req.method,
                request_headers=req_headers,
                response_headers=headers,
                status_code=response.status,
                payload=body,
                timestamp=time.time(),
                content_type=content_type,
            )
            self.transactions.append(transaction)

        except Exception as e:
            logger.debug(f"Intercept error: {e}")

    def freeze(self, url_context: str) -> tuple[str, str, str]:
        """
        Write captured transactions to WARC file.

        Returns:
            Tuple of (warc_path, payload_hash, headers_hash)
        """
        if not self.transactions:
            raise ValueError("No relevant traffic captured")

        # Sort by timestamp
        self.transactions.sort(key=lambda t: t.timestamp)

        # Find primary transaction (main HTML doc)
        primary = next(
            (t for t in self.transactions if t.url == url_context),
            next(
                (t for t in self.transactions if "text/html" in t.content_type),
                self.transactions[0],
            ),
        )

        # Generate filename
        url_hash = hashlib.md5(url_context.encode()).hexdigest()[:8]
        filename = f"record_{int(time.time())}_{url_hash}.warc.gz"
        warc_path = self.storage_path / filename

        # Write WARC
        with gzip.open(warc_path, "wb") as f:
            for t in self.transactions:
                header = self._format_warc_header(t)
                f.write(header)
                f.write(t.payload)
                f.write(b"\r\n\r\n")

        # Compute hashes
        payload_hash = hashlib.sha256(primary.payload).hexdigest()

        header_subset = {
            k: primary.response_headers.get(k)
            for k in ["date", "server", "etag", "last-modified"]
            if primary.response_headers.get(k)
        }
        headers_hash = hashlib.sha256(
            json.dumps(header_subset, sort_keys=True).encode()
        ).hexdigest()

        return str(warc_path), payload_hash, headers_hash

    def _format_warc_header(self, t: HttpTransaction) -> bytes:
        """Format WARC record header."""
        warc_date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t.timestamp))
        return (
            f"WARC/1.0\r\n"
            f"WARC-Type: response\r\n"
            f"WARC-Target-URI: {t.url}\r\n"
            f"WARC-Date: {warc_date}\r\n"
            f"Content-Type: {t.content_type}\r\n"
            f"Content-Length: {len(t.payload)}\r\n"
            f"\r\n"
        ).encode()

    def clear(self):
        """Clear captured transactions."""
        self.transactions = []


class DiveCaptureGear:
    """
    Deep Freeze gear for web capture.

    Navigates to URLs, captures traffic, creates WARC archives.
    """

    def __init__(self, storage_path: str | Path = "./web_archive", config: dict | None = None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.stealth = StealthNavigator(config)

    async def execute(
        self,
        url: str,
        selector: str | None = None,
        wait_for: str | None = None,
        headless: bool = True,
    ) -> dict[str, Any]:
        """
        Execute a capture mission.

        Args:
            url: URL to capture
            selector: CSS selector to extract text from
            wait_for: CSS selector to wait for before capture
            headless: Run browser in headless mode

        Returns:
            CaptureResult as dict
        """
        if not PLAYWRIGHT_AVAILABLE:
            msg = (
                "Playwright not installed. "
                "Run: uv pip install playwright && playwright install chromium"
            )
            return CaptureResult(
                success=False,
                url=url,
                error=msg,
            ).to_dict()

        recorder = WarcRecorder(self.storage_path)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )

                # Apply stealth cloaking
                await self.stealth.cloak(context)

                page = await context.new_page()

                # Wire up recorder
                page.on("response", lambda r: recorder.intercept_response(r))

                # Resilient Navigation
                await self.stealth.goto_resilient(page, url)

                # Wait for selector if specified
                if wait_for:
                    try:
                        await page.wait_for_selector(wait_for, timeout=10000)
                    except Exception:
                        logger.warning(f"Timeout waiting for {wait_for}")

                # Extract content
                extracted = None
                if selector:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            extracted = await element.inner_text()
                    except Exception as e:
                        logger.warning(f"Extraction error: {e}")

                if not extracted:
                    # Try to get main content or body if no selector
                    try:
                        extracted = await page.content()  # Get full HTML for distillation
                    except Exception:
                        extracted = await page.title()

                # Freeze to WARC
                warc_path, payload_hash, headers_hash = recorder.freeze(url)

                await browser.close()

                return CaptureResult(
                    success=True,
                    url=url,
                    warc_path=warc_path,
                    payload_hash=payload_hash,
                    headers_hash=headers_hash,
                    extracted_content=extracted,
                ).to_dict()

        except Exception as e:
            logger.exception(f"Capture failed for {url}")
            return CaptureResult(
                success=False,
                url=url,
                error=str(e),
            ).to_dict()
