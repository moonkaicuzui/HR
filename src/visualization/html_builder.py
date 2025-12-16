"""
html_builder.py - HTML Dashboard Builder
HTML 대시보드 빌더

Generates complete, standalone HTML dashboards with embedded data and JavaScript.
내장된 데이터와 JavaScript가 있는 완전하고 독립적인 HTML 대시보드를 생성합니다.

Core Features / 핵심 기능:
- Single-file HTML generation (no external dependencies) / 단일 파일 HTML 생성 (외부 종속성 없음)
- Embedded Chart.js and Bootstrap via CDN / CDN을 통한 Chart.js 및 Bootstrap 내장
- Multi-language support / 다국어 지원
- Responsive design / 반응형 디자인
- Dark mode support / 다크 모드 지원
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.i18n import I18n
from .chart_generator import ChartGenerator, ChartConfig


class HTMLBuilder:
    """
    HTML dashboard builder with component-based architecture
    컴포넌트 기반 아키텍처를 사용한 HTML 대시보드 빌더
    """

    def __init__(
        self,
        dashboard_config_path: Optional[str] = None,
        i18n: Optional[I18n] = None,
        chart_generator: Optional[ChartGenerator] = None
    ):
        """
        Initialize HTMLBuilder
        HTMLBuilder 초기화

        Args:
            dashboard_config_path: Path to dashboard_config.json / dashboard_config.json 경로
            i18n: I18n instance / I18n 인스턴스
            chart_generator: ChartGenerator instance / ChartGenerator 인스턴스
        """
        self.logger = get_logger()
        self.i18n = i18n
        self.chart_generator = chart_generator or ChartGenerator(i18n=i18n)

        # Load dashboard config / 대시보드 설정 로드
        if dashboard_config_path is None:
            hr_root = Path(__file__).parent.parent.parent
            dashboard_config_path = hr_root / "config" / "dashboard_config.json"

        self.config_path = Path(dashboard_config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load dashboard configuration
        대시보드 설정 로드

        Returns:
            Dashboard configuration dictionary / 대시보드 설정 딕셔너리
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(
                "대시보드 설정 로드 실패",
                "Failed to load dashboard config",
                error=str(e)
            )
            return {}

    def build_dashboard(
        self,
        title: str,
        cards: List[Dict[str, Any]],
        charts: List[ChartConfig],
        language: str = "ko",
        additional_sections: Optional[List[str]] = None
    ) -> str:
        """
        Build complete HTML dashboard
        완전한 HTML 대시보드 구축

        Args:
            title: Dashboard title / 대시보드 제목
            cards: List of metric cards to display / 표시할 메트릭 카드 목록
            charts: List of chart configurations / 차트 설정 목록
            language: Current language / 현재 언어
            additional_sections: Additional HTML sections / 추가 HTML 섹션

        Returns:
            Complete HTML string / 완전한 HTML 문자열
        """
        self.logger.info(
            "대시보드 HTML 빌드 시작",
            "Starting dashboard HTML build",
            cards_count=len(cards),
            charts_count=len(charts)
        )

        # Build HTML components / HTML 컴포넌트 구축
        head = self._build_head(title)
        header = self._build_header(title, language)
        cards_section = self._build_cards_section(cards, language)
        charts_section = self._build_charts_section(charts)
        footer = self._build_footer()

        # Build modal component / 모달 컴포넌트 구축
        modal = self._build_modal()

        # Combine all sections / 모든 섹션 결합
        html = f"""<!DOCTYPE html>
<html lang="{language}">
{head}
<body>
{header}

<div class="container-fluid py-4">
    {cards_section}

    {charts_section}

    {additional_sections if additional_sections else ''}
</div>

{modal}

{footer}

{self._build_scripts(charts, language)}

