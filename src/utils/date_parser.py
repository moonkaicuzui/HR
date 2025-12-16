"""
date_parser.py - Unified Date Parsing Module
통합 날짜 파싱 모듈

Handles various date formats from CSV files and ensures consistent date handling.
CSV 파일의 다양한 날짜 형식을 처리하고 일관된 날짜 처리를 보장합니다.

Core Features / 핵심 기능:
- Parse multiple date formats / 여러 날짜 형식 파싱
- Handle Korean month names (e.g., "9월") / 한국어 월 이름 처리
- Consistent datetime conversion / 일관된 datetime 변환
- Working days calculation / 근무일 계산
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Union, Optional, List
import re


# Korean month name mapping / 한국어 월 이름 매핑
KOREAN_MONTHS = {
    "1월": 1, "2월": 2, "3월": 3, "4월": 4, "5월": 5, "6월": 6,
    "7월": 7, "8월": 8, "9월": 9, "10월": 10, "11월": 11, "12월": 12
}

# Common date format patterns / 일반적인 날짜 형식 패턴
DATE_FORMATS = [
    "%Y-%m-%d",           # 2025-09-15
    "%Y/%m/%d",           # 2025/09/15
    "%d-%m-%Y",           # 15-09-2025
    "%d/%m/%Y",           # 15/09/2025
    "%Y%m%d",             # 20250915
    "%d.%m.%Y",           # 15.09.2025
    "%Y.%m.%d",           # 2025.09.15
    "%m/%d/%Y",           # 09/15/2025
    "%d-%b-%Y",           # 15-Sep-2025
    "%d %b %Y",           # 15 Sep 2025
    "%Y-%m-%d %H:%M:%S",  # 2025-09-15 14:30:00
    "%Y/%m/%d %H:%M:%S",  # 2025/09/15 14:30:00
]


class DateParser:
    """
    Unified date parser with multiple format support
    여러 형식을 지원하는 통합 날짜 파서
    """

    def __init__(self, default_format: str = "%Y-%m-%d"):
        """
        Initialize DateParser
        DateParser 초기화

        Args:
            default_format: Default output format / 기본 출력 형식
        """
        self.default_format = default_format

    def parse_date(self, date_value: Union[str, datetime, pd.Timestamp]) -> Optional[datetime]:
        """
        Parse date from various formats to datetime object
        다양한 형식의 날짜를 datetime 객체로 파싱

        Args:
            date_value: Date value in various formats / 다양한 형식의 날짜 값

        Returns:
            datetime object or None if parsing fails / datetime 객체 또는 파싱 실패 시 None

        Examples:
            >>> parser = DateParser()
            >>> parser.parse_date("2025-09-15")
            datetime.datetime(2025, 9, 15, 0, 0)
            >>> parser.parse_date("15/09/2025")
            datetime.datetime(2025, 9, 15, 0, 0)
        """
        # Handle None or empty values / None 또는 빈 값 처리
        if pd.isna(date_value) or date_value == "" or date_value is None:
            return None

        # If already datetime, return as is / 이미 datetime이면 그대로 반환
        if isinstance(date_value, datetime):
            return date_value

        # If pandas Timestamp, convert to datetime / pandas Timestamp면 datetime으로 변환
        if isinstance(date_value, pd.Timestamp):
            return date_value.to_pydatetime()

        # Convert to string for parsing / 파싱을 위해 문자열로 변환
        date_str = str(date_value).strip()

        # Try parsing with each format / 각 형식으로 파싱 시도
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue

        # Try pandas' flexible parser as fallback / 대체로 pandas의 유연한 파서 시도
        try:
            return pd.to_datetime(date_str)
        except Exception:
            pass

        return None

    def parse_korean_month(self, month_str: str, year: int) -> Optional[datetime]:
        """
        Parse Korean month name to datetime
        한국어 월 이름을 datetime으로 파싱

        Args:
            month_str: Korean month (e.g., "9월") / 한국어 월 (예: "9월")
            year: Year number / 년도

        Returns:
            datetime object for first day of month / 해당 월의 첫 날 datetime 객체

        Examples:
            >>> parser = DateParser()
            >>> parser.parse_korean_month("9월", 2025)
            datetime.datetime(2025, 9, 1, 0, 0)
        """
        if month_str in KOREAN_MONTHS:
            month_num = KOREAN_MONTHS[month_str]
            return datetime(year, month_num, 1)
        return None

    def format_date(self, date_value: Union[str, datetime, pd.Timestamp],
                   output_format: Optional[str] = None) -> Optional[str]:
        """
        Format date to string with specified format
        지정된 형식으로 날짜를 문자열로 포맷

        Args:
            date_value: Date value to format / 포맷할 날짜 값
            output_format: Output format (uses default if None) / 출력 형식 (None이면 기본값 사용)

        Returns:
            Formatted date string / 포맷된 날짜 문자열

        Examples:
            >>> parser = DateParser()
            >>> parser.format_date("2025-09-15", "%d/%m/%Y")
            "15/09/2025"
        """
        parsed_date = self.parse_date(date_value)
        if parsed_date is None:
            return None

        fmt = output_format or self.default_format
        return parsed_date.strftime(fmt)

    def calculate_working_days(self, start_date: Union[str, datetime],
                              end_date: Union[str, datetime],
                              exclude_weekends: bool = True) -> int:
        """
        Calculate number of working days between two dates
        두 날짜 사이의 근무일 수 계산

        Args:
            start_date: Start date / 시작 날짜
            end_date: End date / 종료 날짜
            exclude_weekends: Whether to exclude Saturdays and Sundays / 토요일과 일요일 제외 여부

        Returns:
            Number of working days / 근무일 수

        Examples:
            >>> parser = DateParser()
            >>> parser.calculate_working_days("2025-09-01", "2025-09-05")
            5
        """
        start = self.parse_date(start_date)
        end = self.parse_date(end_date)

        if start is None or end is None:
            return 0

        # Ensure start is before end / 시작이 종료보다 앞서는지 확인
        if start > end:
            start, end = end, start

        total_days = 0
        current = start

        while current <= end:
            # Exclude weekends if specified / 지정된 경우 주말 제외
            if exclude_weekends:
                if current.weekday() < 5:  # Monday = 0, Sunday = 6
                    total_days += 1
            else:
                total_days += 1

            current += timedelta(days=1)

        return total_days

    def get_month_range(self, year: int, month: int) -> tuple:
        """
        Get start and end dates for a given month
        주어진 월의 시작 및 종료 날짜 반환

        Args:
            year: Year number / 년도
            month: Month number (1-12) / 월 번호 (1-12)

        Returns:
            Tuple of (start_date, end_date) / (시작_날짜, 종료_날짜) 튜플

        Examples:
            >>> parser = DateParser()
            >>> parser.get_month_range(2025, 9)
            (datetime.datetime(2025, 9, 1, 0, 0), datetime.datetime(2025, 9, 30, 0, 0))
        """
        start_date = datetime(year, month, 1)

        # Calculate last day of month / 월의 마지막 날 계산
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        return start_date, end_date

    def is_within_date_range(self, date_value: Union[str, datetime],
                            start_date: Union[str, datetime],
                            end_date: Union[str, datetime]) -> bool:
        """
        Check if date is within specified range
        날짜가 지정된 범위 내에 있는지 확인

        Args:
            date_value: Date to check / 확인할 날짜
            start_date: Range start date / 범위 시작 날짜
            end_date: Range end date / 범위 종료 날짜

        Returns:
            True if within range, False otherwise / 범위 내에 있으면 True, 아니면 False
        """
        date = self.parse_date(date_value)
        start = self.parse_date(start_date)
        end = self.parse_date(end_date)

        if date is None or start is None or end is None:
            return False

        return start <= date <= end

    def parse_dataframe_dates(self, df: pd.DataFrame,
                             date_columns: List[str],
                             inplace: bool = False) -> pd.DataFrame:
        """
        Parse date columns in a DataFrame
        DataFrame의 날짜 열 파싱

        Args:
            df: Input DataFrame / 입력 DataFrame
            date_columns: List of column names containing dates / 날짜가 포함된 열 이름 목록
            inplace: Whether to modify DataFrame in place / DataFrame을 제자리에서 수정할지 여부

        Returns:
            DataFrame with parsed dates / 파싱된 날짜가 있는 DataFrame

        Examples:
            >>> parser = DateParser()
            >>> df = pd.DataFrame({'date': ['2025-09-15', '2025-09-16']})
            >>> df = parser.parse_dataframe_dates(df, ['date'])
        """
        result_df = df if inplace else df.copy()

        for col in date_columns:
            if col in result_df.columns:
                result_df[col] = result_df[col].apply(self.parse_date)

        return result_df


# Global instance for easy access / 쉬운 접근을 위한 전역 인스턴스
_global_parser: Optional[DateParser] = None


def get_date_parser(default_format: str = "%Y-%m-%d") -> DateParser:
    """
    Get or create global date parser instance
    전역 날짜 파서 인스턴스 반환 또는 생성

    Args:
        default_format: Default output format / 기본 출력 형식

    Returns:
        DateParser instance / DateParser 인스턴스
    """
    global _global_parser
    if _global_parser is None:
        _global_parser = DateParser(default_format)
    return _global_parser


def parse_date(date_value: Union[str, datetime, pd.Timestamp]) -> Optional[datetime]:
    """
    Convenience function for date parsing using global instance
    전역 인스턴스를 사용한 날짜 파싱 편의 함수

    Args:
        date_value: Date value to parse / 파싱할 날짜 값

    Returns:
        Parsed datetime object / 파싱된 datetime 객체
    """
    return get_date_parser().parse_date(date_value)


def format_date(date_value: Union[str, datetime, pd.Timestamp],
               output_format: str = "%Y-%m-%d") -> Optional[str]:
    """
    Convenience function for date formatting using global instance
    전역 인스턴스를 사용한 날짜 포맷 편의 함수

    Args:
        date_value: Date value to format / 포맷할 날짜 값
        output_format: Output format / 출력 형식

    Returns:
        Formatted date string / 포맷된 날짜 문자열
    """
    return get_date_parser().format_date(date_value, output_format)


def calculate_working_days(start_date: Union[str, datetime],
                          end_date: Union[str, datetime]) -> int:
    """
    Convenience function for working days calculation
    근무일 계산 편의 함수

    Args:
        start_date: Start date / 시작 날짜
        end_date: End date / 종료 날짜

    Returns:
        Number of working days / 근무일 수
    """
    return get_date_parser().calculate_working_days(start_date, end_date)
