"""
dynamic_metric_calculator.py - Dynamic Monthly Metric Calculator
동적 월별 메트릭 계산기

CORE PRINCIPLE: Calculate metrics for ALL available months dynamically
핵심 원칙: 사용 가능한 모든 월에 대해 동적으로 메트릭 계산

NO HARDCODING: Works with any number of months
하드코딩 없음: 어떤 개수의 월에도 작동
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data.monthly_data_collector import MonthlyDataCollector
else:
    from ..data.monthly_data_collector import MonthlyDataCollector


class DynamicMetricCalculator:
    """
    Calculate metrics dynamically for all available months
    사용 가능한 모든 월에 대해 동적으로 메트릭 계산

    NOTE: This is a reference implementation for documentation purposes.
    The actual metric calculations used in production are performed by
    HRMetricCalculator in hr_metric_calculator.py, which handles:
    - Proper column mappings for HR data
    - Maternity/pregnancy exclusions
    - Consolidated attendance data
    - Team-based calculations

    참고: 이 클래스는 문서화 목적의 참조 구현입니다.
    실제 프로덕션에서 사용되는 메트릭 계산은 hr_metric_calculator.py의
    HRMetricCalculator에서 수행됩니다.
    """

    # HR Dashboard column name mapping
    # HR 대시보드 컬럼명 매핑
    COLUMN_MAP = {
        'employee_no': 'Employee No',
        'employee_name': 'Full Name',
        'join_date': 'Entrance Date',
        'resignation_date': 'Stop working Date',
        'position': 'FINAL QIP POSITION NAME CODE',
        'role_type': 'ROLE TYPE STD',
        'assignment_date': None,  # Not available in HR data
        'boss_id': None  # Not available in HR data
    }

    def __init__(self, data_collector: MonthlyDataCollector):
        """
        Initialize DynamicMetricCalculator

        Args:
            data_collector: MonthlyDataCollector instance
        """
        self.data_collector = data_collector
        self.monthly_metrics: Dict[str, Dict[str, Any]] = {}

    def calculate_all_metrics(self, months_to_calculate: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate all metrics for specified months
        지정된 월들에 대해 모든 메트릭 계산

        Args:
            months_to_calculate: List of 'YYYY-MM' strings

        Returns:
            Dictionary mapping month to metrics
            {
                '2025-07': {
                    'total_employees': 378,
                    'absence_rate': 2.5,
                    ...
                },
                '2025-08': { ... },
                ...
            }
        """
        for month in months_to_calculate:
            self.monthly_metrics[month] = self.calculate_month_metrics(month)

        return self.monthly_metrics

    def calculate_month_metrics(self, year_month: str) -> Dict[str, Any]:
        """
        Calculate all metrics for a specific month
        특정 월의 모든 메트릭 계산

        Args:
            year_month: Month in 'YYYY-MM' format

        Returns:
            Dictionary of metrics for the month
        """
        # Load data for this month
        month_data = self.data_collector.load_month_data(year_month)

        basic_df = month_data.get('basic_manpower', pd.DataFrame())
        attendance_df = month_data.get('attendance', pd.DataFrame())
        aql_df = month_data.get('aql', pd.DataFrame())
        prs_df = month_data.get('5prs', pd.DataFrame())

        year, month = year_month.split('-')
        month_num = int(month)

        metrics = {}

        # Metric 1: Total Active Employees (재직자 수)
        metrics['total_employees'] = self._calc_total_employees(basic_df, year_month)

        # Metric 2: Absence Rate (결근율)
        metrics['absence_rate'] = self._calc_absence_rate(attendance_df)

        # Metric 3: Unauthorized Absence Rate (무단결근율)
        metrics['unauthorized_absence_rate'] = self._calc_unauthorized_absence_rate(attendance_df)

        # Metric 4: Resignation Rate (퇴사율)
        metrics['resignation_rate'] = self._calc_resignation_rate(basic_df, year_month)

        # Metric 5: Recent Hires (신규 입사자)
        metrics['recent_hires'] = self._calc_recent_hires(basic_df, year_month)

        # Metric 6: Recent Resignations (최근 퇴사자)
        metrics['recent_resignations'] = self._calc_recent_resignations(basic_df, year_month)

        # Metric 7: Under 60 Days (60일 미만)
        metrics['under_60_days'] = self._calc_under_60_days(basic_df, year_month)

        # Metric 8: Post-Assignment Resignations (배정 후 퇴사자)
        metrics['post_assignment_resignations'] = self._calc_post_assignment_resignations(basic_df)

        # Metric 9: Perfect Attendance (개근 직원)
        metrics['perfect_attendance'] = self._calc_perfect_attendance(attendance_df)

        # Metric 10: Long-term Employees (장기근속자 1년+)
        metrics['long_term_employees'] = self._calc_long_term_employees(basic_df, year_month)

        # Metric 11: Data Errors (데이터 오류)
        metrics['data_errors'] = self._calc_data_errors(basic_df)

        return metrics

    def _calc_total_employees(self, df: pd.DataFrame, year_month: str) -> int:
        """Calculate total active employees (no resignation date or future resignation)"""
        if df.empty:
            return 0

        # Column name: 'Stop working Date' instead of 'Resignation date'
        resign_col = 'Stop working Date' if 'Stop working Date' in df.columns else 'Resignation date'

        # Parse target date
        year, month = year_month.split('-')
        target_date = pd.Timestamp(f"{year}-{month}-01")

        # Employees without resignation date OR resignation date after target month
        active = df[
            (df[resign_col].isna()) |
            (pd.to_datetime(df[resign_col], errors='coerce') > target_date)
        ]

        return len(active)

    def _calc_absence_rate(self, df: pd.DataFrame) -> float:
        """
        Calculate absence rate from attendance data
        출석 데이터에서 결근율 계산

        NOTE: This is a reference implementation. The actual calculation is
        performed in HRMetricCalculator._absence_rate() which uses the
        consolidated attendance data with proper column mappings.
        참고: 실제 계산은 HRMetricCalculator._absence_rate()에서 수행됩니다.
        """
        if df.empty:
            return 0.0

        # Reference implementation - not used in production
        # Actual implementation in HRMetricCalculator handles:
        # - Maternity/pregnancy exclusions
        # - Proper working day calculations
        # - Absence categorization (authorized/unauthorized)
        return 0.0

    def _calc_unauthorized_absence_rate(self, df: pd.DataFrame) -> float:
        """
        Calculate unauthorized absence rate
        무단 결근율 계산

        NOTE: This is a reference implementation. The actual calculation is
        performed in HRMetricCalculator using absence_data categorization.
        참고: 실제 계산은 HRMetricCalculator에서 수행됩니다.
        """
        if df.empty:
            return 0.0

        # Reference implementation - not used in production
        # See HRMetricCalculator for actual implementation
        return 0.0

    def _calc_resignation_rate(self, df: pd.DataFrame, year_month: str) -> float:
        """Calculate resignation rate for the month"""
        if df.empty:
            return 0.0

        year, month = year_month.split('-')
        month_num = int(month)

        # Resignations in this month
        resignations = df[
            (pd.to_datetime(df['Resignation date'], errors='coerce').dt.month == month_num) &
            (pd.to_datetime(df['Resignation date'], errors='coerce').dt.year == int(year))
        ]

        total_active = self._calc_total_employees(df, year_month)

        if total_active == 0:
            return 0.0

        return (len(resignations) / total_active) * 100

    def _calc_recent_hires(self, df: pd.DataFrame, year_month: str) -> int:
        """Calculate new hires in the target month"""
        if df.empty:
            return 0

        year, month = year_month.split('-')
        month_num = int(month)

        # Join date in this month
        hires = df[
            (pd.to_datetime(df['Join Date'], errors='coerce').dt.month == month_num) &
            (pd.to_datetime(df['Join Date'], errors='coerce').dt.year == int(year))
        ]

        return len(hires)

    def _calc_recent_resignations(self, df: pd.DataFrame, year_month: str) -> int:
        """Calculate resignations in the target month"""
        if df.empty:
            return 0

        year, month = year_month.split('-')
        month_num = int(month)

        # Resignation date in this month
        resignations = df[
            (pd.to_datetime(df['Resignation date'], errors='coerce').dt.month == month_num) &
            (pd.to_datetime(df['Resignation date'], errors='coerce').dt.year == int(year))
        ]

        return len(resignations)

    def _calc_under_60_days(self, df: pd.DataFrame, year_month: str) -> int:
        """Calculate employees with tenure < 60 days"""
        if df.empty:
            return 0

        year, month = year_month.split('-')
        end_of_month = pd.Timestamp(f"{year}-{month}-01") + pd.DateOffset(months=1) - pd.DateOffset(days=1)

        join_dates = pd.to_datetime(df['Join Date'], errors='coerce')
        tenure_days = (end_of_month - join_dates).dt.days

        under_60 = df[tenure_days < 60]

        return len(under_60)

    def _calc_post_assignment_resignations(self, df: pd.DataFrame) -> int:
        """Calculate employees who resigned after assignment"""
        if df.empty:
            return 0

        # Has both Assignment date and Resignation date
        post_assignment = df[
            df['Assignment date'].notna() &
            df['Resignation date'].notna()
        ]

        return len(post_assignment)

    def _calc_perfect_attendance(self, df: pd.DataFrame) -> int:
        """
        Calculate employees with perfect attendance
        개근 직원 수 계산

        NOTE: This is a reference implementation. The actual calculation is
        performed in HRMetricCalculator._perfect_attendance() which uses:
        - working_days == attendance_days
        - absent_days == 0
        - unauthorized_absent_days == 0
        참고: 실제 계산은 HRMetricCalculator._perfect_attendance()에서 수행됩니다.
        """
        if df.empty:
            return 0

        # Reference implementation - not used in production
        # See HRMetricCalculator for actual implementation
        return 0

    def _calc_long_term_employees(self, df: pd.DataFrame, year_month: str) -> int:
        """Calculate employees with 1+ year tenure"""
        if df.empty:
            return 0

        year, month = year_month.split('-')
        reference_date = pd.Timestamp(f"{year}-{month}-01")

        join_dates = pd.to_datetime(df['Join Date'], errors='coerce')
        tenure_days = (reference_date - join_dates).dt.days

        long_term = df[tenure_days >= 365]

        return len(long_term)

    def _calc_data_errors(self, df: pd.DataFrame) -> int:
        """Calculate number of data errors/anomalies"""
        if df.empty:
            return 0

        error_count = 0

        # Temporal inconsistencies
        join_dates = pd.to_datetime(df['Join Date'], errors='coerce')
        resign_dates = pd.to_datetime(df['Resignation date'], errors='coerce')

        # Resignation before join
        temporal_errors = (resign_dates < join_dates).sum()
        error_count += temporal_errors

        # Missing required fields
        missing_id = df['Employee No'].isna().sum()
        missing_name = df['Employee Name'].isna().sum()
        error_count += missing_id + missing_name

        return error_count

    def get_metric_trend(self, metric_key: str, months: List[str]) -> List[Any]:
        """
        Get trend data for a specific metric across months
        특정 메트릭의 월별 추세 데이터 가져오기

        Args:
            metric_key: Metric identifier (e.g., 'total_employees')
            months: List of months in order

        Returns:
            List of metric values in order
        """
        return [
            self.monthly_metrics.get(month, {}).get(metric_key, 0)
            for month in months
        ]

    def get_month_over_month_change(self, metric_key: str, target_month: str) -> Optional[Dict[str, Any]]:
        """
        Calculate month-over-month change for a metric
        메트릭의 전월 대비 변화 계산

        Args:
            metric_key: Metric identifier
            target_month: Target month in 'YYYY-MM' format

        Returns:
            Dictionary with absolute and percentage change
        """
        if target_month not in self.monthly_metrics:
            return None

        # Find previous month
        all_months = sorted(self.monthly_metrics.keys())
        month_index = all_months.index(target_month)

        if month_index == 0:
            return None  # No previous month

        previous_month = all_months[month_index - 1]

        current_value = self.monthly_metrics[target_month].get(metric_key, 0)
        previous_value = self.monthly_metrics[previous_month].get(metric_key, 0)

        absolute_change = current_value - previous_value

        if previous_value != 0:
            percentage_change = (absolute_change / previous_value) * 100
        else:
            percentage_change = 0.0 if absolute_change == 0 else 100.0

        return {
            'current': current_value,
            'previous': previous_value,
            'absolute': absolute_change,
            'percentage': round(percentage_change, 1)
        }

    def to_json(self) -> str:
        """
        Convert monthly metrics to JSON for JavaScript embedding
        JavaScript 임베딩용 JSON으로 변환
        """
        import json
        return json.dumps(self.monthly_metrics, ensure_ascii=False, indent=2)