</body>
</html>"""

        self.logger.info(
            "대시보드 HTML 빌드 완료",
            "Dashboard HTML build completed"
        )

        return html

    def _build_head(self, title: str) -> str:
        """
        Build HTML head section with CDN links
        CDN 링크가 있는 HTML head 섹션 구축

        Args:
            title: Page title / 페이지 제목

        Returns:
            HTML head section / HTML head 섹션
        """
        cdn_urls = self.chart_generator.get_cdn_urls()
        colors = self.config.get('colors', {})
        typography = self.config.get('typography', {})

        return f"""<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="HR Management Dashboard">
    <title>{title}</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">

    <!-- Chart.js -->
    <script src="{cdn_urls.get('chartjs', 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js')}"></script>
    <script src="{cdn_urls.get('chartjs_treemap', 'https://cdn.jsdelivr.net/npm/chartjs-chart-treemap@2.2.2/dist/chartjs-chart-treemap.min.js')}"></script>

    <style>
        :root {{
            --primary-color: {colors.get('primary', '#6366f1')};
            --primary-dark: {colors.get('primary_dark', '#4f46e5')};
            --primary-light: {colors.get('primary_light', '#818cf8')};
            --secondary-color: {colors.get('secondary', '#64748b')};
            --success-color: {colors.get('success', '#10b981')};
            --danger-color: {colors.get('danger', '#ef4444')};
            --warning-color: {colors.get('warning', '#f59e0b')};
            --info-color: {colors.get('info', '#3b82f6')};
            --background-color: {colors.get('background', '#f8fafc')};
            --background-secondary: {colors.get('background_secondary', '#ffffff')};
            --text-color: {colors.get('text', '#0f172a')};
            --text-secondary: {colors.get('text_secondary', '#64748b')};
            --border-color: {colors.get('border', '#e2e8f0')};
            --font-family: {typography.get('font_family', "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif")};
            --shadow-sm: {colors.get('shadow_sm', '0 1px 2px 0 rgba(0, 0, 0, 0.05)')};
            --shadow-md: {colors.get('shadow_md', '0 4px 6px -1px rgba(0, 0, 0, 0.1)')};
            --shadow-lg: {colors.get('shadow_lg', '0 10px 15px -3px rgba(0, 0, 0, 0.1)')};
            --shadow-xl: {colors.get('shadow_xl', '0 20px 25px -5px rgba(0, 0, 0, 0.1)')};
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: var(--font-family);
            color: var(--text-color);
            background-color: var(--background-color);
            line-height: 1.6;
        }}

        /* Modern Header with Gradient */
        .bg-primary {{
            background: {colors.get('gradient_primary', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')} !important;
            box-shadow: var(--shadow-lg);
        }}

        /* Enhanced Metric Cards */
        .metric-card {{
            position: relative;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: none;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            background: var(--background-secondary);
            cursor: pointer;
            box-shadow: var(--shadow-sm);
            overflow: hidden;
        }}

        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--primary-color);
            transition: width 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: var(--shadow-xl);
        }}

        .metric-card:hover::before {{
            width: 100%;
            opacity: 0.05;
        }}

        .metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin: 12px 0;
            background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .metric-label {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Enhanced Chart Containers */
        .chart-container {{
            position: relative;
            margin: 30px 0;
            padding: 32px;
            background: var(--background-secondary);
            border-radius: 20px;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}

        .chart-container:hover {{
            box-shadow: var(--shadow-lg);
        }}

        /* Modern Badges */
        .badge-threshold {{
            font-size: 0.75rem;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            letter-spacing: 0.025em;
        }}

        .badge.bg-success {{
            background: {colors.get('gradient_success', 'linear-gradient(135deg, #10b981 0%, #34d399 100%)')} !important;
        }}

        .badge.bg-danger {{
            background: {colors.get('gradient_danger', 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)')} !important;
        }}

        .badge.bg-warning {{
            background: {colors.get('gradient_warning', 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)')} !important;
        }}

        .badge.bg-info {{
            background: {colors.get('gradient_info', 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)')} !important;
        }}

        /* Language Selector */
        .language-selector {{
            position: fixed;
            top: 24px;
            right: 24px;
            z-index: 1050;
        }}

        .language-selector select {{
            border-radius: 12px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            color: white;
            font-weight: 600;
            padding: 8px 16px;
            box-shadow: var(--shadow-md);
        }}

        .language-selector select:focus {{
            border-color: white;
            box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
        }}

        /* Trend Indicators */
        .trend-indicator {{
            display: inline-flex;
            align-items: center;
            margin-left: 8px;
            font-weight: 600;
        }}

        .trend-up {{ color: var(--success-color); }}
        .trend-down {{ color: var(--danger-color); }}
        .trend-stable {{ color: var(--info-color); }}

        /* Modal Styles */
        .modal-content {{
            border-radius: 20px;
            border: none;
            box-shadow: var(--shadow-xl);
        }}

        .modal-header {{
            background: {colors.get('gradient_primary', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')};
            color: white;
            border-radius: 20px 20px 0 0;
            padding: 24px;
            border: none;
        }}

        .modal-title {{
            font-weight: 700;
            font-size: 1.5rem;
        }}

        .modal-body {{
            padding: 32px;
        }}

        .modal-footer {{
            border-top: 1px solid var(--border-color);
            padding: 20px 32px;
        }}

        .btn-close {{
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 50%;
            opacity: 1;
        }}

        /* Section Headers */
        h2 {{
            font-weight: 700;
            font-size: 2rem;
            color: var(--text-color);
            margin-bottom: 32px;
            position: relative;
            padding-bottom: 16px;
        }}

        h2::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 60px;
            height: 4px;
            background: {colors.get('gradient_primary', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')};
            border-radius: 2px;
        }}

        /* Responsive Design */
        @media (max-width: 768px) {{
            .metric-card {{
                margin-bottom: 16px;
                padding: 20px;
            }}

            .metric-value {{
                font-size: 2rem;
            }}

            .chart-container {{
                margin: 20px 0;
                padding: 20px;
            }}

            h2 {{
                font-size: 1.5rem;
            }}

            .language-selector {{
                top: 16px;
                right: 16px;
            }}
        }}

        /* Print Styles */
        @media print {{
            .language-selector {{
                display: none;
            }}

            .metric-card {{
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid var(--border-color);
            }}

            .chart-container {{
                break-inside: avoid;
                box-shadow: none;
            }}
        }}

        /* Animation */
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .metric-card, .chart-container {{
            animation: fadeIn 0.5s ease-out;
        }}

        /* Detail Table Styles */
        .detail-table {{
            width: 100%;
            font-size: 0.9rem;
        }}

        .detail-table th {{
            background-color: var(--background-color);
            color: var(--text-color);
            font-weight: 600;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid var(--border-color);
        }}

        .detail-table td {{
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
        }}

        .detail-table tbody tr:hover {{
            background-color: var(--background-color);
        }}

        /* Stat Grid in Modal */
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .stat-item {{
            padding: 16px;
            background-color: var(--background-color);
            border-radius: 12px;
            border-left: 4px solid var(--primary-color);
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }}

        .stat-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-color);
        }}
    </style>
</head>"""

    def _build_header(self, title: str, language: str) -> str:
        """
        Build dashboard header
        대시보드 헤더 구축

        Args:
            title: Dashboard title / 대시보드 제목
            language: Current language / 현재 언어

        Returns:
            HTML header section / HTML 헤더 섹션
        """
        return f"""<header class="bg-primary text-white py-4 mb-4">
    <div class="container-fluid">
        <div class="row align-items-center">
            <div class="col-md-8">
                <h1 class="mb-0">
                    <i class="bi bi-clipboard-data me-2"></i>
                    {title}
                </h1>
                <p class="mb-0 mt-2 opacity-75">
                    {self._get_translation('subtitle', language)}
                </p>
            </div>
            <div class="col-md-4 text-end">
                <div class="language-selector">
                    <select id="languageSelect" class="form-select" onchange="changeLanguage(this.value)">
                        <option value="ko" {'selected' if language == 'ko' else ''}>한국어</option>
                        <option value="en" {'selected' if language == 'en' else ''}>English</option>
                        <option value="vi" {'selected' if language == 'vi' else ''}>Tiếng Việt</option>
                    </select>
                </div>
            </div>
        </div>
    </div>
</header>"""

    def _build_cards_section(
        self,
        cards: List[Dict[str, Any]],
        language: str
    ) -> str:
        """
        Build metrics cards section
        메트릭 카드 섹션 구축

        Args:
            cards: List of card data / 카드 데이터 목록
            language: Current language / 현재 언어

        Returns:
            HTML cards section / HTML 카드 섹션
        """
        cards_per_row = self.config.get('cards', {}).get('cards_per_row', 3)

        cards_html = '<div class="row g-4">\n'

        for card in cards:
            col_class = f"col-md-{12 // cards_per_row}"
            card_html = self._build_single_card(card, language)
            cards_html += f'    <div class="{col_class}">\n{card_html}\n    </div>\n'

        cards_html += '</div>'

        return f"""<section class="metrics-section mb-5">
    <h2 class="mb-4">{self._get_translation('sections.hr_metrics.title', language)}</h2>
    {cards_html}
</section>"""

    def _build_single_card(
        self,
        card: Dict[str, Any],
        language: str
    ) -> str:
        """
        Build a single metric card
        단일 메트릭 카드 구축

        Args:
            card: Card data / 카드 데이터
            language: Current language / 현재 언어

        Returns:
            HTML card / HTML 카드
        """
        metric_id = card.get('metric_id', '')
        value = card.get('value', 0)
        display_value = card.get('display_value', str(value))
        threshold_level = card.get('threshold_level', '')
        color = card.get('color', '')

        # Get label from translations / 번역에서 라벨 가져오기
        label = self._get_translation(f'cards.{metric_id}', language)

        # Determine badge color / 배지 색상 결정
        badge_class = {
            'excellent': 'bg-success',
            'good': 'bg-info',
            'warning': 'bg-warning',
            'critical': 'bg-danger'
        }.get(threshold_level, 'bg-secondary')

        return f"""        <div class="metric-card" onclick="showDetails('{metric_id}')">
            <div class="d-flex justify-content-between align-items-start">
                <div class="metric-label">{label}</div>
                {f'<span class="badge badge-threshold {badge_class}">{threshold_level}</span>' if threshold_level else ''}
            </div>
            <div class="metric-value" style="{f'color: {color};' if color else ''}">
                {display_value}
            </div>
            <div class="metric-metadata">
                {self._build_card_metadata(card, language)}
            </div>
        </div>"""

    def _build_card_metadata(
        self,
        card: Dict[str, Any],
        language: str
    ) -> str:
        """
        Build card metadata section (trend indicators, comparisons, etc.)
        카드 메타데이터 섹션 구축 (추세 표시기, 비교 등)

        Args:
            card: Card data / 카드 데이터
            language: Current language / 현재 언어

        Returns:
            HTML metadata section / HTML 메타데이터 섹션
        """
        metadata = card.get('metadata', {})
        html_parts = []

        # Add trend indicator if available / 사용 가능한 경우 추세 표시기 추가
        trend = metadata.get('trend_direction')
        if trend:
            trend_icons = {
                'increasing': '<i class="bi bi-arrow-up trend-up"></i>',
                'decreasing': '<i class="bi bi-arrow-down trend-down"></i>',
                'stable': '<i class="bi bi-dash trend-stable"></i>'
            }
            html_parts.append(f'<span class="trend-indicator">{trend_icons.get(trend, "")}</span>')

        # Add comparison with previous period / 이전 기간과 비교 추가
        prev_comparison = metadata.get('previous_period_change')
        if prev_comparison:
            html_parts.append(f'<small class="text-muted ms-2">{prev_comparison}%</small>')

        return ' '.join(html_parts)

    def _build_charts_section(self, charts: List[ChartConfig]) -> str:
        """
        Build charts section with canvas elements
        캔버스 요소가 있는 차트 섹션 구축

        Args:
            charts: List of chart configurations / 차트 설정 목록

        Returns:
            HTML charts section / HTML 차트 섹션
        """
        if not charts:
            return ''

        charts_html = '<div class="row">\n'

        for idx, chart in enumerate(charts):
            canvas_id = f"chart_{idx}"
            chart_title = chart.metadata.get('title', f'Chart {idx + 1}')

            charts_html += f"""    <div class="col-12 mb-4">
        <div class="chart-container">
            <h3>{chart_title}</h3>
            <canvas id="{canvas_id}"></canvas>
        </div>
    </div>\n"""

        charts_html += '</div>'

        return f"""<section class="charts-section mb-5">
    <h2 class="mb-4">Analysis Charts</h2>
    {charts_html}
</section>"""

    def _build_footer(self) -> str:
        """
        Build dashboard footer
        대시보드 푸터 구축

        Returns:
            HTML footer / HTML 푸터
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""<footer class="bg-light text-center py-3 mt-5">
    <div class="container">
        <p class="mb-0 text-muted">
            Generated: {current_time} |
            HR Management Dashboard v1.0 |
            <span class="text-danger">NO FAKE DATA</span>
        </p>
    </div>
</footer>"""

    def _build_modal(self) -> str:
        """
        Build metric detail modal component
        메트릭 상세 정보 모달 컴포넌트 구축

        Returns:
            HTML modal structure / HTML 모달 구조
        """
        return """<!-- Metric Detail Modal -->
<!-- 메트릭 상세 정보 모달 -->
<div class="modal fade" id="metricDetailModal" tabindex="-1" aria-labelledby="metricDetailModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="metricDetailModalLabel">Metric Details</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div id="modalContent">
                <!-- Dynamic content will be injected here -->
                <!-- 동적 콘텐츠가 여기에 삽입됩니다 -->
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기 / Close</button>
            </div>
        </div>
    </div>
</div>"""

    def _build_scripts(
        self,
        charts: List[ChartConfig],
        language: str
    ) -> str:
        """
        Build JavaScript section with chart initialization
        차트 초기화가 있는 JavaScript 섹션 구축

        Args:
            charts: List of chart configurations / 차트 설정 목록
            language: Current language / 현재 언어

        Returns:
            HTML script section / HTML 스크립트 섹션
        """
        # Build chart initialization code / 차트 초기화 코드 구축
        chart_init_code = []

        for idx, chart in enumerate(charts):
            canvas_id = f"chart_{idx}"
            chart_json = self.chart_generator.to_json(chart)

            chart_init_code.append(f"""
    // Initialize Chart {idx}
    (function() {{
        const ctx = document.getElementById('{canvas_id}');
        if (!ctx) return;

        const chartConfig = {chart_json};

        // Destroy existing chart if any
        if (window.chart_{idx}_instance) {{
            window.chart_{idx}_instance.destroy();
        }}

        // Create new chart
        window.chart_{idx}_instance = new Chart(ctx.getContext('2d'), chartConfig);
    }})();""")

        charts_init = '\n'.join(chart_init_code)

        return f"""<!-- Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<script>
// Language switching function
function changeLanguage(lang) {{
    localStorage.setItem('hr_dashboard_language', lang);
    location.reload();
}}

// KPI Metric definitions with detailed information
// KPI 메트릭 정의 및 상세 정보
const metricDetails = {{
    'total_employees': {{
        title_ko: '전체 직원 상세 정보',
        title_en: 'Total Employees Details',
        title_vi: 'Chi tiết nhân viên',
        description_ko: '현재 재직 중인 전체 직원 수입니다.',
        description_en: 'Total number of currently employed staff.',
        description_vi: 'Tổng số nhân viên đang làm việc.',
        type: 'count'
    }},
    'absence_rate': {{
        title_ko: '결근율 상세 분석',
        title_en: 'Absence Rate Analysis',
        title_vi: 'Phân tích tỷ lệ vắng mặt',
        description_ko: '전체 근무일 대비 결근일 비율입니다.',
        description_en: 'Ratio of absent days to total working days.',
        description_vi: 'Tỷ lệ ngày vắng mặt so với tổng số ngày làm việc.',
        type: 'rate'
    }},
    'unauthorized_absence_rate': {{
        title_ko: '무단결근율 상세 분석',
        title_en: 'Unauthorized Absence Rate',
        title_vi: 'Tỷ lệ vắng mặt không phép',
        description_ko: '사전 승인 없이 결근한 비율입니다.',
        description_en: 'Rate of absences without prior approval.',
        description_vi: 'Tỷ lệ vắng mặt không được phép trước.',
        type: 'rate'
    }},
    'resignation_rate': {{
        title_ko: '퇴사율 상세 분석',
        title_en: 'Resignation Rate Analysis',
        title_vi: 'Phân tích tỷ lệ nghỉ việc',
        description_ko: '전체 직원 대비 퇴사자 비율입니다.',
        description_en: 'Ratio of resigned employees to total employees.',
        description_vi: 'Tỷ lệ nhân viên nghỉ việc so với tổng số.',
        type: 'rate'
    }},
    'recent_hires': {{
        title_ko: '신규 입사자 상세 정보',
        title_en: 'Recent Hires Details',
        title_vi: 'Chi tiết nhân viên mới',
        description_ko: '최근 입사한 직원 수입니다.',
        description_en: 'Number of recently hired employees.',
        description_vi: 'Số lượng nhân viên mới tuyển dụng.',
        type: 'count'
    }},
    'recent_resignations': {{
        title_ko: '최근 퇴사자 상세 정보',
        title_en: 'Recent Resignations Details',
        title_vi: 'Chi tiết nhân viên nghỉ việc',
        description_ko: '최근 퇴사한 직원 수입니다.',
        description_en: 'Number of recently resigned employees.',
        description_vi: 'Số lượng nhân viên nghỉ việc gần đây.',
        type: 'count'
    }},
    'under_60_days': {{
        title_ko: '재직 60일 미만 직원',
        title_en: 'Employees Under 60 Days',
        title_vi: 'Nhân viên dưới 60 ngày',
        description_ko: '입사 후 60일 미만 재직 직원 수입니다.',
        description_en: 'Number of employees with less than 60 days tenure.',
        description_vi: 'Số nhân viên làm việc dưới 60 ngày.',
        type: 'count'
    }},
    'post_assignment_resignations': {{
        title_ko: '배정 후 퇴사자',
        title_en: 'Post-Assignment Resignations',
        title_vi: 'Nghỉ việc sau phân công',
        description_ko: '업무 배정 후 퇴사한 직원 수입니다.',
        description_en: 'Employees who resigned after job assignment.',
        description_vi: 'Nhân viên nghỉ sau khi phân công công việc.',
        type: 'count'
    }},
    'full_attendance': {{
        title_ko: '개근 직원',
        title_en: 'Perfect Attendance',
        title_vi: 'Chuyên cần hoàn hảo',
        description_ko: '결근 없이 완벽하게 출근한 직원 수입니다.',
        description_en: 'Employees with perfect attendance.',
        description_vi: 'Nhân viên có chuyên cần hoàn hảo.',
        type: 'count'
    }},
    'long_term_employees': {{
        title_ko: '장기 근속 직원',
        title_en: 'Long-term Employees',
        title_vi: 'Nhân viên lâu năm',
        description_ko: '장기간 재직 중인 직원 수입니다.',
        description_en: 'Employees with long tenure.',
        description_vi: 'Nhân viên có thâm niên lâu năm.',
        type: 'count'
    }},
    'data_errors': {{
        title_ko: '데이터 오류',
        title_en: 'Data Errors',
        title_vi: 'Lỗi dữ liệu',
        description_ko: '감지된 데이터 품질 문제입니다.',
        description_en: 'Detected data quality issues.',
        description_vi: 'Các vấn đề chất lượng dữ liệu phát hiện.',
        type: 'error'
    }}
}};

// Card details function with modal display
// 카드 상세 정보 함수 (모달 표시)
function showDetails(metricId) {{
    const metric = metricDetails[metricId];
    if (!metric) {{
        console.error('Metric not found:', metricId);
        return;
    }}

    const currentLang = localStorage.getItem('hr_dashboard_language') || 'ko';
    const title = metric[`title_${{currentLang}}`] || metric.title_ko;
    const description = metric[`description_${{currentLang}}`] || metric.description_ko;

    // Get metric card data from DOM
    const cardElement = event.target.closest('.metric-card');
    const valueElement = cardElement.querySelector('.metric-value');
    const currentValue = valueElement ? valueElement.textContent.trim() : 'N/A';

    // Build modal content based on metric type
    let modalContent = '';

    if (metric.type === 'count') {{
        modalContent = `
            <div class="modal-body">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> ${{description}}
                </div>
                <div class="stat-grid mb-4">
                    <div class="stat-item">
                        <div class="stat-label">현재 값 / Current Value</div>
                        <div class="stat-value text-primary">${{currentValue}}</div>
                    </div>
                </div>
                <div class="alert alert-warning">
                    <strong>📊 NO FAKE DATA Policy</strong><br>
                    실제 데이터만 표시합니다. 상세 분석은 원본 데이터를 참조하세요.<br>
                    Only real data is displayed. Refer to source data for detailed analysis.
                </div>
            </div>
        `;
    }} else if (metric.type === 'rate') {{
        modalContent = `
            <div class="modal-body">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> ${{description}}
                </div>
                <div class="stat-grid mb-4">
                    <div class="stat-item">
                        <div class="stat-label">현재 비율 / Current Rate</div>
                        <div class="stat-value text-primary">${{currentValue}}</div>
                    </div>
                </div>
                <div class="alert alert-warning">
                    <strong>📊 NO FAKE DATA Policy</strong><br>
                    실제 데이터만 표시합니다. 상세 분석은 원본 데이터를 참조하세요.<br>
                    Only real data is displayed. Refer to source data for detailed analysis.
                </div>
            </div>
        `;
    }} else if (metric.type === 'error') {{
        modalContent = `
            <div class="modal-body">
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> ${{description}}
                </div>
                <div class="stat-grid mb-4">
                    <div class="stat-item">
                        <div class="stat-label">감지된 오류 / Detected Errors</div>
                        <div class="stat-value text-danger">${{currentValue}}</div>
                    </div>
                </div>
                <div class="alert alert-info">
                    <strong>🔍 데이터 품질 점검 / Data Quality Check</strong><br>
                    데이터 오류는 6가지 카테고리로 분류됩니다:<br>
                    시간적 오류, 유형 오류, 직급 오류, 팀 오류, 출근 오류, 중복 오류<br>
                    <br>
                    Errors are categorized into 6 types:<br>
                    Temporal, Type, Position, Team, Attendance, Duplicate
                </div>
            </div>
        `;
    }}

    // Set modal content
    const modalElement = document.getElementById('metricDetailModal');
    if (modalElement) {{
        modalElement.querySelector('.modal-title').textContent = title;
        modalElement.querySelector('#modalContent').innerHTML = modalContent;

        // Show modal
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }}
}}

// Initialize charts
document.addEventListener('DOMContentLoaded', function() {{
    {charts_init}
}});

// Handle window resize
window.addEventListener('resize', function() {{
    // Charts automatically handle resize with responsive: true
}});
</script>"""

    def _get_translation(self, key: str, language: str) -> str:
        """
        Get translation for a key
        키에 대한 번역 가져오기

        Args:
            key: Translation key / 번역 키
            language: Language code / 언어 코드

        Returns:
            Translated string / 번역된 문자열
        """
        if self.i18n:
            return self.i18n.t(key, language)
        return key

    def save_to_file(self, html: str, output_path: str) -> bool:
        """
        Save HTML to file
        HTML을 파일로 저장

        Args:
            html: HTML content / HTML 내용
            output_path: Output file path / 출력 파일 경로

        Returns:
            True if successful / 성공 시 True
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            self.logger.info(
                "HTML 파일 저장 완료",
                "HTML file saved successfully",
                path=str(output_file)
            )
            return True

        except Exception as e:
            self.logger.error(
                "HTML 파일 저장 실패",
                "Failed to save HTML file",
                path=output_path,
                error=str(e)
            )
            return False
