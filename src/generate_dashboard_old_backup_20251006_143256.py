"""
HR Dashboard Generation Main Orchestrator
HR 대시보드 생성 메인 오케스트레이터

This module orchestrates the complete dashboard generation process:
이 모듈은 완전한 대시보드 생성 프로세스를 조율합니다:
- Data loading from files or Google Drive / 파일 또는 Google Drive에서 데이터 로딩
- Metric calculation using configuration / 설정을 사용한 메트릭 계산
- Trend analysis for all metrics / 모든 메트릭에 대한 트렌드 분석
- Chart generation from templates / 템플릿으로부터 차트 생성
- Error detection and validation / 에러 감지 및 검증
- HTML dashboard assembly / HTML 대시보드 조립

REUSABILITY PRINCIPLE / 재활용성 원칙:
The same orchestration flow works for ANY configuration of subjects, metrics, and charts.
동일한 조율 흐름이 어떤 주제, 메트릭, 차트 조합에서도 작동합니다.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse
import pandas as pd
import json

# Add parent directory to path for imports
# 부모 디렉토리를 import 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.i18n import I18n
from src.utils.date_parser import DateParser
from src.utils.logger import HRLogger
from src.integration.google_drive_sync import GoogleDriveSync
from src.core.data_loader import DataLoader
from src.core.data_validator import DataValidator
from src.core.error_detector import ErrorDetector
from src.analytics.trend_analyzer import TrendAnalyzer, TrendPoint
from src.analytics.metric_calculator import MetricCalculator, MetricValue
from src.visualization.chart_generator import ChartGenerator, ChartData
from src.visualization.html_builder import HTMLBuilder


class DashboardGenerator:
    """
    Main orchestrator for HR dashboard generation
    HR 대시보드 생성을 위한 메인 오케스트레이터

    This class coordinates all modules to generate a complete dashboard.
    이 클래스는 완전한 대시보드를 생성하기 위해 모든 모듈을 조율합니다.

    NO FAKE DATA policy enforced throughout the pipeline.
    전체 파이프라인에서 가짜 데이터 금지 정책이 적용됩니다.
    """

    def __init__(
        self,
        month: int,
        year: int,
        language: str = "ko",
        use_google_drive: bool = False,
        config_path: Optional[Path] = None
    ):
        """
        Initialize dashboard generator
        대시보드 생성기 초기화

        Args:
            month: Target month (1-12) / 대상 월 (1-12)
            year: Target year (e.g., 2025) / 대상 연도 (예: 2025)
            language: Default language (ko/en/vi) / 기본 언어 (ko/en/vi)
            use_google_drive: Enable Google Drive sync / Google Drive 동기화 활성화
            config_path: Path to dashboard_config.json / dashboard_config.json 경로
        """
        self.month = month
        self.year = year
        self.language = language
        self.use_google_drive = use_google_drive

        # Initialize base directory paths
        # 기본 디렉토리 경로 초기화
        self.hr_root = Path(__file__).parent.parent
        self.config_dir = self.hr_root / "config"
        self.input_dir = self.hr_root / "input_files"
        self.output_dir = self.hr_root / "output_files"

        # Ensure output directory exists
        # 출력 디렉토리가 존재하는지 확인
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize logger
        # 로거 초기화
        self.logger = HRLogger(
            name="DashboardGenerator",
            log_dir=self.hr_root / "logs"
        )

        self.logger.info(
            f"대시보드 생성기 초기화: {year}년 {month}월",
            f"Dashboard generator initialized: {year}-{month:02d}"
        )

        # Initialize core components
        # 핵심 컴포넌트 초기화
        self.i18n = I18n(self.config_dir / "translations.json", default_lang=language)
        self.date_parser = DateParser()

        # Initialize data loader (with optional Google Drive sync)
        # 데이터 로더 초기화 (선택적 Google Drive 동기화 포함)
        self.data_loader = DataLoader(
            data_root=str(self.input_dir),
            date_parser=self.date_parser
        )

        # Initialize Google Drive sync if enabled
        # Google Drive 동기화가 활성화된 경우 초기화
        self.drive_sync = None
        if self.use_google_drive:
            try:
                credentials_path = self.hr_root / "credentials" / "service-account-key.json"
                cache_dir = self.hr_root / ".cache" / "drive_sync"

                if credentials_path.exists():
                    self.drive_sync = GoogleDriveSync(
                        credentials_path=str(credentials_path),
                        cache_dir=str(cache_dir)
                    )
                    self.drive_sync.initialize()
                    self.logger.info(
                        "Google Drive 동기화 초기화 완료",
                        "Google Drive sync initialized successfully"
                    )
                else:
                    self.logger.warning(
                        f"인증 파일을 찾을 수 없습니다: {credentials_path}",
                        f"Credentials file not found: {credentials_path}"
                    )
                    self.use_google_drive = False
            except Exception as e:
                self.logger.warning(
                    f"Google Drive 동기화 초기화 실패: {str(e)}",
                    f"Google Drive sync initialization failed: {str(e)}"
                )
                self.use_google_drive = False

        # Initialize analytics engines (configuration-driven, NO HARDCODING)
        # 분석 엔진 초기화 (설정 기반, 하드코딩 없음)
        self.metric_calculator = MetricCalculator(
            metric_definitions_path=self.config_dir / "metric_definitions.json",
            logger=self.logger,
            date_parser=self.date_parser,
            i18n=self.i18n
        )

        self.trend_analyzer = TrendAnalyzer(
            date_parser=self.date_parser
        )

        # Initialize visualization components (template-driven, reusable)
        # 시각화 컴포넌트 초기화 (템플릿 기반, 재활용 가능)
        self.chart_generator = ChartGenerator(
            template_config_path=str(self.config_dir / "chart_templates.json"),
            i18n=self.i18n
        )

        self.html_builder = HTMLBuilder(
            dashboard_config_path=str(config_path or (self.config_dir / "dashboard_config.json")),
            i18n=self.i18n,
            chart_generator=self.chart_generator
        )

        # Data storage for loaded datasets
        # 로드된 데이터셋 저장소
        self.datasets: Dict[str, pd.DataFrame] = {}
        self.calculated_metrics: Dict[str, MetricValue] = {}
        self.trend_results: Dict[str, Any] = {}
        self.error_report: Dict[str, Any] = {}

    def _sync_from_google_drive(self):
        """
        Synchronize monthly data from Google Drive
        Google Drive에서 월별 데이터 동기화

        This method downloads the latest data files from Google Drive
        to the local input directory.
        이 메서드는 Google Drive에서 최신 데이터 파일을
        로컬 입력 디렉토리로 다운로드합니다.
        """
        self.logger.info(
            "Google Drive 동기화 시작",
            "Starting Google Drive sync"
        )

        try:
            # Load drive configuration
            # Drive 설정 로드
            drive_config_path = self.config_dir / "drive_config.json"

            if not drive_config_path.exists():
                self.logger.warning(
                    f"drive_config.json을 찾을 수 없습니다: {drive_config_path}",
                    f"drive_config.json not found: {drive_config_path}"
                )
                return

            with open(drive_config_path, 'r', encoding='utf-8') as f:
                drive_config = json.load(f)

            # Get monthly data folder ID from configuration
            # 설정에서 월별 데이터 폴더 ID 가져오기
            folder_id = drive_config.get('google_drive', {}).get(
                'folder_structure', {}
            ).get('monthly_data', {}).get('id')

            if not folder_id:
                self.logger.warning(
                    "drive_config.json에 monthly_data 폴더 ID가 없습니다",
                    "monthly_data folder ID not found in drive_config.json"
                )
                return

            # Perform synchronization
            # 동기화 수행
            result = self.drive_sync.sync_monthly_data(
                year=self.year,
                month=self.month,
                folder_id=folder_id,
                destination_dir=str(self.input_dir)
            )

            # Log sync results
            # 동기화 결과 로그
            self.logger.info(
                f"Google Drive 동기화 완료: {result.files_synced}개 파일 동기화됨",
                f"Google Drive sync complete: {result.files_synced} files synced"
            )

            if result.errors:
                for error in result.errors:
                    self.logger.warning(
                        f"동기화 오류: {error}",
                        f"Sync error: {error}"
                    )

        except Exception as e:
            self.logger.error(
                f"Google Drive 동기화 실패: {str(e)}",
                f"Google Drive sync failed: {str(e)}"
            )

    def load_all_data(self) -> bool:
        """
        Load all required data sources
        모든 필수 데이터 소스 로드

        Returns:
            bool: True if all data loaded successfully (or empty if not exists)
                  모든 데이터가 성공적으로 로드되었는지 (또는 존재하지 않으면 비어있음)

        NO FAKE DATA: Returns empty DataFrames if files don't exist
        가짜 데이터 없음: 파일이 존재하지 않으면 빈 DataFrame 반환
        """
        self.logger.info(
            "데이터 로딩 시작",
            "Starting data loading"
        )

        # Sync from Google Drive if enabled
        # Google Drive에서 동기화 (활성화된 경우)
        if self.use_google_drive and self.drive_sync is not None:
            self._sync_from_google_drive()

        try:
            # Load basic manpower data (core dataset)
            # 기본 인력 데이터 로드 (핵심 데이터셋)
            self.datasets['basic_manpower'] = self.data_loader.load_basic_manpower(
                self.month, self.year
            )

            # Load attendance data
            # 출근 데이터 로드
            self.datasets['attendance'] = self.data_loader.load_attendance(
                self.month, self.year
            )

            # Load AQL data (quality metrics)
            # AQL 데이터 로드 (품질 메트릭)
            self.datasets['aql'] = self.data_loader.load_aql_history(
                self.month, self.year
            )

            # Load 5PRS data (5-point rating system)
            # 5PRS 데이터 로드 (5점 평가 시스템)
            self.datasets['5prs'] = self.data_loader.load_5prs_data(
                self.month, self.year
            )

            # Load team structure (organizational hierarchy)
            # 팀 구조 로드 (조직 계층)
            # Note: team_structure loading not implemented yet
            # 주의: team_structure 로딩 아직 구현되지 않음
            self.datasets['team_structure'] = pd.DataFrame()

            # Log data loading results
            # 데이터 로딩 결과 로그
            for name, df in self.datasets.items():
                if df.empty:
                    self.logger.warning(
                        f"{name} 데이터가 비어있습니다 (파일 없음)",
                        f"{name} data is empty (file not found)"
                    )
                else:
                    self.logger.info(
                        f"{name} 로드 완료: {len(df)} 행",
                        f"{name} loaded: {len(df)} rows"
                    )

            return True

        except Exception as e:
            self.logger.error(
                f"데이터 로딩 실패: {str(e)}",
                f"Data loading failed: {str(e)}"
            )
            return False

    def validate_data(self) -> Dict[str, Any]:
        """
        Validate all loaded data and detect errors
        로드된 모든 데이터를 검증하고 오류 감지

        Returns:
            Dict containing error report / 오류 보고서를 포함하는 Dict
        """
        self.logger.info(
            "데이터 검증 시작",
            "Starting data validation"
        )

        # Initialize error detector
        # 오류 감지기 초기화
        error_detector = ErrorDetector(
            year=self.year,
            month=self.month,
            latest_data_date=datetime(self.year, self.month, 1)
        )

        # Detect all errors across datasets
        # 모든 데이터셋에서 오류 감지
        self.error_report = error_detector.detect_all_errors(
            basic_manpower=self.datasets.get('basic_manpower'),
            attendance=self.datasets.get('attendance'),
            team_structure=self.datasets.get('team_structure')
        )

        # Log error summary
        # 오류 요약 로그
        summary = self.error_report.get('summary', {})
        self.logger.info(
            f"검증 완료: 총 {summary.get('total_errors', 0)}개 오류 발견",
            f"Validation complete: {summary.get('total_errors', 0)} errors found"
        )

        return self.error_report

    def calculate_all_metrics(self) -> Dict[str, MetricValue]:
        """
        Calculate all configured metrics
        설정된 모든 메트릭 계산

        This method is REUSABLE - it works with ANY metric definitions in JSON.
        이 메서드는 재활용 가능 - JSON의 모든 메트릭 정의와 작동합니다.

        Returns:
            Dict mapping metric IDs to calculated MetricValue objects
            메트릭 ID를 계산된 MetricValue 객체로 매핑하는 Dict
        """
        self.logger.info(
            "메트릭 계산 시작",
            "Starting metric calculation"
        )

        # Get list of all available metrics from configuration
        # 설정에서 사용 가능한 모든 메트릭 목록 가져오기
        available_metrics = self.metric_calculator.get_available_metrics()

        for metric_id in available_metrics:
            try:
                # Calculate each metric using the reusable calculator
                # 재활용 가능한 계산기를 사용하여 각 메트릭 계산
                metric_value = self.metric_calculator.calculate_metric(
                    metric_id=metric_id,
                    data=self.datasets.get('basic_manpower', pd.DataFrame()),
                    subject="Overall"  # Can be overridden for team/position-specific metrics
                )

                self.calculated_metrics[metric_id] = metric_value

                self.logger.info(
                    f"메트릭 계산 완료: {metric_id} = {metric_value.value}",
                    f"Metric calculated: {metric_id} = {metric_value.value}"
                )

            except Exception as e:
                self.logger.error(
                    f"메트릭 계산 실패 ({metric_id}): {str(e)}",
                    f"Metric calculation failed ({metric_id}): {str(e)}"
                )

        return self.calculated_metrics

    def analyze_all_trends(self) -> Dict[str, Any]:
        """
        Analyze trends for all configured metrics
        설정된 모든 메트릭에 대한 트렌드 분석

        REUSABILITY: Same analysis logic works for ANY subject/metric combination.
        재활용성: 동일한 분석 로직이 모든 주제/메트릭 조합에서 작동합니다.

        Returns:
            Dict mapping metric IDs to trend analysis results
            메트릭 ID를 트렌드 분석 결과로 매핑하는 Dict
        """
        self.logger.info(
            "트렌드 분석 시작",
            "Starting trend analysis"
        )

        # Get metrics that have trend analysis enabled
        # 트렌드 분석이 활성화된 메트릭 가져오기
        trend_enabled_metrics = [
            m for m in self.metric_calculator.get_available_metrics()
            if self.metric_calculator.metric_definitions.get(m, {}).get('trend_enabled', False)
        ]

        for metric_id in trend_enabled_metrics:
            try:
                # For now, analyze overall trends
                # 현재는 전체 트렌드 분석
                # TODO: Add team-specific and position-specific trends

                # This would require historical data loading
                # 이는 과거 데이터 로딩이 필요합니다
                # For MVP, we'll store placeholder for future implementation
                # MVP의 경우 향후 구현을 위한 플레이스홀더를 저장합니다

                self.trend_results[metric_id] = {
                    'metric_id': metric_id,
                    'subject': 'Overall',
                    'status': 'placeholder',
                    'message': 'Historical data required for trend analysis'
                }

                self.logger.info(
                    f"트렌드 분석 준비: {metric_id}",
                    f"Trend analysis prepared: {metric_id}"
                )

            except Exception as e:
                self.logger.error(
                    f"트렌드 분석 실패 ({metric_id}): {str(e)}",
                    f"Trend analysis failed ({metric_id}): {str(e)}"
                )

        return self.trend_results

    def generate_all_charts(self) -> List[Any]:
        """
        Generate all charts from calculated metrics and trends
        계산된 메트릭과 트렌드로부터 모든 차트 생성

        REUSABILITY: Charts are generated from templates - works for ANY data.
        재활용성: 차트는 템플릿에서 생성 - 모든 데이터에서 작동합니다.

        Returns:
            List of ChartConfig objects / ChartConfig 객체 리스트
        """
        self.logger.info(
            "차트 생성 시작",
            "Starting chart generation"
        )

        charts = []

        # Generate metric summary charts (bar/pie charts for current values)
        # 메트릭 요약 차트 생성 (현재 값에 대한 막대/파이 차트)
        for metric_id, metric_value in self.calculated_metrics.items():
            try:
                # Generate a simple bar chart for the metric
                # 메트릭에 대한 간단한 막대 차트 생성
                chart_data = ChartData(
                    labels=[self.i18n.t(f'metrics.{metric_id}', self.language)],
                    datasets=[{
                        'label': self.i18n.t(f'metrics.{metric_id}', self.language),
                        'data': [metric_value.value],
                        'backgroundColor': [metric_value.color]
                    }]
                )

                chart_config = self.chart_generator.generate_chart(
                    chart_data=chart_data,
                    template_name='bar',
                    title=self.i18n.t(f'metrics.{metric_id}', self.language)
                )

                charts.append(chart_config)

            except Exception as e:
                self.logger.error(
                    f"차트 생성 실패 ({metric_id}): {str(e)}",
                    f"Chart generation failed ({metric_id}): {str(e)}"
                )

        self.logger.info(
            f"차트 생성 완료: {len(charts)}개",
            f"Chart generation complete: {len(charts)} charts"
        )

        return charts

    def build_dashboard_html(self, charts: List[Any]) -> str:
        """
        Build final HTML dashboard
        최종 HTML 대시보드 빌드

        Args:
            charts: List of ChartConfig objects / ChartConfig 객체 리스트

        Returns:
            Complete HTML string / 완전한 HTML 문자열
        """
        self.logger.info(
            "HTML 대시보드 빌드 시작",
            "Starting HTML dashboard build"
        )

        # Prepare summary cards from calculated metrics
        # 계산된 메트릭으로부터 요약 카드 준비
        cards = []
        for metric_id, metric_value in self.calculated_metrics.items():
            cards.append({
                'metric_id': metric_id,  # Required by _build_single_card / _build_single_card에 필요
                'title': self.i18n.t(f'metrics.{metric_id}', self.language),
                'value': metric_value.value,
                'display_value': metric_value.display_value,
                'unit': metric_value.unit,
                'color': metric_value.color,
                'threshold_level': metric_value.threshold_level,
                'metadata': metric_value.metadata
            })

        # Build complete HTML dashboard
        # 완전한 HTML 대시보드 빌드
        html = self.html_builder.build_dashboard(
            title=f"HR Dashboard - {self.year}/{self.month:02d}",
            cards=cards,
            charts=charts,
            language=self.language
        )

        self.logger.info(
            "HTML 대시보드 빌드 완료",
            "HTML dashboard build complete"
        )

        return html

    def save_dashboard(self, html: str) -> Path:
        """
        Save dashboard HTML to file
        대시보드 HTML을 파일에 저장

        Args:
            html: Complete HTML string / 완전한 HTML 문자열

        Returns:
            Path to saved file / 저장된 파일 경로
        """
        output_filename = f"HR_Dashboard_{self.year}_{self.month:02d}.html"
        output_path = self.output_dir / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        self.logger.info(
            f"대시보드 저장 완료: {output_path}",
            f"Dashboard saved: {output_path}"
        )

        return output_path

    def generate(self) -> Path:
        """
        Execute complete dashboard generation pipeline
        완전한 대시보드 생성 파이프라인 실행

        This is the main entry point that orchestrates all steps.
        이것은 모든 단계를 조율하는 메인 진입점입니다.

        Returns:
            Path to generated dashboard file / 생성된 대시보드 파일 경로
        """
        self.logger.info(
            f"=== 대시보드 생성 시작: {self.year}년 {self.month}월 ===",
            f"=== Dashboard generation started: {self.year}-{self.month:02d} ==="
        )

        # Step 1: Load all data
        # 단계 1: 모든 데이터 로드
        if not self.load_all_data():
            raise RuntimeError("Failed to load data / 데이터 로딩 실패")

        # Step 2: Validate data and detect errors
        # 단계 2: 데이터 검증 및 오류 감지
        self.validate_data()

        # Step 3: Calculate all metrics (configuration-driven)
        # 단계 3: 모든 메트릭 계산 (설정 기반)
        self.calculate_all_metrics()

        # Step 4: Analyze trends (reusable for any metric)
        # 단계 4: 트렌드 분석 (모든 메트릭에 재활용 가능)
        self.analyze_all_trends()

        # Step 5: Generate charts (template-driven)
        # 단계 5: 차트 생성 (템플릿 기반)
        charts = self.generate_all_charts()

        # Step 6: Build HTML dashboard
        # 단계 6: HTML 대시보드 빌드
        html = self.build_dashboard_html(charts)

        # Step 7: Save to file
        # 단계 7: 파일에 저장
        output_path = self.save_dashboard(html)

        self.logger.info(
            f"=== 대시보드 생성 완료: {output_path} ===",
            f"=== Dashboard generation completed: {output_path} ==="
        )

        return output_path


def main():
    """
    Command-line interface for dashboard generation
    대시보드 생성을 위한 커맨드라인 인터페이스
    """
    parser = argparse.ArgumentParser(
        description="Generate HR Dashboard / HR 대시보드 생성"
    )
    parser.add_argument(
        '--month', '-m',
        type=int,
        required=True,
        help='Target month (1-12) / 대상 월 (1-12)'
    )
    parser.add_argument(
        '--year', '-y',
        type=int,
        required=True,
        help='Target year (e.g., 2025) / 대상 연도 (예: 2025)'
    )
    parser.add_argument(
        '--language', '-l',
        type=str,
        default='ko',
        choices=['ko', 'en', 'vi'],
        help='Dashboard language / 대시보드 언어'
    )
    parser.add_argument(
        '--sync',
        action='store_true',
        help='Enable Google Drive sync / Google Drive 동기화 활성화'
    )

    args = parser.parse_args()

    # Create and run dashboard generator
    # 대시보드 생성기 생성 및 실행
    generator = DashboardGenerator(
        month=args.month,
        year=args.year,
        language=args.language,
        use_google_drive=args.sync
    )

    try:
        output_path = generator.generate()
        print(f"\n✅ Dashboard generated successfully: {output_path}")
        print(f"✅ 대시보드 생성 성공: {output_path}\n")

    except Exception as e:
        print(f"\n❌ Dashboard generation failed: {str(e)}")
        print(f"❌ 대시보드 생성 실패: {str(e)}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
