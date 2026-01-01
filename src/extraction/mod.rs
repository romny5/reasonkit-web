//! Content extraction module
//!
//! This module provides intelligent content extraction from web pages,
//! including main content, metadata, and link extraction.

mod content;
mod links;
mod metadata;

pub use content::{ContentExtractor, ExtractedContent};
pub use links::{ExtractedLink, LinkExtractor, LinkType};
pub use metadata::{MetadataExtractor, OpenGraphData, PageMetadata, TwitterCardData};
