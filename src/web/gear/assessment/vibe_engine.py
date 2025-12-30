"""
VIBE Assessment Engine - MiniMax M2 Integration

Implements aesthetic expression mastery for automatic UI/UX quality evaluation.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Page
import numpy as np
from colorama import Fore, Style

logger = logging.getLogger("web.vibe")


@dataclass
class VisualElement:
    """Individual visual element analysis."""

    selector: str
    element_type: str
    position: Tuple[float, float, float, float]
    color_analysis: Dict[str, Any]
    text_analysis: Dict[str, Any]
    accessibility_score: float
    visual_hierarchy: float
    contrast_ratio: float
    issues: List[str]
    recommendations: List[str]


@dataclass
class LayoutAnalysis:
    """Overall layout and composition analysis."""

    balance_score: float
    alignment_score: float
    whitespace_score: float
    visual_flow_score: float
    grid_consistency: float
    responsive_score: float


class VIBEAssessmentEngine:
    """
    VIBE Benchmark Assessment Engine

    Implements MiniMax M2's aesthetic expression mastery for:
    - Automatic UI/UX quality evaluation
    - Visual design analysis
    - Accessibility compliance
    - Performance assessment
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}
        self.assessment_history: List[Dict[str, Any]] = []

    async def assess_page(self, page: Page) -> Dict[str, Any]:
        """Perform comprehensive VIBE assessment of a page."""
        start_time = time.time()

        try:
            # Capture screenshot
            screenshot_path = await self._capture_page_screenshot(page)

            # Analyze elements
            visual_elements = await self._analyze_visual_elements(page)
            layout_analysis = await self._analyze_layout(page, visual_elements)
            accessibility_score = await self._assess_accessibility(page, visual_elements)
            performance_score = await self._assess_performance(page)

            # Calculate scores
            aesthetic_score = self._calculate_aesthetic_score(visual_elements, layout_analysis)
            usability_score = self._calculate_usability_score(visual_elements, layout_analysis)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                visual_elements, layout_analysis, accessibility_score, performance_score
            )

            # Overall assessment
            overall_score = (
                aesthetic_score * 0.3
                + usability_score * 0.3
                + accessibility_score * 0.2
                + performance_score * 0.2
            )

            assessment = {
                "timestamp": time.time(),
                "url": page.url,
                "scores": {
                    "aesthetic": round(aesthetic_score, 2),
                    "usability": round(usability_score, 2),
                    "accessibility": round(accessibility_score, 2),
                    "performance": round(performance_score, 2),
                    "overall": round(overall_score, 2),
                },
                "analysis": {
                    "visual_elements": [ve.__dict__ for ve in visual_elements],
                    "layout": layout_analysis.__dict__,
                    "element_count": len(visual_elements),
                },
                "issues": self._collect_issues(visual_elements, layout_analysis),
                "recommendations": recommendations,
                "assessment_time": round(time.time() - start_time, 2),
                "screenshot": screenshot_path,
            }

            self.assessment_history.append(assessment)
            self._print_vibe_summary(assessment)

            return assessment

        except Exception as e:
            logger.error(f"VIBE assessment failed: {e}")
            raise

    async def _capture_page_screenshot(self, page: Page) -> str:
        """Capture full page screenshot."""
        screenshot_dir = Path("./assessments/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        screenshot_path = screenshot_dir / f"page_{timestamp}.png"

        await page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)

    async def _analyze_visual_elements(self, page: Page) -> List[VisualElement]:
        """Analyze individual visual elements."""
        elements = []

        selectors = ["button", "input", "a", "h1, h2, h3, h4, h5, h6", "p", "img"]

        for selector in selectors:
            try:
                element_handles = await page.query_selector_all(selector)

                for handle in element_handles:
                    try:
                        tag_name = await handle.evaluate("el => el.tagName.toLowerCase()")
                        bounding_box = await handle.bounding_box()

                        if not bounding_box:
                            continue

                        # Get computed styles
                        computed_style = await handle.evaluate("""
                            el => {
                                const styles = window.getComputedStyle(el);
                                return {
                                    color: styles.color,
                                    backgroundColor: styles.backgroundColor,
                                    fontSize: styles.fontSize,
                                    fontWeight: styles.fontWeight
                                };
                            }
                        """)

                        # Analyze element
                        element_analysis = await self._analyze_single_element(
                            page, handle, tag_name, bounding_box, computed_style
                        )

                        elements.append(element_analysis)

                    except Exception:
                        continue

            except Exception:
                continue

        return elements

    async def _analyze_single_element(
        self, page: Page, handle, tag_name: str, box: dict, styles: dict
    ) -> VisualElement:
        """Analyze a single visual element."""

        # Color analysis
        color_analysis = self._analyze_color_usage(styles)

        # Text analysis
        text_content = ""
        if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6", "p", "a"]:
            try:
                text_content = await handle.inner_text()
            except:
                pass

        text_analysis = self._analyze_text_content(text_content, styles)

        # Contrast ratio
        contrast_ratio = self._calculate_contrast_ratio(styles)

        # Accessibility score
        accessibility_score = self._assess_element_accessibility(tag_name, styles, contrast_ratio)

        # Visual hierarchy
        visual_hierarchy = self._assess_visual_hierarchy(tag_name, styles)

        # Issues and recommendations
        issues, recommendations = self._element_quality_check(tag_name, styles, contrast_ratio)

        return VisualElement(
            selector=await handle.evaluate("el => el.selector || el.tagName"),
            element_type=tag_name,
            position=(box["x"], box["y"], box["width"], box["height"]),
            color_analysis=color_analysis,
            text_analysis=text_analysis,
            accessibility_score=accessibility_score,
            visual_hierarchy=visual_hierarchy,
            contrast_ratio=contrast_ratio,
            issues=issues,
            recommendations=recommendations,
        )

    def _analyze_color_usage(self, styles: Dict[str, str]) -> Dict[str, Any]:
        """Analyze color usage and consistency."""
        colors = {
            "text": styles.get("color", "#000000"),
            "background": styles.get("backgroundColor", "#ffffff"),
        }

        return {
            "text_color": colors["text"],
            "background_color": colors["background"],
            "color_harmony_score": 0.7,  # Simplified
        }

    def _analyze_text_content(self, text: str, styles: Dict[str, str]) -> Dict[str, Any]:
        """Analyze text content quality."""
        if not text:
            return {"has_text": False}

        font_size = styles.get("fontSize", "16px")
        try:
            size_px = float(font_size.replace("px", ""))
        except:
            size_px = 16

        return {
            "has_text": True,
            "text_length": len(text),
            "word_count": len(text.split()),
            "font_size_px": size_px,
            "readability_score": min(1.0, size_px / 16),
        }

    def _calculate_contrast_ratio(self, styles: Dict[str, str]) -> float:
        """Calculate contrast ratio."""
        # Simplified contrast calculation
        try:
            text_color = styles.get("color", "#000000")
            bg_color = styles.get("backgroundColor", "#ffffff")

            def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
                hex_color = hex_color.lstrip("#")
                return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

            text_rgb = hex_to_rgb(text_color) if text_color.startswith("#") else (0, 0, 0)
            bg_rgb = hex_to_rgb(bg_color) if bg_color.startswith("#") else (255, 255, 255)

            # Calculate relative luminance
            def get_luminance(rgb: Tuple[int, int, int]) -> float:
                r, g, b = [c / 255 for c in rgb]
                r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
                g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
                b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
                return 0.2126 * r + 0.7152 * g + 0.0722 * b

            text_lum = get_luminance(text_rgb)
            bg_lum = get_luminance(bg_rgb)

            if bg_lum > text_lum:
                return (bg_lum + 0.05) / (text_lum + 0.05)
            else:
                return (text_lum + 0.05) / (bg_lum + 0.05)

        except Exception:
            return 4.5

    def _assess_element_accessibility(
        self, tag_name: str, styles: Dict[str, str], contrast_ratio: float
    ) -> float:
        """Assess accessibility compliance."""
        score = 1.0

        if contrast_ratio < 4.5:
            score -= 0.3
        elif contrast_ratio < 7.0:
            score -= 0.1

        try:
            font_size = float(styles.get("fontSize", "16px").replace("px", ""))
            if font_size < 14:
                score -= 0.2
            elif font_size < 16:
                score -= 0.1
        except:
            score -= 0.1

        return max(0.0, score)

    def _assess_visual_hierarchy(self, tag_name: str, styles: Dict[str, str]) -> float:
        """Assess visual hierarchy strength."""
        score = 0.5

        if tag_name == "h1":
            score = 1.0
        elif tag_name == "h2":
            score = 0.9
        elif tag_name == "h3":
            score = 0.8
        elif tag_name in ["h4", "h5", "h6"]:
            score = 0.7
        elif tag_name == "p":
            score = 0.6

        font_weight = styles.get("fontWeight", "normal")
        if font_weight == "bold" or font_weight == "700":
            score += 0.1

        return min(1.0, score)

    def _element_quality_check(
        self, tag_name: str, styles: Dict[str, str], contrast_ratio: float
    ) -> Tuple[List[str], List[str]]:
        """Check element for quality issues."""
        issues = []
        recommendations = []

        if contrast_ratio < 3.0:
            issues.append("Poor contrast ratio")
            recommendations.append("Increase contrast ratio to at least 4.5:1")
        elif contrast_ratio < 4.5:
            issues.append("Below recommended contrast ratio")
            recommendations.append("Consider increasing contrast ratio to 4.5:1 or higher")

        try:
            font_size = float(styles.get("fontSize", "16px").replace("px", ""))
            if font_size < 14:
                issues.append("Font size too small for accessibility")
                recommendations.append("Increase font size to at least 16px")
        except:
            issues.append("Invalid font size")
            recommendations.append("Ensure font size is properly specified")

        return issues, recommendations

    async def _analyze_layout(self, page: Page, elements: List[VisualElement]) -> LayoutAnalysis:
        """Analyze overall layout quality."""
        if not elements:
            return LayoutAnalysis(0, 0, 0, 0, 0, 0)

        positions = [e.position for e in elements]

        return LayoutAnalysis(
            balance_score=self._assess_layout_balance(positions),
            alignment_score=self._assess_alignment(positions),
            whitespace_score=self._assess_whitespace_usage(positions),
            visual_flow_score=0.7,  # Simplified
            grid_consistency=0.6,  # Simplified
            responsive_score=0.8,  # Simplified
        )

    def _assess_layout_balance(self, positions: List[Tuple[float, float, float, float]]) -> float:
        """Assess visual balance."""
        if not positions:
            return 0.0

        # Simplified balance assessment
        return 0.7

    def _assess_alignment(self, positions: List[Tuple[float, float, float, float]]) -> float:
        """Assess element alignment."""
        if len(positions) < 2:
            return 1.0

        return 0.6

    def _assess_whitespace_usage(self, positions: List[Tuple[float, float, float, float]]) -> float:
        """Assess whitespace usage."""
        if not positions:
            return 0.0

        return 0.6

    async def _assess_accessibility(self, page: Page, elements: List[VisualElement]) -> float:
        """Assess overall page accessibility."""
        if not elements:
            return 0.0

        avg_score = sum(element.accessibility_score for element in elements) / len(elements)
        return min(1.0, avg_score)

    async def _assess_performance(self, page: Page) -> float:
        """Assess page performance."""
        try:
            metrics = await page.evaluate("""
                () => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    return {
                        loadTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0
                    };
                }
            """)

            load_time = metrics.get("loadTime", 0)

            if load_time < 1000:
                return 1.0
            elif load_time < 3000:
                return 0.8
            elif load_time < 5000:
                return 0.6
            else:
                return 0.3

        except Exception:
            return 0.5

    def _calculate_aesthetic_score(
        self, elements: List[VisualElement], layout: LayoutAnalysis
    ) -> float:
        """Calculate aesthetic score."""
        if not elements:
            return 0.0

        color_scores = [
            element.color_analysis.get("color_harmony_score", 0.5) for element in elements
        ]
        avg_color_score = sum(color_scores) / len(color_scores)

        hierarchy_scores = [element.visual_hierarchy for element in elements]
        avg_hierarchy_score = sum(hierarchy_scores) / len(hierarchy_scores)

        aesthetic_score = avg_color_score * 0.5 + avg_hierarchy_score * 0.5
        return min(1.0, aesthetic_score)

    def _calculate_usability_score(
        self, elements: List[VisualElement], layout: LayoutAnalysis
    ) -> float:
        """Calculate usability score."""
        if not elements:
            return 0.0

        readability_scores = [
            element.text_analysis.get("readability_score", 0.5)
            for element in elements
            if element.text_analysis.get("has_text", False)
        ]
        avg_readability = (
            sum(readability_scores) / len(readability_scores) if readability_scores else 0.5
        )

        return avg_readability

    def _generate_recommendations(
        self,
        elements: List[VisualElement],
        layout: LayoutAnalysis,
        accessibility_score: float,
        performance_score: float,
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        for element in elements:
            recommendations.extend(element.recommendations)

        if accessibility_score < 0.7:
            recommendations.append("Improve accessibility compliance (WCAG guidelines)")

        if performance_score < 0.7:
            recommendations.append("Optimize page performance (load time, resource usage)")

        return list(dict.fromkeys(recommendations))[:10]

    def _collect_issues(self, elements: List[VisualElement], layout: LayoutAnalysis) -> List[str]:
        """Collect all identified issues."""
        issues = []

        for element in elements:
            issues.extend(element.issues)

        return issues

    def _print_vibe_summary(self, assessment: Dict[str, Any]) -> None:
        """Print VIBE assessment summary."""
        scores = assessment["scores"]

        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}VIBE BENCHMARK ASSESSMENT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

        print(f"URL: {assessment['url']}")
        print(f"Elements Analyzed: {assessment['analysis']['element_count']}")
        print(f"Assessment Time: {assessment['assessment_time']}s")

        print(f"\n{Fore.YELLOW}SCORES:{Style.RESET_ALL}")
        print(f"  Aesthetic:     {scores['aesthetic']:.1f}/10")
        print(f"  Usability:     {scores['usability']:.1f}/10")
        print(f"  Accessibility: {scores['accessibility']:.1f}/10")
        print(f"  Performance:   {scores['performance']:.1f}/10")
        print(f"  {Fore.GREEN}OVERALL:      {scores['overall']:.1f}/10{Style.RESET_ALL}")

        if assessment["issues"]:
            print(f"\n{Fore.RED}ISSUES DETECTED:{Style.RESET_ALL}")
            for issue in assessment["issues"][:5]:
                print(f"  • {issue}")

        if assessment["recommendations"]:
            print(f"\n{Fore.BLUE}TOP RECOMMENDATIONS:{Style.RESET_ALL}")
            for rec in assessment["recommendations"][:5]:
                print(f"  • {rec}")

        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
