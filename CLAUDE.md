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

## TASK MANAGEMENT (MANDATORY - CONS-007)

> **Axiom:** No work exists without task tracking. ALL AI agents MUST use the full task system.

### Taskwarrior Integration

**ALL AI agents MUST use Taskwarrior for task tracking.**

```bash
# Create task (MANDATORY format for RK-PROJECT)
task add project:rk-project.web.{component} "{description}" priority:{H|M|L} due:{date} +{tags}

# Examples:
task add project:rk-project.web.capture "Implement WARC creation" priority:H due:today +python +mcp
task add project:rk-project.web.sonar "Add entropy detection" priority:M due:friday +automation
task add project:rk-project.web.triangulate "Build source triangulation" priority:M due:tomorrow +research

# Start working (CRITICAL: Auto-starts timewarrior!)
task {id} start

# Stop working (pauses time tracking)
task {id} stop

# Complete task (stops timewarrior, records completion)
task {id} done

# Add annotations (progress notes, decisions, blockers)
task {id} annotate "Completed WARC capture, tested with 10 sites"
task {id} annotate "BLOCKED: Waiting for Playwright update"
task {id} annotate "DECISION: Using warcio over custom WARC writer"

# View status
task project:rk-project.web list
task project:rk-project.web summary
timew summary :week
```

**Components:**
- `web.capture` → WARC creation and browser automation
- `web.sonar` → Entropy-based saturation detection
- `web.triangulate` → Source triangulation for verification
- `web.storage` → WARC archive management

**Full Documentation:** See `ORCHESTRATOR.md` for complete Taskwarrior reference.

---

## MCP SERVERS, SKILLS & PLUGINS (MAXIMIZE)

### MCP Server Usage

**Agents MUST leverage MCP servers for all compatible operations.**

```yaml
MCP_SERVERS_PRIORITY:
  - sequential-thinking   # ALWAYS use for complex reasoning chains
  - filesystem            # File operations
  - github               # Repository operations
  - memory               # Persistent memory
  - puppeteer            # Web automation (reasonkit-web provides this)
  - fetch                # HTTP requests with caching

USAGE_PATTERN:
  1. Check if MCP server exists for operation
  2. If yes: USE IT (preferred over direct implementation)
  3. If no: Implement in Rust, consider creating MCP server
```

### Skills & Plugins

```yaml
SKILLS_MAXIMIZATION:
  - Use pdf skill for PDF operations
  - Use xlsx skill for spreadsheet operations
  - Use docx skill for document operations
  - Use frontend-design skill for UI work
  - Use mcp-builder skill for MCP server creation

PLUGIN_PRIORITY:
  - api-contract-sync for API validation
  - math for deterministic calculations
  - experienced-engineer agents for specialized tasks
```

### Extensions

```yaml
BROWSER_EXTENSIONS:
  - Use when web research needed
  - Prefer official provider extensions

IDE_EXTENSIONS:
  - Cursor: .cursorrules enforcement
  - VS Code: copilot-instructions.md
  - Windsurf: .windsurfrules
```

**Full Reference:** See [ORCHESTRATOR.md](../../ORCHESTRATOR.md#mcp-servers-skills--plugins-maximize) for complete MCP/Skills/Plugins documentation.

---

## CONSTRAINTS (INHERITED)

| Constraint | Details |
|------------|---------|
| CONS-010 | UV ONLY - No pip |
| CONS-001 | No Node.js |
| CONS-005 | Performance paths in Rust (use core for ledger) |

---

*reasonkit-web v0.1.0 | The Sensing Layer | Apache 2.0*
