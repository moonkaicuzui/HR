"""
data_validator.py - HR Data Validation Module
HR 데이터 검증 모듈

Validates data integrity and quality for HR data sources.
HR 데이터 소스의 데이터 무결성 및 품질을 검증합니다.

Core Features / 핵심 기능:
- Schema validation / 스키마 검증
- Data quality checks / 데이터 품질 확인
- Consistency validation / 일관성 검증
- Error reporting / 에러 보고
"""

import pandas as pd
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from ..utils.logger import get_logger
from ..utils.date_parser import DateParser


@dataclass
class ValidationError:
    """
    Represents a data validation error
    데이터 검증 에러를 나타냅니다
    """
    error_type: str  # Type of error / 에러 유형
    severity: str  # critical, warning, info / 심각도
    row_index: Optional[int]  # Row number (if applicable) / 행 번호 (해당하는 경우)
    column: Optional[str]  # Column name / 열 이름
    value: Optional[Any]  # Problematic value / 문제가 있는 값
    message_ko: str  # Korean error message / 한국어 에러 메시지
    message_en: str  # English error message / 영어 에러 메시지
    details: Dict[str, Any] = field(default_factory=dict)  # Additional details / 추가 세부정보


@dataclass
class ValidationResult:
    """
    Result of data validation
    데이터 검증 결과
    """
    is_valid: bool
    total_errors: int = 0
    critical_errors: int = 0
    warnings: int = 0
    infos: int = 0
    errors: List[ValidationError] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class DataValidator:
    """
    Main data validator for HR data sources
    HR 데이터 소스용 메인 데이터 검증기
    """

    def __init__(self, date_parser: Optional[DateParser] = None):
        """
        Initialize DataValidator
        DataValidator 초기화

        Args:
            date_parser: Custom date parser instance / 커스텀 날짜 파서 인스턴스
        """
        self.logger = get_logger()
        self.date_parser = date_parser or DateParser()

        # Expected columns for each data type / 각 데이터 유형에 대한 예상 열
        self.expected_columns = {
            'basic_manpower': {
                'required': ['employee_no', 'name', 'entrance_date'],
                'optional': ['position', 'team', 'stop_working_date', 'resignation_date', 'type']
            },
            'attendance': {
                'required': ['employee_no', 'actual_working_days', 'total_working_days'],
                'optional': ['name', 'position']
            },
            'aql_history': {
                'required': ['employee_no'],
                'optional': ['aql_result', 'failure_count', 'inspection_date']
            },
            '5prs': {
                'required': ['employee_no'],
                'optional': ['rating', 'score']
            }
        }

    def validate_basic_manpower(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate basic manpower data
        기본 인력 데이터 검증

        Args:
            df: DataFrame to validate / 검증할 DataFrame

        Returns:
            ValidationResult with validation results / 검증 결과가 있는 ValidationResult

        Examples:
            >>> validator = DataValidator()
            >>> df = pd.DataFrame({'employee_no': [1, 2], 'name': ['A', 'B']})
            >>> result = validator.validate_basic_manpower(df)
            >>> print(result.is_valid)
        """
        errors: List[ValidationError] = []

        # 1. Schema validation / 스키마 검증
        schema_errors = self._validate_schema(df, 'basic_manpower')
        errors.extend(schema_errors)

        # 2. Required field validation / 필수 필드 검증
        required_errors = self._validate_required_fields(
            df,
            required_fields=['employee_no', 'name', 'entrance_date']
        )
        errors.extend(required_errors)

        # 3. Date field validation / 날짜 필드 검증
        date_errors = self._validate_date_fields(
            df,
            date_columns=['entrance_date', 'stop_working_date', 'resignation_date']
        )
        errors.extend(date_errors)

        # 4. Temporal logic validation / 시간 논리 검증
        temporal_errors = self._validate_temporal_logic(df)
        errors.extend(temporal_errors)

        # 5. Duplicate check / 중복 확인
        duplicate_errors = self._check_duplicates(df, 'employee_no')
        errors.extend(duplicate_errors)

        # 6. Employee number format / 사원번호 형식
        empno_errors = self._validate_employee_numbers(df)
        errors.extend(empno_errors)

        return self._build_validation_result(errors)

    def validate_attendance(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate attendance data
        출근 데이터 검증

        Args:
            df: DataFrame to validate / 검증할 DataFrame

        Returns:
            ValidationResult / 검증 결과
        """
        errors: List[ValidationError] = []

        # 1. Schema validation / 스키마 검증
        schema_errors = self._validate_schema(df, 'attendance')
        errors.extend(schema_errors)

        # 2. Required fields / 필수 필드
        required_errors = self._validate_required_fields(
            df,
            required_fields=['employee_no', 'actual_working_days', 'total_working_days']
        )
        errors.extend(required_errors)

        # 3. Numeric validation / 숫자 검증
        numeric_errors = self._validate_numeric_fields(
            df,
            numeric_columns=['actual_working_days', 'total_working_days']
        )
        errors.extend(numeric_errors)

        # 4. Attendance logic / 출근 논리
        attendance_errors = self._validate_attendance_logic(df)
        errors.extend(attendance_errors)

        # 5. Duplicate check / 중복 확인
        duplicate_errors = self._check_duplicates(df, 'employee_no')
        errors.extend(duplicate_errors)

        return self._build_validation_result(errors)

    def validate_consistency(
        self,
        basic_manpower: pd.DataFrame,
        attendance: pd.DataFrame,
        aql_history: Optional[pd.DataFrame] = None,
        prs_data: Optional[pd.DataFrame] = None
    ) -> ValidationResult:
        """
        Validate data consistency across multiple sources
        여러 소스 간 데이터 일관성 검증

        Args:
            basic_manpower: Basic manpower DataFrame / 기본 인력 DataFrame
            attendance: Attendance DataFrame / 출근 DataFrame
            aql_history: AQL history DataFrame (optional) / AQL 이력 DataFrame (선택)
            prs_data: 5PRS data DataFrame (optional) / 5PRS 데이터 DataFrame (선택)

        Returns:
            ValidationResult / 검증 결과
        """
        errors: List[ValidationError] = []

        # 1. Check employee consistency between sources
        # 소스 간 직원 일관성 확인
        if not attendance.empty:
            consistency_errors = self._check_employee_consistency(
                basic_manpower,
                attendance,
                'attendance'
            )
            errors.extend(consistency_errors)

        # 2. Check for orphaned records in attendance
        # 출근 데이터의 고아 레코드 확인
        if not attendance.empty and not basic_manpower.empty:
            orphan_errors = self._check_orphaned_records(
                basic_manpower,
                attendance,
                'employee_no',
                'attendance'
            )
            errors.extend(orphan_errors)

        # 3. Check AQL consistency if provided / AQL 일관성 확인 (제공된 경우)
        if aql_history is not None and not aql_history.empty:
            aql_errors = self._check_employee_consistency(
                basic_manpower,
                aql_history,
                'aql_history'
            )
            errors.extend(aql_errors)

        # 4. Check 5PRS consistency if provided / 5PRS 일관성 확인 (제공된 경우)
        if prs_data is not None and not prs_data.empty:
            prs_errors = self._check_employee_consistency(
                basic_manpower,
                prs_data,
                '5prs'
            )
            errors.extend(prs_errors)

        return self._build_validation_result(errors)

    def _validate_schema(self, df: pd.DataFrame, data_type: str) -> List[ValidationError]:
        """
        Validate DataFrame schema against expected columns
        예상 열에 대해 DataFrame 스키마 검증

        Args:
            df: DataFrame to validate / 검증할 DataFrame
            data_type: Type of data (basic_manpower, attendance, etc.)
                      데이터 유형

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        if data_type not in self.expected_columns:
            return errors

        expected = self.expected_columns[data_type]
        required_cols = set(expected['required'])
        actual_cols = set(df.columns)

        # Check for missing required columns / 누락된 필수 열 확인
        missing_cols = required_cols - actual_cols

        for col in missing_cols:
            errors.append(ValidationError(
                error_type='schema_missing_column',
                severity='critical',
                row_index=None,
                column=col,
                value=None,
                message_ko=f"필수 열 누락: {col}",
                message_en=f"Missing required column: {col}",
                details={'data_type': data_type}
            ))

        return errors

    def _validate_required_fields(
        self,
        df: pd.DataFrame,
        required_fields: List[str]
    ) -> List[ValidationError]:
        """
        Validate that required fields have non-null values
        필수 필드에 null이 아닌 값이 있는지 검증

        Args:
            df: DataFrame to validate / 검증할 DataFrame
            required_fields: List of required field names / 필수 필드 이름 목록

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        for field in required_fields:
            if field not in df.columns:
                continue

            null_mask = df[field].isnull()
            null_indices = df[null_mask].index.tolist()

            for idx in null_indices:
                errors.append(ValidationError(
                    error_type='required_field_null',
                    severity='critical',
                    row_index=int(idx),
                    column=field,
                    value=None,
                    message_ko=f"필수 필드가 비어있습니다: {field}",
                    message_en=f"Required field is empty: {field}"
                ))

        return errors

    def _validate_date_fields(
        self,
        df: pd.DataFrame,
        date_columns: List[str]
    ) -> List[ValidationError]:
        """
        Validate date fields for proper format
        올바른 형식의 날짜 필드 검증

        Args:
            df: DataFrame to validate / 검증할 DataFrame
            date_columns: List of date column names / 날짜 열 이름 목록

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        for col in date_columns:
            if col not in df.columns:
                continue

            for idx, value in df[col].items():
                if pd.notna(value):
                    parsed_date = self.date_parser.parse_date(value)
                    if parsed_date is None:
                        errors.append(ValidationError(
                            error_type='invalid_date_format',
                            severity='warning',
                            row_index=int(idx),
                            column=col,
                            value=value,
                            message_ko=f"잘못된 날짜 형식: {value}",
                            message_en=f"Invalid date format: {value}"
                        ))

        return errors

    def _validate_temporal_logic(self, df: pd.DataFrame) -> List[ValidationError]:
        """
        Validate temporal logic (e.g., entrance_date < stop_working_date)
        시간 논리 검증 (예: entrance_date < stop_working_date)

        Args:
            df: DataFrame to validate / 검증할 DataFrame

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        if 'entrance_date' not in df.columns:
            return errors

        for idx, row in df.iterrows():
            entrance = self.date_parser.parse_date(row.get('entrance_date'))
            stop = self.date_parser.parse_date(row.get('stop_working_date'))

            if entrance and stop and entrance > stop:
                errors.append(ValidationError(
                    error_type='temporal_logic_error',
                    severity='critical',
                    row_index=int(idx),
                    column='entrance_date',
                    value=None,
                    message_ko=f"입사일이 퇴사일보다 늦습니다",
                    message_en=f"Entrance date is later than stop working date",
                    details={
                        'entrance_date': str(entrance),
                        'stop_working_date': str(stop)
                    }
                ))

            # Check if entrance_date is in the future / 입사일이 미래인지 확인
            if entrance and entrance > datetime.now():
                errors.append(ValidationError(
                    error_type='future_entrance_date',
                    severity='warning',
                    row_index=int(idx),
                    column='entrance_date',
                    value=str(entrance),
                    message_ko=f"입사일이 미래입니다",
                    message_en=f"Entrance date is in the future"
                ))

        return errors

    def _validate_numeric_fields(
        self,
        df: pd.DataFrame,
        numeric_columns: List[str]
    ) -> List[ValidationError]:
        """
        Validate numeric fields for proper type and range
        올바른 유형 및 범위의 숫자 필드 검증

        Args:
            df: DataFrame to validate / 검증할 DataFrame
            numeric_columns: List of numeric column names / 숫자 열 이름 목록

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        for col in numeric_columns:
            if col not in df.columns:
                continue

            for idx, value in df[col].items():
                if pd.notna(value):
                    try:
                        numeric_value = float(value)
                        if numeric_value < 0:
                            errors.append(ValidationError(
                                error_type='negative_numeric_value',
                                severity='critical',
                                row_index=int(idx),
                                column=col,
                                value=value,
                                message_ko=f"음수 값은 허용되지 않습니다: {value}",
                                message_en=f"Negative value not allowed: {value}"
                            ))
                    except (ValueError, TypeError):
                        errors.append(ValidationError(
                            error_type='invalid_numeric_format',
                            severity='critical',
                            row_index=int(idx),
                            column=col,
                            value=value,
                            message_ko=f"잘못된 숫자 형식: {value}",
                            message_en=f"Invalid numeric format: {value}"
                        ))

        return errors

    def _validate_attendance_logic(self, df: pd.DataFrame) -> List[ValidationError]:
        """
        Validate attendance-specific logic
        출근 관련 논리 검증

        Args:
            df: DataFrame to validate / 검증할 DataFrame

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        if 'actual_working_days' not in df.columns or 'total_working_days' not in df.columns:
            return errors

        for idx, row in df.iterrows():
            actual = row.get('actual_working_days')
            total = row.get('total_working_days')

            if pd.notna(actual) and pd.notna(total):
                try:
                    actual_num = float(actual)
                    total_num = float(total)

                    # Actual should not exceed total / 실제가 총계를 초과하면 안 됨
                    if actual_num > total_num:
                        errors.append(ValidationError(
                            error_type='attendance_logic_error',
                            severity='critical',
                            row_index=int(idx),
                            column='actual_working_days',
                            value=actual,
                            message_ko=f"실제 근무일이 총 근무일을 초과합니다",
                            message_en=f"Actual working days exceeds total working days",
                            details={
                                'actual': actual_num,
                                'total': total_num
                            }
                        ))

                    # Both should be positive / 둘 다 양수여야 함
                    if total_num == 0 and actual_num > 0:
                        errors.append(ValidationError(
                            error_type='zero_total_working_days',
                            severity='warning',
                            row_index=int(idx),
                            column='total_working_days',
                            value=total,
                            message_ko=f"총 근무일이 0인데 실제 근무일이 있습니다",
                            message_en=f"Total working days is 0 but actual working days exists"
                        ))

                except (ValueError, TypeError):
                    pass  # Numeric validation will catch this / 숫자 검증에서 처리

        return errors

    def _check_duplicates(self, df: pd.DataFrame, column: str) -> List[ValidationError]:
        """
        Check for duplicate values in a column
        열에서 중복 값 확인

        Args:
            df: DataFrame to check / 확인할 DataFrame
            column: Column name to check for duplicates / 중복 확인할 열 이름

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        if column not in df.columns:
            return errors

        duplicates = df[df[column].duplicated(keep=False)]

        if not duplicates.empty:
            duplicate_values = duplicates[column].unique()

            for value in duplicate_values:
                indices = df[df[column] == value].index.tolist()
                errors.append(ValidationError(
                    error_type='duplicate_value',
                    severity='critical',
                    row_index=None,
                    column=column,
                    value=value,
                    message_ko=f"중복된 값: {value}",
                    message_en=f"Duplicate value: {value}",
                    details={'row_indices': indices}
                ))

        return errors

    def _validate_employee_numbers(self, df: pd.DataFrame) -> List[ValidationError]:
        """
        Validate employee number format
        사원번호 형식 검증

        Args:
            df: DataFrame to validate / 검증할 DataFrame

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        if 'employee_no' not in df.columns:
            return errors

        # Employee numbers should be non-empty strings or integers
        # 사원번호는 비어있지 않은 문자열 또는 정수여야 함
        for idx, value in df['employee_no'].items():
            if pd.isna(value) or str(value).strip() == '':
                errors.append(ValidationError(
                    error_type='invalid_employee_number',
                    severity='critical',
                    row_index=int(idx),
                    column='employee_no',
                    value=value,
                    message_ko=f"잘못된 사원번호",
                    message_en=f"Invalid employee number"
                ))

        return errors

    def _check_employee_consistency(
        self,
        base_df: pd.DataFrame,
        check_df: pd.DataFrame,
        data_source: str
    ) -> List[ValidationError]:
        """
        Check if employees in check_df exist in base_df
        check_df의 직원이 base_df에 있는지 확인

        Args:
            base_df: Base DataFrame (usually basic_manpower) / 기본 DataFrame
            check_df: DataFrame to check / 확인할 DataFrame
            data_source: Name of data source being checked / 확인 중인 데이터 소스 이름

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        if 'employee_no' not in base_df.columns or 'employee_no' not in check_df.columns:
            return errors

        base_employees = set(base_df['employee_no'].dropna().astype(str))
        check_employees = set(check_df['employee_no'].dropna().astype(str))

        # Find employees in check_df but not in base_df
        # check_df에는 있지만 base_df에는 없는 직원 찾기
        missing_employees = check_employees - base_employees

        for emp_no in missing_employees:
            errors.append(ValidationError(
                error_type='employee_not_in_base_data',
                severity='warning',
                row_index=None,
                column='employee_no',
                value=emp_no,
                message_ko=f"{data_source}에 있지만 기본 인력 데이터에 없는 직원: {emp_no}",
                message_en=f"Employee in {data_source} but not in base manpower data: {emp_no}",
                details={'data_source': data_source}
            ))

        return errors

    def _check_orphaned_records(
        self,
        base_df: pd.DataFrame,
        check_df: pd.DataFrame,
        key_column: str,
        data_source: str
    ) -> List[ValidationError]:
        """
        Check for orphaned records (records in check_df without matching base_df)
        고아 레코드 확인 (base_df와 일치하지 않는 check_df의 레코드)

        Args:
            base_df: Base DataFrame / 기본 DataFrame
            check_df: DataFrame to check / 확인할 DataFrame
            key_column: Column to use for matching / 매칭에 사용할 열
            data_source: Name of data source / 데이터 소스 이름

        Returns:
            List of validation errors / 검증 에러 목록
        """
        errors = []

        if key_column not in base_df.columns or key_column not in check_df.columns:
            return errors

        base_keys = set(base_df[key_column].dropna().astype(str))
        orphaned_rows = check_df[~check_df[key_column].astype(str).isin(base_keys)]

        for idx, row in orphaned_rows.iterrows():
            errors.append(ValidationError(
                error_type='orphaned_record',
                severity='warning',
                row_index=int(idx),
                column=key_column,
                value=row[key_column],
                message_ko=f"{data_source}에 고아 레코드",
                message_en=f"Orphaned record in {data_source}",
                details={'data_source': data_source}
            ))

        return errors

    def _build_validation_result(self, errors: List[ValidationError]) -> ValidationResult:
        """
        Build ValidationResult from list of errors
        에러 목록에서 ValidationResult 구성

        Args:
            errors: List of validation errors / 검증 에러 목록

        Returns:
            ValidationResult / 검증 결과
        """
        critical_errors = [e for e in errors if e.severity == 'critical']
        warnings = [e for e in errors if e.severity == 'warning']
        infos = [e for e in errors if e.severity == 'info']

        # Count errors by type / 유형별 에러 수 계산
        error_counts = {}
        for error in errors:
            error_type = error.error_type
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        return ValidationResult(
            is_valid=len(critical_errors) == 0,
            total_errors=len(errors),
            critical_errors=len(critical_errors),
            warnings=len(warnings),
            infos=len(infos),
            errors=errors,
            summary={
                'error_counts_by_type': error_counts,
                'critical_errors_list': [e.message_en for e in critical_errors],
                'validation_timestamp': datetime.now().isoformat()
            }
        )
