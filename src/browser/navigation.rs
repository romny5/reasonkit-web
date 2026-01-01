//! Page navigation functionality
//!
//! This module handles URL navigation with retry logic, timeout handling,
//! and human-like behavior simulation.

use crate::browser::PageHandle;
use crate::error::{Error, NavigationError, Result};
use std::time::Duration;
use tracing::{debug, info, instrument, warn};

/// Options for page navigation
#[derive(Debug, Clone)]
pub struct NavigationOptions {
    /// Timeout in milliseconds (default: 30000)
    pub timeout_ms: u64,
    /// Wait until condition (default: networkidle0)
    pub wait_until: WaitUntil,
    /// Number of retry attempts (default: 3)
    pub retries: u32,
    /// Delay between retries in ms (default: 1000)
    pub retry_delay_ms: u64,
    /// Simulate human-like behavior (default: true)
    pub human_like: bool,
}

impl Default for NavigationOptions {
    fn default() -> Self {
        Self {
            timeout_ms: 30000,
            wait_until: WaitUntil::NetworkIdle0,
            retries: 3,
            retry_delay_ms: 1000,
            human_like: true,
        }
    }
}

/// Condition to wait for after navigation
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WaitUntil {
    /// Wait until load event fires
    Load,
    /// Wait until DOMContentLoaded event fires
    DomContentLoaded,
    /// Wait until network is idle (0 connections for 500ms)
    NetworkIdle0,
    /// Wait until network is idle (max 2 connections for 500ms)
    NetworkIdle2,
}

/// Result of a navigation operation
#[derive(Debug)]
pub struct NavigationResult {
    /// Final URL after any redirects
    pub final_url: String,
    /// HTTP status code
    pub status: Option<u16>,
    /// Page title
    pub title: Option<String>,
    /// Navigation duration in milliseconds
    pub duration_ms: u64,
}

/// Page navigator with advanced navigation capabilities
pub struct PageNavigator;

impl PageNavigator {
    /// Navigate to a URL with default options
    #[instrument(skip(page))]
    pub async fn goto(
        page: &PageHandle,
        url: &str,
        options: Option<NavigationOptions>,
    ) -> Result<NavigationResult> {
        let opts = options.unwrap_or_default();
        let start = std::time::Instant::now();

        // Validate URL
        if !url.starts_with("http://")
            && !url.starts_with("https://")
            && !url.starts_with("file://")
        {
            return Err(NavigationError::InvalidUrl(format!(
                "URL must start with http://, https://, or file://: {}",
                url
            ))
            .into());
        }

        info!("Navigating to: {}", url);

        let mut last_error = None;
        for attempt in 0..=opts.retries {
            if attempt > 0 {
                warn!("Navigation retry attempt {} of {}", attempt, opts.retries);
                tokio::time::sleep(Duration::from_millis(opts.retry_delay_ms)).await;
            }

            match Self::navigate_once(&page.page, url, &opts).await {
                Ok(result) => {
                    // Update page URL
                    page.set_url(result.final_url.clone()).await;

                    // Apply human-like behavior if enabled
                    if opts.human_like {
                        Self::simulate_human_behavior(&page.page).await?;
                    }

                    let duration_ms = start.elapsed().as_millis() as u64;
                    return Ok(NavigationResult {
                        final_url: result.final_url,
                        status: result.status,
                        title: result.title,
                        duration_ms,
                    });
                }
                Err(e) => {
                    warn!("Navigation attempt {} failed: {}", attempt + 1, e);
                    last_error = Some(e);
                }
            }
        }

        Err(last_error.unwrap_or_else(|| {
            NavigationError::LoadFailed("Navigation failed after all retries".to_string()).into()
        }))
    }

    /// Perform a single navigation attempt
    async fn navigate_once(
        page: &chromiumoxide::Page,
        url: &str,
        opts: &NavigationOptions,
    ) -> Result<NavigationResult> {
        // Navigate with timeout
        let timeout = Duration::from_millis(opts.timeout_ms);

        let nav_future = page.goto(url);
        let _response = tokio::time::timeout(timeout, nav_future)
            .await
            .map_err(|_| NavigationError::Timeout(opts.timeout_ms))?
            .map_err(|e| NavigationError::LoadFailed(e.to_string()))?;

        // Wait for page to be ready based on wait_until option
        Self::wait_for_ready(page, opts).await?;

        // Get final URL and title
        let final_url = page
            .url()
            .await
            .map_err(|e| Error::cdp(e.to_string()))?
            .unwrap_or_else(|| url.to_string());

        let title = page
            .evaluate("document.title")
            .await
            .ok()
            .and_then(|v| v.into_value::<String>().ok());

        // Navigation doesn't return status directly in chromiumoxide
        let status: Option<u16> = None;

        debug!("Navigation complete: {} -> {}", url, final_url);

        Ok(NavigationResult {
            final_url,
            status,
            title,
            duration_ms: 0, // Will be set by caller
        })
    }

