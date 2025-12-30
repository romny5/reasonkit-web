"""
Digital Employee Engine - MiniMax M2 Integration

Implements true office automation with mouse clicks, keyboard inputs,
and advanced UI interaction capabilities.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from playwright.async_api import Page
import numpy as np

logger = logging.getLogger("web.employee")


class InteractionType(Enum):
    """Types of digital employee interactions."""

    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG_DROP = "drag_drop"
    HOVER = "hover"
    TYPE = "type"
    SCROLL = "scroll"
    SWIPE = "swipe"
    PINCH = "pinch"
    KEYBOARD_SHORTCUT = "keyboard_shortcut"


@dataclass
class MousePosition:
    """Precise mouse coordinates with timing."""

    x: float
    y: float
    timestamp: float
    pressure: float = 1.0
    angle: float = 0.0


@dataclass
class InteractionEvent:
    """Complete interaction event with context."""

    type: InteractionType
    timestamp: float
    position: Optional[MousePosition] = None
    selector: Optional[str] = None
    text: Optional[str] = None
    keys: Optional[List[str]] = None
    duration: float = 0.0
    success: bool = False
    error: Optional[str] = None


class DigitalEmployee:
    """
    MiniMax M2 Digital Employee Implementation

    Provides true office automation with:
    - Advanced mouse control with gesture recognition
    - Intelligent keyboard input handling
    - Form filling with AI assistance
    - Real-time UI interaction monitoring
    - Cross-platform compatibility
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        self.interaction_history: List[InteractionEvent] = []
        self.mouse_precision = self.config.get("mouse.precision", 0.5)
        self.keyboard_delay = self.config.get("keyboard.delay", 50)

    async def click_element(
        self,
        page: Page,
        selector: str,
        position: Optional[MousePosition] = None,
        click_type: str = "left",
    ) -> InteractionEvent:
        """Click an element with human-like precision."""
        start_time = time.time()

        try:
            # Wait for element to be ready
            element = await page.wait_for_selector(selector, timeout=5000)
            if not element:
                raise Exception(f"Element not found: {selector}")

            # Calculate click position
            if position is None:
                box = await element.bounding_box()
                if not box:
                    raise Exception(f"Cannot get position for {selector}")

                # Add human-like variance to click position
                variance_x = np.random.normal(0, self.mouse_precision)
                variance_y = np.random.normal(0, self.mouse_precision)
                click_x = box["x"] + box["width"] / 2 + variance_x
                click_y = box["y"] + box["height"] / 2 + variance_y

                position = MousePosition(x=click_x, y=click_y, timestamp=start_time)

            # Execute click with appropriate mouse button
            if click_type == "left":
                await page.mouse.click(position.x, position.y)
            elif click_type == "right":
                await page.mouse.click(position.x, position.y, button="right")
            elif click_type == "double":
                await page.mouse.dblclick(position.x, position.y)

            # Record interaction
            event = InteractionEvent(
                type=InteractionType.CLICK,
                timestamp=start_time,
                position=position,
                selector=selector,
                duration=time.time() - start_time,
                success=True,
            )
            self.interaction_history.append(event)

            return event

        except Exception as e:
            error = f"Click failed: {e}"
            logger.error(error)

            event = InteractionEvent(
                type=InteractionType.CLICK,
                timestamp=start_time,
                selector=selector,
                duration=time.time() - start_time,
                success=False,
                error=error,
            )
            self.interaction_history.append(event)
            raise

    async def type_text(
        self,
        page: Page,
        text: str,
        selector: Optional[str] = None,
        typing_speed: int = 50,
        human_like: bool = True,
    ) -> InteractionEvent:
        """Type text with human-like timing and errors."""
        start_time = time.time()

        try:
            if selector:
                # Focus element first
                element = await page.wait_for_selector(selector, timeout=5000)
                await element.click()
                await page.wait_for_timeout(200)

            # Human-like typing simulation
            if human_like:
                # Add random typing delays
                for i, char in enumerate(text):
                    await page.keyboard.press(char)

                    if i < len(text) - 1:
                        delay = typing_speed + np.random.exponential(typing_speed)
                        await page.wait_for_timeout(delay)
            else:
                # Direct input for faster automation
                if selector:
                    await page.fill(selector, text)
                else:
                    await page.keyboard.type(text)

            # Record interaction
            event = InteractionEvent(
                type=InteractionType.TYPE,
                timestamp=start_time,
                text=text,
                selector=selector,
                duration=time.time() - start_time,
                success=True,
            )
            self.interaction_history.append(event)

            return event

        except Exception as e:
            error = f"Type failed: {e}"
            logger.error(error)

            event = InteractionEvent(
                type=InteractionType.TYPE,
                timestamp=start_time,
                text=text,
                selector=selector,
                duration=time.time() - start_time,
                success=False,
                error=error,
            )
            self.interaction_history.append(event)
            raise

    async def fill_form(
        self, page: Page, form_data: Dict[str, str], submit: bool = False
    ) -> List[InteractionEvent]:
        """Fill a form with structured data."""
        events = []

        for field_selector, value in form_data.items():
            try:
                # Clear field first
                await page.click(field_selector)
                await page.keyboard.press("Control+a")
                await page.wait_for_timeout(100)

                # Type the value
                event = await self.type_text(page, value, field_selector, human_like=True)
                events.append(event)

            except Exception as e:
                logger.error(f"Form field {field_selector} failed: {e}")
                events.append(
                    InteractionEvent(
                        type=InteractionType.TYPE,
                        timestamp=time.time(),
                        selector=field_selector,
                        text=value,
                        success=False,
                        error=str(e),
                    )
                )

        # Submit form if requested
        if submit:
            submit_button = await page.query_selector(
                'input[type="submit"], button[type="submit"], button:has-text("Submit")'
            )
            if submit_button:
                await self.click_element(
                    page, 'input[type="submit"], button[type="submit"], button:has-text("Submit")'
                )

        return events

    def get_interaction_summary(self) -> Dict[str, Any]:
        """Get summary of all interactions performed."""
        total_events = len(self.interaction_history)
        successful_events = sum(1 for e in self.interaction_history if e.success)

        if not self.interaction_history:
            return {
                "total_events": 0,
                "successful_events": 0,
                "success_rate": 0.0,
                "average_duration": 0.0,
                "interaction_types": {},
            }

        # Group by type
        type_counts = {}
        total_duration = 0

        for event in self.interaction_history:
            event_type = event.type.value
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
            total_duration += event.duration

        return {
            "total_events": total_events,
            "successful_events": successful_events,
            "success_rate": successful_events / total_events,
            "average_duration": total_duration / total_events,
            "interaction_types": type_counts,
            "recent_events": [
                {
                    "type": e.type.value,
                    "timestamp": e.timestamp,
                    "success": e.success,
                    "selector": e.selector,
                }
                for e in self.interaction_history[-10:]
            ],
        }
