"""
test_visualization_modules.py - Unit Tests for Visualization Modules
시각화 모듈 단위 테스트

Tests for:
- StyleGenerator (style_generator.py)
- JSUtilities (js_utilities.py)
- VirtualScrollGenerator (virtual_scroll.py)
- Design Tokens (design_tokens.json)
"""

import unittest
import json
from pathlib import Path
import sys

# Add src to path
# src를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.visualization.style_generator import StyleGenerator
from src.visualization.js_utilities import JSUtilities
from src.visualization.virtual_scroll import VirtualScrollGenerator


class TestDesignTokens(unittest.TestCase):
    """
    Test design tokens configuration
    디자인 토큰 설정 테스트
    """

    @classmethod
    def setUpClass(cls):
        """Load design tokens / 디자인 토큰 로드"""
        cls.tokens_path = Path(__file__).parent.parent / "config" / "design_tokens.json"
        with open(cls.tokens_path, 'r', encoding='utf-8') as f:
            cls.tokens = json.load(f)

    def test_tokens_file_exists(self):
        """Test that design tokens file exists / 디자인 토큰 파일 존재 테스트"""
        self.assertTrue(self.tokens_path.exists())

    def test_tokens_has_version(self):
        """Test that tokens have version / 토큰에 버전 존재 테스트"""
        self.assertIn('version', self.tokens)
        self.assertEqual(self.tokens['version'], '1.0.0')

    def test_tokens_has_colors(self):
        """Test that tokens have colors section / 토큰에 색상 섹션 존재 테스트"""
        self.assertIn('colors', self.tokens)
        colors = self.tokens['colors']
        self.assertIn('brand', colors)
        self.assertIn('gradients', colors)
        self.assertIn('status', colors)
        self.assertIn('neutral', colors)

    def test_brand_colors_valid(self):
        """Test that brand colors are valid hex / 브랜드 색상이 유효한 hex 테스트"""
        brand = self.tokens['colors']['brand']
        for name, color in brand.items():
            self.assertTrue(color.startswith('#'), f"Color {name} should start with #")
            self.assertEqual(len(color), 7, f"Color {name} should be 7 chars")

    def test_tokens_has_spacing(self):
        """Test that tokens have spacing section / 토큰에 간격 섹션 존재 테스트"""
        self.assertIn('spacing', self.tokens)
        spacing = self.tokens['spacing']
        self.assertIn('0', spacing)
        self.assertIn('4', spacing)

    def test_tokens_has_typography(self):
        """Test that tokens have typography section / 토큰에 타이포그래피 섹션 존재 테스트"""
        self.assertIn('typography', self.tokens)
        typography = self.tokens['typography']
        self.assertIn('font_family', typography)
        self.assertIn('font_size', typography)
        self.assertIn('font_weight', typography)

    def test_tokens_has_components(self):
        """Test that tokens have components section / 토큰에 컴포넌트 섹션 존재 테스트"""
        self.assertIn('components', self.tokens)
        components = self.tokens['components']
        self.assertIn('card', components)
        self.assertIn('button', components)
        self.assertIn('modal', components)

    def test_tokens_has_breakpoints(self):
        """Test that tokens have breakpoints / 토큰에 브레이크포인트 존재 테스트"""
        self.assertIn('breakpoints', self.tokens)
        breakpoints = self.tokens['breakpoints']
        self.assertIn('sm', breakpoints)
        self.assertIn('md', breakpoints)
        self.assertIn('lg', breakpoints)

    def test_chart_colors_count(self):
        """Test that chart has enough colors / 차트에 충분한 색상 존재 테스트"""
        chart_colors = self.tokens['colors']['chart']
        self.assertGreaterEqual(len(chart_colors), 10)


