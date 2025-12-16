#!/usr/bin/env python3
"""
logger_config.py - Centralized Logging Configuration
중앙 집중식 로깅 설정

Provides consistent logging setup across the HR dashboard system
HR 대시보드 시스템 전체에서 일관된 로깅 설정 제공
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with colors for console output
    콘솔 출력용 색상이 있는 커스텀 포매터
    """

    # Color codes for different log levels
    # 로그 레벨별 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        """
        Format log record with colors
        색상으로 로그 레코드 포맷
        """
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class DetailedFileFormatter(logging.Formatter):
    """
    Detailed formatter for file output with extra context
    추가 컨텍스트가 있는 파일 출력용 상세 포매터
    """

    def format(self, record):
        """
        Format with additional context for debugging
        디버깅을 위한 추가 컨텍스트로 포맷
        """
        # Add extra context fields if available
        # 가능한 경우 추가 컨텍스트 필드 추가
        extras = []
        if hasattr(record, 'employee_id'):
            extras.append(f"EmpID:{record.employee_id}")
        if hasattr(record, 'metric_name'):
            extras.append(f"Metric:{record.metric_name}")
        if hasattr(record, 'phase'):
            extras.append(f"Phase:{record.phase}")

        if extras:
            record.context = f" [{' | '.join(extras)}]"
        else:
            record.context = ""

        return super().format(record)


def setup_logger(
    name: str = 'hr_dashboard',
    level: str = 'INFO',
    log_dir: Optional[Path] = None,
    console: bool = True,
    file: bool = True,
    rotate: bool = True
) -> logging.Logger:
    """
    Setup logger with consistent configuration
    일관된 설정으로 로거 설정

    Args:
        name: Logger name / 로거 이름
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files / 로그 파일 디렉토리
        console: Enable console output / 콘솔 출력 활성화
        file: Enable file output / 파일 출력 활성화
        rotate: Enable log rotation / 로그 회전 활성화

    Returns:
        Configured logger instance / 설정된 로거 인스턴스
    """
    # Create logger
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    # 기존 핸들러 제거
    logger.handlers = []

    # Console handler
    # 콘솔 핸들러
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Use colored formatter for console
        # 콘솔에 색상 포매터 사용
        console_format = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    # File handler
    # 파일 핸들러
    if file:
        # Create log directory if needed
        # 필요한 경우 로그 디렉토리 생성
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)

        # Create dated log file
        # 날짜가 있는 로그 파일 생성
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

        if rotate:
            # Rotating file handler (10MB max, keep 5 backups)
            # 회전 파일 핸들러 (최대 10MB, 5개 백업 유지)
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
        else:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')

        file_handler.setLevel(logging.DEBUG)

        # Use detailed formatter for file
        # 파일에 상세 포매터 사용
        file_format = DetailedFileFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d%(context)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance with standard configuration
    표준 설정으로 로거 인스턴스 가져오기

    Args:
        name: Module name / 모듈 이름

    Returns:
        Logger instance / 로거 인스턴스
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding extra context to log messages
    로그 메시지에 추가 컨텍스트를 추가하기 위한 컨텍스트 매니저
    """

    def __init__(self, logger: logging.Logger, **kwargs):
        """
        Initialize with logger and context fields
        로거와 컨텍스트 필드로 초기화
        """
        self.logger = logger
        self.context = kwargs
        self.old_factory = None

    def __enter__(self):
        """
        Enter context and add fields to log records
        컨텍스트 진입 및 로그 레코드에 필드 추가
        """
        old_factory = logging.getLogRecordFactory()
        self.old_factory = old_factory

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context and restore original factory
        컨텍스트 종료 및 원래 팩토리 복원
        """
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


# Predefined loggers for different modules
# 다른 모듈용 사전 정의된 로거
LOGGERS = {
    'data_loader': 'hr_dashboard.data',
    'metric_calculator': 'hr_dashboard.metrics',
    'date_handler': 'hr_dashboard.dates',
    'dashboard_builder': 'hr_dashboard.dashboard',
    'validator': 'hr_dashboard.validation',
    'error_detector': 'hr_dashboard.errors'
}


def setup_all_loggers(level: str = 'INFO'):
    """
    Setup all predefined loggers
    모든 사전 정의된 로거 설정

    Args:
        level: Default log level / 기본 로그 레벨
    """
    # Setup main logger
    # 메인 로거 설정
    main_logger = setup_logger('hr_dashboard', level)
    main_logger.info(f"Logging system initialized at {level} level")

    # Setup module loggers
    # 모듈 로거 설정
    for module, logger_name in LOGGERS.items():
        module_logger = logging.getLogger(logger_name)
        module_logger.setLevel(getattr(logging, level.upper()))
        module_logger.info(f"Logger {logger_name} initialized")

    return main_logger


# Convenience functions for common logging patterns
# 일반적인 로깅 패턴용 편의 함수

def log_execution_time(logger: logging.Logger, func_name: str):
    """
    Decorator to log function execution time
    함수 실행 시간을 로그하는 데코레이터
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.debug(f"Starting {func_name}")

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Completed {func_name} in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Failed {func_name} after {duration:.2f}s: {str(e)}")
                raise

        return wrapper
    return decorator


def log_data_operation(logger: logging.Logger, operation: str, details: dict):
    """
    Log data operation with structured details
    구조화된 세부 정보로 데이터 작업 로그

    Args:
        logger: Logger instance / 로거 인스턴스
        operation: Operation name / 작업 이름
        details: Operation details / 작업 세부 정보
    """
    detail_str = ' | '.join(f"{k}={v}" for k, v in details.items())
    logger.info(f"Data Operation: {operation} | {detail_str}")