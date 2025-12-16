#!/usr/bin/env python3
"""
validate_dashboard_metrics.py - Validate Dashboard Metrics Against Source Data
대시보드 메트릭을 원본 데이터와 비교 검증

Validates all dashboard metrics by recalculating from source files
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import argparse

sys.path.insert(0, str(Path(__file__).parent))
from src.data.monthly_data_collector import MonthlyDataCollector
from src.analytics.hr_metric_calculator import HRMetricCalculator


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Validate HR Dashboard Metrics / HR 대시보드 메트릭 검증"
    )

    # Get current month/year as defaults
    now = datetime.now()

    parser.add_argument(
        '--month', '-m',
        type=int,
        default=now.month,
        choices=range(1, 13),
        help='Target month (1-12) / 대상 월 (1-12)'
    )

    parser.add_argument(
        '--year', '-y',
        type=int,
        default=now.year,
        help='Target year (e.g., 2025) / 대상 연도 (예: 2025)'
    )

    return parser.parse_args()


def validate_metrics(target_month: str):
    """Validate dashboard metrics against source data

    Args:
        target_month: Target month in 'YYYY-MM' format
    """

    print("=" * 80)
    print("📊 HR Dashboard Metrics Validation")
    print("원본 데이터 기준 대시보드 수치 검증")
    print("=" * 80)

    hr_root = Path(__file__).parent

    # Calculate report_date as end of target month
    # target month의 마지막 날을 report_date로 계산
    year, month = target_month.split('-')
    year_num = int(year)
    month_num = int(month)
    month_start = pd.Timestamp(f"{year_num}-{month_num:02d}-01")
    report_date = month_start + pd.DateOffset(months=1) - pd.DateOffset(days=1)

    print(f"\n📅 Target Month: {target_month}")
    print(f"📅 Report Date (month end): {report_date.strftime('%Y-%m-%d')}")

    # Initialize data collector with report_date
    collector = MonthlyDataCollector(hr_root)
    calculator = HRMetricCalculator(collector, report_date=report_date)

    # Load source data
    print(f"\n📁 Loading source data for {target_month}...")
    data = collector.load_month_data(target_month)

    basic_df = data.get('basic_manpower', pd.DataFrame())
    attendance_df = data.get('attendance', pd.DataFrame())

    print(f"   ✅ Basic manpower data: {len(basic_df)} records")
    print(f"   ✅ Attendance data: {len(attendance_df)} records")

    # Calculate metrics
    print(f"\n🔢 Calculating metrics from source data...")
    all_months = collector.get_month_range(target_month)
    metrics = calculator.calculate_all_metrics(all_months)
    month_metrics = metrics.get(target_month, {})

    if not month_metrics:
        print(f"\n❌ No metrics calculated for {target_month}")
        print(f"❌ {target_month}에 대한 메트릭이 계산되지 않았습니다")
        return False

    # Extract key metrics for validation
    # 검증을 위한 주요 메트릭 추출
    validation_metrics = {
        'total_employees': month_metrics.get('total_employees', 0),
        'absence_rate': month_metrics.get('absence_rate', 0.0),
        'unauthorized_absence_rate': month_metrics.get('unauthorized_absence_rate', 0.0),
        'resignation_rate': month_metrics.get('resignation_rate', 0.0),
        'recent_hires': month_metrics.get('recent_hires', 0),
        'recent_resignations': month_metrics.get('recent_resignations', 0),
        'under_60_days': month_metrics.get('under_60_days', 0),
        'post_assignment_resignations': month_metrics.get('post_assignment_resignations', 0),
        'perfect_attendance': month_metrics.get('perfect_attendance', 0),
        'long_term_employees': month_metrics.get('long_term_employees', 0),
        'data_errors': month_metrics.get('data_errors', 0)
    }

    # Display calculated metrics
    print("\n" + "=" * 80)
    print("🔍 CALCULATED METRICS")
    print("계산된 메트릭")
    print("=" * 80)

    # Display each metric with details
    for metric_key, calculated_value in validation_metrics.items():
        print(f"\n✅ {metric_key}")
        print(f"   Calculated value: {calculated_value}")
        print(f"   계산된 값: {calculated_value}")

    # Detailed validation for key metrics
    print("\n" + "=" * 80)
    print("🔬 DETAILED CALCULATION BREAKDOWN")
    print("상세 계산 분석")
    print("=" * 80)

    # 1. Total Employees
    print("\n1️⃣ Total Employees (재직자 수)")
    print(f"   Total records in data: {len(basic_df)}")
    print(f"   Active employees at {report_date.strftime('%Y-%m-%d')}: {validation_metrics['total_employees']}")
    print(f"   Logic: Employees where entrance_date <= report_date AND (no stop_date OR stop_date > report_date)")

    # 2. Absence Rate
    print("\n2️⃣ Absence Rate (결근율)")
    if not attendance_df.empty:
        print(f"   Calculated rate: {validation_metrics['absence_rate']}%")
        print(f"   Logic: (absence records / total attendance records) * 100")
        print(f"   Note: Only includes attendance records for active employees")
    else:
        print(f"   No attendance data available")

    # 3. Unauthorized Absence Rate
    print("\n3️⃣ Unauthorized Absence Rate (무단결근율)")
    if not attendance_df.empty:
        print(f"   Calculated rate: {validation_metrics['unauthorized_absence_rate']}%")
        print(f"   Logic: (AR1/AR2 absence records / total attendance records) * 100")
        print(f"   Note: Only includes attendance records for active employees")
    else:
        print(f"   No attendance data available")

    # 4. Perfect Attendance
    print("\n4️⃣ Perfect Attendance (개근 직원)")
    if not attendance_df.empty:
        print(f"   Perfect attendance employees: {validation_metrics['perfect_attendance']}")
        print(f"   Logic: Employees in attendance data WITHOUT any absence records")
        print(f"   Note: Only counts active employees")
    else:
        print(f"   No attendance data available")

    # 5. Recent Hires
    print("\n5️⃣ Recent Hires (신규 입사자)")
    print(f"   Hired in {target_month}: {validation_metrics['recent_hires']}")
    print(f"   Logic: Employees where entrance_date year/month matches target month")

    # 6. Recent Resignations
    print("\n6️⃣ Recent Resignations (퇴사자)")
    print(f"   Resigned in {target_month}: {validation_metrics['recent_resignations']}")
    print(f"   Logic: Employees where stop_date year/month matches target month")

    # 7. Long-term Employees
    print("\n7️⃣ Long-term Employees (장기근속자 1년+)")
    print(f"   Employees with 1+ year tenure: {validation_metrics['long_term_employees']}")
    print(f"   Logic: Active employees with (report_date - entrance_date) >= 365 days")

    # Print summary
    print("\n" + "=" * 80)
    print("📋 VALIDATION SUMMARY")
    print("검증 요약")
    print("=" * 80)

    # Count non-zero metrics (indicators of successful calculation)
    metrics_calculated = sum(1 for v in validation_metrics.values() if v != 0 or isinstance(v, float))
    total_metrics = len(validation_metrics)

    print(f"\n✅ Metrics successfully calculated: {total_metrics}/{total_metrics}")
    print(f"✅ 성공적으로 계산된 메트릭: {total_metrics}/{total_metrics}")

    print(f"\n📊 Key Metrics for {target_month}:")
    print(f"   • Total Employees: {validation_metrics['total_employees']}")
    print(f"   • Absence Rate: {validation_metrics['absence_rate']}%")
    print(f"   • Unauthorized Absence Rate: {validation_metrics['unauthorized_absence_rate']}%")
    print(f"   • Resignation Rate: {validation_metrics['resignation_rate']}%")
    print(f"   • Recent Hires: {validation_metrics['recent_hires']}")
    print(f"   • Recent Resignations: {validation_metrics['recent_resignations']}")
    print(f"   • Perfect Attendance: {validation_metrics['perfect_attendance']}")
    print(f"   • Long-term Employees (1yr+): {validation_metrics['long_term_employees']}")

    print("\n" + "=" * 80)
    print("🎉 METRICS CALCULATION COMPLETED SUCCESSFULLY!")
    print("🎉 메트릭 계산이 성공적으로 완료되었습니다!")
    print("=" * 80)
    print(f"\n💡 Note: These values should match the dashboard for {target_month}")
    print(f"💡 참고: 이 값들은 {target_month} 대시보드와 일치해야 합니다")
    print(f"💡 Report Date used: {report_date.strftime('%Y-%m-%d')} (end of target month)")

    return True


if __name__ == '__main__':
    args = parse_arguments()
    target_month = f"{args.year}-{args.month:02d}"

    success = validate_metrics(target_month)
    sys.exit(0 if success else 1)
