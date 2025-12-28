"""
Semantic Mapper - "The Translator"

Maps DOM state to Semantic representations for LLM consumption.
Extracts Accessibility Trees and Structured Metadata (JSON-LD, OpenGraph).
"""

from typing import Any

from playwright.async_api import Page


class SemanticMapper:
    """
    Maps DOM state to Semantic representations for LLM consumption.
    Extracts Accessibility Trees and Structured Metadata.
    """

    async def get_llm_friendly_accessibility_tree(self, page: Page) -> str:
        """
        Extracts the AX tree and formats it into a concise, indentation-based
        representation optimized for LLM token usage (removing redundant coordinates).
        """
        snapshot = await page.accessibility.snapshot(interesting_only=True)
        if not snapshot:
            return "No accessible content found."

        lines = []
        self._format_ax_node(snapshot, lines, depth=0)
        return "\n".join(lines)

    def _format_ax_node(self, node: dict, lines: list, depth: int):
        """Recursive formatter for AX nodes."""
        indent = "  " * depth
        role = node.get("role", "generic")
        name = node.get("name", "").replace("\n", " ")
        value = node.get("value")
        description = node.get("description")

        # Format: [role] "name" (value: X) | description
        line = f"{indent}- [{role}]"
        if name:
            line += f' "{name}"'
        if value:
            line += f" (value: {value})"
        if description:
            line += f" | {description}"

        lines.append(line)

        for child in node.get("children", []):
            self._format_ax_node(child, lines, depth + 1)

    async def extract_structured_data(self, page: Page) -> dict[str, Any]:
        """
        Extracts JSON-LD, OpenGraph, and Twitter Card data via JS evaluation.
        """
        return await page.evaluate("""() => {
            const data = {
                json_ld: [],
                open_graph: {},
                twitter_card: {},
                meta: {}
            };

            // Extract JSON-LD
            document.querySelectorAll('script[type="application/ld+json"]').forEach(script => {
                try {
                    data.json_ld.push(JSON.parse(script.innerText));
                } catch (e) {}
            });

            // Extract Meta Tags (OpenGraph, Twitter, Standard)
            document.querySelectorAll('meta').forEach(meta => {
                const name = meta.getAttribute('name') || meta.getAttribute('property');
                const content = meta.getAttribute('content');

                if (!name || !content) return;

                if (name.startsWith('og:')) {
                    data.open_graph[name.substring(3)] = content;
                } else if (name.startsWith('twitter:')) {
                    data.twitter_card[name.substring(8)] = content;
                } else {
                    data.meta[name] = content;
                }
            });

            return data;
        }""")
