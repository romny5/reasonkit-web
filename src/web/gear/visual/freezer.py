"""
Visual Freezer - "The Camera"

Handles MHTML snapshots and visual screenshot capture.
Uses Chrome DevTools Protocol (CDP) for high-fidelity archiving.
"""

import logging

from playwright.async_api import Page

logger = logging.getLogger("web.visual")


class VisualFreezer:
    """
    Handles visual state preservation: MHTML snapshots and Screenshots.
    Uses Chrome DevTools Protocol (CDP) for full-page MHTML serialization.
    """

    @staticmethod
    async def capture_mhtml(page: Page) -> bytes:
        """
        Captures a full-page MHTML snapshot using CDP.
        This includes HTML, CSS, Images, and Frames in a single archive.
        """
        try:
            # Create a CDP session attached to the page
            client = await page.context.new_cdp_session(page)

            # Request Page.captureSnapshot with MHTML format
            # Reference: https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-captureSnapshot
            result = await client.send("Page.captureSnapshot", {"format": "mhtml"})

            # The data is returned as a large string, encode to bytes for storage
            return result["data"].encode("utf-8")
        except Exception as e:
            logger.error(f"MHTML capture failed: {e}")
            raise

    @staticmethod
    async def capture_screenshot(page: Page, full_page: bool = True, quality: int = 80) -> bytes:
        """
        Captures a visual screenshot (JPEG for compression efficiency).
        """
        return await page.screenshot(
            full_page=full_page,
            type="jpeg",
            quality=quality,
            animations="disabled",  # Freeze animations for consistent snapshots
        )
