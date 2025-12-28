"""
Content Distiller - "The Essence"

Strips boilerplate, noise, and navigation elements to extract core content.
Converts to Markdown for optimal LLM consumption.
"""

import logging
import re
from typing import Any

import html2text

logger = logging.getLogger("web.density")


class ContentDistiller:
    """
    Distills HTML into density-optimized Markdown.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.format = self.config.get("density.format", "markdown")

        # Configure HTML2Text
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_emphasis = False
        self.h2t.skip_internal_links = True
        self.h2t.body_width = 0  # No wrapping

    def distill(self, html_content: str) -> str:
        """
        Convert HTML to clean Markdown, stripping noise.
        """
        if not html_content:
            return ""

        try:
            # 1. Pre-process HTML (basic noise reduction)
            # Remove scripts, styles, comments
            cleaned_html = re.sub(
                r"<(script|style|noscript)[^>]*>.*?</\1>", "", html_content, flags=re.DOTALL
            )
            cleaned_html = re.sub(r"<!--.*?-->", "", cleaned_html, flags=re.DOTALL)

            # 2. Convert to Markdown
            markdown = self.h2t.handle(cleaned_html)

            # 3. Post-process Markdown (remove excessive whitespace)
            markdown = re.sub(r"\n{3,}", "\n\n", markdown)
            markdown = markdown.strip()

            # 4. Remove common footer/nav noise patterns (heuristic)
            # (Simple implementation - in production use Readability.js logic)
            lines = markdown.split("\n")
            filtered_lines = []

            for line in lines:
                # Filter out obvious cookie notices or short nav items
                if "cookie" in line.lower() and "accept" in line.lower():
                    continue
                filtered_lines.append(line)

            return "\n".join(filtered_lines)

        except Exception as e:
            logger.error(f"Distillation failed: {e}")
            return html_content  # Fallback to raw
