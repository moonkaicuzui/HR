#!/usr/bin/env python3
"""
debug_metrics.py - Debug and compare metrics calculation
메트릭 계산 디버깅 및 비교

Independently calculates each metric and shows detailed breakdowns
각 메트릭을 독립적으로 계산하고 상세 분석 표시
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_metrics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.monthly_data_collector import MonthlyDataCollector
from src.analytics.hr_metric_calculator import HRMetricCalculator
from src.utils.date_handler import parse_entrance_date, parse_stop_date


def debug_employee_count(df: pd.DataFrame, target_month: str = '2025-10'):
    """
    Debug employee count calculation with detailed breakdown
    직원 수 계산을 상세하게 디버깅
    """
    print("\n" + "=" * 80)
    print("🔍 EMPLOYEE COUNT DEBUGGING")
    print("=" * 80)

    # Parse dates properly
    entrance_dates = parse_entrance_date(df)
    stop_dates = parse_stop_date(df)

    # Check for date parsing issues
    print(f"\n📅 Date Parsing Statistics:")
    print(f"   Total records: {len(df)}")
    print(f"   Valid entrance dates: {entrance_dates.notna().sum()}")
    print(f"   Valid stop dates: {stop_dates.notna().sum()}")
    print(f"   Invalid entrance dates: {entrance_dates.isna().sum()}")
    print(f"   Invalid stop dates (excluding active): {(stop_dates.isna() & df['Stop working Date'].notna()).sum()}")

    # Sample some dates for verification
    print(f"\n📋 Sample Date Conversions:")
    sample_indices = df.head(5).index
    for idx in sample_indices:
        orig_entrance = df.loc[idx, 'Entrance Date']
        parsed_entrance = entrance_dates.loc[idx]
        orig_stop = df.loc[idx, 'Stop working Date']
        parsed_stop = stop_dates.loc[idx]
        print(f"   Row {idx}: Entrance: {orig_entrance} → {parsed_entrance}, Stop: {orig_stop} → {parsed_stop}")

    # Calculate reference dates
    year, month = target_month.split('-')
    year_num = int(year)
    month_num = int(month)
    month_start = pd.Timestamp(f"{year_num}-{month_num:02d}-01")
    month_end = pd.Timestamp(f"{year_num}-{month_num:02d}-01") + pd.DateOffset(months=1) - pd.DateOffset(days=1)
    report_date = datetime.now()
    report_timestamp = pd.Timestamp(report_date)

    print(f"\n📅 Reference Dates:")
    print(f"   Target month: {target_month}")
    print(f"   Month start: {month_start}")
    print(f"   Month end: {month_end}")
    print(f"   Report date: {report_timestamp}")

    # Calculate different employee counts
    print(f"\n👥 Employee Count Calculations:")

    # Method 1: Active at month end
    active_month_end = df[
        (entrance_dates <= month_end) &
        ((stop_dates.isna()) | (stop_dates > month_end))
    ]
    print(f"\n   Method 1 - Active at month end: {len(active_month_end)}")

    # Method 2: Active at report date
    active_report_date = df[
        (entrance_dates <= report_timestamp) &
        ((stop_dates.isna()) | (stop_dates > report_timestamp))
    ]
    print(f"   Method 2 - Active at report date: {len(active_report_date)}")

    # Method 3: Active at any time during the month (for incentive)
    active_during_month = df[
        (entrance_dates <= month_end) &
        ((stop_dates.isna()) | (stop_dates >= month_start))
    ]
    print(f"   Method 3 - Active during month (incentive basis): {len(active_during_month)}")

    # Breakdown of differences
    print(f"\n🔍 Detailed Breakdown:")

    # New hires in the month
    new_hires = df[
        (entrance_dates >= month_start) &
        (entrance_dates <= month_end)
    ]
    print(f"   New hires in {target_month}: {len(new_hires)}")

    # Resignations in the month
    resignations = df[
        (stop_dates >= month_start) &
        (stop_dates <= month_end)
    ]
    print(f"   Resignations in {target_month}: {len(resignations)}")

    # Active but will resign after month end
    future_resignations = df[
        (entrance_dates <= month_end) &
        (stop_dates > month_end) &
        (stop_dates <= report_timestamp)
    ]
    print(f"   Will resign after month but before report date: {len(future_resignations)}")

    # Find discrepancies
    print(f"\n⚠️ Potential Issues:")

    # Check for entrance dates in the future
    future_entrance = df[entrance_dates > report_timestamp]
    if not future_entrance.empty:
        print(f"   ❌ {len(future_entrance)} employees have entrance dates in the future!")
        print(f"      Sample: {future_entrance['Entrance Date'].head(3).tolist()}")

    # Check for stop dates before entrance dates
    invalid_timeline = df[
        entrance_dates.notna() &
        stop_dates.notna() &
        (stop_dates < entrance_dates)
    ]
    if not invalid_timeline.empty:
        print(f"   ❌ {len(invalid_timeline)} employees have stop dates before entrance dates!")
        print(f"      Sample Employee IDs: {invalid_timeline['Employee No'].head(3).tolist()}")

    return {
        'month_end': len(active_month_end),
        'report_date': len(active_report_date),
        'during_month': len(active_during_month),
        'new_hires': len(new_hires),
        'resignations': len(resignations)
    }


def debug_absence_metrics(df: pd.DataFrame, attendance_df: pd.DataFrame):
    """
    Debug absence-related metrics
    결근 관련 메트릭 디버깅
    """
    print("\n" + "=" * 80)
    print("🔍 ABSENCE METRICS DEBUGGING")
    print("=" * 80)

    if attendance_df.empty:
        print("   ❌ No attendance data available")
        return

    print(f"\n📊 Attendance Data Overview:")
    print(f"   Total attendance records: {len(attendance_df)}")
    print(f"   Unique employees in attendance: {attendance_df['ID No'].nunique()}")

    if 'compAdd' in attendance_df.columns:
        absence_records = attendance_df[attendance_df['compAdd'] == 'Vắng mặt']
        print(f"   Total absence records: {len(absence_records)}")
        print(f"   Unique employees with absences: {absence_records['ID No'].nunique()}")

        # Calculate rates
        total_records = len(attendance_df)
        absence_rate = (len(absence_records) / total_records * 100) if total_records > 0 else 0
        print(f"   Raw absence rate: {absence_rate:.2f}%")

        # Perfect attendance
        all_employee_ids = attendance_df['ID No'].unique()
        absent_employee_ids = absence_records['ID No'].unique()
        perfect_attendance_count = len(set(all_employee_ids) - set(absent_employee_ids))
        print(f"   Perfect attendance employees: {perfect_attendance_count}")
    else:
        print("   ⚠️ 'compAdd' column not found in attendance data")

    if 'Reason Description' in attendance_df.columns:
        unauthorized = attendance_df[
            attendance_df['Reason Description'].str.contains('AR1', na=False)
        ]
        print(f"\n   Unauthorized absences (AR1): {len(unauthorized)}")
        unauthorized_rate = (len(unauthorized) / len(attendance_df) * 100) if len(attendance_df) > 0 else 0
        print(f"   Unauthorized absence rate: {unauthorized_rate:.2f}%")
    else:
        print("   ⚠️ 'Reason Description' column not found")


def main():
    """Main debugging function"""
    print("\n" + "=" * 80)
    print("🛠️ HR DASHBOARD METRICS DEBUGGER")
    print("=" * 80)

    hr_root = Path(__file__).parent
    target_month = '2025-10'

    # Initialize data collector
    collector = MonthlyDataCollector(hr_root)
    calculator = HRMetricCalculator(collector)

    # Load data
    print(f"\n📁 Loading data for {target_month}...")
    data = collector.load_month_data(target_month)

    basic_df = data.get('basic_manpower', pd.DataFrame())
    attendance_df = data.get('attendance', pd.DataFrame())

    if basic_df.empty:
        print("   ❌ No basic manpower data found!")
        return

    print(f"   ✅ Loaded {len(basic_df)} employee records")
    print(f"   ✅ Loaded {len(attendance_df)} attendance records")

    # Debug employee count
    employee_counts = debug_employee_count(basic_df, target_month)

    # Debug absence metrics
    debug_absence_metrics(basic_df, attendance_df)

    # Compare with calculator output
    print("\n" + "=" * 80)
    print("🔄 COMPARING WITH CALCULATOR OUTPUT")
    print("=" * 80)

    all_months = collector.get_month_range(target_month)
    metrics = calculator.calculate_all_metrics(all_months)
    oct_metrics = metrics.get(target_month, {})

    print(f"\n📊 Calculator Results vs Debug:")
    print(f"   Total employees: Calculator={oct_metrics.get('total_employees')}, Debug={employee_counts['report_date']}")
    print(f"   Absence rate: Calculator={oct_metrics.get('absence_rate')}%")
    print(f"   Perfect attendance: Calculator={oct_metrics.get('perfect_attendance')}")
    print(f"   Recent hires: Calculator={oct_metrics.get('recent_hires')}, Debug={employee_counts['new_hires']}")
    print(f"   Recent resignations: Calculator={oct_metrics.get('recent_resignations')}, Debug={employee_counts['resignations']}")

    # Generate HTML dashboard data
    print("\n" + "=" * 80)
    print("📄 CHECKING GENERATED DASHBOARD")
    print("=" * 80)

    dashboard_file = hr_root / 'output_files' / f'HR_Dashboard_Complete_{target_month.replace("-", "_")}.html'
    if dashboard_file.exists():
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Search for metrics in the HTML
            if '"total_employees": 399' in content:
                print("   ⚠️ Dashboard shows 399 employees (hardcoded or cached?)")
            elif f'"total_employees": {oct_metrics.get("total_employees")}' in content:
                print(f"   ✅ Dashboard shows {oct_metrics.get('total_employees')} employees (matches calculator)")
            else:
                print("   ❓ Could not find total_employees in dashboard HTML")


if __name__ == "__main__":
    main()