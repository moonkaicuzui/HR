#!/usr/bin/env python3
"""
analyze_metric_discrepancies.py - Metric Discrepancy Analysis Tool
메트릭 불일치 분석 도구

Performs deep analysis of why metrics differ from expected values
메트릭이 예상 값과 다른 이유에 대한 심층 분석 수행
"""

import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.monthly_data_collector import MonthlyDataCollector
from src.analytics.hr_metric_calculator import HRMetricCalculator
from src.utils.date_handler import parse_entrance_date, parse_stop_date
from src.utils.data_tracker import DataFlowTracker
from src.utils.logger_config import setup_logger


class MetricDiscrepancyAnalyzer:
    """
    Analyze discrepancies between expected and calculated metrics
    예상 메트릭과 계산된 메트릭 간의 불일치 분석
    """

    def __init__(self, target_month: str = '2025-10'):
        """
        Initialize analyzer
        분석기 초기화
        """
        self.target_month = target_month
        self.hr_root = Path(__file__).parent
        self.logger = setup_logger('metric_analyzer', 'INFO')

        # Initialize components
        # 컴포넌트 초기화
        self.collector = MonthlyDataCollector(self.hr_root)
        self.calculator = HRMetricCalculator(self.collector)
        self.tracker = DataFlowTracker()

    def analyze_recent_hires(self, df: pd.DataFrame) -> Dict:
        """
        Deep analysis of recent hires metric
        신규 입사자 메트릭의 심층 분석
        """
        print("\n" + "=" * 80)
        print("🔍 RECENT HIRES ANALYSIS (신규 입사자 분석)")
        print("=" * 80)

        year, month = self.target_month.split('-')
        year_num = int(year)
        month_num = int(month)

        # Parse dates
        # 날짜 파싱
        entrance_dates = parse_entrance_date(df)

        # Track parsing success
        # 파싱 성공 추적
        parsing_failed = entrance_dates.isna() & df['Entrance Date'].notna()
        print(f"\n📊 Date Parsing:")
        print(f"   Total records: {len(df)}")
        print(f"   Parsed successfully: {(~entrance_dates.isna()).sum()}")
        print(f"   Parsing failed: {parsing_failed.sum()}")

        if parsing_failed.any():
            print(f"\n⚠️  Failed parsing samples:")
            failed_samples = df[parsing_failed]['Entrance Date'].head(5)
            for idx, sample in enumerate(failed_samples, 1):
                print(f"      {idx}. '{sample}'")

        # Method 1: Year-Month string matching
        # 방법 1: 연-월 문자열 매칭
        df_with_parsed = df.copy()
        df_with_parsed['entrance_parsed'] = entrance_dates
        df_with_parsed['entrance_yearmonth'] = entrance_dates.dt.strftime('%Y-%m')

        method1_result = df_with_parsed[
            df_with_parsed['entrance_yearmonth'] == self.target_month
        ]

        print(f"\n📈 Method 1: Year-Month String Matching")
        print(f"   Result: {len(method1_result)} hires")
        print(f"   Logic: entrance_date.strftime('%Y-%m') == '{self.target_month}'")

        # Method 2: Date range filtering
        # 방법 2: 날짜 범위 필터링
        month_start = pd.Timestamp(f"{year_num}-{month_num:02d}-01")
        if month_num == 12:
            month_end = pd.Timestamp(f"{year_num}-12-31 23:59:59")
        else:
            month_end = pd.Timestamp(f"{year_num}-{month_num+1:02d}-01") - pd.Timedelta(seconds=1)

        method2_result = df_with_parsed[
            (entrance_dates >= month_start) &
            (entrance_dates <= month_end)
        ]

        print(f"\n📈 Method 2: Date Range Filtering")
        print(f"   Result: {len(method2_result)} hires")
        print(f"   Logic: {month_start.date()} <= entrance_date <= {month_end.date()}")

        # Method 3: With status filter
        # 방법 3: 상태 필터 포함
        if 'Status' in df.columns:
            method3_result = method2_result[method2_result['Status'] == 'Active']
            print(f"\n📈 Method 3: With Status Filter")
            print(f"   Result: {len(method3_result)} hires")
            print(f"   Logic: Method 2 + Status == 'Active'")
        else:
            method3_result = method2_result
            print(f"\n⚠️  'Status' column not found, skipping Method 3")

        # Analysis
        # 분석
        print(f"\n🔍 Analysis:")
        print(f"   Method 1 vs Method 2 difference: {abs(len(method1_result) - len(method2_result))}")

        if len(method1_result) != len(method2_result):
            print(f"   ⚠️  Methods produce different results!")
            print(f"   This suggests edge cases around month boundaries")

        # Show sample hires
        # 샘플 신규 입사자 표시
        print(f"\n📋 Sample Recent Hires:")
        if not method2_result.empty:
            sample_cols = ['Employee No', 'Employee name', 'Entrance Date', 'Status']
            available_cols = [col for col in sample_cols if col in method2_result.columns]
            print(method2_result[available_cols].head(10).to_string(index=False))

        return {
            'method1_count': len(method1_result),
            'method2_count': len(method2_result),
            'method3_count': len(method3_result) if 'Status' in df.columns else None,
            'parsing_failed': parsing_failed.sum()
        }

    def analyze_perfect_attendance(
        self,
        employee_df: pd.DataFrame,
        attendance_df: pd.DataFrame
    ) -> Dict:
        """
        Deep analysis of perfect attendance metric
        개근 직원 메트릭의 심층 분석
        """
        print("\n" + "=" * 80)
        print("🔍 PERFECT ATTENDANCE ANALYSIS (개근 직원 분석)")
        print("=" * 80)

        if attendance_df.empty:
            print("❌ No attendance data available")
            return {}

        print(f"\n📊 Attendance Data Overview:")
        print(f"   Total attendance records: {len(attendance_df)}")
        print(f"   Unique employees: {attendance_df['ID No'].nunique()}")

        # Check compAdd column
        # compAdd 컬럼 확인
        if 'compAdd' not in attendance_df.columns:
            print("❌ 'compAdd' column not found")
            return {}

        # Analyze absence types
        # 결근 유형 분석
        print(f"\n📊 Absence Types:")
        absence_types = attendance_df['compAdd'].value_counts()
        print(absence_types)

        # Method 1: No absences at all
        # 방법 1: 결근이 전혀 없음
        absent_employees = set(attendance_df[
            attendance_df['compAdd'] == 'Vắng mặt'
        ]['ID No'].unique())
        all_employees = set(attendance_df['ID No'].unique())
        method1_perfect = all_employees - absent_employees

        print(f"\n📈 Method 1: No 'Vắng mặt' Records")
        print(f"   All employees in attendance: {len(all_employees)}")
        print(f"   Employees with 'Vắng mặt': {len(absent_employees)}")
        print(f"   Perfect attendance: {len(method1_perfect)}")

        # Method 2: Consider unauthorized absences only
        # 방법 2: 무단 결근만 고려
        if 'Reason Description' in attendance_df.columns:
            unauthorized_employees = set(attendance_df[
                attendance_df['Reason Description'].str.contains('AR1', na=False)
            ]['ID No'].unique())
            method2_perfect = all_employees - unauthorized_employees

            print(f"\n📈 Method 2: No Unauthorized Absences (AR1)")
            print(f"   Employees with AR1: {len(unauthorized_employees)}")
            print(f"   Perfect attendance: {len(method2_perfect)}")
        else:
            method2_perfect = set()
            print(f"\n⚠️  'Reason Description' column not found")

        # Method 3: Cross-check with employee master data
        # 방법 3: 직원 마스터 데이터와 교차 확인
        employee_ids = set(employee_df['Employee No'].astype(str).unique())
        attendance_ids = set(attendance_df['ID No'].astype(str).unique())

        employees_without_attendance = employee_ids - attendance_ids

        print(f"\n📈 Method 3: Employee Master vs Attendance Cross-Check")
        print(f"   Total employees in master: {len(employee_ids)}")
        print(f"   Employees with attendance records: {len(attendance_ids)}")
        print(f"   Employees without attendance records: {len(employees_without_attendance)}")

        if employees_without_attendance:
            print(f"   → These {len(employees_without_attendance)} might be counted as 'perfect'")

        # Analysis
        # 분석
        print(f"\n🔍 Analysis:")
        print(f"   Method 1 result: {len(method1_perfect)}")
        print(f"   Method 2 result: {len(method2_perfect) if method2_perfect else 'N/A'}")
        print(f"   Difference: {abs(len(method1_perfect) - len(method2_perfect)) if method2_perfect else 'N/A'}")

        print(f"\n💡 Interpretation:")
        print(f"   If dashboard shows 333:")
        print(f"      → Likely counting employees without attendance records")
        print(f"   If dashboard shows 192:")
        print(f"      → Correctly counting only those with attendance & no absences")

        return {
            'all_employees': len(all_employees),
            'with_absences': len(absent_employees),
            'method1_perfect': len(method1_perfect),
            'method2_perfect': len(method2_perfect) if method2_perfect else None,
            'without_attendance_records': len(employees_without_attendance)
        }

    def analyze_all_metrics(self):
        """
        Perform comprehensive analysis of all metrics
        모든 메트릭에 대한 종합 분석 수행
        """
        print("\n" + "=" * 80)
        print("🔬 COMPREHENSIVE METRIC ANALYSIS")
        print("종합 메트릭 분석")
        print("=" * 80)

        # Load data
        # 데이터 로드
        print(f"\n📁 Loading data for {self.target_month}...")
        data = self.collector.load_month_data(self.target_month)

        employee_df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        print(f"   Employee records: {len(employee_df)}")
        print(f"   Attendance records: {len(attendance_df)}")

        # Analyze each metric
        # 각 메트릭 분석
        results = {}

        # 1. Recent Hires
        # 1. 신규 입사자
        if not employee_df.empty:
            results['recent_hires'] = self.analyze_recent_hires(employee_df)

        # 2. Perfect Attendance
        # 2. 개근 직원
        if not employee_df.empty and not attendance_df.empty:
            results['perfect_attendance'] = self.analyze_perfect_attendance(
                employee_df, attendance_df
            )

        # Generate summary report
        # 요약 보고서 생성
        self.print_analysis_summary(results)

        return results

    def print_analysis_summary(self, results: Dict):
        """
        Print analysis summary
        분석 요약 출력
        """
        print("\n" + "=" * 80)
        print("📋 ANALYSIS SUMMARY")
        print("분석 요약")
        print("=" * 80)

        if 'recent_hires' in results:
            rh = results['recent_hires']
            print(f"\n신규 입사자 (Recent Hires):")
            print(f"   Method 1: {rh['method1_count']}")
            print(f"   Method 2: {rh['method2_count']}")
            print(f"   Parsing failures: {rh['parsing_failed']}")

        if 'perfect_attendance' in results:
            pa = results['perfect_attendance']
            print(f"\n개근 직원 (Perfect Attendance):")
            print(f"   Method 1 (no absences): {pa['method1_perfect']}")
            if pa['method2_perfect']:
                print(f"   Method 2 (no unauthorized): {pa['method2_perfect']}")
            print(f"   Without attendance records: {pa['without_attendance_records']}")

        print("\n" + "=" * 80)


def main():
    """
    Main analysis execution
    주요 분석 실행
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze metric discrepancies / 메트릭 불일치 분석'
    )
    parser.add_argument(
        '--month',
        type=str,
        default='2025-10',
        help='Target month (YYYY-MM) / 대상 월 (YYYY-MM)'
    )

    args = parser.parse_args()

    # Create analyzer
    # 분석기 생성
    analyzer = MetricDiscrepancyAnalyzer(args.month)

    # Run analysis
    # 분석 실행
    analyzer.analyze_all_metrics()


if __name__ == '__main__':
    main()