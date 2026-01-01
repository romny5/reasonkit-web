//! MCP stdio server implementation
//!
//! This module implements the MCP server that communicates over stdio,
//! handling JSON-RPC requests and dispatching to registered tools.

use crate::error::Result;
use crate::mcp::tools::ToolRegistry;
use crate::mcp::types::{
    JsonRpcRequest, JsonRpcResponse, McpCapabilities, McpServerInfo, ToolCallParams,
};
use serde_json::{json, Value};
use std::io::{self, BufRead, Write};
use tokio::sync::RwLock;
use tracing::{debug, error, info, instrument, warn};

/// MCP server state
pub struct McpServer {
    /// Tool registry
    tools: ToolRegistry,
    /// Server info
    info: McpServerInfo,
    /// Whether the server has been initialized
    initialized: RwLock<bool>,
}

impl McpServer {
    /// Create a new MCP server
    pub fn new() -> Self {
        Self {
            tools: ToolRegistry::new(),
            info: McpServerInfo::default(),
            initialized: RwLock::new(false),
        }
    }

    /// Run the MCP server (blocking)
    #[instrument(skip(self))]
    pub async fn run(&self) -> Result<()> {
        info!(
            "Starting MCP server: {} v{}",
            self.info.name, self.info.version
        );

        let stdin = io::stdin();
        let mut stdout = io::stdout();

        for line in stdin.lock().lines() {
            let line = match line {
                Ok(l) => l,
                Err(e) => {
                    error!("Failed to read line: {}", e);
                    continue;
                }
            };

            if line.trim().is_empty() {
                continue;
            }

            debug!("Received: {}", line);

            let response = self.handle_line(&line).await;

            if let Some(resp) = response {
                let json = serde_json::to_string(&resp).unwrap_or_else(|e| {
                    error!("Failed to serialize response: {}", e);
                    r#"{"jsonrpc":"2.0","error":{"code":-32603,"message":"Internal error"}}"#
                        .to_string()
                });

                debug!("Sending: {}", json);

                if let Err(e) = writeln!(stdout, "{}", json) {
                    error!("Failed to write response: {}", e);
                }
                if let Err(e) = stdout.flush() {
                    error!("Failed to flush stdout: {}", e);
                }
            }
        }

        info!("MCP server shutting down");
        Ok(())
    }

    /// Handle a single line of input
    async fn handle_line(&self, line: &str) -> Option<JsonRpcResponse> {
        // Try to parse as JSON-RPC request
        let request: JsonRpcRequest = match serde_json::from_str(line) {
            Ok(r) => r,
            Err(e) => {
                warn!("Failed to parse request: {}", e);
                return Some(JsonRpcResponse::parse_error());
            }
        };

        // Handle the request
        self.handle_request(request).await
    }

    /// Handle a JSON-RPC request
    #[instrument(skip(self, request))]
    async fn handle_request(&self, request: JsonRpcRequest) -> Option<JsonRpcResponse> {
        let id = request.id.clone();
        let method = request.method.as_str();

        info!("Handling method: {}", method);

        let result = match method {
            // Lifecycle methods
            "initialize" => self.handle_initialize(request.params).await,
            "initialized" => {
                // Notification, no response needed
                return None;
            }
            "shutdown" => self.handle_shutdown().await,

            // Tool methods
            "tools/list" => self.handle_tools_list().await,
            "tools/call" => self.handle_tools_call(request.params).await,

            // Ping (for testing)
            "ping" => Ok(json!({ "pong": true })),

            // Unknown method
            _ => {
                warn!("Unknown method: {}", method);
                return Some(JsonRpcResponse::method_not_found(id, method));
            }
        };

        Some(match result {
            Ok(value) => JsonRpcResponse::success(id, value),
            Err(e) => JsonRpcResponse::internal_error(id, &e.to_string()),
        })
    }

    /// Handle initialize request
    async fn handle_initialize(&self, params: Option<Value>) -> Result<Value> {
        info!("Handling initialize");

        // Validate protocol version if provided
        if let Some(ref p) = params {
            if let Some(version) = p.get("protocolVersion").and_then(|v| v.as_str()) {
                debug!("Client protocol version: {}", version);
                // We support MCP protocol version 2024-11-05 and earlier
            }
        }

        *self.initialized.write().await = true;

        Ok(json!({
            "protocolVersion": "2024-11-05",
            "capabilities": McpCapabilities::default(),
            "serverInfo": self.info
        }))
    }

    /// Handle shutdown request
    async fn handle_shutdown(&self) -> Result<Value> {
        info!("Handling shutdown");
        *self.initialized.write().await = false;
        Ok(json!(null))
    }

    /// Handle tools/list request
    async fn handle_tools_list(&self) -> Result<Value> {
        let definitions = self.tools.definitions();
        Ok(json!({
            "tools": definitions
        }))
    }

    /// Handle tools/call request
    async fn handle_tools_call(&self, params: Option<Value>) -> Result<Value> {
        let params = params.ok_or_else(|| crate::error::Error::generic("Missing params"))?;

        let tool_params: ToolCallParams = serde_json::from_value(params)
            .map_err(|e| crate::error::Error::generic(format!("Invalid params: {}", e)))?;

        let result = self
            .tools
            .execute(&tool_params.name, tool_params.arguments)
            .await;

        Ok(serde_json::to_value(result)?)
    }
}

impl Default for McpServer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mcp_server_new() {
        let server = McpServer::new();
        assert_eq!(server.info.name, "reasonkit-web");
    }

    #[tokio::test]
    async fn test_handle_ping() {
        let server = McpServer::new();
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            method: "ping".to_string(),
            params: None,
            id: Some(json!(1)),
        };

        let response = server.handle_request(request).await.unwrap();
        assert!(response.result.is_some());
        assert!(response.result.unwrap()["pong"].as_bool().unwrap());
    }

    #[tokio::test]
    async fn test_handle_initialize() {
        let server = McpServer::new();
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            method: "initialize".to_string(),
            params: Some(json!({
                "protocolVersion": "2024-11-05"
            })),
            id: Some(json!(1)),
        };

        let response = server.handle_request(request).await.unwrap();
        assert!(response.result.is_some());
        let result = response.result.unwrap();
        assert_eq!(result["protocolVersion"], "2024-11-05");
        assert!(result["capabilities"].is_object());
        assert!(result["serverInfo"].is_object());
    }

    #[tokio::test]
    async fn test_handle_tools_list() {
        let server = McpServer::new();
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            method: "tools/list".to_string(),
            params: None,
            id: Some(json!(2)),
        };

        let response = server.handle_request(request).await.unwrap();
        assert!(response.result.is_some());
        let result = response.result.unwrap();
        assert!(result["tools"].is_array());
        assert!(!result["tools"].as_array().unwrap().is_empty());
    }

    #[tokio::test]
    async fn test_handle_unknown_method() {
        let server = McpServer::new();
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            method: "unknown/method".to_string(),
            params: None,
            id: Some(json!(3)),
        };

        let response = server.handle_request(request).await.unwrap();
        assert!(response.error.is_some());
        assert_eq!(response.error.unwrap().code, -32601);
    }

    #[tokio::test]
    async fn test_handle_notification() {
        let server = McpServer::new();
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            method: "initialized".to_string(),
            params: None,
            id: None, // Notification
        };

        let response = server.handle_request(request).await;
        assert!(response.is_none()); // Notifications don't get responses
    }
}
