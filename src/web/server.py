"""
ReasonKit Web MCP Server

The Sensing Layer for Autonomous Reasoning.
Exposes browser automation and WARC archiving as MCP tools.

Tools:
- web.capture: Deep Freeze - Navigate, intercept, create WARC archive
- web.sonar: Drift Detection - Monitor entropy/saturation in research threads
- web.triangulate: Cross-Verify - Find 3 independent sources for claims

Note: For ledger operations (anchor, verify), use reasonkit-core's
ProofLedger tools (proof_anchor, proof_verify) via MCP.
"""

import asyncio
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .gear.capture import DiveCaptureGear
from .gear.density.distill import ContentDistiller
from .gear.sonar import DiveSonarGear

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web")

# Initialize gear
capture_gear = DiveCaptureGear()
sonar_gear = DiveSonarGear()
distiller = ContentDistiller()

# Create MCP server
server = Server("reasonkit-web")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Web tools."""
    return [
        Tool(
            name="web_capture",
            description=(
                "Deep Freeze: Navigate to URL, intercept network traffic, "
                "and create an immutable WARC archive. Use this BEFORE making "
                "claims based on web sources. Returns WARC path and content hash. "
                "For ledger anchoring, call proof_anchor from reasonkit-core."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to capture",
                    },
                    "selector": {
                        "type": "string",
                        "description": "Optional CSS selector to extract specific content",
                    },
                    "wait_for": {
                        "type": "string",
                        "description": "Optional selector to wait for before capture",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="web_sonar",
            description=(
                "Drift Detection: Analyze text for information saturation. "
                "Detects when research is looping or seeing redundant content. "
                "Returns entropy score and 'surface now' recommendation if saturated."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "new_text": {
                        "type": "string",
                        "description": "New text to analyze for novelty",
                    },
                    "context": {
                        "type": "string",
                        "description": "Existing knowledge/context to compare against",
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Information gain threshold (default: 1.05)",
                        "default": 1.05,
                    },
                },
                "required": ["new_text", "context"],
            },
        ),
        Tool(
            name="web_triangulate",
            description=(
                "Cross-Verify: Search for 3 independent sources confirming a claim. "
                "Uses web search to find corroborating evidence. Returns sources "
                "with confidence scores."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "claim": {
                        "type": "string",
                        "description": "The claim to verify with multiple sources",
                    },
                    "min_sources": {
                        "type": "integer",
                        "description": "Minimum sources required (default: 3)",
                        "default": 3,
                    },
                },
                "required": ["claim"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name in {"web_capture", "dive_capture"}:
            result = await capture_gear.execute(
                url=arguments["url"],
                selector=arguments.get("selector"),
                wait_for=arguments.get("wait_for"),
            )

            # Auto-distill if content was extracted
            if result.get("extracted_content") and arguments.get("distill", True):
                # If extracted_content looks like HTML (starts with <), distill it
                content = result["extracted_content"]
                if isinstance(content, str) and content.strip().startswith("<"):
                    result["extracted_content"] = distiller.distill(content)
        elif name in {"web_sonar", "dive_sonar"}:
            result = sonar_gear.analyze(
                new_text=arguments["new_text"],
                context=arguments["context"],
                threshold=arguments.get("threshold", 1.05),
            )
        elif name in {"web_triangulate", "dive_triangulate"}:
            # This is a stub implementation. In a real scenario, this would trigger
            # autonomous research via the agent to find sources.
            # Here we just analyze the claim structure.
            result = {
                "status": "pending_implementation",
                "message": (
                    "To use triangulation, the agent must perform search. "
                    "This tool is a placeholder for the logic engine."
                ),
            }
        else:
            result = {"error": f"Unknown tool: {name}"}

        import json

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.exception(f"Tool {name} failed")
        return [TextContent(type="text", text=f"Error: {e!s}")]


def main() -> int:
    """Run the Web MCP server."""
    if "-h" in sys.argv or "--help" in sys.argv:
        print("Usage: web\n\nRuns the ReasonKit Web MCP server over stdio.")
        return 0

    logger.info("Starting ReasonKit Web MCP Server...")
    asyncio.run(_run_server())
    return 0


async def _run_server() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    main()
