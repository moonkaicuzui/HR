"""
chart_generator.py - Generic Chart Generation Engine
범용 차트 생성 엔진

CORE REUSABILITY PRINCIPLE / 핵심 재사용성 원칙:
This module generates Chart.js configurations based on chart_templates.json.
The same template works for ANY subject/metric combination:
- line_trend template can be used for:
  * Overall absence rate trend
  * Team A attendance rate trend
  * Unauthorized absence trend
  * ANY percentage metric trend

동일한 템플릿이 모든 주체/메트릭 조합에 작동합니다.

Core Features / 핵심 기능:
- Template-based chart generation / 템플릿 기반 차트 생성
- Subject/metric-agnostic design / 주체/메트릭 독립적 설계
- Automatic color assignment / 자동 색상 할당
- Responsive design / 반응형 디자인
- Multi-language label support / 다국어 라벨 지원
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

from ..utils.logger import get_logger
from ..utils.i18n import I18n
from ..analytics.trend_analyzer import TrendAnalysisResult
from ..analytics.metric_calculator import MetricCalculationResult


@dataclass
class ChartData:
    """
    Chart data structure
    차트 데이터 구조
    """
    labels: List[str]  # X-axis labels / X축 라벨
    datasets: List[Dict[str, Any]]  # Chart.js datasets / Chart.js 데이터셋
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartConfig:
    """
    Complete Chart.js configuration
    완전한 Chart.js 설정
    """
    chart_type: str  # "line", "bar", "treemap", etc. / 차트 유형
    data: ChartData
    options: Dict[str, Any]
    plugins: List[str] = field(default_factory=list)  # Required CDN plugins / 필요한 CDN 플러그인
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChartGenerator:
    """
    Generic chart generator driven by templates
    템플릿에 의해 구동되는 범용 차트 생성기

    REUSABILITY DESIGN / 재사용성 설계:
    This class loads chart templates from chart_templates.json
    and generates Chart.js configurations for ANY subject/metric combination.
    No code changes needed for new charts - only template selection.

    이 클래스는 chart_templates.json에서 차트 템플릿을 로드하고
    모든 주체/메트릭 조합에 대한 Chart.js 설정을 생성합니다.
    새 차트에 코드 변경 불필요 - 템플릿 선택만 필요합니다.
    """

    def __init__(
        self,
        template_config_path: Optional[str] = None,
        dashboard_config_path: Optional[str] = None,
        i18n: Optional[I18n] = None
    ):
        """
        Initialize ChartGenerator
        ChartGenerator 초기화

        Args:
            template_config_path: Path to chart_templates.json / chart_templates.json 경로
            dashboard_config_path: Path to dashboard_config.json / dashboard_config.json 경로
            i18n: I18n instance for translations / 번역을 위한 I18n 인스턴스
        """
        self.logger = get_logger()
        self.i18n = i18n

        # Load chart templates / 차트 템플릿 로드
        if template_config_path is None:
            hr_root = Path(__file__).parent.parent.parent
            template_config_path = hr_root / "config" / "chart_templates.json"

        self.template_config_path = Path(template_config_path)
        self.templates = self._load_chart_templates()

        # Load dashboard config for colors / 색상을 위해 대시보드 설정 로드
        if dashboard_config_path is None:
            hr_root = Path(__file__).parent.parent.parent
            dashboard_config_path = hr_root / "config" / "dashboard_config.json"

        self.dashboard_config_path = Path(dashboard_config_path)
        self.dashboard_config = self._load_dashboard_config()

    def _load_chart_templates(self) -> Dict[str, Any]:
        """
        Load chart templates from JSON configuration
        JSON 설정에서 차트 템플릿 로드

        Returns:
            Dictionary of chart templates / 차트 템플릿 딕셔너리
        """
        try:
            with open(self.template_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('templates', {})
        except FileNotFoundError:
            self.logger.error(
                "차트 템플릿 파일을 찾을 수 없습니다",
                "Chart templates file not found",
                path=str(self.template_config_path)
            )
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(
                "차트 템플릿 JSON 파싱 실패",
                "Failed to parse chart templates JSON",
                error=str(e)
            )
            return {}

    def _load_dashboard_config(self) -> Dict[str, Any]:
        """
        Load dashboard configuration
        대시보드 설정 로드

        Returns:
            Dashboard configuration dictionary / 대시보드 설정 딕셔너리
        """
        try:
            with open(self.dashboard_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(
                "대시보드 설정 로드 실패, 기본값 사용",
                "Failed to load dashboard config, using defaults",
                error=str(e)
            )
            return {}

    def generate_chart(
        self,
        chart_data: 'ChartData',
        template_name: str = 'bar',
        title: Optional[str] = None
    ) -> 'ChartConfig':
        """
        Generate a simple chart from data
        데이터로부터 간단한 차트 생성

        Args:
            chart_data: ChartData with labels and datasets / 레이블과 데이터셋이 있는 ChartData
            template_name: Template to use / 사용할 템플릿
            title: Chart title / 차트 제목

        Returns:
            ChartConfig object / ChartConfig 객체
        """
        # Simple chart configuration
        # 간단한 차트 설정
        return ChartConfig(
            chart_type=template_name,
            data=chart_data,
            options={'responsive': True, 'plugins': {'title': {'display': bool(title), 'text': title or ''}}},
            plugins=[],
            metadata={'title': title or ''}
        )

    def generate_trend_chart(
        self,
        trend_result: TrendAnalysisResult,
        template_name: str = "line_trend",
        title: Optional[str] = None,
        language: str = "ko"
    ) -> ChartConfig:
        """
        Generate chart configuration from trend analysis result
        추세 분석 결과에서 차트 설정 생성

        REUSABILITY EXAMPLE / 재사용성 예시:
        >>> generator = ChartGenerator()
        >>>
        >>> # Generate chart for overall absence rate trend
        >>> # 전체 결근율 추세 차트 생성
        >>> chart1 = generator.generate_trend_chart(
        ...     trend_result=overall_absence_trend,
        ...     template_name="line_trend",
        ...     title="Overall Absence Rate Trend"
        ... )
        >>>
        >>> # Generate chart for Team A attendance trend using SAME function
        >>> # 동일한 함수로 팀 A 출근 추세 차트 생성
        >>> chart2 = generator.generate_trend_chart(
        ...     trend_result=team_a_attendance_trend,
        ...     template_name="line_trend",
        ...     title="Team A Attendance Trend"
        ... )

        Args:
            trend_result: TrendAnalysisResult from TrendAnalyzer
                         TrendAnalyzer의 TrendAnalysisResult
            template_name: Template name from chart_templates.json
                          chart_templates.json의 템플릿 이름
            title: Chart title (auto-generated if None) / 차트 제목 (None이면 자동 생성)
            language: Language for labels / 라벨 언어

        Returns:
            ChartConfig ready for Chart.js / Chart.js용 ChartConfig
        """
        # Get template / 템플릿 가져오기
        template = self.templates.get(template_name)
        if not template:
            self.logger.error(
                "차트 템플릿을 찾을 수 없습니다",
                "Chart template not found",
                template=template_name
            )
            return self._get_empty_chart_config()

        # Extract data from trend result / 추세 결과에서 데이터 추출
        labels = [point.label for point in trend_result.data_points]
        values = [point.value for point in trend_result.data_points]

        # Generate title if not provided / 제공되지 않은 경우 제목 생성
        if title is None:
            if self.i18n:
                subject_label = trend_result.subject
                metric_label = self.i18n.t(f"cards.{trend_result.metric}", language)
                title = f"{subject_label} - {metric_label}"
            else:
                title = f"{trend_result.subject} - {trend_result.metric}"

        # Create dataset / 데이터셋 생성
        dataset = self._create_dataset(
            label=title,
            data=values,
            template=template,
            dataset_index=0
        )

        # Build chart data / 차트 데이터 구성
        chart_data = ChartData(
            labels=labels,
            datasets=[dataset],
            metadata={
                'subject': trend_result.subject,
                'metric': trend_result.metric,
                'period': trend_result.period,
                'trend_direction': trend_result.trend_direction
            }
        )

        # Build chart options / 차트 옵션 구성
        options = self._build_chart_options(template, title)

        return ChartConfig(
            chart_type=template['type'],
            data=chart_data,
            options=options,
            plugins=self._get_required_plugins(template['type']),
            metadata={
                'template_name': template_name,
                'subject': trend_result.subject,
                'metric': trend_result.metric
            }
        )

    def generate_comparison_chart(
        self,
        labels: List[str],
        datasets: List[Dict[str, Any]],
        template_name: str = "bar_comparison",
        title: Optional[str] = None,
        language: str = "ko"
    ) -> ChartConfig:
        """
        Generate comparison chart (e.g., team comparison)
        비교 차트 생성 (예: 팀 비교)

        Args:
            labels: X-axis labels (e.g., team names) / X축 라벨 (예: 팀 이름)
            datasets: List of datasets to compare / 비교할 데이터셋 목록
            template_name: Template name / 템플릿 이름
            title: Chart title / 차트 제목
            language: Language for labels / 라벨 언어

        Returns:
            ChartConfig ready for Chart.js / Chart.js용 ChartConfig
        """
        template = self.templates.get(template_name)
        if not template:
            return self._get_empty_chart_config()

        # Process datasets with template styling / 템플릿 스타일로 데이터셋 처리
        styled_datasets = []
        for idx, dataset in enumerate(datasets):
            styled_dataset = self._create_dataset(
                label=dataset.get('label', f'Dataset {idx + 1}'),
                data=dataset.get('data', []),
                template=template,
                dataset_index=idx
            )
            styled_datasets.append(styled_dataset)

        chart_data = ChartData(
            labels=labels,
            datasets=styled_datasets
        )

        options = self._build_chart_options(template, title or "Comparison Chart")

        return ChartConfig(
            chart_type=template['type'],
            data=chart_data,
            options=options,
            plugins=self._get_required_plugins(template['type']),
            metadata={'template_name': template_name}
        )

    def generate_treemap_chart(
        self,
        data: List[Dict[str, Any]],
        title: Optional[str] = None,
        language: str = "ko"
    ) -> ChartConfig:
        """
        Generate treemap chart for hierarchical data
        계층적 데이터를 위한 트리맵 차트 생성

        Args:
            data: List of items with 'label' and 'value' keys
                 'label'과 'value' 키가 있는 항목 목록
            title: Chart title / 차트 제목
            language: Language for labels / 라벨 언어

        Returns:
            ChartConfig for treemap / 트리맵용 ChartConfig
        """
        template = self.templates.get('treemap')
        if not template:
            return self._get_empty_chart_config()

        # Format data for treemap / 트리맵용 데이터 포맷
        treemap_data = []
        colors = self._get_color_palette()

        for idx, item in enumerate(data):
            treemap_data.append({
                'label': item.get('label', ''),
                'value': item.get('value', 0),
                'backgroundColor': colors[idx % len(colors)]
            })

        chart_data = ChartData(
            labels=[],  # Treemap doesn't use labels array / 트리맵은 라벨 배열 사용 안 함
            datasets=[{
                'tree': treemap_data,
                'key': 'value',
                'groups': ['label'],
                'spacing': 1,
                'borderWidth': 2,
                'borderColor': 'white'
            }]
        )

        options = self._build_chart_options(template, title or "Distribution")

        return ChartConfig(
            chart_type='treemap',
            data=chart_data,
            options=options,
            plugins=['chartjs-chart-treemap'],
            metadata={'template_name': 'treemap'}
        )

    def _create_dataset(
        self,
        label: str,
        data: List[float],
        template: Dict[str, Any],
        dataset_index: int = 0
    ) -> Dict[str, Any]:
        """
        Create a Chart.js dataset with template styling
        템플릿 스타일로 Chart.js 데이터셋 생성

        Args:
            label: Dataset label / 데이터셋 라벨
            data: Data values / 데이터 값
            template: Chart template / 차트 템플릿
            dataset_index: Index for color selection / 색상 선택을 위한 인덱스

        Returns:
            Styled dataset dictionary / 스타일이 적용된 데이터셋 딕셔너리
        """
        dataset = {
            'label': label,
            'data': data
        }

        # Apply template colors / 템플릿 색상 적용
        colors = template.get('colors', {})

        if isinstance(colors, dict):
            # Single color configuration / 단일 색상 설정
            if 'line' in colors:
                dataset['borderColor'] = colors['line']
                dataset['backgroundColor'] = colors.get('background', colors['line'])
                dataset['borderWidth'] = colors.get('border_width', 2)
                dataset['pointRadius'] = colors.get('point_radius', 4)
                dataset['pointHoverRadius'] = colors.get('point_hover_radius', 6)
            elif 'default' in colors:
                dataset['backgroundColor'] = colors['default']
                dataset['hoverBackgroundColor'] = colors.get('hover', colors['default'])
        elif isinstance(colors, list):
            # Multiple colors (use index) / 여러 색상 (인덱스 사용)
            color = colors[dataset_index % len(colors)]
            dataset['backgroundColor'] = color
            dataset['borderColor'] = color

        return dataset

    def _build_chart_options(
        self,
        template: Dict[str, Any],
        title: str
    ) -> Dict[str, Any]:
        """
        Build Chart.js options from template
        템플릿에서 Chart.js 옵션 구성

        Args:
            template: Chart template / 차트 템플릿
            title: Chart title / 차트 제목

        Returns:
            Chart.js options object / Chart.js 옵션 객체
        """
        # Start with template config / 템플릿 설정으로 시작
        options = template.get('config', {}).copy()

        # Add title / 제목 추가
        if 'plugins' not in options:
            options['plugins'] = {}

        if 'title' not in options['plugins']:
            options['plugins']['title'] = {
                'display': True,
                'text': title,
                'font': {
                    'size': 16,
                    'weight': 'bold'
                }
            }

        return options

    def _get_color_palette(self) -> List[str]:
        """
        Get color palette from dashboard configuration
        대시보드 설정에서 색상 팔레트 가져오기

        Returns:
            List of color codes / 색상 코드 목록
        """
        colors = self.dashboard_config.get('colors', {}).get('chart_colors', [])

        if not colors:
            # Default colors if config not available / 설정을 사용할 수 없는 경우 기본 색상
            colors = [
                "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2"
            ]

        return colors

    def _get_required_plugins(self, chart_type: str) -> List[str]:
        """
        Get list of required CDN plugins for chart type
        차트 유형에 필요한 CDN 플러그인 목록 가져오기

        Args:
            chart_type: Type of chart / 차트 유형

        Returns:
            List of plugin names / 플러그인 이름 목록
        """
        plugins = ['chart.js']  # Base library always required / 기본 라이브러리 항상 필요

        if chart_type == 'treemap':
            plugins.append('chartjs-chart-treemap')

        return plugins

    def _get_empty_chart_config(self) -> ChartConfig:
        """
        Get empty chart configuration for error cases
        에러 경우를 위한 빈 차트 설정

        Returns:
            Empty ChartConfig / 빈 ChartConfig
        """
        return ChartConfig(
            chart_type='line',
            data=ChartData(labels=[], datasets=[]),
            options={},
            metadata={'error': 'Template not found'}
        )

    def to_json(self, chart_config: ChartConfig) -> str:
        """
        Convert ChartConfig to JSON string for embedding in HTML
        HTML에 포함하기 위해 ChartConfig를 JSON 문자열로 변환

        Args:
            chart_config: Chart configuration / 차트 설정

        Returns:
            JSON string / JSON 문자열
        """
        chart_dict = {
            'type': chart_config.chart_type,
            'data': {
                'labels': chart_config.data.labels,
                'datasets': chart_config.data.datasets
            },
            'options': chart_config.options
        }

        return json.dumps(chart_dict, ensure_ascii=False, indent=2)

    def generate_chart_html(
        self,
        chart_config: ChartConfig,
        canvas_id: str = "myChart",
        width: int = 800,
        height: int = 400
    ) -> str:
        """
        Generate complete HTML for chart including canvas and script
        캔버스와 스크립트를 포함한 차트용 완전한 HTML 생성

        Args:
            chart_config: Chart configuration / 차트 설정
            canvas_id: HTML canvas element ID / HTML 캔버스 요소 ID
            width: Canvas width / 캔버스 너비
            height: Canvas height / 캔버스 높이

        Returns:
            HTML string / HTML 문자열
        """
        chart_json = self.to_json(chart_config)

        html = f"""
