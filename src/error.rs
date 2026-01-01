//! Error types for ReasonKit Web
//!
//! This module provides a comprehensive error type hierarchy using `thiserror`
//! for proper error handling across all components.

use thiserror::Error;

/// The main error type for ReasonKit Web operations
#[derive(Error, Debug)]
pub enum Error {
    /// Browser-related errors
    #[error("Browser error: {0}")]
    Browser(#[from] BrowserError),

    /// MCP protocol errors
    #[error("MCP error: {0}")]
    Mcp(#[from] McpError),

    /// Content extraction errors
    #[error("Extraction error: {0}")]
    Extraction(#[from] ExtractionError),

    /// Navigation errors
    #[error("Navigation error: {0}")]
    Navigation(#[from] NavigationError),

    /// Capture errors (screenshot, PDF, etc.)
    #[error("Capture error: {0}")]
    Capture(#[from] CaptureError),

    /// I/O errors
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    /// JSON serialization/deserialization errors
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    /// ChromiumOxide errors
    #[error("CDP error: {0}")]
    Cdp(String),

    /// Generic error with message
    #[error("{0}")]
    Generic(String),
}

/// Browser lifecycle and control errors
#[derive(Error, Debug)]
pub enum BrowserError {
    /// Failed to launch browser
    #[error("Failed to launch browser: {0}")]
    LaunchFailed(String),

    /// Browser configuration error
    #[error("Invalid browser configuration: {0}")]
    ConfigError(String),

    /// Browser connection lost
    #[error("Browser connection lost")]
    ConnectionLost,

    /// Failed to create new page/tab
    #[error("Failed to create page: {0}")]
    PageCreationFailed(String),

    /// Browser already closed
    #[error("Browser already closed")]
    AlreadyClosed,

    /// Timeout waiting for browser
    #[error("Browser operation timed out after {0}ms")]
    Timeout(u64),
}

/// MCP protocol errors
#[derive(Error, Debug)]
pub enum McpError {
    /// Invalid JSON-RPC request
    #[error("Invalid JSON-RPC request: {0}")]
    InvalidRequest(String),

    /// Unknown method
    #[error("Unknown method: {0}")]
    UnknownMethod(String),

    /// Invalid parameters
    #[error("Invalid parameters: {0}")]
    InvalidParams(String),

    /// Tool not found
    #[error("Tool not found: {0}")]
    ToolNotFound(String),

    /// Tool execution failed
    #[error("Tool execution failed: {0}")]
    ToolExecutionFailed(String),

    /// Protocol version mismatch
    #[error("Protocol version mismatch: expected {expected}, got {actual}")]
    VersionMismatch {
        /// Expected version
        expected: String,
        /// Actual version received
        actual: String,
    },

    /// Parse error
    #[error("Parse error: {0}")]
    ParseError(String),
}

/// Content extraction errors
#[derive(Error, Debug)]
pub enum ExtractionError {
    /// Element not found
    #[error("Element not found: {0}")]
    ElementNotFound(String),

    /// Invalid selector
    #[error("Invalid selector: {0}")]
    InvalidSelector(String),

    /// Extraction failed
    #[error("Extraction failed: {0}")]
    ExtractionFailed(String),

    /// Content parsing failed
    #[error("Content parsing failed: {0}")]
    ParsingFailed(String),

    /// JavaScript execution failed
    #[error("JavaScript execution failed: {0}")]
    JsExecutionFailed(String),
}

/// Navigation errors
#[derive(Error, Debug)]
pub enum NavigationError {
    /// Invalid URL
    #[error("Invalid URL: {0}")]
    InvalidUrl(String),

    /// Navigation timeout
    #[error("Navigation timed out after {0}ms")]
    Timeout(u64),

    /// Page load failed
    #[error("Page load failed: {0}")]
    LoadFailed(String),

    /// SSL/TLS error
    #[error("SSL/TLS error: {0}")]
    SslError(String),

    /// Network error
    #[error("Network error: {0}")]
    NetworkError(String),

    /// HTTP error
    #[error("HTTP error {status}: {message}")]
    HttpError {
        /// HTTP status code
        status: u16,
        /// Error message
        message: String,
    },
}

/// Capture errors (screenshots, PDFs, etc.)
#[derive(Error, Debug)]
pub enum CaptureError {
    /// Screenshot failed
    #[error("Screenshot capture failed: {0}")]
    ScreenshotFailed(String),

    /// PDF generation failed
    #[error("PDF generation failed: {0}")]
    PdfFailed(String),

    /// MHTML capture failed
    #[error("MHTML capture failed: {0}")]
    MhtmlFailed(String),

    /// HTML capture failed
    #[error("HTML capture failed: {0}")]
    HtmlFailed(String),

    /// Invalid capture format
    #[error("Invalid capture format: {0}")]
    InvalidFormat(String),

    /// Capture timeout
    #[error("Capture timed out after {0}ms")]
    Timeout(u64),
}

/// Result type alias for ReasonKit Web operations
pub type Result<T> = std::result::Result<T, Error>;

impl Error {
    /// Create a generic error from a string
    pub fn generic<S: Into<String>>(msg: S) -> Self {
        Error::Generic(msg.into())
    }

    /// Create a CDP error from a string
    pub fn cdp<S: Into<String>>(msg: S) -> Self {
        Error::Cdp(msg.into())
    }
}

/// Convert chromiumoxide errors
impl From<chromiumoxide::error::CdpError> for Error {
    fn from(err: chromiumoxide::error::CdpError) -> Self {
        Error::Cdp(err.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_display() {
        let err = Error::Browser(BrowserError::LaunchFailed("no chrome".to_string()));
        assert!(err.to_string().contains("Failed to launch browser"));
        assert!(err.to_string().contains("no chrome"));
    }

    #[test]
    fn test_mcp_error() {
        let err = McpError::ToolNotFound("unknown_tool".to_string());
        assert_eq!(err.to_string(), "Tool not found: unknown_tool");
    }

    #[test]
    fn test_extraction_error() {
        let err = ExtractionError::ElementNotFound("#missing".to_string());
        assert!(err.to_string().contains("Element not found"));
    }

    #[test]
    fn test_navigation_error() {
        let err = NavigationError::HttpError {
            status: 404,
            message: "Not Found".to_string(),
        };
        assert!(err.to_string().contains("404"));
        assert!(err.to_string().contains("Not Found"));
    }

    #[test]
    fn test_generic_error() {
        let err = Error::generic("something went wrong");
        assert_eq!(err.to_string(), "something went wrong");
    }
}
