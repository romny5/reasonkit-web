use anyhow::Result;
use chromiumoxide::browser::{Browser, BrowserConfig};
use futures::StreamExt;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::io::{self, BufRead};
use tracing::{error, info, Level};
use tracing_subscriber::FmtSubscriber;

mod gear;
use gear::{ExtractionGear, InteractionGear, StealthNavigator, VisualFreezer};

// --- MCP Protocol Types (Simplified) ---

#[derive(Deserialize, Debug)]
struct JsonRpcRequest {
    #[allow(dead_code)]
    jsonrpc: String,
    method: String,
    params: Option<serde_json::Value>,
    id: Option<u64>,
}

#[derive(Serialize, Debug)]
struct JsonRpcResponse {
    jsonrpc: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    id: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<JsonRpcError>,
}

#[derive(Serialize, Debug)]
struct JsonRpcError {
    code: i32,
    message: String,
}

#[derive(Serialize, Debug)]
struct Tool {
    name: String,
    description: String,
    #[serde(rename = "inputSchema")]
    input_schema: serde_json::Value,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .with_writer(std::io::stderr) // MCP uses stdout for communication
        .finish();
    tracing::subscriber::set_global_default(subscriber).expect("setting default subscriber failed");

    info!("ReasonKit Web (Rust) starting...");

    // Stdin loop for MCP communication
    let stdin = io::stdin();
    for line in stdin.lock().lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }

        // Try to parse the request
        if let Ok(req) = serde_json::from_str::<JsonRpcRequest>(&line) {
            handle_request(req).await?;
        } else if let Ok(val) = serde_json::from_str::<serde_json::Value>(&line) {
            // If strict parsing fails, try to extract ID to report error
            let id = val.get("id").and_then(|v| v.as_u64());
            send_error(id, -32700, "Parse error");
        }
    }

    Ok(())
}

fn send_error(id: Option<u64>, code: i32, message: &str) {
    let response = JsonRpcResponse {
        jsonrpc: "2.0".to_string(),
        id,
        result: None,
        error: Some(JsonRpcError {
            code,
            message: message.to_string(),
        }),
    };
    if let Ok(json) = serde_json::to_string(&response) {
        println!("{}", json);
    }
}

async fn handle_request(req: JsonRpcRequest) -> Result<()> {
    let id = req.id;

    let response = match req.method.as_str() {
        "initialize" => {
            json!({
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "reasonkit-web-rs",
                    "version": "0.1.0"
                }
            })
        }
        "tools/list" => {
            let tools = vec![
                Tool {
                    name: "web_capture".to_string(),
                    description: "Captures a URL as MHTML and Screenshot using stealth browser"
                        .to_string(),
                    input_schema: json!({
                        "type": "object",
                        "properties": {
                            "url": { "type": "string" }
                        },
                        "required": ["url"]
                    }),
                },
                Tool {
                    name: "browser_action".to_string(),
                    description: "Performs an action (click, type, scroll) on a page".to_string(),
                    input_schema: json!({
                        "type": "object",
                        "properties": {
                            "url": { "type": "string" },
                            "action": { "type": "string", "enum": ["click", "type", "scroll"] },
                            "selector": { "type": "string" },
                            "text": { "type": "string" },
                            "x": { "type": "integer" },
                            "y": { "type": "integer" }
                        },
                        "required": ["url", "action"]
                    }),
                },
                Tool {
                    name: "extract_data".to_string(),
                    description: "Extracts text or HTML from a page".to_string(),
                    input_schema: json!({
                        "type": "object",
                        "properties": {
                            "url": { "type": "string" },
                            "type": { "type": "string", "enum": ["text", "html"] },
                            "selector": { "type": "string" }
                        },
                        "required": ["url", "type", "selector"]
                    }),
                },
            ];
            json!({ "tools": tools })
        }
        "tools/call" => {
            // Safe unwrap because we control the flow, but better to handle gracefully
            let params = req.params.unwrap_or(json!({}));
            let name = params.get("name").and_then(|v| v.as_str()).unwrap_or("");
            let args = params.get("arguments").cloned().unwrap_or(json!({}));

            if name == "web_capture" {
                if let Some(url) = args.get("url").and_then(|v| v.as_str()) {
                    match perform_web_capture(url).await {
                        Ok(result) => json!({ "content": [{ "type": "text", "text": result }] }),
                        Err(e) => {
                            error!("Web capture failed: {}", e);
                            json!({ "isError": true, "content": [{ "type": "text", "text": format!("Error: {}", e) }] })
                        }
                    }
                } else {
                    json!({ "isError": true, "content": [{ "type": "text", "text": "Missing URL" }] })
                }
            } else if name == "browser_action" {
                let url = args.get("url").and_then(|v| v.as_str()).unwrap_or("");
                let action = args.get("action").and_then(|v| v.as_str()).unwrap_or("");

                match perform_browser_action(url, action, &args).await {
                    Ok(result) => json!({ "content": [{ "type": "text", "text": result }] }),
                    Err(e) => {
                        error!("Browser action failed: {}", e);
                        json!({ "isError": true, "content": [{ "type": "text", "text": format!("Error: {}", e) }] })
                    }
                }
            } else if name == "extract_data" {
                let url = args.get("url").and_then(|v| v.as_str()).unwrap_or("");
                let type_ = args.get("type").and_then(|v| v.as_str()).unwrap_or("");
                let selector = args.get("selector").and_then(|v| v.as_str()).unwrap_or("");

                match perform_extraction(url, type_, selector).await {
                    Ok(result) => json!({ "content": [{ "type": "text", "text": result }] }),
                    Err(e) => {
                        error!("Extraction failed: {}", e);
                        json!({ "isError": true, "content": [{ "type": "text", "text": format!("Error: {}", e) }] })
                    }
                }
            } else {
                json!({ "isError": true, "content": [{ "type": "text", "text": "Unknown tool" }] })
            }
        }
        _ => return Ok(()), // Ignore unknown notifications or methods
    };

    let rpc_response = JsonRpcResponse {
        jsonrpc: "2.0".to_string(),
        id,
        result: Some(response),
        error: None,
    };

    println!("{}", serde_json::to_string(&rpc_response)?);
    Ok(())
}

