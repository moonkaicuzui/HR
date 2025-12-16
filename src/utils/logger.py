"""
logger.py - Structured Logging Module
구조화된 로깅 모듈

Provides consistent logging with Korean/English bilingual messages.
한국어/영어 이중 언어 메시지로 일관된 로깅을 제공합니다.

Core Features / 핵심 기능:
- Structured logging with levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  수준별 구조화 로깅 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File and console output / 파일 및 콘솔 출력
- Bilingual message support / 이중 언어 메시지 지원
- Automatic log rotation / 자동 로그 회전
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime


# Log level mapping / 로그 레벨 매핑
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


class BilingualFormatter(logging.Formatter):
    """
    Custom formatter that supports bilingual (Korean/English) messages
    이중 언어(한국어/영어) 메시지를 지원하는 커스텀 포맷터
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with bilingual support
        이중 언어 지원으로 로그 레코드 포맷

        Args:
            record: Log record to format / 포맷할 로그 레코드

        Returns:
            Formatted log string / 포맷된 로그 문자열
        """
        # Add timestamp / 타임스탬프 추가
        record.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Format message / 메시지 포맷
        formatted = super().format(record)

        return formatted


class HRLogger:
    """
    HR Dashboard logging system
    HR 대시보드 로깅 시스템
    """

    def __init__(
        self,
        name: str = "HR",
        log_dir: Optional[Path] = None,
        log_level: str = "INFO",
        console_output: bool = True,
        file_output: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        Initialize HR Logger
        HR 로거 초기화

        Args:
            name: Logger name / 로거 이름
            log_dir: Directory for log files / 로그 파일 디렉토리
            log_level: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL) / 로깅 레벨
            console_output: Enable console output / 콘솔 출력 활성화
            file_output: Enable file output / 파일 출력 활성화
            max_bytes: Maximum log file size before rotation / 회전 전 최대 로그 파일 크기
            backup_count: Number of backup files to keep / 보관할 백업 파일 수
        """
        self.name = name
        self.logger = logging.getLogger(name)

        # Set log level / 로그 레벨 설정
        level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
        self.logger.setLevel(level)

        # Remove existing handlers / 기존 핸들러 제거
        self.logger.handlers = []

        # Create formatters / 포맷터 생성
        detailed_format = BilingualFormatter(
            fmt='%(timestamp)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_format = BilingualFormatter(
            fmt='%(levelname)s - %(message)s'
        )

        # Console handler / 콘솔 핸들러
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(simple_format)
            self.logger.addHandler(console_handler)

        # File handler with rotation / 회전 기능이 있는 파일 핸들러
        if file_output:
            if log_dir is None:
                # Default to HR/logs/ directory / 기본값은 HR/logs/ 디렉토리
                hr_root = Path(__file__).parent.parent.parent
                log_dir = hr_root / "logs"

            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f"{name.lower()}.log"

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(detailed_format)
            self.logger.addHandler(file_handler)

    def debug(self, msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
        """
        Log DEBUG level message
        DEBUG 레벨 메시지 로그

        Args:
            msg_ko: Korean message / 한국어 메시지
            msg_en: English message (optional) / 영어 메시지 (선택)
            **kwargs: Additional context / 추가 컨텍스트
        """
        message = self._format_bilingual(msg_ko, msg_en, **kwargs)
        self.logger.debug(message)

    def info(self, msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
        """
        Log INFO level message
        INFO 레벨 메시지 로그

        Args:
            msg_ko: Korean message / 한국어 메시지
            msg_en: English message (optional) / 영어 메시지 (선택)
            **kwargs: Additional context / 추가 컨텍스트
        """
        message = self._format_bilingual(msg_ko, msg_en, **kwargs)
        self.logger.info(message)

    def warning(self, msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
        """
        Log WARNING level message
        WARNING 레벨 메시지 로그

        Args:
            msg_ko: Korean message / 한국어 메시지
            msg_en: English message (optional) / 영어 메시지 (선택)
            **kwargs: Additional context / 추가 컨텍스트
        """
        message = self._format_bilingual(msg_ko, msg_en, **kwargs)
        self.logger.warning(message)

    def error(self, msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
        """
        Log ERROR level message
        ERROR 레벨 메시지 로그

        Args:
            msg_ko: Korean message / 한국어 메시지
            msg_en: English message (optional) / 영어 메시지 (선택)
            **kwargs: Additional context / 추가 컨텍스트
        """
        message = self._format_bilingual(msg_ko, msg_en, **kwargs)
        self.logger.error(message)

    def critical(self, msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
        """
        Log CRITICAL level message
        CRITICAL 레벨 메시지 로그

        Args:
            msg_ko: Korean message / 한국어 메시지
            msg_en: English message (optional) / 영어 메시지 (선택)
            **kwargs: Additional context / 추가 컨텍스트
        """
        message = self._format_bilingual(msg_ko, msg_en, **kwargs)
        self.logger.critical(message)

    def _format_bilingual(self, msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> str:
        """
        Format bilingual message
        이중 언어 메시지 포맷

        Args:
            msg_ko: Korean message / 한국어 메시지
            msg_en: English message / 영어 메시지
            **kwargs: Additional context to append / 추가할 컨텍스트

        Returns:
            Formatted bilingual message / 포맷된 이중 언어 메시지
        """
        # Base message / 기본 메시지
        if msg_en:
            message = f"{msg_ko} / {msg_en}"
        else:
            message = msg_ko

        # Add context if provided / 제공된 경우 컨텍스트 추가
        if kwargs:
            context_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} [{context_str}]"

        return message

    def log_dataframe_info(self, df_name: str, df) -> None:
        """
        Log DataFrame information
        DataFrame 정보 로그

        Args:
            df_name: Name of DataFrame / DataFrame 이름
            df: pandas DataFrame / pandas DataFrame
        """
        self.info(
            f"DataFrame '{df_name}' 로드됨",
            f"DataFrame '{df_name}' loaded",
            rows=len(df),
            columns=len(df.columns)
        )

    def log_file_operation(self, operation: str, file_path: str, success: bool = True) -> None:
        """
        Log file operation
        파일 작업 로그

        Args:
            operation: Operation type (read/write/delete) / 작업 유형
            file_path: File path / 파일 경로
            success: Whether operation succeeded / 작업 성공 여부
        """
        if success:
            self.info(
                f"파일 {operation} 성공",
                f"File {operation} successful",
                file=file_path
            )
        else:
            self.error(
                f"파일 {operation} 실패",
                f"File {operation} failed",
                file=file_path
            )

    def log_metric_calculation(self, metric_name: str, value: float, details: Optional[dict] = None) -> None:
        """
        Log metric calculation
        메트릭 계산 로그

        Args:
            metric_name: Name of metric / 메트릭 이름
            value: Calculated value / 계산된 값
            details: Additional details / 추가 세부정보
        """
        log_kwargs = {"metric": metric_name, "value": value}
        if details:
            log_kwargs.update(details)

        self.info(
            f"메트릭 '{metric_name}' 계산 완료",
            f"Metric '{metric_name}' calculated",
            **log_kwargs
        )

    def log_error_with_traceback(self, msg_ko: str, msg_en: Optional[str] = None, exc_info: bool = True) -> None:
        """
        Log error with traceback
        트레이스백과 함께 에러 로그

        Args:
            msg_ko: Korean error message / 한국어 에러 메시지
            msg_en: English error message / 영어 에러 메시지
            exc_info: Include exception info / 예외 정보 포함
        """
        message = self._format_bilingual(msg_ko, msg_en)
        self.logger.error(message, exc_info=exc_info)


# Global logger instance / 전역 로거 인스턴스
_global_logger: Optional[HRLogger] = None


def init_logger(
    name: str = "HR",
    log_dir: Optional[Path] = None,
    log_level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True
) -> HRLogger:
    """
    Initialize global logger instance
    전역 로거 인스턴스 초기화

    Args:
        name: Logger name / 로거 이름
        log_dir: Log directory / 로그 디렉토리
        log_level: Log level / 로그 레벨
        console_output: Enable console output / 콘솔 출력 활성화
        file_output: Enable file output / 파일 출력 활성화

    Returns:
        Initialized HRLogger instance / 초기화된 HRLogger 인스턴스
    """
    global _global_logger
    _global_logger = HRLogger(
        name=name,
        log_dir=log_dir,
        log_level=log_level,
        console_output=console_output,
        file_output=file_output
    )
    return _global_logger


def get_logger() -> HRLogger:
    """
    Get global logger instance
    전역 로거 인스턴스 반환

    Returns:
        Global HRLogger instance / 전역 HRLogger 인스턴스

    Raises:
        RuntimeError: If logger not initialized / 로거가 초기화되지 않은 경우
    """
    global _global_logger
    if _global_logger is None:
        # Auto-initialize with defaults / 기본값으로 자동 초기화
        _global_logger = HRLogger()
    return _global_logger


# Convenience functions / 편의 함수
def debug(msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
    """Log DEBUG message / DEBUG 메시지 로그"""
    get_logger().debug(msg_ko, msg_en, **kwargs)


def info(msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
    """Log INFO message / INFO 메시지 로그"""
    get_logger().info(msg_ko, msg_en, **kwargs)


def warning(msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
    """Log WARNING message / WARNING 메시지 로그"""
    get_logger().warning(msg_ko, msg_en, **kwargs)


def error(msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
    """Log ERROR message / ERROR 메시지 로그"""
    get_logger().error(msg_ko, msg_en, **kwargs)


def critical(msg_ko: str, msg_en: Optional[str] = None, **kwargs) -> None:
    """Log CRITICAL message / CRITICAL 메시지 로그"""
    get_logger().critical(msg_ko, msg_en, **kwargs)