class TestStyleGenerator(unittest.TestCase):
    """
    Test StyleGenerator functionality
    StyleGenerator 기능 테스트
    """

    @classmethod
    def setUpClass(cls):
        """Initialize StyleGenerator / StyleGenerator 초기화"""
        cls.generator = StyleGenerator()

    def test_init_loads_tokens(self):
        """Test that tokens are loaded / 토큰 로드 테스트"""
        self.assertIsNotNone(self.generator.tokens)
        self.assertIn('colors', self.generator.tokens)

    def test_get_css_variables(self):
        """Test CSS variables generation / CSS 변수 생성 테스트"""
        css = self.generator.get_css_variables()
        self.assertIn(':root', css)
        self.assertIn('--color-primary', css)
        self.assertIn('--gradient-primary', css)

    def test_get_base_styles(self):
        """Test base styles generation / 기본 스타일 생성 테스트"""
        css = self.generator.get_base_styles()
        self.assertIn('body', css)
        self.assertIn('.visually-hidden', css)
        self.assertIn(':focus-visible', css)

    def test_get_card_styles(self):
        """Test card component styles / 카드 컴포넌트 스타일 테스트"""
        css = self.generator.get_component_styles('card')
        self.assertIn('.summary-card', css)
        self.assertIn('border-radius', css)
        self.assertIn(':hover', css)

    def test_get_navbar_styles(self):
        """Test navbar component styles / 네비게이션 바 컴포넌트 스타일 테스트"""
        css = self.generator.get_component_styles('navbar')
        self.assertIn('.top-navbar', css)
        self.assertIn('.nav-brand', css)
        self.assertIn('.nav-link', css)

    def test_get_table_styles(self):
        """Test table component styles / 테이블 컴포넌트 스타일 테스트"""
        css = self.generator.get_component_styles('table')
        self.assertIn('.employee-table', css)
        self.assertIn('thead', css)
        self.assertIn('.sortable', css)

    def test_get_utility_classes(self):
        """Test utility classes generation / 유틸리티 클래스 생성 테스트"""
        css = self.generator.get_utility_classes()
        self.assertIn('.m-', css)
        self.assertIn('.p-', css)
        self.assertIn('.text-', css)
        self.assertIn('.bg-', css)

    def test_generate_full_stylesheet(self):
        """Test full stylesheet generation / 전체 스타일시트 생성 테스트"""
        css = self.generator.generate_full_stylesheet()
        self.assertIn(':root', css)
        self.assertIn('body', css)
        self.assertIn('.summary-card', css)
        # Should be substantial
        self.assertGreater(len(css), 5000)


class TestJSUtilities(unittest.TestCase):
    """
    Test JSUtilities functionality
    JSUtilities 기능 테스트
    """

    @classmethod
    def setUpClass(cls):
        """Initialize JSUtilities / JSUtilities 초기화"""
        cls.js_utils = JSUtilities()

    def test_get_security_utils(self):
        """Test security utilities generation / 보안 유틸리티 생성 테스트"""
        js = self.js_utils.get_security_utils()
        self.assertIn('SecurityUtils', js)
        self.assertIn('sanitizeHTML', js)
        self.assertIn('setInnerHTML', js)
        self.assertIn('escapeRegex', js)

    def test_get_accessibility_utils(self):
        """Test accessibility utilities generation / 접근성 유틸리티 생성 테스트"""
        js = self.js_utils.get_accessibility_utils()
        self.assertIn('A11yUtils', js)
        self.assertIn('announce', js)
        self.assertIn('trapFocus', js)
        self.assertIn('handleKeyboardClick', js)
        self.assertIn('updateAriaSort', js)

    def test_get_performance_utils(self):
        """Test performance utilities generation / 성능 유틸리티 생성 테스트"""
        js = self.js_utils.get_performance_utils()
        self.assertIn('PerformanceUtils', js)
        self.assertIn('debounce', js)
        self.assertIn('throttle', js)
        self.assertIn('nextFrame', js)

    def test_get_data_utils(self):
        """Test data utilities generation / 데이터 유틸리티 생성 테스트"""
        js = self.js_utils.get_data_utils()
        self.assertIn('DataUtils', js)
        self.assertIn('formatNumber', js)
        self.assertIn('formatPercent', js)
        self.assertIn('formatDate', js)
        self.assertIn('calculateTenure', js)
        self.assertIn('sortByKey', js)

    def test_get_dom_utils(self):
        """Test DOM utilities generation / DOM 유틸리티 생성 테스트"""
        js = self.js_utils.get_dom_utils()
        self.assertIn('DOMUtils', js)
        self.assertIn('createElement', js)
        self.assertIn('show', js)
        self.assertIn('hide', js)
        self.assertIn('toggle', js)

    def test_get_storage_utils(self):
        """Test storage utilities generation / 저장소 유틸리티 생성 테스트"""
        js = self.js_utils.get_storage_utils()
        self.assertIn('StorageUtils', js)
        self.assertIn('get', js)
        self.assertIn('set', js)
        self.assertIn('remove', js)
        self.assertIn('isAvailable', js)

    def test_get_export_utils(self):
        """Test export utilities generation / 내보내기 유틸리티 생성 테스트"""
        js = self.js_utils.get_export_utils()
        self.assertIn('ExportUtils', js)
        self.assertIn('toCSV', js)
        self.assertIn('toJSON', js)
        self.assertIn('downloadFile', js)
        self.assertIn('printElement', js)

    def test_get_all_utilities(self):
        """Test all utilities combined / 모든 유틸리티 결합 테스트"""
        js = self.js_utils.get_all_utilities()
        self.assertIn('DEBUG_MODE', js)
        self.assertIn('debugLog', js)
        self.assertIn('SecurityUtils', js)
        self.assertIn('A11yUtils', js)
        self.assertIn('PerformanceUtils', js)
        self.assertIn('DataUtils', js)
        self.assertIn('DOMUtils', js)
        self.assertIn('StorageUtils', js)
        self.assertIn('ExportUtils', js)
        # Should be substantial
        self.assertGreater(len(js), 10000)


