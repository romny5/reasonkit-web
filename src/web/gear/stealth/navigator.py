"""
Stealth Navigator - "The Ghost"

Handles evasion of anti-bot detection and robust navigation.
Wraps Playwright context to inject stealth scripts and manage fingerprinting.
"""

import logging
import random
from typing import Any

from playwright.async_api import BrowserContext, Page

logger = logging.getLogger("web.stealth")


class StealthNavigator:
    """
    Navigator that evades detection and handles network resilience.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.mask_webgl = self.config.get("stealth.mask_webgl", True)
        self.fingerprint_rotation = self.config.get("browser.fingerprint_rotation", True)

    async def cloak(self, context: BrowserContext) -> None:
        """Apply stealth evasions to a browser context."""

        # 1. WebGL Override
        if self.mask_webgl:
            await context.add_init_script("""
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    // UNMASKED_VENDOR_WEBGL
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    // UNMASKED_RENDERER_WEBGL
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter(parameter);
                };
            """)

        # 2. WebDriver Removal
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # 3. Chrome Runtime Mock
        await context.add_init_script("""
            window.chrome = {
                runtime: {}
            };
        """)

        # 4. Plugins/MimeTypes Mock (Basic)
        await context.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        logger.debug("Stealth cloaking applied to context")

    async def goto_resilient(
        self, page: Page, url: str, wait_strategy: str = "domcontentloaded"
    ) -> bool:
        """
        Navigate to URL with retry logic and smart waiting.
        """
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # Add slight random delay before navigation to mimic human
                if attempt > 0:
                    delay = random.uniform(1.0, 3.0) * (2**attempt)
                    await page.wait_for_timeout(delay * 1000)

                logger.info(f"Navigating to {url} (attempt {attempt + 1})")

                await page.goto(url, wait_until=wait_strategy, timeout=30000)

                # Human-like scroll to trigger lazy loading
                await page.evaluate("""
                    window.scrollTo({
                        top: 100,
                        behavior: 'smooth'
                    });
                """)
                await page.wait_for_timeout(random.randint(500, 1500))

                return True

            except Exception as e:
                logger.warning(f"Navigation failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    raise e

        return False
