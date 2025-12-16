#!/usr/bin/env python3
"""
data_validator.py - Comprehensive Data Validation Utility
종합적인 데이터 검증 유틸리티

Provides validation functions for HR dashboard data integrity
HR 대시보드 데이터 무결성을 위한 검증 함수 제공
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Setup logger
# 로거 설정
logger = logging.getLogger(__name__)


class DataValidator:
    """
    Comprehensive data validation for HR system
    HR 시스템을 위한 종합적인 데이터 검증
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator
        검증기 초기화

        Args:
            strict_mode: If True, raise exceptions on validation failures
                        If False, log warnings and return validation results
            strict_mode: True면 검증 실패 시 예외 발생
                        False면 경고 로그 및 검증 결과 반환
        """
        self.strict_mode = strict_mode
        self.validation_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    def validate_employee_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate employee master data
        직원 마스터 데이터 검증

        Args:
            df: Employee DataFrame / 직원 DataFrame

        Returns:
            Validation results / 검증 결과
        """
        results = {
            'total_records': len(df),
            'valid_records': 0,
            'issues': [],
            'statistics': {}
        }

        # Required columns
        # 필수 컬럼
        required_columns = [
            'Employee No',
            'Employee name',
            'Entrance Date',
            'QIP POSITION 3RD  NAME'
        ]

        # Check required columns
        # 필수 컬럼 확인
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issue = f"Missing required columns: {missing_columns}"
            results['issues'].append(issue)
            self.validation_results['failed'].append(issue)
            if self.strict_mode:
                raise ValueError(issue)
            return results

        # Validate Employee Numbers
        # 직원 번호 검증
        employee_no_issues = self._validate_employee_numbers(df)
        results['issues'].extend(employee_no_issues)

        # Validate dates
        # 날짜 검증
        date_issues = self._validate_dates(df)
        results['issues'].extend(date_issues)

        # Validate positions
        # 직급 검증
        position_issues = self._validate_positions(df)
        results['issues'].extend(position_issues)

        # Calculate statistics
        # 통계 계산
        results['statistics'] = {
            'unique_employees': df['Employee No'].nunique(),
            'duplicate_employees': len(df[df['Employee No'].duplicated()]),
            'missing_entrance_dates': df['Entrance Date'].isna().sum(),
            'missing_positions': df['QIP POSITION 3RD  NAME'].isna().sum(),
            'active_employees': len(df[df['Stop working Date'].isna()]) if 'Stop working Date' in df.columns else 0
        }

        # Count valid records
        # 유효한 레코드 수 계산
        valid_mask = (
            ~df['Employee No'].duplicated() &
            df['Entrance Date'].notna() &
            df['QIP POSITION 3RD  NAME'].notna()
        )
        results['valid_records'] = valid_mask.sum()

        # Update validation results
        # 검증 결과 업데이트
        if results['issues']:
            self.validation_results['failed'].append(f"Employee data: {len(results['issues'])} issues")
        else:
            self.validation_results['passed'].append("Employee data validation passed")

        logger.info(f"Employee data validation: {results['valid_records']}/{results['total_records']} valid records")
        return results

    def _validate_employee_numbers(self, df: pd.DataFrame) -> List[str]:
        """
        Validate employee numbers
        직원 번호 검증
        """
        issues = []

        # Check for duplicates
        # 중복 확인
        duplicates = df[df['Employee No'].duplicated()]
        if not duplicates.empty:
            duplicate_ids = duplicates['Employee No'].unique()
            issues.append(f"Duplicate employee numbers found: {len(duplicate_ids)} employees")
            logger.warning(f"Duplicate employee IDs: {duplicate_ids[:5].tolist()}...")  # Show first 5

        # Check for missing values
        # 누락된 값 확인
        missing = df['Employee No'].isna().sum()
        if missing > 0:
            issues.append(f"Missing employee numbers: {missing} records")

        # Check for invalid formats (assuming numeric IDs)
        # 유효하지 않은 형식 확인 (숫자 ID 가정)
        if 'Employee No' in df.columns:
            non_numeric = df[~df['Employee No'].astype(str).str.isdigit()]
            if not non_numeric.empty:
                issues.append(f"Non-numeric employee numbers: {len(non_numeric)} records")

        return issues

    def _validate_dates(self, df: pd.DataFrame) -> List[str]:
        """
        Validate date columns
        날짜 컬럼 검증
        """
        issues = []
        current_date = pd.Timestamp.now()
        min_date = pd.Timestamp('1990-01-01')
        max_date = current_date + pd.Timedelta(days=365)  # Allow 1 year future

        date_columns = [
            'Entrance Date',
            'Stop working Date',
            'Resignation Date'
        ]

        for col in date_columns:
            if col not in df.columns:
                continue

            # Convert to datetime
            # datetime으로 변환
            dates = pd.to_datetime(df[col], errors='coerce')

            # Check for parsing failures
            # 파싱 실패 확인
            failed_parse = dates.isna() & df[col].notna()
            if failed_parse.any():
                issues.append(f"{col}: {failed_parse.sum()} values failed to parse as dates")

            # Check for future dates
            # 미래 날짜 확인
            future_dates = dates > max_date
            if future_dates.any():
                issues.append(f"{col}: {future_dates.sum()} dates are more than 1 year in future")

            # Check for too old dates
            # 너무 오래된 날짜 확인
            old_dates = dates < min_date
            if old_dates.any():
                issues.append(f"{col}: {old_dates.sum()} dates are before 1990")

            # Check logical consistency
            # 논리적 일관성 확인
            if col == 'Stop working Date' and 'Entrance Date' in df.columns:
                entrance_dates = pd.to_datetime(df['Entrance Date'], errors='coerce')
                invalid_sequence = (dates.notna() & entrance_dates.notna() & (dates < entrance_dates))
                if invalid_sequence.any():
                    issues.append(f"Stop date before entrance date: {invalid_sequence.sum()} records")

        return issues

    def _validate_positions(self, df: pd.DataFrame) -> List[str]:
        """
        Validate position data
        직급 데이터 검증
        """
        issues = []

        position_columns = [
            'QIP POSITION 3RD  NAME',
            'POSITION 1ST NAME',
            'POSITION 2ND NAME'
        ]

        for col in position_columns:
            if col not in df.columns:
                continue

            # Check for missing values
            # 누락된 값 확인
            missing = df[col].isna().sum()
            if missing > 0:
                missing_pct = (missing / len(df)) * 100
                if missing_pct > 10:  # More than 10% missing
                    issues.append(f"{col}: {missing} ({missing_pct:.1f}%) missing values")

            # Check for consistency
            # 일관성 확인
            if col == 'QIP POSITION 3RD  NAME':
                unique_positions = df[col].nunique()
                if unique_positions > 100:  # Suspiciously many unique positions
                    self.validation_results['warnings'].append(
                        f"High number of unique positions: {unique_positions}"
                    )

        return issues

    def validate_attendance_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate attendance data
        근태 데이터 검증

        Args:
            df: Attendance DataFrame / 근태 DataFrame

        Returns:
            Validation results / 검증 결과
        """
        results = {
            'total_records': len(df),
            'valid_records': 0,
            'issues': [],
            'statistics': {}
        }

        # Required columns
        # 필수 컬럼
        required_columns = ['ID No', 'Date', 'compAdd']

        # Check required columns
        # 필수 컬럼 확인
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issue = f"Missing required columns: {missing_columns}"
            results['issues'].append(issue)
            if self.strict_mode:
                raise ValueError(issue)
            return results

        # Validate attendance records
        # 근태 레코드 검증
        issues = []

        # Check for duplicate records
        # 중복 레코드 확인
        duplicates = df[df.duplicated(subset=['ID No', 'Date'])]
        if not duplicates.empty:
            issues.append(f"Duplicate attendance records: {len(duplicates)} entries")

        # Check date validity
        # 날짜 유효성 확인
        dates = pd.to_datetime(df['Date'], errors='coerce')
        invalid_dates = dates.isna() & df['Date'].notna()
        if invalid_dates.any():
            issues.append(f"Invalid dates: {invalid_dates.sum()} records")

        # Check for future dates
        # 미래 날짜 확인
        future_dates = dates > pd.Timestamp.now()
        if future_dates.any():
            issues.append(f"Future attendance dates: {future_dates.sum()} records")

        # Calculate statistics
        # 통계 계산
        results['statistics'] = {
            'unique_employees': df['ID No'].nunique(),
            'date_range': f"{dates.min()} to {dates.max()}" if dates.notna().any() else "N/A",
            'absence_records': len(df[df['compAdd'] == 'Vắng mặt']) if 'compAdd' in df.columns else 0,
            'total_days': dates.nunique() if dates.notna().any() else 0
        }

        # Count valid records
        # 유효한 레코드 수 계산
        valid_mask = df['ID No'].notna() & dates.notna()
        results['valid_records'] = valid_mask.sum()
        results['issues'] = issues

        # Update validation results
        # 검증 결과 업데이트
        if issues:
            self.validation_results['failed'].append(f"Attendance data: {len(issues)} issues")
        else:
            self.validation_results['passed'].append("Attendance data validation passed")

        logger.info(f"Attendance validation: {results['valid_records']}/{results['total_records']} valid records")
        return results

    def validate_metric_value(
        self,
        metric_name: str,
        value: Any,
        expected_type: type = float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate individual metric value
        개별 메트릭 값 검증

        Args:
            metric_name: Metric name / 메트릭 이름
            value: Value to validate / 검증할 값
            expected_type: Expected data type / 예상 데이터 타입
            min_value: Minimum valid value / 최소 유효 값
            max_value: Maximum valid value / 최대 유효 값

        Returns:
            (is_valid, message) / (유효 여부, 메시지)
        """
        # Type check
        # 타입 확인
        if not isinstance(value, expected_type):
            try:
                value = expected_type(value)
            except (ValueError, TypeError):
                return False, f"{metric_name}: Invalid type {type(value)}, expected {expected_type}"

        # Range check
        # 범위 확인
        if min_value is not None and value < min_value:
            return False, f"{metric_name}: Value {value} below minimum {min_value}"

        if max_value is not None and value > max_value:
            return False, f"{metric_name}: Value {value} above maximum {max_value}"

        # Special validations for percentages
        # 퍼센트에 대한 특별 검증
        if 'rate' in metric_name.lower() or 'percentage' in metric_name.lower():
            if not 0 <= value <= 100:
                self.validation_results['warnings'].append(
                    f"{metric_name}: Percentage value {value} outside 0-100 range"
                )

        return True, f"{metric_name}: Valid value {value}"

    def cross_validate_data(
        self,
        employee_df: pd.DataFrame,
        attendance_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Cross-validate between different data sources
        다른 데이터 소스 간 교차 검증

        Args:
            employee_df: Employee master data / 직원 마스터 데이터
            attendance_df: Attendance data / 근태 데이터

        Returns:
            Cross-validation results / 교차 검증 결과
        """
        results = {
            'issues': [],
            'warnings': [],
            'statistics': {}
        }

        # Get employee IDs from both sources
        # 두 소스에서 직원 ID 가져오기
        employee_ids = set(employee_df['Employee No'].astype(str).unique())
        attendance_ids = set(attendance_df['ID No'].astype(str).unique())

        # Find mismatches
        # 불일치 찾기
        in_employee_not_attendance = employee_ids - attendance_ids
        in_attendance_not_employee = attendance_ids - employee_ids

        if in_employee_not_attendance:
            msg = f"Employees without attendance records: {len(in_employee_not_attendance)}"
            results['warnings'].append(msg)
            logger.warning(msg)

        if in_attendance_not_employee:
            msg = f"Attendance records for unknown employees: {len(in_attendance_not_employee)}"
            results['issues'].append(msg)
            logger.error(msg)

        # Statistics
        # 통계
        results['statistics'] = {
            'total_employees': len(employee_ids),
            'total_attendance_employees': len(attendance_ids),
            'overlap': len(employee_ids & attendance_ids),
            'employee_only': len(in_employee_not_attendance),
            'attendance_only': len(in_attendance_not_employee)
        }

        return results

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all validation results
        모든 검증 결과의 요약 가져오기

        Returns:
            Validation summary / 검증 요약
        """
        total_tests = (
            len(self.validation_results['passed']) +
            len(self.validation_results['failed'])
        )

        pass_rate = (
            len(self.validation_results['passed']) / total_tests * 100
            if total_tests > 0 else 0
        )

        return {
            'total_tests': total_tests,
            'passed': len(self.validation_results['passed']),
            'failed': len(self.validation_results['failed']),
            'warnings': len(self.validation_results['warnings']),
            'pass_rate': round(pass_rate, 2),
            'details': self.validation_results
        }

    def reset(self):
        """
        Reset validation results
        검증 결과 초기화
        """
        self.validation_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }