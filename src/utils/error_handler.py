#!/usr/bin/env python3
"""
error_handler.py - Comprehensive Error Handling Utility
종합적인 에러 처리 유틸리티

Provides centralized error handling and recovery strategies
중앙 집중식 에러 처리 및 복구 전략 제공
"""

import sys
import traceback
import logging
from typing import Any, Optional, Dict, Callable, Type
from functools import wraps
from datetime import datetime
from pathlib import Path
import pandas as pd


class HRDashboardError(Exception):
    """
    Base exception class for HR Dashboard system
    HR 대시보드 시스템의 기본 예외 클래스
    """

    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        """
        Initialize with message, code and details
        메시지, 코드 및 세부 정보로 초기화
        """
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()


class DataLoadError(HRDashboardError):
    """
    Error during data loading operations
    데이터 로딩 작업 중 오류
    """
    pass


class DateParseError(HRDashboardError):
    """
    Error parsing date values
    날짜 값 파싱 오류
    """
    pass


class MetricCalculationError(HRDashboardError):
    """
    Error during metric calculation
    메트릭 계산 중 오류
    """
    pass


class ValidationError(HRDashboardError):
    """
    Data validation failure
    데이터 검증 실패
    """
    pass


class ConfigurationError(HRDashboardError):
    """
    Configuration or setup error
    설정 또는 셋업 오류
    """
    pass


def safe_execute(
    default_value: Any = None,
    error_types: tuple = (Exception,),
    logger: Optional[logging.Logger] = None,
    raise_on_critical: bool = True
):
    """
    Decorator for safe function execution with error handling
    에러 처리와 함께 안전한 함수 실행을 위한 데코레이터

    Args:
        default_value: Value to return on error / 오류 시 반환할 값
        error_types: Exception types to catch / 캐치할 예외 타입
        logger: Logger instance / 로거 인스턴스
        raise_on_critical: Raise critical errors / 치명적 오류 발생
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                error_msg = f"Error in {func.__name__}: {str(e)}"

                if logger:
                    logger.error(error_msg, exc_info=True)
                else:
                    print(f"ERROR: {error_msg}", file=sys.stderr)

                # Check if it's a critical error
                # 치명적 오류인지 확인
                if raise_on_critical and isinstance(e, (SystemError, MemoryError, KeyboardInterrupt)):
                    raise

                # Return default value for non-critical errors
                # 비치명적 오류에 대해 기본값 반환
                return default_value

        return wrapper
    return decorator


def handle_missing_file(
    file_path: Path,
    logger: Optional[logging.Logger] = None,
    return_empty: bool = True
) -> pd.DataFrame:
    """
    Handle missing data files consistently
    누락된 데이터 파일을 일관되게 처리

    Args:
        file_path: Path to check / 확인할 경로
        logger: Logger instance / 로거 인스턴스
        return_empty: Return empty DataFrame if True / True면 빈 DataFrame 반환

    Returns:
        Empty DataFrame or raises exception / 빈 DataFrame 또는 예외 발생
    """
    error_msg = f"File not found: {file_path}"

    if logger:
        logger.warning(error_msg)
    else:
        print(f"WARNING: {error_msg}", file=sys.stderr)

    if return_empty:
        # Return empty DataFrame (NO FAKE DATA policy)
        # 빈 DataFrame 반환 (가짜 데이터 없음 정책)
        return pd.DataFrame()
    else:
        raise DataLoadError(
            error_msg,
            error_code="FILE_NOT_FOUND",
            details={'file_path': str(file_path)}
        )


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: list,
    min_rows: int = 0,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Validate DataFrame structure and content
    DataFrame 구조와 내용 검증

    Args:
        df: DataFrame to validate / 검증할 DataFrame
        required_columns: Required column names / 필수 컬럼 이름
        min_rows: Minimum required rows / 최소 필요 행 수
        logger: Logger instance / 로거 인스턴스

    Returns:
        True if valid, raises ValidationError otherwise
        유효하면 True, 그렇지 않으면 ValidationError 발생
    """
    # Check if DataFrame is empty
    # DataFrame이 비어있는지 확인
    if df.empty and min_rows > 0:
        raise ValidationError(
            "DataFrame is empty",
            error_code="EMPTY_DATAFRAME",
            details={'min_rows': min_rows}
        )

    # Check for required columns
    # 필수 컬럼 확인
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValidationError(
            f"Missing required columns: {missing_columns}",
            error_code="MISSING_COLUMNS",
            details={'missing': list(missing_columns)}
        )

    # Check minimum rows
    # 최소 행 수 확인
    if len(df) < min_rows:
        raise ValidationError(
            f"Insufficient rows: {len(df)} < {min_rows}",
            error_code="INSUFFICIENT_ROWS",
            details={'actual': len(df), 'required': min_rows}
        )

    if logger:
        logger.debug(f"DataFrame validation passed: {len(df)} rows, columns: {list(df.columns)}")

    return True