<div class="chart-container" style="position: relative; height:{height}px; width:{width}px;">
    <canvas id="{canvas_id}"></canvas>
</div>

<script>
(function() {{
    const ctx = document.getElementById('{canvas_id}').getContext('2d');
    const chartConfig = {chart_json};

    // Destroy existing chart if any / 기존 차트가 있으면 파괴
    if (window.{canvas_id}_instance) {{
        window.{canvas_id}_instance.destroy();
    }}

    // Create new chart / 새 차트 생성
    window.{canvas_id}_instance = new Chart(ctx, chartConfig);
}})();
</script>
"""

        return html

    def get_cdn_urls(self) -> Dict[str, str]:
        """
        Get CDN URLs for required Chart.js libraries
        필요한 Chart.js 라이브러리의 CDN URL 가져오기

        Returns:
            Dictionary mapping library names to CDN URLs
            라이브러리 이름을 CDN URL에 매핑하는 딕셔너리
        """
        try:
            with open(self.template_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('cdn_resources', {})
        except Exception:
            # Default CDN URLs / 기본 CDN URL
            return {
                'chartjs': 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js',
                'chartjs_treemap': 'https://cdn.jsdelivr.net/npm/chartjs-chart-treemap@2.2.2/dist/chartjs-chart-treemap.min.js'
            }
