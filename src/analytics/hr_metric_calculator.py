"""
hr_metric_calculator.py - HR Dashboard Metric Calculator (Complete Rebuild)
HR 대시보드 메트릭 계산기 (완전 재구축)

Optimized for HR Dashboard data structure
HR 대시보드 데이터 구조에 최적화
"""

import pandas as pd
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data.monthly_data_collector import MonthlyDataCollector
    from src.utils.employee_counter import count_employees_by_month
    from src.utils.date_handler import parse_entrance_date, parse_stop_date, parse_date_column
else:
    from ..data.monthly_data_collector import MonthlyDataCollector
    from ..utils.employee_counter import count_employees_by_month
    from ..utils.date_handler import parse_entrance_date, parse_stop_date, parse_date_column


class HRMetricCalculator:
    """
    Calculate HR metrics dynamically for all available months
    사용 가능한 모든 월에 대해 동적으로 HR 메트릭 계산

    Includes caching mechanism for performance optimization
    성능 최적화를 위한 캐싱 메커니즘 포함
    """

    # Class-level cache for metrics (shared across instances)
    # 클래스 수준 메트릭 캐시 (인스턴스 간 공유)
    _metrics_cache: Dict[str, Dict[str, Any]] = {}
    _cache_timestamps: Dict[str, datetime] = {}
    _cache_ttl_minutes: int = 30  # Cache TTL in minutes / 캐시 TTL (분)

    def __init__(self, data_collector: MonthlyDataCollector, report_date: Optional[datetime] = None):
        self.data_collector = data_collector
        self.monthly_metrics: Dict[str, Dict[str, Any]] = {}
        # Report generation date (default: today)
        self.report_date = report_date if report_date else datetime.now()
        # Load config thresholds / 설정 임계치 로드
        self._config = self._load_config()
        self._thresholds = self._config.get('thresholds', {})
        # Load absence reason patterns from config / 결근 사유 패턴 설정 로드
        self._absence_patterns = self._config.get('absence_reason_patterns', {})
        self._maternity_keywords = self._absence_patterns.get('maternity', {}).get('keywords',
            ['Thai sản', 'Sinh', 'sinh', 'Dưỡng sinh', 'Khám thai'])
        self._unauthorized_keywords = self._absence_patterns.get('unauthorized', {}).get('keywords',
            ['AR1', 'AR2', 'Không phép', 'Vắng không phép', 'Unauthorized'])
        self._annual_leave_keywords = self._absence_patterns.get('annual_leave', {}).get('keywords',
            ['Phép năm', 'Annual leave', 'Nghỉ phép', 'AL'])
        self._sick_leave_keywords = self._absence_patterns.get('sick_leave', {}).get('keywords',
            ['Ốm đau', 'Sick leave', 'Bệnh', 'Sick', 'SL'])
        # Performance config / 성능 설정
        self._cache_enabled = self._config.get('performance', {}).get('cache_data', True)
        cache_ttl = self._config.get('performance', {}).get('cache_ttl_minutes', 30)
        HRMetricCalculator._cache_ttl_minutes = cache_ttl

    def _load_config(self) -> Dict[str, Any]:
        """
        Load metric definitions config
        메트릭 정의 설정 로드
        """
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "metric_definitions.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load config: {e}")
            return {}

    def _get_threshold(self, key: str, default: Any = None) -> Any:
        """
        Get threshold value from config with fallback
        설정에서 임계치 값 가져오기 (대체값 포함)
        """
        return self._thresholds.get(key, default)

    def _get_cache_key(self, year_month: str) -> str:
        """
        Generate cache key for a specific month
        특정 월에 대한 캐시 키 생성
        """
        return f"{year_month}_{self.report_date.strftime('%Y%m%d')}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cached metrics are still valid
        캐시된 메트릭이 아직 유효한지 확인
        """
        if not self._cache_enabled:
            return False

        if cache_key not in self._metrics_cache:
            return False

        cached_time = self._cache_timestamps.get(cache_key)
        if not cached_time:
            return False

        elapsed_minutes = (datetime.now() - cached_time).total_seconds() / 60
        return elapsed_minutes < self._cache_ttl_minutes

    def _cache_metrics(self, cache_key: str, metrics: Dict[str, Any]) -> None:
        """
        Store metrics in cache
        메트릭을 캐시에 저장
        """
        if self._cache_enabled:
            HRMetricCalculator._metrics_cache[cache_key] = metrics.copy()
            HRMetricCalculator._cache_timestamps[cache_key] = datetime.now()

    def _get_cached_metrics(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metrics from cache if valid
        유효한 경우 캐시에서 메트릭 검색
        """
        if self._is_cache_valid(cache_key):
            return self._metrics_cache.get(cache_key, {}).copy()
        return None

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all cached metrics (useful for force refresh)
        모든 캐시된 메트릭 삭제 (강제 새로고침 시 유용)
        """
        cls._metrics_cache.clear()
        cls._cache_timestamps.clear()

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get cache statistics for debugging
        디버깅용 캐시 통계 반환
        """
        return {
            'cached_months': len(cls._metrics_cache),
            'cache_keys': list(cls._metrics_cache.keys()),
            'cache_enabled': True,
            'ttl_minutes': cls._cache_ttl_minutes
        }

    def calculate_all_metrics(self, months: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate metrics for all specified months with caching
        캐싱을 사용하여 지정된 모든 월에 대한 메트릭 계산
        """
        cache_hits = 0
        cache_misses = 0

        for month in months:
            cache_key = self._get_cache_key(month)
            cached = self._get_cached_metrics(cache_key)

            if cached:
                self.monthly_metrics[month] = cached
                cache_hits += 1
            else:
                metrics = self._calculate_month(month)
                self.monthly_metrics[month] = metrics
                self._cache_metrics(cache_key, metrics)
                cache_misses += 1

        # Log cache performance (only if there's activity)
        # 캐시 성능 로그 (활동이 있는 경우에만)
        if cache_hits > 0 or cache_misses > 0:
            total = cache_hits + cache_misses
            hit_rate = (cache_hits / total * 100) if total > 0 else 0
            print(f"📊 Metric cache: {cache_hits} hits, {cache_misses} misses ({hit_rate:.0f}% hit rate)")

        return self.monthly_metrics

    def _calculate_month(self, year_month: str) -> Dict[str, Any]:
        """Calculate all metrics for a specific month"""
        data = self.data_collector.load_month_data(year_month)
        df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        if df.empty:
            return self._empty_metrics()

        # Add Team column if not present
        # Team 컬럼이 없으면 추가
        if 'Team' not in df.columns:
            df = self._add_team_column(df)

        year, month = year_month.split('-')
        month_num = int(month)
        year_num = int(year)

        return {
            'total_employees': self._total_employees(df, year_num, month_num),
            'total_employees_incentive': self._total_employees_incentive_basis(df, year_num, month_num),
            'absence_rate': self._absence_rate(attendance_df, df, year_num, month_num),
            'absence_rate_all': self._absence_rate_all(attendance_df, df, year_num, month_num),
            'absence_rate_excl_maternity': self._absence_rate_excl_maternity(attendance_df, df, year_num, month_num),
            'unauthorized_absence_rate': self._unauthorized_absence_rate(attendance_df, df, year_num, month_num),
            'team_unauthorized_rates': self._team_unauthorized_absence_rates(attendance_df, df, year_num, month_num),
            'team_absence_rates_excl_maternity': self._team_absence_rates_excl_maternity(attendance_df, df, year_num, month_num),
            'type_absence_rates_excl_maternity': self._type_absence_rates_excl_maternity(attendance_df, df, year_num, month_num),
            'team_absence_breakdown': self._team_absence_breakdown(attendance_df, df, year_num, month_num),
            'resignation_rate': self._resignation_rate(df, year_num, month_num),
            'team_resignation_rates': self._team_resignation_rates(df, year_num, month_num),
            'recent_hires': self._recent_hires(df, year_num, month_num),
            'recent_resignations': self._recent_resignations(df, year_num, month_num),
            'maternity_leave_count': self._maternity_leave_count(attendance_df),
            'under_60_days': self._under_60_days(df, year_num, month_num),
            'post_assignment_resignations': self._post_assignment_resignations(df, year_num, month_num),
            'perfect_attendance': self._perfect_attendance(attendance_df, df),
            'long_term_employees': self._long_term_employees(df, year_num, month_num),
            'data_errors': self._data_errors(df),
            'average_incentive': self._average_incentive(df, year_num, month_num),
            'total_incentive': self._total_incentive(df, year_num, month_num),
            'tenure_distribution': self._tenure_distribution(df, year_num, month_num),
            'pregnant_employees': self._pregnant_employees(df),
            # New KPI Metrics / 새로운 KPI 메트릭
            'average_tenure_days': self._average_tenure_days(df, year_num, month_num),
            'early_resignation_30': self._early_resignation_rate(df, year_num, month_num, 30),
            'early_resignation_60': self._early_resignation_rate(df, year_num, month_num, 60),
            'early_resignation_90': self._early_resignation_rate(df, year_num, month_num, 90),
            'retention_rate': self._retention_rate(df, year_num, month_num),
            'attendance_rate': self._attendance_rate(attendance_df, df, year_num, month_num),
            'weekly_metrics': self._calculate_weekly_metrics(df, attendance_df, year_num, month_num),
            'daily_metrics': self._calculate_daily_metrics(df, attendance_df, year_num, month_num)
        }

    def _add_team_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract team name from position columns
        직급 컬럼에서 팀 이름 추출

        Args:
            df: DataFrame with position columns

        Returns:
            DataFrame with 'Team' column added
        """
        df = df.copy()

        # Check which position column exists
        position_col = None
        for col in ['QIP POSITION 3RD  NAME', 'QIP POSITION 2ND  NAME', 'Position']:
            if col in df.columns:
                position_col = col
                break

        if position_col is None:
            df['Team'] = 'UNKNOWN'
            return df

        # Extract team from position
        def extract_team(position_str):
            if pd.isna(position_str):
                return 'UNKNOWN'

            position = str(position_str).upper()

            # Team mapping based on keywords
            if 'ASSEMBLY' in position:
                return 'ASSEMBLY'
            elif 'STITCHING' in position:
                return 'STITCHING'
            elif 'CUTTING' in position:
                return 'CUTTING'
            elif 'LASTING' in position:
                return 'LASTING'
            elif 'STOCKFITTING' in position or 'STOCK' in position:
                return 'STOCKFITTING'
            elif 'BOTTOM' in position or 'OUTSOLE' in position:
                return 'BOTTOM'
            elif 'QSC' in position or 'QC' in position or 'QUALITY' in position:
                return 'QSC'
            elif 'MATERIAL' in position or 'MTL' in position or 'TEXTILE' in position or 'LEATHER' in position:
                return 'MTL'
            elif 'REPACKING' in position or 'PACKING' in position:
                return 'REPACKING'
            elif 'OSC' in position or 'INCOMING' in position:
                return 'OSC'
            elif 'QA' in position:
                return 'QA'
            elif 'NEW' in position:
                return 'NEW'
            else:
                return 'QIP_MANAGER_OFFICE_OCPT'

        df['Team'] = df[position_col].apply(extract_team)
        return df

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics when no data"""
        return {k: 0 for k in [
            'total_employees', 'absence_rate', 'absence_rate_excl_maternity',
            'unauthorized_absence_rate', 'resignation_rate', 'recent_hires',
            'recent_resignations', 'maternity_leave_count', 'under_60_days',
            'post_assignment_resignations', 'perfect_attendance',
            'long_term_employees', 'data_errors'
        ]}

    def _total_employees(self, df: pd.DataFrame, year: int, month: int) -> int:
        """Total active employees at report generation date (보고서 생성일 기준 재직자)

        For HR management: Current headcount at report generation date
        보고서 생성일 기준 실제 재직 인원

        Uses employee_counter utility for standardized counting logic
        """
        year_month = f"{year}-{month:02d}"
        return count_employees_by_month(df, year_month, self.report_date)

    def _total_employees_incentive_basis(self, df: pd.DataFrame, year: int, month: int) -> int:
        """Total employees for incentive calculation (인센티브 계산 기준)

        For incentive: Anyone who worked during the month
        해당 월에 근무한 모든 직원 (월초 기준)

        Includes employees who resigned during the month
        월 중 퇴사자 포함
        """
        month_start = pd.Timestamp(f"{year}-{month:02d}-01")

        # Active: No stop date OR stop date >= month start
        stop_dates = parse_stop_date(df)
        active = df[(stop_dates.isna()) | (stop_dates >= month_start)]

        return len(active)

    def _resignation_rate(self, df: pd.DataFrame, year: int, month: int) -> float:
        """Resignation rate (퇴사율) - Improved formula using monthly average headcount
        월평균 인원을 사용한 개선된 퇴사율 계산

        Formula: (Monthly resignations / Average monthly headcount) * 100
        공식: (월 중 퇴사자 수 / 월평균 인원) * 100
        """
        # Calculate month boundaries
        month_start = pd.Timestamp(f"{year}-{month:02d}-01")
        month_end = month_start + pd.DateOffset(months=1) - pd.DateOffset(days=1)

        # Parse dates
        entrance_dates = parse_entrance_date(df)
        stop_dates = parse_stop_date(df)

        # Calculate employees at month start
        # 월초 재직자: 월초 이전 입사 & (퇴사 안함 OR 월초 이후 퇴사)
        employees_at_month_start = df[
            (entrance_dates <= month_start) &
            ((stop_dates.isna()) | (stop_dates >= month_start))
        ]

        # Calculate employees at month end
        # 월말 재직자: 월말 이전 입사 & (퇴사 안함 OR 월말 이후 퇴사)
        employees_at_month_end = df[
            (entrance_dates <= month_end) &
            ((stop_dates.isna()) | (stop_dates > month_end))
        ]

        # Calculate average monthly headcount
        # 월평균 인원 = (월초 인원 + 월말 인원) / 2
        avg_headcount = (len(employees_at_month_start) + len(employees_at_month_end)) / 2

        if avg_headcount == 0:
            return 0.0

        # Count resignations in this month
        resigned_in_month = df[
            (stop_dates >= month_start) &
            (stop_dates <= month_end)
        ]

        # Calculate resignation rate
        resignation_rate = (len(resigned_in_month) / avg_headcount) * 100

        return round(resignation_rate, 1)

    def _team_resignation_rates(self, df: pd.DataFrame, year: int, month: int) -> Dict[str, float]:
        """Calculate resignation rate by team
        팀별 퇴사율 계산

        Returns:
            Dictionary with team names as keys and resignation rates as values
            팀명을 키로, 퇴사율을 값으로 하는 딕셔너리
        """
        if 'Team' not in df.columns:
            return {}

        # Calculate month boundaries
        month_start = pd.Timestamp(f"{year}-{month:02d}-01")
        month_end = month_start + pd.DateOffset(months=1) - pd.DateOffset(days=1)

        # Parse dates
        entrance_dates = parse_entrance_date(df)
        stop_dates = parse_stop_date(df)

        team_rates = {}

        for team in df['Team'].unique():
            if pd.isna(team):
                continue

            team_df = df[df['Team'] == team].copy()
            team_entrance = entrance_dates[team_df.index]
            team_stop = stop_dates[team_df.index]

            # Calculate employees at month start for this team
            employees_at_month_start = team_df[
                (team_entrance <= month_start) &
                ((team_stop.isna()) | (team_stop >= month_start))
            ]

            # Calculate employees at month end for this team
            employees_at_month_end = team_df[
                (team_entrance <= month_end) &
                ((team_stop.isna()) | (team_stop > month_end))
            ]

            # Calculate average monthly headcount for team
            avg_headcount = (len(employees_at_month_start) + len(employees_at_month_end)) / 2

            if avg_headcount == 0:
                team_rates[team] = 0.0
                continue

            # Count resignations in this month for this team
            resigned_in_month = team_df[
                (team_stop >= month_start) &
                (team_stop <= month_end)
            ]

            # Calculate resignation rate for team
            resignation_rate = (len(resigned_in_month) / avg_headcount) * 100
            team_rates[team] = round(resignation_rate, 1)

        return team_rates

    def _recent_hires(self, df: pd.DataFrame, year: int, month: int) -> int:
        """New hires in target month (신규 입사자)"""
        entrance_dates = parse_entrance_date(df)
        hires = df[
            (entrance_dates.dt.year == year) &
            (entrance_dates.dt.month == month)
        ]
        return len(hires)

    def _recent_resignations(self, df: pd.DataFrame, year: int, month: int) -> int:
        """Resignations in target month (퇴사자)"""
        stop_dates = parse_stop_date(df)
        resigned = df[
            (stop_dates.dt.year == year) &
            (stop_dates.dt.month == month)
        ]
        return len(resigned)

    def _under_60_days(self, df: pd.DataFrame, year: int, month: int) -> int:
        """Employees with tenure < 60 days (60일 미만) - ACTIVE EMPLOYEES ONLY

        Only counts employees who are active at report generation date
        보고서 생성일 기준 재직자만 포함
        """
        end_of_month = pd.Timestamp(f"{year}-{month:02d}-01") + pd.DateOffset(months=1) - pd.DateOffset(days=1)
        entrance_dates = parse_entrance_date(df)
        stop_dates = parse_stop_date(df)

        tenure_days = (end_of_month - entrance_dates).dt.days

        # Filter for active employees AND tenure < 60 days
        under_60 = df[
            (tenure_days < 60) &
            ((stop_dates.isna()) | (stop_dates > self.report_date))
        ]

        return len(under_60)

    def _post_assignment_resignations(self, df: pd.DataFrame, year: int, month: int) -> int:
        """Employees who resigned between 30-60 days after hire (배치 후 퇴사)

        Counts employees who resigned this month with tenure between 30 and 60 days.
        This indicates early turnover after initial assignment/training period.
        해당 월에 퇴사한 직원 중 입사 후 30~60일 사이에 퇴사한 직원 수

        Assumptions / 가정:
        - Assignment typically happens ~30 days after hire / 배정은 보통 입사 후 30일 경에 발생
        - Resignations between 30-60 days indicate post-assignment issues / 30-60일 사이 퇴사는 배정 후 문제 의미
        """
        stop_dates = parse_stop_date(df)
        entrance_dates = parse_entrance_date(df)

        # Calculate tenure at resignation
        # 퇴사 시점의 근속일수 계산
        tenure_at_resignation = (stop_dates - entrance_dates).dt.days

        # Filter for resignations this month with tenure 30-60 days
        # 해당 월 퇴사자 중 근속 30-60일인 직원
        post_assignment = df[
            (stop_dates.dt.year == year) &
            (stop_dates.dt.month == month) &
            (tenure_at_resignation > 30) &
            (tenure_at_resignation <= 60)
        ]

        return len(post_assignment)

    def _long_term_employees(self, df: pd.DataFrame, year: int, month: int) -> int:
        """Employees with 1+ year tenure (장기근속자) - ACTIVE EMPLOYEES ONLY

        Only counts employees who are active at report generation date
        보고서 생성일 기준 재직자만 포함
        """
        reference_date = pd.Timestamp(f"{year}-{month:02d}-01")
        entrance_dates = parse_entrance_date(df)
        stop_dates = parse_stop_date(df)

        tenure_days = (reference_date - entrance_dates).dt.days

        # Filter for active employees AND tenure >= long_term_employee_days (from config)
        # 재직자 중 장기근속 임계치 이상인 직원 필터링 (설정에서 가져옴)
        long_term_days = self._get_threshold('long_term_employee_days', 365)
        long_term = df[
            (tenure_days >= long_term_days) &
            ((stop_dates.isna()) | (stop_dates > self.report_date))
        ]

        return len(long_term)

    def _absence_rate(self, attendance_df: pd.DataFrame, df: pd.DataFrame, year: int, month: int) -> float:
        """Calculate absence rate (결근율) from attendance data - EXCLUDES resigned employees

        Only includes attendance records for employees who are active at report generation date
        보고서 생성일 기준 재직자만 포함
        """
        if attendance_df.empty or 'compAdd' not in attendance_df.columns or 'ID No' not in attendance_df.columns:
            return 0.0

        # Get active employee IDs at report generation date
        stop_dates = parse_stop_date(df)
        active_employees = df[(stop_dates.isna()) | (stop_dates > self.report_date)]
        active_ids = set(active_employees['Employee No'].dropna())

        # Filter attendance records to only include active employees
        filtered_attendance = attendance_df[attendance_df['ID No'].isin(active_ids)]

        if filtered_attendance.empty:
            return 0.0

        total_records = len(filtered_attendance)
        absences = len(filtered_attendance[filtered_attendance['compAdd'] == 'Vắng mặt'])

        if total_records == 0:
            return 0.0

        return round((absences / total_records) * 100, 1)

    def _absence_rate_all(self, attendance_df: pd.DataFrame, df: pd.DataFrame, year: int, month: int) -> float:
        """Calculate absence rate (결근율) INCLUDING resigned employees
        퇴사자를 포함한 전체 직원의 결근율 계산

        Includes all employees who worked during the month (more accurate for monthly performance)
        월 중 근무한 모든 직원 포함 (월별 성과 측정에 더 정확)
        """
        if attendance_df.empty or 'compAdd' not in attendance_df.columns:
            return 0.0

        # Include ALL attendance records for the month
        total_records = len(attendance_df)
        absences = len(attendance_df[attendance_df['compAdd'] == 'Vắng mặt'])

        if total_records == 0:
            return 0.0

        return round((absences / total_records) * 100, 1)

    def _absence_rate_excl_maternity(self, attendance_df: pd.DataFrame, df: pd.DataFrame, year: int, month: int) -> float:
        """Calculate absence rate excluding maternity leave (출산휴가 제외 시 결근율) - EXCLUDES resigned employees

        Only includes attendance records for employees who are active at report generation date
        보고서 생성일 기준 재직자만 포함

        Formula: (absences - maternity) / (total_records - maternity) * 100
        """
        if attendance_df.empty or 'compAdd' not in attendance_df.columns or 'ID No' not in attendance_df.columns:
            return 0.0

        # Get active employee IDs at report generation date
        stop_dates = parse_stop_date(df)
        active_employees = df[(stop_dates.isna()) | (stop_dates > self.report_date)]
        active_ids = set(active_employees['Employee No'].dropna())

        # Filter attendance records to only include active employees
        filtered_attendance = attendance_df[attendance_df['ID No'].isin(active_ids)]

        if filtered_attendance.empty:
            return 0.0

        total_records = len(filtered_attendance)

        # Get all absences
        absences_df = filtered_attendance[filtered_attendance['compAdd'] == 'Vắng mặt']
        total_absences = len(absences_df)

        if 'Reason Description' not in filtered_attendance.columns:
            # If no reason description, return regular absence rate
            return round((total_absences / total_records) * 100, 1) if total_records > 0 else 0.0

        # Count maternity leave records
        maternity_keywords = ['Thai sản', 'Sinh', 'sinh', 'Dưỡng sinh', 'Khám thai']

        # Count maternity absences
        maternity_absences = absences_df[
            absences_df['Reason Description'].str.contains(
                '|'.join(maternity_keywords), na=False, case=False
            )
        ]
        maternity_count = len(maternity_absences)

        # Calculate: non-maternity absences / (total records - maternity records)
        non_maternity_absences = total_absences - maternity_count
        denominator = total_records - maternity_count

        if denominator <= 0:
            return 0.0

        return round((non_maternity_absences / denominator) * 100, 1)

    def _unauthorized_absence_rate(self, attendance_df: pd.DataFrame, df: pd.DataFrame, year: int, month: int) -> float:
        """Calculate unauthorized absence rate (무단결근율) - EXCLUDES resigned employees

        Only includes attendance records for employees who are active at report generation date
        보고서 생성일 기준 재직자만 포함
        """
        if attendance_df.empty or 'Reason Description' not in attendance_df.columns or 'ID No' not in attendance_df.columns:
            return 0.0

        # Get active employee IDs at report generation date
        stop_dates = parse_stop_date(df)
        active_employees = df[(stop_dates.isna()) | (stop_dates > self.report_date)]
        active_ids = set(active_employees['Employee No'].dropna())

        # Filter attendance records to only include active employees
        filtered_attendance = attendance_df[attendance_df['ID No'].isin(active_ids)]

        if filtered_attendance.empty:
            return 0.0

        total_records = len(filtered_attendance)

        # Expanded unauthorized absence codes (AR1, AR2, and variations)
        unauthorized_patterns = ['AR1', 'AR2', 'Không phép', 'Vắng không phép', 'Unauthorized']
        pattern = '|'.join(unauthorized_patterns)

        unauthorized = len(filtered_attendance[
            filtered_attendance['Reason Description'].str.contains(pattern, na=False, case=False)
        ])

        if total_records == 0:
            return 0.0

        return round((unauthorized / total_records) * 100, 2)

    def _team_unauthorized_absence_rates(self, attendance_df: pd.DataFrame, df: pd.DataFrame, year: int, month: int) -> Dict[str, float]:
        """Calculate unauthorized absence rate by team (팀별 무단결근율)

        Returns dictionary with team names as keys and rates as values
        """
        if attendance_df.empty or df.empty:
            return {}

        # Get active employees with their teams
        stop_dates = parse_stop_date(df)
        active_employees = df[(stop_dates.isna()) | (stop_dates > self.report_date)].copy()

        # Team mapping from position data
        team_rates = {}

        # Define team positions mapping (same as used in dashboard)
        team_mappings = {
            'ASSEMBLY': ['ASSEMBLY', 'ASSEMBLY LINE'],
            'STITCHING': ['STITCHING', 'SEWING'],
            'CUTTING': ['CUTTING'],
            'LASTING': ['LASTING'],
            'STOCKFITTING': ['STOCKFITTING', 'STOCK'],
            'BOTTOM': ['BOTTOM', 'OUTSOLE'],
            'QSC': ['QSC', 'QUALITY'],
            'MTL': ['MTL', 'MATERIAL'],
            'NEW': ['NEW'],
            'REPACKING': ['REPACKING', 'PACKING'],
            'AQL': ['AQL', 'AUDIT'],
            'QA': ['QA', 'QUALITY ASSURANCE'],
            'QIP_MANAGER_OFFICE_OCPT': ['QIP', 'MANAGER', 'OFFICE', 'OCPT']
        }

        for team_name, keywords in team_mappings.items():
            # Find employees belonging to this team
            team_employees = active_employees[
                active_employees['QIP POSITION 2ND  NAME'].str.contains('|'.join(keywords), na=False, case=False) |
                active_employees['QIP POSITION 3RD  NAME'].str.contains('|'.join(keywords), na=False, case=False)
            ]

            if team_employees.empty:
                team_rates[team_name] = 0.0
                continue

            team_ids = set(team_employees['Employee No'].dropna())

            # Filter attendance for this team
            team_attendance = attendance_df[attendance_df['ID No'].isin(team_ids)]

            if team_attendance.empty:
                team_rates[team_name] = 0.0
                continue

            total_records = len(team_attendance)

            # Check for unauthorized absences
            if 'Reason Description' in team_attendance.columns:
                unauthorized_patterns = ['AR1', 'AR2', 'Không phép', 'Vắng không phép', 'Unauthorized']
                pattern = '|'.join(unauthorized_patterns)

                unauthorized = len(team_attendance[
                    team_attendance['Reason Description'].str.contains(pattern, na=False, case=False)
                ])
            else:
                unauthorized = 0

            if total_records > 0:
                team_rates[team_name] = round((unauthorized / total_records) * 100, 2)
            else:
                team_rates[team_name] = 0.0

        return team_rates

    def _team_absence_rates_excl_maternity(self, attendance_df: pd.DataFrame, df: pd.DataFrame, year: int, month: int) -> Dict[str, float]:
        """Calculate absence rate excluding maternity leave by team (팀별 출산휴가 제외 결근율)

        Returns dictionary with team names as keys and rates as values
        """
        if attendance_df.empty or df.empty:
            return {}

        # Get active employees with their teams
        stop_dates = parse_stop_date(df)
        active_employees = df[(stop_dates.isna()) | (stop_dates > self.report_date)].copy()

        # Team mapping from position data
        team_rates = {}

        # Define team positions mapping (same as used in dashboard)
        team_mappings = {
            'ASSEMBLY': ['ASSEMBLY', 'ASSEMBLY LINE'],
            'STITCHING': ['STITCHING', 'SEWING'],
            'CUTTING': ['CUTTING'],
            'LASTING': ['LASTING'],
            'STOCKFITTING': ['STOCKFITTING', 'STOCK'],
            'BOTTOM': ['BOTTOM', 'OUTSOLE'],
            'QSC': ['QSC', 'QUALITY'],
            'MTL': ['MTL', 'MATERIAL'],
            'NEW': ['NEW'],
            'REPACKING': ['REPACKING', 'PACKING'],
            'AQL': ['AQL', 'AUDIT'],
            'QA': ['QA', 'QUALITY ASSURANCE'],
            'QIP_MANAGER_OFFICE_OCPT': ['QIP', 'MANAGER', 'OFFICE', 'OCPT']
        }

        # Maternity leave keywords
        maternity_keywords = ['Thai sản', 'Sinh', 'sinh', 'Dưỡng sinh', 'Khám thai']
        maternity_pattern = '|'.join(maternity_keywords)

        for team_name, keywords in team_mappings.items():
            # Find employees belonging to this team
            team_employees = active_employees[
                active_employees['QIP POSITION 2ND  NAME'].str.contains('|'.join(keywords), na=False, case=False) |
                active_employees['QIP POSITION 3RD  NAME'].str.contains('|'.join(keywords), na=False, case=False)
            ]

            if team_employees.empty:
                team_rates[team_name] = 0.0
                continue

            team_ids = set(team_employees['Employee No'].dropna())

            # Filter attendance for this team
            team_attendance = attendance_df[attendance_df['ID No'].isin(team_ids)]

            if team_attendance.empty:
                team_rates[team_name] = 0.0
                continue

            # Calculate absence rate excluding maternity leave
            if 'compAdd' in team_attendance.columns:
                total_records = len(team_attendance)

                # Get all absences for this team
                absence_records = team_attendance[team_attendance['compAdd'] == 'Vắng mặt']
                total_absences = len(absence_records)

                # Count maternity absences if we have reason descriptions
                maternity_count = 0
                if 'Reason Description' in team_attendance.columns and not absence_records.empty:
                    maternity_absences = absence_records[
                        absence_records['Reason Description'].str.contains(
                            maternity_pattern, na=False, case=False
                        )
                    ]
                    maternity_count = len(maternity_absences)

                # Calculate: (total_absences - maternity) / (total_records - maternity) * 100
                non_maternity_absences = total_absences - maternity_count
                denominator = total_records - maternity_count

                if denominator > 0:
                    team_rates[team_name] = round((non_maternity_absences / denominator) * 100, 2)
                else:
                    team_rates[team_name] = 0.0
            else:
                team_rates[team_name] = 0.0

        return team_rates

    def _type_absence_rates_excl_maternity(self, attendance_df: pd.DataFrame, df: pd.DataFrame, year: int, month: int) -> Dict[str, float]:
        """Calculate absence rate by employee TYPE (직원 TYPE별 결근율) - excluding maternity leave

        TYPE is based on ROLE TYPE STD column in basic manpower data:
        - TYPE-1: Employees classified as TYPE-1
        - TYPE-2: Employees classified as TYPE-2
        - TYPE-3: Employees classified as TYPE-3

        Calculation:
        TYPE-X 결근율 = (TYPE-X 직원들의 출산휴가 제외 결근 일수) / (TYPE-X 직원들의 출산휴가 제외 총 근무일) × 100

        Uses total_records approach which automatically accounts for varying working days per employee
        (신규 입사자, 퇴사자 등 직원별 근무일수 차이를 자동 반영)

        Returns dictionary with TYPE names as keys and rates as values
        """
        if attendance_df.empty or 'ID No' not in attendance_df.columns or df.empty:
            return {'TYPE-1': 0.0, 'TYPE-2': 0.0, 'TYPE-3': 0.0}

        # Check if ROLE TYPE STD column exists
        if 'ROLE TYPE STD' not in df.columns:
            # Fallback to 0 if column doesn't exist
            return {'TYPE-1': 0.0, 'TYPE-2': 0.0, 'TYPE-3': 0.0}

        # Get active employees at report generation date
        stop_dates = parse_stop_date(df)
        active_employees = df[(stop_dates.isna()) | (stop_dates > self.report_date)].copy()

        if active_employees.empty:
            return {'TYPE-1': 0.0, 'TYPE-2': 0.0, 'TYPE-3': 0.0}

        # Get maternity patterns to exclude
        maternity_patterns = ['Thai sản', 'Sinh thường', 'sinh', 'Dưỡng sinh', 'Khám thai', 'maternity', '출산']
        maternity_pattern = '|'.join(maternity_patterns)

        # Initialize result dictionary
        type_rates = {}

        # Calculate for each TYPE
        for type_name in ['TYPE-1', 'TYPE-2', 'TYPE-3']:
            # Get employees of this TYPE
            type_employees = active_employees[active_employees['ROLE TYPE STD'] == type_name]

            if type_employees.empty:
                type_rates[type_name] = 0.0
                continue

            # Get employee IDs for this TYPE
            type_employee_ids = set(type_employees['Employee No'].dropna())

            # Filter attendance records for this TYPE's employees
            type_attendance = attendance_df[attendance_df['ID No'].isin(type_employee_ids)]

            if type_attendance.empty:
                type_rates[type_name] = 0.0
                continue

            # Total records for this TYPE (actual working days for all TYPE employees)
            total_records = len(type_attendance)

            # Get absence records only (Vắng mặt)
            type_absences = type_attendance[type_attendance['compAdd'] == 'Vắng mặt']
            total_absences = len(type_absences)

            if 'Reason Description' not in type_attendance.columns:
                # No reason description available, return regular absence rate
                if total_records > 0:
                    type_rates[type_name] = round((total_absences / total_records) * 100, 2)
                else:
                    type_rates[type_name] = 0.0
                continue

            # Count maternity leave records
            maternity_absences = type_absences[
                type_absences['Reason Description'].str.contains(
                    maternity_pattern, na=False, case=False
                )
            ]
            maternity_count = len(maternity_absences)

            # Calculate: non-maternity absences / (total records - maternity records)
            non_maternity_absences = total_absences - maternity_count
            denominator = total_records - maternity_count

            if denominator <= 0:
                type_rates[type_name] = 0.0
                continue

            # Calculate absence rate for this TYPE
            # 결근율 = (출산휴가 제외 결근 일수) / (출산휴가 제외 총 근무일) × 100
            absence_rate = (non_maternity_absences / denominator) * 100
            type_rates[type_name] = round(absence_rate, 2)

        return type_rates

    def _maternity_leave_count(self, attendance_df: pd.DataFrame) -> int:
        """Calculate number of employees on maternity leave (출산 휴가자 수)"""
        if attendance_df.empty or 'Reason Description' not in attendance_df.columns or 'ID No' not in attendance_df.columns:
            return 0

        # Find maternity leave records
        maternity_keywords = ['Sinh', 'sinh', 'Dưỡng sinh', 'Khám thai']
        maternity_mask = attendance_df['Reason Description'].str.contains(
            '|'.join(maternity_keywords), na=False, case=False
        )

        maternity_records = attendance_df[maternity_mask]

        if maternity_records.empty:
            return 0

        # Count unique employees on maternity leave
        maternity_employees = maternity_records['ID No'].nunique()

        return maternity_employees

    def _perfect_attendance(self, attendance_df: pd.DataFrame, df: pd.DataFrame = None) -> int:
        """Calculate employees with perfect attendance (개근 직원) - ACTIVE EMPLOYEES ONLY

        Only counts perfect attendance for employees who are active at report generation date
        보고서 생성일 기준 재직자만 포함
        """
        if attendance_df.empty or 'compAdd' not in attendance_df.columns or 'ID No' not in attendance_df.columns:
            return 0

        # Get active employee IDs at report generation date if df provided
        if df is not None and not df.empty:
            stop_dates = parse_stop_date(df)
            active_employees = df[(stop_dates.isna()) | (stop_dates > self.report_date)]
            active_ids = set(active_employees['Employee No'].dropna())

            # Filter attendance to only include active employees
            attendance_df = attendance_df[attendance_df['ID No'].isin(active_ids)]

        # Find employees who have absence records
        absent_employees = attendance_df[attendance_df['compAdd'] == 'Vắng mặt']['ID No'].unique()
        all_employees = attendance_df['ID No'].unique()

        # Perfect attendance = total employees - employees with absences
        perfect_count = len(set(all_employees) - set(absent_employees))

        return perfect_count

    def _data_errors(self, df: pd.DataFrame) -> int:
        """Count data errors (데이터 오류)"""
        errors = 0

        # Missing critical fields
        errors += df['Employee No'].isna().sum()
        errors += df['Full Name'].isna().sum()

        # Temporal inconsistencies
        entrance = parse_entrance_date(df)
        stop = pd.to_datetime(df['Stop working Date'], errors='coerce')
        errors += ((stop < entrance) & stop.notna()).sum()

        return errors

    def _average_incentive(self, df: pd.DataFrame, year: int, month: int) -> float:
        """Calculate average incentive for active employees (평균 인센티브)"""
        # Get active employees at report date
        stop_dates = parse_stop_date(df)
        active = df[(stop_dates.isna()) | (stop_dates > self.report_date)]

        if active.empty:
            return 0.0

        # Calculate average incentive
        incentive_col = 'Final Incentive amount'
        if incentive_col in active.columns:
            incentives = pd.to_numeric(active[incentive_col], errors='coerce').fillna(0)
            return round(incentives.mean(), 0)

        return 0.0

    def _total_incentive(self, df: pd.DataFrame, year: int, month: int) -> float:
        """Calculate total incentive for active employees (총 인센티브)"""
        # Get active employees at report date
        stop_dates = parse_stop_date(df)
        active = df[(stop_dates.isna()) | (stop_dates > self.report_date)]

        if active.empty:
            return 0.0

        # Calculate total incentive
        incentive_col = 'Final Incentive amount'
        if incentive_col in active.columns:
            incentives = pd.to_numeric(active[incentive_col], errors='coerce').fillna(0)
            return round(incentives.sum(), 0)

        return 0.0

    def _tenure_distribution(self, df: pd.DataFrame, year: int, month: int) -> Dict[str, int]:
        """Calculate tenure distribution (근속 기간 분포)"""
        reference_date = self.report_date
        entrance_dates = parse_entrance_date(df)

        # Get active employees
        stop_dates = parse_stop_date(df)
        active = df[(stop_dates.isna()) | (stop_dates > reference_date)]

        if active.empty:
            return {'under_1yr': 0, '1_to_3yr': 0, '3_to_5yr': 0, 'over_5yr': 0}

        active_entrance = parse_entrance_date(active)
        tenure_days = (reference_date - active_entrance).dt.days

        # Get tenure bucket thresholds from config
        # 설정에서 근속 기간 버킷 임계치 가져오기
        buckets = self._thresholds.get('tenure_buckets', {})
        under_1yr_max = buckets.get('under_1yr', {}).get('max_days', 365)
        yr_1_3_max = buckets.get('1_to_3yr', {}).get('max_days', 1095)
        yr_3_5_max = buckets.get('3_to_5yr', {}).get('max_days', 1825)

        return {
            'under_1yr': len(active[tenure_days < under_1yr_max]),
            '1_to_3yr': len(active[(tenure_days >= under_1yr_max) & (tenure_days < yr_1_3_max)]),
            '3_to_5yr': len(active[(tenure_days >= yr_1_3_max) & (tenure_days < yr_3_5_max)]),
            'over_5yr': len(active[tenure_days >= yr_3_5_max])
        }

    def _pregnant_employees(self, df: pd.DataFrame) -> int:
        """Count pregnant employees (임신 직원 수)"""
        pregnant_col = 'pregnant vacation-yes or no'

        if pregnant_col not in df.columns:
            return 0

        # Get active employees
        stop_dates = parse_stop_date(df)
        active = df[(stop_dates.isna()) | (stop_dates > self.report_date)]

        if active.empty:
            return 0

        # Count employees marked as pregnant
        # Convert to string to handle non-string types
        pregnant_status = active[pregnant_col].astype(str).str.lower()
        pregnant = active[pregnant_status == 'yes']
        return len(pregnant)

    def _calculate_weekly_metrics(self, df: pd.DataFrame, attendance_df: pd.DataFrame, year: int, month: int) -> Dict[str, Dict[str, Any]]:
        """Calculate weekly metrics for the month"""
        import calendar

        # Get the month's date range
        start_date = pd.Timestamp(f"{year}-{month:02d}-01")
        _, last_day = calendar.monthrange(year, month)
        end_date = pd.Timestamp(f"{year}-{month:02d}-{last_day}")

        # Prepare attendance data if available
        if not attendance_df.empty and 'Work Date' in attendance_df.columns:
            attendance_df = attendance_df.copy()
            attendance_df['Date'] = pd.to_datetime(attendance_df['Work Date'], errors='coerce')
            # Filter to current month
            month_attendance = attendance_df[
                (attendance_df['Date'] >= start_date) &
                (attendance_df['Date'] <= end_date)
            ].copy()
        else:
            month_attendance = pd.DataFrame()

        # Calculate weekly metrics
        weekly_metrics = {}
        current_date = start_date
        week_num = 1

        while current_date <= end_date:
            week_end = min(current_date + pd.DateOffset(days=6), end_date)

            # Count employees for this week (use middle of week)
            mid_week = current_date + pd.DateOffset(days=3)

            # Active employees at this point in time
            stop_dates = parse_stop_date(df)
            entrance_dates = parse_entrance_date(df)

            active_employees = df[
                (entrance_dates <= mid_week) &
                ((stop_dates.isna()) | (stop_dates > mid_week))
            ]

            total_employees = len(active_employees)

            # Calculate attendance rate for this week if data available
            attendance_rate = 0.0
            absence_rate = 0.0
            new_hires = 0
            resignations = 0
            has_attendance_data = False

            if not month_attendance.empty:
                week_attendance = month_attendance[
                    (month_attendance['Date'] >= current_date) &
                    (month_attendance['Date'] <= week_end)
                ]

                if not week_attendance.empty and 'compAdd' in week_attendance.columns:
                    has_attendance_data = True
                    total_records = len(week_attendance)
                    absent_records = len(week_attendance[week_attendance['compAdd'] == 'Vắng mặt'])

                    if total_records > 0:
                        attendance_rate = round((1 - absent_records / total_records) * 100, 2)
                        absence_rate = round((absent_records / total_records) * 100, 2)

            # New hires this week
            new_hires = len(df[
                (entrance_dates >= current_date) &
                (entrance_dates <= week_end)
            ])

            # Resignations this week
            resignations = len(df[
                (stop_dates >= current_date) &
                (stop_dates <= week_end)
            ])

            # Skip this week if no attendance data available
            if not has_attendance_data:
                current_date = week_end + pd.DateOffset(days=1)
                week_num += 1
                continue

            # Format date as MM/DD
            date_label = f"{month:02d}/{current_date.day:02d}"

            weekly_metrics[f"Week{week_num}"] = {
                'date': date_label,
                'date_full': current_date.strftime('%Y-%m-%d'),
                'total_employees': total_employees,
                'attendance_rate': attendance_rate,
                'absence_rate': absence_rate,
                'new_hires': new_hires,
                'resignations': resignations
            }

            # Move to next week
            current_date = week_end + pd.DateOffset(days=1)
            week_num += 1

        return weekly_metrics

    def _calculate_daily_metrics(self, df: pd.DataFrame, attendance_df: pd.DataFrame, year: int, month: int) -> Dict[str, Dict[str, Any]]:
        """Calculate daily absence rate metrics for the last 30 days"""
        import calendar
        from datetime import timedelta

        # Calculate last 30 days from report date
        # 보고서 날짜로부터 최근 30일 계산
        end_date = pd.Timestamp(self.report_date.date())
        start_date = end_date - timedelta(days=29)  # 30 days including end date

        # Collect attendance data from multiple months if needed
        # 필요한 경우 여러 월의 출근 데이터 수집
        all_attendance_dfs = []

        # Get previous month's data if start_date is in previous month
        # start_date가 이전 달인 경우 이전 달 데이터 가져오기
        if start_date.month != month or start_date.year != year:
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            prev_month_str = f"{prev_year}-{prev_month:02d}"

            # Load previous month's attendance data
            # 이전 달 출근 데이터 로드
            prev_data = self.data_collector.load_month_data(prev_month_str)
            prev_attendance = prev_data.get('attendance', pd.DataFrame())

            if not prev_attendance.empty and 'Work Date' in prev_attendance.columns:
                prev_attendance = prev_attendance.copy()
                prev_attendance['Date'] = pd.to_datetime(
                    prev_attendance['Work Date'].str.replace('.', '-', regex=False),
                    errors='coerce'
                )
                all_attendance_dfs.append(prev_attendance)

        # Add current month's attendance data
        # 현재 월 출근 데이터 추가
        if not attendance_df.empty and 'Work Date' in attendance_df.columns:
            current_attendance = attendance_df.copy()
            # Convert Work Date from YYYY.MM.DD format to datetime
            # Handle both YYYY.MM.DD and YYYY-MM-DD formats
            current_attendance['Date'] = pd.to_datetime(
                current_attendance['Work Date'].str.replace('.', '-', regex=False),
                errors='coerce'
            )
            all_attendance_dfs.append(current_attendance)

        if not all_attendance_dfs:
            return {}

        # Combine all attendance data
        # 모든 출근 데이터 결합
        combined_attendance = pd.concat(all_attendance_dfs, ignore_index=True)

        # Filter to last 30 days
        # 최근 30일로 필터링
        daily_attendance = combined_attendance[
            (combined_attendance['Date'] >= start_date) &
            (combined_attendance['Date'] <= end_date)
        ].copy()

        # Get active employee IDs at report generation date
        stop_dates = parse_stop_date(df)
        active_employees = df[(stop_dates.isna()) | (stop_dates > self.report_date)]
        active_ids = set(active_employees['Employee No'].dropna())

        # Calculate daily metrics
        daily_metrics = {}

        for single_date in pd.date_range(start=start_date, end=end_date):
            date_str = single_date.strftime('%Y-%m-%d')

            # Filter attendance for this specific day and active employees
            day_attendance = daily_attendance[
                (daily_attendance['Date'] == single_date) &
                (daily_attendance['ID No'].isin(active_ids))
            ]

            if day_attendance.empty:
                continue

            # Calculate absence rates
            total_records = len(day_attendance)
            absences = len(day_attendance[day_attendance['compAdd'] == 'Vắng mặt'])

            absence_rate = round((absences / total_records) * 100, 1) if total_records > 0 else 0.0

            # Calculate maternity-excluded absence rate
            absence_rate_excl = absence_rate  # Default to same as total

            if 'Reason Description' in day_attendance.columns:
                absences_df = day_attendance[day_attendance['compAdd'] == 'Vắng mặt']
                total_absences = len(absences_df)

                # Count maternity absences
                maternity_keywords = ['Thai sản', 'Sinh', 'sinh', 'Dưỡng sinh', 'Khám thai']
                maternity_absences = absences_df[
                    absences_df['Reason Description'].str.contains(
                        '|'.join(maternity_keywords), na=False, case=False
                    )
                ]
                maternity_count = len(maternity_absences)

                # Calculate excluding maternity
                non_maternity_absences = total_absences - maternity_count
                denominator = total_records - maternity_count

                if denominator > 0:
                    absence_rate_excl = round((non_maternity_absences / denominator) * 100, 1)

            daily_metrics[date_str] = {
                'date': single_date.strftime('%m/%d'),
                'absence_rate': absence_rate,
                'absence_rate_excl_maternity': absence_rate_excl,
                'total_records': total_records,
                'absences': absences
            }

        return daily_metrics

    def get_metric_trend(self, metric_key: str, months: List[str]) -> List[Any]:
        """Get trend data for a metric across months"""
        return [
            self.monthly_metrics.get(m, {}).get(metric_key, 0)
            for m in months
        ]

    def get_month_over_month_change(self, metric_key: str, target_month: str) -> Optional[Dict[str, Any]]:
        """Calculate month-over-month change"""
        if target_month not in self.monthly_metrics:
            return None

        all_months = sorted(self.monthly_metrics.keys())
        idx = all_months.index(target_month)

        if idx == 0:
            return None

        prev_month = all_months[idx - 1]
        current = self.monthly_metrics[target_month].get(metric_key, 0)
        previous = self.monthly_metrics[prev_month].get(metric_key, 0)

        absolute = current - previous
        percentage = (absolute / previous * 100) if previous != 0 else (100.0 if absolute > 0 else 0.0)

        return {
            'current': current,
            'previous': previous,
            'absolute': absolute,
            'percentage': round(percentage, 1)
        }

    def _team_absence_breakdown(self, attendance_df: pd.DataFrame, df: pd.DataFrame, year: int, month: int) -> Dict[str, Dict[str, Any]]:
        """Calculate comprehensive team absence breakdown
        팀별 결근 종합 분석

        Returns dictionary with:
        - total_absence_rate: 전체 결근율
        - unauthorized_absence_rate: 무단 결근율
        - authorized_absence_rate: 승인 결근율
        - total_absence_days: 전체 결근 일수
        - unauthorized_days: 무단 결근 일수
        - authorized_days: 승인 결근 일수
        - authorized_breakdown: 승인 결근 사유별 분포
        """
        if attendance_df.empty or df.empty:
            return {}

        # Get active employees
        stop_dates = parse_stop_date(df)
        active_employees = df[(stop_dates.isna()) | (stop_dates > self.report_date)].copy()

        if active_employees.empty:
            return {}

        # Team mapping
        team_mappings = {
            'ASSEMBLY': ['ASSEMBLY', 'ASSEMBLY LINE'],
            'STITCHING': ['STITCHING', 'SEWING'],
            'CUTTING': ['CUTTING'],
            'LASTING': ['LASTING'],
            'STOCKFITTING': ['STOCKFITTING', 'STOCK'],
            'BOTTOM': ['BOTTOM', 'OUTSOLE'],
            'QSC': ['QSC', 'QUALITY'],
            'MTL': ['MTL', 'MATERIAL'],
            'NEW': ['NEW'],
            'REPACKING': ['REPACKING', 'PACKING'],
            'AQL': ['AQL', 'AUDIT'],
            'QA': ['QA', 'QUALITY ASSURANCE'],
            'QIP_MANAGER_OFFICE_OCPT': ['QIP', 'MANAGER', 'OFFICE', 'OCPT']
        }

        # Absence reason patterns
        unauthorized_patterns = ['AR1', 'AR2', 'Không phép', 'Vắng không phép', 'Unauthorized']
        unauthorized_pattern = '|'.join(unauthorized_patterns)

        # Authorized absence reason categories
        maternity_patterns = ['Thai sản', 'Sinh thường', 'sinh', 'Dưỡng sinh', 'Khám thai', 'maternity', '출산']
        annual_leave_patterns = ['Phép năm', 'Annual leave', 'Nghỉ phép']
        sick_leave_patterns = ['Ốm đau', 'Sick leave', 'Bệnh', 'Sick']

        team_breakdown = {}

        for team_name, keywords in team_mappings.items():
            # Find team employees
            team_employees = active_employees[
                active_employees['QIP POSITION 2ND  NAME'].str.contains('|'.join(keywords), na=False, case=False) |
                active_employees['QIP POSITION 3RD  NAME'].str.contains('|'.join(keywords), na=False, case=False)
            ]

            if team_employees.empty:
                team_breakdown[team_name] = {
                    'total_absence_rate': 0.0,
                    'unauthorized_absence_rate': 0.0,
                    'authorized_absence_rate': 0.0,
                    'total_absence_days': 0,
                    'unauthorized_days': 0,
                    'authorized_days': 0,
                    'authorized_breakdown': {
                        'maternity': 0,
                        'annual_leave': 0,
                        'sick_leave': 0,
                        'other': 0
                    }
                }
                continue

            team_ids = set(team_employees['Employee No'].dropna())
            team_attendance = attendance_df[attendance_df['ID No'].isin(team_ids)]

            if team_attendance.empty or 'compAdd' not in team_attendance.columns:
                team_breakdown[team_name] = {
                    'total_absence_rate': 0.0,
                    'unauthorized_absence_rate': 0.0,
                    'authorized_absence_rate': 0.0,
                    'total_absence_days': 0,
                    'unauthorized_days': 0,
                    'authorized_days': 0,
                    'authorized_breakdown': {
                        'maternity': 0,
                        'annual_leave': 0,
                        'sick_leave': 0,
                        'other': 0
                    }
                }
                continue

            # Calculate total records and absences
            total_records = len(team_attendance)
            all_absences = team_attendance[team_attendance['compAdd'] == 'Vắng mặt']
            total_absence_days = len(all_absences)

            # Unauthorized absences
            unauthorized_days = 0
            if 'Reason Description' in team_attendance.columns:
                unauthorized_absences = all_absences[
                    all_absences['Reason Description'].str.contains(
                        unauthorized_pattern, na=False, case=False
                    )
                ]
                unauthorized_days = len(unauthorized_absences)

            # Authorized absences (total - unauthorized)
            authorized_days = total_absence_days - unauthorized_days

            # Break down authorized absences by reason
            authorized_breakdown = {
                'maternity': 0,
                'annual_leave': 0,
                'sick_leave': 0,
                'other': 0
            }

            if 'Reason Description' in all_absences.columns and not all_absences.empty:
                # Maternity leave
                maternity_count = len(all_absences[
                    all_absences['Reason Description'].str.contains(
                        '|'.join(maternity_patterns), na=False, case=False
                    )
                ])
                authorized_breakdown['maternity'] = maternity_count

                # Annual leave
                annual_count = len(all_absences[
                    all_absences['Reason Description'].str.contains(
                        '|'.join(annual_leave_patterns), na=False, case=False
                    )
                ])
                authorized_breakdown['annual_leave'] = annual_count

                # Sick leave
                sick_count = len(all_absences[
                    all_absences['Reason Description'].str.contains(
                        '|'.join(sick_leave_patterns), na=False, case=False
                    )
                ])
                authorized_breakdown['sick_leave'] = sick_count

                # Other authorized (authorized total - categorized)
                categorized = maternity_count + annual_count + sick_count
                authorized_breakdown['other'] = max(0, authorized_days - categorized)

            # Calculate rates
            total_absence_rate = round((total_absence_days / total_records) * 100, 2) if total_records > 0 else 0.0
            unauthorized_rate = round((unauthorized_days / total_records) * 100, 2) if total_records > 0 else 0.0
            authorized_rate = round((authorized_days / total_records) * 100, 2) if total_records > 0 else 0.0

            team_breakdown[team_name] = {
                'total_absence_rate': total_absence_rate,
                'unauthorized_absence_rate': unauthorized_rate,
                'authorized_absence_rate': authorized_rate,
                'total_absence_days': total_absence_days,
                'unauthorized_days': unauthorized_days,
                'authorized_days': authorized_days,
                'authorized_breakdown': authorized_breakdown
            }

        return team_breakdown

    def to_json(self) -> str:
        """Convert to JSON for JavaScript embedding"""
        import json
        return json.dumps(self.monthly_metrics, ensure_ascii=False, indent=2)

    def _average_tenure_days(self, df: pd.DataFrame, year: int, month: int) -> float:
        """Calculate average tenure days for active employees
        재직자의 평균 재직 일수 계산

        Returns average number of days employees have been working
        직원들이 근무한 평균 일수를 반환
        """
        reference_date = pd.Timestamp(f"{year}-{month:02d}-01") + pd.DateOffset(months=1) - pd.DateOffset(days=1)
        entrance_dates = parse_entrance_date(df)
        stop_dates = parse_stop_date(df)

        # Filter for active employees
        active_employees = df[
            ((stop_dates.isna()) | (stop_dates > self.report_date))
        ]

        if len(active_employees) == 0:
            return 0.0

        # Calculate tenure for each active employee
        active_entrance_dates = entrance_dates[active_employees.index]
        tenure_days = (reference_date - active_entrance_dates).dt.days

        # Remove negative values (future entrance dates)
        tenure_days = tenure_days[tenure_days >= 0]

        if len(tenure_days) == 0:
            return 0.0

        return round(tenure_days.mean(), 1)

    def _early_resignation_rate(self, df: pd.DataFrame, year: int, month: int, days_threshold: int) -> float:
        """Calculate early resignation rate within specified days
        지정된 일수 이내 조기 퇴사율 계산

        Args:
            days_threshold: Number of days to define "early" (30, 60, 90)

        Returns:
            Percentage of employees who resigned within threshold days
        """
        entrance_dates = parse_entrance_date(df)
        stop_dates = parse_stop_date(df)

        # Get resignations in this month
        resigned_in_month = df[
            (stop_dates.dt.year == year) &
            (stop_dates.dt.month == month)
        ]

        if len(resigned_in_month) == 0:
            return 0.0

        # Calculate tenure at resignation
        resigned_entrance = entrance_dates[resigned_in_month.index]
        resigned_stop = stop_dates[resigned_in_month.index]
        tenure_at_resignation = (resigned_stop - resigned_entrance).dt.days

        # Count early resignations
        early_resignations = len(tenure_at_resignation[tenure_at_resignation <= days_threshold])

        # Calculate rate
        rate = (early_resignations / len(resigned_in_month)) * 100

        return round(rate, 1)

    def _retention_rate(self, df: pd.DataFrame, year: int, month: int) -> float:
        """Calculate retention rate (inverse of resignation rate)
        재직 유지율 계산 (퇴사율의 역)

        Formula: 100 - resignation_rate
        """
        resignation_rate = self._resignation_rate(df, year, month)
        return round(100 - resignation_rate, 1)

    def _attendance_rate(self, attendance_df: pd.DataFrame, df: pd.DataFrame, year: int, month: int) -> float:
        """Calculate overall attendance rate (inverse of absence rate)
        전체 출근율 계산 (결근율의 역)

        Only includes active employees at report generation date
        보고서 생성일 기준 재직자만 포함
        """
        absence_rate = self._absence_rate(attendance_df, df, year, month)
        return round(100 - absence_rate, 1)


def main():
    """Test HRMetricCalculator"""
    hr_root = Path(__file__).parent.parent.parent

    collector = MonthlyDataCollector(hr_root)
    available_months = collector.detect_available_months()

    print(f"📅 Available months: {available_months}")

    calculator = HRMetricCalculator(collector)
    target_month = '2025-09'

    all_months = collector.get_month_range(target_month)
    print(f"\n📊 Calculating metrics for: {all_months}")

    metrics = calculator.calculate_all_metrics(all_months)

    print(f"\n✅ Metrics calculated for {len(metrics)} months")

    # Show September metrics
    if target_month in metrics:
        print(f"\n📈 {target_month} Metrics:")
        for key, value in metrics[target_month].items():
            print(f"  {key}: {value}")

        # Show changes
        print(f"\n📊 Month-over-Month Changes (Sep vs Aug):")
        for metric_key in ['total_employees', 'recent_hires', 'recent_resignations']:
            change = calculator.get_month_over_month_change(metric_key, target_month)
            if change:
                sign = '+' if change['absolute'] >= 0 else ''
                print(f"  {metric_key}: {change['current']} ({sign}{change['absolute']}, {sign}{change['percentage']:.1f}%)")


if __name__ == '__main__':
    main()
