"""
date_handler.py - Centralized Date Handling Utility
중앙화된 날짜 처리 유틸리티

Handles all date parsing operations with consistent formats
모든 날짜 파싱 작업을 일관된 형식으로 처리
"""

import pandas as pd
from typing import Union, Optional
import logging
import sys
from pathlib import Path

# Add parent directory for imports
# 임포트를 위해 부모 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.date_config import (
    DATE_FORMATS, DATE_PARSING, DATE_COLUMNS,
    EXCEL_DATE, DATE_VALIDATION, ERROR_MESSAGES, LOGGING
)

logger = logging.getLogger(__name__)
# Configure logger based on settings
# 설정에 따라 로거 구성
if LOGGING['ENABLE_DEBUG']:
    logger.setLevel(logging.DEBUG)

# Use configuration values
# 설정 값 사용
STANDARD_DATE_FORMAT = DATE_FORMATS['PRIMARY']
ALTERNATIVE_FORMATS = DATE_FORMATS['ALTERNATIVES']


def parse_date_column(
    series: pd.Series,
    column_name: str = "Date",
    dayfirst: bool = False
) -> pd.Series:
    """
    Parse date column with consistent format handling
    일관된 형식 처리로 날짜 컬럼 파싱

    Args:
        series: Date series to parse
        column_name: Name of the column for logging
        dayfirst: Whether to interpret first value as day (should be False for US format)

    Returns:
        Parsed datetime series
    """
    # First, try the standard format (MM/DD/YYYY)
    # 먼저 표준 형식 시도 (MM/DD/YYYY)
    try:
        # For US format dates, dayfirst should be False
        # 미국 형식 날짜의 경우 dayfirst는 False여야 함
        result = pd.to_datetime(series, format=STANDARD_DATE_FORMAT, errors='coerce')

        # Check how many failed
        failed_count = result.isna().sum()
        total_count = len(series)

        if failed_count > 0 and failed_count < total_count:
            logger.info(f"{column_name}: Parsed {total_count - failed_count}/{total_count} dates with format {STANDARD_DATE_FORMAT}")

            # Try alternative formats for failed dates
            # 실패한 날짜에 대해 대체 형식 시도
            mask = result.isna() & series.notna()
            if mask.any():
                for alt_format in ALTERNATIVE_FORMATS:
                    if not mask.any():
                        break
                    alt_parsed = pd.to_datetime(
                        series[mask],
                        format=alt_format,
                        errors='coerce'
                    )
                    valid_parsed = ~alt_parsed.isna()
                    if valid_parsed.any():
                        result.loc[mask[mask].index[valid_parsed]] = alt_parsed[valid_parsed]
                        prev_failed = mask.sum()
                        mask = result.isna() & series.notna()
                        new_parsed = prev_failed - mask.sum()
                        if new_parsed > 0 and LOGGING['LOG_SUCCESS']:
                            logger.info(f"{column_name}: Parsed {new_parsed} dates with format {alt_format}")

        # Final fallback for remaining unparsed dates
        # 남은 미파싱 날짜에 대한 최종 폴백
        if result.isna().any() and series.notna().any():
            mask = result.isna() & series.notna()
            if mask.any():
                # Use dateutil parser with dayfirst=False for US format
                # 미국 형식을 위해 dayfirst=False로 dateutil 파서 사용
                fallback = pd.to_datetime(series[mask], errors='coerce', dayfirst=dayfirst)
                result.loc[mask] = fallback

                final_failed = result.isna().sum()
                if final_failed < failed_count:
                    logger.info(f"{column_name}: Parsed final {failed_count - final_failed} dates with fallback parser")

        # Log final statistics
        # 최종 통계 로깅
        success_rate = ((total_count - result.isna().sum()) / total_count * 100) if total_count > 0 else 0
        logger.info(f"{column_name}: Final parse rate: {success_rate:.1f}% ({total_count - result.isna().sum()}/{total_count})")

        return result

    except Exception as e:
        logger.error(f"Error parsing {column_name}: {str(e)}")
        # Fallback to pandas default parser
        # pandas 기본 파서로 폴백
        return pd.to_datetime(series, errors='coerce', dayfirst=dayfirst)


def parse_entrance_date(df: pd.DataFrame) -> pd.Series:
    """
    Parse Entrance Date column with proper format
    적절한 형식으로 입사일 컬럼 파싱
    """
    col_name = DATE_COLUMNS.get('ENTRANCE', 'Entrance Date')
    if col_name not in df.columns:
        error_msg = ERROR_MESSAGES['MISSING_COLUMN']['en'].format(column=col_name)
        raise KeyError(error_msg)

    return parse_date_column(df[col_name], col_name, dayfirst=DATE_PARSING['DAYFIRST'])


def parse_stop_date(df: pd.DataFrame) -> pd.Series:
    """
    Parse Stop working Date column with proper format
    적절한 형식으로 퇴사일 컬럼 파싱
    """
    col_name = DATE_COLUMNS.get('STOP', 'Stop working Date')
    if col_name not in df.columns:
        error_msg = ERROR_MESSAGES['MISSING_COLUMN']['en'].format(column=col_name)
        raise KeyError(error_msg)

    return parse_date_column(df[col_name], col_name, dayfirst=DATE_PARSING['DAYFIRST'])


def get_month_date_range(year: int, month: int) -> tuple:
    """
    Get start and end date for a given month
    주어진 월의 시작일과 종료일 반환

    Returns:
        (month_start, month_end) as pd.Timestamp
    """
    month_start = pd.Timestamp(f"{year}-{month:02d}-01")
    # Calculate last day of month
    # 월의 마지막 날 계산
    if month == 12:
        month_end = pd.Timestamp(f"{year}-12-31")
    else:
        month_end = pd.Timestamp(f"{year}-{month+1:02d}-01") - pd.Timedelta(days=1)

    return month_start, month_end