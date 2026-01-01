//! Browser automation module
//!
//! This module provides high-level browser control through ChromiumOxide,
//! including lifecycle management, navigation, and capture functionality.

mod capture;
mod controller;
mod navigation;
mod stealth;

pub use capture::{CaptureFormat, CaptureOptions, CaptureResult, PageCapture};
pub use controller::{BrowserConfig, BrowserController, PageHandle};
pub use navigation::{NavigationOptions, NavigationResult, PageNavigator, WaitUntil};
pub use stealth::StealthMode;