def main():
    """Test DynamicMetricCalculator"""
    from pathlib import Path

    hr_root = Path(__file__).parent.parent.parent

    # Initialize data collector
    collector = MonthlyDataCollector(hr_root)
    available_months = collector.detect_available_months()

    print(f"📅 Available months: {available_months}")

    # Calculate metrics for September
    calculator = DynamicMetricCalculator(collector)
    target_month = '2025-09'

    # Calculate for all available months
    all_months = collector.get_month_range(target_month)
    print(f"\n📊 Calculating metrics for: {all_months}")

    metrics = calculator.calculate_all_metrics(all_months)

    print(f"\n✅ Metrics calculated for {len(metrics)} months")

    # Show September metrics
    if target_month in metrics:
        print(f"\n📈 {target_month} Metrics:")
        for key, value in metrics[target_month].items():
            print(f"  {key}: {value}")

        # Show month-over-month changes
        print(f"\n📊 Month-over-Month Changes:")
        for metric_key in ['total_employees', 'recent_hires', 'recent_resignations']:
            change = calculator.get_month_over_month_change(metric_key, target_month)
            if change:
                print(f"  {metric_key}: {change['current']} ({change['absolute']:+d}, {change['percentage']:+.1f}%)")


if __name__ == '__main__':
    main()
