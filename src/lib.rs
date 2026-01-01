//! ReasonKit Web - High-Performance Web Sensing & Browser Automation Layer
//!
//! This crate provides a production-ready MCP (Model Context Protocol) server
//! for web sensing, browser automation, and content extraction.
//!
//! # Features
//!
//! - **MCP Server**: Full MCP stdio server for AI agent integration
//! - **Browser Automation**: Headless browser control via ChromiumOxide (CDP)
//! - **Web Capture**: Screenshot, PDF, and HTML capture
//! - **Content Extraction**: Intelligent content parsing and metadata extraction
//!
//! # Architecture
//!
//! ```text
//! AI Agent ──▶ MCP Server ──▶ Browser Controller (CDP)
//!                  │                │
//!                  ▼                ▼
//!            ┌──────────┐    ┌──────────────┐
//!            │ Capture  │    │ Extraction   │
//!            └────┬─────┘    └──────┬───────┘
//!                 │                 │
//!                 ▼                 ▼
//!           Screenshots        Content + Metadata
//!           PDFs, HTML         Links, Structured Data
//! ```
//!
//! # Quick Start
//!
//! ```rust,no_run
//! use reasonkit_web::browser::BrowserController;
//! use reasonkit_web::extraction::ContentExtractor;
//!
//! #[tokio::main]
//! async fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     // Create a browser controller
//!     let controller = BrowserController::new().await?;
//!     
//!     // Navigate and extract
//!     let page = controller.navigate("https://example.com").await?;
//!     let content = ContentExtractor::extract_main_content(&page).await?;
//!     
//!     println!("Extracted: {}", content.text);
//!     Ok(())
//! }
//! ```

#![warn(missing_docs)]
#![warn(rustdoc::missing_crate_level_docs)]

pub mod browser;
pub mod error;
pub mod extraction;
pub mod mcp;

// Re-exports for convenience
pub use browser::BrowserController;
pub use error::{Error, Result};
pub use extraction::{ContentExtractor, LinkExtractor, MetadataExtractor};
pub use mcp::{McpServer, McpTool};

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Library name
pub const NAME: &str = env!("CARGO_PKG_NAME");