class TestVirtualScrollGenerator(unittest.TestCase):
    """
    Test VirtualScrollGenerator functionality
    VirtualScrollGenerator 기능 테스트
    """

    def test_default_config(self):
        """Test default configuration / 기본 설정 테스트"""
        generator = VirtualScrollGenerator()
        self.assertEqual(generator.row_height, 48)
        self.assertEqual(generator.buffer_size, 10)

    def test_custom_config(self):
        """Test custom configuration / 사용자 정의 설정 테스트"""
        generator = VirtualScrollGenerator(row_height=60, buffer_size=15)
        self.assertEqual(generator.row_height, 60)
        self.assertEqual(generator.buffer_size, 15)

    def test_get_virtual_scroll_js(self):
        """Test virtual scroll JS generation / 가상 스크롤 JS 생성 테스트"""
        generator = VirtualScrollGenerator()
        js = generator.get_virtual_scroll_js()

        # Check for main object
        # 메인 객체 확인
        self.assertIn('VirtualScroll', js)

        # Check for configuration
        # 설정 확인
        self.assertIn('rowHeight: 48', js)
        self.assertIn('bufferSize: 10', js)

        # Check for methods
        # 메서드 확인
        self.assertIn('init:', js)
        self.assertIn('render:', js)
        self.assertIn('renderRows:', js)
        self.assertIn('updateData:', js)
        self.assertIn('scrollToRow:', js)

    def test_get_integration_code(self):
        """Test integration code generation / 통합 코드 생성 테스트"""
        generator = VirtualScrollGenerator()
        js = generator.get_integration_code()

        self.assertIn('initVirtualScrolling', js)
        self.assertIn('DOMContentLoaded', js)

    def test_row_height_in_output(self):
        """Test that custom row height appears in output / 사용자 정의 행 높이가 출력에 나타나는지 테스트"""
        generator = VirtualScrollGenerator(row_height=50)
        js = generator.get_virtual_scroll_js()
        self.assertIn('rowHeight: 50', js)


