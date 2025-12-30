"""
Browser Manager - Cross-Platform Browser Automation

Unified browser automation across Chrome, Firefox, Safari, and Edge.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger("web.browser")


class BrowserType(Enum):
    """Supported browser types."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"
    EDGE = "edge"


class BrowserProfile(Enum):
    """Browser profile types."""

    DEFAULT = "default"
    AUTOMATION = "automation"
    STEALTH = "stealth"


@dataclass
class BrowserConfig:
    """Browser configuration."""

    browser_type: BrowserType
    profile: BrowserProfile
    headless: bool = True
    window_size: Tuple[int, int] = (1920, 1080)
    user_agent: Optional[str] = None
    viewport_size: Optional[Tuple[int, int]] = None
    locale: str = "en-US"
    ignore_https_errors: bool = True
    java_script_enabled: bool = True


@dataclass
class BrowserSession:
    """Browser session information."""

    session_id: str
    browser: Browser
    context: BrowserContext
    pages: List[Page]
    start_time: float
    config: BrowserConfig
    errors: List[str]


class CrossPlatformBrowserManager:
    """
    Cross-Platform Browser Manager

    Provides unified browser automation across all major browsers.
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        self.playwright: Optional[Playwright] = None
        self.active_sessions: Dict[str, BrowserSession] = {}

    async def start_browser(
        self,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        config: Optional[BrowserConfig] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Start a new browser session."""
        if not self.playwright:
            self.playwright = await async_playwright().start()

        if session_id is None:
            session_id = f"session_{int(time.time())}_{browser_type.value}"

        browser_config = config or BrowserConfig(
            browser_type=browser_type, profile=BrowserProfile.AUTOMATION
        )

        try:
            # Start browser based on type
            if browser_type == BrowserType.CHROMIUM:
                browser = await self.playwright.chromium.launch(
                    headless=browser_config.headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
            elif browser_type == BrowserType.FIREFOX:
                browser = await self.playwright.firefox.launch(headless=browser_config.headless)
            elif browser_type == BrowserType.WEBKIT:
                browser = await self.playwright.webkit.launch(headless=browser_config.headless)
            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")

            # Create context
            context_options = {
                "viewport": browser_config.viewport_size or browser_config.window_size,
                "locale": browser_config.locale,
                "ignore_https_errors": browser_config.ignore_https_errors,
                "java_script_enabled": browser_config.java_script_enabled,
            }

            if browser_config.user_agent:
                context_options["user_agent"] = browser_config.user_agent

            context = await browser.new_context(**context_options)

            # Create initial page
            page = await context.new_page()

            # Store session
            session = BrowserSession(
                session_id=session_id,
                browser=browser,
                context=context,
                pages=[page],
                start_time=time.time(),
                config=browser_config,
                errors=[],
            )

            self.active_sessions[session_id] = session

            logger.info(f"Started {browser_type.value} browser session: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to start {browser_type.value} browser: {e}")
            raise

    async def get_page(self, session_id: str, page_id: Optional[int] = None) -> Page:
        """Get a page from browser session."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self.active_sessions[session_id]

        if page_id is not None:
            if page_id < 0 or page_id >= len(session.pages):
                raise ValueError(f"Page ID {page_id} out of range")
            return session.pages[page_id]

        # Create new page
        page = await session.context.new_page()
        session.pages.append(page)
        return page

    async def navigate(
        self, session_id: str, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000
    ) -> Dict[str, Any]:
        """Navigate to URL in browser session."""
        page = await self.get_page(session_id)

        start_time = time.time()

        try:
            response = await page.goto(url, wait_until=wait_until, timeout=timeout)

            navigation_result = {
                "success": True,
                "url": page.url,
                "status_code": response.status if response else None,
                "load_time": time.time() - start_time,
                "timestamp": time.time(),
            }

            logger.info(f"Navigated to {url} in session {session_id}")
            return navigation_result

        except Exception as e:
            error_msg = f"Navigation failed: {e}"
            logger.error(error_msg)

            session = self.active_sessions[session_id]
            session.errors.append(error_msg)

            return {
                "success": False,
                "error": error_msg,
                "url": url,
                "load_time": time.time() - start_time,
                "timestamp": time.time(),
            }

    async def get_browser_info(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive browser session information."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self.active_sessions[session_id]

        page_info = []
        for i, page in enumerate(session.pages):
            try:
                page_info.append(
                    {
                        "page_id": i,
                        "url": page.url,
                        "title": await page.title(),
                        "viewport": page.viewport_size,
                    }
                )
            except Exception as e:
                page_info.append({"page_id": i, "error": str(e)})

        return {
            "session_id": session.session_id,
            "browser_type": session.config.browser_type.value,
            "uptime": time.time() - session.start_time,
            "pages": page_info,
            "error_count": len(session.errors),
            "errors": session.errors[-5:],
        }

    async def close_session(self, session_id: str) -> bool:
        """Close browser session."""
        if session_id not in self.active_sessions:
            logger.warning(f"Session not found: {session_id}")
            return False

        session = self.active_sessions[session_id]

        try:
            # Close all pages
            for page in session.pages:
                try:
                    await page.close()
                except Exception as e:
                    logger.debug(f"Error closing page: {e}")

            # Close context and browser
            await session.context.close()
            await session.browser.close()

            # Remove from active sessions
            del self.active_sessions[session_id]

            logger.info(f"Closed browser session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error closing session {session_id}: {e}")
            return False

    async def close_all_sessions(self) -> int:
        """Close all active browser sessions."""
        closed_count = 0

        for session_id in list(self.active_sessions.keys()):
            if await self.close_session(session_id):
                closed_count += 1

        # Close Playwright
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        return closed_count

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on browser manager."""
        return {
            "timestamp": time.time(),
            "playwright_initialized": self.playwright is not None,
            "active_sessions": len(self.active_sessions),
            "available_browsers": ["chromium", "firefox", "webkit"],
        }