class ErrorRecovery:
    """
    Error recovery strategies for different scenarios
    다양한 시나리오에 대한 오류 복구 전략
    """

    @staticmethod
    def recover_date_parsing(
        series: pd.Series,
        fallback_date: Optional[datetime] = None,
        logger: Optional[logging.Logger] = None
    ) -> pd.Series:
        """
        Recover from date parsing errors
        날짜 파싱 오류로부터 복구

        Args:
            series: Date series with potential errors / 잠재적 오류가 있는 날짜 시리즈
            fallback_date: Date to use for invalid entries / 무효 항목에 사용할 날짜
            logger: Logger instance / 로거 인스턴스

        Returns:
            Cleaned date series / 정리된 날짜 시리즈
        """
        # Count invalid dates
        # 유효하지 않은 날짜 계산
        invalid_count = series.isna().sum()

        if invalid_count > 0:
            msg = f"Found {invalid_count} invalid dates"
            if logger:
                logger.warning(msg)

            if fallback_date:
                # Fill with fallback date
                # 대체 날짜로 채우기
                series = series.fillna(pd.Timestamp(fallback_date))
                if logger:
                    logger.info(f"Filled invalid dates with {fallback_date}")

        return series

    @staticmethod
    def recover_numeric_parsing(
        series: pd.Series,
        default_value: float = 0.0,
        logger: Optional[logging.Logger] = None
    ) -> pd.Series:
        """
        Recover from numeric parsing errors
        숫자 파싱 오류로부터 복구

        Args:
            series: Numeric series with potential errors / 잠재적 오류가 있는 숫자 시리즈
            default_value: Default value for invalid entries / 무효 항목의 기본값
            logger: Logger instance / 로거 인스턴스

        Returns:
            Cleaned numeric series / 정리된 숫자 시리즈
        """
        # Convert to numeric
        # 숫자로 변환
        numeric_series = pd.to_numeric(series, errors='coerce')

        # Count conversion failures
        # 변환 실패 계산
        failed_count = numeric_series.isna().sum() - series.isna().sum()

        if failed_count > 0:
            msg = f"Failed to convert {failed_count} values to numeric"
            if logger:
                logger.warning(msg)

            # Fill with default value
            # 기본값으로 채우기
            numeric_series = numeric_series.fillna(default_value)

        return numeric_series

    @staticmethod
    def recover_missing_column(
        df: pd.DataFrame,
        column_name: str,
        fill_value: Any = None,
        logger: Optional[logging.Logger] = None
    ) -> pd.DataFrame:
        """
        Recover from missing column by adding it
        컬럼 추가로 누락된 컬럼 복구

        Args:
            df: DataFrame / DataFrame
            column_name: Missing column name / 누락된 컬럼 이름
            fill_value: Value to fill the column / 컬럼을 채울 값
            logger: Logger instance / 로거 인스턴스

        Returns:
            DataFrame with added column / 컬럼이 추가된 DataFrame
        """
        if column_name not in df.columns:
            msg = f"Adding missing column '{column_name}' with fill value: {fill_value}"
            if logger:
                logger.warning(msg)

            df[column_name] = fill_value

        return df


def create_error_report(
    errors: list,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Create comprehensive error report
    종합적인 오류 보고서 생성

    Args:
        errors: List of errors / 오류 목록
        output_path: Path to save report / 보고서 저장 경로

    Returns:
        Error report dictionary / 오류 보고서 딕셔너리
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_errors': len(errors),
        'errors_by_type': {},
        'errors': []
    }

    # Categorize errors by type
    # 유형별로 오류 분류
    for error in errors:
        error_type = type(error).__name__
        if error_type not in report['errors_by_type']:
            report['errors_by_type'][error_type] = 0
        report['errors_by_type'][error_type] += 1

        # Add error details
        # 오류 세부 정보 추가
        error_detail = {
            'type': error_type,
            'message': str(error),
            'timestamp': getattr(error, 'timestamp', None)
        }

        if hasattr(error, 'error_code'):
            error_detail['code'] = error.error_code
        if hasattr(error, 'details'):
            error_detail['details'] = error.details

        report['errors'].append(error_detail)

    # Save report if path provided
    # 경로가 제공되면 보고서 저장
    if output_path:
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)

    return report


class ErrorContext:
    """
    Context manager for error collection and reporting
    오류 수집 및 보고를 위한 컨텍스트 매니저
    """

    def __init__(self, logger: Optional[logging.Logger] = None, raise_on_exit: bool = False):
        """
        Initialize error context
        오류 컨텍스트 초기화
        """
        self.logger = logger
        self.raise_on_exit = raise_on_exit
        self.errors = []

    def __enter__(self):
        """
        Enter context
        컨텍스트 진입
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context and handle collected errors
        컨텍스트 종료 및 수집된 오류 처리
        """
        if self.errors:
            # Create error report
            # 오류 보고서 생성
            report = create_error_report(self.errors)

            if self.logger:
                self.logger.error(f"Collected {len(self.errors)} errors during execution")
                self.logger.debug(f"Error report: {report}")

            if self.raise_on_exit:
                raise HRDashboardError(
                    f"Execution failed with {len(self.errors)} errors",
                    error_code="MULTIPLE_ERRORS",
                    details=report
                )

        # Don't suppress exceptions
        # 예외를 억제하지 않음
        return False

    def add_error(self, error: Exception):
        """
        Add error to collection
        컬렉션에 오류 추가
        """
        self.errors.append(error)
        if self.logger:
            self.logger.error(f"Error collected: {error}")