async fn perform_web_capture(url: &str) -> Result<String> {
    info!("Launching stealth browser for {}", url);

    let config = BrowserConfig::builder()
        .with_head() // Start with head for debugging/stealth, or headless for prod
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to build browser config: {}", e))?;

    let (mut browser, mut handler) = Browser::launch(config).await?;

    let handle = tokio::task::spawn(async move {
        while let Some(h) = handler.next().await {
            if h.is_err() {
                break;
            }
        }
    });

    let page = browser.new_page("about:blank").await?;

    // 1. Cloak
    StealthNavigator::cloak(&page).await?;

    // 2. Navigate
    StealthNavigator::goto_resilient(&page, url).await?;

    // 3. Capture
    let mhtml = VisualFreezer::capture_mhtml(&page).await?;
    let screenshot = VisualFreezer::capture_screenshot(&page).await?;

    // In a real app, we'd save these to files or a DB.
    // For now, return a summary.
    let mhtml_len = mhtml.len();
    let screenshot_len = screenshot.len();

    browser.close().await?;
    handle.await?;

    Ok(format!(
        "Successfully captured {}. MHTML size: {} bytes, Screenshot size: {} bytes",
        url, mhtml_len, screenshot_len
    ))
}

async fn perform_browser_action(
    url: &str,
    action: &str,
    args: &serde_json::Value,
) -> Result<String> {
    info!("Performing browser action: {} on {}", action, url);

    let config = BrowserConfig::builder()
        .with_head()
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to build browser config: {}", e))?;

    let (mut browser, mut handler) = Browser::launch(config).await?;

    let handle = tokio::task::spawn(async move {
        while let Some(h) = handler.next().await {
            if h.is_err() {
                break;
            }
        }
    });

    let page = browser.new_page("about:blank").await?;
    StealthNavigator::cloak(&page).await?;
    StealthNavigator::goto_resilient(&page, url).await?;

    match action {
        "click" => {
            let selector = args.get("selector").and_then(|v| v.as_str()).unwrap_or("");
            InteractionGear::click(&page, selector).await?;
        }
        "type" => {
            let selector = args.get("selector").and_then(|v| v.as_str()).unwrap_or("");
            let text = args.get("text").and_then(|v| v.as_str()).unwrap_or("");
            InteractionGear::type_text(&page, selector, text).await?;
        }
        "scroll" => {
            let x = args.get("x").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            let y = args.get("y").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            InteractionGear::scroll(&page, x, y).await?;
        }
        _ => return Err(anyhow::anyhow!("Unknown action: {}", action)),
    }

    // Wait a bit for action to take effect
    tokio::time::sleep(std::time::Duration::from_millis(500)).await;

    browser.close().await?;
    handle.await?;

    Ok(format!("Successfully performed {} on {}", action, url))
}

async fn perform_extraction(url: &str, type_: &str, selector: &str) -> Result<String> {
    info!("Performing extraction: {} from {}", type_, url);

    let config = BrowserConfig::builder()
        .with_head()
        .build()
        .map_err(|e| anyhow::anyhow!("Failed to build browser config: {}", e))?;

    let (mut browser, mut handler) = Browser::launch(config).await?;

    let handle = tokio::task::spawn(async move {
        while let Some(h) = handler.next().await {
            if h.is_err() {
                break;
            }
        }
    });

    let page = browser.new_page("about:blank").await?;
    StealthNavigator::cloak(&page).await?;
    StealthNavigator::goto_resilient(&page, url).await?;

    let result = match type_ {
        "text" => ExtractionGear::extract_text(&page, selector).await?,
        "html" => ExtractionGear::extract_html(&page, selector).await?,
        _ => return Err(anyhow::anyhow!("Unknown extraction type: {}", type_)),
    };

    browser.close().await?;
    handle.await?;

    Ok(result)
}