    /// Wait for page to be ready based on wait_until condition
    async fn wait_for_ready(page: &chromiumoxide::Page, opts: &NavigationOptions) -> Result<()> {
        let script = match opts.wait_until {
            WaitUntil::Load => {
                r#"
                    new Promise(resolve => {
                        if (document.readyState === 'complete') {
                            resolve(true);
                        } else {
                            window.addEventListener('load', () => resolve(true));
                        }
                    })
                "#
            }
            WaitUntil::DomContentLoaded => {
                r#"
                    new Promise(resolve => {
                        if (document.readyState !== 'loading') {
                            resolve(true);
                        } else {
                            document.addEventListener('DOMContentLoaded', () => resolve(true));
                        }
                    })
                "#
            }
            WaitUntil::NetworkIdle0 | WaitUntil::NetworkIdle2 => {
                // For network idle, we'll just wait a short time after load
                // A more sophisticated approach would monitor actual network activity
                r#"
                    new Promise(resolve => {
                        if (document.readyState === 'complete') {
                            setTimeout(() => resolve(true), 500);
                        } else {
                            window.addEventListener('load', () => {
                                setTimeout(() => resolve(true), 500);
                            });
                        }
                    })
                "#
            }
        };

        let timeout = Duration::from_millis(opts.timeout_ms);
        tokio::time::timeout(timeout, page.evaluate(script))
            .await
            .map_err(|_| NavigationError::Timeout(opts.timeout_ms))?
            .map_err(|e| Error::cdp(e.to_string()))?;

        Ok(())
    }

    /// Simulate human-like behavior after navigation
    async fn simulate_human_behavior(page: &chromiumoxide::Page) -> Result<()> {
        // Random small delay
        let delay = rand::random::<u64>() % 500 + 200;
        tokio::time::sleep(Duration::from_millis(delay)).await;

        // Gentle scroll
        let scroll_script = r#"
            window.scrollTo({
                top: Math.random() * 100 + 50,
                behavior: 'smooth'
            });
        "#;

        let _ = page.evaluate(scroll_script).await;

        // Small delay after scroll
        tokio::time::sleep(Duration::from_millis(200)).await;

        Ok(())
    }

    /// Go back in browser history
    #[instrument(skip(page))]
    pub async fn back(page: &PageHandle) -> Result<()> {
        page.page
            .evaluate("window.history.back()")
            .await
            .map_err(|e| Error::cdp(e.to_string()))?;

        tokio::time::sleep(Duration::from_millis(500)).await;
        Ok(())
    }

    /// Go forward in browser history
    #[instrument(skip(page))]
    pub async fn forward(page: &PageHandle) -> Result<()> {
        page.page
            .evaluate("window.history.forward()")
            .await
            .map_err(|e| Error::cdp(e.to_string()))?;

        tokio::time::sleep(Duration::from_millis(500)).await;
        Ok(())
    }

    /// Reload the current page
    #[instrument(skip(page))]
    pub async fn reload(page: &PageHandle) -> Result<()> {
        page.page
            .reload()
            .await
            .map_err(|e| Error::cdp(e.to_string()))?;

        Ok(())
    }

    /// Wait for a specific element to appear
    #[instrument(skip(page))]
    pub async fn wait_for_selector(
        page: &PageHandle,
        selector: &str,
        timeout_ms: u64,
    ) -> Result<()> {
        let script = format!(
            r#"
                new Promise((resolve, reject) => {{
                    const timeout = {};
                    const start = Date.now();
                    
                    function check() {{
                        const el = document.querySelector('{}');
                        if (el) {{
                            resolve(true);
                        }} else if (Date.now() - start > timeout) {{
                            reject(new Error('Timeout waiting for selector'));
                        }} else {{
                            requestAnimationFrame(check);
                        }}
                    }}
                    check();
                }})
            "#,
            timeout_ms,
            selector.replace('\'', "\\'")
        );

        let timeout = Duration::from_millis(timeout_ms + 1000);
        tokio::time::timeout(timeout, page.page.evaluate(script.as_str()))
            .await
            .map_err(|_| NavigationError::Timeout(timeout_ms))?
            .map_err(|e| Error::cdp(e.to_string()))?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_navigation_options_default() {
        let opts = NavigationOptions::default();
        assert_eq!(opts.timeout_ms, 30000);
        assert_eq!(opts.retries, 3);
        assert!(opts.human_like);
    }

    #[test]
    fn test_wait_until_variants() {
        assert_ne!(WaitUntil::Load, WaitUntil::DomContentLoaded);
        assert_eq!(WaitUntil::NetworkIdle0, WaitUntil::NetworkIdle0);
    }
}
