#!/usr/bin/env python3
"""
compare_data.py - Dashboard vs Actual Data Comparison Tool
대시보드 vs 실제 데이터 비교 도구

Compares dashboard displayed values with calculated values from source data
대시보드 표시 값을 원본 데이터에서 계산된 값과 비교
"""

import pandas as pd
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.monthly_data_collector import MonthlyDataCollector
from src.analytics.hr_metric_calculator import HRMetricCalculator
from src.utils.logger_config import setup_logger, LogContext
from src.utils.error_handler import ErrorContext, ValidationError


class DashboardDataComparator:
    """
    Compare dashboard data with source calculations
    대시보드 데이터를 원본 계산과 비교
    """

    def __init__(self, target_month: str = '2025-10'):
        """
        Initialize comparator
        비교기 초기화
        """
        self.target_month = target_month
        self.hr_root = Path(__file__).parent
        self.logger = setup_logger('data_comparator', 'INFO')

        # Initialize data components
        # 데이터 컴포넌트 초기화
        self.collector = MonthlyDataCollector(self.hr_root)
        self.calculator = HRMetricCalculator(self.collector)

        # Storage for results
        # 결과 저장소
        self.dashboard_data = {}
        self.calculated_data = {}
        self.comparison_results = {
            'matches': [],
            'mismatches': [],
            'missing_in_dashboard': [],
            'missing_in_calculation': []
        }

    def load_dashboard_data(self, html_path: Path) -> bool:
        """
        Load data from dashboard HTML
        대시보드 HTML에서 데이터 로드

        Returns:
            Success status / 성공 상태
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metrics data from JavaScript
            # JavaScript에서 메트릭 데이터 추출
            metrics_pattern = r'const monthlyMetrics\s*=\s*(\{.*?\});'
            metrics_match = re.search(metrics_pattern, content, re.DOTALL)

            if metrics_match:
                metrics_json = metrics_match.group(1)
                # Clean up JavaScript to valid JSON
                # JavaScript를 유효한 JSON으로 정리
                metrics_json = re.sub(r'(\w+):', r'"\1":', metrics_json)  # Quote keys
                metrics_json = re.sub(r"'", '"', metrics_json)  # Single to double quotes

                self.dashboard_data = json.loads(metrics_json)
                self.logger.info(f"Loaded dashboard data for {len(self.dashboard_data)} months")
                return True
            else:
                self.logger.error("Could not find metrics data in dashboard HTML")
                return False

        except Exception as e:
            self.logger.error(f"Error loading dashboard data: {e}")
            return False

    def calculate_source_data(self) -> bool:
        """
        Calculate metrics from source data
        원본 데이터에서 메트릭 계산

        Returns:
            Success status / 성공 상태
        """
        try:
            # Get all months for comparison
            # 비교를 위한 모든 월 가져오기
            all_months = self.collector.get_month_range(self.target_month)

            # Calculate metrics
            # 메트릭 계산
            self.calculated_data = self.calculator.calculate_all_metrics(all_months)

            self.logger.info(f"Calculated metrics for {len(self.calculated_data)} months")
            return True

        except Exception as e:
            self.logger.error(f"Error calculating source data: {e}")
            return False

    def compare_metric(
        self,
        metric_name: str,
        dashboard_value: Any,
        calculated_value: Any,
        tolerance: float = 0.01
    ) -> Tuple[bool, str]:
        """
        Compare single metric values
        단일 메트릭 값 비교

        Args:
            metric_name: Metric name / 메트릭 이름
            dashboard_value: Value from dashboard / 대시보드 값
            calculated_value: Calculated value / 계산된 값
            tolerance: Tolerance for float comparison / 부동소수점 비교 허용 오차

        Returns:
            (is_match, description) / (일치 여부, 설명)
        """
        # Handle None values
        # None 값 처리
        if dashboard_value is None and calculated_value is None:
            return True, "Both None"
        if dashboard_value is None or calculated_value is None:
            return False, f"One is None: dashboard={dashboard_value}, calculated={calculated_value}"

        # Compare based on type
        # 타입에 따라 비교
        if isinstance(dashboard_value, (int, float)) and isinstance(calculated_value, (int, float)):
            # Numeric comparison with tolerance
            # 허용 오차를 포함한 숫자 비교
            difference = abs(dashboard_value - calculated_value)
            if difference <= tolerance:
                return True, f"Match within tolerance: {dashboard_value} ≈ {calculated_value}"
            else:
                return False, f"Mismatch: dashboard={dashboard_value}, calculated={calculated_value}, diff={difference:.4f}"
        else:
            # Exact comparison
            # 정확한 비교
            if dashboard_value == calculated_value:
                return True, f"Exact match: {dashboard_value}"
            else:
                return False, f"Mismatch: dashboard={dashboard_value}, calculated={calculated_value}"

    def compare_month_data(self, month: str) -> Dict:
        """
        Compare all metrics for a specific month
        특정 월의 모든 메트릭 비교

        Args:
            month: Month string (YYYY-MM) / 월 문자열 (YYYY-MM)

        Returns:
            Comparison results / 비교 결과
        """
        results = {
            'month': month,
            'total_metrics': 0,
            'matches': 0,
            'mismatches': 0,
            'missing': 0,
            'details': []
        }

        # Get data for the month
        # 해당 월의 데이터 가져오기
        dashboard_month = self.dashboard_data.get(month, {})
        calculated_month = self.calculated_data.get(month, {})

        # Get all metric keys
        # 모든 메트릭 키 가져오기
        all_metrics = set(dashboard_month.keys()) | set(calculated_month.keys())
        results['total_metrics'] = len(all_metrics)

        for metric in sorted(all_metrics):
            dashboard_val = dashboard_month.get(metric)
            calculated_val = calculated_month.get(metric)

            # Check if metric exists in both
            # 두 곳 모두에 메트릭이 있는지 확인
            if metric not in dashboard_month:
                results['missing'] += 1
                results['details'].append({
                    'metric': metric,
                    'status': 'missing_in_dashboard',
                    'calculated': calculated_val
                })
                self.comparison_results['missing_in_dashboard'].append((month, metric))
            elif metric not in calculated_month:
                results['missing'] += 1
                results['details'].append({
                    'metric': metric,
                    'status': 'missing_in_calculation',
                    'dashboard': dashboard_val
                })
                self.comparison_results['missing_in_calculation'].append((month, metric))
            else:
                # Compare values
                # 값 비교
                is_match, description = self.compare_metric(metric, dashboard_val, calculated_val)

                if is_match:
                    results['matches'] += 1
                    results['details'].append({
                        'metric': metric,
                        'status': 'match',
                        'description': description
                    })
                    self.comparison_results['matches'].append((month, metric))
                else:
                    results['mismatches'] += 1
                    results['details'].append({
                        'metric': metric,
                        'status': 'mismatch',
                        'dashboard': dashboard_val,
                        'calculated': calculated_val,
                        'description': description
                    })
                    self.comparison_results['mismatches'].append({
                        'month': month,
                        'metric': metric,
                        'dashboard': dashboard_val,
                        'calculated': calculated_val
                    })

        return results

    def run_comparison(self) -> Dict:
        """
        Run full comparison
        전체 비교 실행

        Returns:
            Complete comparison report / 완전한 비교 보고서
        """
        with LogContext(self.logger, phase='comparison'):
            # Load dashboard data
            # 대시보드 데이터 로드
            year, month_num = self.target_month.split('-')
            dashboard_path = (
                self.hr_root / 'output_files' /
                f'HR_Dashboard_Complete_{year}_{month_num}.html'
            )

            if not dashboard_path.exists():
                raise ValidationError(f"Dashboard file not found: {dashboard_path}")

            if not self.load_dashboard_data(dashboard_path):
                raise ValidationError("Failed to load dashboard data")

            # Calculate source data
            # 원본 데이터 계산
            if not self.calculate_source_data():
                raise ValidationError("Failed to calculate source data")

            # Compare each month
            # 각 월 비교
            monthly_results = []
            for month in sorted(set(self.dashboard_data.keys()) | set(self.calculated_data.keys())):
                month_result = self.compare_month_data(month)
                monthly_results.append(month_result)

                # Log month summary
                # 월 요약 로그
                self.logger.info(
                    f"{month}: {month_result['matches']}/{month_result['total_metrics']} matches, "
                    f"{month_result['mismatches']} mismatches, {month_result['missing']} missing"
                )

            # Create summary report
            # 요약 보고서 생성
            report = self.create_summary_report(monthly_results)
            return report

    def create_summary_report(self, monthly_results: List[Dict]) -> Dict:
        """
        Create summary comparison report
        요약 비교 보고서 생성

        Args:
            monthly_results: Results for each month / 각 월의 결과

        Returns:
            Summary report / 요약 보고서
        """
        total_comparisons = sum(r['total_metrics'] for r in monthly_results)
        total_matches = sum(r['matches'] for r in monthly_results)
        total_mismatches = sum(r['mismatches'] for r in monthly_results)
        total_missing = sum(r['missing'] for r in monthly_results)

        accuracy = (total_matches / total_comparisons * 100) if total_comparisons > 0 else 0

        report = {
            'timestamp': datetime.now().isoformat(),
            'target_month': self.target_month,
            'summary': {
                'total_comparisons': total_comparisons,
                'total_matches': total_matches,
                'total_mismatches': total_mismatches,
                'total_missing': total_missing,
                'accuracy_percentage': round(accuracy, 2)
            },
            'monthly_results': monthly_results,
            'mismatches': self.comparison_results['mismatches'],
            'critical_issues': []
        }

        # Identify critical issues
        # 중요한 문제 식별
        for mismatch in self.comparison_results['mismatches']:
            if mismatch['metric'] in ['total_employees', 'absence_rate', 'resignation_rate']:
                report['critical_issues'].append(mismatch)

        return report

    def print_report(self, report: Dict):
        """
        Print formatted comparison report
        포맷된 비교 보고서 출력
        """
        print("\n" + "=" * 80)
        print("📊 DASHBOARD vs SOURCE DATA COMPARISON REPORT")
        print("대시보드 vs 원본 데이터 비교 보고서")
        print("=" * 80)

        print(f"\n📅 Target Month: {report['target_month']}")
        print(f"🕐 Generated: {report['timestamp']}")

        # Summary
        # 요약
        summary = report['summary']
        print(f"\n📈 SUMMARY:")
        print(f"   Total Comparisons: {summary['total_comparisons']}")
        print(f"   ✅ Matches: {summary['total_matches']}")
        print(f"   ❌ Mismatches: {summary['total_mismatches']}")
        print(f"   ❓ Missing: {summary['total_missing']}")
        print(f"   📊 Accuracy: {summary['accuracy_percentage']}%")

        # Critical issues
        # 중요한 문제
        if report['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES ({len(report['critical_issues'])}):")
            for issue in report['critical_issues']:
                print(f"   {issue['month']} - {issue['metric']}:")
                print(f"      Dashboard: {issue['dashboard']}")
                print(f"      Calculated: {issue['calculated']}")

        # Monthly breakdown
        # 월별 분석
        print(f"\n📅 MONTHLY BREAKDOWN:")
        for month_result in report['monthly_results']:
            status = "✅" if month_result['mismatches'] == 0 else "⚠️"
            print(f"   {status} {month_result['month']}: "
                  f"{month_result['matches']}/{month_result['total_metrics']} matches")

            # Show mismatches for this month
            # 이 달의 불일치 표시
            month_mismatches = [
                d for d in month_result['details']
                if d['status'] == 'mismatch'
            ]
            if month_mismatches:
                for detail in month_mismatches[:3]:  # Show first 3
                    print(f"      ❌ {detail['metric']}: {detail['description']}")

        print("\n" + "=" * 80)

        # Return status code
        # 상태 코드 반환
        return 0 if summary['total_mismatches'] == 0 else 1


def main():
    """
    Main comparison execution
    주요 비교 실행
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Compare dashboard data with source calculations / 대시보드 데이터와 원본 계산 비교'
    )
    parser.add_argument(
        '--month',
        type=str,
        default='2025-10',
        help='Target month (YYYY-MM format) / 대상 월 (YYYY-MM 형식)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file path / 출력 JSON 파일 경로'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output / 상세 출력 활성화'
    )

    args = parser.parse_args()

    # Create comparator
    # 비교기 생성
    comparator = DashboardDataComparator(args.month)

    if args.verbose:
        comparator.logger.setLevel(logging.DEBUG)

    try:
        # Run comparison
        # 비교 실행
        report = comparator.run_comparison()

        # Save report if requested
        # 요청된 경우 보고서 저장
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"Report saved to: {output_path}")

        # Print report
        # 보고서 출력
        return comparator.print_report(report)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())