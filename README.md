# ReasonKit Web

> The Sensing Layer for Autonomous Reasoning

**ReasonKit Web** is the Python MCP (Model Context Protocol) sidecar for ReasonKit. It provides web sensing capabilities including browser automation, WARC archiving, and source triangulation.

## Features

- **Web Capture** - Full page capture with WARC archiving (ISO 28500)
- **Web Sonar** - Entropy-based saturation detection for research loops
- **Web Triangulate** - Find 3+ independent sources for claim verification
- **Browser Automation** - Playwright-based stealth browser

## Installation

```bash
# Clone the repository
git clone https://github.com/reasonkit/reasonkit-web.git
cd reasonkit-web

# Install dependencies (requires uv)
uv sync

# Install browser
uv run playwright install chromium
```

## Usage

### Run MCP Server

```bash
uv run web
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "reasonkit-web": {
      "command": "uv",
      "args": ["run", "web"],
      "cwd": "/path/to/reasonkit-web"
    }
  }
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AGENT (Claude/Gemini)                │
│                          ↓                              │
│                    MCP Client                           │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ↓                           ↓
┌─────────────────────┐   ┌─────────────────────────────┐
│  reasonkit-core     │   │  reasonkit-web              │
│  (Rust - Brain)     │   │  (Python - Eyes)            │
│                     │   │                             │
│  ✓ ThinkTools       │   │  ✓ web_capture (WARC)      │
│  ✓ ProofLedger      │   │  ✓ web_sonar (entropy)      │
│  ✓ Verification     │   │  ✓ web_triangulate         │
└─────────────────────┘   └─────────────────────────────┘
```

## Tools

| Tool | Purpose | Output |
|------|---------|--------|
| `web_capture` | Navigate + intercept + create WARC | WARC path + content hash |
| `web_sonar` | Detect information saturation | Entropy score |
| `web_triangulate` | Find independent sources | 3+ source URLs |

## Requirements

- Python 3.11+
- uv (package manager)
- Chromium (installed via Playwright)

## License

Apache License 2.0 - see [LICENSE](LICENSE)

## Links

- [ReasonKit Core](https://github.com/reasonkit/reasonkit-core) - The reasoning engine
- [ReasonKit Mem](https://github.com/reasonkit/reasonkit-mem) - Memory infrastructure
- [Website](https://reasonkit.sh) - Official website
