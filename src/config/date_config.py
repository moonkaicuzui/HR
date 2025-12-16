#!/usr/bin/env python3
"""
date_config.py - Date Format Configuration
날짜 형식 설정 파일

Centralized configuration for date formats used throughout the HR dashboard system
HR 대시보드 시스템 전체에서 사용되는 날짜 형식의 중앙 집중식 설정
"""

# Standard date formats / 표준 날짜 형식
DATE_FORMATS = {
    # Primary format used in data files (US format)
    # 데이터 파일에서 사용되는 기본 형식 (미국 형식)
    'PRIMARY': '%m/%d/%Y',

    # Alternative formats in priority order
    # 우선순위 순서의 대체 형식
    'ALTERNATIVES': [
        '%Y.%m.%d',        # Korean format (2025.10.01)
        '%Y/%m/%d',        # ISO-like with slashes
        '%d/%m/%Y',        # European format (day first)
        '%Y-%m-%d',        # ISO 8601 standard
        '%m-%d-%Y',        # US format with dashes
        '%d-%m-%Y',        # European format with dashes
        '%Y년 %m월 %d일',  # Korean text format
        '%m/%d/%y',        # US format with 2-digit year
        '%d/%m/%y',        # European format with 2-digit year
        '%Y%m%d',          # Compact format (20251001)
        '%m%d%Y',          # Compact US format (10012025)
        '%d%m%Y'           # Compact European format (01102025)
    ]
}

# Date parsing configuration / 날짜 파싱 설정
DATE_PARSING = {
    # Whether to interpret the first value as day (False = month first)
    # 첫 번째 값을 일로 해석할지 여부 (False = 월이 먼저)
    'DAYFIRST': False,

    # How to handle parsing errors ('coerce' = convert to NaT)
    # 파싱 오류 처리 방법 ('coerce' = NaT로 변환)
    'ERRORS': 'coerce',

    # Whether to infer date format automatically
    # 날짜 형식을 자동으로 추론할지 여부
    'INFER_FORMAT': False,

    # Cache parsed dates for performance
    # 성능을 위해 파싱된 날짜 캐시
    'CACHE': True
}

# Column name mappings / 컬럼 이름 매핑
DATE_COLUMNS = {
    'ENTRANCE': 'Entrance Date',
    'STOP': 'Stop working Date',
    'RESIGNATION': 'Resignation Date',
    'LEAVE_START': 'Leave Start Date',
    'LEAVE_END': 'Leave End Date',
    'ATTENDANCE': 'Date',
    'REPORT': 'Report Date'
}

# Excel serial date configuration / 엑셀 시리얼 날짜 설정
EXCEL_DATE = {
    # Excel epoch date (January 0, 1900)
    # 엑셀 기준 날짜 (1900년 1월 0일)
    'EPOCH': '1899-12-30',

    # Maximum valid Excel serial number
    # 유효한 최대 엑셀 시리얼 번호
    'MAX_SERIAL': 60000,

    # Minimum valid Excel serial number
    # 유효한 최소 엑셀 시리얼 번호
    'MIN_SERIAL': 1
}

# Validation rules / 검증 규칙
DATE_VALIDATION = {
    # Minimum valid year
    # 유효한 최소 연도
    'MIN_YEAR': 1990,

    # Maximum valid year (current year + 1)
    # 유효한 최대 연도 (현재 연도 + 1)
    'MAX_YEAR': 2026,

    # Allow future dates
    # 미래 날짜 허용
    'ALLOW_FUTURE': False,

    # Maximum days in the future allowed (if ALLOW_FUTURE is True)
    # 허용된 미래 최대 일수 (ALLOW_FUTURE가 True인 경우)
    'MAX_FUTURE_DAYS': 365
}

# Error messages / 오류 메시지
ERROR_MESSAGES = {
    'INVALID_FORMAT': {
        'ko': '잘못된 날짜 형식: {date}',
        'en': 'Invalid date format: {date}'
    },
    'FUTURE_DATE': {
        'ko': '미래 날짜는 허용되지 않습니다: {date}',
        'en': 'Future dates not allowed: {date}'
    },
    'OUT_OF_RANGE': {
        'ko': '날짜가 유효 범위를 벗어났습니다: {date}',
        'en': 'Date out of valid range: {date}'
    },
    'MISSING_COLUMN': {
        'ko': '날짜 컬럼을 찾을 수 없습니다: {column}',
        'en': 'Date column not found: {column}'
    }
}

# Logging configuration / 로깅 설정
LOGGING = {
    # Enable detailed date parsing logs
    # 상세한 날짜 파싱 로그 활성화
    'ENABLE_DEBUG': True,

    # Log successful parses
    # 성공적인 파싱 로그
    'LOG_SUCCESS': False,

    # Log parsing failures
    # 파싱 실패 로그
    'LOG_FAILURES': True,

    # Log format inference attempts
    # 형식 추론 시도 로그
    'LOG_INFERENCE': True
}