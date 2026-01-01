//! MCP protocol types
//!
//! This module defines the types used in the MCP JSON-RPC protocol.

use serde::{Deserialize, Serialize};
use serde_json::Value;

/// JSON-RPC 2.0 request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JsonRpcRequest {
    /// JSON-RPC version (always "2.0")
    pub jsonrpc: String,
    /// Method name
    pub method: String,
    /// Optional parameters
    #[serde(default)]
    pub params: Option<Value>,
    /// Request ID (None for notifications)
    pub id: Option<Value>,
}

/// JSON-RPC 2.0 response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JsonRpcResponse {
    /// JSON-RPC version (always "2.0")
    pub jsonrpc: String,
    /// Request ID
    #[serde(skip_serializing_if = "Option::is_none")]
    pub id: Option<Value>,
    /// Success result
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<Value>,
    /// Error result
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<JsonRpcError>,
}

impl JsonRpcResponse {
    /// Create a success response
    pub fn success(id: Option<Value>, result: Value) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            id,
            result: Some(result),
            error: None,
        }
    }

    /// Create an error response
    pub fn error(id: Option<Value>, code: i32, message: impl Into<String>) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            id,
            result: None,
            error: Some(JsonRpcError {
                code,
                message: message.into(),
                data: None,
            }),
        }
    }

    /// Create a parse error response
    pub fn parse_error() -> Self {
        Self::error(None, -32700, "Parse error")
    }

    /// Create an invalid request error
    pub fn invalid_request(id: Option<Value>) -> Self {
        Self::error(id, -32600, "Invalid Request")
    }

    /// Create a method not found error
    pub fn method_not_found(id: Option<Value>, method: &str) -> Self {
        Self::error(id, -32601, format!("Method not found: {}", method))
    }

    /// Create an invalid params error
    pub fn invalid_params(id: Option<Value>, msg: &str) -> Self {
        Self::error(id, -32602, format!("Invalid params: {}", msg))
    }

    /// Create an internal error
    pub fn internal_error(id: Option<Value>, msg: &str) -> Self {
        Self::error(id, -32603, format!("Internal error: {}", msg))
    }
}

/// JSON-RPC 2.0 error object
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JsonRpcError {
    /// Error code
    pub code: i32,
    /// Error message
    pub message: String,
    /// Optional additional data
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<Value>,
}

/// MCP server capabilities
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct McpCapabilities {
    /// Tools capability
    #[serde(default)]
    pub tools: ToolsCapability,
    /// Resources capability
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub resources: Option<ResourcesCapability>,
    /// Prompts capability
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub prompts: Option<PromptsCapability>,
}

/// Tools capability
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ToolsCapability {
    /// Whether tool list changes should be notified
    #[serde(default, rename = "listChanged")]
    pub list_changed: bool,
}

/// Resources capability (not implemented)
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ResourcesCapability {}

/// Prompts capability (not implemented)
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PromptsCapability {}

/// MCP server info
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpServerInfo {
    /// Server name
    pub name: String,
    /// Server version
    pub version: String,
}

impl Default for McpServerInfo {
    fn default() -> Self {
        Self {
            name: "reasonkit-web".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
        }
    }
}

/// MCP tool definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpToolDefinition {
    /// Tool name
    pub name: String,
    /// Tool description
    pub description: String,
    /// Input JSON schema
    #[serde(rename = "inputSchema")]
    pub input_schema: Value,
}

/// Parameters for tools/call method
#[derive(Debug, Clone, Deserialize)]
pub struct ToolCallParams {
    /// Tool name
    pub name: String,
    /// Tool arguments
    #[serde(default)]
    pub arguments: Value,
}

/// Result of a tool call
#[derive(Debug, Clone, Serialize)]
pub struct ToolCallResult {
    /// Whether the call was an error
    #[serde(rename = "isError", skip_serializing_if = "std::ops::Not::not")]
    pub is_error: bool,
    /// Content array
    pub content: Vec<ToolContent>,
}

impl ToolCallResult {
    /// Create a success result with text content
    pub fn text(text: impl Into<String>) -> Self {
        Self {
            is_error: false,
            content: vec![ToolContent::text(text)],
        }
    }

    /// Create a success result with image content
    pub fn image(data: String, mime_type: impl Into<String>) -> Self {
        Self {
            is_error: false,
            content: vec![ToolContent::image(data, mime_type)],
        }
    }

    /// Create an error result
    pub fn error(message: impl Into<String>) -> Self {
        Self {
            is_error: true,
            content: vec![ToolContent::text(message)],
        }
    }

    /// Create a result with multiple content items
    pub fn multi(content: Vec<ToolContent>) -> Self {
        Self {
            is_error: false,
            content,
        }
    }
}

/// Content item in tool result
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ToolContent {
    /// Text content
    #[serde(rename = "text")]
    Text {
        /// The text content
        text: String,
    },
    /// Image content
    #[serde(rename = "image")]
    Image {
        /// Base64 encoded image data
        data: String,
        /// MIME type
        #[serde(rename = "mimeType")]
        mime_type: String,
    },
    /// Resource content
    #[serde(rename = "resource")]
    Resource {
        /// Resource URI
        uri: String,
        /// Resource content
        resource: ResourceContent,
    },
}

impl ToolContent {
    /// Create text content
    pub fn text(text: impl Into<String>) -> Self {
        Self::Text { text: text.into() }
    }

    /// Create image content
    pub fn image(data: String, mime_type: impl Into<String>) -> Self {
        Self::Image {
            data,
            mime_type: mime_type.into(),
        }
    }
}

/// Resource content in tool result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceContent {
    /// MIME type
    #[serde(rename = "mimeType")]
    pub mime_type: String,
    /// Text content (for text resources)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub text: Option<String>,
    /// Binary content as base64 (for binary resources)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub blob: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_jsonrpc_request_deserialize() {
        let json = r#"{"jsonrpc":"2.0","method":"test","id":1}"#;
        let req: JsonRpcRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.method, "test");
        assert_eq!(req.id, Some(serde_json::json!(1)));
    }

    #[test]
    fn test_jsonrpc_response_success() {
        let resp =
            JsonRpcResponse::success(Some(serde_json::json!(1)), serde_json::json!({"ok": true}));
        let json = serde_json::to_string(&resp).unwrap();
        assert!(json.contains("\"result\""));
        assert!(!json.contains("\"error\""));
    }

    #[test]
    fn test_jsonrpc_response_error() {
        let resp = JsonRpcResponse::error(Some(serde_json::json!(1)), -32600, "Invalid");
        let json = serde_json::to_string(&resp).unwrap();
        assert!(json.contains("\"error\""));
        assert!(json.contains("-32600"));
    }

    #[test]
    fn test_tool_call_result_text() {
        let result = ToolCallResult::text("Hello, world!");
        assert!(!result.is_error);
        assert_eq!(result.content.len(), 1);
    }

    #[test]
    fn test_tool_call_result_error() {
        let result = ToolCallResult::error("Something went wrong");
        assert!(result.is_error);
    }

    #[test]
    fn test_tool_content_serialize() {
        let content = ToolContent::text("Hello");
        let json = serde_json::to_string(&content).unwrap();
        assert!(json.contains("\"type\":\"text\""));
        assert!(json.contains("\"text\":\"Hello\""));
    }

    #[test]
    fn test_mcp_capabilities() {
        let caps = McpCapabilities::default();
        assert!(!caps.tools.list_changed);
        assert!(caps.resources.is_none());
    }
}
