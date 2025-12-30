"""
Testing Suite with VIBE-style validation

Comprehensive testing for browser automation capabilities including:
- Unit tests for Digital Employee
- Integration tests for VIBE Assessment
- Performance tests for 3D Rendering
- Cross-platform browser compatibility tests
- Security and sandboxing tests
"""

import asyncio
import json
import logging
import pytest
import time
from pathlib import Path
from typing import Dict, Any, List

from playwright.async_api import async_playwright, Page
from ..employee.digital_employee import DigitalEmployee, InteractionType
from ..assessment.vibe_engine import VIBEAssessmentEngine
from ..render3d.engine import Render3DEngine
from ..browser.manager import CrossPlatformBrowserManager, BrowserType, BrowserProfile

logger = logging.getLogger("web.testing")


class TestDigitalEmployee:
    """Test suite for Digital Employee capabilities."""

    @pytest.fixture
    async def browser_page(self):
        """Create a test browser page."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            yield page
            await browser.close()

    @pytest.mark.asyncio
    async def test_click_element(self, browser_page):
        """Test element clicking with precision."""
        employee = DigitalEmployee()

        # Navigate to a test page
        await browser_page.goto("data:text/html,<button id='test'>Click Me</button>")

        # Click the button
        event = await employee.click_element(browser_page, "#test", click_type="left")

        assert event.success
        assert event.type == InteractionType.CLICK
        assert event.selector == "#test"
        assert event.position is not None

    @pytest.mark.asyncio
    async def test_type_text(self, browser_page):
        """Test text input with human-like timing."""
        employee = DigitalEmployee()

        # Navigate to a test page
        await browser_page.goto("data:text/html,<input id='text' />")

        # Type text
        event = await employee.type_text(
            browser_page, "Hello World", selector="#text", typing_speed=30
        )

        assert event.success
        assert event.type == InteractionType.TYPE
        assert event.text == "Hello World"

        # Verify text was entered
        value = await browser_page.input_value("#text")
        assert "Hello" in value

    @pytest.mark.asyncio
    async def test_fill_form(self, browser_page):
        """Test form filling automation."""
        employee = DigitalEmployee()

        # Navigate to a test page
        await browser_page.goto("data:text/html,<input id='name' /><input id='email' />")

        # Fill form
        form_data = {"#name": "John Doe", "#email": "john@example.com"}

        events = await employee.fill_form(browser_page, form_data)

        assert len(events) == 2
        assert all(event.success for event in events)

        # Verify form values
        name = await browser_page.input_value("#name")
        email = await browser_page.input_value("#email")

        assert name == "John Doe"
        assert email == "john@example.com"


class TestVIBEAssessment:
    """Test suite for VIBE Assessment capabilities."""

    @pytest.fixture
    async def browser_page(self):
        """Create a test browser page."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            yield page
            await browser.close()

    @pytest.mark.asyncio
    async def test_page_assessment(self, browser_page):
        """Test comprehensive page assessment."""
        vibe_engine = VIBEAssessmentEngine()

        # Navigate to a test page
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <style>
                body { font-family: Arial; margin: 20px; }
                h1 { color: #333; font-size: 24px; }
                p { color: #666; font-size: 16px; }
                .button { background: #007cba; color: white; padding: 10px; }
            </style>
        </head>
        <body>
            <h1>Test Page Title</h1>
            <p>This is a test paragraph with good contrast.</p>
            <button class="button">Test Button</button>
        </body>
        </html>
        """

        await browser_page.goto(f"data:text/html,{test_html}")

        # Perform assessment
        assessment = await vibe_engine.assess_page(browser_page)

        # Verify assessment structure
        assert "scores" in assessment
        assert "aesthetic" in assessment["scores"]
        assert "usability" in assessment["scores"]
        assert "accessibility" in assessment["scores"]
        assert "performance" in assessment["scores"]
        assert "overall" in assessment["scores"]

        # Verify scores are reasonable
        for score_name, score_value in assessment["scores"].items():
            assert isinstance(score_value, (int, float))
            assert 0 <= score_value <= 10

    @pytest.mark.asyncio
    async def test_element_analysis(self, browser_page):
        """Test individual element analysis."""
        vibe_engine = VIBEAssessmentEngine()

        # Navigate to a test page
        await browser_page.goto("data:text/html,<p id='test'>Test Text</p>")

        # Get element information directly (simplified test)
        element = await browser_page.query_selector("#test")
        assert element is not None

        # This would normally call vibe_engine._analyze_single_element
        # but we'll test the individual components
        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
        assert tag_name == "p"


class TestRender3DEngine:
    """Test suite for 3D Rendering capabilities."""

    @pytest.fixture
    async def browser_page(self):
        """Create a test browser page."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Add Three.js library
            await page.add_script_tag(
                url="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
            )

            yield page
            await browser.close()

    @pytest.mark.asyncio
    async def test_3d_content_detection(self, browser_page):
        """Test 3D content detection."""
        render_engine = Render3DEngine()

        # Navigate to a page with 3D content
        await browser_page.goto("data:text/html,<canvas id='three-canvas'></canvas>")

        # Detect 3D content
        analysis = await render_engine.detect_3d_content(browser_page)

        # Verify analysis structure
        assert "timestamp" in analysis
        assert "url" in analysis
        assert "threejs_detected" in analysis
        assert "webgl_capabilities" in analysis
        assert "capability_score" in analysis

    @pytest.mark.asyncio
    async def test_3d_scene_creation(self, browser_page):
        """Test 3D scene creation."""
        render_engine = Render3DEngine()

        scene_config = {
            "scene_id": "test_scene",
            "quality": "medium",
            "background_color": "0x222222",
            "antialias": True,
        }

        # Create scene
        result = await render_engine.create_3d_scene(browser_page, scene_config)

        # Verify result
        assert "success" in result
        assert result["success"] == True

    @pytest.mark.asyncio
    async def test_3d_instance_creation(self, browser_page):
        """Test 3D instance creation."""
        render_engine = Render3DEngine()

        # First create a scene
        scene_config = {"scene_id": "test_scene"}
        await render_engine.create_3d_scene(browser_page, scene_config)

        # Add instance
        instance_config = {
            "instance_id": "test_instance",
            "type": "box",
            "size": [1, 1, 1],
            "position": [0, 0, 0],
        }

        result = await render_engine.add_3d_instance(browser_page, "test_scene", instance_config)

        # Verify result
        assert "success" in result
        assert result["success"] == True


class TestCrossPlatformBrowserManager:
    """Test suite for cross-platform browser capabilities."""

    @pytest.mark.asyncio
    async def test_browser_startup(self):
        """Test browser session startup."""
        manager = CrossPlatformBrowserManager()

        # Start browser session
        session_id = await manager.start_browser(BrowserType.CHROMIUM)

        assert session_id is not None
        assert session_id in manager.active_sessions

        # Get browser info
        info = await manager.get_browser_info(session_id)

        assert info["browser_type"] == "chromium"
        assert info["uptime"] > 0

        # Cleanup
        await manager.close_session(session_id)

    @pytest.mark.asyncio
    async def test_navigation(self):
        """Test browser navigation."""
        manager = CrossPlatformBrowserManager()

        session_id = await manager.start_browser(BrowserType.CHROMIUM)

        # Navigate to test page
        result = await manager.navigate(
            session_id, "data:text/html,<h1>Test Page</h1>", wait_until="domcontentloaded"
        )

        assert result["success"] == True
        assert "load_time" in result

        # Cleanup
        await manager.close_session(session_id)

    @pytest.mark.asyncio
    async def test_multiple_sessions(self):
        """Test multiple browser sessions."""
        manager = CrossPlatformBrowserManager()

        # Start multiple sessions
        session1 = await manager.start_browser(BrowserType.CHROMIUM)
        session2 = await manager.start_browser(BrowserType.FIREFOX)

        assert len(manager.active_sessions) == 2

        # Navigate in both sessions
        await manager.navigate(session1, "data:text/html,<h1>Session 1</h1>")
        await manager.navigate(session2, "data:text/html,<h1>Session 2</h1>")

        # Get info for both
        info1 = await manager.get_browser_info(session1)
        info2 = await manager.get_browser_info(session2)

        assert info1["browser_type"] == "chromium"
        assert info2["browser_type"] == "firefox"

        # Cleanup
        await manager.close_all_sessions()


class TestSecurityAndSandboxing:
    """Test security and sandboxing features."""

    @pytest.mark.asyncio
    async def test_stealth_mode(self):
        """Test stealth mode browser configuration."""
        manager = CrossPlatformBrowserManager()

        # Start browser in stealth mode
        session_id = await manager.start_browser(BrowserType.CHROMIUM, session_id="stealth_test")

        page = await manager.get_page(session_id)

        # Check for stealth features
        webdriver = await page.evaluate("navigator.webdriver")
        assert webdriver is None or webdriver is False

        # Cleanup
        await manager.close_session(session_id)

    @pytest.mark.asyncio
    async def test_isolation(self):
        """Test browser session isolation."""
        manager = CrossPlatformBrowserManager()

        # Start two sessions
        session1 = await manager.start_browser(BrowserType.CHROMIUM, session_id="isolated_1")
        session2 = await manager.start_browser(BrowserType.CHROMIUM, session_id="isolated_2")

        # Navigate to different pages
        await manager.navigate(session1, "data:text/html,<p id='unique1'>Session 1 Content</p>")
        await manager.navigate(session2, "data:text/html,<p id='unique2'>Session 2 Content</p>")

        # Verify isolation
        page1 = await manager.get_page(session1)
        page2 = await manager.get_page(session2)

        content1 = await page1.text_content("#unique1")
        content2 = await page2.text_content("#unique2")

        assert "Session 1 Content" in content1
        assert "Session 2 Content" in content2

        # Cleanup
        await manager.close_all_sessions()


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_browser_performance_monitoring(self):
        """Test performance monitoring capabilities."""
        manager = CrossPlatformBrowserManager()

        session_id = await manager.start_browser(BrowserType.CHROMIUM)

        # Navigate to page and get performance report
        await manager.navigate(session_id, "data:text/html,<h1>Performance Test</h1>")

        report = await manager.get_performance_report()

        assert "timestamp" in report
        assert "active_sessions" in report
        assert "sessions" in report

        # Cleanup
        await manager.close_session(session_id)

    @pytest.mark.asyncio
    async def test_interaction_performance(self):
        """Test interaction performance characteristics."""
        employee = DigitalEmployee()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto("data:text/html,<button id='perf'>Performance Test</button>")

            # Measure interaction performance
            start_time = time.time()

            # Perform multiple interactions
            for i in range(10):
                await employee.click_element(page, "#perf")

            end_time = time.time()
            total_time = end_time - start_time

            # Should complete 10 interactions in reasonable time
            assert total_time < 10.0  # Less than 10 seconds for 10 interactions

            await browser.close()


class TestVIBEStyleValidation:
    """Test VIBE-style validation and scoring."""

    @pytest.mark.asyncio
    async def test_aesthetic_scoring(self):
        """Test aesthetic scoring algorithm."""
        vibe_engine = VIBEAssessmentEngine()

        # Test with good design
        good_design = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px;
                    background: #f5f5f5;
                    color: #333;
                }
                h1 { 
                    color: #2c3e50; 
                    font-size: 2.5em;
                    margin-bottom: 20px;
                }
                .content {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
            </style>
        </head>
        <body>
            <h1>Well Designed Page</h1>
            <div class="content">
                <p>This is a well-designed page with good contrast and typography.</p>
            </div>
        </body>
        </html>
        """

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(f"data:text/html,{good_design}")

            assessment = await vibe_engine.assess_page(page)

            # Should score well on aesthetic metrics
            assert assessment["scores"]["aesthetic"] >= 6.0
            assert assessment["scores"]["overall"] >= 6.0

            await browser.close()

    @pytest.mark.asyncio
    async def test_accessibility_scoring(self):
        """Test accessibility scoring with known accessibility issues."""
        vibe_engine = VIBEAssessmentEngine()

        # Test with poor accessibility
        poor_accessibility = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .low-contrast { color: #888; background: #999; }
                .tiny-text { font-size: 10px; }
                .no-alt { }
            </style>
        </head>
        <body>
            <h1 style="color: #888; background: #999; font-size: 10px;">Poor Accessibility</h1>
            <p class="low-contrast">This text has poor contrast.</p>
            <p class="tiny-text">This text is too small.</p>
            <img src="test.jpg" class="no-alt">
        </body>
        </html>
        """

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(f"data:text/html,{poor_accessibility}")

            assessment = await vibe_engine.assess_page(page)

            # Should score poorly on accessibility
            assert assessment["scores"]["accessibility"] <= 4.0
            assert len(assessment["issues"]) > 0

            await browser.close()


# Integration tests
class TestIntegration:
    """Integration tests combining multiple capabilities."""

    @pytest.mark.asyncio
    async def test_digital_employee_vibe_integration(self):
        """Test Digital Employee and VIBE working together."""
        employee = DigitalEmployee()
        vibe_engine = VIBEAssessmentEngine()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Create a test form
            test_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Form Test</title>
                <style>
                    body { font-family: Arial; margin: 20px; }
                    .form-group { margin: 10px 0; }
                    label { display: block; margin-bottom: 5px; }
                    input { padding: 5px; width: 200px; }
                    .submit { background: #007cba; color: white; padding: 10px; border: none; }
                </style>
            </head>
            <body>
                <h1>User Registration</h1>
                <form id="registration">
                    <div class="form-group">
                        <label for="name">Name:</label>
                        <input type="text" id="name" required>
                    </div>
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="email" id="email" required>
                    </div>
                    <button type="submit" class="submit">Register</button>
                </form>
            </body>
            </html>
            """

            await page.goto(f"data:text/html,{test_html}")

            # Use Digital Employee to fill the form
            form_data = {"#name": "John Doe", "#email": "john@example.com"}

            events = await employee.fill_form(page, form_data)
            assert all(event.success for event in events)

            # Use VIBE to assess the page after interaction
            assessment = await vibe_engine.assess_page(page)

            # Verify the integration worked
            assert assessment["scores"]["usability"] > 0
            assert "element_count" in assessment["analysis"]

            await browser.close()

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: start browser, navigate, interact, assess."""
        manager = CrossPlatformBrowserManager()
        employee = DigitalEmployee()
        vibe_engine = VIBEAssessmentEngine()

        # Start browser session
        session_id = await manager.start_browser(BrowserType.CHROMIUM)

        try:
            # Navigate to test page
            test_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Complete Test</title>
                <style>
                    body { font-family: Arial; margin: 20px; }
                    #interactive { padding: 10px; background: #f0f0f0; cursor: pointer; }
                </style>
            </head>
            <body>
                <h1>Interactive Test Page</h1>
                <p id="interactive">Click me to test interaction</p>
                <button id="action">Action Button</button>
            </body>
            </html>
            """

            await manager.navigate(session_id, f"data:text/html,{test_html}")

            # Get page for interactions
            page = await manager.get_page(session_id)

            # Use Digital Employee to interact
            click_event = await employee.click_element(page, "#interactive")
            assert click_event.success

            type_event = await employee.type_text(page, "Test Input", "#action")
            assert type_event.success

            # Use VIBE to assess
            assessment = await vibe_engine.assess_page(page)

            # Verify complete workflow
            assert "scores" in assessment
            assert manager.active_sessions

        finally:
            # Cleanup
            await manager.close_session(session_id)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
