//! Main content extraction
//!
//! This module extracts the main content from web pages, converting it
//! to clean text or markdown format.

use crate::browser::PageHandle;
use crate::error::{ExtractionError, Result};
use serde::{Deserialize, Serialize};
use tracing::{debug, info, instrument};

/// Extracted content from a page
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExtractedContent {
    /// Plain text content
    pub text: String,
    /// Content as markdown (if converted)
    pub markdown: Option<String>,
    /// HTML of the main content
    pub html: String,
    /// Word count
    pub word_count: usize,
    /// Character count
    pub char_count: usize,
    /// Whether content was extracted from article/main element
    pub from_main: bool,
}

/// Content extraction functionality
pub struct ContentExtractor;

impl ContentExtractor {
    /// Extract main content from the page
    #[instrument(skip(page))]
    pub async fn extract_main_content(page: &PageHandle) -> Result<ExtractedContent> {
        info!("Extracting main content");

        // Try to find the main content using various strategies
        let (html, from_main) = Self::find_main_content(&page.page).await?;
        let text = Self::html_to_text(&html);
        let markdown = Self::html_to_markdown(&html);

        let word_count = text.split_whitespace().count();
        let char_count = text.chars().count();

        debug!(
            "Extracted {} words, {} chars, from_main={}",
            word_count, char_count, from_main
        );

        Ok(ExtractedContent {
            text,
            markdown: Some(markdown),
            html,
            word_count,
            char_count,
            from_main,
        })
    }

    /// Extract content from a specific selector
    #[instrument(skip(page))]
    pub async fn extract_from_selector(
        page: &PageHandle,
        selector: &str,
    ) -> Result<ExtractedContent> {
        info!("Extracting from selector: {}", selector);

        let script = format!(
            r#"
            (() => {{
                const el = document.querySelector('{}');
                if (!el) return null;
                return {{
                    html: el.innerHTML,
                    text: el.innerText
                }};
            }})()
            "#,
            selector.replace('\'', "\\'")
        );

        let result: Option<serde_json::Value> = page
            .page
            .evaluate(script.as_str())
            .await
            .map_err(|e| ExtractionError::ExtractionFailed(e.to_string()))?
            .into_value()
            .map_err(|e| ExtractionError::ExtractionFailed(e.to_string()))?;

        let result =
            result.ok_or_else(|| ExtractionError::ElementNotFound(selector.to_string()))?;

        let html = result["html"].as_str().unwrap_or("").to_string();
        let text = result["text"].as_str().unwrap_or("").to_string();

        let markdown = Self::html_to_markdown(&html);
        let word_count = text.split_whitespace().count();
        let char_count = text.chars().count();

        Ok(ExtractedContent {
            text,
            markdown: Some(markdown),
            html,
            word_count,
            char_count,
            from_main: false,
        })
    }

    /// Extract all text from the page body
    #[instrument(skip(page))]
    pub async fn extract_all_text(page: &PageHandle) -> Result<String> {
        let script = r#"
            document.body.innerText
        "#;

        let text: String = page
            .page
            .evaluate(script)
            .await
            .map_err(|e| ExtractionError::ExtractionFailed(e.to_string()))?
            .into_value()
            .map_err(|e| ExtractionError::ExtractionFailed(e.to_string()))?;

        Ok(text)
    }

    /// Find the main content element using various strategies
    async fn find_main_content(page: &chromiumoxide::Page) -> Result<(String, bool)> {
        let script = r#"
            (() => {
                // Strategy 1: Look for article or main elements
                const mainSelectors = [
                    'article',
                    'main',
                    '[role="main"]',
                    '[role="article"]',
                    '.article',
                    '.post',
                    '.content',
                    '.entry-content',
                    '.post-content',
                    '#content',
                    '#main-content',
                    '.main-content'
                ];
                
                for (const selector of mainSelectors) {
                    const el = document.querySelector(selector);
                    if (el && el.innerText.length > 200) {
                        return { html: el.innerHTML, fromMain: true };
                    }
                }
                
                // Strategy 2: Find the largest text block
                const textBlocks = [];
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_ELEMENT,
                    {
                        acceptNode: (node) => {
                            const tag = node.tagName.toLowerCase();
                            if (['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript'].includes(tag)) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            return NodeFilter.FILTER_ACCEPT;
                        }
                    }
                );
                
                let node;
                while (node = walker.nextNode()) {
                    const text = node.innerText || '';
                    if (text.length > 200) {
                        textBlocks.push({
                            el: node,
                            length: text.length
                        });
                    }
                }
                
                if (textBlocks.length > 0) {
                    // Sort by length and get the longest
                    textBlocks.sort((a, b) => b.length - a.length);
                    return { html: textBlocks[0].el.innerHTML, fromMain: false };
                }
                
                // Fallback: return body
                return { html: document.body.innerHTML, fromMain: false };
            })()
        "#;

        let result: serde_json::Value = page
            .evaluate(script)
            .await
            .map_err(|e| ExtractionError::ExtractionFailed(e.to_string()))?
            .into_value()
            .map_err(|e| ExtractionError::ExtractionFailed(e.to_string()))?;

        let html = result["html"].as_str().unwrap_or("").to_string();
        let from_main = result["fromMain"].as_bool().unwrap_or(false);

