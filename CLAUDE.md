# REASONKIT-WEB PROJECT CONTEXT
> The Sensing Layer for Autonomous Reasoning | Python MCP Server | Apache 2.0

**LICENSE:** Apache 2.0 (open source)
**REPOSITORY:** https://github.com/ReasonKit/reasonkit-web
**WEBSITE:** https://reasonkit.sh

---

## IDENTITY

If `reasonkit-core` is the **Brain**, `reasonkit-web` is the **Eyes and Ears**.

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
│  (Rust MCP Server)  │   │  (Python MCP Sidecar)       │
│                     │   │                             │
│  ✓ proof_anchor     │   │  ✓ web_capture (WARC)      │
│  ✓ proof_verify     │   │  ✓ web_sonar (entropy)      │
│  ✓ ProofLedger      │   │  ✓ web_triangulate         │
│  ✓ All ThinkTools   │   │  ✓ Browser automation      │
│                     │   │                             │
│  SQLite Ledger      │   │  WARC Archives             │
└─────────────────────┘   └─────────────────────────────┘
```

---

## TOOL MAPPING (NO DUPLICATION)

| Tool | Project | Purpose | When to Use |
|------|---------|---------|-------------|
| `web_capture` | **web** | Navigate + intercept + create WARC | Before citing any web source |
| `web_sonar` | **web** | Entropy-based saturation detection | During research loops |
| `web_triangulate` | **web** | Find 3 independent sources | Verifying claims |
| `proof_anchor` | **core** | Bind content hash to ledger | After web_capture returns |
| `proof_verify` | **core** | Check content drift | When re-visiting sources |
| `proof_lookup` | **core** | Query ledger by hash | Citation retrieval |

**Workflow:**
```
1. web_capture(url) → returns WARC path + content hash
2. proof_anchor(content, url) → binds to ProofLedger
3. Later: proof_verify(hash, new_content) → checks for drift
```

---

## TECHNOLOGY STACK

| Component | Technology | Purpose |
|-----------|------------|---------|
| Package Manager | `uv` (MANDATORY) | Dependency management |
| MCP Interface | `mcp` | Tool exposure |
| Browser | `playwright` | Web automation |
| Archiving | `warcio` | ISO 28500 WARC files |
| HTTP | `httpx` | Async HTTP client |

---

## DIRECTORY STRUCTURE

```
reasonkit-web/
├── pyproject.toml       # UV-managed dependencies
├── CLAUDE.md            # This file
├── src/
│   └── web/
│       ├── __init__.py
│       ├── server.py    # MCP server entrypoint
│       ├── gear/
│       │   ├── capture.py   # WARC creation + browser
│       │   └── sonar.py     # Entropy detection
│       └── storage/
│           └── __init__.py
├── legacy-reasonkit/    # Legacy Python ReasonKit package (archived from rk-startup)
└── tests/
```

---

## USAGE

### Installation
```bash
cd reasonkit-web
uv sync
uv run playwright install chromium
```

### Run MCP Server
```bash
uv run web
```

### Claude Desktop Config
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

---

## CONSTRAINTS (INHERITED)

| Constraint | Details |
|------------|---------|
| CONS-010 | UV ONLY - No pip |
| CONS-001 | No Node.js |
| CONS-005 | Performance paths in Rust (use core for ledger) |

---

*reasonkit-web v0.1.0 | The Sensing Layer | Apache 2.0*
