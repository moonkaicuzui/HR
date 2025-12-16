"""
error_detector.py - Comprehensive Error Detection System
종합 에러 감지 시스템

Detects data quality issues across all HR data sources.
모든 HR 데이터 소스의 데이터 품질 문제를 감지합니다.

Core Features / 핵심 기능:
- 6 error categories (temporal, type, position, team, attendance, duplicate)
  6가지 에러 카테고리
- Severity classification (critical, warning, info) / 심각도 분류
- JSON export for dashboards / 대시보드용 JSON 내보내기
- Reusable across different data sources / 다양한 데이터 소스에서 재사용 가능
"""

import pandas as pd
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.date_parser import DateParser
from .data_validator import DataValidator, ValidationError, ValidationResult


class ErrorDetector:
    """
    Comprehensive error detector for HR data
    HR 데이터용 종합 에러 감지기

    This extends DataValidator with dashboard-specific error categorization
    and JSON export capabilities.
    이것은 대시보드 전용 에러 분류 및 JSON 내보내기 기능으로 DataValidator를 확장합니다.
    """

    def __init__(
        self,
        year: int,
        month: int,
        latest_data_date: Optional[datetime] = None,
        date_parser: Optional[DateParser] = None
    ):
        """
        Initialize ErrorDetector
        ErrorDetector 초기화

        Args:
            year: Year for error detection context / 에러 감지 컨텍스트 년도
            month: Month for error detection context / 에러 감지 컨텍스트 월
            latest_data_date: Latest date in actual data / 실제 데이터의 최신 날짜
            date_parser: Custom date parser / 커스텀 날짜 파서
        """
        self.logger = get_logger()
        self.date_parser = date_parser or DateParser()
        self.validator = DataValidator(date_parser=date_parser)

        self.year = year
        self.month = month

        # Calculate month boundaries / 월 경계 계산
        self.month_start = pd.Timestamp(year, month, 1)
        if month == 12:
            self.month_end = pd.Timestamp(year + 1, 1, 1) - pd.Timedelta(days=1)
        else:
            self.month_end = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)

        # Set latest data date / 최신 데이터 날짜 설정
        if latest_data_date:
            self.latest_data_date = latest_data_date
        else:
            # Default to end of month / 기본값은 월말
            self.latest_data_date = self.month_end

        # Error storage / 에러 저장소
        self.errors = {
            'temporal_errors': [],
            'type_errors': [],
            'position_errors': [],
            'team_errors': [],
            'attendance_errors': [],
            'duplicate_errors': [],
            'summary': {
                'total_errors': 0,
                'critical': 0,
                'warning': 0,
                'info': 0,
                'detection_timestamp': None
            }
        }

    def detect_all_errors(
        self,
        basic_manpower: pd.DataFrame,
        attendance: Optional[pd.DataFrame] = None,
        team_structure: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Detect all error types across data sources
        데이터 소스 전반에 걸쳐 모든 에러 유형 감지

        Args:
            basic_manpower: Basic manpower DataFrame / 기본 인력 DataFrame
            attendance: Attendance DataFrame (optional) / 출근 DataFrame (선택)
            team_structure: Team structure mapping (optional) / 팀 구조 매핑 (선택)

        Returns:
            Dictionary with all detected errors / 감지된 모든 에러 딕셔너리

        Examples:
            >>> detector = ErrorDetector(2025, 9)
            >>> errors = detector.detect_all_errors(manpower_df, attendance_df)
            >>> print(f"Total errors: {errors['summary']['total_errors']}")
        """
        self.logger.info(
            "종합 에러 감지 시작",
            "Starting comprehensive error detection",
            year=self.year,
            month=self.month
        )

        # Reset errors / 에러 초기화
        self.errors = {
            'temporal_errors': [],
            'type_errors': [],
            'position_errors': [],
            'team_errors': [],
            'attendance_errors': [],
            'duplicate_errors': [],
            'summary': {
                'total_errors': 0,
                'critical': 0,
                'warning': 0,
                'info': 0,
                'detection_timestamp': datetime.now().isoformat()
            }
        }

        # Skip error detection if basic_manpower is empty (NO FAKE DATA policy)
        # basic_manpower가 비어있으면 에러 감지 건너뛰기 (가짜 데이터 금지 정책)
        if basic_manpower.empty:
            self.logger.info(
                "기본 인력 데이터가 없어 에러 감지를 건너뜁니다",
                "Skipping error detection - no basic manpower data available"
            )
            return self.errors

        # 1. Temporal Errors / 시간 관련 에러
        self._detect_temporal_errors(basic_manpower)

        # 2. TYPE Errors / TYPE 에러
        self._detect_type_errors(basic_manpower)

        # 3. Position Errors / 직급 에러
        self._detect_position_errors(basic_manpower)

        # 4. Team Errors / 팀 에러
        if team_structure is not None and isinstance(team_structure, dict) and team_structure:
            self._detect_team_errors(basic_manpower, team_structure)

        # 5. Attendance Errors / 출근 에러
        if attendance is not None and not attendance.empty:
            self._detect_attendance_errors(attendance, basic_manpower)

        # 6. Duplicate Errors / 중복 에러
        self._detect_duplicate_errors(basic_manpower)

        # Calculate summary / 요약 계산
        self._calculate_summary()

        self.logger.info(
            "에러 감지 완료",
            "Error detection completed",
            total=self.errors['summary']['total_errors'],
            critical=self.errors['summary']['critical']
        )

        return self.errors

    def _add_error(
        self,
        category: str,
        error_data: Dict[str, Any]
    ) -> None:
        """
        Add error to specific category
        특정 카테고리에 에러 추가

        Args:
            category: Error category name / 에러 카테고리 이름
            error_data: Error data dictionary / 에러 데이터 딕셔너리
        """
        self.errors[category].append(error_data)

    def _detect_temporal_errors(self, df: pd.DataFrame) -> None:
        """
        Detect temporal/date-related errors
        시간/날짜 관련 에러 감지

        Args:
            df: Basic manpower DataFrame / 기본 인력 DataFrame
        """
        self.logger.debug("시간 관련 에러 감지 중", "Detecting temporal errors")

        # Normalize column names / 열 이름 정규화
        df_copy = df.copy()
        df_copy.columns = [col.lower().replace(' ', '_') for col in df_copy.columns]

        # Future employees (입사일이 데이터 기준일 이후)
        if 'entrance_date' in df_copy.columns:
            for idx, row in df_copy.iterrows():
                entrance_date = self.date_parser.parse_date(row.get('entrance_date'))

                if entrance_date and entrance_date > self.latest_data_date:
                    self._add_error('temporal_errors', {
                        'id': str(row.get('employee_no', row.get('id_no', 'N/A'))),
                        'name': str(row.get('full_name', row.get('name', 'N/A'))),
                        'error_type': '날짜 형태 오류 / Date Format Error',
                        'error_column': 'entrance_date',
                        'error_value': entrance_date.strftime('%Y-%m-%d'),
                        'expected_value': f'{self.latest_data_date.strftime("%Y-%m-%d")} 이전 / before',
                        'severity': 'critical',
                        'description': f'입사일이 데이터 기준일 이후 / Entrance date after data cut-off date',
                        'suggested_action': '날짜 형식 확인 및 수정 / Verify and correct date format'
                    })

        # Invalid date sequences (퇴사일 < 입사일)
        if 'entrance_date' in df_copy.columns and 'stop_working_date' in df_copy.columns:
            for idx, row in df_copy.iterrows():
                entrance = self.date_parser.parse_date(row.get('entrance_date'))
                stop = self.date_parser.parse_date(row.get('stop_working_date'))

                if entrance and stop and stop < entrance:
                    self._add_error('temporal_errors', {
                        'id': str(row.get('employee_no', 'N/A')),
                        'name': str(row.get('full_name', row.get('name', 'N/A'))),
                        'error_type': 'Invalid Date Sequence',
                        'error_column': 'stop_working_date',
                        'error_value': f"Stop: {stop.strftime('%Y-%m-%d')}, Enter: {entrance.strftime('%Y-%m-%d')}",
                        'expected_value': 'Stop Date >= Entrance Date',
                        'severity': 'critical',
                        'description': '퇴사일이 입사일보다 빠름 / Stop date before entrance date',
                        'suggested_action': '날짜 순서 수정 / Correct date sequence',
                        'is_resigned': True
                    })

    def _detect_type_errors(self, df: pd.DataFrame) -> None:
        """
        Detect TYPE classification errors
        TYPE 분류 에러 감지

        Args:
            df: Basic manpower DataFrame / 기본 인력 DataFrame
        """
        self.logger.debug("TYPE 분류 에러 감지 중", "Detecting TYPE classification errors")

        df_copy = df.copy()
        df_copy.columns = [col.lower().replace(' ', '_') for col in df_copy.columns]

        # Check for TYPE column / TYPE 열 확인
        type_col = None
        for possible_name in ['role_type_std', 'type', 'employee_type']:
            if possible_name in df_copy.columns:
                type_col = possible_name
                break

        if not type_col:
            return

        # Missing TYPE / TYPE 누락
        valid_types = ['TYPE-1', 'TYPE-2', 'TYPE-3']
        for idx, row in df_copy.iterrows():
            type_value = str(row.get(type_col, '')).strip()

            if not type_value or type_value == 'nan':
                self._add_error('type_errors', {
                    'id': str(row.get('employee_no', 'N/A')),
                    'name': str(row.get('full_name', row.get('name', 'N/A'))),
                    'error_type': 'Missing TYPE',
                    'error_column': type_col,
                    'error_value': 'NULL/Empty',
                    'expected_value': 'TYPE-1, TYPE-2, or TYPE-3',
                    'severity': 'critical',
                    'description': 'TYPE 분류 누락 / TYPE classification missing',
                    'suggested_action': '적절한 TYPE 할당 / Assign appropriate TYPE'
                })
            elif type_value not in valid_types:
                self._add_error('type_errors', {
                    'id': str(row.get('employee_no', 'N/A')),
                    'name': str(row.get('full_name', row.get('name', 'N/A'))),
                    'error_type': 'Invalid TYPE Value',
                    'error_column': type_col,
                    'error_value': type_value,
                    'expected_value': ', '.join(valid_types),
                    'severity': 'warning',
                    'description': '잘못된 TYPE 값 / Invalid TYPE value',
                    'suggested_action': 'TYPE을 TYPE-1, TYPE-2, TYPE-3 중 하나로 수정 / Correct to valid TYPE'
                })

    def _detect_position_errors(self, df: pd.DataFrame) -> None:
        """
        Detect position/role errors
        직급/역할 에러 감지

        Args:
            df: Basic manpower DataFrame / 기본 인력 DataFrame
        """
        self.logger.debug("직급 에러 감지 중", "Detecting position errors")

        df_copy = df.copy()
        df_copy.columns = [col.lower().replace(' ', '_') for col in df_copy.columns]

        # Check for position columns / 직급 열 확인
        position_columns = [col for col in df_copy.columns if 'position' in col]

        for pos_col in position_columns:
            for idx, row in df_copy.iterrows():
                pos_value = row.get(pos_col)

                if pd.isna(pos_value) or str(pos_value).strip() == '':
                    self._add_error('position_errors', {
                        'id': str(row.get('employee_no', 'N/A')),
                        'name': str(row.get('full_name', row.get('name', 'N/A'))),
                        'error_type': 'Missing Position',
                        'error_column': pos_col,
                        'error_value': 'NULL/Empty',
                        'expected_value': 'Valid position title',
                        'severity': 'warning',
                        'description': f'직급 정보 누락 / Position information missing in {pos_col}',
                        'suggested_action': '직급 정보 입력 / Enter position information'
                    })

    def _detect_team_errors(
        self,
        df: pd.DataFrame,
        team_structure: Dict
    ) -> None:
        """
        Detect team assignment errors
        팀 할당 에러 감지

        Args:
            df: Basic manpower DataFrame / 기본 인력 DataFrame
            team_structure: Team structure mapping / 팀 구조 매핑
        """
        self.logger.debug("팀 할당 에러 감지 중", "Detecting team assignment errors")

        df_copy = df.copy()
        df_copy.columns = [col.lower().replace(' ', '_') for col in df_copy.columns]

        # Check for team column / 팀 열 확인
        if 'team' not in df_copy.columns:
            return

        # Get valid teams from structure / 구조에서 유효한 팀 가져오기
        valid_teams = set(team_structure.keys()) if team_structure else set()

        for idx, row in df_copy.iterrows():
            team_value = str(row.get('team', '')).strip()

            if not team_value or team_value == 'nan':
                self._add_error('team_errors', {
                    'id': str(row.get('employee_no', 'N/A')),
                    'name': str(row.get('full_name', row.get('name', 'N/A'))),
                    'error_type': 'Missing Team Assignment',
                    'error_column': 'team',
                    'error_value': 'NULL/Empty',
                    'expected_value': 'Valid team name',
                    'severity': 'warning',
                    'description': '팀 할당 누락 / Team assignment missing',
                    'suggested_action': '팀 할당 / Assign to team'
                })
            elif valid_teams and team_value not in valid_teams and team_value not in ['Team Unidentified', 'NONE']:
                self._add_error('team_errors', {
                    'id': str(row.get('employee_no', 'N/A')),
                    'name': str(row.get('full_name', row.get('name', 'N/A'))),
                    'error_type': 'Unknown Team',
                    'error_column': 'team',
                    'error_value': team_value,
                    'expected_value': ', '.join(list(valid_teams)[:5]) + '...',
                    'severity': 'info',
                    'description': '알 수 없는 팀 / Unknown team',
                    'suggested_action': '팀 구조에 팀 추가 또는 팀 이름 수정 / Add team to structure or correct name'
                })

    def _detect_attendance_errors(
        self,
        attendance_df: pd.DataFrame,
        basic_manpower_df: pd.DataFrame
    ) -> None:
        """
        Detect attendance data errors
        출근 데이터 에러 감지

        Args:
            attendance_df: Attendance DataFrame / 출근 DataFrame
            basic_manpower_df: Basic manpower DataFrame / 기본 인력 DataFrame
        """
        self.logger.debug("출근 데이터 에러 감지 중", "Detecting attendance errors")

        att_copy = attendance_df.copy()
        att_copy.columns = [col.lower().replace(' ', '_') for col in att_copy.columns]

        # Attendance logic errors (actual > total)
        if 'actual_working_days' in att_copy.columns and 'total_working_days' in att_copy.columns:
            for idx, row in att_copy.iterrows():
                try:
                    actual = float(row.get('actual_working_days', 0))
                    total = float(row.get('total_working_days', 0))

                    if actual > total:
                        self._add_error('attendance_errors', {
                            'id': str(row.get('employee_no', 'N/A')),
                            'name': str(row.get('full_name', row.get('name', 'N/A'))),
                            'error_type': 'Attendance Logic Error',
                            'error_column': 'actual_working_days',
                            'error_value': f'Actual: {actual}, Total: {total}',
                            'expected_value': 'Actual <= Total',
                            'severity': 'critical',
                            'description': '실제 근무일이 총 근무일 초과 / Actual working days exceeds total',
                            'suggested_action': '출근 데이터 확인 및 수정 / Verify and correct attendance data'
                        })
                except (ValueError, TypeError):
                    pass

    def _detect_duplicate_errors(self, df: pd.DataFrame) -> None:
        """
        Detect duplicate employee records
        중복 직원 레코드 감지

        Args:
            df: Basic manpower DataFrame / 기본 인력 DataFrame
        """
        self.logger.debug("중복 레코드 감지 중", "Detecting duplicate records")

        df_copy = df.copy()
        df_copy.columns = [col.lower().replace(' ', '_') for col in df_copy.columns]

        # Check for duplicate employee numbers / 중복 사원번호 확인
        if 'employee_no' in df_copy.columns:
            duplicates = df_copy[df_copy['employee_no'].duplicated(keep=False)]

            for emp_no, group in duplicates.groupby('employee_no'):
                if len(group) > 1:
                    self._add_error('duplicate_errors', {
                        'id': str(emp_no),
                        'name': ', '.join(group['full_name'].astype(str).tolist() if 'full_name' in group.columns else ['N/A']),
                        'error_type': 'Duplicate Employee Number',
                        'error_column': 'employee_no',
                        'error_value': str(emp_no),
                        'expected_value': 'Unique',
                        'severity': 'critical',
                        'description': f'중복 사원번호 ({len(group)}건) / Duplicate employee number ({len(group)} records)',
                        'suggested_action': '중복 레코드 확인 및 제거 / Verify and remove duplicate records',
                        'duplicate_count': len(group)
                    })

    def _calculate_summary(self) -> None:
        """
        Calculate error summary statistics
        에러 요약 통계 계산
        """
        total = 0
        critical = 0
        warning = 0
        info = 0

        for category in ['temporal_errors', 'type_errors', 'position_errors',
                        'team_errors', 'attendance_errors', 'duplicate_errors']:
            for error in self.errors[category]:
                total += 1
                severity = error.get('severity', 'info')
                if severity == 'critical':
                    critical += 1
                elif severity == 'warning':
                    warning += 1
                else:
                    info += 1

        self.errors['summary']['total_errors'] = total
        self.errors['summary']['critical'] = critical
        self.errors['summary']['warning'] = warning
        self.errors['summary']['info'] = info

    def export_to_json(self, output_path: str) -> bool:
        """
        Export errors to JSON file
        에러를 JSON 파일로 내보내기

        Args:
            output_path: Output JSON file path / 출력 JSON 파일 경로

        Returns:
            True if successful / 성공 시 True
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, ensure_ascii=False, indent=2)

            self.logger.info(
                "에러 JSON 파일 생성 완료",
                "Error JSON file created successfully",
                path=str(output_file),
                total_errors=self.errors['summary']['total_errors']
            )
            return True

        except Exception as e:
            self.logger.error(
                "에러 JSON 파일 생성 실패",
                "Failed to create error JSON file",
                path=output_path,
                error=str(e)
            )
            return False

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get error summary for display
        표시용 에러 요약 가져오기

        Returns:
            Summary dictionary / 요약 딕셔너리
        """
        return {
            'total_errors': self.errors['summary']['total_errors'],
            'by_severity': {
                'critical': self.errors['summary']['critical'],
                'warning': self.errors['summary']['warning'],
                'info': self.errors['summary']['info']
            },
            'by_category': {
                'temporal': len(self.errors['temporal_errors']),
                'type': len(self.errors['type_errors']),
                'position': len(self.errors['position_errors']),
                'team': len(self.errors['team_errors']),
                'attendance': len(self.errors['attendance_errors']),
                'duplicate': len(self.errors['duplicate_errors'])
            }
        }