        Ok((html, from_main))
    }

    /// Convert HTML to plain text
    fn html_to_text(html: &str) -> String {
        // Remove script and style tags
        let mut text = html.to_string();

        // Remove script tags and content
        let script_re = regex::Regex::new(r"<script[^>]*>[\s\S]*?</script>").unwrap();
        text = script_re.replace_all(&text, "").to_string();

        // Remove style tags and content
        let style_re = regex::Regex::new(r"<style[^>]*>[\s\S]*?</style>").unwrap();
        text = style_re.replace_all(&text, "").to_string();

        // Replace block elements with newlines
        let block_re = regex::Regex::new(r"</(p|div|br|li|h[1-6])>").unwrap();
        text = block_re.replace_all(&text, "\n").to_string();

        // Remove all remaining HTML tags
        let tag_re = regex::Regex::new(r"<[^>]+>").unwrap();
        text = tag_re.replace_all(&text, "").to_string();

        // Decode common HTML entities
        text = text
            .replace("&nbsp;", " ")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
            .replace("&quot;", "\"")
            .replace("&#39;", "'")
            .replace("&apos;", "'");

        // Normalize whitespace
        let ws_re = regex::Regex::new(r"\s+").unwrap();
        text = ws_re.replace_all(&text, " ").to_string();

        // Normalize newlines
        let nl_re = regex::Regex::new(r"\n\s*\n+").unwrap();
        text = nl_re.replace_all(&text, "\n\n").to_string();

        text.trim().to_string()
    }

    /// Convert HTML to markdown
    fn html_to_markdown(html: &str) -> String {
        let mut md = html.to_string();

        // Remove script and style
        let script_re = regex::Regex::new(r"<script[^>]*>[\s\S]*?</script>").unwrap();
        md = script_re.replace_all(&md, "").to_string();
        let style_re = regex::Regex::new(r"<style[^>]*>[\s\S]*?</style>").unwrap();
        md = style_re.replace_all(&md, "").to_string();

        // Convert headers
        for i in (1..=6).rev() {
            let h_re = regex::Regex::new(&format!(r"<h{}[^>]*>(.*?)</h{}>", i, i)).unwrap();
            let prefix = "#".repeat(i);
            md = h_re
                .replace_all(&md, format!("{} $1\n\n", prefix))
                .to_string();
        }

        // Convert paragraphs
        let p_re = regex::Regex::new(r"<p[^>]*>(.*?)</p>").unwrap();
        md = p_re.replace_all(&md, "$1\n\n").to_string();

        // Convert line breaks
        let br_re = regex::Regex::new(r"<br\s*/?>").unwrap();
        md = br_re.replace_all(&md, "\n").to_string();

        // Convert bold
        let b_re = regex::Regex::new(r"<(b|strong)[^>]*>(.*?)</(b|strong)>").unwrap();
        md = b_re.replace_all(&md, "**$2**").to_string();

        // Convert italic
        let i_re = regex::Regex::new(r"<(i|em)[^>]*>(.*?)</(i|em)>").unwrap();
        md = i_re.replace_all(&md, "*$2*").to_string();

        // Convert links
        let a_re = regex::Regex::new(r#"<a[^>]*href=["']([^"']+)["'][^>]*>(.*?)</a>"#).unwrap();
        md = a_re.replace_all(&md, "[$2]($1)").to_string();

        // Convert code
        let code_re = regex::Regex::new(r"<code[^>]*>(.*?)</code>").unwrap();
        md = code_re.replace_all(&md, "`$1`").to_string();

        // Convert pre blocks
        let pre_re = regex::Regex::new(r"<pre[^>]*>(.*?)</pre>").unwrap();
        md = pre_re.replace_all(&md, "```\n$1\n```").to_string();

        // Convert lists
        let li_re = regex::Regex::new(r"<li[^>]*>(.*?)</li>").unwrap();
        md = li_re.replace_all(&md, "- $1\n").to_string();

        // Remove remaining tags
        let tag_re = regex::Regex::new(r"<[^>]+>").unwrap();
        md = tag_re.replace_all(&md, "").to_string();

        // Decode HTML entities
        md = md
            .replace("&nbsp;", " ")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
            .replace("&quot;", "\"")
            .replace("&#39;", "'");

        // Clean up whitespace
        let ws_re = regex::Regex::new(r"\n{3,}").unwrap();
        md = ws_re.replace_all(&md, "\n\n").to_string();

        md.trim().to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_html_to_text() {
        let html = "<p>Hello <b>world</b>!</p><p>Second paragraph.</p>";
        let text = ContentExtractor::html_to_text(html);
        assert!(text.contains("Hello"));
        assert!(text.contains("world"));
        assert!(!text.contains("<"));
    }

    #[test]
    fn test_html_to_text_removes_scripts() {
        let html = "<p>Content</p><script>evil();</script><p>More</p>";
        let text = ContentExtractor::html_to_text(html);
        assert!(!text.contains("evil"));
        assert!(text.contains("Content"));
        assert!(text.contains("More"));
    }

    #[test]
    fn test_html_to_markdown() {
        let html = "<h1>Title</h1><p>Para with <b>bold</b> and <a href=\"http://example.com\">link</a>.</p>";
        let md = ContentExtractor::html_to_markdown(html);
        assert!(md.contains("# Title"));
        assert!(md.contains("**bold**"));
        assert!(md.contains("[link](http://example.com)"));
    }

    #[test]
    fn test_extracted_content_structure() {
        let content = ExtractedContent {
            text: "Hello world".to_string(),
            markdown: Some("Hello world".to_string()),
            html: "<p>Hello world</p>".to_string(),
            word_count: 2,
            char_count: 11,
            from_main: true,
        };
        assert_eq!(content.word_count, 2);
        assert!(content.from_main);
    }
}
