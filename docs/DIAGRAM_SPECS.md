# Visual Asset Specifications: ReasonKit Web

> **Status:** SPECIFICATION ONLY
> **Target:** Design Team / Generation Scripts
> **Brand Identity:** See `../BRAND_IDENTITY.md` (Cyan #06b6d4, Purple #a855f7, Void Black #030508)
> **Font:** JetBrains Mono (Technical labels), Inter (Headers)

This document contains the exact content, structure, and data required to generate the visual assets referenced in the `README.md`.

---

## 1. Technology Stack Diagram
**Filename:** `tech_stack.png`
**Type:** Stacked Layer Diagram

### Content Layers (Bottom to Top)

1.  **Foundation Layer (System)**
    *   **Color:** `#1e293b` (Slate 800)
    *   **Label:** "System"
    *   **Items:**
        *   "Linux / macOS / Windows" (Icon: OS generic)
        *   "Headless Chromium" (Icon: Chrome/Chromium)

2.  **Runtime Layer (Rust)**
    *   **Color:** `#f97316` (Rust Orange)
    *   **Label:** "Rust Runtime (Tokio)"
    *   **Items:**
        *   "ChromiumOxide" (CDP Client)
        *   "Tokio" (Async I/O)
        *   "Serde" (Zero-copy Serialization)

3.  **Application Layer**
    *   **Color:** `#06b6d4` (Brand Cyan)
    *   **Label:** "ReasonKit Web"
    *   **Items:**
        *   "Browser Controller"
        *   "Content Extractor"
        *   "Resource Monitor"

4.  **Interface Layer**
    *   **Color:** `#10b981` (Green)
    *   **Label:** "Interface"
    *   **Items:**
        *   "Model Context Protocol (MCP)"
        *   "Stdio / HTTP Transport"

### Flow Arrows
*   Upward arrow from Foundation to Runtime: "CDP (Chrome DevTools Protocol)"
*   Upward arrow from Runtime to Application: "Async Events"
*   Upward arrow from Application to Interface: "JSON-RPC 2.0"

---

## 2. Ecosystem Connection Diagram
**Filename:** `ecosystem_connection.png`
**Type:** Hub-and-Spoke Network Diagram

### Central Hub
*   **Node:** "ReasonKit Orchestrator" (reasonkit-core)
*   **Icon:** Brain/Processor
*   **Color:** `#a855f7` (Purple)

### Peripheral Nodes
1.  **Node A:** "ReasonKit Web" (This Repo)
    *   **Role:** "Sensing"
    *   **Connection:** "MCP (Tools)"
    *   **Color:** `#06b6d4` (Cyan)
    *   **Data Flow:** Returns: HTML, Screenshots, Accessibility Tree

2.  **Node B:** "ReasonKit Mem"
    *   **Role:** "Memory"
    *   **Connection:** "Vector Search"
    *   **Color:** `#10b981` (Green)
    *   **Data Flow:** Stores: Embeddings, Snapshots

3.  **Node C:** "LLM Provider"
    *   **Role:** "Intelligence"
    *   **Connection:** "API"
    *   **Color:** `#f59e0b` (Amber)
    *   **Data Flow:** Logic, Decision Making

### Connections
*   Solid lines connecting all Peripherals to the Center.
*   Dotted line between "ReasonKit Web" and "ReasonKit Mem" labeled: "Direct Archival (Optional)"

---

## 3. Performance Benchmark Visualization
**Filename:** `performance_benchmark.png`
**Type:** Horizontal Bar Chart

### Data Points

| Metric | Python (Selenium) | Node.js (Puppeteer) | ReasonKit Web (Rust) |
| :--- | :--- | :--- | :--- |
| **Startup Time** | 1.2s | 0.8s | **0.05s** |
| **Memory Footprint** | 250MB | 180MB | **35MB** |
| **Page Extraction** | 450ms | 320ms | **120ms** |
| **Concurrent Tabs** | ~15 | ~25 | **100+** |

### Style Guide
*   **ReasonKit Bar:** Brand Cyan (`#06b6d4`), Glowing effect, labeled "10x Faster".
*   **Competitor Bars:** Grey (`#475569`), muted.
*   **Background:** Dark Grid.
*   **Y-Axis:** "Time/Resources (Lower is Better)" (except for Concurrent Tabs).

---

## 4. Use Case Scenarios Visual
**Filename:** `use_cases.png`
**Type:** 3-Column Card Layout

### Card 1: Research
*   **Icon:** Magnifying Glass
*   **Title:** "Autonomous Research"
*   **Text:** "Deep crawling of documentation, academic papers, and technical specifications with automated citation tracking."
*   **Tags:** `read_page`, `search_google`

### Card 2: Monitoring
*   **Icon:** Pulse/Waveform
*   **Title:** "Visual Monitoring"
*   **Text:** "Change detection on dynamic single-page applications (SPAs) to trigger system alerts or memory updates."
*   **Tags:** `screenshot`, `element_diff`

### Card 3: Testing
*   **Icon:** Checkmark Shield
*   **Title:** "E2E Validation"
*   **Text:** "Validate deployment health by simulating user interactions and checking visual integrity."
*   **Tags:** `click`, `fill_form`

---

## 5. API Workflow Diagram
**Filename:** `api_workflow.png`
**Type:** Sequence Diagram

### Actors
1.  **User/Agent**
2.  **MCP Server**
3.  **Browser**

### Sequence Steps
1.  **User** sends: `call_tool("read_page", { url: "..." })`
2.  **MCP Server** validates input schema (Serde).
3.  **MCP Server** spawns/reuses Chromium tab.
4.  **Browser** navigates & renders (JS execution).
5.  **Browser** returns DOM tree.
6.  **MCP Server** extracts Markdown + Metadata.
7.  **MCP Server** sanitizes content (removes scripts/styles).
8.  **MCP Server** returns: `TextContent { type: "text", text: "..." }`

### Annotations
*   **Critical:** "Sandboxed Execution" label over the Browser section.
*   **Critical:** "Zero-Copy" label on the return path.