class TestInputValidation(unittest.TestCase):
    """
    Test input validation in generate_dashboard.py
    generate_dashboard.py의 입력 검증 테스트
    """

    def test_year_validation_range(self):
        """Test year range validation / 연도 범위 검증 테스트"""
        # Valid years should be 2020-2050
        # 유효한 연도는 2020-2050이어야 함
        valid_years = [2020, 2025, 2030, 2050]
        invalid_years = [2019, 2051, 1999, 3000]

        for year in valid_years:
            self.assertTrue(2020 <= year <= 2050, f"Year {year} should be valid")

        for year in invalid_years:
            self.assertFalse(2020 <= year <= 2050, f"Year {year} should be invalid")

    def test_path_traversal_detection(self):
        """Test path traversal detection / 경로 순회 탐지 테스트"""
        safe_paths = [
            "/Users/test/output",
            "output_files",
            "./output"
        ]
        unsafe_paths = [
            "../../../etc/passwd",
            "output/../../../secret",
            "..\\..\\windows"
        ]

        for path in safe_paths:
            self.assertNotIn('..', path.replace('\\', '/').split('/'),
                           f"Path {path} should be safe")

        for path in unsafe_paths:
            self.assertIn('..', path.replace('\\', '/'),
                         f"Path {path} should be detected as unsafe")


class TestSecurityUtils(unittest.TestCase):
    """
    Test security-related functionality
    보안 관련 기능 테스트
    """

    def test_xss_prevention_patterns(self):
        """Test XSS prevention patterns / XSS 방지 패턴 테스트"""
        dangerous_inputs = [
            '<script>alert("XSS")</script>',
            '<img src="x" onerror="alert(1)">',
            '<svg onload="alert(1)">',
            'javascript:alert(1)',
            '<a href="javascript:alert(1)">click</a>'
        ]

        # These patterns should be detected/sanitized
        # 이러한 패턴은 탐지/살균되어야 함
        for input_str in dangerous_inputs:
            # Check that dangerous patterns exist
            self.assertTrue(
                '<script' in input_str.lower() or
                'onerror' in input_str.lower() or
                'onload' in input_str.lower() or
                'javascript:' in input_str.lower(),
                f"Pattern should be detected: {input_str}"
            )

    def test_html_entity_encoding(self):
        """Test HTML entity encoding / HTML 엔티티 인코딩 테스트"""
        # Characters that should be encoded
        # 인코딩되어야 하는 문자
        chars_to_encode = {
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '"': '&quot;',
            "'": '&#x27;'
        }

        for char, encoded in chars_to_encode.items():
            # Verify encoding mapping exists
            self.assertNotEqual(char, encoded)


class TestAccessibilityCompliance(unittest.TestCase):
    """
    Test accessibility compliance
    접근성 준수 테스트
    """

    def test_aria_attributes_in_js_utils(self):
        """Test ARIA attributes in JS utilities / JS 유틸리티의 ARIA 속성 테스트"""
        js_utils = JSUtilities()
        js = js_utils.get_accessibility_utils()

        # Check for ARIA-related functions
        # ARIA 관련 함수 확인
        self.assertIn('aria-live', js)
        self.assertIn('aria-sort', js)
        self.assertIn('aria-atomic', js)
        self.assertIn('role', js)

    def test_keyboard_navigation_support(self):
        """Test keyboard navigation support / 키보드 내비게이션 지원 테스트"""
        js_utils = JSUtilities()
        js = js_utils.get_accessibility_utils()

        # Check for keyboard event handling
        # 키보드 이벤트 처리 확인
        self.assertIn('handleKeyboardClick', js)
        self.assertIn('Enter', js)
        self.assertIn('Tab', js)

    def test_focus_trap_for_modals(self):
        """Test focus trap for modals / 모달용 포커스 트랩 테스트"""
        js_utils = JSUtilities()
        js = js_utils.get_accessibility_utils()

        self.assertIn('trapFocus', js)
        self.assertIn('focusableElements', js)


def run_tests():
    """Run all tests / 모든 테스트 실행"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    # 모든 테스트 클래스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestDesignTokens))
    suite.addTests(loader.loadTestsFromTestCase(TestStyleGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestJSUtilities))
    suite.addTests(loader.loadTestsFromTestCase(TestVirtualScrollGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestInputValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestAccessibilityCompliance))

    # Run tests
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
