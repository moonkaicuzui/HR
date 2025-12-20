"""
style_generator.py - CSS Style Generator using Design Tokens
디자인 토큰을 사용한 CSS 스타일 생성기

This module generates CSS styles from centralized design tokens,
ensuring consistency across all dashboard components.
이 모듈은 중앙 집중식 디자인 토큰에서 CSS 스타일을 생성하여
모든 대시보드 구성 요소 간의 일관성을 보장합니다.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class StyleGenerator:
    """
    Generate CSS styles from design tokens
    디자인 토큰에서 CSS 스타일 생성
    """

    def __init__(self, tokens_path: Optional[Path] = None):
        """
        Initialize StyleGenerator with design tokens
        디자인 토큰으로 StyleGenerator 초기화

        Args:
            tokens_path: Path to design_tokens.json
        """
        if tokens_path is None:
            tokens_path = Path(__file__).parent.parent.parent / "config" / "design_tokens.json"

        self.tokens = self._load_tokens(tokens_path)

    def _load_tokens(self, path: Path) -> Dict[str, Any]:
        """
        Load design tokens from JSON file
        JSON 파일에서 디자인 토큰 로드

        Args:
            path: Path to tokens file

        Returns:
            Dictionary of design tokens
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load design tokens: {e}")
            return self._get_default_tokens()

    def _get_default_tokens(self) -> Dict[str, Any]:
        """
        Return default tokens if file not found
        파일을 찾을 수 없는 경우 기본 토큰 반환
        """
        return {
            "colors": {
                "brand": {"primary": "#667eea"},
                "neutral": {"background": "#f8f9fa", "white": "#ffffff"}
            },
            "shadows": {"card": "0 4px 6px rgba(0,0,0,0.07)"},
            "spacing": {"4": "16px"},
            "typography": {"font_family": {"sans": "sans-serif"}}
        }

    def get_css_variables(self) -> str:
        """
        Generate CSS custom properties from tokens
        토큰에서 CSS 커스텀 속성 생성

        Returns:
            CSS :root block with custom properties
        """
        colors = self.tokens.get("colors", {})
        shadows = self.tokens.get("shadows", {})
        spacing = self.tokens.get("spacing", {})
        typography = self.tokens.get("typography", {})

        variables = [":root {"]

        # Brand colors
        # 브랜드 색상
        brand = colors.get("brand", {})
        for name, value in brand.items():
            variables.append(f"    --color-{name}: {value};")

        # Gradients
        # 그라디언트
        gradients = colors.get("gradients", {})
        for name, value in gradients.items():
            variables.append(f"    --gradient-{name}: {value};")

        # Status colors
        # 상태 색상
        status = colors.get("status", {})
        for name, value in status.items():
            variables.append(f"    --color-{name}: {value};")

        # Neutral colors
        # 중립 색상
        neutral = colors.get("neutral", {})
        for name, value in neutral.items():
            variables.append(f"    --color-{name.replace('_', '-')}: {value};")

        # Shadows
        # 그림자
        for name, value in shadows.items():
            variables.append(f"    --shadow-{name.replace('_', '-')}: {value};")

        # Spacing
        # 간격
        for name, value in spacing.items():
            variables.append(f"    --spacing-{name}: {value};")

        # Typography
        # 타이포그래피
        font_sizes = typography.get("font_size", {})
        for name, value in font_sizes.items():
            variables.append(f"    --font-size-{name}: {value};")

        font_weights = typography.get("font_weight", {})
        for name, value in font_weights.items():
            variables.append(f"    --font-weight-{name}: {value};")

        variables.append("}")

        return "\n".join(variables)

    def get_base_styles(self) -> str:
        """
        Generate base/reset styles
        기본/리셋 스타일 생성

        Returns:
            CSS base styles
        """
        typography = self.tokens.get("typography", {})
        colors = self.tokens.get("colors", {})

        font_family = typography.get("font_family", {}).get("sans", "sans-serif")
        bg_color = colors.get("neutral", {}).get("background", "#f8f9fa")

        return f"""
/* Base Styles / 기본 스타일 */
*, *::before, *::after {{
    box-sizing: border-box;
}}

body {{
    font-family: {font_family};
    background: {bg_color};
    margin: 0;
    padding: 0;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

/* Visually Hidden (Accessibility) / 시각적으로 숨김 (접근성) */
.visually-hidden {{
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    padding: 0 !important;
    margin: -1px !important;
    overflow: hidden !important;
    clip: rect(0, 0, 0, 0) !important;
    white-space: nowrap !important;
    border: 0 !important;
}}

/* Focus Styles (Accessibility) / 포커스 스타일 (접근성) */
:focus-visible {{
    outline: 2px solid var(--color-primary, #667eea);
    outline-offset: 2px;
}}

/* Skip Link (Accessibility) / 스킵 링크 (접근성) */
.skip-link {{
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--color-primary, #667eea);
    color: white;
    padding: 8px 16px;
    z-index: 10000;
    transition: top 0.3s;
}}

.skip-link:focus {{
    top: 0;
}}

/* Reduced Motion Preference / 모션 감소 선호 */
@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }}
}}
"""

    def get_component_styles(self, component: str) -> str:
        """
        Generate styles for a specific component
        특정 컴포넌트의 스타일 생성

        Args:
            component: Component name (card, button, modal, etc.)

        Returns:
            CSS styles for the component
        """
        components = self.tokens.get("components", {})
        config = components.get(component, {})

        if component == "card":
            return self._get_card_styles(config)
        elif component == "button":
            return self._get_button_styles(config)
        elif component == "modal":
            return self._get_modal_styles(config)
        elif component == "navbar":
            return self._get_navbar_styles(config)
        elif component == "table":
            return self._get_table_styles(config)

        return ""

    def _get_card_styles(self, config: Dict[str, Any]) -> str:
        """Generate card component styles / 카드 컴포넌트 스타일 생성"""
        padding = config.get("padding", "25px")
        radius = config.get("border_radius", "12px")
        margin = config.get("margin_bottom", "20px")

        return f"""
/* Card Component / 카드 컴포넌트 */
.summary-card {{
    background: var(--color-white, white);
    border-radius: {radius};
    padding: {padding};
    margin-bottom: {margin};
    box-shadow: var(--shadow-card, 0 4px 6px rgba(0,0,0,0.07));
    transition: transform 0.3s, box-shadow 0.3s;
    cursor: pointer;
    position: relative;
    overflow: hidden;
}}

.summary-card:hover {{
    transform: translateY(-5px);
    box-shadow: var(--shadow-card-hover, 0 8px 16px rgba(0,0,0,0.12));
}}

.summary-card:focus {{
    outline: 2px solid var(--color-primary, #667eea);
    outline-offset: 2px;
}}
"""

    def _get_button_styles(self, config: Dict[str, Any]) -> str:
        """Generate button component styles / 버튼 컴포넌트 스타일 생성"""
        padding = config.get("padding_base", "8px 16px")
        radius = config.get("border_radius", "8px")

        return f"""
/* Button Component / 버튼 컴포넌트 */
.btn-custom {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: {padding};
    border-radius: {radius};
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    border: none;
}}

.btn-custom:hover {{
    transform: translateY(-2px);
}}

.btn-custom:focus-visible {{
    outline: 2px solid var(--color-primary, #667eea);
    outline-offset: 2px;
}}
"""

    def _get_modal_styles(self, config: Dict[str, Any]) -> str:
        """Generate modal component styles / 모달 컴포넌트 스타일 생성"""
        max_width = config.get("max_width", "900px")

        return f"""
/* Modal Component / 모달 컴포넌트 */
.modal-content {{
    max-width: {max_width};
    border-radius: 16px;
    border: none;
    box-shadow: var(--shadow-xl, 0 20px 25px -5px rgba(0, 0, 0, 0.1));
}}

.modal-header {{
    border-bottom: 1px solid var(--color-border, #e2e8f0);
    padding: 16px 20px;
}}

.modal-body {{
    padding: 20px;
}}

.modal-footer {{
    border-top: 1px solid var(--color-border, #e2e8f0);
    padding: 16px 20px;
}}
"""

    def _get_navbar_styles(self, config: Dict[str, Any]) -> str:
        """Generate navbar component styles / 네비게이션 바 컴포넌트 스타일 생성"""
        padding = config.get("padding", "12px 0")

        return f"""
/* Navbar Component / 네비게이션 바 컴포넌트 */
.top-navbar {{
    background: var(--gradient-navbar, linear-gradient(135deg, #1a1a2e 0%, #16213e 100%));
    padding: {padding};
    box-shadow: var(--shadow-navbar, 0 2px 10px rgba(0,0,0,0.2));
    position: sticky;
    top: 0;
    z-index: var(--z-sticky, 1020);
}}

.nav-brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    color: white;
}}

.nav-links {{
    display: flex;
    gap: 8px;
}}

.nav-link {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 8px;
    text-decoration: none;
    color: rgba(255,255,255,0.8);
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    transition: all 0.3s ease;
}}

.nav-link:hover {{
    background: rgba(255,255,255,0.15);
    color: white;
    transform: translateY(-2px);
}}

.nav-link.active {{
    background: var(--gradient-primary, linear-gradient(135deg, #667eea 0%, #764ba2 100%));
    color: white;
}}
"""

    def _get_table_styles(self, config: Dict[str, Any]) -> str:
        """Generate table component styles / 테이블 컴포넌트 스타일 생성"""
        header_bg = config.get("header_bg", "#f8f9fa")
        stripe_bg = config.get("stripe_bg", "#f8fafc")

        return f"""
/* Table Component / 테이블 컴포넌트 */
.employee-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}}

.employee-table thead {{
    background: {header_bg};
    position: sticky;
    top: 0;
    z-index: 10;
}}

.employee-table th {{
    padding: 12px 8px;
    font-weight: 600;
    text-align: left;
    border-bottom: 2px solid var(--color-border, #e2e8f0);
}}

.employee-table th.sortable {{
    cursor: pointer;
    user-select: none;
}}

.employee-table th.sortable:hover {{
    background: var(--color-border-light, #f1f5f9);
}}

.employee-table tbody tr {{
    transition: background 0.2s;
}}

.employee-table tbody tr:nth-child(even) {{
    background: {stripe_bg};
}}

.employee-table tbody tr:hover {{
    background: var(--color-info-light, #dbeafe);
}}

.employee-table td {{
    padding: 10px 8px;
    border-bottom: 1px solid var(--color-border-light, #f1f5f9);
    vertical-align: middle;
}}
"""

    def get_utility_classes(self) -> str:
        """
        Generate utility classes
        유틸리티 클래스 생성

        Returns:
            CSS utility classes
        """
        spacing = self.tokens.get("spacing", {})
        colors = self.tokens.get("colors", {})

        utilities = ["/* Utility Classes / 유틸리티 클래스 */"]

        # Margin utilities
        # 마진 유틸리티
        for name, value in spacing.items():
            utilities.append(f".m-{name} {{ margin: {value}; }}")
            utilities.append(f".mt-{name} {{ margin-top: {value}; }}")
            utilities.append(f".mb-{name} {{ margin-bottom: {value}; }}")
            utilities.append(f".mx-{name} {{ margin-left: {value}; margin-right: {value}; }}")
            utilities.append(f".my-{name} {{ margin-top: {value}; margin-bottom: {value}; }}")

        # Padding utilities
        # 패딩 유틸리티
        for name, value in spacing.items():
            utilities.append(f".p-{name} {{ padding: {value}; }}")
            utilities.append(f".pt-{name} {{ padding-top: {value}; }}")
            utilities.append(f".pb-{name} {{ padding-bottom: {value}; }}")
            utilities.append(f".px-{name} {{ padding-left: {value}; padding-right: {value}; }}")
            utilities.append(f".py-{name} {{ padding-top: {value}; padding-bottom: {value}; }}")

        # Text color utilities
        # 텍스트 색상 유틸리티
        status_colors = colors.get("status", {})
        for name, value in status_colors.items():
            utilities.append(f".text-{name.replace('_', '-')} {{ color: {value}; }}")

        # Background color utilities
        # 배경 색상 유틸리티
        for name, value in status_colors.items():
            utilities.append(f".bg-{name.replace('_', '-')} {{ background-color: {value}; }}")

        return "\n".join(utilities)

    def generate_full_stylesheet(self) -> str:
        """
        Generate complete stylesheet from design tokens
        디자인 토큰에서 전체 스타일시트 생성

        Returns:
            Complete CSS stylesheet
        """
        sections = [
            "/* ========================================",
            " * HR Dashboard Styles - Generated from Design Tokens",
            " * HR 대시보드 스타일 - 디자인 토큰에서 생성됨",
            " * ======================================== */",
            "",
            self.get_css_variables(),
            "",
            self.get_base_styles(),
            "",
            self.get_component_styles("navbar"),
            "",
            self.get_component_styles("card"),
            "",
            self.get_component_styles("button"),
            "",
            self.get_component_styles("table"),
            "",
            self.get_component_styles("modal"),
            "",
            self.get_utility_classes(),
        ]

        return "\n".join(sections)


def main():
    """Test StyleGenerator / StyleGenerator 테스트"""
    generator = StyleGenerator()
    css = generator.generate_full_stylesheet()
    print("Generated CSS length:", len(css), "characters")
    print("\n--- CSS Variables ---")
    print(generator.get_css_variables()[:500])


if __name__ == "__main__":
    main()
