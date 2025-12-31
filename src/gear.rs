use anyhow::{Context, Result};
use chromiumoxide::cdp::browser_protocol::page::{
    AddScriptToEvaluateOnNewDocumentParams, CaptureSnapshotFormat, CaptureSnapshotParams,
};
use chromiumoxide::Page;
use std::time::Duration;
use tracing::{info, instrument};

/// The "VisualFreezer" - Handles MHTML snapshots and screenshots
pub struct VisualFreezer;

impl VisualFreezer {
    /// Captures a full-page MHTML snapshot using CDP.
    #[instrument(skip(page))]
    pub async fn capture_mhtml(page: &Page) -> Result<Vec<u8>> {
        info!("Capturing MHTML snapshot");

        // Use the raw CDP command for Page.captureSnapshot
        let params = CaptureSnapshotParams::builder()
            .format(CaptureSnapshotFormat::Mhtml)
            .build();

        let result = page
            .execute(params)
            .await
            .context("Failed to execute Page.captureSnapshot")?;

        // MHTML data is returned as a string - clone to get ownership
        Ok(result.data.clone().into_bytes())
    }

    /// Captures a visual screenshot (JPEG).
    #[instrument(skip(page))]
    pub async fn capture_screenshot(page: &Page) -> Result<Vec<u8>> {
        info!("Capturing JPEG screenshot");

        // chromiumoxide handles screenshotting with a nicer API
        let screenshot_params = chromiumoxide::page::ScreenshotParams::builder()
            .format(chromiumoxide::cdp::browser_protocol::page::CaptureScreenshotFormat::Jpeg)
            .quality(80)
            .from_surface(true)
            .build();

        let data = page
            .screenshot(screenshot_params)
            .await
            .context("Failed to capture screenshot")?;

        Ok(data)
    }
}

/// The "StealthNavigator" - Handles evasion and anti-fingerprinting
pub struct StealthNavigator;

impl StealthNavigator {
    /// Injects stealth scripts into the page to mask automation signals.
    #[instrument(skip(page))]
    pub async fn cloak(page: &Page) -> Result<()> {
        info!("Applying stealth cloak");

        // 1. WebGL Override
        let webgl_script = r#"
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter(parameter);
            };
        "#;
        Self::inject_script(page, webgl_script, "WebGL").await?;

        // 2. WebDriver Removal
        let webdriver_script = r#"
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        "#;
        Self::inject_script(page, webdriver_script, "WebDriver").await?;

        // 3. Chrome Runtime Mock
        let chrome_script = r#"
            window.chrome = {
                runtime: {}
            };
        "#;
        Self::inject_script(page, chrome_script, "Chrome runtime").await?;

        // 4. Plugins/Languages Mock
        let plugins_script = r#"
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        "#;
        Self::inject_script(page, plugins_script, "Plugins").await?;

        Ok(())
    }

    /// Helper to inject a script with proper error handling
    async fn inject_script(page: &Page, script: &str, name: &str) -> Result<()> {
        let params = AddScriptToEvaluateOnNewDocumentParams::builder()
            .source(script)
            .build()
            .map_err(|e| anyhow::anyhow!("Failed to build {} script params: {}", name, e))?;

        page.execute(params)
            .await
            .context(format!("Failed to inject {} stealth script", name))?;

        Ok(())
    }

    /// Navigates to a URL with resilience
    #[instrument(skip(page))]
    pub async fn goto_resilient(page: &Page, url: &str) -> Result<()> {
        info!("Navigating to {}", url);

        page.goto(url).await.context("Failed to navigate to URL")?;

        // Human-like behavior: slight scroll
        let scroll_script = r#"
            window.scrollTo({
                top: 100,
                behavior: 'smooth'
            });
        "#;

        // Give it a moment to load execution context
        tokio::time::sleep(Duration::from_millis(1000)).await;

        // Use string directly for evaluate - chromiumoxide accepts &str
        page.evaluate(scroll_script)
            .await
            .context("Failed to perform human-like scroll")?;

        Ok(())
    }
}

/// The "InteractionGear" - Handles active page interaction
pub struct InteractionGear;

impl InteractionGear {
    /// Clicks an element matching the selector
    #[instrument(skip(page))]
    pub async fn click(page: &Page, selector: &str) -> Result<()> {
        info!("Clicking element: {}", selector);

        let element = page
            .find_element(selector)
            .await
            .context(format!("Failed to find element: {}", selector))?;

        element
            .click()
            .await
            .context(format!("Failed to click element: {}", selector))?;

        Ok(())
    }

    /// Types text into an element matching the selector
    #[instrument(skip(page))]
    pub async fn type_text(page: &Page, selector: &str, text: &str) -> Result<()> {
        info!("Typing into element: {}", selector);

        let element = page
            .find_element(selector)
            .await
            .context(format!("Failed to find element: {}", selector))?;

        element
            .click()
            .await
            .context("Failed to focus element before typing")?;

        element
            .type_str(text)
            .await
            .context(format!("Failed to type text into: {}", selector))?;

        Ok(())
    }

    /// Scrolls the page to specific coordinates
    #[instrument(skip(page))]
    pub async fn scroll(page: &Page, x: i32, y: i32) -> Result<()> {
        info!("Scrolling to {}, {}", x, y);

        let script = format!(
            "window.scrollTo({{ left: {}, top: {}, behavior: 'smooth' }});",
            x, y
        );

        page.evaluate(script)
            .await
            .context("Failed to execute scroll script")?;

        Ok(())
    }
}

/// The "ExtractionGear" - Handles data extraction
pub struct ExtractionGear;

impl ExtractionGear {
    /// Extracts inner text from an element
    #[instrument(skip(page))]
    pub async fn extract_text(page: &Page, selector: &str) -> Result<String> {
        info!("Extracting text from: {}", selector);

        let element = page
            .find_element(selector)
            .await
            .context(format!("Failed to find element: {}", selector))?;

        let text = element
            .inner_text()
            .await
            .context(format!("Failed to get inner text from: {}", selector))?;

        Ok(text.unwrap_or_default())
    }

    /// Extracts outer HTML from an element
    #[instrument(skip(page))]
    pub async fn extract_html(page: &Page, selector: &str) -> Result<String> {
        info!("Extracting HTML from: {}", selector);

        // chromiumoxide doesn't have a direct outer_html method on Element in all versions,
        // so we use JS evaluation on the element handle if needed, or check if the crate supports it.
        // Checking crate docs (mental model): Element usually has inner_html or we use evaluate.
        // Let's use a safe JS evaluation approach for robustness.

        let script = format!(
            "document.querySelector('{}').outerHTML",
            selector.replace("'", "\\'") // Basic escaping
        );

        let result = page
            .evaluate(script)
            .await
            .context(format!("Failed to extract HTML from: {}", selector))?;

        Ok(result.into_value::<String>()?)
    }
}
