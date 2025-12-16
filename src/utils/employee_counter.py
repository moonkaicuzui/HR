"""
employee_counter.py - Reusable Employee Counting Utilities
재사용 가능한 직원 수 계산 유틸리티

Provides standardized functions for counting employees across different contexts:
- Monthly headcount with date-based filtering
- Team-based employee counting
- Department/position-based grouping
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from .date_handler import parse_date_column


def count_active_employees(
    df: pd.DataFrame,
    reference_date: pd.Timestamp,
    entrance_col: str = 'Entrance Date',
    stop_col: str = 'Stop working Date'
) -> int:
    """
    Count active employees at a specific reference date
    특정 기준일의 재직자 수 계산

    Args:
        df: Employee DataFrame
        reference_date: Reference date for counting
        entrance_col: Column name for entrance date
        stop_col: Column name for stop working date

    Returns:
        int: Number of active employees

    Logic:
        Active if: entrance_date <= reference_date AND (no stop_date OR stop_date > reference_date)
    """
    if df.empty:
        return 0

    # Parse dates with proper format (US format: MM/DD/YYYY)
    # 적절한 형식으로 날짜 파싱 (미국 형식: MM/DD/YYYY)
    entrance_dates = parse_date_column(df[entrance_col], entrance_col, dayfirst=False)
    stop_dates = parse_date_column(df[stop_col], stop_col, dayfirst=False)

    # Active employees
    active = df[
        (entrance_dates <= reference_date) &
        ((stop_dates.isna()) | (stop_dates > reference_date))
    ]

    return len(active)


def count_employees_by_month(
    df: pd.DataFrame,
    year_month: str,
    report_date: Optional[datetime] = None,
    entrance_col: str = 'Entrance Date',
    stop_col: str = 'Stop working Date'
) -> int:
    """
    Count employees for a specific month using report date logic
    특정 월의 직원 수 계산 (보고서 날짜 로직 적용)

    Args:
        df: Employee DataFrame
        year_month: 'YYYY-MM' format
        report_date: Report generation date (default: today)
        entrance_col: Column name for entrance date
        stop_col: Column name for stop working date

    Returns:
        int: Number of employees for the month

    Logic:
        - If report_date is within target month: use report_date as reference
        - Otherwise: use month-end date as reference
    """
    if df.empty:
        return 0

    year, month = year_month.split('-')
    year_num = int(year)
    month_num = int(month)

    # Calculate reference date
    month_start = pd.Timestamp(f"{year_num}-{month_num:02d}-01")
    end_of_month = month_start + pd.DateOffset(months=1) - pd.DateOffset(days=1)

    if report_date:
        report_timestamp = pd.Timestamp(report_date)
        if month_start <= report_timestamp <= end_of_month:
            reference_date = report_timestamp
        else:
            reference_date = end_of_month
    else:
        reference_date = end_of_month

    return count_active_employees(df, reference_date, entrance_col, stop_col)


def count_employees_by_team(
    df: pd.DataFrame,
    team_mapping: Dict[str, List[str]],
    reference_date: pd.Timestamp,
    position_col: str = 'QIP POSITION 3RD  NAME',
    entrance_col: str = 'Entrance Date',
    stop_col: str = 'Stop working Date'
) -> Dict[str, int]:
    """
    Count employees by team at a specific reference date
    특정 기준일의 팀별 직원 수 계산

    Args:
        df: Employee DataFrame
        team_mapping: Dict mapping team_name -> list of position_3rd values
        reference_date: Reference date for counting
        position_col: Column name for position classification
        entrance_col: Column name for entrance date
        stop_col: Column name for stop working date

    Returns:
        Dict[str, int]: Team name -> employee count mapping

    Example:
        team_mapping = {
            'ASSEMBLY': ['ASSEMBLY LINE TQC', 'ASSEMBLY LINE RQC', ...],
            'STITCHING': ['STITCHING INLINE INSPECTOR', ...]
        }
    """
    if df.empty:
        return {team: 0 for team in team_mapping.keys()}

    # Build reverse mapping
    reverse_mapping = {}
    for team_name, positions in team_mapping.items():
        for pos in positions:
            reverse_mapping[pos] = team_name

    # Filter active employees at reference date
    # Parse dates with proper format (US format: MM/DD/YYYY)
    # 적절한 형식으로 날짜 파싱 (미국 형식: MM/DD/YYYY)
    entrance_dates = parse_date_column(df[entrance_col], entrance_col, dayfirst=False)
    stop_dates = parse_date_column(df[stop_col], stop_col, dayfirst=False)

    active_df = df[
        (entrance_dates <= reference_date) &
        ((stop_dates.isna()) | (stop_dates > reference_date))
    ].copy()

    # Count by team
    team_counts = {team: 0 for team in team_mapping.keys()}

    for _, row in active_df.iterrows():
        position = str(row.get(position_col, ''))
        team_name = reverse_mapping.get(position)

        if team_name:
            team_counts[team_name] += 1

    return team_counts


def count_employees_by_teams_monthly(
    df: pd.DataFrame,
    team_mapping: Dict[str, List[str]],
    months: List[str],
    report_date: Optional[datetime] = None,
    position_col: str = 'QIP POSITION 3RD  NAME',
    entrance_col: str = 'Entrance Date',
    stop_col: str = 'Stop working Date'
) -> Dict[str, Dict[str, int]]:
    """
    Count employees by team for multiple months
    여러 월의 팀별 직원 수 계산

    Args:
        df: Employee DataFrame
        team_mapping: Dict mapping team_name -> list of position_3rd values
        months: List of 'YYYY-MM' month strings
        report_date: Report generation date (default: today)
        position_col: Column name for position classification
        entrance_col: Column name for entrance date
        stop_col: Column name for stop working date

    Returns:
        Dict[str, Dict[str, int]]: month -> (team_name -> count) mapping

    Example:
        {
            '2024-09': {'ASSEMBLY': 121, 'STITCHING': 95, ...},
            '2024-10': {'ASSEMBLY': 117, 'STITCHING': 90, ...}
        }
    """
    monthly_team_counts = {}

    for year_month in months:
        year, month = year_month.split('-')
        year_num = int(year)
        month_num = int(month)

        # Calculate reference date for this month
        month_start = pd.Timestamp(f"{year_num}-{month_num:02d}-01")
        end_of_month = month_start + pd.DateOffset(months=1) - pd.DateOffset(days=1)

        if report_date:
            report_timestamp = pd.Timestamp(report_date)
            if month_start <= report_timestamp <= end_of_month:
                reference_date = report_timestamp
            else:
                reference_date = end_of_month
        else:
            reference_date = end_of_month

        # Count by team for this month
        team_counts = count_employees_by_team(
            df, team_mapping, reference_date,
            position_col, entrance_col, stop_col
        )

        monthly_team_counts[year_month] = team_counts

    return monthly_team_counts


def get_active_employees_df(
    df: pd.DataFrame,
    reference_date: pd.Timestamp,
    entrance_col: str = 'Entrance Date',
    stop_col: str = 'Stop working Date'
) -> pd.DataFrame:
    """
    Get DataFrame of active employees at reference date
    기준일 기준 재직자 DataFrame 반환

    Args:
        df: Employee DataFrame
        reference_date: Reference date for filtering
        entrance_col: Column name for entrance date
        stop_col: Column name for stop working date

    Returns:
        pd.DataFrame: Filtered DataFrame with only active employees
    """
    if df.empty:
        return pd.DataFrame()

    # Parse dates with proper format (US format: MM/DD/YYYY)
    # 적절한 형식으로 날짜 파싱 (미국 형식: MM/DD/YYYY)
    entrance_dates = parse_date_column(df[entrance_col], entrance_col, dayfirst=False)
    stop_dates = parse_date_column(df[stop_col], stop_col, dayfirst=False)

    active_df = df[
        (entrance_dates <= reference_date) &
        ((stop_dates.isna()) | (stop_dates > reference_date))
    ].copy()

    return active_df


def calculate_monthly_metrics(
    df: pd.DataFrame,
    months: List[str],
    report_date: Optional[datetime] = None,
    entrance_col: str = 'Entrance Date',
    stop_col: str = 'Stop working Date'
) -> Dict[str, int]:
    """
    Calculate monthly employee counts for multiple months
    여러 월의 직원 수 계산

    Args:
        df: Employee DataFrame
        months: List of 'YYYY-MM' month strings
        report_date: Report generation date (default: today)
        entrance_col: Column name for entrance date
        stop_col: Column name for stop working date

    Returns:
        Dict[str, int]: month -> employee count mapping

    Example:
        {'2024-09': 502, '2024-10': 399}
    """
    monthly_counts = {}

    for year_month in months:
        count = count_employees_by_month(
            df, year_month, report_date,
            entrance_col, stop_col
        )
        monthly_counts[year_month] = count

    return monthly_counts
