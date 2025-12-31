<div align="center">

<!-- Hero Banner - Web Sensing Layer -->
<img src="https://raw.githubusercontent.com/ReasonKit/reasonkit-core/main/brand/banners/cognitive-engine.png" alt="ReasonKit Web" width="100%" style="border-radius: 12px;">

# ReasonKit Web

**High-Performance Web Sensing & Browser Automation Layer**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square&color=%23a855f7)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.74%2B-orange?style=flat-square&logo=rust)](https://www.rust-lang.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green?style=flat-square&color=%2310b981)](https://modelcontextprotocol.io)

_The Eyes and Ears of AI Reasoning - Now Blazingly Fast_

[ReasonKit Core](https://github.com/ReasonKit/reasonkit-core) | [Documentation](https://reasonkit.sh/docs) | [Website](https://reasonkit.sh)

</div>

---

> **Note:** This is the **Rust implementation** of the ReasonKit Web Sensing layer. It supersedes the legacy Python prototype for performance-critical deployments.

Web sensing and browser automation layer for ReasonKit. Implements the Model Context Protocol (MCP) for seamless web interactions with AI reasoning systems, powered by Rust and ChromiumOxide.

## Features

- **Headless Browser Automation** - Full browser control via ChromiumOxide (CDP)
- **MCP Server** - Model Context Protocol for AI integration
- **Web Capture** - Screenshot, PDF, and HTML capture
- **Content Extraction** - Intelligent content parsing and triangulation
- **High Performance** - Async Rust runtime (Tokio) for low-latency operations

## Quick Start

```bash
# Build the server
cargo build --release

# Run the MCP server
./target/release/reasonkit-web
```

## Architecture

<div align="center">

```
┌─────────────────────────────────────────────────────────────────┐
│                      WEB SENSING LAYER (RUST)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   AI Agent ──▶ MCP Server ──▶ Browser Controller (CDP)         │
│                    │                │                           │
│                    ▼                ▼                           │
│              ┌──────────┐    ┌──────────────┐                   │
│              │ Capture  │    │ Triangulate  │                   │
│              └────┬─────┘    └──────┬───────┘                   │
│                   │                 │                           │
│                   ▼                 ▼                           │
│            Screenshots        Content + Sources                 │
│            PDFs, HTML        Verified Facts                     │
└─────────────────────────────────────────────────────────────────┘
```

</div>

## Technology Stack

| Component         | Technology    | Purpose               |
| ----------------- | ------------- | --------------------- |
| **Browser**       | ChromiumOxide | Async Rust CDP client |
| **MCP Server**    | mcp-sdk-rs    | AI agent integration  |
| **Runtime**       | Tokio         | Async runtime         |
| **Serialization** | Serde         | JSON handling         |

## License

Apache License 2.0 - see [LICENSE](LICENSE)

---

<div align="center">

**Part of the ReasonKit Ecosystem**

[ReasonKit Core](https://github.com/ReasonKit/reasonkit-core) • [ReasonKit Mem](https://github.com/ReasonKit/reasonkit-mem) • [Website](https://reasonkit.sh)

_"See How Your AI Thinks"_

</div>
