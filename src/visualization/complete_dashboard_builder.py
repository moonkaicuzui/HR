"""
complete_dashboard_builder.py - Complete HR Dashboard Builder (Enhanced Version)
완전한 HR 대시보드 빌더 (향상된 버전)

Enhanced with:
- Vietnamese language support in KPI cards
- Language switching in all modals
- Sortable tables in all modals
- Detailed attendance data integration
- Assignment date calculation (entrance + 30 days)
- Rich visualizations (charts) in all modals
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sys
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.monthly_data_collector import MonthlyDataCollector
from src.analytics.hr_metric_calculator import HRMetricCalculator
from src.analytics.metric_validator import MetricValidator, DataQualityScore
from src.utils.employee_counter import count_employees_by_teams_monthly
from src.visualization.enhanced_modal_generator import EnhancedModalGenerator
from src.utils.i18n import I18n
from src.utils.logger import get_logger


def _load_dashboard_config() -> Dict[str, Any]:
    """
    Load dashboard configuration from JSON file
    대시보드 설정을 JSON 파일에서 로드
    """
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "dashboard_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


# Load team mapping from config (fallback to empty dict)
# 설정에서 팀 매핑 로드 (fallback: 빈 딕셔너리)
_dashboard_config = _load_dashboard_config()
TEAM_MAPPING = _dashboard_config.get('team_mapping', {}).get('teams', {})
TEAM_KEYWORD_MAPPING = _dashboard_config.get('team_mapping', {}).get('keyword_mapping', {})
TEAM_FALLBACK = _dashboard_config.get('team_mapping', {}).get('fallback_team', 'QIP_MANAGER_OFFICE_OCPT')


class CompleteDashboardBuilder:
    """Build complete HR dashboard with all enhanced features"""

    def __init__(self, target_month: str, language: str = 'ko', report_date: Optional[datetime] = None):
        """
        Args:
            target_month: 'YYYY-MM' format
            language: 'ko', 'en', or 'vi'
            report_date: Report generation date (default: today)
        """
        self.target_month = target_month
        self.language = language
        self.hr_root = Path(__file__).parent.parent.parent
        self.report_date = report_date if report_date else datetime.now()

        # Extract year from target_month (format: YYYY-MM)
        # target_month에서 연도 추출
        target_year = int(target_month.split('-')[0]) if '-' in target_month else datetime.now().year

        # Initialize components
        self.collector = MonthlyDataCollector(self.hr_root, target_year=target_year)
        self.calculator = HRMetricCalculator(self.collector, self.report_date)

        # Initialize i18n and logger
        self.i18n = I18n(default_lang=self.language)
        self.i18n.set_language(self.language)
        self.logger = get_logger()

        # Initialize enhanced modal generator
        self.modal_generator = EnhancedModalGenerator(self.i18n, self.calculator, self.logger)

        # Data storage
        self.available_months: List[str] = []
        self.month_labels: List[str] = []
        self.monthly_metrics: Dict[str, Dict[str, Any]] = {}
        self.employee_details: List[Dict[str, Any]] = []
        self.modal_data: Dict[str, Any] = {}  # NEW: Store detailed modal data
        self.team_data: Dict[str, Any] = {}  # NEW: Team-based analysis data (current month)
        self.previous_month_team_data: Dict[str, Any] = {}  # NEW: Previous month team data for comparison
        self.monthly_team_counts: Dict[str, Dict[str, int]] = {}  # NEW: Team counts for each month
        self.hierarchy_data: List[Dict[str, Any]] = []  # NEW: Organization hierarchy data
        self.quality_score: Optional[DataQualityScore] = None  # Data quality score / 데이터 품질 점수
        self.attendance_data: List[Dict[str, Any]] = []  # NEW: Individual attendance records / 개인 출결 기록

    def build(self) -> str:
        """Build complete dashboard HTML"""
        print(f"🔨 Building HR Dashboard for {self.target_month}...")

        # Step 1: Detect available months
        self.available_months = self.collector.get_month_range(self.target_month)
        self.month_labels = self.collector.get_month_labels(self.available_months, self.language)
        print(f"📅 Months: {self.available_months}")

        # Step 2: Calculate metrics
        self.monthly_metrics = self.calculator.calculate_all_metrics(self.available_months)
        print(f"📊 Metrics calculated for {len(self.monthly_metrics)} months")

        # Step 2.5: Validate metrics and calculate data quality score
        # 메트릭 검증 및 데이터 품질 점수 계산
        self._validate_metrics()
        print(f"✅ Data quality score: {self.quality_score.score:.1f}% (Grade: {self.quality_score.grade})")

        # Step 3: Collect employee details
        self._collect_employee_details()
        print(f"👥 Employee details: {len(self.employee_details)} employees")

        # Step 4: Collect modal-specific data
        self._collect_modal_data()
        print(f"📋 Modal data collected")

        # Step 4.5: Collect team-based data
        self.team_data = self._collect_team_data()
        print(f"🏢 Team data collected: {len(self.team_data)} teams")

        # Step 4.5.1: Collect previous month team data for comparison
        self.previous_month_team_data = self._collect_previous_month_team_data()
        print(f"🏢 Previous month team data collected: {len(self.previous_month_team_data)} teams")

        # Step 4.5.2: Calculate team counts for all months
        self._calculate_monthly_team_counts()
        print(f"📊 Monthly team counts calculated for {len(self.monthly_team_counts)} months")

        # Step 4.6: Build organization hierarchy
        self.hierarchy_data = self._build_hierarchy_data()
        print(f"🌳 Organization hierarchy built: {len(self.hierarchy_data)} root nodes")

        # Step 4.7: Collect individual attendance data
        # 개인 출결 데이터 수집
        self._collect_attendance_data()
        print(f"📅 Attendance data collected: {len(self.attendance_data)} records")

        # Step 5: Generate HTML
        html = self._generate_html()

        # Step 6: Fix JavaScript template literals (convert {{ to { and }} to })
        # This fixes the issue where JavaScript code has double braces from Python string formatting
        html = html.replace('{{', '{').replace('}}', '}')
        print(f"✅ Dashboard HTML generated")

        return html

    def _validate_metrics(self) -> None:
        """
        Validate calculated metrics and compute data quality score
        계산된 메트릭 검증 및 데이터 품질 점수 계산
        """
        # Get target month metrics for validation
        # 검증용 대상 월 메트릭 가져오기
        target_metrics = self.monthly_metrics.get(self.target_month, {})

        # Initialize validator and run validation
        # 검증기 초기화 및 검증 실행
        validator = MetricValidator()
        self.quality_score = validator.validate_metrics(target_metrics)

        # Log any warnings
        # 경고 로그 기록
        if self.quality_score.warnings:
            for warning in self.quality_score.warnings:
                if warning.severity == 'error':
                    self.logger.warning(f"❌ {warning.message_ko}")
                else:
                    self.logger.info(f"⚠️ {warning.message_ko}")

    def _extract_team_from_position(self, position_str: str) -> str:
        """
        Extract team name from position string using config-driven keyword mapping
        설정 기반 키워드 매핑을 사용하여 직급 문자열에서 팀 이름 추출

        Uses keyword_mapping from dashboard_config.json for consistency
        일관성을 위해 dashboard_config.json의 keyword_mapping 사용

        Args:
            position_str: Position string (QIP POSITION 3RD NAME preferred)

        Returns:
            Team name (ASSEMBLY, STITCHING, etc.) or fallback team
        """
        if pd.isna(position_str) or not position_str:
            return TEAM_FALLBACK

        position = str(position_str).upper()

        # Use config-driven keyword mapping
        # 설정 기반 키워드 매핑 사용
        for team_name, keywords in TEAM_KEYWORD_MAPPING.items():
            for keyword in keywords:
                if keyword.upper() in position:
                    return team_name

        return TEAM_FALLBACK

    def _collect_employee_details(self):
        """Collect employee details with calculated fields for the target month"""
        data = self.collector.load_month_data(self.target_month)
        df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        if df.empty:
            return

        year, month = self.target_month.split('-')
        year_num = int(year)
        month_num = int(month)
        end_of_month = pd.Timestamp(f"{year_num}-{month_num:02d}-01") + pd.DateOffset(months=1) - pd.DateOffset(days=1)
        start_of_month = pd.Timestamp(f"{year_num}-{month_num:02d}-01")

        # Build attendance lookup with working days and absent days
        employee_attendance = {}
        if not attendance_df.empty and 'ID No' in attendance_df.columns:
            # Filter attendance data for current month
            if 'Date' in attendance_df.columns:
                attendance_df_copy = attendance_df.copy()
                attendance_df_copy['Date'] = pd.to_datetime(attendance_df_copy['Date'], errors='coerce')
                month_attendance = attendance_df_copy[
                    (attendance_df_copy['Date'] >= start_of_month) &
                    (attendance_df_copy['Date'] <= end_of_month)
                ]
            else:
                month_attendance = attendance_df

            for emp_id in month_attendance['ID No'].unique():
                emp_records = month_attendance[month_attendance['ID No'] == emp_id]
                working_days = len(emp_records)
                absent_days = 0
                if 'compAdd' in emp_records.columns:
                    absent_days = len(emp_records[emp_records['compAdd'] == 'Vắng mặt'])

                employee_attendance[emp_id] = {
                    'working_days': working_days,
                    'absent_days': absent_days
                }

        # Build absence sets
        absent_employees = set()
        unauthorized_absent_employees = set()
        if not attendance_df.empty and 'ID No' in attendance_df.columns:
            if 'compAdd' in attendance_df.columns:
                absent_employees = set(attendance_df[attendance_df['compAdd'] == 'Vắng mặt']['ID No'].unique())
            if 'Reason Description' in attendance_df.columns:
                # Match unauthorized patterns: AR1, AR2 / 무단결근 패턴 매칭: AR1, AR2
                unauthorized_pattern = 'AR1|AR2|Không phép|Vắng không phép'
                unauthorized_absent_employees = set(
                    attendance_df[attendance_df['Reason Description'].str.contains(unauthorized_pattern, na=False, case=False)]['ID No'].unique()
                )

        for _, row in df.iterrows():
            employee_id = row.get('Employee No', '')
            entrance_date = pd.to_datetime(row.get('Entrance Date', ''), errors='coerce', dayfirst=False)
            stop_date = pd.to_datetime(row.get('Stop working Date', ''), errors='coerce', dayfirst=False)

            # Get attendance data
            att_data = employee_attendance.get(employee_id, {'working_days': 0, 'absent_days': 0})
            working_days = att_data['working_days']
            absent_days = att_data['absent_days']

            # Calculate tenure days (from month end)
            tenure_days = 0
            if pd.notna(entrance_date):
                tenure_days = (end_of_month - entrance_date).days

            # Calculate assignment date (entrance + 30 days)
            assignment_date = None
            if pd.notna(entrance_date):
                assignment_date = entrance_date + timedelta(days=30)

            # Determine employee status
            # 직원 상태 결정
            is_active = pd.isna(stop_date) or stop_date > end_of_month
            hired_this_month = pd.notna(entrance_date) and entrance_date.year == year_num and entrance_date.month == month_num
            resigned_this_month = pd.notna(stop_date) and stop_date.year == year_num and stop_date.month == month_num

            # under_60_days: Active employees with tenure < 60 days only
            # 60일 미만 재직자: 재직 중인 직원만 (퇴사자 제외)
            under_60_days = is_active and tenure_days > 0 and tenure_days < 60

            # long_term: Active employees with 1+ year tenure only
            # 장기근속자: 재직 중인 직원만 (퇴사자 제외)
            long_term = is_active and pd.notna(entrance_date) and (start_of_month - entrance_date).days >= 365

            # perfect_attendance: Active employees with working_days > 0 and absent_days == 0
            # 개근자: 재직 중이고, 출근일이 있고, 결근일이 0인 직원
            perfect_attendance = is_active and working_days > 0 and absent_days == 0

            has_unauthorized_absence = employee_id in unauthorized_absent_employees

            # Post-assignment resignation (resigned between 30-60 days after hire)
            # 배치 후 퇴사: 입사 후 30~60일 사이에 퇴사한 경우
            # This indicates turnover after initial training/assignment period
            post_assignment_resignation = False
            if resigned_this_month and pd.notna(entrance_date) and pd.notna(stop_date):
                tenure_at_resignation = (stop_date - entrance_date).days
                post_assignment_resignation = 30 < tenure_at_resignation <= 60

            # Data error detection (데이터 오류 감지)
            has_data_error = False
            error_type = ''
            error_description = ''

            # 1. Missing required fields (필수 필드 누락)
            if not employee_id or pd.isna(employee_id):
                has_data_error = True
                error_type = 'missing_id'
                error_description = 'Employee No is missing'
            elif not row.get('Full Name', ''):
                has_data_error = True
                error_type = 'missing_name'
                error_description = 'Full Name is missing'
            # 2. TYPE error (TYPE 오류)
            role_type = row.get('ROLE TYPE STD', '')
            if not role_type or role_type not in ['TYPE-1', 'TYPE-2', 'TYPE-3']:
                has_data_error = True
                error_type = 'type_error'
                error_description = f'Invalid TYPE: {role_type or "empty"}'
            # 3. Temporal error (시간 오류)
            if pd.notna(entrance_date) and entrance_date > end_of_month:
                has_data_error = True
                error_type = 'temporal_error'
                error_description = 'Entrance date is in the future'
            if pd.notna(stop_date) and pd.notna(entrance_date) and stop_date < entrance_date:
                has_data_error = True
                error_type = 'temporal_error'
                error_description = 'Stop date is before entrance date'
            # 4. Attendance error (출근 오류)
            if absent_days > working_days and working_days > 0:
                has_data_error = True
                error_type = 'attendance_error'
                error_description = f'Absent days ({absent_days}) > Working days ({working_days})'

            # Get additional fields
            incentive = row.get('Final Incentive amount', 0)
            if pd.notna(incentive):
                try:
                    incentive = float(incentive)
                except (ValueError, TypeError):
                    incentive = 0
            else:
                incentive = 0

            pregnant_status = row.get('pregnant vacation-yes or no', '')
            is_pregnant = str(pregnant_status).lower() == 'yes' if pregnant_status else False

            # Map position to team using QIP POSITION 3RD NAME (more accurate)
            # QIP POSITION 3RD NAME을 사용하여 팀 매핑 (더 정확함)
            position_3rd = row.get('QIP POSITION 3RD  NAME', '')
            position_2nd = row.get('QIP POSITION 2ND  NAME', '')
            position_1st = row.get('QIP POSITION 1ST  NAME', '')

            # Use the best available position column for team extraction
            # 팀 추출을 위해 가장 적합한 position 컬럼 사용
            position_for_team = position_3rd or position_2nd or position_1st or ''
            team_name = self._extract_team_from_position(position_for_team)

            self.employee_details.append({
                'employee_id': str(employee_id),
                'employee_no': str(employee_id),  # Add alias
                'employee_name': row.get('Full Name', ''),
                'full_name': row.get('Full Name', ''),  # Add alias
                'position': row.get('FINAL QIP POSITION NAME CODE', ''),
                'position_1st': position_1st,
                'position_2nd': row.get('QIP POSITION 2ND  NAME', ''),
                'position_3rd': row.get('QIP POSITION 3RD  NAME', ''),
                'role_type': row.get('ROLE TYPE STD', ''),
                'TYPE': row.get('ROLE TYPE STD', ''),  # Add TYPE alias for chart
                'team': team_name,  # Add team field
                'team_name': team_name,  # Add team_name alias
                'building': row.get('BUILDING', ''),
                'line': row.get('LINE', ''),
                'boss_name': row.get('Boss name', ''),
                'incentive': round(incentive, 0),
                'is_pregnant': is_pregnant,
                'entrance_date': entrance_date.strftime('%Y-%m-%d') if pd.notna(entrance_date) else '',
                'stop_date': stop_date.strftime('%Y-%m-%d') if pd.notna(stop_date) else '',
                'assignment_date': assignment_date.strftime('%Y-%m-%d') if assignment_date else '',
                'tenure_days': int(tenure_days) if tenure_days > 0 else 0,
                'years_of_service': f"{tenure_days} days" if tenure_days > 0 else '0 days',
                'working_days': working_days,
                'absent_days': absent_days,
                'is_active': is_active,
                'hired_this_month': hired_this_month,
                'resigned_this_month': resigned_this_month,
                'under_60_days': under_60_days,
                'long_term': long_term,
                'perfect_attendance': perfect_attendance,
                'has_unauthorized_absence': has_unauthorized_absence,
                'post_assignment_resignation': post_assignment_resignation,
                'has_data_error': has_data_error,
                'error_type': error_type,
                'error_description': error_description
            })

    def _collect_modal_data(self):
        """Collect detailed data for each modal"""
        data = self.collector.load_month_data(self.target_month)
        attendance_df = data.get('attendance', pd.DataFrame())
        basic_df = data.get('basic_manpower', pd.DataFrame())

        # Modal 2 & 3: Attendance data (exclude resigned employees)
        if not attendance_df.empty and not basic_df.empty:
            # Join attendance with basic_df to get stop dates and pregnancy status
            # Use 'Employee No' from basic_df, which matches 'ID No' in attendance_df
            basic_cols_to_merge = basic_df[['Employee No', 'Stop working Date', 'pregnant vacation-yes or no']].copy()
            basic_cols_to_merge.rename(columns={'Employee No': 'ID No'}, inplace=True)

            attendance_with_info = attendance_df.merge(
                basic_cols_to_merge,
                on='ID No',
                how='left'
            )

            # Filter to only active employees (exclude resigned)
            stop_dates = pd.to_datetime(attendance_with_info['Stop working Date'], errors='coerce')
            active_attendance = attendance_with_info[(stop_dates.isna()) | (stop_dates > self.report_date)]

            # Absence details (only active employees)
            if 'compAdd' in active_attendance.columns and 'ID No' in active_attendance.columns:
                absence_records = active_attendance[active_attendance['compAdd'] == 'Vắng mặt'].copy()

                # Also calculate maternity-excluded absence
                pregnant_status = absence_records['pregnant vacation-yes or no'].astype(str).str.lower()
                non_pregnant_absence = absence_records[pregnant_status != 'yes']

                self.modal_data['absence_details'] = []
                for emp_id in absence_records['ID No'].unique():
                    emp_absences = absence_records[absence_records['ID No'] == emp_id]
                    emp_name = emp_absences['Last name'].iloc[0] if 'Last name' in emp_absences.columns else ''
                    is_pregnant = emp_absences['pregnant vacation-yes or no'].iloc[0]
                    is_pregnant = str(is_pregnant).lower() == 'yes' if pd.notna(is_pregnant) else False

                    self.modal_data['absence_details'].append({
                        'employee_id': str(emp_id),
                        'employee_name': emp_name,
                        'absence_count': len(emp_absences),
                        'is_pregnant': is_pregnant,
                        'dates': emp_absences['Work Date'].tolist() if 'Work Date' in emp_absences.columns else []
                    })

                # Store maternity exclusion metrics for charts
                total_attendance_records = len(active_attendance)
                total_absences = len(absence_records)
                non_pregnant_absences = len(non_pregnant_absence)

                self.modal_data['absence_metrics'] = {
                    'overall_rate': round((total_absences / total_attendance_records * 100), 1) if total_attendance_records > 0 else 0,
                    'excluding_maternity_rate': round((non_pregnant_absences / total_attendance_records * 100), 1) if total_attendance_records > 0 else 0,
                    'total_records': total_attendance_records,
                    'total_absences': total_absences,
                    'non_pregnant_absences': non_pregnant_absences
                }

            # Unauthorized absence details (only active employees)
            if 'Reason Description' in active_attendance.columns:
                # Match unauthorized patterns: AR1, AR2 / 무단결근 패턴 매칭: AR1, AR2
                unauthorized_pattern = 'AR1|AR2|Không phép|Vắng không phép'
                unauthorized_records = active_attendance[
                    active_attendance['Reason Description'].str.contains(unauthorized_pattern, na=False, case=False)
                ].copy()

                # Also calculate maternity-excluded unauthorized absence
                pregnant_status = unauthorized_records['pregnant vacation-yes or no'].astype(str).str.lower()
                non_pregnant_unauthorized = unauthorized_records[pregnant_status != 'yes']

                self.modal_data['unauthorized_details'] = []
                for emp_id in unauthorized_records['ID No'].unique():
                    emp_records = unauthorized_records[unauthorized_records['ID No'] == emp_id]
                    emp_name = emp_records['Last name'].iloc[0] if 'Last name' in emp_records.columns else ''
                    is_pregnant = emp_records['pregnant vacation-yes or no'].iloc[0]
                    is_pregnant = str(is_pregnant).lower() == 'yes' if pd.notna(is_pregnant) else False

                    self.modal_data['unauthorized_details'].append({
                        'employee_id': str(emp_id),
                        'employee_name': emp_name,
                        'unauthorized_count': len(emp_records),
                        'is_pregnant': is_pregnant,
                        'dates': emp_records['Work Date'].tolist() if 'Work Date' in emp_records.columns else [],
                        'reasons': emp_records['Reason Description'].tolist()
                    })

                # Store maternity exclusion metrics for unauthorized absence
                total_unauthorized = len(unauthorized_records)
                non_pregnant_unauthorized_count = len(non_pregnant_unauthorized)
                total_attendance_records = len(active_attendance)

                self.modal_data['unauthorized_metrics'] = {
                    'overall_rate': round((total_unauthorized / total_attendance_records * 100), 2) if total_attendance_records > 0 else 0,
                    'excluding_maternity_rate': round((non_pregnant_unauthorized_count / total_attendance_records * 100), 2) if total_attendance_records > 0 else 0,
                    'total_records': total_attendance_records,
                    'total_unauthorized': total_unauthorized,
                    'non_pregnant_unauthorized': non_pregnant_unauthorized_count
                }

            # Absence reason analysis (only active employees with absence)
            if 'Reason Description' in active_attendance.columns and 'compAdd' in active_attendance.columns:
                # Get only absence records
                absence_with_reasons = active_attendance[active_attendance['compAdd'] == 'Vắng mặt'].copy()

                # Categorize absence reasons
                def categorize_reason(reason_str):
                    """Categorize absence reasons into major categories"""
                    if pd.isna(reason_str) or str(reason_str).strip() == '':
                        return '기타 (Other)'

                    reason_lower = str(reason_str).lower()

                    # Maternity leave
                    if 'sinh' in reason_lower or 'thai' in reason_lower:
                        return '출산휴가 (Maternity)'
                    # Annual/Paid leave
                    elif 'phép năm' in reason_lower or 'vắng có phép' in reason_lower:
                        return '연차/유급휴가 (Annual Leave)'
                    # Unauthorized absence
                    elif 'ar1' in reason_lower or 'vắng không phép' in reason_lower:
                        return '무단결근 (Unauthorized)'
                    # Child illness
                    elif 'con dưới' in reason_lower or 'bệnh' in reason_lower:
                        return '자녀 질병 (Child Illness)'
                    # Business trip
                    elif 'công tác' in reason_lower:
                        return '출장 (Business Trip)'
                    # Medical/Health
                    elif 'khám' in reason_lower or 'ốm' in reason_lower:
                        return '건강/의료 (Medical)'
                    # Card issues
                    elif 'quẹt thẻ' in reason_lower:
                        return '카드 미인식 (Card Issue)'
                    else:
                        return '기타 (Other)'

                absence_with_reasons['reason_category'] = absence_with_reasons['Reason Description'].apply(categorize_reason)

                # Overall reason distribution
                reason_counts = absence_with_reasons['reason_category'].value_counts().to_dict()

                self.modal_data['absence_reason_distribution'] = {
                    category: int(count) for category, count in reason_counts.items()
                }

                # Monthly reason trends (for all available months)
                monthly_reason_data = {}

                for month_str in self.available_months:
                    # Load month data
                    month_data = self.collector.load_month_data(month_str)
                    month_attendance = month_data.get('attendance', pd.DataFrame())
                    month_basic = month_data.get('basic_manpower', pd.DataFrame())

                    if month_attendance.empty or month_basic.empty:
                        continue

                    # Merge with basic data to filter active employees
                    basic_cols = month_basic[['Employee No', 'Stop working Date']].copy()
                    basic_cols.rename(columns={'Employee No': 'ID No'}, inplace=True)

                    month_att_merged = month_attendance.merge(basic_cols, on='ID No', how='left')

                    # Filter active employees
                    stop_dates = pd.to_datetime(month_att_merged['Stop working Date'], errors='coerce')
                    month_active = month_att_merged[(stop_dates.isna()) | (stop_dates > self.report_date)]

                    # Get absence records
                    if 'compAdd' in month_active.columns and 'Reason Description' in month_active.columns:
                        month_absences = month_active[month_active['compAdd'] == 'Vắng mặt'].copy()
                        month_absences['reason_category'] = month_absences['Reason Description'].apply(categorize_reason)

                        month_reason_counts = month_absences['reason_category'].value_counts().to_dict()
                        monthly_reason_data[month_str] = {
                            category: int(count) for category, count in month_reason_counts.items()
                        }

                self.modal_data['monthly_absence_reasons'] = monthly_reason_data

                # Team-based reason distribution (for current month only)
                # Need to map employees to teams
                if not basic_df.empty:
                    # Create ID to team mapping using QIP POSITION 2ND  NAME (team field)
                    id_to_team = {}
                    for _, row in basic_df.iterrows():
                        emp_id = row.get('Employee No')
                        team_name = str(row.get('QIP POSITION 2ND  NAME', '')).strip()
                        if team_name and team_name != '':
                            id_to_team[emp_id] = team_name

                    # Map absence records to teams
                    absence_with_reasons['team'] = absence_with_reasons['ID No'].map(id_to_team)

                    # Calculate team-based reason distribution
                    team_reason_data = {}
                    for team_name in absence_with_reasons['team'].dropna().unique():
                        team_absences = absence_with_reasons[absence_with_reasons['team'] == team_name]
                        team_reason_counts = team_absences['reason_category'].value_counts().to_dict()
                        team_reason_data[team_name] = {
                            category: int(count) for category, count in team_reason_counts.items()
                        }

                    self.modal_data['team_absence_reasons'] = team_reason_data

            # Punctuality data (Come late / Leave early) for Modal 14
            # 지각/조퇴 데이터 (Modal 14용)
            if 'Come late' in active_attendance.columns or 'Leave early' in active_attendance.columns:
                punctuality_details = []
                come_late_total = 0
                leave_early_total = 0

                # Get unique employee data with punctuality issues
                # 지각/조퇴가 있는 직원의 고유 데이터 가져오기
                for emp_id in active_attendance['ID No'].unique():
                    emp_records = active_attendance[active_attendance['ID No'] == emp_id]

                    # Get come late and leave early COUNTS (number of instances)
                    # 지각 및 조퇴 횟수 가져오기 (인스턴스 수 = 건수)
                    come_late_count = 0
                    leave_early_count = 0

                    if 'Come late' in emp_records.columns:
                        # Count records where Come late > 0 (any positive value, including decimals like 0.65)
                        # 지각이 있는 레코드 수 (0.65 같은 소수점 값도 포함)
                        come_late_numeric = pd.to_numeric(emp_records['Come late'], errors='coerce').fillna(0)
                        come_late_count = int((come_late_numeric > 0).sum())

                    if 'Leave early' in emp_records.columns:
                        # Count records where Leave early > 0
                        # 조퇴가 있는 레코드 수
                        leave_early_numeric = pd.to_numeric(emp_records['Leave early'], errors='coerce').fillna(0)
                        leave_early_count = int((leave_early_numeric > 0).sum())

                    # Only add employees with punctuality issues
                    # 지각/조퇴가 있는 직원만 추가
                    if come_late_count > 0 or leave_early_count > 0:
                        emp_name = emp_records['Last name'].iloc[0] if 'Last name' in emp_records.columns else ''
                        team_name = ''
                        if not basic_df.empty:
                            basic_match = basic_df[basic_df['Employee No'] == emp_id]
                            if not basic_match.empty:
                                team_name = str(basic_match['QIP POSITION 2ND  NAME'].iloc[0]) if 'QIP POSITION 2ND  NAME' in basic_match.columns else ''

                        punctuality_details.append({
                            'employee_id': str(emp_id),
                            'employee_name': emp_name,
                            'team': team_name,
                            'come_late': come_late_count,
                            'leave_early': leave_early_count,
                            'total_issues': come_late_count + leave_early_count
                        })

                        come_late_total += come_late_count
                        leave_early_total += leave_early_count

                # Sort by total issues (highest first) / 총 이슈 수 기준 정렬 (높은 순)
                punctuality_details.sort(key=lambda x: x['total_issues'], reverse=True)

                self.modal_data['punctuality_details'] = punctuality_details
                self.modal_data['punctuality_metrics'] = {
                    'come_late_total': come_late_total,
                    'leave_early_total': leave_early_total,
                    'affected_employees': len(punctuality_details),
                    'total_issues': come_late_total + leave_early_total
                }

    def _collect_team_data_legacy(self):
        """
        LEGACY: Collect team data based on position_1st (동적 그룹화)
        Kept for rollback purposes only
        """
        data = self.collector.load_month_data(self.target_month)
        df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        if df.empty:
            return {}

        team_data = {}

        for idx, row in df.iterrows():
            employee_no = str(row.get('Employee No', ''))
            if not employee_no:
                continue

            position_1st = str(row.get('QIP POSITION 1ST  NAME', ''))
            position_2nd = str(row.get('QIP POSITION 2ND  NAME', ''))
            position_3rd = str(row.get('QIP POSITION 3RD  NAME', ''))

            boss_id = ''
            if 'MST direct boss name' in row and pd.notna(row['MST direct boss name']):
                boss_val = row['MST direct boss name']
                try:
                    boss_id = str(int(float(boss_val)))
                except (ValueError, TypeError):
                    boss_id = str(boss_val).replace('.0', '')

            if boss_id in ['nan', '0', '', 'None']:
                boss_id = ''

            if position_1st and position_1st != 'nan':
                if position_1st not in team_data:
                    team_data[position_1st] = {'name': position_1st, 'members': [], 'sub_teams': {}}

                employee_info = {
                    'employee_no': employee_no,
                    'full_name': str(row.get('Full Name', '')),
                    'position_1st': position_1st,
                    'position_2nd': position_2nd,
                    'position_3rd': position_3rd,
                    'boss_id': boss_id,
                    'role_type': str(row.get('ROLE TYPE STD', '')),
                    'entrance_date': row.get('Entrance Date', ''),
                    'stop_date': row.get('Stop working Date', '')
                }

                team_data[position_1st]['members'].append(employee_info)

                if position_2nd and position_2nd != 'nan':
                    if position_2nd not in team_data[position_1st]['sub_teams']:
                        team_data[position_1st]['sub_teams'][position_2nd] = {'name': position_2nd, 'members': []}
                    team_data[position_1st]['sub_teams'][position_2nd]['members'].append(employee_info)

        for team_name, team_info in team_data.items():
            team_info['metrics'] = self._calculate_team_metrics(team_info['members'], attendance_df)
            for sub_team_name, sub_team_info in team_info.get('sub_teams', {}).items():
                sub_team_info['metrics'] = self._calculate_team_metrics(sub_team_info['members'], attendance_df)

        return team_data

    def _collect_team_data(self):
        """
        Collect team data using 11 original teams + sub-teams (Hybrid approach)
        원조 11개 팀 + 동적 하위팀 하이브리드 방식

        Based on: FINAL_TEAM_MAPPING_V2.md
        Mapping rate: 100% (506 employees, 11 teams)

        IMPORTANT: Target month file is cumulative - contains all employees with entrance/stop dates
        중요: 대상 월 파일은 누적 개념 - 모든 직원의 입사일/퇴사일 포함
        """
        # Load target month data (cumulative file with all employee history)
        data = self.collector.load_month_data(self.target_month)
        df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        if df.empty:
            return {}

        # Build reverse mapping: position_3rd -> team_name
        reverse_mapping = {}
        for team_name, pos3_list in TEAM_MAPPING.items():
            for pos3 in pos3_list:
                reverse_mapping[pos3] = team_name

        # Initialize team structure (11 teams)
        team_data = {}
        for team_name in TEAM_MAPPING.keys():
            team_data[team_name] = {
                'name': team_name,
                'members': [],
                'sub_teams': {}
            }

        # Build attendance lookup for team members
        year, month = self.target_month.split('-')
        year_num = int(year)
        month_num = int(month)
        start_of_month = pd.Timestamp(f"{year_num}-{month_num:02d}-01")
        end_of_month = start_of_month + pd.DateOffset(months=1) - pd.DateOffset(days=1)

        employee_attendance = {}
        if not attendance_df.empty and 'ID No' in attendance_df.columns:
            if 'Date' in attendance_df.columns:
                attendance_df_copy = attendance_df.copy()
                attendance_df_copy['Date'] = pd.to_datetime(attendance_df_copy['Date'], errors='coerce')
                month_attendance = attendance_df_copy[
                    (attendance_df_copy['Date'] >= start_of_month) &
                    (attendance_df_copy['Date'] <= end_of_month)
                ]
            else:
                month_attendance = attendance_df

            for emp_id in month_attendance['ID No'].unique():
                emp_records = month_attendance[month_attendance['ID No'] == emp_id]
                working_days = len(emp_records)
                absent_days = 0
                unauthorized_days = 0

                if 'compAdd' in emp_records.columns:
                    absent_days = len(emp_records[emp_records['compAdd'] == 'Vắng mặt'])

                if 'Reason Description' in emp_records.columns:
                    # Match unauthorized patterns: AR1, AR2 / 무단결근 패턴 매칭: AR1, AR2
                    unauthorized_pattern = 'AR1|AR2|Không phép|Vắng không phép'
                    unauthorized_days = len(emp_records[emp_records['Reason Description'].str.contains(unauthorized_pattern, na=False, case=False)])

                employee_attendance[emp_id] = {
                    'working_days': working_days,
                    'absent_days': absent_days,
                    'unauthorized_absent_days': unauthorized_days
                }

        # Process each employee
        for idx, row in df.iterrows():
            employee_no = str(row.get('Employee No', ''))
            if not employee_no or employee_no == 'nan':
                continue

            # Get attendance data
            emp_id_num = row.get('Employee No', 0)
            att_data = employee_attendance.get(emp_id_num, {'working_days': 0, 'absent_days': 0, 'unauthorized_absent_days': 0})

            # Calculate tenure
            entrance_date = pd.to_datetime(row.get('Entrance Date', ''), errors='coerce', dayfirst=False)
            tenure_days = 0
            if pd.notna(entrance_date):
                tenure_days = (end_of_month - entrance_date).days

            pos1 = str(row.get('QIP POSITION 1ST  NAME', ''))
            pos2 = str(row.get('QIP POSITION 2ND  NAME', ''))
            pos3 = str(row.get('QIP POSITION 3RD  NAME', ''))
            pos4 = str(row.get('FINAL QIP POSITION NAME CODE', ''))

            # Map to team using position_3rd
            team_name = reverse_mapping.get(pos3, None)

            if not team_name:
                # Unmapped employee - should not happen with 100% mapping
                print(f"⚠️  Warning: Unmapped employee {employee_no} - {row.get('Full Name')} (pos3: {pos3})")
                continue

            # Extract boss_id
            boss_id = ''
            if 'MST direct boss name' in row and pd.notna(row['MST direct boss name']):
                boss_val = row['MST direct boss name']
                try:
                    boss_id = str(int(float(boss_val)))
                except (ValueError, TypeError):
                    boss_id = str(boss_val).replace('.0', '')

            if boss_id in ['nan', '0', '', 'None']:
                boss_id = ''

            # Get pregnant status
            pregnant_status = row.get('pregnant vacation-yes or no', '')
            is_pregnant = str(pregnant_status).lower() == 'yes' if pregnant_status else False

            # Calculate is_active status
            # 재직 여부 계산: 퇴사일이 없거나 월말 이후인 경우 재직 중
            stop_date = pd.to_datetime(row.get('Stop working Date', ''), errors='coerce', dayfirst=False)
            is_active = pd.isna(stop_date) or stop_date > end_of_month

            # Calculate perfect_attendance status
            # 개근 여부 계산: 재직 중이고, 출근일이 있고, 결근일이 0인 경우
            perfect_attendance = is_active and att_data['working_days'] > 0 and att_data['absent_days'] == 0

            # Build employee info with attendance data
            employee_info = {
                'employee_no': employee_no,
                'full_name': str(row.get('Full Name', '')),
                'position_1st': pos1,
                'position_2nd': pos2,
                'position_3rd': pos3,
                'position_4th': pos4,
                'boss_id': boss_id,
                'role_type': str(row.get('ROLE TYPE STD', '')),
                'entrance_date': str(row.get('Entrance Date', '')),
                'stop_date': str(row.get('Stop working Date', '')),
                'working_days': att_data['working_days'],
                'absent_days': att_data['absent_days'],
                'unauthorized_absent_days': att_data['unauthorized_absent_days'],
                'pregnant_status': 'yes' if is_pregnant else '',  # Fixed field name to match metrics calculation
                'is_pregnant': is_pregnant,  # Boolean field for JavaScript consistency
                'is_active': is_active,  # Boolean field for active status - 재직 여부
                'perfect_attendance': perfect_attendance,  # Boolean field for perfect attendance - 개근 여부
                'years_of_service': f"{tenure_days} days" if tenure_days > 0 else '0 days'
            }

            # Add to team
            team_data[team_name]['members'].append(employee_info)

            # Add to sub-team (position_2nd) - preserve hierarchy
            if pos2 and pos2 != 'nan':
                if pos2 not in team_data[team_name]['sub_teams']:
                    team_data[team_name]['sub_teams'][pos2] = {
                        'name': pos2,
                        'members': []
                    }
                team_data[team_name]['sub_teams'][pos2]['members'].append(employee_info)

        # Calculate metrics for each team
        for team_name, team_info in team_data.items():
            team_info['metrics'] = self._calculate_team_metrics(
                team_info['members'],
                attendance_df
            )

            # Derive position_1st from most common value among members
            # 멤버들 중 가장 흔한 position_1st 값으로 팀의 position_1st 설정
            pos1_counts = {}
            for member in team_info['members']:
                pos1 = member.get('position_1st', 'Unknown')
                pos1_counts[pos1] = pos1_counts.get(pos1, 0) + 1

            if pos1_counts:
                team_info['position_1st'] = max(pos1_counts, key=pos1_counts.get)
            else:
                team_info['position_1st'] = 'Unknown'

            # Calculate metrics for sub-teams
            for sub_team_name, sub_team_info in team_info.get('sub_teams', {}).items():
                sub_team_info['metrics'] = self._calculate_team_metrics(
                    sub_team_info['members'],
                    attendance_df
                )

        # Remove empty teams
        team_data = {k: v for k, v in team_data.items() if v['members']}

        # Validation
        total_mapped = sum(len(team['members']) for team in team_data.values())
        print(f"✅ Team mapping complete: {total_mapped} employees across {len(team_data)} teams")

        if total_mapped != 506:
            print(f"⚠️  Warning: Expected 506 employees, got {total_mapped}")
        if len(team_data) != 11:
            print(f"⚠️  Warning: Expected 11 teams, got {len(team_data)}")
            print(f"   Teams: {list(team_data.keys())}")

        return team_data

    def _collect_previous_month_team_data(self):
        """
        Collect previous month team data for month-over-month comparison
        전월 대비 비교를 위한 이전 달 팀 데이터 수집
        """
        # Find previous month
        if len(self.available_months) < 2:
            print("⚠️  No previous month data available for comparison")
            return {}

        # Get previous month (second to last in available_months)
        current_month_idx = self.available_months.index(self.target_month)
        if current_month_idx == 0:
            print("⚠️  Current month is the first available month, no previous data")
            return {}

        previous_month = self.available_months[current_month_idx - 1]
        print(f"📅 Loading previous month data: {previous_month}")

        # Load previous month data
        data = self.collector.load_month_data(previous_month)
        df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        if df.empty:
            print(f"⚠️  No data for previous month {previous_month}")
            return {}

        # Build reverse mapping
        reverse_mapping = {}
        for team_name, pos3_list in TEAM_MAPPING.items():
            for pos3 in pos3_list:
                reverse_mapping[pos3] = team_name

        # Initialize team structure
        team_data = {}
        for team_name in TEAM_MAPPING.keys():
            team_data[team_name] = {
                'name': team_name,
                'members': [],
                'metrics': {},
                'sub_teams': {}
            }

        # Get report date for previous month (end of month)
        year_num, month_num = map(int, previous_month.split('-'))
        import calendar
        last_day = calendar.monthrange(year_num, month_num)[1]
        prev_report_date = pd.Timestamp(f"{year_num}-{month_num:02d}-{last_day}")

        # Map employees to teams
        for idx, row in df.iterrows():
            pos3 = row.get('QIP POSITION 3RD  NAME', '')
            team_name = reverse_mapping.get(pos3)

            if not team_name:
                position_3rd = row.get('QIP POSITION 3RD  NAME', '')
                position_2nd = row.get('QIP POSITION 2ND  NAME', '')
                position_1st = row.get('QIP POSITION 1ST  NAME', '')
                position_for_team = position_3rd or position_2nd or position_1st or ''
                team_name = self._extract_team_from_position(position_for_team)

            if not team_name or team_name not in team_data:
                continue

            # Check if employee is active in previous month
            entrance_date_str = row.get('Entrance Date', '')
            stop_date_str = row.get('Stop working Date', '')

            try:
                entrance_date = pd.to_datetime(entrance_date_str, errors='coerce', dayfirst=False)
                if pd.isna(entrance_date) or entrance_date > prev_report_date:
                    continue

                is_active = True
                if stop_date_str and str(stop_date_str) != 'nan':
                    stop_date = pd.to_datetime(stop_date_str, errors='coerce', dayfirst=False)
                    if pd.notna(stop_date) and stop_date <= prev_report_date:
                        is_active = False

                # Calculate tenure
                tenure_days = (prev_report_date - entrance_date).days if pd.notna(entrance_date) else 0

                pos1 = str(row.get('QIP POSITION 1ST  NAME', ''))
                employee_info = {
                    'employee_no': str(row.get('Employee No', '')),
                    'name': str(row.get('Name', '')),
                    'team': team_name,
                    'position_1st': pos1,
                    'is_active': is_active,
                    'entrance_date': str(entrance_date_str),
                    'stop_date': str(stop_date_str),
                    'tenure_days': tenure_days,
                    'pregnant_status': 'yes' if str(row.get('pregnant vacation-yes or no', '')).lower() == 'yes' else ''
                }

                team_data[team_name]['members'].append(employee_info)

            except Exception as e:
                continue

        # Calculate metrics for each team
        for team_name, team_info in team_data.items():
            if team_info['members']:
                team_info['metrics'] = self._calculate_team_metrics(
                    team_info['members'],
                    attendance_df
                )

                # Derive position_1st from most common value among members
                # 멤버들 중 가장 흔한 position_1st 값으로 팀의 position_1st 설정
                pos1_counts = {}
                for member in team_info['members']:
                    pos1 = member.get('position_1st', 'Unknown')
                    pos1_counts[pos1] = pos1_counts.get(pos1, 0) + 1

                if pos1_counts:
                    team_info['position_1st'] = max(pos1_counts, key=pos1_counts.get)
                else:
                    team_info['position_1st'] = 'Unknown'

        # Remove empty teams
        team_data = {k: v for k, v in team_data.items() if v['members']}

        return team_data

    def _calculate_monthly_team_counts(self):
        """
        Calculate team counts for all available months using employee_counter utility
        모든 월의 팀별 인원 계산 (employee_counter 유틸리티 사용)
        """
        # Load target month data (contains all employee history)
        data = self.collector.load_month_data(self.target_month)
        df = data.get('basic_manpower', pd.DataFrame())

        if df.empty:
            return

        # Use utility function for standardized counting
        self.monthly_team_counts = count_employees_by_teams_monthly(
            df=df,
            team_mapping=TEAM_MAPPING,
            months=self.available_months,
            report_date=self.report_date
        )

        # Log for verification
        for month_str, team_counts in self.monthly_team_counts.items():
            total = sum(team_counts.values())
            print(f"  {month_str}: {total} employees across teams")

    def _calculate_team_metrics(self, team_members: List[Dict], attendance_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate team performance metrics
        팀 성과 메트릭 계산

        Args:
            team_members: List of employee dictionaries
            attendance_df: Attendance DataFrame

        Returns:
            Dict with calculated metrics
        """
        if not team_members:
            return {
                'total_members': 0,
                'active_members': 0,
                'avg_attendance_rate': 0.0,
                'perfect_attendance_count': 0,
                'avg_tenure_days': 0.0,
                'high_risk_count': 0,
                'type_distribution': {}
            }

        year, month = self.target_month.split('-')
        year_num = int(year)
        month_num = int(month)
        end_of_month = pd.Timestamp(f"{year_num}-{month_num:02d}-01") + pd.DateOffset(months=1) - pd.DateOffset(days=1)

        # Calculate metrics
        total_members = len(team_members)
        active_members = 0
        tenure_days_sum = 0
        type_distribution = {}

        # Employee IDs for attendance lookup
        employee_ids = [m['employee_no'] for m in team_members]

        for member in team_members:
            # Active status
            stop_date_str = member.get('stop_date', '')
            is_active = True
            if stop_date_str and stop_date_str != 'nan':
                try:
                    stop_date = pd.to_datetime(stop_date_str, errors='coerce', dayfirst=False)
                    if pd.notna(stop_date) and stop_date <= end_of_month:
                        is_active = False
                except:
                    pass

            if is_active:
                active_members += 1

            # Tenure calculation
            entrance_date_str = member.get('entrance_date', '')
            if entrance_date_str and entrance_date_str != 'nan':
                try:
                    entrance_date = pd.to_datetime(entrance_date_str, errors='coerce')
                    if pd.notna(entrance_date):
                        tenure_days = (end_of_month - entrance_date).days
                        if tenure_days > 0:
                            tenure_days_sum += tenure_days
                except:
                    pass

            # TYPE distribution
            role_type = member.get('role_type', 'Unknown')
            if role_type and role_type != 'nan':
                type_distribution[role_type] = type_distribution.get(role_type, 0) + 1

        # Attendance rate calculation
        avg_attendance_rate = 0.0
        perfect_attendance_count = 0
        high_risk_count = 0

        if not attendance_df.empty and 'ID No' in attendance_df.columns:
            # Convert employee_ids to int to match attendance 'ID No' column type
            # employee_ids are strings from 'Employee No', but attendance 'ID No' is int
            employee_ids_int = []
            for emp_id in employee_ids:
                try:
                    employee_ids_int.append(int(emp_id))
                except (ValueError, TypeError):
                    pass  # Skip invalid IDs

            team_attendance = attendance_df[attendance_df['ID No'].isin(employee_ids_int)]

            if len(team_attendance) > 0:
                # Overall team attendance rate
                if 'compAdd' in team_attendance.columns:
                    total_records = len(team_attendance)
                    absences = len(team_attendance[team_attendance['compAdd'] == 'Vắng mặt'])
                    avg_attendance_rate = ((total_records - absences) / total_records * 100) if total_records > 0 else 0.0

                # Perfect attendance count
                # 개근자 수: 출근 기록이 있고, 결근(Vắng mặt) 기록이 없는 재직 직원
                absent_employees = set()
                employees_with_records = set()
                if 'compAdd' in team_attendance.columns:
                    absent_employees = set(team_attendance[team_attendance['compAdd'] == 'Vắng mặt']['ID No'].unique())
                    employees_with_records = set(team_attendance['ID No'].unique())

                # Only count employees who have attendance records and no absences
                # 출근 기록이 있고 결근이 없는 직원만 개근으로 계산
                perfect_attendance_count = len(employees_with_records - absent_employees)

                # High risk employees (attendance < 60%)
                for emp_id in employee_ids_int:
                    emp_records = team_attendance[team_attendance['ID No'] == emp_id]
                    if len(emp_records) > 0:
                        emp_absences = len(emp_records[emp_records['compAdd'] == 'Vắng mặt'])
                        emp_attendance_rate = ((len(emp_records) - emp_absences) / len(emp_records) * 100)
                        if emp_attendance_rate < 60:
                            high_risk_count += 1

        # Calculate absence rate from attendance rate
        absence_rate = round(100 - avg_attendance_rate, 1) if avg_attendance_rate > 0 else 0.0

        # Calculate additional KPIs for team summary cards
        # 팀 요약 카드용 추가 KPI 계산

        # 1. Recent day absence rate (최근일 결근율)
        recent_day_absence_rate = 0.0
        if not attendance_df.empty and 'Date' in attendance_df.columns:
            # Get most recent date
            attendance_df_copy = attendance_df.copy()
            attendance_df_copy['Date'] = pd.to_datetime(attendance_df_copy['Date'], errors='coerce')
            if not attendance_df_copy['Date'].isna().all():
                most_recent_date = attendance_df_copy['Date'].max()
                recent_day_data = attendance_df_copy[attendance_df_copy['Date'] == most_recent_date]
                team_recent = recent_day_data[recent_day_data['ID No'].isin(employee_ids_int)]
                if len(team_recent) > 0:
                    recent_absences = len(team_recent[team_recent['compAdd'] == 'Vắng mặt'])
                    recent_day_absence_rate = round((recent_absences / len(team_recent) * 100), 1)

        # 2. Monthly resignation rate (월 퇴사율)
        resignations_this_month = 0
        start_of_month = pd.Timestamp(f"{year_num}-{month_num:02d}-01")
        for member in team_members:
            stop_date_str = member.get('stop_date', '')
            if stop_date_str and stop_date_str != 'nan':
                try:
                    stop_date = pd.to_datetime(stop_date_str, errors='coerce', dayfirst=False)
                    if pd.notna(stop_date) and start_of_month <= stop_date <= end_of_month:
                        resignations_this_month += 1
                except:
                    pass

        # Calculate average headcount for resignation rate
        employees_at_start = sum(1 for m in team_members
                                 if pd.to_datetime(m.get('entrance_date', ''), errors='coerce') <= start_of_month)
        employees_at_end = active_members
        avg_headcount = (employees_at_start + employees_at_end) / 2
        resignation_rate = round((resignations_this_month / avg_headcount * 100), 1) if avg_headcount > 0 else 0.0

        # 3. Pregnant employees count (임산부 수)
        pregnant_count = sum(1 for m in team_members
                            if str(m.get('pregnant_status', '')).lower() == 'yes')

        # 4. Under 90 days employees (90일 미만 직원 수)
        under_90_days_count = 0
        for member in team_members:
            # Only count active employees
            stop_date_str = member.get('stop_date', '')
            is_active = True
            if stop_date_str and stop_date_str != 'nan':
                try:
                    stop_date = pd.to_datetime(stop_date_str, errors='coerce', dayfirst=False)
                    if pd.notna(stop_date) and stop_date <= end_of_month:
                        is_active = False
                except:
                    pass

            if is_active:
                entrance_date_str = member.get('entrance_date', '')
                if entrance_date_str and entrance_date_str != 'nan':
                    try:
                        entrance_date = pd.to_datetime(entrance_date_str, errors='coerce')
                        if pd.notna(entrance_date):
                            tenure = (end_of_month - entrance_date).days
                            if 0 < tenure < 90:
                                under_90_days_count += 1
                    except:
                        pass

        return {
            'total_members': total_members,
            'active_members': active_members,
            'avg_attendance_rate': round(avg_attendance_rate, 1),
            'absence_rate': absence_rate,
            'recent_day_absence_rate': recent_day_absence_rate,
            'resignation_rate': resignation_rate,
            'resignations_this_month': resignations_this_month,
            'pregnant_count': pregnant_count,
            'under_90_days_count': under_90_days_count,
            'perfect_attendance_count': perfect_attendance_count,
            'avg_tenure_days': round(tenure_days_sum / active_members, 1) if active_members > 0 else 0.0,
            'avg_tenure_years': round((tenure_days_sum / active_members / 365), 2) if active_members > 0 else 0.0,
            'high_risk_count': high_risk_count,
            'type_distribution': type_distribution
        }

    def _build_hierarchy_data(self):
        """
        Build hierarchical organization structure based on boss_id
        boss_id 기반 계층적 조직 구조 생성

        Returns:
            List of root nodes with recursive children
        """
        data = self.collector.load_month_data(self.target_month)
        df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        if df.empty:
            return []

        # Filter to only include active employees (exclude resigned)
        # 퇴사자 제외 - 재직자만 포함
        stop_dates = pd.to_datetime(df['Stop working Date'], errors='coerce')
        active_df = df[(stop_dates.isna()) | (stop_dates > self.report_date)]

        # Build employee map
        employee_map = {}

        for idx, row in active_df.iterrows():
            employee_no = str(row.get('Employee No', ''))
            if not employee_no or employee_no == 'nan':
                continue

            # Boss ID - MST direct boss name is actually Employee No stored as float
            boss_id = ''
            if 'MST direct boss name' in row and pd.notna(row['MST direct boss name']):
                boss_val = row['MST direct boss name']
                # Convert float to int to string (e.g., 620070050.0 -> "620070050")
                try:
                    boss_id = str(int(float(boss_val)))
                except (ValueError, TypeError):
                    boss_id = str(boss_val).replace('.0', '')

            if boss_id in ['nan', '0', '', 'None']:
                boss_id = ''

            employee_map[employee_no] = {
                'id': employee_no,
                'name': str(row.get('Full Name', '')),
                'position': str(row.get('QIP POSITION 1ST  NAME', '')),
                'team': str(row.get('QIP POSITION 2ND  NAME', '')),
                'department': str(row.get('QIP POSITION 3RD  NAME', '')),
                'boss_id': boss_id,
                'role_type': str(row.get('ROLE TYPE STD', '')),
                'entrance_date': row.get('Entrance Date', ''),
                'stop_date': row.get('Stop working Date', ''),
                'children': []
            }

        # Build parent-child relationships
        root_nodes = []

        for emp_id, emp_data in employee_map.items():
            boss_id = emp_data['boss_id']

            if boss_id and boss_id in employee_map:
                # Add as child to boss
                employee_map[boss_id]['children'].append(emp_data)
            else:
                # No boss or boss not found - this is a root node
                root_nodes.append(emp_data)

        # Calculate team metrics for managers (those with children)
        for emp_id, emp_data in employee_map.items():
            if emp_data['children']:
                # This is a manager - calculate team metrics
                subordinate_ids = [child['id'] for child in emp_data['children']]

                # Get subordinate info for metric calculation
                subordinates_info = []
                for child_id in subordinate_ids:
                    if child_id in employee_map:
                        child = employee_map[child_id]
                        subordinates_info.append({
                            'employee_no': str(child['id']),  # Convert to string for consistency
                            'full_name': child['name'],
                            'position_1st': child['position'],
                            'role_type': child['role_type'],
                            'entrance_date': child['entrance_date'],
                            'stop_date': child['stop_date']
                        })

                emp_data['team_metrics'] = self._calculate_team_metrics(
                    subordinates_info,
                    attendance_df
                )

        return root_nodes

    def _convert_to_json_serializable(self, obj):
        """Convert numpy types to Python native types for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            # Check for NaN and convert to None (which becomes null in JSON)
            if pd.isna(obj) or np.isnan(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):  # Handle pandas NaT, NA, and other pandas missing values
            return None
        else:
            return obj

    def _safe_json_dumps(self, obj, **kwargs):
        """Safe JSON dumps with automatic NaN handling"""
        def default_handler(o):
            # Handle pandas/numpy types
            if pd.isna(o):
                return None
            elif isinstance(o, (np.integer, np.int64)):
                return int(o)
            elif isinstance(o, (np.floating, np.float64)):
                if np.isnan(o):
                    return None
                return float(o)
            elif isinstance(o, np.ndarray):
                return o.tolist()
            elif isinstance(o, (pd.Timestamp, pd.Timedelta)):
                return str(o)
            else:
                raise TypeError(f"Object of type {type(o)} is not JSON serializable")

        # First convert with our method, then use json.dumps with default handler
        converted = self._convert_to_json_serializable(obj)
        return json.dumps(converted, default=default_handler, **kwargs)

    def _collect_attendance_data(self) -> None:
        """
        Collect individual attendance data for all employees
        모든 직원의 개인 출결 데이터 수집
        """
        # Get month name for file lookup
        # 파일 조회용 월 이름 추출
        month_map = {
            '01': 'january', '02': 'february', '03': 'march', '04': 'april',
            '05': 'may', '06': 'june', '07': 'july', '08': 'august',
            '09': 'september', '10': 'october', '11': 'november', '12': 'december'
        }
        month_num = self.target_month.split('-')[1]
        month_name = month_map.get(month_num, 'december')

        # Load attendance file
        # 출결 파일 로드
        attendance_file = f"input_files/attendance/converted/attendance data {month_name}_converted.csv"
        try:
            df = pd.read_csv(attendance_file)
        except FileNotFoundError:
            print(f"⚠️  Attendance file not found: {attendance_file}")
            return

        # Process each row into attendance record
        # 각 행을 출결 기록으로 처리
        records = []
        for _, row in df.iterrows():
            try:
                # Parse date to get day of week
                # 요일 추출을 위한 날짜 파싱
                work_date = str(row.get('Work Date', ''))
                day_of_week = ''
                if work_date:
                    try:
                        date_obj = pd.to_datetime(work_date.replace('.', '-'))
                        day_names_ko = ['월', '화', '수', '목', '금', '토', '일']
                        day_names_en = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                        day_names_vi = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
                        day_of_week = day_names_ko[date_obj.dayofweek]
                        day_of_week_en = day_names_en[date_obj.dayofweek]
                        day_of_week_vi = day_names_vi[date_obj.dayofweek]
                    except Exception:
                        day_of_week = ''
                        day_of_week_en = ''
                        day_of_week_vi = ''

                # Determine attendance status
                # 출결 상태 결정
                status = str(row.get('compAdd', '')).strip()
                reason = str(row.get('Reason Description', '')).strip()
                if pd.isna(row.get('Reason Description')):
                    reason = ''

                # Map status to standardized values
                # 상태를 표준화된 값으로 매핑
                if 'Đi làm' in status:
                    status_ko = '출근'
                    status_en = 'Present'
                    status_vi = 'Đi làm'
                    status_type = 'present'
                elif 'Vắng mặt' in status:
                    status_ko = '결근'
                    status_en = 'Absent'
                    status_vi = 'Vắng mặt'
                    status_type = 'absent'
                else:
                    status_ko = status
                    status_en = status
                    status_vi = status
                    status_type = 'other'

                # Map common Vietnamese reasons to Korean/English/Vietnamese
                # 일반적인 베트남어 사유를 한국어/영어/베트남어로 매핑
                reason_map = {
                    # Authorized absences / 승인 결근
                    'Vắng có phép': ('유급휴가', 'Authorized Leave', 'Vắng có phép'),
                    'Phép năm': ('연차', 'Annual Leave', 'Phép năm'),
                    'Nghỉ ốm': ('병가', 'Sick Leave', 'Nghỉ ốm'),
                    'Thai sản': ('출산휴가', 'Maternity Leave', 'Thai sản'),
                    'Nghỉ việc riêng': ('개인사유', 'Personal Leave', 'Nghỉ việc riêng'),
                    'Nghỉ bù': ('대체휴무', 'Compensatory Leave', 'Nghỉ bù'),
                    'Đi công tác': ('출장', 'Business Trip', 'Đi công tác'),
                    'Nghỉ lễ': ('공휴일', 'Holiday', 'Nghỉ lễ'),
                    'Đào tạo': ('교육', 'Training', 'Đào tạo'),
                    'Nghỉ phép': ('휴가', 'Leave', 'Nghỉ phép'),
                    'Nghỉ cưới': ('경조휴가', 'Wedding Leave', 'Nghỉ cưới'),
                    'Nghỉ tang': ('경조휴가', 'Bereavement Leave', 'Nghỉ tang'),
                    # Unauthorized absences / 무단 결근
                    'Nghỉ không phép': ('무단결근', 'Unauthorized Absence', 'Nghỉ không phép'),
                    'Không quẹt thẻ': ('미체크', 'No Card Swipe', 'Không quẹt thẻ'),
                    'Vắng không phép': ('무단결근', 'Unauthorized Absence', 'Vắng không phép'),
                    # Other / 기타
                    'Đi làm muộn': ('지각', 'Late', 'Đi làm muộn'),
                    'Về sớm': ('조퇴', 'Left Early', 'Về sớm'),
                    'Nghỉ nửa ngày': ('반차', 'Half Day', 'Nghỉ nửa ngày'),
                }
                reason_ko = reason
                reason_en = reason
                reason_vi = reason
                if reason in reason_map:
                    reason_ko, reason_en, reason_vi = reason_map[reason]

                # Get come late and leave early values / 지각 및 조퇴 값 가져오기
                come_late_val = row.get('Come late', 0)
                leave_early_val = row.get('Leave early', 0)
                # Convert to numeric, default 0 / 숫자로 변환, 기본값 0
                try:
                    come_late = int(come_late_val) if pd.notna(come_late_val) and str(come_late_val).strip() else 0
                except (ValueError, TypeError):
                    come_late = 0
                try:
                    leave_early = int(leave_early_val) if pd.notna(leave_early_val) and str(leave_early_val).strip() else 0
                except (ValueError, TypeError):
                    leave_early = 0

                record = {
                    'employee_no': str(row.get('ID No', '')),
                    'employee_name': str(row.get('Last name', '')),
                    'work_date': work_date,
                    'day_of_week': day_of_week,
                    'day_of_week_en': day_of_week_en if 'day_of_week_en' in dir() else '',
                    'day_of_week_vi': day_of_week_vi if 'day_of_week_vi' in dir() else '',
                    'status': status_type,
                    'status_ko': status_ko,
                    'status_en': status_en,
                    'status_vi': status_vi,
                    'reason': reason,
                    'reason_ko': reason_ko,
                    'reason_en': reason_en,
                    'reason_vi': reason_vi,
                    'department': str(row.get('Department', '')),
                    'work_time': str(row.get('WTime', '')),
                    'come_late': come_late,
                    'leave_early': leave_early
                }
                records.append(record)
            except Exception as e:
                continue

        self.attendance_data = records

    def _generate_html(self) -> str:
        """Generate complete HTML with all components"""
        target_metrics = self.monthly_metrics.get(self.target_month, {})

        # Calculate average team absence rate for KPI card #13
        # KPI 카드 #13을 위한 평균 팀 결근율 계산
        team_absence_data = target_metrics.get('team_absence_breakdown', {})
        if team_absence_data:
            total_rates = [data.get('total_absence_rate', 0) for data in team_absence_data.values()]
            avg_rate = round(sum(total_rates) / len(total_rates), 1) if total_rates else 0.0
            target_metrics['team_absence_avg'] = avg_rate
        else:
            target_metrics['team_absence_avg'] = 0.0

        # Calculate punctuality issues for KPI card #14 / KPI 카드 #14를 위한 지각/조퇴 인원 계산
        # Count unique employees with come_late > 0 or leave_early > 0
        # 지각 또는 조퇴가 있는 고유 직원 수 계산
        punctuality_employees = set()
        come_late_total = 0
        leave_early_total = 0
        if hasattr(self, 'attendance_data') and self.attendance_data:
            for record in self.attendance_data:
                emp_no = record.get('employee_no', '')
                come_late = record.get('come_late', 0)
                leave_early = record.get('leave_early', 0)
                if come_late > 0 or leave_early > 0:
                    punctuality_employees.add(emp_no)
                come_late_total += come_late
                leave_early_total += leave_early
        target_metrics['punctuality_issues'] = len(punctuality_employees)
        target_metrics['come_late_count'] = come_late_total
        target_metrics['leave_early_count'] = leave_early_total

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR Dashboard - {self.target_month}</title>

    <!-- Content Security Policy / 콘텐츠 보안 정책 -->
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'self';
                   script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://d3js.org https://cdn.plot.ly;
                   style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
                   img-src 'self' data: blob:;
                   font-src 'self' https://cdn.jsdelivr.net;">

    <!-- Bootstrap 5.3 CSS / Bootstrap 5.3 스타일시트 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Chart.js CDN / Chart.js CDN 로드 -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

    <!-- Chart Utilities (embedded inline for portability) -->
    <script>
{self._embed_chart_utils()}
    </script>

    <!-- D3.js for Treemap -->
    <script src="https://d3js.org/d3.v7.min.js"
            crossorigin="anonymous"></script>

    <!-- Plotly.js for Sunburst Chart -->
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"
            crossorigin="anonymous"></script>

    {self._generate_css()}
</head>
<body>
    <!-- Skip to main content link for accessibility / 접근성을 위한 본문 바로가기 링크 -->
    <a href="#main-content" class="skip-to-content">
        <span data-ko="본문으로 바로가기" data-en="Skip to main content" data-vi="Bỏ qua đến nội dung chính">Skip to main content</span>
    </a>

    {self._generate_header()}

    <main id="main-content" class="container-xl px-4 py-4" role="main">
        <!-- Tab Navigation / 탭 네비게이션 -->
        <ul class="nav nav-tabs mb-4" id="dashboardTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active lang-tab" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview"
                        type="button" role="tab" aria-controls="overview" aria-selected="true"
                        data-ko="📊 Overview" data-en="📊 Overview" data-vi="📊 Tổng quan">
                    📊 Overview
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link lang-tab" id="trends-tab" data-bs-toggle="tab" data-bs-target="#trends"
                        type="button" role="tab" aria-controls="trends" aria-selected="false"
                        data-ko="📈 Trends" data-en="📈 Trends" data-vi="📈 Xu hướng">
                    📈 Trends
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link lang-tab" id="details-tab" data-bs-toggle="tab" data-bs-target="#details"
                        type="button" role="tab" aria-controls="details" aria-selected="false"
                        data-ko="👥 Employee Details" data-en="👥 Employee Details" data-vi="👥 Chi tiết nhân viên">
                    👥 Employee Details
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link lang-tab" id="teamanalysis-tab" data-bs-toggle="tab" data-bs-target="#teamanalysis"
                        type="button" role="tab" aria-controls="teamanalysis" aria-selected="false"
                        data-ko="🏢 Team Analysis" data-en="🏢 Team Analysis" data-vi="🏢 Phân tích nhóm">
                    🏢 Team Analysis
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link lang-tab" id="attendance-tab" data-bs-toggle="tab" data-bs-target="#attendance"
                        type="button" role="tab" aria-controls="attendance" aria-selected="false"
                        data-ko="📅 개인 출결 조회" data-en="📅 Individual Attendance" data-vi="📅 Điểm danh cá nhân">
                    📅 개인 출결 조회
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link lang-tab" id="help-tab" data-bs-toggle="tab" data-bs-target="#help"
                        type="button" role="tab" aria-controls="help" aria-selected="false"
                        data-ko="❓ 도움말" data-en="❓ Help" data-vi="❓ Trợ giúp">
                    ❓ Help
                </button>
            </li>
        </ul>

        <!-- Tab Content -->
        <div class="tab-content" id="dashboardTabContent">
            <!-- Overview Tab -->
            <div class="tab-pane fade show active" id="overview" role="tabpanel" aria-labelledby="overview-tab">
                {self._generate_executive_summary(target_metrics)}
                {self._generate_summary_cards(target_metrics)}
                {self._generate_hierarchy_visualization_section()}
            </div>

            <!-- Trends Tab -->
            <div class="tab-pane fade" id="trends" role="tabpanel" aria-labelledby="trends-tab">
                {self._generate_charts_section()}
            </div>

            <!-- Details Tab -->
            <div class="tab-pane fade" id="details" role="tabpanel" aria-labelledby="details-tab">
                {self._generate_details_tab()}
            </div>

            <!-- Team Analysis Tab -->
            <div class="tab-pane fade" id="teamanalysis" role="tabpanel" aria-labelledby="teamanalysis-tab">
                {self._generate_teamanalysis_tab()}
            </div>

            <!-- Individual Attendance Tab / 개인 출결 조회 탭 -->
            <div class="tab-pane fade" id="attendance" role="tabpanel" aria-labelledby="attendance-tab">
                {self._generate_individual_attendance_tab()}
            </div>

            <!-- Help Tab -->
            <div class="tab-pane fade" id="help" role="tabpanel" aria-labelledby="help-tab">
                {self._generate_help_tab()}
            </div>
        </div>
    </main>

    {self._generate_modals()}

    <!-- Bootstrap 5.3 JS Bundle / Bootstrap 5.3 자바스크립트 -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        // Embedded data
        const monthlyMetrics =
{self._safe_json_dumps(self.monthly_metrics, ensure_ascii=False, indent=2)}
;
        const monthLabels =
{self._safe_json_dumps(self.month_labels, ensure_ascii=False)}
;
        const availableMonths =
{self._safe_json_dumps(self.available_months)}
;
        const targetMonth = '{self.target_month}';
        const employeeDetails =
{self._safe_json_dumps(self.employee_details, ensure_ascii=False, indent=2)}
;
        const modalData =
{self._safe_json_dumps(self.modal_data, ensure_ascii=False, indent=2)}
;
        const teamData =
{self._safe_json_dumps(self.team_data, ensure_ascii=False, indent=2)}
;
        const previousMonthTeamData =
{self._safe_json_dumps(self.previous_month_team_data, ensure_ascii=False, indent=2)}
;
        const monthlyTeamCounts =
{self._safe_json_dumps(self.monthly_team_counts, ensure_ascii=False, indent=2)}
;
        const hierarchyData =
{self._safe_json_dumps(self.hierarchy_data, ensure_ascii=False, indent=2)}
;
        const attendanceData =
{self._safe_json_dumps(self.attendance_data, ensure_ascii=False, indent=2)}
;

        {self._generate_javascript()}
    </script>
</body>
</html>"""
        return html

    def _embed_chart_utils(self) -> str:
        """
        Embed chart_utils.js content inline
        chart_utils.js 내용을 인라인으로 포함

        This ensures the dashboard works as a standalone HTML file
        대시보드가 독립 실행형 HTML 파일로 작동하도록 함
        """
        chart_utils_path = self.hr_root / 'src' / 'visualization' / 'chart_utils.js'
        try:
            with open(chart_utils_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback: try output_files directory
            fallback_path = self.hr_root / 'output_files' / 'chart_utils.js'
            try:
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return "// chart_utils.js not found - charts may not work properly"

    def _generate_css(self) -> str:
        """Generate CSS styles"""
        return """
<style>
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --card-shadow: 0 4px 6px rgba(0,0,0,0.07);
        --card-hover-shadow: 0 8px 16px rgba(0,0,0,0.12);
        --touch-target-min: 44px;
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background: #f8f9fa;
    }

    /* WCAG AA Color Contrast Fix - Improved button text colors */
    /* WCAG AA 색상 대비 수정 - 개선된 버튼 텍스트 색상 */
    .btn-outline-secondary {
        color: #495057;  /* 7.1:1 contrast ratio (was #6c757d at 3.5:1) */
        border-color: #6c757d;
    }
    .btn-outline-secondary:hover {
        color: #fff;
        background-color: #6c757d;
        border-color: #6c757d;
    }
    .btn-outline-info {
        color: #0c7489;  /* 4.6:1 contrast ratio (was #17a2b8 at 3.1:1) */
        border-color: #17a2b8;
    }
    .btn-outline-info:hover {
        color: #fff;
        background-color: #17a2b8;
        border-color: #17a2b8;
    }
    /* Improve filter button badge visibility on active state */
    /* 활성 상태에서 필터 버튼 배지 가시성 개선 */
    .btn.active .badge {
        background: rgba(255,255,255,0.9) !important;
        color: #333 !important;
        font-weight: 600;
    }

    /* ============================================ */
    /* Enhanced Stat Cards / 개선된 통계 카드 */
    /* ============================================ */
    .stat-card {
        border-radius: 12px;
        padding: 1rem;
        color: white;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: all 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
    }
    .stat-card .stat-icon {
        font-size: 1.75rem;
        opacity: 0.9;
    }
    .stat-card .stat-content {
        flex: 1;
    }
    .stat-card .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .stat-card .stat-label {
        font-size: 0.75rem;
        opacity: 0.85;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    @media (max-width: 768px) {
        .stat-card {
            padding: 0.75rem;
        }
        .stat-card .stat-icon {
            font-size: 1.25rem;
        }
        .stat-card .stat-value {
            font-size: 1.25rem;
        }
        .stat-card .stat-label {
            font-size: 0.65rem;
        }
    }

    /* ============================================ */
    /* New Filter Chip System / 새로운 필터 칩 시스템 */
    /* ============================================ */

    /* Filter Group Cards / 필터 그룹 카드 */
    .filter-group-card {
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: all 0.2s ease;
    }
    .filter-group-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .filter-group-card .card-header {
        border-bottom: none;
        font-size: 0.85rem;
    }
    .filter-group-card .card-body {
        background: #fafbfc;
    }

    /* Filter Chips / 필터 칩 */
    .filter-chip {
        background: #fff;
        border: 1px solid #e0e4e8;
        border-radius: 20px;
        padding: 0.35rem 0.75rem;
        font-size: 0.8rem;
        color: #495057;
        transition: all 0.15s ease;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
    }
    .filter-chip:hover {
        background: #f1f3f5;
        border-color: #ced4da;
        transform: translateY(-1px);
    }
    .filter-chip.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-color: transparent;
        color: #fff;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
    }
    .filter-chip.active .badge {
        background: rgba(255,255,255,0.25) !important;
        color: #fff !important;
    }
    .filter-chip .filter-icon {
        font-size: 0.9rem;
    }
    .filter-chip .badge {
        background: #e9ecef;
        color: #495057;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2em 0.5em;
    }

    /* Danger filter chip / 위험 필터 칩 */
    .filter-chip-danger:not(.active):hover {
        background: #fff5f5;
        border-color: #fecaca;
    }
    .filter-chip-danger.active {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
    }

    /* Active Filters Bar / 활성 필터 바 */
    .active-filters-bar {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 0.75rem 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    .active-filter-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        background: #667eea;
        color: #fff;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
    }
    .active-filter-tag .remove-filter {
        cursor: pointer;
        opacity: 0.7;
        margin-left: 0.25rem;
    }
    .active-filter-tag .remove-filter:hover {
        opacity: 1;
    }

    /* ============================================ */
    /* Improved Table Styles / 개선된 테이블 스타일 */
    /* ============================================ */

    /* Absence count color coding / 결근 수 색상 코딩 */
    .absence-count-0 { color: #9ca3af; }
    .absence-count-low {
        background: #fef3c7;
        color: #92400e;
        font-weight: 500;
        border-radius: 4px;
        padding: 0.15rem 0.4rem;
    }
    .absence-count-high {
        background: #fee2e2;
        color: #991b1b;
        font-weight: 600;
        border-radius: 4px;
        padding: 0.15rem 0.4rem;
    }

    /* Improved status badges / 개선된 상태 배지 */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .status-active {
        background: #d1fae5;
        color: #065f46;
    }
    .status-resigned {
        background: #f3f4f6;
        color: #6b7280;
    }
    .status-new {
        background: #dbeafe;
        color: #1e40af;
    }
    .status-longterm {
        background: #ede9fe;
        color: #5b21b6;
    }
    .status-pregnant {
        background: #fce7f3;
        color: #9d174d;
    }
    .status-risk {
        background: #fef3c7;
        color: #92400e;
    }

    /* Row highlight for resigned employees / 퇴사자 행 하이라이트 */
    .employee-row-resigned {
        background: #f9fafb !important;
        opacity: 0.85;
    }
    .employee-row-resigned:hover {
        background: #f3f4f6 !important;
    }

    /* Skip to main content link for screen readers and keyboard users */
    /* 스크린 리더 및 키보드 사용자를 위한 본문 바로가기 링크 */
    .skip-to-content {
        position: absolute;
        top: -100px;
        left: 50%;
        transform: translateX(-50%);
        background: #1a1a2e;
        color: #fff;
        padding: 12px 24px;
        border-radius: 0 0 8px 8px;
        z-index: 9999;
        text-decoration: none;
        font-weight: 600;
        transition: top 0.3s ease;
    }
    .skip-to-content:focus {
        top: 0;
        outline: 3px solid #667eea;
        outline-offset: 2px;
    }

    /* Loading Indicator / 로딩 인디케이터 */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s, visibility 0.3s;
    }

    .loading-overlay.active {
        opacity: 1;
        visibility: visible;
    }

    .loading-spinner {
        width: 50px;
        height: 50px;
        border: 4px solid #e2e8f0;
        border-top-color: #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    .loading-text {
        margin-top: 16px;
        font-size: 14px;
        color: #475569;  /* Improved contrast: 7.5:1 (was #64748b at 3.8:1) */
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* Last Updated Indicator / 마지막 업데이트 표시 */
    .last-updated {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .last-updated-icon {
        font-size: 14px;
    }

    /* Touch Target Improvements / 터치 영역 개선 */
    button, .btn, [role="button"] {
        min-height: var(--touch-target-min);
        min-width: var(--touch-target-min);
    }

    /* Error Boundary / 오류 경계 */
    .error-boundary {
        padding: 20px;
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 8px;
        color: #991b1b;
        text-align: center;
    }

    .error-boundary-icon {
        font-size: 32px;
        margin-bottom: 8px;
    }

    .error-boundary-message {
        font-weight: 500;
    }

    .error-boundary-retry {
        margin-top: 12px;
        padding: 8px 16px;
        background: #991b1b;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
    }

    /* P1-3 Enhanced: Search Highlighting with animation / 검색 하이라이팅 애니메이션 추가 */
    .search-highlight, mark.search-highlight {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        color: #92400e;
        padding: 1px 4px;
        border-radius: 3px;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(251, 191, 36, 0.4);
        animation: highlightPulse 0.5s ease-out;
    }

    @keyframes highlightPulse {
        0% {
            background: #fbbf24;
            transform: scale(1.1);
        }
        100% {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            transform: scale(1);
        }
    }

    /* Search result count badge / 검색 결과 수 배지 */
    .search-result-count {
        font-size: 11px;
        color: #6c757d;
        margin-left: 8px;
    }

    /* P2-1: Turnover Risk Badge / 이직 위험 배지 */
    .badge-risk {
        font-size: 10px;
        padding: 3px 6px;
        cursor: help;
        animation: riskPulse 2s ease-in-out infinite;
    }

    .badge-risk[data-risk-score] {
        position: relative;
    }

    @keyframes riskPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Risk filter button / 위험 필터 버튼 */
    .btn-risk-filter {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        border: none;
    }

    .btn-risk-filter:hover {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        color: white;
    }

    /* Instant Insights Widget / 즉시 인사이트 위젯 */
    .instant-insights-widget {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #bae6fd;
    }

    .instant-insights-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px dashed #0ea5e9;
    }

    .instant-insights-header span:first-child {
        font-size: 16px;
        font-weight: 600;
        color: #0369a1;
    }

    .insight-timestamp {
        font-size: 12px;
        color: #6c757d;
    }

    .instant-insights-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
    }

    .instant-insight-card {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 12px;
        border-radius: 10px;
        background: white;
        border-left: 4px solid #6c757d;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .instant-insight-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .insight-icon {
        font-size: 24px;
        line-height: 1;
    }

    .insight-content {
        flex: 1;
    }

    .insight-title {
        font-weight: 600;
        font-size: 14px;
        color: #1a1a1a;
        margin-bottom: 4px;
    }

    .insight-desc {
        font-size: 12px;
        color: #6c757d;
    }

    /* Insight type colors / 인사이트 유형별 색상 */
    .insight-positive { border-left-color: #10b981; background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); }
    .insight-negative { border-left-color: #f59e0b; background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); }
    .insight-critical { border-left-color: #ef4444; background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); }
    .insight-warning { border-left-color: #f59e0b; background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); }
    .insight-info { border-left-color: #3b82f6; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); }

    .insight-positive .insight-title { color: #059669; }
    .insight-negative .insight-title { color: #d97706; }
    .insight-critical .insight-title { color: #dc2626; }
    .insight-warning .insight-title { color: #d97706; }
    .insight-info .insight-title { color: #2563eb; }

    /* Top Navigation Bar / 상단 네비게이션 바 */
    .top-navbar {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 12px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        position: sticky;
        top: 0;
        z-index: 1000;
    }

    .nav-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        color: white;
    }

    .nav-icon {
        font-size: 1.5rem;
    }

    .nav-title {
        font-size: 1.1rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .nav-links {
        display: flex;
        gap: 8px;
    }

    .top-navbar .nav-link {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 18px;
        border-radius: 8px;
        text-decoration: none;
        color: rgba(255,255,255,0.8);
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
        font-size: 0.9rem;
    }

    .top-navbar .nav-link:hover {
        background: rgba(255,255,255,0.15);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .top-navbar .nav-link.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: transparent;
    }

    .top-navbar .nav-link-icon {
        font-size: 1.1rem;
    }

    @media (max-width: 768px) {
        .nav-title {
            display: none;
        }
        .top-navbar .nav-link-text {
            display: none;
        }
        .top-navbar .nav-link {
            padding: 10px 14px;
        }
        .top-navbar .nav-link-icon {
            font-size: 1.3rem;
        }
    }

    .dashboard-header {
        background: var(--primary-gradient);
        color: white;
        padding: 40px 0;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }

    .dashboard-header h1 {
        font-weight: 700;
        margin-bottom: 10px;
    }

    /* Header Controls Container / 헤더 컨트롤 컨테이너 */
    .header-controls {
        position: absolute;
        top: 20px;
        right: 20px;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 10px;
        z-index: 10;
    }

    /* Language Switcher */
    .language-switcher {
        display: flex;
        gap: 8px;
    }

    .lang-btn {
        width: 45px;
        height: 45px;
        border: 2px solid rgba(255,255,255,0.3);
        background: rgba(255,255,255,0.1);
        border-radius: 50%;
        font-size: 24px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
    }

    .lang-btn:hover {
        background: rgba(255,255,255,0.2);
        border-color: rgba(255,255,255,0.6);
        transform: scale(1.1);
    }

    .lang-btn.active {
        background: white;
        border-color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: scale(1.15);
    }

    /* Download Button / 다운로드 버튼 */
    .download-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        background: rgba(255,255,255,0.15);
        border: 2px solid rgba(255,255,255,0.4);
        border-radius: 25px;
        color: white;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }

    .download-btn:hover {
        background: rgba(255,255,255,0.25);
        border-color: rgba(255,255,255,0.7);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .download-btn:active {
        transform: translateY(0);
    }

    .download-icon {
        font-size: 18px;
    }

    @media (max-width: 768px) {
        .header-controls {
            top: 10px;
            right: 10px;
            gap: 8px;
        }

        /* Touch target minimum 44x44px for accessibility / 접근성을 위한 최소 터치 영역 44x44px */
        .lang-btn {
            width: 44px;
            height: 44px;
            font-size: 20px;
            min-width: 44px;
            min-height: 44px;
        }

        .download-btn {
            padding: 10px 16px;
            font-size: 14px;
            min-height: 44px;
        }

        .download-text {
            display: none;
        }

        .download-icon {
            font-size: 20px;
        }
    }

    /* Download Toast Notification / 다운로드 토스트 알림 */
    .download-toast {
        position: fixed;
        bottom: 30px;
        right: 30px;
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 24px;
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(40, 167, 69, 0.4);
        z-index: 9999;
        opacity: 0;
        transform: translateY(20px) scale(0.95);
        transition: all 0.3s ease;
    }

    .download-toast.show {
        opacity: 1;
        transform: translateY(0) scale(1);
    }

    .download-toast-icon {
        font-size: 28px;
        animation: bounce 0.5s ease;
    }

    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }

    .download-toast-content {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .download-toast-message {
        font-size: 15px;
        font-weight: 600;
    }

    .download-toast-filename {
        font-size: 12px;
        opacity: 0.9;
        font-family: monospace;
    }

    @media (max-width: 768px) {
        .download-toast {
            bottom: 20px;
            right: 20px;
            left: 20px;
            padding: 12px 16px;
        }

        .download-toast-icon {
            font-size: 24px;
        }

        .download-toast-message {
            font-size: 13px;
        }

        .download-toast-filename {
            font-size: 10px;
        }
    }

    .summary-card {
        background: white;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: var(--card-shadow);
        transition: transform 0.3s, box-shadow 0.3s;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }

    .summary-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--card-hover-shadow);
    }

    .summary-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--primary-gradient);
    }

    /* KPI Card Threshold Status Indicators */
    /* KPI 카드 임계값 상태 표시기 */
    .summary-card.status-critical {
        border: 2px solid #dc3545;
        box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.15);
    }
    .summary-card.status-critical::before {
        background: #dc3545;
        width: 6px;
    }
    .summary-card.status-critical .card-number {
        background: #dc3545;
        animation: pulse-critical 2s infinite;
    }
    @keyframes pulse-critical {
        0%, 100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.5); }
        50% { box-shadow: 0 0 0 8px rgba(220, 53, 69, 0); }
    }

    .summary-card.status-warning {
        border: 2px solid #ffc107;
        box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.15);
    }
    .summary-card.status-warning::before {
        background: #ffc107;
        width: 6px;
    }
    .summary-card.status-warning .card-number {
        background: #ffc107;
        color: #212529;
    }

    .summary-card.status-good {
        border: 2px solid #17a2b8;
    }
    .summary-card.status-good::before {
        background: #17a2b8;
    }

    .summary-card.status-excellent {
        border: 2px solid #28a745;
    }
    .summary-card.status-excellent::before {
        background: #28a745;
    }
    .summary-card.status-excellent .card-number {
        background: #28a745;
    }

    .card-number {
        position: absolute;
        top: 15px;
        right: 15px;
        width: 35px;
        height: 35px;
        border-radius: 50%;
        background: #667eea;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
    }

    .card-title {
        font-size: 14px;
        color: #6c757d;
        margin-bottom: 10px;
        font-weight: 600;
    }

    .card-value {
        font-size: 36px;
        font-weight: bold;
        color: #1a1a1a;
        margin-bottom: 10px;
    }

    .card-change {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
    }

    .card-change.positive {
        background: #d4edda;
        color: #155724;
    }

    .card-change.negative {
        background: #f8d7da;
        color: #721c24;
    }

    /* Trend Arrow Styles - 트렌드 화살표 스타일 */
    .trend-arrow {
        font-size: 1.1em;
        font-weight: bold;
        margin-right: 4px;
    }

    .card-change.positive .trend-arrow {
        color: #28a745;
    }

    .card-change.negative .trend-arrow {
        color: #dc3545;
    }

    .card-info-line {
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #e9ecef;
        font-size: 12px;
        line-height: 1.4;
    }

    .card-info-line small {
        display: block;
        color: #6c757d;
        font-weight: 500;
    }

    .summary-card[title] {
        cursor: help;
    }

    .summary-card[title]:hover .card-info-line {
        background: #f8f9fa;
        border-radius: 6px;
        padding: 4px 8px;
        margin: 8px -8px -8px;
    }

    /* Team Alert Widget Styles / 팀 알림 위젯 스타일 */
    .team-alert-widget {
        background: linear-gradient(135deg, #fff8f0 0%, #fff5f5 100%);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #ffe0cc;
    }

    .team-alert-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px dashed #ffc107;
    }

    .team-alert-header h5 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #6c757d;
    }

    .team-alert-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }

    @media (max-width: 768px) {
        .team-alert-grid {
            grid-template-columns: 1fr;
        }
    }

    .team-alert-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }

    .team-alert-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    .team-alert-card.alert-critical {
        border-color: #dc3545;
        background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
    }

    .team-alert-card.alert-warning {
        border-color: #ffc107;
        background: linear-gradient(135deg, #fffef5 0%, #fff8e1 100%);
    }

    .team-alert-card.alert-info {
        border-color: #17a2b8;
        background: linear-gradient(135deg, #f0f9ff 0%, #e3f2fd 100%);
    }

    .team-alert-rank {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        font-size: 12px;
        font-weight: bold;
        margin-right: 8px;
    }

    .team-alert-card.alert-critical .team-alert-rank {
        background: #dc3545;
        color: white;
    }

    .team-alert-card.alert-warning .team-alert-rank {
        background: #ffc107;
        color: #212529;
    }

    .team-alert-card.alert-info .team-alert-rank {
        background: #17a2b8;
        color: white;
    }

    .team-alert-name {
        font-weight: 600;
        font-size: 14px;
        color: #212529;
    }

    .team-alert-metrics {
        margin-top: 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .team-alert-metric {
        display: inline-flex;
        align-items: center;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 11px;
        background: rgba(0,0,0,0.05);
    }

    .team-alert-metric.metric-bad {
        background: rgba(220, 53, 69, 0.1);
        color: #dc3545;
    }

    .team-alert-metric.metric-warn {
        background: rgba(255, 193, 7, 0.15);
        color: #856404;
    }

    .team-alert-click-hint {
        font-size: 10px;
        color: #6c757d;
        margin-top: 8px;
        text-align: right;
    }

    /* Executive Summary Section Styles / 현황 요약 섹션 스타일 */
    .executive-summary {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
        border: 1px solid rgba(102, 126, 234, 0.1);
        overflow: hidden;
    }

    .summary-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .summary-title {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
    }

    .summary-period {
        font-size: 14px;
        opacity: 0.9;
        background: rgba(255,255,255,0.2);
        padding: 4px 12px;
        border-radius: 12px;
    }

    .summary-header-right {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .quality-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        font-size: 13px;
        cursor: help;
        transition: transform 0.2s;
    }

    .quality-badge:hover {
        transform: scale(1.05);
    }

    .quality-grade {
        font-size: 14px;
        font-weight: 700;
    }

    .quality-score {
        font-size: 12px;
        opacity: 0.9;
    }

    .summary-body {
        padding: 20px 24px;
    }

    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 12px;
        margin-bottom: 16px;
    }

    .status-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        border-radius: 10px;
        background: white;
        border-left: 4px solid;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .status-item.status-success {
        border-left-color: #28a745;
        background: linear-gradient(135deg, #ffffff 0%, #d4edda 100%);
    }

    .status-item.status-warning {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, #ffffff 0%, #fff3cd 100%);
    }

    .status-item.status-danger {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, #ffffff 0%, #f8d7da 100%);
    }

    .status-icon {
        font-size: 20px;
    }

    .status-text {
        font-size: 14px;
        color: #333;
        font-weight: 500;
    }

    .summary-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
        margin: 16px 0;
    }

    .summary-columns {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
    }

    @media (max-width: 768px) {
        .summary-columns {
            grid-template-columns: 1fr;
        }
    }

    .issues-section, .actions-section {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .section-label {
        font-size: 14px;
        font-weight: 600;
        color: #495057;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e9ecef;
    }

    .issue-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
    }

    .issue-item:last-child {
        border-bottom: none;
    }

    /* Clickable Issue Items / 클릭 가능한 이슈 아이템 */
    .issue-item-clickable {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 10px 12px;
        border-bottom: 1px solid #f0f0f0;
        cursor: pointer;
        border-radius: 8px;
        transition: all 0.2s ease;
        margin-bottom: 4px;
    }

    .issue-item-clickable:hover {
        background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
        transform: translateX(4px);
        box-shadow: 0 2px 8px rgba(220, 53, 69, 0.15);
    }

    .issue-item-clickable:last-child {
        border-bottom: none;
    }

    .issue-item-clickable .issue-arrow {
        font-size: 14px;
        opacity: 0.5;
        margin-left: auto;
        transition: opacity 0.2s ease;
    }

    .issue-item-clickable:hover .issue-arrow {
        opacity: 1;
    }

    /* Positive Changes Section / 긍정적 변화 섹션 */
    .positive-section {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .positive-item-clickable {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 10px 12px;
        border-bottom: 1px solid #f0f0f0;
        cursor: pointer;
        border-radius: 8px;
        transition: all 0.2s ease;
        margin-bottom: 4px;
    }

    .positive-item-clickable:hover {
        background: linear-gradient(135deg, #f0fff4 0%, #d4edda 100%);
        transform: translateX(4px);
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.15);
    }

    .positive-item-clickable:last-child {
        border-bottom: none;
    }

    .positive-item-clickable .positive-arrow {
        font-size: 14px;
        opacity: 0.5;
        margin-left: auto;
        transition: opacity 0.2s ease;
    }

    .positive-item-clickable:hover .positive-arrow {
        opacity: 1;
    }

    .positive-severity {
        font-size: 16px;
        flex-shrink: 0;
    }

    .positive-text {
        font-size: 13px;
        color: #155724;
        line-height: 1.4;
        flex: 1;
    }

    /* Three Column Layout for Summary / 요약 3열 레이아웃 */
    .summary-columns-three {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 16px;
    }

    @media (max-width: 992px) {
        .summary-columns-three {
            grid-template-columns: 1fr 1fr;
        }
    }

    @media (max-width: 768px) {
        .summary-columns-three {
            grid-template-columns: 1fr;
        }
    }

    /* Issue Summary Modal Styles / 이슈 요약 모달 스타일 */
    .issue-modal-content {
        max-height: 70vh;
        overflow-y: auto;
    }

    .issue-detail-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .issue-detail-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .issue-detail-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px;
        margin-bottom: 16px;
    }

    .issue-metric-box {
        background: white;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .issue-metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #333;
    }

    .issue-metric-label {
        font-size: 12px;
        color: #6c757d;
        margin-top: 4px;
    }

    .issue-detail-table {
        width: 100%;
        font-size: 13px;
    }

    .issue-detail-table th {
        background: #e9ecef;
        padding: 10px;
        text-align: left;
        font-weight: 600;
    }

    .issue-detail-table td {
        padding: 10px;
        border-bottom: 1px solid #dee2e6;
    }

    .issue-detail-table tr:hover {
        background: #f8f9fa;
    }

    .issue-severity {
        font-size: 16px;
        flex-shrink: 0;
    }

    .issue-text {
        font-size: 13px;
        color: #495057;
        line-height: 1.4;
        flex: 1;
    }

    .action-buttons {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .action-btn {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 13px;
        font-weight: 500;
    }

    .action-btn:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .action-arrow {
        font-size: 16px;
        opacity: 0.8;
    }

    .no-actions {
        font-size: 13px;
        color: #6c757d;
        text-align: center;
        padding: 16px;
        background: #f8f9fa;
        border-radius: 8px;
    }

    .charts-section {
        background: white;
        border-radius: 12px;
        padding: 30px;
        box-shadow: var(--card-shadow);
        margin-bottom: 30px;
    }

    .chart-container {
        position: relative;
        height: 300px;
        width: 100%;
        max-width: 100%;
        overflow-x: auto;
        margin-bottom: 30px;
    }

    /* Modal Styles */
    .modal-header {
        background: var(--primary-gradient);
        color: white;
    }

    .modal-title {
        font-weight: 600;
    }

    .btn-close-white {
        filter: brightness(0) invert(1);
    }

    .modal-body {
        max-height: 70vh;
        overflow-y: auto;
    }

    /* Modal Table Styles */
    .modal-table {
        font-size: 0.9rem;
        margin-top: 20px;
    }

    .modal-table thead th {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        font-weight: 600;
        color: #495057;
        cursor: pointer;
        user-select: none;
        position: sticky;
        top: 0;
        z-index: 10;
        padding: 12px 8px;
    }

    .modal-table thead th:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
    }

    .modal-table thead th .sort-icon {
        font-size: 0.8rem;
        margin-left: 5px;
        opacity: 0.5;
    }

    .modal-table tbody tr {
        transition: background-color 0.2s ease;
    }

    /* UX Fix: Remove transform to prevent layout shift */
    /* UX 수정: 레이아웃 변형 방지를 위해 transform 제거 */
    .modal-table tbody tr:hover {
        background: rgba(102, 126, 234, 0.08);
    }

    .modal-chart-container {
        position: relative;
        margin: 20px 0;
        padding: 20px;
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        min-height: 450px;
        width: 100%;
        max-width: 100%;
        overflow-x: auto;
    }

    /* Gradient backgrounds for modal headers */
    .bg-gradient-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }

    .bg-gradient-info {
        background: linear-gradient(135deg, #06beb6 0%, #48b1bf 100%) !important;
    }

    .bg-gradient-warning {
        background: linear-gradient(135deg, #ffd89b 0%, #f9a825 100%) !important;
    }

    .bg-gradient-success {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%) !important;
    }

    .bg-gradient-secondary {
        background: linear-gradient(135deg, #636c72 0%, #868e96 100%) !important;
    }

    /* Metric card styles */
    .metric-card {
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    .modal-chart-container h6 {
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #f0f0f0;
        color: #333;
        font-weight: 600;
    }

    /* Tab Navigation Styles */
    .nav-tabs {
        border-bottom: 2px solid #dee2e6;
    }

    .nav-tabs .nav-link {
        color: #495057;
        font-weight: 500;
        border: none;
        border-bottom: 3px solid transparent;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }

    .nav-tabs .nav-link:hover {
        border-color: transparent;
        color: #667eea;
        background: rgba(102, 126, 234, 0.05);
    }

    .nav-tabs .nav-link.active {
        color: #667eea;
        border-color: #667eea;
        background: transparent;
    }

    /* Details Tab Styles */
    .details-section {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: var(--card-shadow);
    }

    #employeeTable thead th {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        font-weight: 600;
        color: #495057;
        cursor: pointer;
        user-select: none;
        position: sticky;
        top: 0;
        z-index: 10;
    }

    #employeeTable thead th:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
    }

    #employeeTable tbody tr {
        transition: background-color 0.2s ease;
    }

    /* UX Fix: Remove transform to prevent layout shift */
    /* UX 수정: 레이아웃 변형 방지를 위해 transform 제거 */
    #employeeTable tbody tr:hover {
        background: rgba(102, 126, 234, 0.08);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .table-responsive {
        max-height: 600px;
        overflow-y: auto;
    }

    .badge-status {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
    }

    /* Enhanced Table Styles */
    .employee-table thead th.sortable {
        cursor: pointer;
        user-select: none;
        transition: background-color 0.2s;
    }

    .employee-table thead th.sortable:hover {
        background-color: #e9ecef !important;
    }

    .sort-indicator {
        opacity: 0.3;
        margin-left: 5px;
    }

    .sort-indicator::after {
        content: '⬍';
    }

    .sort-indicator.asc {
        opacity: 1;
    }

    .sort-indicator.asc::after {
        content: '▲';
    }

    .sort-indicator.desc {
        opacity: 1;
    }

    .sort-indicator.desc::after {
        content: '▼';
    }

    /* Sorted column highlight / 정렬된 컬럼 강조 */
    .employee-table thead th.sorted {
        background-color: #e3f2fd !important;
        border-bottom: 3px solid #2196f3;
    }

    /* Secondary sorted column / 2차 정렬 컬럼 */
    .employee-table thead th.sorted-secondary {
        background-color: #fff3e0 !important;
        border-bottom: 2px dashed #ff9800;
    }

    /* Multi-sort indicator styling / 다중 정렬 표시 스타일 */
    .sort-indicator {
        font-size: 12px;
        opacity: 0.9;
    }

    th.sorted .sort-indicator,
    th.sorted-secondary .sort-indicator {
        font-weight: bold;
    }

    th.sorted-secondary .sort-indicator {
        color: #e65100;
    }

    .employee-table tbody tr {
        transition: background-color 0.2s;
    }

    /* UX Fix: Remove transform to prevent layout shift */
    /* UX 수정: 레이아웃 변형 방지를 위해 transform 제거 */
    .employee-table tbody tr:hover {
        background-color: #f8f9fa !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .employee-table tbody tr.row-active {
        background-color: #e7f5ff !important;
    }

    .employee-table tbody tr.row-resigned {
        background-color: #ffe3e3 !important;
    }

    .employee-table tbody tr.row-new {
        background-color: #e3f5ff !important;
    }

    .employee-table tbody tr.row-perfect {
        background-color: #e6ffe6 !important;
    }

    .employee-table tbody tr.row-selected {
        background-color: #fff3cd !important;
    }

    /* Search Suggestions */
    .search-suggestions {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-top: none;
        border-radius: 0 0 4px 4px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 1000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .search-suggestion-item {
        padding: 8px 12px;
        cursor: pointer;
        transition: background-color 0.2s;
    }

    .search-suggestion-item:hover {
        background-color: #f8f9fa;
    }

    .search-suggestion-item mark {
        background-color: #fff3cd;
        font-weight: bold;
        padding: 0 2px;
    }

    /* Column visibility */
    .column-hidden {
        display: none !important;
    }

    /* Column Toggle Dropdown - Enhanced Design / 열 표시 드롭다운 - 개선된 디자인 */
    .column-toggle-menu {
        min-width: 280px;
        padding: 0.75rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        border: 1px solid #e9ecef;
    }

    .column-toggle-actions {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #e9ecef;
    }

    .column-toggle-actions .btn {
        flex: 1;
        font-size: 0.75rem;
        padding: 0.35rem 0.5rem;
        border-radius: 6px;
    }

    .column-category {
        margin-bottom: 0.75rem;
    }

    .column-category:last-child {
        margin-bottom: 0;
    }

    .category-header {
        font-size: 0.7rem;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 0.25rem 0.5rem;
        margin-bottom: 0.25rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 6px;
    }

    .column-item {
        display: flex;
        align-items: center;
        padding: 0.4rem 0.5rem;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 2px;
    }

    .column-item:hover {
        background-color: #e7f1ff;
    }

    .column-item input[type="checkbox"] {
        width: 16px;
        height: 16px;
        margin-right: 0.5rem;
        accent-color: #0d6efd;
        cursor: pointer;
    }

    .column-item .column-icon {
        margin-right: 0.5rem;
        font-size: 0.9rem;
    }

    .column-item .column-name {
        font-size: 0.85rem;
        color: #495057;
    }

    /* Bulk Actions - Enhanced Design / 대량 작업 - 개선된 디자인 */
    .bulk-actions-group {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        align-items: center;
    }

    .bulk-actions-group .btn {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .bulk-actions-group .btn:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    .bulk-actions-group .btn:disabled {
        opacity: 0.5;
    }

    .bulk-actions-group .btn-icon {
        font-size: 1rem;
    }

    .bulk-actions-group .btn-text {
        font-size: 0.8rem;
    }

    /* Accessibility */
    .btn:focus, .form-control:focus, .form-select:focus {
        outline: 2px solid #4285f4;
        outline-offset: 2px;
    }

    /* Mobile Responsiveness - Enhanced / 모바일 반응형 - 개선됨 */
    @media (max-width: 768px) {
        .btn-toolbar {
            flex-direction: column;
        }

        .btn-toolbar .btn-group {
            width: 100%;
            margin-bottom: 0.5rem;
            flex-wrap: wrap;
        }

        .btn-toolbar .btn-group .btn {
            flex: 1 1 auto;
            min-width: calc(50% - 2px);
            font-size: 0.75rem;
            padding: 0.35rem 0.5rem;
        }

        .employee-table {
            font-size: 0.75rem;
        }

        .employee-table thead th {
            font-size: 0.7rem;
            padding: 0.4rem 0.25rem !important;
            white-space: nowrap;
        }

        .employee-table tbody td {
            padding: 0.35rem 0.25rem !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100px;
        }

        .employee-table tbody tr:hover {
            transform: none;
        }

        /* Hide less important columns on mobile / 모바일에서 덜 중요한 컬럼 숨기기 */
        .employee-table th:nth-child(5),
        .employee-table td:nth-child(5),
        .employee-table th:nth-child(6),
        .employee-table td:nth-child(6),
        .employee-table th:nth-child(7),
        .employee-table td:nth-child(7),
        .employee-table th:nth-child(9),
        .employee-table td:nth-child(9) {
            display: none !important;
        }

        /* Smaller badges on mobile / 모바일에서 작은 배지 */
        .badge-status {
            font-size: 0.6rem !important;
            padding: 0.15rem 0.3rem !important;
        }

        /* Compact search / 컴팩트 검색 */
        #employeeSearch {
            font-size: 0.85rem;
        }

        /* Quick stats panel / 빠른 통계 패널 */
        #quickStatsPanel .stat-value {
            font-size: 1rem !important;
        }

        #quickStatsPanel .stat-label {
            font-size: 0.65rem !important;
        }

        #quickStatsPanel .stat-item {
            padding: 0.5rem !important;
        }

        /* Pagination controls / 페이지네이션 컨트롤 */
        .pagination .btn {
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
        }

        #pageInfo {
            font-size: 0.75rem;
        }

        /* Column visibility dropdown / 컬럼 표시 드롭다운 */
        .dropdown-menu {
            max-height: 300px;
            overflow-y: auto;
        }

        /* Column toggle mobile / 열 표시 모바일 */
        .column-toggle-menu {
            min-width: 260px;
        }

        .column-toggle-actions .btn {
            padding: 0.25rem 0.4rem;
            font-size: 0.7rem;
        }

        .category-header {
            font-size: 0.65rem;
        }

        .column-item {
            padding: 0.3rem 0.4rem;
        }

        .column-item .column-name {
            font-size: 0.8rem;
        }

        /* Bulk actions mobile - icon only / 대량 작업 모바일 - 아이콘만 */
        .bulk-actions-group .btn-text {
            display: none;
        }

        .bulk-actions-group .btn {
            padding: 0.35rem 0.5rem;
        }
    }

    /* Extra small devices / 매우 작은 기기 */
    /* WCAG AA Fix: Minimum 14px font size for accessibility */
    /* WCAG AA 수정: 접근성을 위한 최소 14px 폰트 크기 */
    @media (max-width: 480px) {
        .employee-table {
            font-size: 0.875rem;  /* 14px - WCAG AA minimum */
        }

        .employee-table thead th {
            font-size: 0.8125rem;  /* 13px */
        }

        .employee-table tbody td {
            max-width: 90px;
        }

        /* Hide even more columns / 더 많은 컬럼 숨기기 */
        .employee-table th:nth-child(4),
        .employee-table td:nth-child(4),
        .employee-table th:nth-child(8),
        .employee-table td:nth-child(8) {
            display: none !important;
        }

        .badge-status {
            font-size: 0.6875rem !important;  /* 11px minimum */
        }

        .btn-toolbar .btn-group .btn {
            font-size: 0.75rem;  /* 12px */
            padding: 0.25rem 0.4rem;
        }
    }

    /* Organization Chart Styles */
    .orgchart-section {
        min-height: 600px;
    }

    .org-tree-container {
        padding: 20px;
    }

    .org-tree-node {
        margin: 15px 0;
        padding-left: 30px;
        border-left: 2px solid #dee2e6;
    }

    .org-tree-node:last-child {
        border-left-color: transparent;
    }

    .node-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
    }

    .node-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateX(5px);
    }

    .node-card.health-good {
        border-left: 4px solid #28a745;
    }

    .node-card.health-warning {
        border-left: 4px solid #ffc107;
    }

    .node-card.health-danger {
        border-left: 4px solid #dc3545;
    }

    .node-metrics {
        display: flex;
        gap: 5px;
        flex-wrap: wrap;
    }

    /* Organization Chart Styles */
    .org-network-container {
        margin-bottom: 30px;
    }

    #orgNetworkChart svg {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        background: #f8f9fa;
    }

    .hierarchy-node {
        margin-bottom: 5px;
    }

    .hierarchy-node-card {
        padding: 12px 15px;
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .hierarchy-node-card:hover {
        background: #f8f9fa;
        border-color: #667eea;
        transform: translateX(3px);
    }

    .hierarchy-children {
        margin-top: 5px;
    }

    .toggle-icon {
        transition: transform 0.2s ease;
    }

    #managerTable {
        margin-top: 20px;
    }

    #managerTable th {
        background: #667eea;
        color: white;
        font-weight: 600;
    }

    .node-children {
        margin-top: 10px;
    }

    .mini-chart {
        margin-top: 10px;
        height: 50px;
    }

    /* Heatmap Grid */
    .heatmap-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 15px;
        padding: 20px;
    }

    .heatmap-cell {
        background: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid #dee2e6;
    }

    .heatmap-cell:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    .heatmap-name {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }

    .heatmap-position {
        font-size: 0.75rem;
        color: #6c757d;
        margin-bottom: 8px;
    }

    .heatmap-value {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 5px 0;
    }

    .heatmap-team {
        font-size: 0.8rem;
        color: #6c757d;
    }

    /* KPI Mini Card Styles for Team Summary */
    .kpi-mini-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        transition: all 0.2s ease;
        height: 100%;
        min-height: 100px;
    }

    .kpi-mini-card:hover {
        background: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }

    .kpi-label {
        font-size: 0.85rem;
        color: #6c757d;
        font-weight: 500;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }

    .kpi-value {
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
    }

    /* Comparison View */
    .comparison-section {
        padding: 20px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Team Analysis Styles */
    .teamanalysis-section {
        min-height: 600px;
    }

    .team-selector-group {
        display: flex;
        gap: 10px;
    }

    .team-selector-group select {
        min-width: 200px;
    }

    #teamDetailsTable tbody tr {
        cursor: pointer;
        transition: background-color 0.2s ease;
    }

    /* ============================================
       Mobile Responsive Styles (Phase 3 Optimization)
       ============================================ */

    /* Touch-friendly improvements for mobile */
    @media (max-width: 768px) {
        /* Increase tap target sizes */
        .kpi-card {
            min-height: 120px;
            margin-bottom: 15px;
        }

        .nav-tabs .nav-link {
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
        }

        /* Stack KPI cards vertically on mobile */
        .kpi-row {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        /* Reduce modal chart container heights for mobile */
        .modal-chart-container {
            min-height: 300px;
            padding: 15px;
        }

        /* Make tables horizontally scrollable */
        .table-responsive {
            max-height: 400px;
        }

        .modal-table {
            font-size: 0.85rem;
        }

        /* Adjust chart heights for mobile */
        canvas {
            max-height: 300px !important;
        }

        /* Treemap mobile optimization */
        #teamDetailTreemap {
            height: 350px !important;
        }

        /* Sunburst mobile layout */
        .modal-chart-container > div {
            flex-direction: column !important;
        }

        #sunburstChart {
            width: 100% !important;
            min-width: unset !important;
        }

        #sunburstLegend {
            width: 100% !important;
            max-height: 300px !important;
            margin-top: 15px;
        }

        /* Hide less important columns on mobile */
        .modal-table th:nth-child(n+5),
        .modal-table td:nth-child(n+5) {
            display: none;
        }

        /* Adjust header for mobile */
        .header-content h1 {
            font-size: 1.5rem;
        }

        .header-subtitle {
            font-size: 0.9rem;
        }
    }

    /* Tablet responsive (768px - 1024px) */
    @media (min-width: 768px) and (max-width: 1024px) {
        .kpi-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }

        .modal-chart-container {
            min-height: 400px;
        }

        canvas {
            max-height: 350px !important;
        }
    }

    /* Touch event optimization */
    @media (hover: none) and (pointer: coarse) {
        /* Increase tap targets for touch devices */
        .kpi-card {
            padding: 20px;
        }

        .node-card {
            padding: 20px;
        }

        .heatmap-cell {
            padding: 20px;
        }

        /* Improve scrolling performance on touch devices */
        .table-responsive {
            -webkit-overflow-scrolling: touch;
        }

        /* Disable hover effects on touch devices */
        .kpi-card:hover,
        .node-card:hover,
        .heatmap-cell:hover {
            transform: none;
            box-shadow: inherit;
        }
    }

    /* Executive Summary Mobile Styles / 현황 요약 모바일 스타일 */
    @media (max-width: 768px) {
        .summary-header {
            flex-direction: column;
            gap: 10px;
            text-align: center;
        }

        .summary-header-right {
            flex-direction: row;
            justify-content: center;
        }

        .quality-badge {
            font-size: 11px;
            padding: 3px 8px;
        }

        .quality-grade {
            font-size: 12px;
        }

        .summary-columns-three {
            flex-direction: column;
            gap: 16px;
        }

        .issues-section,
        .positive-section,
        .actions-section {
            width: 100%;
        }

        .status-grid {
            grid-template-columns: 1fr;
        }

        .status-item {
            padding: 10px 12px;
        }

        /* Top navbar mobile / 상단 네비게이션 모바일 */
        .top-navbar {
            padding: 8px 12px;
        }

        .nav-title {
            font-size: 14px;
        }

        .top-navbar .nav-link-text {
            display: none;
        }

        .top-navbar .nav-link-icon {
            font-size: 18px;
        }

        /* Header controls mobile / 헤더 컨트롤 모바일 */
        .header-controls {
            flex-direction: column;
            gap: 8px;
        }

        .download-text {
            display: none;
        }
    }

    @media (max-width: 480px) {
        .summary-title {
            font-size: 15px;
        }

        .summary-period {
            font-size: 12px;
            padding: 2px 8px;
        }

        .quality-badge {
            font-size: 10px;
            padding: 2px 6px;
        }

        .issue-item-clickable,
        .positive-item-clickable {
            padding: 8px;
            font-size: 12px;
        }

        .action-btn {
            padding: 6px 12px;
            font-size: 11px;
        }
    }

    #teamDetailsTable tbody tr:hover {
        background-color: #f8f9fa;
    }
</style>
"""

    def _generate_header(self) -> str:
        """Generate dashboard header with language switcher"""
        year, month = self.target_month.split('-')
        report_date_str = self.report_date.strftime('%Y-%m-%d')
        report_date_ko = self.report_date.strftime('%Y년 %m월 %d일')
        report_date_en = self.report_date.strftime('%Y/%m/%d')
        report_date_vi = self.report_date.strftime('%d/%m/%Y')

        return f"""
<!-- Top Navigation Bar / 상단 네비게이션 바 -->
<nav class="top-navbar" role="navigation" aria-label="Main navigation">
    <div class="container-xl d-flex justify-content-between align-items-center">
        <div class="nav-brand">
            <span class="nav-icon" aria-hidden="true">📊</span>
            <span class="nav-title lang-text" data-ko="HR 관리 시스템" data-en="HR Management System" data-vi="Hệ thống quản lý HR">HR 관리 시스템</span>
        </div>
        <div class="nav-links" role="menubar">
            <a href="selector.html" class="nav-link active" title="HR Dashboard" role="menuitem" aria-current="page">
                <span class="nav-link-icon" aria-hidden="true">👥</span>
                <span class="nav-link-text lang-text" data-ko="HR 대시보드" data-en="HR Dashboard" data-vi="Bảng điều khiển HR">HR 대시보드</span>
            </a>
            <a href="https://moonkaicuzui.github.io/qip-dashboard/" class="nav-link" title="Incentive Dashboard" role="menuitem">
                <span class="nav-link-icon" aria-hidden="true">💰</span>
                <span class="nav-link-text lang-text" data-ko="인센티브 대시보드" data-en="Incentive Dashboard" data-vi="Bảng khuyến khích">인센티브 대시보드</span>
            </a>
        </div>
    </div>
</nav>

<div class="dashboard-header">
    <div class="container-xl position-relative">
        <!-- Language Switcher & Download Button -->
        <!-- 언어 전환 및 다운로드 버튼 -->
        <div class="header-controls">
            <div class="language-switcher" role="group" aria-label="Language selection">
                <button class="lang-btn{' active' if self.language == 'ko' else ''}" data-lang="ko" onclick="switchLanguage('ko')" title="한국어" aria-label="Switch to Korean" aria-pressed="{'true' if self.language == 'ko' else 'false'}">🇰🇷</button>
                <button class="lang-btn{' active' if self.language == 'en' else ''}" data-lang="en" onclick="switchLanguage('en')" title="English" aria-label="Switch to English" aria-pressed="{'true' if self.language == 'en' else 'false'}">🇺🇸</button>
                <button class="lang-btn{' active' if self.language == 'vi' else ''}" data-lang="vi" onclick="switchLanguage('vi')" title="Tiếng Việt" aria-label="Switch to Vietnamese" aria-pressed="{'true' if self.language == 'vi' else 'false'}">🇻🇳</button>
            </div>
            <button class="download-btn" onclick="downloadDashboard()" title="대시보드 다운로드" aria-label="Download dashboard as HTML file">
                <span class="download-icon" aria-hidden="true">📥</span>
                <span class="download-text lang-text" data-ko="다운로드" data-en="Download" data-vi="Tải xuống">다운로드</span>
            </button>
        </div>

        <h1 class="lang-title" data-ko="👥 HR 대시보드" data-en="👥 HR Dashboard" data-vi="👥 Bảng điều khiển HR">👥 HR 대시보드</h1>
        <p class="mb-0 lang-subtitle"
           data-ko="인사 현황 대시보드 - {year}년 {int(month)}월"
           data-en="Human Resources Dashboard - {year}/{int(month)}"
           data-vi="Bảng điều khiển Nhân sự - {int(month)}/{year}">
           인사 현황 대시보드 - {year}년 {int(month)}월
        </p>
        <p class="mb-0 mt-1" style="font-size: 0.9rem; opacity: 0.8;">
            <span class="lang-text" data-ko="📅 기준일: {report_date_ko}" data-en="📅 Report Date: {report_date_en}" data-vi="📅 Ngày báo cáo: {report_date_vi}">📅 기준일: {report_date_ko}</span>
        </p>
    </div>
</div>
"""

    def _generate_executive_summary(self, metrics: Dict[str, Any]) -> str:
        """
        Generate Executive Summary section for quick status overview
        빠른 현황 파악을 위한 Executive Summary 섹션 생성

        Features:
        - Status indicators (✅⚠️🚨) based on thresholds
        - Top 3 issues automatically detected
        - Action required list with direct links
        - Multi-language support (KO/EN/VI)
        """
        # Get current month metrics
        # 현재 월 메트릭 가져오기
        total_employees = metrics.get('total_employees', 0)
        absence_rate_incl = metrics.get('absence_rate', 0)  # Including maternity / 출산휴가 포함
        absence_rate = metrics.get('absence_rate_excl_maternity', 0)  # Excluding maternity / 출산휴가 제외
        unauthorized_rate = metrics.get('unauthorized_absence_rate', 0)
        resignation_rate = metrics.get('resignation_rate', 0)
        recent_hires = metrics.get('recent_hires', 0)
        recent_resignations = metrics.get('recent_resignations', 0)
        under_60_days = metrics.get('under_60_days', 0)
        data_errors = metrics.get('data_errors', 0)

        # Get previous month change
        # 전월 대비 변화 가져오기
        total_change = self.calculator.get_month_over_month_change('total_employees', self.target_month)
        total_change_val = total_change['absolute'] if total_change else 0
        total_change_sign = '+' if total_change_val >= 0 else ''

        # Define thresholds for status indicators
        # 상태 표시를 위한 임계치 정의
        ABSENCE_TARGET = 10.0  # Target: 10%
        ABSENCE_WARNING = 12.0  # Warning: 12%
        UNAUTHORIZED_WARNING = 2.0  # Warning: 2%
        UNAUTHORIZED_CRITICAL = 5.0  # Critical: 5%

        # Determine status for each metric
        # 각 메트릭에 대한 상태 결정

        # Total employees status (always normal unless dramatic change)
        # 총 인원 상태 (급격한 변화가 없으면 정상)
        if abs(total_change_val) > 20:
            total_status = '⚠️'
            total_status_class = 'warning'
        else:
            total_status = '✅'
            total_status_class = 'success'

        # Absence rate status - show both including and excluding maternity
        # 결근율 상태 - 출산휴가 포함/제외 둘 다 표시
        if absence_rate <= ABSENCE_TARGET:
            absence_status = '✅'
            absence_status_class = 'success'
            absence_msg_ko = f'결근율 {absence_rate:.1f}% (출산휴가 제외) / {absence_rate_incl:.1f}% (포함) - 목표 {ABSENCE_TARGET}% 이내'
            absence_msg_en = f'Absence {absence_rate:.1f}% (excl. maternity) / {absence_rate_incl:.1f}% (incl.) - target ≤{ABSENCE_TARGET}%'
            absence_msg_vi = f'Vắng {absence_rate:.1f}% (không thai sản) / {absence_rate_incl:.1f}% (có) - mục tiêu ≤{ABSENCE_TARGET}%'
        elif absence_rate <= ABSENCE_WARNING:
            absence_status = '⚠️'
            absence_status_class = 'warning'
            absence_msg_ko = f'결근율 {absence_rate:.1f}% (출산휴가 제외) / {absence_rate_incl:.1f}% (포함) - 목표 초과'
            absence_msg_en = f'Absence {absence_rate:.1f}% (excl. maternity) / {absence_rate_incl:.1f}% (incl.) - above target'
            absence_msg_vi = f'Vắng {absence_rate:.1f}% (không thai sản) / {absence_rate_incl:.1f}% (có) - vượt mục tiêu'
        else:
            absence_status = '🚨'
            absence_status_class = 'danger'
            absence_msg_ko = f'결근율 {absence_rate:.1f}% (출산휴가 제외) / {absence_rate_incl:.1f}% (포함) - 크게 초과'
            absence_msg_en = f'Absence {absence_rate:.1f}% (excl. maternity) / {absence_rate_incl:.1f}% (incl.) - significantly above'
            absence_msg_vi = f'Vắng {absence_rate:.1f}% (không thai sản) / {absence_rate_incl:.1f}% (có) - vượt xa'

        # Unauthorized absence status
        # 무단결근 상태
        # Count employees with unauthorized absence
        unauthorized_count = 0
        for emp in self.employee_details:
            if emp.get('has_unauthorized_absence', False):
                unauthorized_count += 1

        if unauthorized_rate <= UNAUTHORIZED_WARNING and unauthorized_count == 0:
            unauthorized_status = '✅'
            unauthorized_status_class = 'success'
            unauthorized_msg_ko = '무단결근 없음'
            unauthorized_msg_en = 'No unauthorized absence'
            unauthorized_msg_vi = 'Không vắng không phép'
        elif unauthorized_rate <= UNAUTHORIZED_CRITICAL:
            unauthorized_status = '⚠️'
            unauthorized_status_class = 'warning'
            unauthorized_msg_ko = f'무단결근 {unauthorized_count}명 - 관리 필요'
            unauthorized_msg_en = f'Unauthorized absence: {unauthorized_count} - needs attention'
            unauthorized_msg_vi = f'Vắng không phép: {unauthorized_count} - cần chú ý'
        else:
            unauthorized_status = '🚨'
            unauthorized_status_class = 'danger'
            unauthorized_msg_ko = f'무단결근 {unauthorized_count}명 - 즉시 조치 필요'
            unauthorized_msg_en = f'Unauthorized absence: {unauthorized_count} - immediate action needed'
            unauthorized_msg_vi = f'Vắng không phép: {unauthorized_count} - cần xử lý ngay'

        # Detect Top 3 Issues automatically
        # 상위 3개 이슈 자동 감지
        issues = []

        # Issue 1: Team with high absence rate
        # 이슈 1: 결근율 높은 팀
        if self.team_data:
            team_absence_rates = []
            for team_name, team_info in self.team_data.items():
                members = team_info.get('members', [])
                active_members = [m for m in members if m.get('is_active', False)]
                if len(active_members) >= 3:  # Only teams with 3+ members
                    total_working = sum(m.get('working_days', 0) for m in active_members)
                    total_absent = sum(m.get('absent_days', 0) for m in active_members)
                    if total_working > 0:
                        team_rate = (total_absent / total_working) * 100
                        team_absence_rates.append((team_name, team_rate, len(active_members)))

            if team_absence_rates:
                team_absence_rates.sort(key=lambda x: x[1], reverse=True)
                worst_team = team_absence_rates[0]
                if worst_team[1] > ABSENCE_TARGET * 1.5:  # 50% above target
                    issues.append({
                        'severity': '🚨' if worst_team[1] > ABSENCE_TARGET * 2 else '⚠️',
                        'type': 'absence_high',
                        'ko': f'{worst_team[0]}팀 결근율 {worst_team[1]:.1f}% (전사 평균 대비 높음)',
                        'en': f'{worst_team[0]} team absence {worst_team[1]:.1f}% (above company avg)',
                        'vi': f'Nhóm {worst_team[0]} vắng {worst_team[1]:.1f}% (cao hơn TB công ty)',
                        'details': {
                            'metric': 'absence_rate_excl_maternity',
                            'current': worst_team[1],
                            'previous': None,
                            'team': worst_team[0],
                            'team_count': worst_team[2]
                        }
                    })

        # Issue 2: High new employee turnover risk
        # 이슈 2: 신규 입사자 이탈 위험
        if under_60_days > 0:
            turnover_risk_pct = (under_60_days / total_employees * 100) if total_employees > 0 else 0
            if turnover_risk_pct > 10:
                issues.append({
                    'severity': '⚠️',
                    'type': 'under60_high',
                    'ko': f'60일 미만 재직자 {under_60_days}명 ({turnover_risk_pct:.1f}%) - 이탈 위험군',
                    'en': f'{under_60_days} employees under 60 days ({turnover_risk_pct:.1f}%) - turnover risk',
                    'vi': f'{under_60_days} NV dưới 60 ngày ({turnover_risk_pct:.1f}%) - rủi ro nghỉ việc',
                    'details': {
                        'metric': 'under_60_days',
                        'current': under_60_days,
                        'previous': None,
                        'percentage': turnover_risk_pct
                    }
                })

        # Issue 3: Data quality issues
        # 이슈 3: 데이터 품질 문제
        if data_errors > 0:
            issues.append({
                'severity': '⚠️' if data_errors < 10 else '🚨',
                'type': 'data_errors',
                'ko': f'데이터 오류 {data_errors}건 - 정정 필요',
                'en': f'{data_errors} data errors - correction needed',
                'vi': f'{data_errors} lỗi dữ liệu - cần sửa',
                'details': {
                    'metric': 'data_errors',
                    'current': data_errors,
                    'previous': None
                }
            })

        # Issue 4: High resignation rate
        # 이슈 4: 높은 퇴사율
        if resignation_rate > 5:
            issues.append({
                'severity': '🚨' if resignation_rate > 10 else '⚠️',
                'type': 'resignation_high',
                'ko': f'퇴사율 {resignation_rate:.1f}% - 주의 필요',
                'en': f'Resignation rate {resignation_rate:.1f}% - attention needed',
                'vi': f'Tỷ lệ nghỉ việc {resignation_rate:.1f}% - cần chú ý',
                'details': {
                    'metric': 'resignation_rate',
                    'current': resignation_rate,
                    'previous': None
                }
            })

        # Issue 5: Unauthorized absence concentration
        # 이슈 5: 무단결근 집중
        if unauthorized_count >= 3:
            issues.append({
                'severity': '🚨',
                'type': 'unauthorized_high',
                'ko': f'무단결근 {unauthorized_count}명 집중 발생',
                'en': f'Unauthorized absence concentrated: {unauthorized_count} employees',
                'vi': f'Vắng không phép tập trung: {unauthorized_count} NV',
                'details': {
                    'metric': 'unauthorized_absence_rate',
                    'current': unauthorized_count,
                    'previous': None
                }
            })

        # Sort issues by severity and take top 3
        # 심각도로 정렬하고 상위 3개 선택
        severity_order = {'🚨': 0, '⚠️': 1, '✅': 2}
        issues.sort(key=lambda x: severity_order.get(x['severity'], 2))
        top_issues = issues[:3]

        # ========================================
        # Detect Positive Changes / 긍정적 변화 감지
        # ========================================
        positive_changes = []

        # Positive 1: Resignation rate decreased significantly
        # 긍정 1: 퇴사율 크게 감소
        resignation_change = self.calculator.get_month_over_month_change('resignation_rate', self.target_month)
        if resignation_change and resignation_change['absolute'] < -1:
            positive_changes.append({
                'id': 'positive_resignation',
                'type': 'resignation_improved',
                'icon': '📉',
                'ko': f"퇴사율 {abs(resignation_change['absolute']):.1f}%p 감소 ({resignation_change['percentage']:.1f}% 개선)",
                'en': f"Resignation rate down {abs(resignation_change['absolute']):.1f}%p ({abs(resignation_change['percentage']):.1f}% improvement)",
                'vi': f"Tỷ lệ nghỉ việc giảm {abs(resignation_change['absolute']):.1f}%p ({abs(resignation_change['percentage']):.1f}% cải thiện)",
                'details': {
                    'metric': 'resignation_rate',
                    'current': resignation_rate,
                    'previous': resignation_rate - resignation_change['absolute'],
                    'change': resignation_change
                }
            })

        # Positive 2: Perfect attendance increased
        # 긍정 2: 개근 직원 증가
        perfect_attendance = metrics.get('perfect_attendance', 0)
        perfect_change = self.calculator.get_month_over_month_change('perfect_attendance', self.target_month)
        if perfect_change and perfect_change['absolute'] > 5:
            positive_changes.append({
                'id': 'positive_attendance',
                'type': 'attendance_improved',
                'icon': '🏆',
                'ko': f"개근 직원 {perfect_change['absolute']:+.0f}명 증가 ({perfect_change['percentage']:.1f}% 증가)",
                'en': f"Perfect attendance up {perfect_change['absolute']:+.0f} employees ({perfect_change['percentage']:.1f}%)",
                'vi': f"Chuyên cần hoàn hảo tăng {perfect_change['absolute']:+.0f} NV ({perfect_change['percentage']:.1f}%)",
                'details': {
                    'metric': 'perfect_attendance',
                    'current': perfect_attendance,
                    'previous': perfect_attendance - perfect_change['absolute'],
                    'change': perfect_change
                }
            })

        # Positive 3: Under 60 days decreased (turnover risk reduced)
        # 긍정 3: 60일 미만 감소 (이탈 위험 감소)
        under60_change = self.calculator.get_month_over_month_change('under_60_days', self.target_month)
        if under60_change and under60_change['absolute'] < -3:
            positive_changes.append({
                'id': 'positive_retention',
                'type': 'retention_improved',
                'icon': '🛡️',
                'ko': f"60일 미만 재직자 {abs(under60_change['absolute']):.0f}명 감소 (이탈 위험 감소)",
                'en': f"Under 60 days employees down {abs(under60_change['absolute']):.0f} (lower turnover risk)",
                'vi': f"NV dưới 60 ngày giảm {abs(under60_change['absolute']):.0f} (rủi ro nghỉ việc giảm)",
                'details': {
                    'metric': 'under_60_days',
                    'current': under_60_days,
                    'previous': under_60_days - under60_change['absolute'],
                    'change': under60_change
                }
            })

        # Positive 4: Total employees increased (growth)
        # 긍정 4: 총 인원 증가 (성장)
        if total_change and total_change_val > 3:
            positive_changes.append({
                'id': 'positive_growth',
                'type': 'headcount_growth',
                'icon': '📈',
                'ko': f"총 인원 {total_change_val:+.0f}명 증가 ({total_change['percentage']:.1f}% 성장)",
                'en': f"Headcount up {total_change_val:+.0f} employees ({total_change['percentage']:.1f}% growth)",
                'vi': f"Tổng nhân sự tăng {total_change_val:+.0f} NV ({total_change['percentage']:.1f}% tăng trưởng)",
                'details': {
                    'metric': 'total_employees',
                    'current': total_employees,
                    'previous': total_employees - total_change_val,
                    'change': total_change
                }
            })

        # Positive 5: Absence rate decreased
        # 긍정 5: 결근율 감소
        absence_change = self.calculator.get_month_over_month_change('absence_rate_excl_maternity', self.target_month)
        if absence_change and absence_change['absolute'] < -0.5:
            positive_changes.append({
                'id': 'positive_absence',
                'type': 'absence_improved',
                'icon': '✨',
                'ko': f"결근율 {abs(absence_change['absolute']):.1f}%p 감소 ({abs(absence_change['percentage']):.1f}% 개선)",
                'en': f"Absence rate down {abs(absence_change['absolute']):.1f}%p ({abs(absence_change['percentage']):.1f}% improvement)",
                'vi': f"Tỷ lệ vắng giảm {abs(absence_change['absolute']):.1f}%p ({abs(absence_change['percentage']):.1f}% cải thiện)",
                'details': {
                    'metric': 'absence_rate_excl_maternity',
                    'current': absence_rate,
                    'previous': absence_rate - absence_change['absolute'],
                    'change': absence_change
                }
            })

        # Positive 6: Long-term employees increased
        # 긍정 6: 장기근속자 증가
        long_term = metrics.get('long_term_employees', 0)
        long_term_change = self.calculator.get_month_over_month_change('long_term_employees', self.target_month)
        if long_term_change and long_term_change['absolute'] > 0:
            positive_changes.append({
                'id': 'positive_loyalty',
                'type': 'loyalty_improved',
                'icon': '🎖️',
                'ko': f"장기근속자 {long_term_change['absolute']:+.0f}명 증가 (조직 안정성 향상)",
                'en': f"Long-term employees up {long_term_change['absolute']:+.0f} (improved stability)",
                'vi': f"NV lâu năm tăng {long_term_change['absolute']:+.0f} (ổn định hơn)",
                'details': {
                    'metric': 'long_term_employees',
                    'current': long_term,
                    'previous': long_term - long_term_change['absolute'],
                    'change': long_term_change
                }
            })

        # Take top 3 positive changes
        # 상위 3개 긍정적 변화 선택
        top_positive = positive_changes[:3]

        # Build Action Required list
        # Action Required 목록 생성
        actions = []

        # Action: Long-term absence
        # 액션: 장기 결근
        long_absence_count = 0
        for emp in self.employee_details:
            absent_days = emp.get('absent_days', 0)
            if absent_days >= 5:
                long_absence_count += 1
        if long_absence_count > 0:
            actions.append({
                'ko': f'장기결근 (5일+): {long_absence_count}명',
                'en': f'Long absence (5d+): {long_absence_count}',
                'vi': f'Vắng dài (5 ngày+): {long_absence_count}',
                'filter': 'long_absence'
            })

        # Action: Unauthorized absence
        # 액션: 무단결근
        if unauthorized_count > 0:
            actions.append({
                'ko': f'무단결근자: {unauthorized_count}명',
                'en': f'Unauthorized absence: {unauthorized_count}',
                'vi': f'Vắng không phép: {unauthorized_count}',
                'filter': 'unauthorized'
            })

        # Action: Data errors
        # 액션: 데이터 오류
        if data_errors > 0:
            actions.append({
                'ko': f'데이터 오류: {data_errors}건',
                'en': f'Data errors: {data_errors}',
                'vi': f'Lỗi dữ liệu: {data_errors}',
                'filter': 'data_error'
            })

        # Action: TYPE unregistered (use data_errors as proxy)
        # 액션: TYPE 미등록

        # Format month display
        year, month = self.target_month.split('-')

        # ========================================
        # Add issue IDs and store data for modals
        # 이슈 ID 추가 및 모달용 데이터 저장
        # ========================================
        for i, issue in enumerate(top_issues):
            issue['id'] = f'issue_{i}'

        # Store issue and positive data in modal_data for JavaScript access
        # 모달용 JavaScript 접근을 위해 데이터 저장
        quality_info = {
            'score': self.quality_score.score if self.quality_score else 0,
            'grade': self.quality_score.grade if self.quality_score else 'N/A',
            'grade_color': self.quality_score.grade_color if self.quality_score else '#6c757d',
            'passed': self.quality_score.passed_checks if self.quality_score else 0,
            'total': self.quality_score.total_checks if self.quality_score else 0,
            'warning_count': len([w for w in self.quality_score.warnings if w.severity == 'warning']) if self.quality_score else 0,
            'error_count': len([w for w in self.quality_score.warnings if w.severity == 'error']) if self.quality_score else 0
        }
        self.modal_data['executive_summary'] = {
            'issues': top_issues,
            'positive_changes': top_positive,
            'actions': actions,
            'quality': quality_info,
            'metrics': {
                'total_employees': total_employees,
                'absence_rate': absence_rate,  # Excluding maternity / 출산휴가 제외
                'absence_rate_incl': absence_rate_incl,  # Including maternity / 출산휴가 포함
                'resignation_rate': resignation_rate,
                'unauthorized_count': unauthorized_count,
                'perfect_attendance': perfect_attendance,
                'under_60_days': under_60_days,
                'long_term_employees': long_term,
                'data_errors': data_errors
            }
        }

        # Build Clickable Issues HTML
        # 클릭 가능한 이슈 HTML 생성
        issues_html = ''
        if top_issues:
            issues_items = ''.join([
                f'''<div class="issue-item-clickable" onclick="showIssueSummaryModal('issue', {i})" title="클릭하여 상세 정보 보기">
                    <span class="issue-severity">{issue['severity']}</span>
                    <span class="issue-text lang-text" data-ko="{issue['ko']}" data-en="{issue['en']}" data-vi="{issue['vi']}">{issue['ko']}</span>
                    <span class="issue-arrow">→</span>
                </div>'''
                for i, issue in enumerate(top_issues)
            ])
            issues_html = f'''
            <div class="issues-section">
                <div class="section-label lang-text" data-ko="🚨 주의 필요 사항" data-en="🚨 Issues" data-vi="🚨 Vấn đề">🚨 주의 필요 사항</div>
                {issues_items}
            </div>'''
        else:
            issues_html = '''
            <div class="issues-section">
                <div class="section-label lang-text" data-ko="🚨 주의 필요 사항" data-en="🚨 Issues" data-vi="🚨 Vấn đề">🚨 주의 필요 사항</div>
                <div class="issue-item">
                    <span class="issue-severity">✅</span>
                    <span class="issue-text lang-text" data-ko="현재 특이사항 없음" data-en="No significant issues" data-vi="Không có vấn đề đáng kể">현재 특이사항 없음</span>
                </div>
            </div>'''

        # Build Clickable Positive Changes HTML
        # 클릭 가능한 긍정적 변화 HTML 생성
        positive_html = ''
        if top_positive:
            positive_items = ''.join([
                f'''<div class="positive-item-clickable" onclick="showIssueSummaryModal('positive', {i})" title="클릭하여 상세 정보 보기">
                    <span class="positive-severity">{item['icon']}</span>
                    <span class="positive-text lang-text" data-ko="{item['ko']}" data-en="{item['en']}" data-vi="{item['vi']}">{item['ko']}</span>
                    <span class="positive-arrow">→</span>
                </div>'''
                for i, item in enumerate(top_positive)
            ])
            positive_html = f'''
            <div class="positive-section">
                <div class="section-label lang-text" data-ko="✅ 긍정적 변화" data-en="✅ Positive Changes" data-vi="✅ Thay đổi tích cực">✅ 긍정적 변화</div>
                {positive_items}
            </div>'''
        else:
            positive_html = '''
            <div class="positive-section">
                <div class="section-label lang-text" data-ko="✅ 긍정적 변화" data-en="✅ Positive Changes" data-vi="✅ Thay đổi tích cực">✅ 긍정적 변화</div>
                <div class="issue-item">
                    <span class="issue-severity">➖</span>
                    <span class="issue-text lang-text" data-ko="전월 대비 유의미한 변화 없음" data-en="No significant changes from last month" data-vi="Không có thay đổi đáng kể">전월 대비 유의미한 변화 없음</span>
                </div>
            </div>'''

        # Build Actions HTML
        # 액션 HTML 생성
        actions_html = ''
        if actions:
            action_items = ''.join([
                f'''<button class="action-btn" onclick="filterEmployeeDetails('{action['filter']}')">
                    <span class="action-text lang-text" data-ko="{action['ko']}" data-en="{action['en']}" data-vi="{action['vi']}">{action['ko']}</span>
                    <span class="action-arrow">→</span>
                </button>'''
                for action in actions
            ])
            actions_html = f'''
            <div class="actions-section">
                <div class="section-label lang-text" data-ko="⚡ 즉시 조치 필요" data-en="⚡ Action Required" data-vi="⚡ Cần xử lý ngay">⚡ 즉시 조치 필요</div>
                <div class="action-buttons">
                    {action_items}
                </div>
            </div>'''
        else:
            actions_html = '''
            <div class="actions-section">
                <div class="section-label lang-text" data-ko="⚡ 즉시 조치 필요" data-en="⚡ Action Required" data-vi="⚡ Cần xử lý ngay">⚡ 즉시 조치 필요</div>
                <div class="no-actions lang-text" data-ko="현재 조치 필요 항목 없음" data-en="No action items" data-vi="Không có mục cần xử lý">현재 조치 필요 항목 없음</div>
            </div>'''

        # Get quality score info for display
        # 표시용 품질 점수 정보
        qs_score = self.quality_score.score if self.quality_score else 0
        qs_grade = self.quality_score.grade if self.quality_score else 'N/A'
        qs_color = self.quality_score.grade_color if self.quality_score else '#6c757d'
        qs_passed = self.quality_score.passed_checks if self.quality_score else 0
        qs_total = self.quality_score.total_checks if self.quality_score else 0

        return f'''
<!-- Executive Summary Section / 현황 요약 섹션 -->
<div class="executive-summary mb-4">
    <div class="summary-header">
        <h5 class="summary-title lang-text" data-ko="📊 현황 요약" data-en="📊 Executive Summary" data-vi="📊 Tóm tắt">📊 현황 요약</h5>
        <div class="summary-header-right">
            <span class="quality-badge" style="background-color: {qs_color};" title="{qs_passed}/{qs_total} checks passed">
                <span class="quality-grade">{qs_grade}</span>
                <span class="quality-score">{qs_score:.0f}%</span>
            </span>
            <span class="summary-period">{year}.{int(month):02d}</span>
        </div>
    </div>

    <div class="summary-body">
        <!-- Status Indicators / 상태 지표 -->
        <div class="status-grid">
            <div class="status-item status-{total_status_class}">
                <span class="status-icon">{total_status}</span>
                <span class="status-text lang-text"
                    data-ko="총인원: {total_employees}명 (전월 {total_change_sign}{total_change_val})"
                    data-en="Total: {total_employees} (prev {total_change_sign}{total_change_val})"
                    data-vi="Tổng: {total_employees} (trước {total_change_sign}{total_change_val})">
                    총인원: {total_employees}명 (전월 {total_change_sign}{total_change_val})
                </span>
            </div>
            <div class="status-item status-{absence_status_class}">
                <span class="status-icon">{absence_status}</span>
                <span class="status-text lang-text"
                    data-ko="{absence_msg_ko}"
                    data-en="{absence_msg_en}"
                    data-vi="{absence_msg_vi}">
                    {absence_msg_ko}
                </span>
            </div>
            <div class="status-item status-{unauthorized_status_class}">
                <span class="status-icon">{unauthorized_status}</span>
                <span class="status-text lang-text"
                    data-ko="{unauthorized_msg_ko}"
                    data-en="{unauthorized_msg_en}"
                    data-vi="{unauthorized_msg_vi}">
                    {unauthorized_msg_ko}
                </span>
            </div>
        </div>

        <!-- Instant Insights Widget: Key actionable insights at a glance -->
        <!-- 핵심 인사이트 위젯: 한눈에 보는 핵심 실행 정보 -->
        {self._generate_instant_insights()}

        <!-- Team Alert Widget: Top 3 Teams Needing Attention -->
        <!-- 팀 주의 위젯: 주의가 필요한 상위 3개 팀 -->
        {self._generate_team_alert_widget()}

        <!-- Divider -->
        <div class="summary-divider"></div>

        <!-- Three Column Layout: Issues + Positive Changes + Actions -->
        <div class="summary-columns-three">
            {issues_html}
            {positive_html}
            {actions_html}
        </div>
    </div>
</div>
'''

    def _generate_team_alert_widget(self) -> str:
        """
        Generate Team Alert Widget showing top 3 teams needing attention
        주의가 필요한 상위 3개 팀을 보여주는 팀 알림 위젯 생성

        Ranks teams by a composite score based on:
        - Absence rate (weighted 40%)
        - Unauthorized absence rate (weighted 30%)
        - Resignation count (weighted 30%)
        """
        if not self.team_data:
            return ''

        # Calculate composite risk score for each team
        # 각 팀의 복합 위험 점수 계산
        team_scores = []
        for team_name, team_info in self.team_data.items():
            if team_name in ['Unknown', 'unknown', '미지정', '']:
                continue

            absence_rate = team_info.get('absence_rate', 0) or 0
            unauthorized_rate = team_info.get('unauthorized_absence_rate', 0) or 0
            resignations = team_info.get('resignation_count', 0) or 0
            headcount = team_info.get('headcount', 1) or 1

            # Normalize resignation to rate (per 100 employees)
            # 퇴사를 비율로 정규화 (100명당)
            resignation_rate = (resignations / headcount) * 100 if headcount > 0 else 0

            # Composite score (higher = needs more attention)
            # 복합 점수 (높을수록 더 주의 필요)
            risk_score = (absence_rate * 0.4) + (unauthorized_rate * 0.3) + (resignation_rate * 0.3)

            # Determine alert level
            # 알림 수준 결정
            if risk_score >= 15 or unauthorized_rate >= 3:
                alert_level = 'critical'
                alert_icon = '🚨'
            elif risk_score >= 8 or unauthorized_rate >= 1:
                alert_level = 'warning'
                alert_icon = '⚠️'
            else:
                alert_level = 'normal'
                alert_icon = '✅'

            team_scores.append({
                'name': team_name,
                'absence_rate': absence_rate,
                'unauthorized_rate': unauthorized_rate,
                'resignations': resignations,
                'headcount': headcount,
                'risk_score': risk_score,
                'alert_level': alert_level,
                'alert_icon': alert_icon
            })

        # Sort by risk score (highest first) and get top 3
        # 위험 점수로 정렬 (높은 것 먼저) 후 상위 3개 가져오기
        top_teams = sorted(team_scores, key=lambda x: x['risk_score'], reverse=True)[:3]

        # Only show widget if there are teams with warning or critical level
        # 경고 또는 위험 수준의 팀이 있는 경우에만 위젯 표시
        alert_teams = [t for t in top_teams if t['alert_level'] in ['warning', 'critical']]
        if not alert_teams:
            return ''

        # Build team cards HTML
        # 팀 카드 HTML 생성
        team_cards = []
        for team in top_teams:
            bg_class = 'bg-danger-subtle' if team['alert_level'] == 'critical' else 'bg-warning-subtle' if team['alert_level'] == 'warning' else 'bg-light'
            border_class = 'border-danger' if team['alert_level'] == 'critical' else 'border-warning' if team['alert_level'] == 'warning' else ''

            team_cards.append(f'''
            <div class="team-alert-card {bg_class} {border_class}" onclick="switchToTeamAnalysis('{team['name']}')" style="cursor: pointer;" title="Click to view team details">
                <div class="team-alert-header">
                    <span class="team-alert-icon">{team['alert_icon']}</span>
                    <span class="team-alert-name">{team['name']}</span>
                    <span class="team-alert-count">{team['headcount']}명</span>
                </div>
                <div class="team-alert-metrics">
                    <div class="team-alert-metric">
                        <span class="metric-label lang-text" data-ko="결근율" data-en="Absence" data-vi="Vắng">결근율</span>
                        <span class="metric-value" style="color: {'#dc3545' if team['absence_rate'] > 15 else '#ffc107' if team['absence_rate'] > 10 else '#198754'}">{team['absence_rate']:.1f}%</span>
                    </div>
                    <div class="team-alert-metric">
                        <span class="metric-label lang-text" data-ko="무단" data-en="Unauth" data-vi="K.phép">무단</span>
                        <span class="metric-value" style="color: {'#dc3545' if team['unauthorized_rate'] > 2 else '#ffc107' if team['unauthorized_rate'] > 0.5 else '#198754'}">{team['unauthorized_rate']:.1f}%</span>
                    </div>
                    <div class="team-alert-metric">
                        <span class="metric-label lang-text" data-ko="퇴사" data-en="Resign" data-vi="N.việc">퇴사</span>
                        <span class="metric-value">{team['resignations']}명</span>
                    </div>
                </div>
            </div>''')

        return f'''
        <!-- Team Alert Widget / 팀 알림 위젯 -->
        <div class="team-alert-widget">
            <div class="team-alert-title">
                <span class="lang-text" data-ko="🏢 주의 필요 팀" data-en="🏢 Teams Needing Attention" data-vi="🏢 Nhóm cần chú ý">🏢 주의 필요 팀</span>
                <span class="team-alert-subtitle lang-text" data-ko="결근율/무단결근 기준" data-en="Based on absence metrics" data-vi="Dựa trên chỉ số vắng">(결근율/무단결근 기준)</span>
            </div>
            <div class="team-alert-grid">
                {''.join(team_cards)}
            </div>
        </div>
        '''

    def _generate_instant_insights(self) -> str:
        """
        Generate Instant Insights widget showing critical actionable information
        핵심 실행 가능한 정보를 보여주는 즉시 인사이트 위젯 생성
        """
        insights = []

        # Get current month's metrics
        # 현재 월의 메트릭 가져오기
        metrics = self.monthly_metrics.get(self.target_month, {})

        # Calculate key metrics for insights
        # 인사이트를 위한 핵심 메트릭 계산
        total = metrics.get('total_employees', 0)
        resignations = metrics.get('recent_resignations', 0)
        hires = metrics.get('recent_hires', 0)
        absence_rate = metrics.get('absence_rate_excl_maternity', 0) or 0
        unauth_rate = metrics.get('unauthorized_absence_rate', 0) or 0
        under_60 = metrics.get('under_60_days', 0)

        # Insight 1: Net headcount change
        # 인사이트 1: 순 인원 변동
        net_change = hires - resignations
        if net_change > 0:
            insights.append({
                'icon': '📈',
                'title_ko': f'순증 {net_change}명',
                'title_en': f'Net +{net_change}',
                'desc_ko': f'입사 {hires}명 > 퇴사 {resignations}명',
                'desc_en': f'Hired {hires} > Resigned {resignations}',
                'type': 'positive'
            })
        elif net_change < 0:
            insights.append({
                'icon': '📉',
                'title_ko': f'순감 {abs(net_change)}명',
                'title_en': f'Net -{abs(net_change)}',
                'desc_ko': f'퇴사 {resignations}명 > 입사 {hires}명',
                'desc_en': f'Resigned {resignations} > Hired {hires}',
                'type': 'negative'
            })

        # Insight 2: Absence alert
        # 인사이트 2: 결근 경고
        if absence_rate >= 10:
            insights.append({
                'icon': '🚨',
                'title_ko': f'결근율 경고: {absence_rate:.1f}%',
                'title_en': f'Absence Alert: {absence_rate:.1f}%',
                'desc_ko': '즉시 원인 파악 필요',
                'desc_en': 'Immediate investigation needed',
                'type': 'critical'
            })
        elif absence_rate >= 5:
            insights.append({
                'icon': '⚠️',
                'title_ko': f'결근율 주의: {absence_rate:.1f}%',
                'title_en': f'Absence Warning: {absence_rate:.1f}%',
                'desc_ko': '모니터링 강화 권장',
                'desc_en': 'Enhanced monitoring recommended',
                'type': 'warning'
            })

        # Insight 3: Unauthorized absence
        # 인사이트 3: 무단결근
        if unauth_rate >= 1:
            insights.append({
                'icon': '🔴',
                'title_ko': f'무단결근율: {unauth_rate:.1f}%',
                'title_en': f'Unauthorized: {unauth_rate:.1f}%',
                'desc_ko': '징계/상담 대상자 확인 필요',
                'desc_en': 'Review disciplinary cases',
                'type': 'critical'
            })

        # Insight 4: New employee retention focus
        # 인사이트 4: 신입 직원 정착 관리
        if under_60 > 0 and total > 0:
            new_ratio = (under_60 / total) * 100
            if new_ratio >= 10:
                insights.append({
                    'icon': '🌱',
                    'title_ko': f'신입 관리 집중: {under_60}명 ({new_ratio:.0f}%)',
                    'title_en': f'New Hire Focus: {under_60} ({new_ratio:.0f}%)',
                    'desc_ko': '60일 미만 직원 온보딩 강화',
                    'desc_en': 'Strengthen onboarding for <60 days',
                    'type': 'info'
                })

        # Insight 5: Good news - high retention or perfect attendance
        # 인사이트 5: 좋은 소식 - 높은 정착률 또는 만근자
        perfect_attendance = metrics.get('full_attendance', 0) or metrics.get('perfect_attendance', 0)
        if perfect_attendance and total > 0:
            pa_ratio = (perfect_attendance / total) * 100
            if pa_ratio >= 20:
                insights.append({
                    'icon': '🌟',
                    'title_ko': f'만근자 {perfect_attendance}명 ({pa_ratio:.0f}%)',
                    'title_en': f'Perfect Attendance: {perfect_attendance} ({pa_ratio:.0f}%)',
                    'desc_ko': '우수 출근율 직원 인센티브 검토',
                    'desc_en': 'Consider incentives for attendance',
                    'type': 'positive'
                })

        if not insights:
            insights.append({
                'icon': '✅',
                'title_ko': '특이사항 없음',
                'title_en': 'All Normal',
                'desc_ko': '주요 지표 모두 정상 범위',
                'desc_en': 'All metrics within normal range',
                'type': 'positive'
            })

        # Build insight cards HTML
        # 인사이트 카드 HTML 생성
        insight_cards = []
        type_classes = {
            'positive': 'insight-positive',
            'negative': 'insight-negative',
            'critical': 'insight-critical',
            'warning': 'insight-warning',
            'info': 'insight-info'
        }

        for insight in insights[:4]:  # Show max 4 insights
            type_class = type_classes.get(insight['type'], 'insight-info')
            insight_cards.append(f'''
            <div class="instant-insight-card {type_class}">
                <div class="insight-icon">{insight['icon']}</div>
                <div class="insight-content">
                    <div class="insight-title lang-text" data-ko="{insight['title_ko']}" data-en="{insight['title_en']}">{insight['title_ko']}</div>
                    <div class="insight-desc lang-text" data-ko="{insight['desc_ko']}" data-en="{insight['desc_en']}">{insight['desc_ko']}</div>
                </div>
            </div>''')

        return f'''
        <!-- Instant Insights Widget / 즉시 인사이트 위젯 -->
        <div class="instant-insights-widget">
            <div class="instant-insights-header">
                <span class="lang-text" data-ko="💡 핵심 인사이트" data-en="💡 Key Insights" data-vi="💡 Thông tin chính">💡 핵심 인사이트</span>
                <span class="insight-timestamp">{self.report_date}</span>
            </div>
            <div class="instant-insights-grid">
                {''.join(insight_cards)}
            </div>
        </div>
        '''

    def _get_threshold_status(self, key: str, value: float) -> str:
        """
        Determine threshold status for KPI card visualization
        KPI 카드 시각화를 위한 임계값 상태 결정

        Returns: 'critical', 'warning', 'good', 'excellent', or ''
        """
        # Define thresholds for each metric
        # 각 메트릭별 임계값 정의
        thresholds = {
            'absence_rate_excl_maternity': {  # 결근율 (낮을수록 좋음)
                'critical': 15, 'warning': 10, 'good': 5, 'excellent': 3
            },
            'unauthorized_absence_rate': {  # 무단결근율 (낮을수록 좋음)
                'critical': 5, 'warning': 2, 'good': 1, 'excellent': 0.5
            },
            'resignation_rate': {  # 퇴사율 (낮을수록 좋음)
                'critical': 10, 'warning': 5, 'good': 2, 'excellent': 1
            },
            'data_errors': {  # 데이터 오류 (낮을수록 좋음)
                'critical': 10, 'warning': 5, 'good': 1, 'excellent': 0
            },
            'team_absence_avg': {  # 팀별 평균 결근율 (낮을수록 좋음)
                'critical': 15, 'warning': 10, 'good': 5, 'excellent': 3
            },
            'post_assignment_resignations': {  # 배정 후 퇴사 (낮을수록 좋음)
                'critical': 10, 'warning': 5, 'good': 2, 'excellent': 0
            },
            'punctuality_issues': {  # 지각/조퇴 인원 (낮을수록 좋음, 약 5% 기준)
                'critical': 20, 'warning': 12, 'good': 6, 'excellent': 3
            }
        }

        # Inverse metrics where lower is better
        # 낮을수록 좋은 역방향 지표
        if key in thresholds:
            t = thresholds[key]
            if value >= t['critical']:
                return 'status-critical'
            elif value >= t['warning']:
                return 'status-warning'
            elif value >= t['good']:
                return 'status-good'
            elif value <= t['excellent']:
                return 'status-excellent'
            return ''

        # Positive metrics where higher is better (optional thresholds)
        # 높을수록 좋은 정방향 지표 (선택적 임계값)
        positive_thresholds = {
            'perfect_attendance': {  # 개근율 (높을수록 좋음, 총 인원 대비 %)
                'excellent': 30, 'good': 20, 'warning': 10, 'critical': 5
            },
            'long_term_employees': {  # 장기근속자 비율 적용 안함 - 단순 카운트
                'excellent': 250, 'good': 200, 'warning': 150, 'critical': 100
            }
        }

        if key in positive_thresholds:
            t = positive_thresholds[key]
            if value >= t['excellent']:
                return 'status-excellent'
            elif value >= t['good']:
                return 'status-good'
            elif value >= t['warning']:
                return 'status-warning'
            elif value < t['critical']:
                return 'status-critical'

        return ''  # No threshold for this metric

    def _generate_summary_cards(self, metrics: Dict[str, Any]) -> str:
        """Generate summary cards grid with Vietnamese support and threshold visualization"""
        cards = [
            (1, 'total_employees', '총 재직자 수', '명', 'Total Employees', 'Tổng số nhân viên'),
            (2, 'absence_rate_excl_maternity', '결근율 (출산휴가 제외)', '%', 'Absence Rate (excl. Maternity)', 'Tỷ lệ vắng mặt (không bao gồm thai sản)'),
            (3, 'unauthorized_absence_rate', '무단결근율', '%', 'Unauthorized Absence', 'Vắng không phép'),
            (4, 'resignation_rate', '퇴사율', '%', 'Resignation Rate', 'Tỷ lệ nghỉ việc'),
            (5, 'recent_hires', '신규 입사자', '명', 'Recent Hires', 'Nhân viên mới'),
            (6, 'recent_resignations', '최근 퇴사자', '명', 'Recent Resignations', 'Nghỉ việc gần đây'),
            (7, 'under_60_days', '60일 미만 재직자', '명', 'Under 60 Days Tenure', 'Dưới 60 ngày làm việc'),
            (8, 'post_assignment_resignations', '라인 배정 후 퇴사', '명', 'Post-Line Assignment', 'Nghỉ sau phân công'),
            (9, 'perfect_attendance', '개근 직원', '명', 'Perfect Attendance', 'Chuyên cần hoàn hảo'),
            (10, 'long_term_employees', '장기근속자', '명', 'Long-term (1yr+)', 'Lâu năm (1 năm+)'),
            (11, 'data_errors', '데이터 오류', '건', 'Data Errors', 'Lỗi dữ liệu'),
            (12, 'pregnant_employees', '임신 직원', '명', 'Pregnant Employees', 'Nhân viên mang thai'),
            (13, 'team_absence_avg', '팀별 평균 결근율', '%', 'Team Avg Absence', 'Tỷ lệ vắng TB theo nhóm'),
            (14, 'punctuality_issues', '지각/조퇴', '명', 'Come Late / Leave Early', 'Đi muộn / Về sớm')
        ]

        html_parts = ['<div class="row g-3">']

        for num, key, title_ko, unit, title_en, title_vi in cards:
            value = metrics.get(key, 0)
            change = self.calculator.get_month_over_month_change(key, self.target_month)

            change_html = ''
            if change:
                sign = '+' if change['absolute'] >= 0 else ''

                # Inverse metrics: increase is BAD (should show as negative/red)
                # 역방향 지표: 증가가 나쁜 것 (빨간색으로 표시)
                inverse_metrics = {
                    'absence_rate_excl_maternity',  # 결근율 증가 = 나쁨
                    'unauthorized_absence_rate',     # 무단결근율 증가 = 나쁨
                    'resignation_rate',              # 퇴사율 증가 = 나쁨
                    'recent_resignations',           # 퇴사자 증가 = 나쁨
                    'under_60_days',                 # 60일 미만 증가 = 이탈 위험 증가
                    'post_assignment_resignations',  # 배정 후 퇴사 증가 = 나쁨
                    'data_errors',                   # 데이터 오류 증가 = 나쁨
                    'team_absence_avg',              # 팀별 결근율 증가 = 나쁨
                    'punctuality_issues'             # 지각/조퇴 증가 = 나쁨
                }

                # Determine if this is a good or bad change
                # 이 변화가 좋은 것인지 나쁜 것인지 판단
                is_increase = change['absolute'] >= 0
                is_inverse_metric = key in inverse_metrics

                # For inverse metrics: increase is bad (negative class)
                # For normal metrics: increase is good (positive class)
                # 역방향 지표: 증가 = 나쁨 (negative), 일반 지표: 증가 = 좋음 (positive)
                if is_inverse_metric:
                    change_class = 'negative' if is_increase else 'positive'
                    # Arrow direction: for inverse metrics, decrease is good (↓ green), increase is bad (↑ red)
                    # 화살표 방향: 역방향 지표에서 감소는 좋음 (↓ 녹색), 증가는 나쁨 (↑ 빨강)
                    trend_arrow = '↑' if is_increase else '↓'
                else:
                    change_class = 'positive' if is_increase else 'negative'
                    # Arrow direction: for normal metrics, increase is good (↑ green), decrease is bad (↓ red)
                    # 화살표 방향: 일반 지표에서 증가는 좋음 (↑ 녹색), 감소는 나쁨 (↓ 빨강)
                    trend_arrow = '↑' if is_increase else '↓'

                abs_val = round(change["absolute"], 2) if isinstance(change["absolute"], float) else change["absolute"]
                change_html = f'<div class="card-change {change_class}"><span class="trend-arrow">{trend_arrow}</span> {sign}{abs_val} ({sign}{change["percentage"]:.1f}%)</div>'

            # Enhanced KPI card - tooltip shows calculation formula and basis
            # 향상된 KPI 카드 - 툴팁에 계산 공식과 기준 표시

            # Define formulas for each KPI metric
            # 각 KPI 메트릭에 대한 공식 정의
            kpi_formulas = {
                'total_employees': {
                    'ko': "📐 계산: 보고서 생성일 기준 재직자 수",
                    'en': "📐 Formula: Active employees on report date",
                    'vi': "📐 Công thức: Nhân viên đang làm việc vào ngày báo cáo"
                },
                'absence_rate_excl_maternity': {
                    'ko': "📐 계산: (결근일 - 출산휴가) / (전체 근무일 - 출산휴가) × 100",
                    'en': "📐 Formula: (Absence - Maternity) / (Total days - Maternity) × 100",
                    'vi': "📐 Công thức: (Vắng mặt - Thai sản) / (Tổng ngày - Thai sản) × 100"
                },
                'unauthorized_absence_rate': {
                    'ko': "📐 계산: 무단결근일 / 전체 근무일 × 100",
                    'en': "📐 Formula: Unauthorized absence / Total working days × 100",
                    'vi': "📐 Công thức: Vắng không phép / Tổng ngày làm việc × 100"
                },
                'resignation_rate': {
                    'ko': "📐 계산: 월 중 퇴사자 / 월평균 인원 × 100",
                    'en': "📐 Formula: Monthly resignations / Average monthly headcount × 100",
                    'vi': "📐 Công thức: Nghỉ việc trong tháng / Số nhân viên TB tháng × 100"
                },
                'recent_hires': {
                    'ko': "📐 계산: 해당 월에 입사한 직원 수",
                    'en': "📐 Formula: Employees hired in target month",
                    'vi': "📐 Công thức: Nhân viên được tuyển trong tháng"
                },
                'recent_resignations': {
                    'ko': "📐 계산: 해당 월에 퇴사한 직원 수",
                    'en': "📐 Formula: Employees resigned in target month",
                    'vi': "📐 Công thức: Nhân viên nghỉ việc trong tháng"
                },
                'under_60_days': {
                    'ko': "📐 계산: 재직 기간 < 60일인 재직자 수 (이탈 위험군)",
                    'en': "📐 Formula: Active employees with tenure < 60 days (at-risk group)",
                    'vi': "📐 Công thức: NV đang làm việc < 60 ngày (nhóm rủi ro)"
                },
                'post_assignment_resignations': {
                    'ko': "📐 계산: 라인 배정 후 60일 이내 퇴사자 수",
                    'en': "📐 Formula: Resignations within 60 days after line assignment",
                    'vi': "📐 Công thức: Nghỉ việc trong 60 ngày sau phân công dây chuyền"
                },
                'perfect_attendance': {
                    'ko': "📐 계산: 실제 근무일 = 전체 근무일인 직원 수",
                    'en': "📐 Formula: Employees with actual days = total days",
                    'vi': "📐 Công thức: NV có ngày thực tế = tổng ngày"
                },
                'long_term_employees': {
                    'ko': "📐 계산: 재직 기간 ≥ 365일인 재직자 수",
                    'en': "📐 Formula: Active employees with tenure ≥ 365 days",
                    'vi': "📐 Công thức: NV đang làm việc ≥ 365 ngày"
                },
                'data_errors': {
                    'ko': "📐 계산: 데이터 검증 시스템에서 감지된 오류 수",
                    'en': "📐 Formula: Errors detected by validation system",
                    'vi': "📐 Công thức: Lỗi phát hiện bởi hệ thống kiểm tra"
                },
                'team_absence_avg': {
                    'ko': "📐 계산: 모든 팀의 결근율 평균",
                    'en': "📐 Formula: Average of all team absence rates",
                    'vi': "📐 Công thức: TB tỷ lệ vắng mặt của tất cả các nhóm"
                },
                'pregnant_employees': {
                    'ko': "📐 계산: 임신 상태로 등록된 재직자 수",
                    'en': "📐 Formula: Active employees registered as pregnant",
                    'vi': "📐 Công thức: NV đang làm việc đăng ký mang thai"
                },
                'punctuality_issues': {
                    'ko': "📐 계산: 지각 또는 조퇴한 직원 수 (고유 인원)",
                    'en': "📐 Formula: Employees with late arrivals or early departures",
                    'vi': "📐 Công thức: Nhân viên đi muộn hoặc về sớm"
                }
            }

            # Get formula for current KPI
            formula = kpi_formulas.get(key, {'ko': '', 'en': '', 'vi': ''})

            # Build enhanced tooltip with formula
            tooltip_ko = f"💡 현재: {value}{unit}\\n{formula['ko']}"
            tooltip_en = f"💡 Current: {value}{unit}\\n{formula['en']}"
            tooltip_vi = f"💡 Hiện tại: {value}{unit}\\n{formula['vi']}"

            if change:
                prev_value = value - change['absolute']
                tooltip_ko += f"\\n📊 전월 대비: {prev_value:.0f} → {value}"
                tooltip_en += f"\\n📊 vs Previous: {prev_value:.0f} → {value}"
                tooltip_vi += f"\\n📊 So với trước: {prev_value:.0f} → {value}"

            # Determine threshold status for visual indicator
            # 시각적 표시를 위한 임계값 상태 결정
            threshold_status = self._get_threshold_status(key, value)
            status_class = f' {threshold_status}' if threshold_status else ''

            html_parts.append(f"""
<div class="col-md-6 col-lg-4 col-xl-3">
    <div class="summary-card{status_class}" onclick="showModal{num}()" onkeydown="if(event.key==='Enter')showModal{num}()" title="{tooltip_ko}"
         role="button" tabindex="0" aria-label="{title_en}: {value} {unit}" data-status="{threshold_status}">
        <div class="card-number" aria-hidden="true">{num}</div>
        <div class="card-title lang-card-title" data-ko="{title_ko}" data-en="{title_en}" data-vi="{title_vi}">
            {title_ko}<br><small class="lang-card-subtitle" data-ko="{title_en}" data-en="{title_en}" data-vi="{title_vi}">{title_en}</small>
        </div>
        <div class="card-value" aria-live="polite">{value}<small class="ms-2">{unit}</small></div>
        {change_html}
    </div>
</div>
""")

        html_parts.append('</div>')
        return '\n'.join(html_parts)

    def _generate_charts_section(self) -> str:
        """Generate charts section with 2-column grid and period selector"""
        return """
<div class="charts-section" role="region" aria-label="Monthly Trend Charts">
    <!-- Header with Period Selector / 기간 선택기가 있는 헤더 -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h4 class="mb-0 lang-section-title" data-ko="📈 월별 추세 분석" data-en="📈 Monthly Trends" data-vi="📈 Xu hướng hàng tháng">📈 월별 추세 분석</h4>
        <div class="btn-group" role="group" id="periodSelector" aria-label="Select time period">
            <button type="button" class="btn btn-outline-primary btn-sm" data-period="3" onclick="updateTrendPeriod(3)" aria-pressed="false">
                <span class="lang-option" data-ko="3개월" data-en="3 Months" data-vi="3 tháng">3개월</span>
            </button>
            <button type="button" class="btn btn-outline-primary btn-sm active" data-period="6" onclick="updateTrendPeriod(6)" aria-pressed="true">
                <span class="lang-option" data-ko="6개월" data-en="6 Months" data-vi="6 tháng">6개월</span>
            </button>
            <button type="button" class="btn btn-outline-primary btn-sm" data-period="12" onclick="updateTrendPeriod(12)" aria-pressed="false">
                <span class="lang-option" data-ko="12개월" data-en="12 Months" data-vi="12 tháng">12개월</span>
            </button>
        </div>
    </div>

    <!-- Row 1: Employee Trend & Hires/Resignations -->
    <div class="row">
        <div class="col-lg-6">
            <div class="chart-container" role="img" aria-label="Employee trend chart">
                <canvas id="employeeTrendChart" aria-hidden="true"></canvas>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="chart-container" role="img" aria-label="Hires and resignations trend chart">
                <canvas id="hiresResignationsChart" aria-hidden="true"></canvas>
            </div>
        </div>
    </div>

    <!-- Row 2: Resignation Rate & Long-term Employees -->
    <div class="row">
        <div class="col-lg-6">
            <div class="chart-container" role="img" aria-label="Resignation rate trend chart">
                <canvas id="resignationRateChart" aria-hidden="true"></canvas>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="chart-container" role="img" aria-label="Long-term employees trend chart">
                <canvas id="longTermChart" aria-hidden="true"></canvas>
            </div>
        </div>
    </div>

    <!-- Row 3: Unauthorized Absence & Absence Rate -->
    <div class="row">
        <div class="col-lg-6">
            <div class="chart-container" role="img" aria-label="Unauthorized absence trend chart">
                <canvas id="unauthorizedAbsenceChart" aria-hidden="true"></canvas>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="chart-container" role="img" aria-label="Absence rate trend chart">
                <canvas id="absenceRateChart" aria-hidden="true"></canvas>
            </div>
        </div>
    </div>
</div>
"""

    def _generate_hierarchy_visualization_section(self) -> str:
        """Generate hierarchy visualization section with 3 chart options"""
        return """
<div class="hierarchy-section mt-5">
    <h4 class="mb-4 lang-section-title" data-ko="👥 직급별 인원 분포" data-en="👥 Position Distribution" data-vi="👥 Phân bổ theo chức vụ">👥 직급별 인원 분포</h4>

    <!-- Chart Type Selector -->
    <ul class="nav nav-pills mb-3" id="hierarchyChartTabs" role="tablist">
        <li class="nav-item" role="presentation">
            <button class="nav-link active" id="bar-chart-tab" data-bs-toggle="pill" data-bs-target="#barChartView"
                    type="button" role="tab" aria-controls="barChartView" aria-selected="true">
                <span class="lang-option" data-ko="📊 막대 차트" data-en="📊 Bar Chart" data-vi="📊 Biểu đồ cột">📊 막대 차트</span>
            </button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link" id="sunburst-chart-tab" data-bs-toggle="pill" data-bs-target="#sunburstChartView"
                    type="button" role="tab" aria-controls="sunburstChartView" aria-selected="false">
                <span class="lang-option" data-ko="🌅 선버스트 차트" data-en="🌅 Sunburst Chart" data-vi="🌅 Biểu đồ Sunburst">🌅 선버스트 차트</span>
            </button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link" id="donut-chart-tab" data-bs-toggle="pill" data-bs-target="#donutChartView"
                    type="button" role="tab" aria-controls="donutChartView" aria-selected="false">
                <span class="lang-option" data-ko="🍩 도넛 차트" data-en="🍩 Donut Chart" data-vi="🍩 Biểu đồ Donut">🍩 도넛 차트</span>
            </button>
        </li>
    </ul>

    <!-- Chart Views -->
    <div class="tab-content" id="hierarchyChartContent">
        <!-- Bar Chart View -->
        <div class="tab-pane fade show active" id="barChartView" role="tabpanel" aria-labelledby="bar-chart-tab">
            <div class="chart-container" style="height: 400px;">
                <canvas id="hierarchyBarChart"></canvas>
            </div>
        </div>

        <!-- Sunburst Chart View -->
        <div class="tab-pane fade" id="sunburstChartView" role="tabpanel" aria-labelledby="sunburst-chart-tab">
            <div class="chart-container" style="height: 500px;">
                <div id="hierarchySunburstChart"></div>
            </div>
        </div>

        <!-- Donut Chart View -->
        <div class="tab-pane fade" id="donutChartView" role="tabpanel" aria-labelledby="donut-chart-tab">
            <div class="row">
                <div class="col-md-6">
                    <div class="chart-container" style="height: 400px;">
                        <canvas id="hierarchyDonutChart1"></canvas>
                        <div class="text-center mt-2">
                            <small class="lang-text" data-ko="1차 직급 분포" data-en="Primary Position" data-vi="Chức vụ chính">1차 직급 분포</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="chart-container" style="height: 400px;">
                        <canvas id="hierarchyDonutChart2"></canvas>
                        <div class="text-center mt-2">
                            <small class="lang-text" data-ko="2차 팀 분포" data-en="Team Distribution" data-vi="Phân bổ nhóm">2차 팀 분포</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Team Summary Cards -->
    <div class="mt-5">
        <h5 class="mb-3 lang-section-title" data-ko="📊 팀별 현황 요약" data-en="📊 Team Summary" data-vi="📊 Tóm tắt nhóm">📊 팀별 현황 요약</h5>
        <div class="row g-3" id="teamSummaryCards">
            <!-- Populated by JavaScript -->
        </div>
    </div>
</div>
"""

    def _generate_details_tab(self) -> str:
        """Generate employee details table with filters"""
        return """
<div class="details-section">
    <h4 class="mb-4 lang-section-title" data-ko="👥 직원 상세 정보" data-en="👥 Employee Details" data-vi="👥 Chi tiết nhân viên">👥 직원 상세 정보</h4>

    <!-- Quick Statistics Panel - Enhanced with icons and clear layout -->
    <!-- 빠른 통계 패널 - 아이콘과 명확한 레이아웃 개선 -->
    <div class="row g-3 mb-4" id="quickStatsPanel">
        <div class="col-6 col-md-3">
            <div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div class="stat-icon">👥</div>
                <div class="stat-content">
                    <div class="stat-value" id="statsShowing">0</div>
                    <div class="stat-label">
                        <span class="lang-stat" data-ko="표시 인원" data-en="Showing" data-vi="Đang hiển thị">표시 인원</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-6 col-md-3">
            <div class="stat-card" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
                <div class="stat-icon">✅</div>
                <div class="stat-content">
                    <div class="stat-value" id="statsActiveResigned">0/0</div>
                    <div class="stat-label">
                        <span class="lang-stat" data-ko="재직/퇴사" data-en="Active/Resigned" data-vi="Làm/Nghỉ">재직/퇴사</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-6 col-md-3">
            <div class="stat-card" style="background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);">
                <div class="stat-icon">📅</div>
                <div class="stat-content">
                    <div class="stat-value" id="statsAbsentCount">0</div>
                    <div class="stat-label">
                        <span class="lang-stat" data-ko="이번 달 결근" data-en="Absent (Month)" data-vi="Vắng (Tháng)">이번 달 결근</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-6 col-md-3">
            <div class="stat-card stat-card-danger" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">
                <div class="stat-icon">⚠️</div>
                <div class="stat-content">
                    <div class="stat-value" id="statsUnauthorizedCount">0</div>
                    <div class="stat-label">
                        <span class="lang-stat" data-ko="무단결근자" data-en="Unauthorized" data-vi="Không phép">무단결근자</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Team Filter and Controls -->
    <div class="row mb-3">
        <div class="col-md-3">
            <label for="teamFilter" class="visually-hidden">Select team filter</label>
            <select class="form-select" id="teamFilter" onchange="applyFilters()" aria-label="Filter by team">
                <option value="all">
                    <span class="lang-option" data-ko="전체 팀" data-en="All Teams" data-vi="Tất cả nhóm">전체 팀</span>
                </option>
            </select>
        </div>
        <div class="col-md-6">
            <div class="position-relative" role="search">
                <label for="employeeSearch" class="visually-hidden">Search employees</label>
                <div class="input-group">
                    <input type="search" class="form-control" id="employeeSearch"
                           placeholder="🔍 사번, 이름, 직급, 건물, 라인, 상사로 검색..."
                           onkeyup="handleSearchInput()"
                           aria-label="Search employees by ID, name, position, building, line, or boss"
                           aria-describedby="searchSuggestions searchResultCount"
                           autocomplete="off"
                           data-ko="🔍 사번, 이름, 직급, 건물, 라인, 상사로 검색..."
                           data-en="🔍 Search by ID, Name, Position, Building, Line, Boss..."
                           data-vi="🔍 Tìm theo ID, Tên, Vị trí, Tòa, Dây, Cấp trên...">
                    <button class="btn btn-outline-secondary" type="button" id="clearSearchBtn"
                            onclick="clearSearch()"
                            aria-label="Clear search"
                            style="display: none;"
                            data-ko="지우기" data-en="Clear" data-vi="Xóa">×</button>
                </div>
                <div id="searchSuggestions" class="search-suggestions" role="listbox" aria-live="polite" style="display: none;"></div>
                <span id="searchResultCount" class="visually-hidden" role="status" aria-live="polite"></span>
            </div>
        </div>
        <div class="col-md-3 text-end">
            <div class="dropdown d-inline-block">
                <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" id="columnToggleBtn" data-bs-toggle="dropdown" aria-expanded="false">
                    <span class="d-none d-md-inline lang-btn" data-ko="📊 열 표시" data-en="📊 Columns" data-vi="📊 Cột">📊 열 표시</span>
                    <span class="d-md-none">📊</span>
                </button>
                <div class="dropdown-menu column-toggle-menu" id="columnToggleMenu">
                    <!-- Quick Actions / 빠른 작업 -->
                    <div class="column-toggle-actions">
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="toggleAllColumns(true)" title="Select All">
                            <span class="lang-btn" data-ko="전체" data-en="All" data-vi="Tất cả">전체</span>
                        </button>
                        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="toggleAllColumns(false)" title="Deselect All">
                            <span class="lang-btn" data-ko="해제" data-en="None" data-vi="Bỏ">해제</span>
                        </button>
                        <button type="button" class="btn btn-outline-success btn-sm" onclick="resetColumnVisibility()" title="Reset to Default">
                            <span class="lang-btn" data-ko="기본값" data-en="Reset" data-vi="Mặc định">기본값</span>
                        </button>
                    </div>

                    <!-- Category: Basic Info / 기본정보 -->
                    <div class="column-category">
                        <div class="category-header">
                            <span class="lang-label" data-ko="👤 기본정보" data-en="👤 Basic Info" data-vi="👤 Thông tin cơ bản">👤 기본정보</span>
                        </div>
                        <label class="column-item"><input type="checkbox" checked data-column="0" onchange="toggleColumn(0)"><span class="column-icon">🔢</span><span class="column-name lang-label" data-ko="사번" data-en="ID" data-vi="Mã">사번</span></label>
                        <label class="column-item"><input type="checkbox" checked data-column="1" onchange="toggleColumn(1)"><span class="column-icon">👤</span><span class="column-name lang-label" data-ko="이름" data-en="Name" data-vi="Tên">이름</span></label>
                        <label class="column-item"><input type="checkbox" checked data-column="2" onchange="toggleColumn(2)"><span class="column-icon">📊</span><span class="column-name lang-label" data-ko="직급" data-en="Position" data-vi="Vị trí">직급</span></label>
                        <label class="column-item"><input type="checkbox" checked data-column="3" onchange="toggleColumn(3)"><span class="column-icon">🏷️</span><span class="column-name lang-label" data-ko="유형" data-en="Type" data-vi="Loại">유형</span></label>
                    </div>

                    <!-- Category: Work Info / 근무정보 (hidden by default for cleaner view) -->
                    <div class="column-category">
                        <div class="category-header">
                            <span class="lang-label" data-ko="🏢 근무정보" data-en="🏢 Work Info" data-vi="🏢 Thông tin công việc">🏢 근무정보</span>
                            <small class="text-muted ms-1">(선택)</small>
                        </div>
                        <label class="column-item"><input type="checkbox" data-column="4" onchange="toggleColumn(4)"><span class="column-icon">🏢</span><span class="column-name lang-label" data-ko="건물" data-en="Building" data-vi="Tòa">건물</span></label>
                        <label class="column-item"><input type="checkbox" data-column="5" onchange="toggleColumn(5)"><span class="column-icon">📍</span><span class="column-name lang-label" data-ko="라인" data-en="Line" data-vi="Dây">라인</span></label>
                        <label class="column-item"><input type="checkbox" data-column="6" onchange="toggleColumn(6)"><span class="column-icon">👔</span><span class="column-name lang-label" data-ko="상사" data-en="Boss" data-vi="Cấp trên">상사</span></label>
                    </div>

                    <!-- Category: Attendance Info / 출결정보 (핵심 HR 정보) -->
                    <div class="column-category">
                        <div class="category-header">
                            <span class="lang-label" data-ko="📊 출결정보" data-en="📊 Attendance" data-vi="📊 Chấm công">📊 출결정보</span>
                            <small class="text-success ms-1">★</small>
                        </div>
                        <label class="column-item"><input type="checkbox" checked data-column="7" onchange="toggleColumn(7)"><span class="column-icon">📅</span><span class="column-name lang-label" data-ko="근무일" data-en="Work Days" data-vi="Ngày làm">근무일</span></label>
                        <label class="column-item"><input type="checkbox" checked data-column="8" onchange="toggleColumn(8)"><span class="column-icon">❌</span><span class="column-name lang-label" data-ko="결근" data-en="Absent" data-vi="Vắng">결근</span></label>
                        <label class="column-item"><input type="checkbox" checked data-column="9" onchange="toggleColumn(9)"><span class="column-icon">⚠️</span><span class="column-name lang-label" data-ko="무단" data-en="Unauth" data-vi="K.phép">무단</span></label>
                    </div>

                    <!-- Category: Date Info / 날짜정보 -->
                    <div class="column-category">
                        <div class="category-header">
                            <span class="lang-label" data-ko="📅 날짜정보" data-en="📅 Date Info" data-vi="📅 Thông tin ngày">📅 날짜정보</span>
                        </div>
                        <label class="column-item"><input type="checkbox" checked data-column="10" onchange="toggleColumn(10)"><span class="column-icon">📥</span><span class="column-name lang-label" data-ko="입사일" data-en="Start Date" data-vi="Ngày vào">입사일</span></label>
                        <label class="column-item"><input type="checkbox" data-column="11" onchange="toggleColumn(11)"><span class="column-icon">📤</span><span class="column-name lang-label" data-ko="퇴사일" data-en="End Date" data-vi="Ngày nghỉ">퇴사일</span></label>
                        <label class="column-item"><input type="checkbox" checked data-column="12" onchange="toggleColumn(12)"><span class="column-icon">⏱️</span><span class="column-name lang-label" data-ko="재직기간" data-en="Tenure" data-vi="Thâm niên">재직기간</span></label>
                        <label class="column-item"><input type="checkbox" checked data-column="13" onchange="toggleColumn(13)"><span class="column-icon">🔵</span><span class="column-name lang-label" data-ko="상태" data-en="Status" data-vi="Trạng thái">상태</span></label>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Redesigned Filter System / 재설계된 필터 시스템 -->
    <div class="filter-system mb-4">
        <!-- Active Filters Display / 활성 필터 표시 -->
        <div class="active-filters-bar mb-3 d-none" id="activeFiltersBar">
            <div class="d-flex align-items-center flex-wrap gap-2">
                <span class="text-muted small me-2">
                    <span class="lang-text" data-ko="적용된 필터:" data-en="Active filters:" data-vi="Bộ lọc đang áp dụng:">적용된 필터:</span>
                </span>
                <div id="activeFilterChips" class="d-flex flex-wrap gap-1"></div>
                <button class="btn btn-sm btn-outline-secondary ms-2" onclick="resetAllFilters()" title="Reset all filters">
                    <span class="lang-text" data-ko="🔄 초기화" data-en="🔄 Reset" data-vi="🔄 Đặt lại">🔄 초기화</span>
                </button>
            </div>
        </div>

        <!-- Filter Cards / 필터 카드 -->
        <div class="row g-3">
            <!-- Employment Status Group / 고용 상태 그룹 -->
            <div class="col-md-6 col-lg-3">
                <div class="filter-group-card card h-100">
                    <div class="card-header py-2 bg-primary bg-opacity-10">
                        <h6 class="mb-0 text-primary">
                            <span class="me-1">👥</span>
                            <span class="lang-text" data-ko="고용 상태" data-en="Employment" data-vi="Tình trạng">고용 상태</span>
                        </h6>
                    </div>
                    <div class="card-body py-2">
                        <div class="d-flex flex-wrap gap-1">
                            <button type="button" class="btn btn-sm filter-chip active" id="filterAll" onclick="filterEmployees('all')" data-filter="all">
                                <span class="filter-icon">📋</span>
                                <span class="lang-filter" data-ko="전체" data-en="All" data-vi="Tất cả">전체</span>
                                <span class="badge rounded-pill" id="countAll">0</span>
                            </button>
                            <button type="button" class="btn btn-sm filter-chip" id="filterActive" onclick="filterEmployees('active')" data-filter="active">
                                <span class="filter-icon">✅</span>
                                <span class="lang-filter" data-ko="재직" data-en="Active" data-vi="Đang làm">재직</span>
                                <span class="badge rounded-pill" id="countActive">0</span>
                            </button>
                            <button type="button" class="btn btn-sm filter-chip" id="filterHired" onclick="filterEmployees('hired')" data-filter="hired">
                                <span class="filter-icon">🆕</span>
                                <span class="lang-filter" data-ko="신규" data-en="New" data-vi="Mới">신규</span>
                                <span class="badge rounded-pill" id="countHired">0</span>
                            </button>
                            <button type="button" class="btn btn-sm filter-chip" id="filterResigned" onclick="filterEmployees('resigned')" data-filter="resigned">
                                <span class="filter-icon">📤</span>
                                <span class="lang-filter" data-ko="퇴사" data-en="Left" data-vi="Đã nghỉ">퇴사</span>
                                <span class="badge rounded-pill" id="countResigned">0</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Attendance Group / 근태 그룹 -->
            <div class="col-md-6 col-lg-3">
                <div class="filter-group-card card h-100">
                    <div class="card-header py-2 bg-success bg-opacity-10">
                        <h6 class="mb-0 text-success">
                            <span class="me-1">📊</span>
                            <span class="lang-text" data-ko="근태 현황" data-en="Attendance" data-vi="Chấm công">근태 현황</span>
                        </h6>
                    </div>
                    <div class="card-body py-2">
                        <div class="d-flex flex-wrap gap-1">
                            <button type="button" class="btn btn-sm filter-chip" id="filterPerfect" onclick="filterEmployees('perfect')" data-filter="perfect">
                                <span class="filter-icon">🌟</span>
                                <span class="lang-filter" data-ko="개근" data-en="Perfect" data-vi="Đầy đủ">개근</span>
                                <span class="badge rounded-pill" id="countPerfect">0</span>
                            </button>
                            <button type="button" class="btn btn-sm filter-chip" id="filterAbsent" onclick="filterEmployees('absent')" data-filter="absent">
                                <span class="filter-icon">⚠️</span>
                                <span class="lang-filter" data-ko="결근" data-en="Absent" data-vi="Vắng">결근</span>
                                <span class="badge rounded-pill" id="countAbsent">0</span>
                            </button>
                            <button type="button" class="btn btn-sm filter-chip filter-chip-danger" id="filterUnauthorized" onclick="filterEmployees('unauthorized')" data-filter="unauthorized">
                                <span class="filter-icon">🚨</span>
                                <span class="lang-filter" data-ko="무단" data-en="Unauth" data-vi="K.phép">무단</span>
                                <span class="badge rounded-pill" id="countUnauthorized">0</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tenure Group / 근속 그룹 -->
            <div class="col-md-6 col-lg-3">
                <div class="filter-group-card card h-100">
                    <div class="card-header py-2 bg-info bg-opacity-10">
                        <h6 class="mb-0 text-info">
                            <span class="me-1">📅</span>
                            <span class="lang-text" data-ko="근속 기간" data-en="Tenure" data-vi="Thâm niên">근속 기간</span>
                        </h6>
                    </div>
                    <div class="card-body py-2">
                        <div class="d-flex flex-wrap gap-1">
                            <button type="button" class="btn btn-sm filter-chip" id="filterLongTerm" onclick="filterEmployees('longterm')" data-filter="longterm">
                                <span class="filter-icon">🏆</span>
                                <span class="lang-filter" data-ko="장기" data-en="1yr+" data-vi="Lâu năm">장기</span>
                                <span class="badge rounded-pill" id="countLongTerm">0</span>
                            </button>
                            <button type="button" class="btn btn-sm filter-chip" id="filterNew" onclick="filterEmployees('new60')" data-filter="new60">
                                <span class="filter-icon">🌱</span>
                                <span class="lang-filter" data-ko="60일↓" data-en="<60d" data-vi="<60 ngày">60일↓</span>
                                <span class="badge rounded-pill" id="countNew60">0</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Special Group / 특수 그룹 -->
            <div class="col-md-6 col-lg-3">
                <div class="filter-group-card card h-100">
                    <div class="card-header py-2 bg-warning bg-opacity-10">
                        <h6 class="mb-0 text-warning">
                            <span class="me-1">⭐</span>
                            <span class="lang-text" data-ko="특수 관리" data-en="Special" data-vi="Đặc biệt">특수 관리</span>
                        </h6>
                    </div>
                    <div class="card-body py-2">
                        <div class="d-flex flex-wrap gap-1">
                            <button type="button" class="btn btn-sm filter-chip" id="filterPregnant" onclick="filterEmployees('pregnant')" data-filter="pregnant">
                                <span class="filter-icon">🤰</span>
                                <span class="lang-filter" data-ko="임신" data-en="Pregnant" data-vi="Thai sản">임신</span>
                                <span class="badge rounded-pill" id="countPregnant">0</span>
                            </button>
                            <button type="button" class="btn btn-sm filter-chip" id="filterTurnoverRisk" onclick="filterEmployees('turnover_risk')" data-filter="turnover_risk">
                                <span class="filter-icon">⚡</span>
                                <span class="lang-filter" data-ko="이탈위험" data-en="At Risk" data-vi="Nguy cơ">이탈위험</span>
                                <span class="badge rounded-pill" id="countTurnoverRisk">0</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bulk Actions and Export Buttons -->
    <div class="row mb-3 align-items-center">
        <div class="col-md-6">
            <div class="bulk-actions-group">
                <label class="btn btn-sm btn-outline-secondary" title="Select All">
                    <input type="checkbox" id="selectAllCheckbox" onchange="toggleSelectAll()" autocomplete="off">
                    <span class="btn-icon">☑️</span>
                    <span class="btn-text lang-btn" data-ko="전체 선택" data-en="Select All" data-vi="Chọn tất">전체 선택</span>
                </label>
                <button type="button" class="btn btn-sm btn-outline-success" id="exportSelectedBtn" onclick="exportSelected('csv')" disabled title="Export Selected">
                    <span class="btn-icon">📥</span>
                    <span class="btn-text lang-btn" data-ko="선택 내보내기" data-en="Export Selected" data-vi="Xuất đã chọn">선택 내보내기</span>
                </button>
                <button type="button" class="btn btn-sm btn-outline-primary" id="printSelectedBtn" onclick="printSelected()" disabled title="Print Selected">
                    <span class="btn-icon">🖨️</span>
                    <span class="btn-text lang-btn" data-ko="선택 인쇄" data-en="Print Selected" data-vi="In đã chọn">선택 인쇄</span>
                </button>
                <span class="badge bg-secondary" id="selectedCount">
                    <span class="lang-label" data-ko="0 선택됨" data-en="0 selected" data-vi="Đã chọn 0">0 선택됨</span>
                </span>
            </div>
        </div>
        <div class="col-md-6 text-end">
            <!-- Export Dropdown with Filtered/All Options / 필터/전체 옵션이 있는 내보내기 드롭다운 -->
            <div class="dropdown d-inline-block me-2">
                <button class="btn btn-sm btn-outline-success dropdown-toggle" type="button" id="exportDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                    📥 <span class="lang-btn" data-ko="내보내기" data-en="Export" data-vi="Xuất">내보내기</span>
                </button>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="exportDropdown">
                    <li><h6 class="dropdown-header lang-text" data-ko="📋 현재 필터 적용" data-en="📋 Filtered Data" data-vi="📋 Dữ liệu đã lọc">📋 현재 필터 적용</h6></li>
                    <li><a class="dropdown-item" href="#" onclick="exportFiltered('csv'); return false;">
                        <span class="text-success">CSV</span> - <span class="lang-text" data-ko="필터링된 데이터" data-en="Filtered Data" data-vi="Dữ liệu đã lọc">필터링된 데이터</span>
                        <span class="badge bg-secondary ms-2" id="filteredCountBadge">0</span>
                    </a></li>
                    <li><a class="dropdown-item" href="#" onclick="exportFiltered('json'); return false;">
                        <span class="text-primary">JSON</span> - <span class="lang-text" data-ko="필터링된 데이터" data-en="Filtered Data" data-vi="Dữ liệu đã lọc">필터링된 데이터</span>
                    </a></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><h6 class="dropdown-header lang-text" data-ko="📁 전체 데이터" data-en="📁 All Data" data-vi="📁 Tất cả dữ liệu">📁 전체 데이터</h6></li>
                    <li><a class="dropdown-item" href="#" onclick="exportToCSV(); return false;">
                        <span class="text-success">CSV</span> - <span class="lang-text" data-ko="전체 직원" data-en="All Employees" data-vi="Tất cả nhân viên">전체 직원</span>
                        <span class="badge bg-info ms-2" id="totalCountBadge">0</span>
                    </a></li>
                    <li><a class="dropdown-item" href="#" onclick="exportToJSON(); return false;">
                        <span class="text-primary">JSON</span> - <span class="lang-text" data-ko="전체 직원" data-en="All Employees" data-vi="Tất cả nhân viên">전체 직원</span>
                    </a></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item" href="#" onclick="exportMetricsToJSON(); return false;">
                        <span class="text-warning">📊</span> <span class="lang-text" data-ko="KPI 메트릭" data-en="KPI Metrics" data-vi="Chỉ số KPI">KPI 메트릭</span>
                    </a></li>
                </ul>
            </div>
            <!-- Pagination Controls -->
            <nav aria-label="Employee table pagination" class="d-inline-block">
                <div class="btn-group me-2" role="group">
                    <button type="button" class="btn btn-sm btn-outline-secondary" id="prevPageBtn" onclick="changePage(-1)" aria-label="Previous page">◄</button>
                    <span class="btn btn-sm btn-outline-secondary disabled" id="pageInfo" aria-live="polite" aria-atomic="true">Page 1</span>
                    <button type="button" class="btn btn-sm btn-outline-secondary" id="nextPageBtn" onclick="changePage(1)" aria-label="Next page">►</button>
                </div>
            </nav>
            <label for="pageSizeSelect" class="visually-hidden">Select page size</label>
            <select class="form-select form-select-sm d-inline-block me-2" id="pageSizeSelect" onchange="changePageSize()" style="width: auto;" aria-label="Number of employees per page">
                <option value="20">20/page</option>
                <option value="50" selected>50/page</option>
                <option value="100">100/page</option>
                <option value="-1">All</option>
            </select>
            <span class="badge bg-info fs-6" id="employeeCount" aria-live="polite">Total: 0</span>
        </div>
    </div>

    <!-- Employee Table -->
    <div class="table-responsive" role="region" aria-label="Employee data table" tabindex="0">
        <table class="table table-striped table-hover employee-table" id="employeeTable" aria-label="Employee list with attendance and status information">
            <thead class="table-light sticky-top">
                <tr>
                    <th scope="col" style="width: 40px;"><input type="checkbox" id="headerCheckbox" onchange="toggleSelectAll()" aria-label="Select all employees"></th>
                    <th scope="col" class="sortable" onclick="sortTable(0, event)" id="th-0" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="사번" data-en="ID" data-vi="Mã NV">사번</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(1, event)" id="th-1" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="이름" data-en="Name" data-vi="Tên">이름</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(2, event)" id="th-2" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="직급" data-en="Position" data-vi="Vị trí">직급</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(3, event)" id="th-3" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="유형" data-en="Type" data-vi="Loại">유형</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(4, event)" id="th-4" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="건물" data-en="Building" data-vi="Tòa nhà">건물</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(5, event)" id="th-5" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="라인" data-en="Line" data-vi="Dây chuyền">라인</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(6, event)" id="th-6" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="상사" data-en="Boss" data-vi="Cấp trên">상사</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(7, event)" id="th-7" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="근무일" data-en="Work" data-vi="Làm việc">근무일</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(8, event)" id="th-8" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="결근" data-en="Absent" data-vi="Vắng">결근</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(9, event)" id="th-9" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="무단" data-en="Unauth" data-vi="K.phép">무단</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(10, event)" id="th-10" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="입사일" data-en="Start" data-vi="Ngày vào">입사일</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(11, event)" id="th-11" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="퇴사일" data-en="End" data-vi="Ngày nghỉ">퇴사일</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col" class="sortable" onclick="sortTable(12, event)" id="th-12" aria-sort="none" title="Shift+클릭: 2차 정렬"><span class="lang-th" data-ko="재직" data-en="Tenure" data-vi="Thâm niên">재직</span> <span class="sort-indicator" aria-hidden="true"></span></th>
                    <th scope="col"><span class="lang-th" data-ko="상태" data-en="Status" data-vi="Trạng thái">상태</span></th>
                </tr>
            </thead>
            <tbody id="employeeTableBody">
                <!-- Populated by JavaScript -->
            </tbody>
        </table>
    </div>
</div>
"""

    def _generate_orgchart_tab(self) -> str:
        """Generate organization chart tab with hierarchical structure"""
        return """
<div class="orgchart-section">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h4 class="lang-section-title" data-ko="🌳 조직 구조" data-en="🌳 Organization Structure" data-vi="🌳 Cơ cấu tổ chức">
            🌳 조직 구조
        </h4>
        <div class="btn-group" role="group">
            <button type="button" class="btn btn-sm btn-outline-primary active" onclick="setOrgChartView('network')" id="viewNetwork">
                <span class="lang-btn" data-ko="🕸️ 네트워크" data-en="🕸️ Network" data-vi="🕸️ Mạng">🕸️ 네트워크</span>
            </button>
            <button type="button" class="btn btn-sm btn-outline-info" onclick="setOrgChartView('hierarchy')" id="viewHierarchy">
                <span class="lang-btn" data-ko="📊 계층도" data-en="📊 Hierarchy" data-vi="📊 Phân cấp">📊 계층도</span>
            </button>
            <button type="button" class="btn btn-sm btn-outline-success" onclick="setOrgChartView('stats')" id="viewStats">
                <span class="lang-btn" data-ko="📈 통계" data-en="📈 Statistics" data-vi="📈 Thống kê">📈 통계</span>
            </button>
        </div>
    </div>

    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card bg-gradient" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <div class="card-body text-center">
                    <h6 class="mb-2 lang-text" data-ko="총 직급 수" data-en="Total Positions" data-vi="Tổng chức vụ">총 직급 수</h6>
                    <h2 class="mb-0" id="totalPositionsCount">0</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-gradient" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white;">
                <div class="card-body text-center">
                    <h6 class="mb-2 lang-text" data-ko="총 부서 수" data-en="Total Departments" data-vi="Tổng phòng ban">총 부서 수</h6>
                    <h2 class="mb-0" id="totalDepartmentsCount">0</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-gradient" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white;">
                <div class="card-body text-center">
                    <h6 class="mb-2 lang-text" data-ko="관리자 수" data-en="Managers" data-vi="Quản lý">관리자 수</h6>
                    <h2 class="mb-0" id="totalManagersCount">0</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-gradient" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white;">
                <div class="card-body text-center">
                    <h6 class="mb-2 lang-text" data-ko="평균 팀 크기" data-en="Avg Team Size" data-vi="Kích thước nhóm TB">평균 팀 크기</h6>
                    <h2 class="mb-0" id="avgTeamSize">0</h2>
                </div>
            </div>
        </div>
    </div>

    <!-- Organization Chart Network View -->
    <div id="orgChartNetwork" class="org-network-container">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0 lang-text" data-ko="조직 네트워크 뷰" data-en="Organization Network View" data-vi="Xem mạng tổ chức">조직 네트워크 뷰</h6>
                <div>
                    <select class="form-select form-select-sm" id="orgNetworkFilter" onchange="filterOrgNetwork()">
                        <option value="all" selected>전체 표시</option>
                        <option value="managers">관리자만</option>
                        <option value="dept">부서별</option>
                    </select>
                </div>
            </div>
            <div class="card-body">
                <div id="orgNetworkChart" style="height: 600px; position: relative;">
                    <!-- D3.js Network Graph -->
                </div>
            </div>
        </div>
    </div>

    <!-- Organization Chart Hierarchy View -->
    <div id="orgChartHierarchy" class="org-hierarchy-container" style="display: none;">
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0 lang-text" data-ko="조직 계층 구조" data-en="Organization Hierarchy" data-vi="Hệ thống phân cấp">조직 계층 구조</h6>
            </div>
            <div class="card-body">
                <div id="orgHierarchyTree" style="min-height: 500px;">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
        </div>
    </div>

    <!-- Organization Chart Statistics View -->
    <div id="orgChartStats" class="org-stats-container" style="display: none;">
        <div class="row">
            <div class="col-lg-6 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="mb-0 lang-text" data-ko="직급별 인원 분포" data-en="Position Distribution" data-vi="Phân bổ chức vụ">직급별 인원 분포</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="positionDistChart" height="300"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-lg-6 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="mb-0 lang-text" data-ko="부서별 인원" data-en="Department Headcount" data-vi="Nhân sự phòng ban">부서별 인원</h6>
                    </div>
                    <div class="card-body">
                        <canvas id="deptHeadcountChart" height="300"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-12 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0 lang-text" data-ko="관리자 상세 정보" data-en="Manager Details" data-vi="Chi tiết quản lý">관리자 상세 정보</h6>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover" id="managersTable">
                                <thead class="table-light">
                                    <tr>
                                        <th class="lang-text" data-ko="사번" data-en="ID" data-vi="Mã">사번</th>
                                        <th class="lang-text" data-ko="이름" data-en="Name" data-vi="Tên">이름</th>
                                        <th class="lang-text" data-ko="직급" data-en="Position" data-vi="Chức vụ">직급</th>
                                        <th class="lang-text" data-ko="부서" data-en="Department" data-vi="Phòng ban">부서</th>
                                        <th class="lang-text" data-ko="팀원 수" data-en="Team Size" data-vi="Số thành viên">팀원 수</th>
                                        <th class="lang-text" data-ko="근속 기간" data-en="Tenure" data-vi="Thâm niên">근속 기간</th>
                                    </tr>
                                </thead>
                                <tbody id="managersTableBody">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
"""

    def _generate_teamanalysis_tab(self) -> str:
        """Generate team analysis tab with team selection and metrics"""
        return """
<div class="teamanalysis-section">
    <!-- Team Selection Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h4 class="lang-section-title" data-ko="🏢 팀별 분석" data-en="🏢 Team Analysis" data-vi="🏢 Phân tích nhóm">
            🏢 팀별 분석
        </h4>
        <div class="team-selector-group">
            <select class="form-select lang-select" id="teamPositionSelect" onchange="filterTeamsByPosition()"
                    data-ko-placeholder="전체 직급" data-en-placeholder="All Positions" data-vi-placeholder="Tất cả chức vụ">
                <option value="all" selected class="lang-option" data-ko="전체 직급" data-en="All Positions" data-vi="Tất cả chức vụ">전체 직급</option>
                <!-- Populated by JavaScript -->
            </select>
            <select class="form-select ms-2 lang-select" id="teamNameSelect" onchange="selectTeam()"
                    data-ko-placeholder="팀 선택..." data-en-placeholder="Select Team..." data-vi-placeholder="Chọn nhóm...">
                <option value="all" selected class="lang-option" data-ko="팀 선택..." data-en="Select Team..." data-vi="Chọn nhóm...">팀 선택...</option>
                <!-- Populated by JavaScript -->
            </select>
        </div>
    </div>

    <!-- Team Overview KPI Cards -->
    <div class="row mb-4" id="teamOverviewCards">
        <div class="col-md-3">
            <div class="card border-primary h-100">
                <div class="card-body text-center">
                    <h6 class="text-muted mb-2 lang-text" data-ko="총 팀 수" data-en="Total Teams" data-vi="Tổng số nhóm">총 팀 수</h6>
                    <h2 class="mb-0" id="totalTeamsCount">0</h2>
                    <small class="text-muted lang-text" data-ko="개 팀" data-en="teams" data-vi="nhóm">개 팀</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-success h-100">
                <div class="card-body text-center">
                    <h6 class="text-muted mb-2 lang-text" data-ko="총 팀원 수" data-en="Total Members" data-vi="Tổng thành viên">총 팀원 수</h6>
                    <h2 class="mb-0" id="totalTeamMembersCount">0</h2>
                    <small class="text-muted lang-text" data-ko="명" data-en="people" data-vi="người">명</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-info h-100">
                <div class="card-body text-center">
                    <h6 class="text-muted mb-2 lang-text" data-ko="평균 출근율" data-en="Avg Attendance" data-vi="Tỷ lệ TB">평균 출근율</h6>
                    <h2 class="mb-0" id="avgTeamAttendance">0%</h2>
                    <small class="text-muted lang-text" data-ko="전체 평균" data-en="overall avg" data-vi="trung bình">전체 평균</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-warning h-100" title="출근율이 가장 높은 팀 / Team with highest attendance rate">
                <div class="card-body text-center">
                    <h6 class="text-muted mb-2 lang-text" data-ko="최고 성과 팀" data-en="Top Team" data-vi="Nhóm tốt nhất">최고 성과 팀</h6>
                    <h5 class="mb-0" id="topPerformingTeam">-</h5>
                    <small class="text-muted lang-text" data-ko="📊 출근율 기준" data-en="📊 by attendance" data-vi="📊 theo tỷ lệ">📊 출근율 기준</small>
                </div>
            </div>
        </div>
    </div>

    <!-- Team Performance Charts -->
    <div class="row mb-4">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0 lang-text" data-ko="📊 팀별 출근율 비교" data-en="📊 Attendance by Team" data-vi="📊 Tỷ lệ theo nhóm">📊 팀별 출근율 비교</h6>
                </div>
                <div class="card-body">
                    <canvas id="teamAttendanceComparisonChart" height="250"></canvas>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0 lang-text" data-ko="👥 팀별 인원 분포" data-en="👥 Team Size Distribution" data-vi="👥 Phân bố nhân sự">👥 팀별 인원 분포</h6>
                </div>
                <div class="card-body">
                    <canvas id="teamSizeDistributionChart" height="250"></canvas>
                </div>
            </div>
        </div>
    </div>

    <div class="row mb-4">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0 lang-text" data-ko="🏷️ 팀별 TYPE 분포" data-en="🏷️ TYPE Distribution" data-vi="🏷️ Phân bố TYPE">🏷️ 팀별 TYPE 분포</h6>
                </div>
                <div class="card-body">
                    <canvas id="teamTypeBreakdownChart" height="250"></canvas>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0 lang-text" data-ko="📅 팀별 평균 근속연수" data-en="📅 Avg Tenure by Team" data-vi="📅 Thâm niên TB">📅 팀별 평균 근속연수</h6>
                </div>
                <div class="card-body">
                    <canvas id="teamTenureChart" height="250"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- Team Details Table -->
    <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0 lang-text" data-ko="📋 팀 상세 정보" data-en="📋 Team Details" data-vi="📋 Chi tiết nhóm">📋 팀 상세 정보</h6>
            <div class="btn-group">
                <button type="button" class="btn btn-sm btn-outline-primary dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                    <span class="lang-text" data-ko="📥 내보내기" data-en="📥 Export" data-vi="📥 Xuất">📥 내보내기</span>
                </button>
                <ul class="dropdown-menu dropdown-menu-end">
                    <li><a class="dropdown-item" href="#" onclick="exportTeamAnalysis(); return false;">
                        <span class="lang-text" data-ko="📊 CSV 형식" data-en="📊 CSV Format" data-vi="📊 Định dạng CSV">📊 CSV 형식</span>
                    </a></li>
                    <li><a class="dropdown-item" href="#" onclick="exportTeamAnalysisJSON(); return false;">
                        <span class="lang-text" data-ko="📋 JSON 형식" data-en="📋 JSON Format" data-vi="📋 Định dạng JSON">📋 JSON 형식</span>
                    </a></li>
                </ul>
            </div>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover" id="teamDetailsTable">
                    <thead class="table-light">
                        <tr>
                            <th class="lang-text" data-ko="직급" data-en="Position" data-vi="Chức vụ">직급</th>
                            <th class="lang-text" data-ko="팀명" data-en="Team" data-vi="Nhóm">팀명</th>
                            <th class="lang-text" data-ko="팀원 수" data-en="Members" data-vi="Thành viên">팀원 수</th>
                            <th class="lang-text" data-ko="평균 출근율" data-en="Attendance" data-vi="Tỷ lệ">평균 출근율</th>
                            <th class="lang-text" data-ko="개근자" data-en="Perfect" data-vi="Hoàn hảo">개근자</th>
                            <th class="lang-text" data-ko="고위험 ⓘ" data-en="High Risk ⓘ" data-vi="Rủi ro ⓘ"
                                title="결근율 >30% 또는 무단결근율 >15% / Absence >30% or Unauthorized >15%"
                                style="cursor: help; text-decoration: underline dotted;">고위험 ⓘ</th>
                            <th class="lang-text" data-ko="평균 근속" data-en="Tenure" data-vi="Thâm niên">평균 근속</th>
                            <th class="lang-text" data-ko="액션" data-en="Action" data-vi="Hành động">액션</th>
                        </tr>
                    </thead>
                    <tbody id="teamDetailsTableBody">
                        <!-- Populated by JavaScript -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
"""

    def _generate_individual_attendance_tab(self) -> str:
        """
        Generate individual attendance lookup tab
        개인 출결 조회 탭 생성
        """
        return """
<div class="individual-attendance-section">
    <!-- Search Section / 검색 섹션 -->
    <div class="card mb-4 shadow-sm">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">
                <span class="lang-text" data-ko="🔍 직원 출결 조회" data-en="🔍 Employee Attendance Lookup" data-vi="🔍 Tra cứu điểm danh">
                    🔍 직원 출결 조회
                </span>
            </h5>
        </div>
        <div class="card-body">
            <div class="row align-items-end">
                <div class="col-md-6">
                    <label for="attendanceEmployeeSearch" class="form-label">
                        <span class="lang-text" data-ko="사원번호 입력" data-en="Enter Employee Number" data-vi="Nhập mã nhân viên">
                            사원번호 입력
                        </span>
                    </label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="bi bi-person-badge"></i>🪪</span>
                        <input type="text" class="form-control form-control-lg" id="attendanceEmployeeSearch"
                               placeholder="예: 620060128"
                               aria-label="Employee Number"
                               onkeypress="if(event.key === 'Enter') searchEmployeeAttendance()">
                        <button class="btn btn-primary btn-lg" type="button" onclick="searchEmployeeAttendance()">
                            <span class="lang-text" data-ko="조회" data-en="Search" data-vi="Tìm kiếm">조회</span>
                        </button>
                    </div>
                    <small class="text-muted">
                        <span class="lang-text"
                              data-ko="사원번호를 입력하고 조회 버튼을 클릭하거나 Enter를 누르세요"
                              data-en="Enter employee number and click Search or press Enter"
                              data-vi="Nhập mã nhân viên và nhấn Tìm kiếm hoặc Enter">
                            사원번호를 입력하고 조회 버튼을 클릭하거나 Enter를 누르세요
                        </span>
                    </small>
                </div>
                <div class="col-md-6">
                    <div id="attendanceQuickStats" class="d-none">
                        <!-- Quick stats will be populated by JavaScript -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Results Section / 결과 섹션 -->
    <div id="attendanceResults" class="d-none">
        <!-- Employee Info Card / 직원 정보 카드 -->
        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0" id="attendanceEmployeeName">
                    <span class="lang-text" data-ko="직원 정보" data-en="Employee Information" data-vi="Thông tin nhân viên">
                        직원 정보
                    </span>
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <div class="stat-box text-center p-3 bg-light rounded">
                            <div class="stat-value fs-2 fw-bold text-success" id="attendancePresentDays">0</div>
                            <div class="stat-label text-muted">
                                <span class="lang-text" data-ko="출근일" data-en="Present Days" data-vi="Ngày làm việc">출근일</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-box text-center p-3 bg-light rounded">
                            <div class="stat-value fs-2 fw-bold text-danger" id="attendanceAbsentDays">0</div>
                            <div class="stat-label text-muted">
                                <span class="lang-text" data-ko="결근일" data-en="Absent Days" data-vi="Ngày nghỉ">결근일</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-box text-center p-3 bg-light rounded">
                            <div class="stat-value fs-2 fw-bold text-primary" id="attendanceRate">0%</div>
                            <div class="stat-label text-muted">
                                <span class="lang-text" data-ko="출근율" data-en="Attendance Rate" data-vi="Tỷ lệ đi làm">출근율</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-box text-center p-3 bg-light rounded">
                            <div class="stat-value fs-2 fw-bold text-warning" id="attendanceAbsenceRate">0%</div>
                            <div class="stat-label text-muted">
                                <span class="lang-text" data-ko="결근율" data-en="Absence Rate" data-vi="Tỷ lệ nghỉ">결근율</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Attendance Summary Card / 출결 요약 카드 -->
        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-warning text-dark">
                <h5 class="mb-0">
                    <span class="lang-text" data-ko="📊 출결 분석 요약" data-en="📊 Attendance Analysis Summary" data-vi="📊 Tóm tắt phân tích điểm danh">
                        📊 출결 분석 요약
                    </span>
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <!-- Day of Week Pattern / 요일별 패턴 -->
                    <div class="col-md-6">
                        <h6 class="fw-bold mb-3">
                            <span class="lang-text" data-ko="📅 요일별 결근 패턴" data-en="📅 Absence by Day of Week" data-vi="📅 Nghỉ theo ngày trong tuần">
                                📅 요일별 결근 패턴
                            </span>
                        </h6>
                        <div id="attendanceDayPattern" class="mb-3">
                            <!-- Will be populated by JavaScript -->
                        </div>
                    </div>
                    <!-- Reason Breakdown / 사유별 분석 -->
                    <div class="col-md-6">
                        <h6 class="fw-bold mb-3">
                            <span class="lang-text" data-ko="📋 결근 사유 분석" data-en="📋 Absence Reasons" data-vi="📋 Lý do nghỉ">
                                📋 결근 사유 분석
                            </span>
                        </h6>
                        <div id="attendanceReasonBreakdown" class="mb-3">
                            <!-- Will be populated by JavaScript -->
                        </div>
                    </div>
                </div>
                <!-- Key Insights / 핵심 인사이트 -->
                <div class="mt-3 p-3 bg-light rounded" id="attendanceInsights">
                    <!-- Will be populated by JavaScript -->
                </div>
            </div>
        </div>

        <!-- Daily Attendance Table / 일별 출결 테이블 -->
        <div class="card shadow-sm">
            <div class="card-header bg-secondary text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                    <span class="lang-text" data-ko="📅 일별 출결 현황" data-en="📅 Daily Attendance Records" data-vi="📅 Bảng điểm danh hàng ngày">
                        📅 일별 출결 현황
                    </span>
                </h5>
                <div>
                    <button class="btn btn-sm btn-outline-light me-2" onclick="exportAttendanceCSV()">
                        <span class="lang-text" data-ko="CSV 다운로드" data-en="Download CSV" data-vi="Tải CSV">CSV 다운로드</span>
                    </button>
                </div>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-hover table-striped mb-0" id="attendanceDetailTable">
                        <thead class="table-dark sticky-top">
                            <tr>
                                <th class="text-center" style="width: 120px;">
                                    <span class="lang-text" data-ko="날짜" data-en="Date" data-vi="Ngày">날짜</span>
                                </th>
                                <th class="text-center" style="width: 80px;">
                                    <span class="lang-text" data-ko="요일" data-en="Day" data-vi="Thứ">요일</span>
                                </th>
                                <th class="text-center" style="width: 100px;">
                                    <span class="lang-text" data-ko="출결 상태" data-en="Status" data-vi="Trạng thái">출결 상태</span>
                                </th>
                                <th>
                                    <span class="lang-text" data-ko="결근 사유" data-en="Absence Reason" data-vi="Lý do nghỉ">결근 사유</span>
                                </th>
                                <th class="text-center" style="width: 100px;">
                                    <span class="lang-text" data-ko="근무시간" data-en="Work Time" data-vi="Thời gian">근무시간</span>
                                </th>
                            </tr>
                        </thead>
                        <tbody id="attendanceDetailBody">
                            <!-- Will be populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- No Results Message / 결과 없음 메시지 -->
    <div id="attendanceNoResults" class="d-none">
        <div class="alert alert-warning text-center py-5">
            <h4>
                <span class="lang-text" data-ko="❌ 해당 사원번호의 출결 기록을 찾을 수 없습니다"
                      data-en="❌ No attendance records found for this employee number"
                      data-vi="❌ Không tìm thấy dữ liệu điểm danh cho mã nhân viên này">
                    ❌ 해당 사원번호의 출결 기록을 찾을 수 없습니다
                </span>
            </h4>
            <p class="text-muted">
                <span class="lang-text" data-ko="사원번호를 확인하고 다시 시도해주세요"
                      data-en="Please verify the employee number and try again"
                      data-vi="Vui lòng kiểm tra lại mã nhân viên">
                    사원번호를 확인하고 다시 시도해주세요
                </span>
            </p>
        </div>
    </div>

    <!-- Initial State Message / 초기 상태 메시지 -->
    <div id="attendanceInitialState">
        <div class="text-center py-5 text-muted">
            <div class="display-1 mb-3">📅</div>
            <h4>
                <span class="lang-text" data-ko="사원번호를 입력하여 개인 출결 현황을 조회하세요"
                      data-en="Enter an employee number to view individual attendance records"
                      data-vi="Nhập mã nhân viên để xem dữ liệu điểm danh cá nhân">
                    사원번호를 입력하여 개인 출결 현황을 조회하세요
                </span>
            </h4>
            <p>
                <span class="lang-text" data-ko="출결 현황, 결근 패턴, 사유별 분석을 확인할 수 있습니다"
                      data-en="View attendance records, absence patterns, and reason analysis"
                      data-vi="Xem điểm danh, mô hình nghỉ và phân tích lý do">
                    출결 현황, 결근 패턴, 사유별 분석을 확인할 수 있습니다
                </span>
            </p>
        </div>
    </div>
</div>
"""

    def _generate_help_tab(self) -> str:
        """Generate comprehensive help tab with KPI explanations in 3 languages"""
        return """
<div class="help-section">
    <!-- Help Navigation -->
    <div class="row mb-4">
        <div class="col-12">
            <ul class="nav nav-pills justify-content-center" id="help-nav" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active lang-help-tab" data-bs-toggle="pill" data-bs-target="#help-quickstart"
                            data-ko="🚀 빠른 시작" data-en="🚀 Quick Start" data-vi="🚀 Bắt đầu nhanh">
                        🚀 빠른 시작
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link lang-help-tab" data-bs-toggle="pill" data-bs-target="#help-kpi"
                            data-ko="📊 KPI 지표" data-en="📊 KPI Metrics" data-vi="📊 Chỉ số KPI">
                        📊 KPI 지표
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link lang-help-tab" data-bs-toggle="pill" data-bs-target="#help-features"
                            data-ko="🛠️ 기능 가이드" data-en="🛠️ Features" data-vi="🛠️ Tính năng">
                        🛠️ 기능 가이드
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link lang-help-tab" data-bs-toggle="pill" data-bs-target="#help-faq"
                            data-ko="❓ FAQ" data-en="❓ FAQ" data-vi="❓ Câu hỏi">
                        ❓ FAQ
                    </button>
                </li>
            </ul>
        </div>
    </div>

    <!-- Help Content -->
    <div class="tab-content" id="help-content">
        <!-- Quick Start Guide -->
        <div class="tab-pane fade show active" id="help-quickstart">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0 lang-help-title" data-ko="🚀 대시보드 빠른 시작 가이드"
                        data-en="🚀 Quick Start Guide" data-vi="🚀 Hướng dẫn nhanh">
                        🚀 대시보드 빠른 시작 가이드
                    </h5>
                </div>
                <div class="card-body">
                    <div class="lang-help-content"
                         data-ko="<h6>1단계: 대시보드 개요 확인</h6>
                                  <p>첫 화면(Overview 탭)에서 11개의 핵심 KPI 카드를 확인할 수 있습니다. 각 카드는 실시간 인사 데이터를 시각화하여 보여줍니다.</p>
                                  <ul>
                                    <li><strong>총 직원수</strong>: 현재 활성 직원 수</li>
                                    <li><strong>결근율</strong>: 당월 결근 비율 (목표: 10% 이하)</li>
                                    <li><strong>완벽출근율</strong>: 한 번도 결근하지 않은 직원 비율</li>
                                    <li><strong>이직률</strong>: 최근 3개월 평균 이직률</li>
                                  </ul>
                                  <h6>2단계: 상세 분석</h6>
                                  <p>각 KPI 카드를 클릭하면 상세 모달이 열립니다. 모달에는 다음 정보가 포함됩니다:</p>
                                  <ul>
                                    <li>주간 트렌드 차트</li>
                                    <li>팀별 비교 도넛 차트</li>
                                    <li>상세 데이터 테이블</li>
                                    <li>전월 대비 변화율</li>
                                  </ul>
                                  <h6>3단계: 언어 전환</h6>
                                  <p>우측 상단의 국기 아이콘을 클릭하여 언어를 전환할 수 있습니다:</p>
                                  <ul>
                                    <li>🇰🇷 한국어</li>
                                    <li>🇺🇸 English</li>
                                    <li>🇻🇳 Tiếng Việt</li>
                                  </ul>
                                  <h6>4단계: 데이터 필터링</h6>
                                  <p>각 탭에서 데이터를 필터링하고 정렬할 수 있습니다:</p>
                                  <ul>
                                    <li><strong>Trends 탭</strong>: 기간별 추세 확인</li>
                                    <li><strong>Details 탭</strong>: 개별 직원 정보 검색</li>
                                    <li><strong>Team Analysis 탭</strong>: 팀별 성과 비교</li>
                                  </ul>"
                         data-en="<h6>Step 1: Overview Dashboard</h6>
                                  <p>The first screen (Overview tab) displays 11 key KPI cards with real-time HR data visualization.</p>
                                  <ul>
                                    <li><strong>Total Employees</strong>: Current active headcount</li>
                                    <li><strong>Absence Rate</strong>: Monthly absence percentage (Target: <10%)</li>
                                    <li><strong>Perfect Attendance</strong>: Employees with zero absences</li>
                                    <li><strong>Turnover Rate</strong>: 3-month rolling average</li>
                                  </ul>
                                  <h6>Step 2: Detailed Analysis</h6>
                                  <p>Click any KPI card to open a detailed modal containing:</p>
                                  <ul>
                                    <li>Weekly trend charts</li>
                                    <li>Team comparison donut charts</li>
                                    <li>Detailed data tables</li>
                                    <li>Month-over-month changes</li>
                                  </ul>
                                  <h6>Step 3: Language Switching</h6>
                                  <p>Click the flag icon in the top right to switch languages:</p>
                                  <ul>
                                    <li>🇰🇷 Korean</li>
                                    <li>🇺🇸 English</li>
                                    <li>🇻🇳 Vietnamese</li>
                                  </ul>
                                  <h6>Step 4: Data Filtering</h6>
                                  <p>Filter and sort data in each tab:</p>
                                  <ul>
                                    <li><strong>Trends Tab</strong>: View historical trends</li>
                                    <li><strong>Details Tab</strong>: Search individual employees</li>
                                    <li><strong>Team Analysis Tab</strong>: Compare team performance</li>
                                  </ul>"
                         data-vi="<h6>Bước 1: Tổng quan bảng điều khiển</h6>
                                  <p>Màn hình đầu tiên (tab Tổng quan) hiển thị 11 thẻ KPI chính với trực quan hóa dữ liệu nhân sự thời gian thực.</p>
                                  <ul>
                                    <li><strong>Tổng số nhân viên</strong>: Số lượng nhân viên đang hoạt động</li>
                                    <li><strong>Tỷ lệ vắng mặt</strong>: Tỷ lệ phần trăm vắng mặt hàng tháng (Mục tiêu: <10%)</li>
                                    <li><strong>Chấm công hoàn hảo</strong>: Nhân viên không vắng mặt</li>
                                    <li><strong>Tỷ lệ nghỉ việc</strong>: Trung bình 3 tháng</li>
                                  </ul>
                                  <h6>Bước 2: Phân tích chi tiết</h6>
                                  <p>Nhấp vào bất kỳ thẻ KPI nào để mở cửa sổ chi tiết chứa:</p>
                                  <ul>
                                    <li>Biểu đồ xu hướng hàng tuần</li>
                                    <li>Biểu đồ so sánh nhóm</li>
                                    <li>Bảng dữ liệu chi tiết</li>
                                    <li>Thay đổi theo tháng</li>
                                  </ul>
                                  <h6>Bước 3: Chuyển đổi ngôn ngữ</h6>
                                  <p>Nhấp vào biểu tượng cờ ở góc trên bên phải để chuyển đổi ngôn ngữ:</p>
                                  <ul>
                                    <li>🇰🇷 Tiếng Hàn</li>
                                    <li>🇺🇸 Tiếng Anh</li>
                                    <li>🇻🇳 Tiếng Việt</li>
                                  </ul>
                                  <h6>Bước 4: Lọc dữ liệu</h6>
                                  <p>Lọc và sắp xếp dữ liệu trong mỗi tab:</p>
                                  <ul>
                                    <li><strong>Tab Xu hướng</strong>: Xem xu hướng lịch sử</li>
                                    <li><strong>Tab Chi tiết</strong>: Tìm kiếm nhân viên cá nhân</li>
                                    <li><strong>Tab Phân tích nhóm</strong>: So sánh hiệu suất nhóm</li>
                                  </ul>">
                        <h6>1단계: 대시보드 개요 확인</h6>
                        <p>첫 화면(Overview 탭)에서 11개의 핵심 KPI 카드를 확인할 수 있습니다.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- KPI Metrics Explanation -->
        <div class="tab-pane fade" id="help-kpi">
            <div class="card">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0 lang-help-title" data-ko="📊 KPI 지표 상세 설명"
                        data-en="📊 KPI Metrics Explanation" data-vi="📊 Giải thích chỉ số KPI">
                        📊 KPI 지표 상세 설명
                    </h5>
                </div>
                <div class="card-body">
                    <div class="accordion" id="kpiAccordion">
                        <!-- KPI 1: Total Employees -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi1"
                                        data-ko="1️⃣ 총 직원수 (Total Employees)"
                                        data-en="1️⃣ Total Employees"
                                        data-vi="1️⃣ Tổng số nhân viên">
                                    1️⃣ 총 직원수 (Total Employees)
                                </button>
                            </h2>
                            <div id="kpi1" class="accordion-collapse collapse show">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 현재 활성 상태인 전체 직원 수입니다.<br>
                                              <strong>계산 방식</strong>: Status가 'Active'인 직원 수를 집계합니다.<br>
                                              <strong>중요성</strong>: 조직의 규모와 인력 운영 현황을 파악하는 가장 기본적인 지표입니다.<br>
                                              <strong>활용</strong>: 채용 계획, 예산 편성, 인력 배치 의사결정에 활용됩니다."
                                     data-en="<strong>Definition</strong>: Total number of currently active employees.<br>
                                              <strong>Calculation</strong>: Count of employees with 'Active' status.<br>
                                              <strong>Importance</strong>: Most fundamental metric for understanding organizational size and workforce operations.<br>
                                              <strong>Usage</strong>: Used for hiring plans, budgeting, and workforce allocation decisions."
                                     data-vi="<strong>Định nghĩa</strong>: Tổng số nhân viên đang hoạt động hiện tại.<br>
                                              <strong>Tính toán</strong>: Đếm nhân viên có trạng thái 'Hoạt động'.<br>
                                              <strong>Tầm quan trọng</strong>: Chỉ số cơ bản nhất để hiểu quy mô tổ chức và hoạt động lực lượng lao động.<br>
                                              <strong>Sử dụng</strong>: Dùng cho kế hoạch tuyển dụng, lập ngân sách và quyết định phân bổ lực lượng lao động.">
                                    <strong>정의</strong>: 현재 활성 상태인 전체 직원 수입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 2: Absence Rate -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi2"
                                        data-ko="2️⃣ 결근율 (Absence Rate)"
                                        data-en="2️⃣ Absence Rate"
                                        data-vi="2️⃣ Tỷ lệ vắng mặt">
                                    2️⃣ 결근율 (Absence Rate)
                                </button>
                            </h2>
                            <div id="kpi2" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 전체 근무일 대비 결근 비율입니다.<br>
                                              <strong>계산 방식</strong>: (결근 일수 / 총 근무일) × 100<br>
                                              <strong>목표</strong>: 10% 이하 유지<br>
                                              <strong>중요성</strong>: 조직의 생산성과 직원 몰입도를 나타내는 핵심 지표입니다.<br>
                                              <strong>활용</strong>: 높은 결근율은 업무 환경 개선, 복지 확대, 건강관리 프로그램 도입 등의 액션을 유도합니다."
                                     data-en="<strong>Definition</strong>: Percentage of absences relative to total working days.<br>
                                              <strong>Calculation</strong>: (Absence days / Total working days) × 100<br>
                                              <strong>Target</strong>: Maintain below 10%<br>
                                              <strong>Importance</strong>: Key indicator of organizational productivity and employee engagement.<br>
                                              <strong>Usage</strong>: High absence rates trigger actions like workplace improvements, enhanced benefits, and health programs."
                                     data-vi="<strong>Định nghĩa</strong>: Tỷ lệ vắng mặt so với tổng số ngày làm việc.<br>
                                              <strong>Tính toán</strong>: (Ngày vắng mặt / Tổng ngày làm việc) × 100<br>
                                              <strong>Mục tiêu</strong>: Duy trì dưới 10%<br>
                                              <strong>Tầm quan trọng</strong>: Chỉ số chính về năng suất tổ chức và sự gắn kết của nhân viên.<br>
                                              <strong>Sử dụng</strong>: Tỷ lệ vắng mặt cao kích hoạt các hành động như cải thiện môi trường làm việc, tăng phúc lợi và chương trình sức khỏe.">
                                    <strong>정의</strong>: 전체 근무일 대비 결근 비율입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 3: Perfect Attendance -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi3"
                                        data-ko="3️⃣ 완벽출근율 (Perfect Attendance)"
                                        data-en="3️⃣ Perfect Attendance Rate"
                                        data-vi="3️⃣ Tỷ lệ chấm công hoàn hảo">
                                    3️⃣ 완벽출근율 (Perfect Attendance)
                                </button>
                            </h2>
                            <div id="kpi3" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 한 번도 결근하지 않은 직원의 비율입니다.<br>
                                              <strong>계산 방식</strong>: (완벽출근 직원 수 / 전체 직원 수) × 100<br>
                                              <strong>목표</strong>: 50% 이상 유지<br>
                                              <strong>중요성</strong>: 직원 만족도와 조직 문화의 건강성을 나타냅니다.<br>
                                              <strong>활용</strong>: 인센티브 제도 설계, 우수 직원 포상, 조직 문화 개선에 활용됩니다."
                                     data-en="<strong>Definition</strong>: Percentage of employees with zero absences.<br>
                                              <strong>Calculation</strong>: (Perfect attendance employees / Total employees) × 100<br>
                                              <strong>Target</strong>: Maintain above 50%<br>
                                              <strong>Importance</strong>: Indicates employee satisfaction and healthy organizational culture.<br>
                                              <strong>Usage</strong>: Used for incentive program design, employee recognition, and culture improvement."
                                     data-vi="<strong>Định nghĩa</strong>: Tỷ lệ nhân viên không vắng mặt.<br>
                                              <strong>Tính toán</strong>: (Nhân viên chấm công hoàn hảo / Tổng nhân viên) × 100<br>
                                              <strong>Mục tiêu</strong>: Duy trì trên 50%<br>
                                              <strong>Tầm quan trọng</strong>: Cho biết sự hài lòng của nhân viên và văn hóa tổ chức lành mạnh.<br>
                                              <strong>Sử dụng</strong>: Dùng để thiết kế chương trình khuyến khích, công nhận nhân viên và cải thiện văn hóa.">
                                    <strong>정의</strong>: 한 번도 결근하지 않은 직원의 비율입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 4: Unauthorized Absence Rate -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi4"
                                        data-ko="4️⃣ 무단결근율 (Unauthorized Absence Rate)"
                                        data-en="4️⃣ Unauthorized Absence Rate"
                                        data-vi="4️⃣ Tỷ lệ vắng mặt không phép">
                                    4️⃣ 무단결근율 (Unauthorized Absence Rate)
                                </button>
                            </h2>
                            <div id="kpi4" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 사전 승인 없이 결근한 비율입니다.<br>
                                              <strong>계산 방식</strong>: (무단결근 일수 / 총 근무일) × 100<br>
                                              <strong>목표</strong>: 2% 이하 유지<br>
                                              <strong>중요성</strong>: 무단결근은 생산성에 직접적인 영향을 미치며, 팀 사기와 조직 규율의 지표입니다.<br>
                                              <strong>활용</strong>: 무단결근이 높은 팀은 근태 관리 강화, 개인 면담, 징계 조치 등이 필요할 수 있습니다."
                                     data-en="<strong>Definition</strong>: Percentage of absences without prior approval.<br>
                                              <strong>Calculation</strong>: (Unauthorized absence days / Total working days) × 100<br>
                                              <strong>Target</strong>: Maintain below 2%<br>
                                              <strong>Importance</strong>: Unauthorized absences directly impact productivity and indicate team morale and organizational discipline.<br>
                                              <strong>Usage</strong>: Teams with high rates may need attendance management, individual counseling, or disciplinary actions."
                                     data-vi="<strong>Định nghĩa</strong>: Tỷ lệ vắng mặt không được phê duyệt trước.<br>
                                              <strong>Tính toán</strong>: (Ngày vắng không phép / Tổng ngày làm việc) × 100<br>
                                              <strong>Mục tiêu</strong>: Duy trì dưới 2%<br>
                                              <strong>Tầm quan trọng</strong>: Vắng mặt không phép ảnh hưởng trực tiếp đến năng suất và cho biết tinh thần nhóm và kỷ luật tổ chức.<br>
                                              <strong>Sử dụng</strong>: Các nhóm có tỷ lệ cao có thể cần quản lý chấm công, tư vấn cá nhân hoặc hành động kỷ luật.">
                                    <strong>정의</strong>: 사전 승인 없이 결근한 비율입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 5: Resignation Rate -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi5"
                                        data-ko="5️⃣ 이직률 (Resignation Rate)"
                                        data-en="5️⃣ Resignation Rate"
                                        data-vi="5️⃣ Tỷ lệ nghỉ việc">
                                    5️⃣ 이직률 (Resignation Rate)
                                </button>
                            </h2>
                            <div id="kpi5" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 일정 기간 내 퇴사한 직원 비율입니다.<br>
                                              <strong>계산 방식</strong>: (퇴사 직원 수 / 평균 직원 수) × 100<br>
                                              <strong>목표</strong>: 월 3% 이하 유지<br>
                                              <strong>중요성</strong>: 높은 이직률은 채용 비용 증가, 생산성 저하, 조직 문화 문제를 나타낼 수 있습니다.<br>
                                              <strong>활용</strong>: 퇴사 면담, 직원 만족도 조사, 보상 체계 검토에 활용됩니다."
                                     data-en="<strong>Definition</strong>: Percentage of employees who left within a period.<br>
                                              <strong>Calculation</strong>: (Resigned employees / Average headcount) × 100<br>
                                              <strong>Target</strong>: Maintain below 3% monthly<br>
                                              <strong>Importance</strong>: High turnover indicates increased hiring costs, productivity loss, and potential cultural issues.<br>
                                              <strong>Usage</strong>: Used for exit interviews, satisfaction surveys, and compensation review."
                                     data-vi="<strong>Định nghĩa</strong>: Tỷ lệ nhân viên nghỉ việc trong một khoảng thời gian.<br>
                                              <strong>Tính toán</strong>: (Nhân viên nghỉ việc / Số lượng nhân viên trung bình) × 100<br>
                                              <strong>Mục tiêu</strong>: Duy trì dưới 3% hàng tháng<br>
                                              <strong>Tầm quan trọng</strong>: Tỷ lệ nghỉ việc cao cho thấy chi phí tuyển dụng tăng, mất năng suất và vấn đề văn hóa tiềm ẩn.<br>
                                              <strong>Sử dụng</strong>: Dùng cho phỏng vấn nghỉ việc, khảo sát hài lòng và xem xét lương thưởng.">
                                    <strong>정의</strong>: 일정 기간 내 퇴사한 직원 비율입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 6: New Hires -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi6"
                                        data-ko="6️⃣ 신규입사 (New Hires)"
                                        data-en="6️⃣ New Hires"
                                        data-vi="6️⃣ Nhân viên mới">
                                    6️⃣ 신규입사 (New Hires)
                                </button>
                            </h2>
                            <div id="kpi6" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 당월에 새로 입사한 직원 수입니다.<br>
                                              <strong>계산 방식</strong>: 해당 월에 입사일이 있는 직원 수<br>
                                              <strong>중요성</strong>: 채용 활동의 결과를 나타내며, 조직 성장과 인력 보충 상황을 파악할 수 있습니다.<br>
                                              <strong>활용</strong>: 채용 계획 대비 실적 비교, 온보딩 프로그램 운영, 신입 교육 계획에 활용됩니다."
                                     data-en="<strong>Definition</strong>: Number of employees who joined this month.<br>
                                              <strong>Calculation</strong>: Count of employees with hire date in current month<br>
                                              <strong>Importance</strong>: Reflects hiring activity results and organizational growth/replenishment status.<br>
                                              <strong>Usage</strong>: Compare against hiring plans, manage onboarding programs, and plan new hire training."
                                     data-vi="<strong>Định nghĩa</strong>: Số nhân viên mới gia nhập trong tháng này.<br>
                                              <strong>Tính toán</strong>: Số nhân viên có ngày tuyển dụng trong tháng hiện tại<br>
                                              <strong>Tầm quan trọng</strong>: Phản ánh kết quả hoạt động tuyển dụng và tình trạng tăng trưởng/bổ sung nhân sự.<br>
                                              <strong>Sử dụng</strong>: So sánh với kế hoạch tuyển dụng, quản lý chương trình hội nhập và lên kế hoạch đào tạo nhân viên mới.">
                                    <strong>정의</strong>: 당월에 새로 입사한 직원 수입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 7: Recent Resignations -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi7"
                                        data-ko="7️⃣ 최근퇴사 (Recent Resignations)"
                                        data-en="7️⃣ Recent Resignations"
                                        data-vi="7️⃣ Nghỉ việc gần đây">
                                    7️⃣ 최근퇴사 (Recent Resignations)
                                </button>
                            </h2>
                            <div id="kpi7" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 당월에 퇴사한 직원 수입니다.<br>
                                              <strong>계산 방식</strong>: 해당 월에 퇴사일이 있는 직원 수<br>
                                              <strong>중요성</strong>: 퇴사 현황을 실시간으로 파악하여 인력 공백 대응과 채용 계획 수립에 필수적입니다.<br>
                                              <strong>활용</strong>: 퇴사 사유 분석, 대체 인력 채용, 인수인계 관리에 활용됩니다."
                                     data-en="<strong>Definition</strong>: Number of employees who left this month.<br>
                                              <strong>Calculation</strong>: Count of employees with resignation date in current month<br>
                                              <strong>Importance</strong>: Essential for real-time tracking of departures, addressing workforce gaps, and planning recruitment.<br>
                                              <strong>Usage</strong>: Analyze resignation reasons, recruit replacements, and manage handovers."
                                     data-vi="<strong>Định nghĩa</strong>: Số nhân viên nghỉ việc trong tháng này.<br>
                                              <strong>Tính toán</strong>: Số nhân viên có ngày nghỉ việc trong tháng hiện tại<br>
                                              <strong>Tầm quan trọng</strong>: Cần thiết để theo dõi thời gian thực về nghỉ việc, giải quyết khoảng trống nhân sự và lên kế hoạch tuyển dụng.<br>
                                              <strong>Sử dụng</strong>: Phân tích lý do nghỉ việc, tuyển thay thế và quản lý bàn giao.">
                                    <strong>정의</strong>: 당월에 퇴사한 직원 수입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 8: Under 60 Days -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi8"
                                        data-ko="8️⃣ 60일 미만 신입 (Under 60 Days)"
                                        data-en="8️⃣ Under 60 Days (New Employees)"
                                        data-vi="8️⃣ Dưới 60 ngày (Nhân viên mới)">
                                    8️⃣ 60일 미만 신입 (Under 60 Days)
                                </button>
                            </h2>
                            <div id="kpi8" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 입사 후 60일이 지나지 않은 신입 직원 수입니다.<br>
                                              <strong>계산 방식</strong>: 기준일 - 입사일 < 60일인 직원 수<br>
                                              <strong>중요성</strong>: 신입 직원은 이직 위험이 높고 집중 관리가 필요합니다. 초기 적응 기간의 관리가 장기 재직에 결정적입니다.<br>
                                              <strong>활용</strong>: 멘토링 프로그램 배정, 정기 면담 스케줄링, 조기 이탈 방지 활동에 활용됩니다."
                                     data-en="<strong>Definition</strong>: Number of employees with less than 60 days since hire.<br>
                                              <strong>Calculation</strong>: Count where (Report date - Hire date) < 60 days<br>
                                              <strong>Importance</strong>: New employees have higher turnover risk and need focused attention. Early adaptation period management is critical for long-term retention.<br>
                                              <strong>Usage</strong>: Assign mentoring programs, schedule regular check-ins, and implement early attrition prevention activities."
                                     data-vi="<strong>Định nghĩa</strong>: Số nhân viên có ít hơn 60 ngày kể từ khi tuyển dụng.<br>
                                              <strong>Tính toán</strong>: Đếm nơi (Ngày báo cáo - Ngày tuyển dụng) < 60 ngày<br>
                                              <strong>Tầm quan trọng</strong>: Nhân viên mới có nguy cơ nghỉ việc cao hơn và cần được chú ý tập trung. Quản lý giai đoạn thích nghi ban đầu rất quan trọng cho việc giữ chân lâu dài.<br>
                                              <strong>Sử dụng</strong>: Phân công chương trình mentoring, lên lịch kiểm tra định kỳ và thực hiện hoạt động ngăn ngừa nghỉ việc sớm.">
                                    <strong>정의</strong>: 입사 후 60일이 지나지 않은 신입 직원 수입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 9: Early Warning -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi9"
                                        data-ko="9️⃣ 조기경보 (Early Warning)"
                                        data-en="9️⃣ Early Warning Indicators"
                                        data-vi="9️⃣ Cảnh báo sớm">
                                    9️⃣ 조기경보 (Early Warning)
                                </button>
                            </h2>
                            <div id="kpi9" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 이직 또는 문제 발생 가능성이 높은 직원 수입니다.<br>
                                              <strong>계산 방식</strong>: 결근율 15% 이상, 무단결근 발생, 또는 성과 지표 저하 직원 집계<br>
                                              <strong>중요성</strong>: 사전에 문제를 감지하여 예방적 조치를 취할 수 있습니다.<br>
                                              <strong>활용</strong>: 개인 면담 우선순위 지정, 멘토 배정, 업무 환경 개선 활동에 활용됩니다."
                                     data-en="<strong>Definition</strong>: Number of employees with high likelihood of turnover or issues.<br>
                                              <strong>Calculation</strong>: Count of employees with absence rate ≥15%, unauthorized absences, or declining performance<br>
                                              <strong>Importance</strong>: Enables proactive detection and preventive measures before issues escalate.<br>
                                              <strong>Usage</strong>: Prioritize individual meetings, assign mentors, and implement workplace improvement initiatives."
                                     data-vi="<strong>Định nghĩa</strong>: Số nhân viên có khả năng nghỉ việc hoặc gặp vấn đề cao.<br>
                                              <strong>Tính toán</strong>: Đếm nhân viên có tỷ lệ vắng mặt ≥15%, vắng không phép, hoặc hiệu suất giảm<br>
                                              <strong>Tầm quan trọng</strong>: Cho phép phát hiện chủ động và biện pháp phòng ngừa trước khi vấn đề leo thang.<br>
                                              <strong>Sử dụng</strong>: Ưu tiên cuộc họp cá nhân, phân công mentor và thực hiện các sáng kiến cải thiện môi trường làm việc.">
                                    <strong>정의</strong>: 이직 또는 문제 발생 가능성이 높은 직원 수입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 10: Data Errors -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi10"
                                        data-ko="🔟 데이터 오류 (Data Errors)"
                                        data-en="🔟 Data Errors"
                                        data-vi="🔟 Lỗi dữ liệu">
                                    🔟 데이터 오류 (Data Errors)
                                </button>
                            </h2>
                            <div id="kpi10" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 데이터 정합성 검사에서 발견된 오류 건수입니다.<br>
                                              <strong>검사 항목</strong>: 입사일 미래 날짜, 필수 필드 누락, 중복 사번, 잘못된 팀 코드 등<br>
                                              <strong>목표</strong>: 0건 유지<br>
                                              <strong>중요성</strong>: 데이터 품질은 모든 HR 지표의 신뢰성에 직결됩니다.<br>
                                              <strong>활용</strong>: 데이터 정정 우선순위 지정, 입력 프로세스 개선, 데이터 거버넌스 강화에 활용됩니다."
                                     data-en="<strong>Definition</strong>: Number of errors found in data integrity checks.<br>
                                              <strong>Check Items</strong>: Future hire dates, missing required fields, duplicate employee IDs, invalid team codes, etc.<br>
                                              <strong>Target</strong>: Maintain at 0<br>
                                              <strong>Importance</strong>: Data quality directly impacts the reliability of all HR metrics.<br>
                                              <strong>Usage</strong>: Prioritize data corrections, improve input processes, and strengthen data governance."
                                     data-vi="<strong>Định nghĩa</strong>: Số lỗi được tìm thấy trong kiểm tra tính toàn vẹn dữ liệu.<br>
                                              <strong>Mục kiểm tra</strong>: Ngày tuyển dụng trong tương lai, thiếu trường bắt buộc, mã nhân viên trùng lặp, mã nhóm không hợp lệ, v.v.<br>
                                              <strong>Mục tiêu</strong>: Duy trì ở 0<br>
                                              <strong>Tầm quan trọng</strong>: Chất lượng dữ liệu ảnh hưởng trực tiếp đến độ tin cậy của tất cả các chỉ số HR.<br>
                                              <strong>Sử dụng</strong>: Ưu tiên sửa lỗi dữ liệu, cải thiện quy trình nhập liệu và tăng cường quản trị dữ liệu.">
                                    <strong>정의</strong>: 데이터 정합성 검사에서 발견된 오류 건수입니다.
                                </div>
                            </div>
                        </div>

                        <!-- KPI 11: Team Distribution -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-kpi-title" type="button" data-bs-toggle="collapse" data-bs-target="#kpi11"
                                        data-ko="1️⃣1️⃣ 팀 분포 (Team Distribution)"
                                        data-en="1️⃣1️⃣ Team Distribution"
                                        data-vi="1️⃣1️⃣ Phân bố nhóm">
                                    1️⃣1️⃣ 팀 분포 (Team Distribution)
                                </button>
                            </h2>
                            <div id="kpi11" class="accordion-collapse collapse">
                                <div class="accordion-body lang-kpi-content"
                                     data-ko="<strong>정의</strong>: 각 팀별 인원 분포와 비율입니다.<br>
                                              <strong>계산 방식</strong>: 팀별 직원 수 및 전체 대비 비율<br>
                                              <strong>중요성</strong>: 조직 구조와 인력 배치 균형을 파악하는 데 필수적입니다.<br>
                                              <strong>활용</strong>: 팀 간 인력 재배치, 신규 채용 배분, 조직 구조 개편에 활용됩니다."
                                     data-en="<strong>Definition</strong>: Distribution and ratio of employees across teams.<br>
                                              <strong>Calculation</strong>: Employee count per team and ratio to total<br>
                                              <strong>Importance</strong>: Essential for understanding organizational structure and workforce allocation balance.<br>
                                              <strong>Usage</strong>: Plan inter-team reallocations, distribute new hires, and restructure organization."
                                     data-vi="<strong>Định nghĩa</strong>: Phân bố và tỷ lệ nhân viên giữa các nhóm.<br>
                                              <strong>Tính toán</strong>: Số nhân viên mỗi nhóm và tỷ lệ so với tổng<br>
                                              <strong>Tầm quan trọng</strong>: Cần thiết để hiểu cấu trúc tổ chức và cân bằng phân bổ lực lượng lao động.<br>
                                              <strong>Sử dụng</strong>: Lên kế hoạch phân bổ lại giữa các nhóm, phân bổ nhân viên mới và tái cấu trúc tổ chức.">
                                    <strong>정의</strong>: 각 팀별 인원 분포와 비율입니다.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Features Guide -->
        <div class="tab-pane fade" id="help-features">
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0 lang-help-title" data-ko="🛠️ 주요 기능 가이드"
                        data-en="🛠️ Features Guide" data-vi="🛠️ Hướng dẫn tính năng">
                        🛠️ 주요 기능 가이드
                    </h5>
                </div>
                <div class="card-body">
                    <div class="lang-help-content"
                         data-ko="<h6>🔍 검색 및 필터링</h6>
                                  <p><strong>Details 탭</strong>에서 직원 정보를 검색할 수 있습니다:</p>
                                  <ul>
                                    <li>이름으로 검색</li>
                                    <li>직급으로 필터링</li>
                                    <li>팀별로 정렬</li>
                                    <li>테이블 헤더 클릭으로 오름차순/내림차순 정렬</li>
                                  </ul>
                                  <h6>📊 차트 인터랙션</h6>
                                  <p>모든 차트는 인터랙티브합니다:</p>
                                  <ul>
                                    <li>데이터 포인트에 마우스 오버 시 상세 정보 표시</li>
                                    <li>범례 클릭하여 데이터 시리즈 표시/숨김</li>
                                    <li>툴팁으로 정확한 수치 확인</li>
                                  </ul>
                                  <h6>📥 데이터 내보내기</h6>
                                  <p>Details 탭에서 직원 데이터를 다운로드할 수 있습니다:</p>
                                  <ul>
                                    <li>CSV 형식으로 내보내기 (테이블 상단 버튼)</li>
                                    <li>JSON 형식으로 내보내기</li>
                                  </ul>
                                  <h6>📱 반응형 디자인</h6>
                                  <p>다양한 기기에서 대시보드를 사용할 수 있습니다:</p>
                                  <ul>
                                    <li>데스크톱, 태블릿, 모바일 지원</li>
                                    <li>화면 크기에 맞춰 자동 레이아웃 조정</li>
                                  </ul>"
                         data-en="<h6>🔍 Search and Filtering</h6>
                                  <p>Search employee information in the <strong>Details tab</strong>:</p>
                                  <ul>
                                    <li>Search by name</li>
                                    <li>Filter by position</li>
                                    <li>Sort by team</li>
                                    <li>Click table headers for ascending/descending sort</li>
                                  </ul>
                                  <h6>📊 Chart Interactions</h6>
                                  <p>All charts are interactive:</p>
                                  <ul>
                                    <li>Hover over data points for details</li>
                                    <li>Click legend to show/hide data series</li>
                                    <li>View exact values in tooltips</li>
                                  </ul>
                                  <h6>📥 Data Export</h6>
                                  <p>Download employee data from the Details tab:</p>
                                  <ul>
                                    <li>Export to CSV format (button above table)</li>
                                    <li>Export to JSON format</li>
                                  </ul>
                                  <h6>📱 Responsive Design</h6>
                                  <p>Use the dashboard on various devices:</p>
                                  <ul>
                                    <li>Desktop, tablet, and mobile support</li>
                                    <li>Auto-adjusting layout for screen size</li>
                                  </ul>"
                         data-vi="<h6>🔍 Tìm kiếm và lọc</h6>
                                  <p>Tìm kiếm thông tin nhân viên trong <strong>tab Chi tiết</strong>:</p>
                                  <ul>
                                    <li>Tìm kiếm theo tên</li>
                                    <li>Lọc theo chức vụ</li>
                                    <li>Sắp xếp theo nhóm</li>
                                    <li>Nhấp vào tiêu đề bảng để sắp xếp tăng/giảm</li>
                                  </ul>
                                  <h6>📊 Tương tác biểu đồ</h6>
                                  <p>Tất cả biểu đồ đều tương tác:</p>
                                  <ul>
                                    <li>Di chuột qua điểm dữ liệu để xem chi tiết</li>
                                    <li>Nhấp vào chú giải để hiển thị/ẩn chuỗi dữ liệu</li>
                                    <li>Xem giá trị chính xác trong tooltip</li>
                                  </ul>
                                  <h6>📥 Xuất dữ liệu</h6>
                                  <p>Tải xuống dữ liệu nhân viên từ tab Chi tiết:</p>
                                  <ul>
                                    <li>Xuất sang định dạng CSV (nút phía trên bảng)</li>
                                    <li>Xuất sang định dạng JSON</li>
                                  </ul>
                                  <h6>📱 Thiết kế đáp ứng</h6>
                                  <p>Sử dụng bảng điều khiển trên nhiều thiết bị:</p>
                                  <ul>
                                    <li>Hỗ trợ máy tính, máy tính bảng và điện thoại</li>
                                    <li>Bố cục tự động điều chỉnh theo kích thước màn hình</li>
                                  </ul>">
                        <h6>🔍 검색 및 필터링</h6>
                        <p><strong>Details 탭</strong>에서 직원 정보를 검색할 수 있습니다.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- FAQ -->
        <div class="tab-pane fade" id="help-faq">
            <div class="card">
                <div class="card-header bg-warning">
                    <h5 class="mb-0 lang-help-title" data-ko="❓ 자주 묻는 질문 (FAQ)"
                        data-en="❓ Frequently Asked Questions" data-vi="❓ Câu hỏi thường gặp">
                        ❓ 자주 묻는 질문 (FAQ)
                    </h5>
                </div>
                <div class="card-body">
                    <div class="accordion" id="faqAccordion">
                        <!-- FAQ 1 -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button lang-faq-title" type="button" data-bs-toggle="collapse" data-bs-target="#faq1"
                                        data-ko="Q1. 데이터는 얼마나 자주 업데이트되나요?"
                                        data-en="Q1. How often is the data updated?"
                                        data-vi="Q1. Dữ liệu được cập nhật bao lâu một lần?">
                                    Q1. 데이터는 얼마나 자주 업데이트되나요?
                                </button>
                            </h2>
                            <div id="faq1" class="accordion-collapse collapse show">
                                <div class="accordion-body lang-faq-content"
                                     data-ko="<strong>답변</strong>: 출석 데이터는 일별로 업데이트되며, 기타 인사 정보는 실시간으로 반영됩니다. 대시보드는 매일 오전 6시에 자동으로 재생성됩니다."
                                     data-en="<strong>Answer</strong>: Attendance data is updated daily, and other HR information is reflected in real-time. The dashboard is automatically regenerated daily at 6 AM."
                                     data-vi="<strong>Trả lời</strong>: Dữ liệu chấm công được cập nhật hàng ngày và thông tin nhân sự khác được phản ánh theo thời gian thực. Bảng điều khiển tự động được tạo lại hàng ngày vào lúc 6 giờ sáng.">
                                    <strong>답변</strong>: 출석 데이터는 일별로 업데이트됩니다.
                                </div>
                            </div>
                        </div>

                        <!-- FAQ 2 -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-faq-title" type="button" data-bs-toggle="collapse" data-bs-target="#faq2"
                                        data-ko="Q2. 언어 설정은 어떻게 변경하나요?"
                                        data-en="Q2. How do I change the language settings?"
                                        data-vi="Q2. Làm thế nào để thay đổi cài đặt ngôn ngữ?">
                                    Q2. 언어 설정은 어떻게 변경하나요?
                                </button>
                            </h2>
                            <div id="faq2" class="accordion-collapse collapse">
                                <div class="accordion-body lang-faq-content"
                                     data-ko="<strong>답변</strong>: 대시보드 우측 상단의 국기 아이콘(🇰🇷/🇺🇸/🇻🇳)을 클릭하면 언어가 즉시 전환됩니다. 선택한 언어는 브라우저에 저장되어 다음 방문 시에도 유지됩니다."
                                     data-en="<strong>Answer</strong>: Click the flag icon (🇰🇷/🇺🇸/🇻🇳) in the top right corner to instantly switch languages. Your language preference is saved in the browser and persists across visits."
                                     data-vi="<strong>Trả lời</strong>: Nhấp vào biểu tượng cờ (🇰🇷/🇺🇸/🇻🇳) ở góc trên bên phải để chuyển đổi ngôn ngữ ngay lập tức. Tùy chọn ngôn ngữ của bạn được lưu trong trình duyệt và duy trì qua các lần truy cập.">
                                    <strong>답변</strong>: 우측 상단의 국기 아이콘을 클릭하세요.
                                </div>
                            </div>
                        </div>

                        <!-- FAQ 3 -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-faq-title" type="button" data-bs-toggle="collapse" data-bs-target="#faq3"
                                        data-ko="Q3. 데이터를 내보낼 수 있나요?"
                                        data-en="Q3. Can I export data?"
                                        data-vi="Q3. Tôi có thể xuất dữ liệu không?">
                                    Q3. 데이터를 내보낼 수 있나요?
                                </button>
                            </h2>
                            <div id="faq3" class="accordion-collapse collapse">
                                <div class="accordion-body lang-faq-content"
                                     data-ko="<strong>답변</strong>: 네, <strong>Details 탭</strong>에서 직원 데이터를 내보낼 수 있습니다. 테이블 상단의 'CSV 내보내기' 또는 'JSON 내보내기' 버튼을 클릭하세요."
                                     data-en="<strong>Answer</strong>: Yes, you can export employee data from the <strong>Details tab</strong>. Click the 'Export CSV' or 'Export JSON' button above the table."
                                     data-vi="<strong>Trả lời</strong>: Có, bạn có thể xuất dữ liệu nhân viên từ <strong>tab Chi tiết</strong>. Nhấp vào nút 'Xuất CSV' hoặc 'Xuất JSON' phía trên bảng.">
                                    <strong>답변</strong>: 네, Details 탭에서 CSV/JSON으로 내보낼 수 있습니다.
                                </div>
                            </div>
                        </div>

                        <!-- FAQ 4: Troubleshooting - Data shows 0 -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-faq-title" type="button" data-bs-toggle="collapse" data-bs-target="#faq4"
                                        data-ko="Q4. 일부 수치가 0으로 표시됩니다"
                                        data-en="Q4. Some metrics show 0"
                                        data-vi="Q4. Một số chỉ số hiển thị 0">
                                    Q4. 일부 수치가 0으로 표시됩니다
                                </button>
                            </h2>
                            <div id="faq4" class="accordion-collapse collapse">
                                <div class="accordion-body lang-faq-content"
                                     data-ko="<strong>답변</strong>: 이는 해당 월의 데이터 파일이 없거나 불완전할 때 발생합니다. 시스템은 가짜 데이터를 생성하지 않고, 데이터가 없으면 0 또는 빈 값을 표시합니다.<br><br>
                                              <strong>해결 방법</strong>:<br>
                                              1. input_files 폴더에 해당 월의 데이터 파일이 있는지 확인하세요<br>
                                              2. 파일 이름 형식이 올바른지 확인하세요 (예: 'basic manpower data 2024_09.csv')<br>
                                              3. 관리자에게 데이터 동기화를 요청하세요"
                                     data-en="<strong>Answer</strong>: This happens when data files for that month are missing or incomplete. The system does not generate fake data - it shows 0 or empty values when data is unavailable.<br><br>
                                              <strong>Solutions</strong>:<br>
                                              1. Check if data files exist in the input_files folder for that month<br>
                                              2. Verify file naming format is correct (e.g., 'basic manpower data 2024_09.csv')<br>
                                              3. Contact administrator for data synchronization"
                                     data-vi="<strong>Trả lời</strong>: Điều này xảy ra khi các tệp dữ liệu cho tháng đó bị thiếu hoặc không đầy đủ. Hệ thống không tạo dữ liệu giả - nó hiển thị 0 hoặc giá trị trống khi dữ liệu không có sẵn.<br><br>
                                              <strong>Giải pháp</strong>:<br>
                                              1. Kiểm tra xem các tệp dữ liệu có tồn tại trong thư mục input_files cho tháng đó không<br>
                                              2. Xác minh định dạng tên tệp đúng (ví dụ: 'basic manpower data 2024_09.csv')<br>
                                              3. Liên hệ quản trị viên để đồng bộ hóa dữ liệu">
                                    <strong>답변</strong>: 해당 월의 데이터 파일이 없을 때 발생합니다.
                                </div>
                            </div>
                        </div>

                        <!-- FAQ 5: Troubleshooting - Team not showing -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-faq-title" type="button" data-bs-toggle="collapse" data-bs-target="#faq5"
                                        data-ko="Q5. 내 팀이 목록에 없습니다"
                                        data-en="Q5. My team is not in the list"
                                        data-vi="Q5. Nhóm của tôi không có trong danh sách">
                                    Q5. 내 팀이 목록에 없습니다
                                </button>
                            </h2>
                            <div id="faq5" class="accordion-collapse collapse">
                                <div class="accordion-body lang-faq-content"
                                     data-ko="<strong>답변</strong>: 팀 목록은 Position 4th 필드를 기반으로 자동 분류됩니다.<br><br>
                                              <strong>확인 사항</strong>:<br>
                                              1. 직원의 Position 4th 필드가 올바르게 입력되었는지 확인하세요<br>
                                              2. 신규 팀은 시스템 설정 업데이트가 필요할 수 있습니다<br>
                                              3. '기타' 또는 'NEW' 카테고리에 분류되어 있을 수 있습니다"
                                     data-en="<strong>Answer</strong>: Teams are auto-classified based on the Position 4th field.<br><br>
                                              <strong>Check the following</strong>:<br>
                                              1. Verify the employee's Position 4th field is correctly entered<br>
                                              2. New teams may require system configuration updates<br>
                                              3. The team might be classified under 'Other' or 'NEW' category"
                                     data-vi="<strong>Trả lời</strong>: Các nhóm được tự động phân loại dựa trên trường Position 4th.<br><br>
                                              <strong>Kiểm tra những điều sau</strong>:<br>
                                              1. Xác minh trường Position 4th của nhân viên được nhập đúng<br>
                                              2. Các nhóm mới có thể yêu cầu cập nhật cấu hình hệ thống<br>
                                              3. Nhóm có thể được phân loại trong danh mục 'Khác' hoặc 'NEW'">
                                    <strong>답변</strong>: Position 4th 필드 기반으로 자동 분류됩니다.
                                </div>
                            </div>
                        </div>

                        <!-- FAQ 6: Troubleshooting - Numbers don't match -->
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed lang-faq-title" type="button" data-bs-toggle="collapse" data-bs-target="#faq6"
                                        data-ko="Q6. 수치가 다른 보고서와 다릅니다"
                                        data-en="Q6. Numbers don't match other reports"
                                        data-vi="Q6. Số liệu không khớp với báo cáo khác">
                                    Q6. 수치가 다른 보고서와 다릅니다
                                </button>
                            </h2>
                            <div id="faq6" class="accordion-collapse collapse">
                                <div class="accordion-body lang-faq-content"
                                     data-ko="<strong>답변</strong>: 수치 차이는 다음 이유로 발생할 수 있습니다:<br><br>
                                              1. <strong>기준일 차이</strong>: 대시보드는 월말 기준, 다른 보고서는 다른 기준일 사용<br>
                                              2. <strong>계산 방식 차이</strong>: 결근율에서 출산휴가 제외 여부 등<br>
                                              3. <strong>데이터 갱신 시점</strong>: 실시간 vs 일별 업데이트<br>
                                              4. <strong>필터 조건</strong>: 정규직만 vs 전체 직원 등<br><br>
                                              헤더의 '📅 기준일'을 확인하고, 상세 KPI 정의는 KPI 지표 탭을 참조하세요."
                                     data-en="<strong>Answer</strong>: Differences may occur due to:<br><br>
                                              1. <strong>Reference date</strong>: Dashboard uses month-end, other reports may use different dates<br>
                                              2. <strong>Calculation method</strong>: Whether maternity leave is excluded from absence rate, etc.<br>
                                              3. <strong>Data refresh timing</strong>: Real-time vs daily updates<br>
                                              4. <strong>Filter conditions</strong>: Full-time only vs all employees, etc.<br><br>
                                              Check the '📅 Report Date' in the header, and refer to the KPI Metrics tab for detailed definitions."
                                     data-vi="<strong>Trả lời</strong>: Sự khác biệt có thể xảy ra do:<br><br>
                                              1. <strong>Ngày tham chiếu</strong>: Bảng điều khiển sử dụng cuối tháng, báo cáo khác có thể sử dụng ngày khác<br>
                                              2. <strong>Phương pháp tính toán</strong>: Có loại trừ nghỉ thai sản khỏi tỷ lệ vắng mặt không, v.v.<br>
                                              3. <strong>Thời gian làm mới dữ liệu</strong>: Thời gian thực vs cập nhật hàng ngày<br>
                                              4. <strong>Điều kiện lọc</strong>: Chỉ toàn thời gian vs tất cả nhân viên, v.v.<br><br>
                                              Kiểm tra '📅 Ngày báo cáo' trong tiêu đề và tham khảo tab Chỉ số KPI để biết định nghĩa chi tiết.">
                                    <strong>답변</strong>: 기준일, 계산 방식, 갱신 시점 차이로 발생합니다.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.help-section {
    padding: 20px;
}

.help-section .nav-pills .nav-link {
    border-radius: 20px;
    margin: 0 5px;
    font-weight: 500;
}

.help-section .nav-pills .nav-link.active {
    background-color: #0d6efd;
}

.help-section .card {
    box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
    margin-bottom: 20px;
}

.help-section .accordion-button:not(.collapsed) {
    background-color: #e7f1ff;
    color: #0d6efd;
}

.help-section h6 {
    color: #0d6efd;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 10px;
}

.help-section ul {
    margin-left: 20px;
}

.help-section li {
    margin-bottom: 8px;
}
</style>
"""

    def _generate_enhanced_modals(self) -> str:
        """
        Generate enhanced management-focused modals for critical KPIs
        중요 KPI에 대한 향상된 관리 중심 모달 생성
        """
        enhanced_modals = []

        # Get current month data
        month_data = self.collector.load_month_data(self.target_month)
        current_data = month_data.get('basic_manpower', pd.DataFrame())

        # Get historical data
        historical_data = {}
        for month in self.available_months:
            month_dict = self.collector.load_month_data(month)
            historical_data[month] = month_dict.get('basic_manpower', pd.DataFrame())

        # Get attendance data
        attendance_data = month_data.get('attendance', pd.DataFrame())

        # Critical KPIs that need enhanced modals
        critical_kpis = [
            ('modal_resignation_enhanced', 'resignation_rate', 'Resignation Rate Management'),
            ('modal_absence_enhanced', 'absence_rate', 'Absence Rate Management'),
            ('modal_unauthorized_enhanced', 'unauthorized_absence_rate', 'Unauthorized Absence Management'),
            ('modal_early_resignation_enhanced', 'early_resignation_30', 'Early Resignation Risk Management')
        ]

        for modal_id, metric_id, title in critical_kpis:
            try:
                enhanced_modal = self.modal_generator.generate_enhanced_modal(
                    modal_id=modal_id,
                    metric_id=metric_id,
                    current_data=current_data,
                    historical_data=historical_data,
                    attendance_data=attendance_data
                )
                enhanced_modals.append(enhanced_modal)
            except Exception as e:
                self.logger.error(f"Error generating enhanced modal for {metric_id}", error=str(e))

        return '\n'.join(enhanced_modals)

    def _generate_modals(self) -> str:
        """Generate modals with detailed data, charts, and language support"""
        modals_html = []

        # Add enhanced modals for critical KPIs
        enhanced_modals = self._generate_enhanced_modals()
        modals_html.append(enhanced_modals)

        # Modal 1: Total Employees (Enhanced with 4 charts - weekly, teams, types, change)
        modals_html.append("""
<div class="modal fade" id="modal1" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="총 재직자 수 상세 분석" data-en="Total Employees Analysis" data-vi="Phân tích số nhân viên">총 재직자 수 상세 분석</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="modalContent1">
                <!-- Charts will be dynamically generated by JavaScript -->
                <!-- 1. 월별 총 재직자 수 트렌드 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="월별 총 재직자 수 트렌드" data-en="Monthly Employee Trend" data-vi="Xu hướng nhân viên hàng tháng">월별 총 재직자 수 트렌드</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart1_monthly"></canvas>
                    </div>
                </div>
                <!-- 2. 주차별 총 재직자 수 트렌드 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="주차별 총 재직자 수 트렌드" data-en="Weekly Employee Trend" data-vi="Xu hướng nhân viên hàng tuần">주차별 총 재직자 수 트렌드</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart1_weekly"></canvas>
                    </div>
                </div>
                <!-- 3. 팀별 재직자 수 분포 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="팀별 재직자 수 분포" data-en="Distribution by Team" data-vi="Phân bổ theo nhóm">팀별 재직자 수 분포</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart1_teams"></canvas>
                    </div>
                </div>
                <!-- 4. 팀별 인원 변화 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="팀별 인원 변화 (전월 대비)" data-en="Team Changes (Month-over-Month)" data-vi="Thay đổi theo nhóm">팀별 인원 변화 (전월 대비)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart1_change"></canvas>
                    </div>
                </div>
                <!-- 6. Treemap Chart and Table Container -->
                <div id="treemapContainer" class="mt-4" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <!-- Will be populated by JavaScript -->
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 2: Absence Rate (Unified Structure) - Maternity Excluded
        modals_html.append("""
<div class="modal fade" id="modal2" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="결근율 상세 분석 (출산휴가 제외)" data-en="Absence Rate Analysis (excl. Maternity)" data-vi="Phân tích vắng mặt (không bao gồm thai sản)">결근율 상세 분석 (출산휴가 제외)</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- Summary Metrics Section -->
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="card bg-primary bg-gradient text-white">
                            <div class="card-body">
                                <h6 class="card-title lang-text" data-ko="결근율 (출산휴가 제외)" data-en="Absence Rate (excl. Maternity)" data-vi="Tỷ lệ vắng mặt (không bao gồm thai sản)">결근율 (출산휴가 제외)</h6>
                                <h2 class="mb-0" id="maternityExcludedRate">-</h2>
                                <p class="mb-0 mt-2" style="font-size: 0.9rem;" id="maternityExcludedCount">-</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 1. 주차별 결근율 트렌드 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="주차별 결근율 트렌드 (출산휴가 제외, 20주)" data-en="Weekly Absence Trend (excl. Maternity, 20 weeks)" data-vi="Xu hướng vắng mặt hàng tuần (không bao gồm thai sản)">주차별 결근율 트렌드 (출산휴가 제외, 20주)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart2_weekly"></canvas>
                    </div>
                </div>

                <!-- Daily absence rate chart -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="최근 30일 일별 결근율 (출산휴가 제외)" data-en="Daily Absence Rate (excl. Maternity, Last 30 Days)" data-vi="Tỷ lệ vắng mặt hàng ngày (không bao gồm thai sản)">최근 30일 일별 결근율 (출산휴가 제외)</h6>
                    <div style="height: 350px; position: relative;">
                        <canvas id="modalChart2_daily"></canvas>
                    </div>
                </div>

                <!-- 2. 팀별 결근율 분포 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="팀별 결근율 분포 (출산휴가 제외)" data-en="Absence Rate by Team (excl. Maternity)" data-vi="Tỷ lệ vắng mặt theo nhóm (không bao gồm thai sản)">팀별 결근율 분포 (출산휴가 제외)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart2_teams"></canvas>
                    </div>
                </div>

                <!-- 3. 타입별 결근율 현황 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="TYPE별 결근율 현황 (출산휴가 제외)" data-en="Absence Rate by TYPE (excl. Maternity)" data-vi="Tỷ lệ vắng mặt theo TYPE (không bao gồm thai sản)">TYPE별 결근율 현황 (출산휴가 제외)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart2_types"></canvas>
                    </div>
                </div>

                <!-- 4. 팀별 결근율 전월 대비 변화 (Bar) -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="팀별 결근율 변화 (9월 vs 10월)" data-en="Team Changes (Sep vs Oct)" data-vi="Thay đổi theo nhóm">팀별 결근율 변화 (9월 vs 10월)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart2_change"></canvas>
                    </div>
                </div>

                <!-- 결근 사유 분석 섹션 (Absence Reason Analysis) -->
                <div class="mt-5 mb-3">
                    <h5 class="lang-section-title" data-ko="📊 결근 사유 분석" data-en="📊 Absence Reason Analysis" data-vi="📊 Phân tích lý do vắng mặt">📊 결근 사유 분석</h5>
                    <hr>
                </div>

                <!-- 5. 결근 사유 분포 (Doughnut) -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="결근 사유 분포 (당월)" data-en="Absence Reason Distribution (Current Month)" data-vi="Phân bố lý do vắng mặt (Tháng hiện tại)">결근 사유 분포 (당월)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart2_reasonDistribution"></canvas>
                    </div>
                </div>

                <!-- 6. 월별 결근 사유 추이 (Stacked Bar) -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="월별 결근 사유 추이 (최근 6개월)" data-en="Monthly Absence Reason Trends (Last 6 Months)" data-vi="Xu hướng lý do vắng mặt hàng tháng (6 tháng gần nhất)">월별 결근 사유 추이 (최근 6개월)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart2_reasonTrends"></canvas>
                    </div>
                </div>

                <!-- 7. 팀별 결근 사유 분포 (Grouped Bar) -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="팀별 결근 사유 분포 (당월)" data-en="Team Absence Reason Distribution (Current Month)" data-vi="Phân bố lý do vắng mặt theo nhóm (Tháng hiện tại)">팀별 결근 사유 분포 (당월)</h6>
                    <div style="height: 450px; position: relative;">
                        <canvas id="modalChart2_teamReasons"></canvas>
                    </div>
                </div>

                <!-- 8. Treemap + Table -->
                <div id="treemapContainer2" class="mt-4" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 3: Unauthorized Absence (Custom with maternity exclusion)
        modals_html.append("""
<div class="modal fade" id="modal3" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="무단결근율 상세 분석" data-en="Unauthorized Absence Analysis" data-vi="Vắng không phép">무단결근율 상세 분석</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- Multi-faceted Dashboard Layout -->
                <div class="row">
                    <!-- Panel 1: Trend Analysis with Anomaly Detection -->
                    <div class="col-lg-6 mb-4">
                        <div class="card shadow-sm">
                            <div class="card-header bg-gradient-primary text-white">
                                <h6 class="mb-0">📈 무단결근율 추이 분석 (Trend Analysis)</h6>
                            </div>
                            <div class="card-body">
                                <!-- Summary Cards -->
                                <div class="row mb-3">
                                    <div class="col-6">
                                        <div class="alert alert-danger d-flex align-items-center py-2">
                                            <div>
                                                <small class="text-muted">전체 무단결근율<br>Overall Unauthorized Rate</small>
                                                <h4 class="mb-0" id="overallUnauthorizedRate">-</h4>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="alert alert-warning d-flex align-items-center py-2">
                                            <div>
                                                <small class="text-muted">평균 대비</small>
                                                <h4 class="mb-0" id="vsAverage">-</h4>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <!-- Trend Chart -->
                                <div style="height: 350px; position: relative;">
                                    <canvas id="modalChart3_trend"></canvas>
                                </div>
                                <div id="anomalyAlerts" class="mt-2">
                                    <!-- Anomaly alerts populated by JavaScript -->
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Panel 2: Team Comparison (Diverging Bar Chart) -->
                    <div class="col-lg-6 mb-4">
                        <div class="card shadow-sm">
                            <div class="card-header bg-gradient-info text-white">
                                <h6 class="mb-0">🏢 팀별 무단결근율 비교 (Team Comparison)</h6>
                            </div>
                            <div class="card-body">
                                <div style="height: 400px; position: relative;">
                                    <canvas id="modalChart3_diverging"></canvas>
                                </div>
                                <div class="text-center mt-2">
                                    <span class="badge bg-success">평균 이하</span>
                                    <span class="badge bg-secondary mx-2">평균: <span id="teamAverage">0.34%</span></span>
                                    <span class="badge bg-danger">평균 초과</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Panel 3: Absence Type Distribution -->
                    <div class="col-lg-6 mb-4">
                        <div class="card shadow-sm">
                            <div class="card-header bg-gradient-warning text-white">
                                <h6 class="mb-0">📊 결근 유형 분포 (Absence Type Distribution)</h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-5">
                                        <canvas id="modalChart3_donut" style="max-height: 200px;"></canvas>
                                    </div>
                                    <div class="col-7">
                                        <table class="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>유형 (Type)</th>
                                                    <th>건수</th>
                                                    <th>비율</th>
                                                </tr>
                                            </thead>
                                            <tbody id="absenceTypeTable">
                                                <tr>
                                                    <td><span class="badge bg-danger">TYPE-1</span> 무단결근</td>
                                                    <td id="type1Count">-</td>
                                                    <td id="type1Rate">-</td>
                                                </tr>
                                                <tr>
                                                    <td><span class="badge bg-warning">TYPE-2</span> 병가</td>
                                                    <td id="type2Count">-</td>
                                                    <td id="type2Rate">-</td>
                                                </tr>
                                                <tr>
                                                    <td><span class="badge bg-success">TYPE-3</span> 승인결근</td>
                                                    <td id="type3Count">-</td>
                                                    <td id="type3Rate">-</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Panel 4: Key Metrics Cards -->
                    <div class="col-lg-6 mb-4">
                        <div class="card shadow-sm">
                            <div class="card-header bg-gradient-success text-white">
                                <h6 class="mb-0">📌 핵심 지표 (Key Metrics)</h6>
                            </div>
                            <div class="card-body">
                                <div class="row g-2">
                                    <div class="col-6">
                                        <div class="metric-card p-3 border rounded bg-light">
                                            <small class="text-muted d-block">최고 무단결근 팀</small>
                                            <strong class="d-block" id="highestTeam">-</strong>
                                            <span class="text-danger" id="highestRate">-</span>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="metric-card p-3 border rounded bg-light">
                                            <small class="text-muted d-block">최저 무단결근 팀</small>
                                            <strong class="d-block" id="lowestTeam">-</strong>
                                            <span class="text-success" id="lowestRate">-</span>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="metric-card p-3 border rounded bg-light">
                                            <small class="text-muted d-block">데이터 신뢰도</small>
                                            <div class="progress" style="height: 20px;">
                                                <div class="progress-bar bg-info" role="progressbar" style="width: 95%">95%</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-6">
                                        <div class="metric-card p-3 border rounded bg-light">
                                            <small class="text-muted d-block">이상치 검출</small>
                                            <strong class="d-block text-warning" id="anomalyCount">0개 팀</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Detailed Team Table -->
                <div class="card shadow-sm">
                    <div class="card-header bg-gradient-secondary text-white">
                        <h6 class="mb-0">📋 팀별 상세 현황 (Detailed Team Status)</h6>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th scope="col">팀명 (Team)</th>
                                        <th scope="col">무단결근율 (Rate)</th>
                                        <th scope="col">총 인원 (Total)</th>
                                        <th scope="col">무단결근자 (Unauthorized)</th>
                                        <th scope="col">전월 대비 (vs Previous)</th>
                                        <th scope="col">상태 (Status)</th>
                                    </tr>
                                </thead>
                                <tbody id="teamDetailTable">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 4: Resignation Rate (Unified)
        modals_html.append("""
<div class="modal fade" id="modal4" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="퇴사율 상세 분석" data-en="Resignation Rate Analysis" data-vi="Tỷ lệ nghỉ việc">퇴사율 상세 분석</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- 1. 주차별 퇴사율 트렌드 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="주차별 퇴사율 트렌드 (20주)" data-en="Weekly Resignation Rate Trend" data-vi="Xu hướng nghỉ việc hàng tuần">주차별 퇴사율 트렌드 (20주)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart4_weekly"></canvas>
                    </div>
                </div>

                <!-- 2. 팀별 퇴사율 분포 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="팀별 퇴사율 분포" data-en="Resignation Rate by Team" data-vi="Nghỉ việc theo nhóm">팀별 퇴사율 분포</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart4_teams"></canvas>
                    </div>
                </div>

                <!-- 3. TYPE별 퇴사율 현황 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="TYPE별 퇴사율 현황" data-en="Resignation Rate by TYPE" data-vi="Nghỉ việc theo TYPE">TYPE별 퇴사율 현황</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart4_types"></canvas>
                    </div>
                </div>

                <!-- 4. 팀별 퇴사율 전월 대비 변화 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="팀별 퇴사율 변화 (9월 vs 10월)" data-en="Team Resignation Rate Changes" data-vi="Thay đổi nghỉ việc">팀별 퇴사율 변화 (9월 vs 10월)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart4_change"></canvas>
                    </div>
                </div>

                <!-- 5 & 6. Treemap + Table -->
                <div id="treemapContainer4" class="mt-4" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 5: Recent Hires (CUSTOM COMPREHENSIVE ANALYSIS)
        modals_html.append("""
<div class="modal fade" id="modal5" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="신규 입사자 종합 분석" data-en="Recent Hires Comprehensive Analysis" data-vi="Phân tích toàn diện nhân viên mới">신규 입사자 종합 분석</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- Overview Cards -->
                <div class="row mb-4" id="recentHiresOverview">
                    <!-- Populated by JavaScript -->
                </div>

                <!-- Hiring Trends Section -->
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="modal-chart-container">
                            <h6 class="lang-chart-title" data-ko="월별 신규 입사자 트렌드 (최근 6개월)" data-en="Monthly Hiring Trend (Last 6 Months)" data-vi="Xu hướng tuyển dụng hàng tháng">월별 신규 입사자 트렌드 (최근 6개월)</h6>
                            <div style="height: 300px; position: relative;">
                                <canvas id="recentHiresMonthlyTrendChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="modal-chart-container">
                            <h6 class="lang-chart-title" data-ko="주별 신규 입사자 트렌드 (최근 12주)" data-en="Weekly Hiring Trend (Last 12 Weeks)" data-vi="Xu hướng tuyển dụng hàng tuần">주별 신규 입사자 트렌드 (최근 12주)</h6>
                            <div style="height: 300px; position: relative;">
                                <canvas id="recentHiresWeeklyTrendChart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="modal-chart-container">
                            <h6 class="lang-chart-title" data-ko="일별 신규 입사자 (당월)" data-en="Daily Hiring (Current Month)" data-vi="Tuyển dụng hàng ngày">일별 신규 입사자 (당월)</h6>
                            <div style="height: 300px; position: relative;">
                                <canvas id="recentHiresDailyTrendChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Performance Metrics Section -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="modal-chart-container">
                            <h6 class="lang-chart-title" data-ko="신규 입사자 결근율 비교" data-en="New Hires Absence Rate Comparison" data-vi="So sánh tỷ lệ vắng mặt">신규 입사자 결근율 비교</h6>
                            <div style="height: 400px; position: relative;">
                                <canvas id="recentHiresAbsenceChart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="modal-chart-container">
                            <h6 class="lang-chart-title" data-ko="신규 입사자 결근 사유 분포" data-en="New Hires Absence Reasons" data-vi="Lý do vắng mặt">신규 입사자 결근 사유 분포</h6>
                            <div style="height: 400px; position: relative;">
                                <canvas id="recentHiresReasonsChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Retention Analysis Section -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="modal-chart-container">
                            <h6 class="lang-chart-title" data-ko="조기 퇴사율 분석" data-en="Early Resignation Analysis" data-vi="Phân tích nghỉ việc sớm">조기 퇴사율 분석</h6>
                            <div style="height: 400px; position: relative;">
                                <canvas id="recentHiresRetentionChart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="modal-chart-container">
                            <h6 class="lang-chart-title" data-ko="팀별 신규 입사자 분포" data-en="New Hires by Team" data-vi="Nhân viên mới theo nhóm">팀별 신규 입사자 분포</h6>
                            <div style="height: 400px; position: relative;">
                                <canvas id="recentHiresTeamChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Hires Detail Table -->
                <div class="modal-chart-container">
                    <h6 class="lang-chart-title" data-ko="신규 입사자 상세 정보" data-en="Recent Hires Details" data-vi="Chi tiết nhân viên mới">신규 입사자 상세 정보</h6>
                    <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                        <table class="table table-hover table-sm" style="font-size: 13px;">
                            <thead class="table-light" style="position: sticky; top: 0; z-index: 10;">
                                <tr>
                                    <th class="lang-text" data-ko="사번" data-en="ID" data-vi="Mã">사번</th>
                                    <th class="lang-text" data-ko="이름" data-en="Name" data-vi="Tên">이름</th>
                                    <th class="lang-text" data-ko="팀" data-en="Team" data-vi="Nhóm">팀</th>
                                    <th class="lang-text" data-ko="직급" data-en="Position" data-vi="Chức vụ">직급</th>
                                    <th class="lang-text" data-ko="입사일" data-en="Hire Date" data-vi="Ngày vào">입사일</th>
                                    <th class="lang-text" data-ko="근속일" data-en="Tenure" data-vi="Thâm niên">근속일</th>
                                    <th class="lang-text" data-ko="결근율" data-en="Absence %" data-vi="Vắng %">결근율</th>
                                    <th class="lang-text" data-ko="무단결근율" data-en="Unauth %" data-vi="Không phép %">무단결근율</th>
                                    <th class="lang-text" data-ko="재직상태" data-en="Status" data-vi="Trạng thái">재직상태</th>
                                </tr>
                            </thead>
                            <tbody id="recentHiresTableBody">
                                <!-- Populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 6-12: Unified structure with 6 charts
        unified_modal_configs = [
            (6, "최근 퇴사자", "Recent Resignations", "Nghỉ việc gần đây", "recent_resignations"),
            (7, "60일 미만", "Under 60 Days", "Dưới 60 ngày", "under_60_days"),
            (8, "배정 후 퇴사", "Post-Assignment", "Sau phân công", "post_assignment_resignations"),
            (9, "개근 직원", "Perfect Attendance", "Chuyên cần hoàn hảo", "perfect_attendance"),
            (10, "장기근속자", "Long-term (1yr+)", "Lâu năm (1 năm+)", "long_term_employees"),
            (11, "데이터 오류", "Data Errors", "Lỗi dữ liệu", "data_errors"),
            (12, "임신 직원", "Pregnant Employees", "Nhân viên mang thai", "pregnant_employees")
        ]

        for modal_num, title_ko, title_en, title_vi, kpi_key in unified_modal_configs:
            modals_html.append(f"""
<div class="modal fade" id="modal{modal_num}" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="{title_ko} 상세 분석" data-en="{title_en} Analysis" data-vi="{title_vi}">{title_ko} 상세 분석</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- 1. 주차별 {title_ko} 트렌드 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="주차별 {title_ko} 트렌드 (20주)" data-en="Weekly {title_en} Trend" data-vi="Xu hướng {title_vi} hàng tuần">주차별 {title_ko} 트렌드 (20주)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart{modal_num}_weekly"></canvas>
                    </div>
                </div>

                <!-- 2. 팀별 {title_ko} 분포 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="팀별 {title_ko} 분포" data-en="{title_en} by Team" data-vi="{title_vi} theo nhóm">팀별 {title_ko} 분포</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart{modal_num}_teams"></canvas>
                    </div>
                </div>

                <!-- 3. 타입별 {title_ko} 현황 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="TYPE별 {title_ko} 현황" data-en="{title_en} by TYPE" data-vi="{title_vi} theo TYPE">TYPE별 {title_ko} 현황</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart{modal_num}_types"></canvas>
                    </div>
                </div>

                <!-- 4. 팀별 {title_ko} 전월 대비 변화 (Bar) -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="팀별 {title_ko} 변화 (9월 vs 10월)" data-en="Team {title_en} Changes" data-vi="Thay đổi {title_vi}">팀별 {title_ko} 변화 (9월 vs 10월)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart{modal_num}_change"></canvas>
                    </div>
                </div>

                <!-- 5 & 6. Treemap + Table -->
                <div id="treemapContainer{modal_num}" class="mt-4" style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Team Detail Modal for KPI Analysis (NEW - Universal Team Detail Modal)
        modals_html.append("""
<div class="modal fade" id="teamDetailModal" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <h5 class="modal-title" id="teamDetailModalTitle">팀 상세 분석</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- 1. 월별 팀 [KPI] 트렌드 (최근 6개월) -->
                <div class="modal-chart-container mb-4">
                    <h6 id="teamDetailChart1Title">월별 팀 트렌드 (최근 6개월)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="teamDetailChart_monthly"></canvas>
                    </div>
                </div>

                <!-- 2. 주차별 팀 [KPI] 트렌드 (20주) -->
                <div class="modal-chart-container mb-4">
                    <h6 id="teamDetailChart2Title">주차별 팀 트렌드 (20주)</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="teamDetailChart_weekly"></canvas>
                    </div>
                </div>

                <!-- 3. Interactive Treemap - 팀내 역할별 인원 분포 (Multi-Level) -->
                <div class="modal-chart-container mb-4">
                    <h6 id="teamDetailChart3Title">팀내 역할별 인원 분포 (Interactive Treemap)</h6>
                    <div style="background: #f8f9fa; border-radius: 8px; padding: 20px;">
                        <!-- Treemap Chart -->
                        <div id="teamDetailTreemap" style="width: 100%; height: 500px; background: #fff; border-radius: 4px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <!-- Populated by D3.js -->
                        </div>
                        <!-- Detail Table -->
                        <div id="teamDetailTreemapTable" style="max-height: 300px; overflow-y: auto; background: #fff; border-radius: 4px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <h6 style="margin-bottom: 10px; font-weight: 600; color: #495057;">상세 계층 구조</h6>
                            <table class="table table-sm table-hover" style="font-size: 0.85rem; margin-bottom: 0;">
                                <thead style="background: #e9ecef; position: sticky; top: 0; z-index: 10;">
                                    <tr>
                                        <th scope="col">역할 (Role)</th>
                                        <th scope="col">Position 3rd</th>
                                        <th scope="col">Position 4th</th>
                                        <th scope="col">인원</th>
                                        <th scope="col">비율</th>
                                        <th scope="col">전월 대비</th>
                                    </tr>
                                </thead>
                                <tbody id="treemapTableBody">
                                    <!-- Populated by JavaScript -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- 4. 팀내 역할별 [KPI] 현황 -->
                <div class="modal-chart-container mb-4">
                    <h6 id="teamDetailChart4Title">팀내 역할별 현황</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="teamDetailChart_roleBar"></canvas>
                    </div>
                </div>

                <!-- 5. 5단계 계층 구조 Sunburst 차트 -->
                <div class="modal-chart-container mb-4">
                    <h6 id="teamDetailChart5Title">5단계 계층 구조</h6>
                    <div id="teamDetailSunburst" style="min-height: 600px; background: #f8f9fa; padding: 30px; border-radius: 8px;">
                        <!-- Populated by JavaScript -->
                    </div>
                </div>

                <!-- 6. 팀원 상세 정보 -->
                <div class="modal-chart-container mb-4">
                    <h6 id="teamDetailChart6Title">팀원 상세 정보</h6>
                    <div class="table-responsive" style="max-height: 500px; overflow-y: auto;">
                        <table class="table table-sm table-hover" id="teamDetailMembersTable" style="font-size: 12px;">
                            <thead style="position: sticky; top: 0; background: #f1f3f5; z-index: 10;">
                                <tr>
                                    <th style="padding: 8px; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 0)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Role Category <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                    <th style="padding: 8px; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 1)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Position 1st <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                    <th style="padding: 8px; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 2)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Position 2nd <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                    <th style="padding: 8px; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 3)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Full Name <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                    <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 4)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Employee No <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                    <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 5)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Entrance Date <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                    <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 6)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Years of Service <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                    <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 7)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Working Days <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                    <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 8)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Absent Days <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                    <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; user-select: none; transition: background-color 0.2s;"
                                        onclick="sortTeamMemberTable(this, 9)"
                                        onmouseover="this.style.backgroundColor='#e1e5e8'"
                                        onmouseout="this.style.backgroundColor=''">
                                        Absence Rate (%) <span style="font-size: 10px; color: #666;">▼</span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody id="teamDetailMembersTableBody">
                                <!-- Populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
            </div>
        </div>
    </div>
</div>
""")

        # Team Dashboard Modal (1st Level Modal)
        modals_html.append("""
<div class="modal fade" id="teamDashboardModal" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <h5 class="modal-title" id="teamDashboardTitle">팀 대시보드</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- Team KPI Cards -->
                <div class="row mb-4" id="teamKPICards">
                    <div class="col-md-3">
                        <div class="card border-primary">
                            <div class="card-body text-center">
                                <h6 class="text-muted">총 팀원</h6>
                                <h3 id="teamTotalMembers">0</h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card border-success">
                            <div class="card-body text-center">
                                <h6 class="text-muted">평균 출근율</h6>
                                <h3 id="teamAvgAttendance">0%</h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card border-info">
                            <div class="card-body text-center">
                                <h6 class="text-muted">개근 직원</h6>
                                <h3 id="teamPerfectAttendance">0</h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card border-danger">
                            <div class="card-body text-center">
                                <h6 class="text-muted">고위험 직원</h6>
                                <h3 id="teamHighRisk">0</h3>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Team Charts -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h6>팀원 타입 분포</h6>
                        <canvas id="teamTypeDistributionChart" height="200"></canvas>
                    </div>
                    <div class="col-md-6">
                        <h6>팀원 출근 현황</h6>
                        <canvas id="teamAttendanceStatusChart" height="200"></canvas>
                    </div>
                </div>

                <!-- Team Members Table -->
                <h6 class="mb-3">팀원 목록</h6>
                <div class="table-responsive">
                    <table class="table table-sm table-hover">
                        <thead class="table-light">
                            <tr>
                                <th scope="col">사번</th>
                                <th scope="col">이름</th>
                                <th scope="col">직급</th>
                                <th scope="col">입사일</th>
                                <th scope="col">재직기간</th>
                                <th scope="col">출근율</th>
                                <th scope="col">상세</th>
                            </tr>
                        </thead>
                        <tbody id="teamMembersTableBody">
                            <!-- Populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
                <button type="button" class="btn btn-primary" onclick="exportTeamData()">팀 데이터 내보내기</button>
            </div>
        </div>
    </div>
</div>
""")

        # Employee Detail Modal
        modals_html.append("""
<div class="modal fade" id="employeeDetailModal" tabindex="-1" role="dialog" aria-labelledby="employeeDetailModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="employeeDetailModalLabel">
                    <span class="lang-modal-title" data-ko="직원 상세 정보" data-en="Employee Details" data-vi="Thông tin nhân viên">직원 상세 정보</span>
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="employeeDetailContent">
                <!-- Employee Basic Information Section -->
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        <h6 class="mb-0">
                            <span class="lang-section" data-ko="📋 기본 정보" data-en="📋 Basic Information" data-vi="📋 Thông tin cơ bản">📋 기본 정보</span>
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <table class="table table-sm table-borderless">
                                    <tr>
                                        <td class="text-muted" style="width: 40%;">
                                            <span class="lang-label" data-ko="사번" data-en="ID" data-vi="Mã NV">사번</span>:
                                        </td>
                                        <td id="empDetailId">-</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted">
                                            <span class="lang-label" data-ko="이름" data-en="Name" data-vi="Tên">이름</span>:
                                        </td>
                                        <td id="empDetailName">-</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted">
                                            <span class="lang-label" data-ko="직급" data-en="Position" data-vi="Vị trí">직급</span>:
                                        </td>
                                        <td id="empDetailPosition">-</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted">
                                            <span class="lang-label" data-ko="유형" data-en="Type" data-vi="Loại">유형</span>:
                                        </td>
                                        <td id="empDetailType">-</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted">
                                            <span class="lang-label" data-ko="팀" data-en="Team" data-vi="Nhóm">팀</span>:
                                        </td>
                                        <td id="empDetailTeam">-</td>
                                    </tr>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <table class="table table-sm table-borderless">
                                    <tr>
                                        <td class="text-muted" style="width: 40%;">
                                            <span class="lang-label" data-ko="건물" data-en="Building" data-vi="Tòa nhà">건물</span>:
                                        </td>
                                        <td id="empDetailBuilding">-</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted">
                                            <span class="lang-label" data-ko="라인" data-en="Line" data-vi="Dây chuyền">라인</span>:
                                        </td>
                                        <td id="empDetailLine">-</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted">
                                            <span class="lang-label" data-ko="상사" data-en="Boss" data-vi="Cấp trên">상사</span>:
                                        </td>
                                        <td id="empDetailBoss">-</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted">
                                            <span class="lang-label" data-ko="입사일" data-en="Entrance Date" data-vi="Ngày vào">입사일</span>:
                                        </td>
                                        <td id="empDetailEntrance">-</td>
                                    </tr>
                                    <tr>
                                        <td class="text-muted">
                                            <span class="lang-label" data-ko="재직기간" data-en="Tenure" data-vi="Thâm niên">재직기간</span>:
                                        </td>
                                        <td id="empDetailTenure">-</td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                        <div class="mt-2" id="empDetailStatusBadges">
                            <!-- Status badges will be inserted here -->
                        </div>
                    </div>
                </div>

                <!-- Attendance Information Section -->
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h6 class="mb-0">
                            <span class="lang-section" data-ko="📊 출결 정보 (해당월)" data-en="📊 Attendance Details (Current Month)" data-vi="📊 Chi tiết chuyên cần">📊 출결 정보 (해당월)</span>
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="row text-center mb-3">
                            <div class="col-md-3">
                                <div class="p-3 bg-light rounded">
                                    <div class="text-muted small">
                                        <span class="lang-label" data-ko="근무일수" data-en="Working Days" data-vi="Ngày làm việc">근무일수</span>
                                    </div>
                                    <div class="fs-4 fw-bold text-primary" id="empDetailWorkingDays">0</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3 bg-light rounded">
                                    <div class="text-muted small">
                                        <span class="lang-label" data-ko="결근일수" data-en="Absent Days" data-vi="Ngày vắng">결근일수</span>
                                    </div>
                                    <div class="fs-4 fw-bold text-danger" id="empDetailAbsentDays">0</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3 bg-light rounded">
                                    <div class="text-muted small">
                                        <span class="lang-label" data-ko="출석률" data-en="Attendance Rate" data-vi="Tỷ lệ chuyên cần">출석률</span>
                                    </div>
                                    <div class="fs-4 fw-bold text-success" id="empDetailAttendanceRate">0%</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="p-3 bg-light rounded">
                                    <div class="text-muted small">
                                        <span class="lang-label" data-ko="무단결근" data-en="Unauthorized" data-vi="Vắng không phép">무단결근</span>
                                    </div>
                                    <div class="fs-4 fw-bold" id="empDetailUnauthorized">-</div>
                                </div>
                            </div>
                        </div>

                        <div id="empDetailAttendanceInfo" class="mt-3">
                            <!-- Additional attendance details will be shown here -->
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    <span class="lang-btn" data-ko="닫기" data-en="Close" data-vi="Đóng">닫기</span>
                </button>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 13: Team Absence Breakdown (팀별 결근 분석)
        modals_html.append("""
<div class="modal fade" id="modal13" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="팀별 결근 분석 상세" data-en="Team Absence Analysis" data-vi="Phân tích vắng mặt theo nhóm">팀별 결근 분석 상세</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="modalContent13">
                <!-- Summary Cards -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card bg-danger bg-gradient text-white">
                            <div class="card-body">
                                <h6 class="card-title lang-text" data-ko="평균 전체 결근율" data-en="Avg Total Absence Rate" data-vi="Tỷ lệ vắng TB">평균 전체 결근율</h6>
                                <h2 class="mb-0" id="avgTotalAbsenceRate">-</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-warning bg-gradient text-white">
                            <div class="card-body">
                                <h6 class="card-title lang-text" data-ko="평균 무단 결근율" data-en="Avg Unauthorized Rate" data-vi="Tỷ lệ không phép TB">평균 무단 결근율</h6>
                                <h2 class="mb-0" id="avgUnauthorizedRate">-</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-info bg-gradient text-white">
                            <div class="card-body">
                                <h6 class="card-title lang-text" data-ko="평균 승인 결근율" data-en="Avg Authorized Rate" data-vi="Tỷ lệ có phép TB">평균 승인 결근율</h6>
                                <h2 class="mb-0" id="avgAuthorizedRate">-</h2>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Chart 1: 팀별 전체 결근율 비교 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="1️⃣ 팀별 전체 결근율 비교" data-en="1️⃣ Total Absence Rate by Team" data-vi="1️⃣ Tỷ lệ vắng tổng theo nhóm">1️⃣ 팀별 전체 결근율 비교</h6>
                    <div style="height: 400px; position: relative;">
                        <canvas id="modalChart13_totalRate"></canvas>
                    </div>
                </div>

                <!-- Chart 2: 팀별 무단 vs 승인 결근율 비교 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="2️⃣ 팀별 무단 vs 승인 결근율 비교" data-en="2️⃣ Unauthorized vs Authorized by Team" data-vi="2️⃣ Không phép vs Có phép theo nhóm">2️⃣ 팀별 무단 vs 승인 결근율 비교</h6>
                    <div style="height: 450px; position: relative;">
                        <canvas id="modalChart13_comparison"></canvas>
                    </div>
                </div>

                <!-- Chart 3: 팀별 결근 일수 분포 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="3️⃣ 팀별 결근 일수 분포 (무단 + 승인)" data-en="3️⃣ Absence Days Distribution by Team" data-vi="3️⃣ Phân bố ngày vắng theo nhóm">3️⃣ 팀별 결근 일수 분포 (무단 + 승인)</h6>
                    <div style="height: 450px; position: relative;">
                        <canvas id="modalChart13_days"></canvas>
                    </div>
                </div>

                <!-- Chart 4: 승인 결근 사유 세부 분석 -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="4️⃣ 팀별 승인 결근 사유 세부 분석" data-en="4️⃣ Authorized Absence Breakdown by Team" data-vi="4️⃣ Phân tích lý do có phép theo nhóm">4️⃣ 팀별 승인 결근 사유 세부 분석</h6>
                    <p class="text-muted small mb-3">
                        <span class="lang-text" data-ko="출산휴가, 연차, 병가, 기타 승인 사유별 일수" data-en="Maternity, Annual Leave, Sick Leave, Other Authorized" data-vi="Thai sản, Nghỉ phép, Nghỉ ốm, Khác có phép">출산휴가, 연차, 병가, 기타 승인 사유별 일수</span>
                    </p>
                    <div style="height: 450px; position: relative;">
                        <canvas id="modalChart13_authorizedBreakdown"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 14: Punctuality Issues (Come Late / Leave Early)
        # 모달 14: 지각/조퇴 현황
        modals_html.append("""
<div class="modal fade" id="modal14" tabindex="-1">
    <div class="modal-dialog modal-xl" style="max-width: 90%;">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="지각/조퇴 현황 상세" data-en="Punctuality Issues - Details" data-vi="Chi tiết đi muộn / về sớm">지각/조퇴 현황 상세</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="modalContent14">
                <!-- Summary Cards -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card bg-warning bg-gradient text-white">
                            <div class="card-body">
                                <h6 class="card-title lang-text" data-ko="지각 총 건수" data-en="Total Late Arrivals" data-vi="Tổng số lần đi muộn">지각 총 건수</h6>
                                <h2 class="mb-0" id="totalComeLate">-</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-info bg-gradient text-white">
                            <div class="card-body">
                                <h6 class="card-title lang-text" data-ko="조퇴 총 건수" data-en="Total Early Departures" data-vi="Tổng số lần về sớm">조퇴 총 건수</h6>
                                <h2 class="mb-0" id="totalLeaveEarly">-</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-danger bg-gradient text-white">
                            <div class="card-body">
                                <h6 class="card-title lang-text" data-ko="영향 받은 직원 수" data-en="Employees Affected" data-vi="Số nhân viên bị ảnh hưởng">영향 받은 직원 수</h6>
                                <h2 class="mb-0" id="punctualityAffected">-</h2>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Chart: Come Late vs Leave Early -->
                <div class="modal-chart-container mb-4">
                    <h6 class="lang-chart-title" data-ko="1️⃣ 지각 vs 조퇴 비교" data-en="1️⃣ Late Arrivals vs Early Departures" data-vi="1️⃣ Đi muộn vs Về sớm">1️⃣ 지각 vs 조퇴 비교</h6>
                    <div style="height: 300px; position: relative;">
                        <canvas id="modalChart14_comparison"></canvas>
                    </div>
                </div>

                <!-- Employee List with Punctuality Issues -->
                <div class="modal-chart-container">
                    <h6 class="lang-chart-title" data-ko="2️⃣ 지각/조퇴 직원 목록" data-en="2️⃣ Employees with Punctuality Issues" data-vi="2️⃣ Danh sách nhân viên đi muộn/về sớm">2️⃣ 지각/조퇴 직원 목록</h6>
                    <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark sticky-top">
                                <tr>
                                    <th class="lang-text" data-ko="사번" data-en="Employee No" data-vi="Mã NV">사번</th>
                                    <th class="lang-text" data-ko="이름" data-en="Name" data-vi="Tên">이름</th>
                                    <th class="lang-text" data-ko="부서" data-en="Department" data-vi="Phòng ban">부서</th>
                                    <th class="lang-text" data-ko="지각 건수" data-en="Late Count" data-vi="Số lần muộn">지각 건수</th>
                                    <th class="lang-text" data-ko="조퇴 건수" data-en="Early Count" data-vi="Số lần sớm">조퇴 건수</th>
                                    <th class="lang-text" data-ko="합계" data-en="Total" data-vi="Tổng">합계</th>
                                </tr>
                            </thead>
                            <tbody id="punctualityEmployeeList">
                                <!-- Populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Issue Summary Modal (for Executive Summary clickable items)
        # 이슈 요약 모달 (경영진 요약 클릭 항목용)
        modals_html.append("""
<div class="modal fade" id="issueSummaryModal" tabindex="-1" role="dialog" aria-labelledby="issueSummaryModalTitle" aria-hidden="true">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header bg-light">
                <h5 class="modal-title" id="issueSummaryModalTitle">이슈 상세</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body issue-modal-content" id="issueSummaryModalBody">
                <!-- Dynamic content will be inserted here -->
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    <span class="lang-text" data-ko="닫기" data-en="Close" data-vi="Đóng">닫기</span>
                </button>
            </div>
        </div>
    </div>
</div>
""")

        return '\n'.join(modals_html)

    def _generate_javascript(self) -> str:
        """Generate JavaScript for charts, interactivity, and modal management"""
        # Use string concatenation to set initial language from Python
        # 파이썬에서 초기 언어를 설정하기 위해 문자열 결합 사용
        return f"""
// ============================================
// Debug Mode & Security Utilities
// 디버그 모드 및 보안 유틸리티
// ============================================

const DEBUG_MODE = false;  // Set to true for development / 개발시 true로 설정

// Safe logging - only logs in debug mode
// 안전한 로깅 - 디버그 모드에서만 로그 출력
function debugLog(...args) {{
    if (DEBUG_MODE) console.log(...args);
}}

// HTML sanitization to prevent XSS
// XSS 방지를 위한 HTML 새니타이징
function sanitizeHTML(str) {{
    if (typeof str !== 'string') return str;
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}}

// Safe innerHTML setter - sanitizes unless content is trusted HTML
// 안전한 innerHTML 설정 - 신뢰할 수 있는 HTML이 아니면 새니타이징
function setInnerHTML(element, html, trusted = false) {{
    if (trusted) {{
        element.innerHTML = html;
    }} else {{
        element.innerHTML = sanitizeHTML(html);
    }}
}}

// ============================================
// Keyboard Navigation (P0 Accessibility Fix)
// 키보드 네비게이션 (P0 접근성 수정)
// ============================================

// Close modal with Escape key
// Escape 키로 모달 닫기
document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{
        // Close any open Bootstrap modal
        // 열려있는 Bootstrap 모달 닫기
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {{
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        }});

        // Close employee detail panel if open
        // 열려있는 직원 상세 패널 닫기
        const detailPanel = document.getElementById('employeeDetailPanel');
        if (detailPanel && detailPanel.classList.contains('show')) {{
            hideEmployeeDetail();
        }}
    }}
}});

// Focus trap for modals - keep focus within modal when open
// 모달 포커스 트랩 - 모달이 열려있을 때 포커스를 모달 내부에 유지
document.addEventListener('shown.bs.modal', function(e) {{
    const modal = e.target;
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusableElements.length > 0) {{
        focusableElements[0].focus();
    }}
}});

// ============================================
// Loading Indicator (P0 Fix)
// 로딩 인디케이터 (P0 수정)
// ============================================

let loadingCount = 0;

function showLoading(message) {{
    loadingCount++;
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {{
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-message" id="loadingMessage"></div>
        `;
        document.body.appendChild(overlay);
    }}
    const msgElem = document.getElementById('loadingMessage');
    if (msgElem && message) {{
        msgElem.textContent = message;
    }}
    overlay.classList.add('show');
}}

function hideLoading() {{
    loadingCount = Math.max(0, loadingCount - 1);
    if (loadingCount === 0) {{
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {{
            overlay.classList.remove('show');
        }}
    }}
}}

// ============================================
// Error Boundary (P0 Fix)
// 에러 경계 (P0 수정)
// ============================================

// Global error handler
// 전역 에러 핸들러
window.onerror = function(message, source, lineno, colno, error) {{
    console.error('Dashboard error:', {{ message, source, lineno, colno, error }});
    showError(message);
    return true; // Prevent default error handling / 기본 에러 처리 방지
}};

// Promise rejection handler
// Promise 거부 핸들러
window.onunhandledrejection = function(event) {{
    console.error('Unhandled promise rejection:', event.reason);
    showError(event.reason?.message || 'An unexpected error occurred');
}};

function showError(message) {{
    hideLoading(); // Clear any loading state / 로딩 상태 초기화

    let errorBoundary = document.getElementById('errorBoundary');
    if (!errorBoundary) {{
        errorBoundary = document.createElement('div');
        errorBoundary.id = 'errorBoundary';
        errorBoundary.className = 'error-boundary';
        document.body.insertBefore(errorBoundary, document.body.firstChild);
    }}

    const errorMessages = {{
        ko: 'オ류가 발생했습니다',
        en: 'An error occurred',
        vi: 'Đã xảy ra lỗi'
    }};

    const retryMessages = {{
        ko: '다시 시도',
        en: 'Retry',
        vi: 'Thử lại'
    }};

    const dismissMessages = {{
        ko: '닫기',
        en: 'Dismiss',
        vi: 'Đóng'
    }};

    errorBoundary.innerHTML = `
        <div class="error-boundary-content">
            <span class="error-boundary-icon">⚠️</span>
            <div>
                <strong>${{errorMessages[currentLanguage] || errorMessages.en}}</strong>
                <p>${{sanitizeHTML(message)}}</p>
            </div>
            <div class="error-boundary-actions">
                <button onclick="location.reload()" class="btn btn-primary btn-sm">
                    ${{retryMessages[currentLanguage] || retryMessages.en}}
                </button>
                <button onclick="dismissError()" class="btn btn-outline-secondary btn-sm">
                    ${{dismissMessages[currentLanguage] || dismissMessages.en}}
                </button>
            </div>
        </div>
    `;
    errorBoundary.style.display = 'block';
}}

function dismissError() {{
    const errorBoundary = document.getElementById('errorBoundary');
    if (errorBoundary) {{
        errorBoundary.style.display = 'none';
    }}
}}

// Safe function wrapper for error boundary
// 에러 경계를 위한 안전한 함수 래퍼
function safeExecute(fn, fallback = null) {{
    return function(...args) {{
        try {{
            return fn.apply(this, args);
        }} catch (error) {{
            console.error('Error in function:', error);
            showError(error.message);
            return fallback;
        }}
    }};
}}

// ============================================
// Language Switching
// ============================================

let currentLanguage = '{self.language}';
""" + """
function switchLanguage(lang) {
    currentLanguage = lang;

    // Update button states
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.lang === lang) {
            btn.classList.add('active');
        }
    });

    // Update all elements with language data attributes
    document.querySelectorAll('[data-ko]').forEach(elem => {
        if (elem.dataset[lang]) {
            if (elem.tagName === 'INPUT') {
                elem.placeholder = elem.dataset[lang];
            } else if (elem.classList.contains('lang-help-content') ||
                       elem.classList.contains('lang-kpi-content') ||
                       elem.classList.contains('lang-faq-content')) {
                // For help tab content with HTML
                elem.innerHTML = elem.dataset[lang];
            } else {
                elem.textContent = elem.dataset[lang];
            }
        }
    });

    // Update card titles and subtitles
    document.querySelectorAll('.lang-card-title').forEach(elem => {
        const subtitle = elem.querySelector('.lang-card-subtitle');
        if (subtitle) {
            elem.innerHTML = elem.dataset[lang] + '<br><small class="lang-card-subtitle" data-ko="' +
                elem.querySelector('.lang-card-subtitle').dataset.ko + '" data-en="' +
                elem.querySelector('.lang-card-subtitle').dataset.en + '" data-vi="' +
                elem.querySelector('.lang-card-subtitle').dataset.vi + '">' +
                subtitle.dataset[lang] + '</small>';
        }
    });

    // Save preference
    localStorage.setItem('dashboard_language', lang);

    debugLog(`✅ Language switched to: ${lang}`);
}

// Load saved language preference on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedLang = localStorage.getItem('dashboard_language');
    if (savedLang && ['ko', 'en', 'vi'].includes(savedLang)) {
        switchLanguage(savedLang);
    }
});

// ============================================
// Dashboard Download Function
// 대시보드 다운로드 기능
// ============================================

function downloadDashboard() {{
    // Get the current page HTML
    // 현재 페이지 HTML 가져오기
    const htmlContent = document.documentElement.outerHTML;

    // Create a Blob with the HTML content
    // HTML 콘텐츠로 Blob 생성
    const blob = new Blob([htmlContent], {{ type: 'text/html;charset=utf-8' }});

    // Create download link
    // 다운로드 링크 생성
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);

    // Generate filename with current date
    // 현재 날짜로 파일명 생성
    const now = new Date();
    const dateStr = now.toISOString().slice(0, 10);
    const pageTitle = document.title || 'HR_Dashboard';
    const filename = `${{pageTitle.replace(/[^a-zA-Z0-9가-힣_-]/g, '_')}}_${{dateStr}}.html`;

    link.download = filename;

    // Trigger download
    // 다운로드 실행
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up
    // 정리
    URL.revokeObjectURL(link.href);

    // Show success message based on current language
    // 현재 언어에 맞는 성공 메시지 표시
    const messages = {{
        ko: '✅ 대시보드가 다운로드되었습니다!',
        en: '✅ Dashboard downloaded successfully!',
        vi: '✅ Đã tải xuống bảng điều khiển!'
    }};

    // Create toast notification
    // 토스트 알림 생성
    showDownloadToast(messages[currentLanguage] || messages.ko, filename);

    debugLog(`📥 Dashboard downloaded: ${{filename}}`);
}}

function showDownloadToast(message, filename) {{
    // Create toast element
    // 토스트 요소 생성
    const toast = document.createElement('div');
    toast.className = 'download-toast';
    toast.innerHTML = `
        <div class="download-toast-icon">📥</div>
        <div class="download-toast-content">
            <div class="download-toast-message">${{message}}</div>
            <div class="download-toast-filename">${{filename}}</div>
        </div>
    `;

    // Add to document
    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Remove after 3 seconds
    setTimeout(() => {{
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }}, 3000);
}}

// ============================================
// Helper Functions
// ============================================

function getTrendData(metricKey) {
    return availableMonths.map(month => monthlyMetrics[month][metricKey]);
}

/**
 * 공통 날짜 파싱 함수 - 모든 날짜 처리에 사용
 * Common date parsing function - used for all date processing
 *
 * Handles:
 * - null, "nan", "null", "undefined" values
 * - "YYYY.DD.MM" format (converts to "YYYY-MM-DD")
 * - Standard date formats
 *
 * @param {{string|Date}} dateStr - Date string to parse
 * @returns {{Date|null}} Parsed Date object or null if invalid
 */
function parseDateSafe(dateStr) {{
    if (!dateStr || dateStr === 'nan' || dateStr === 'null' || dateStr === 'undefined') return null;

    // Handle "YYYY.DD.MM" format (dots as separators) - convert to "YYYY-MM-DD"
    // Example: "2025.05.10" → "2025-10-05" (October 5, 2025)
    if (typeof dateStr === 'string' && dateStr.includes('.')) {{
        const parts = dateStr.split('.');
        if (parts.length === 3) {{
            // YYYY.DD.MM -> YYYY-MM-DD
            const normalized = `${{parts[0]}}-${{parts[2]}}-${{parts[1]}}`;
            const d = new Date(normalized);
            if (!isNaN(d.getTime())) return d;
        }}
    }}

    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? null : d;
}}

/**
 * 공통 총 재직자 수 계산 함수 - 모든 차트와 KPI에서 사용
 * Common total employees calculation function - used by all charts and KPIs
 *
 * 기준: 기간 말일 기준으로 재직 중인 직원 수
 * Criteria: Employees active as of end-of-period date
 *
 * 로직:
 * - entrance_date <= 기준일 (Entrance date <= reference date)
 * - stop_date가 없거나 stop_date > 기준일 (No stop date OR stop date > reference date)
 *
 * @param {{Array}} members - Employee array
 * @param {{Date|string}} referenceDate - Reference date (end of period)
 * @returns {{number}} Count of active employees
 */
function countActiveEmployees(members, referenceDate) {{
    const refDate = parseDateSafe(referenceDate);
    if (!refDate) return 0;

    return members.filter(member => {{
        const entranceDate = parseDateSafe(member.entrance_date);
        const stopDate = parseDateSafe(member.stop_date);

        // Must have entrance date
        if (!entranceDate) return false;

        // Entrance date must be on or before reference date
        if (entranceDate > refDate) return false;

        // If no stop date or stop date is after reference date, employee is active
        return !stopDate || stopDate > refDate;
    }}).length;
}}

// ============================================
// Universal KPI Modal System
// ============================================

// KPI Configuration: Defines data structure and calculation for each KPI
const kpiConfig = {{
    total_employees: {{
        key: 'total_employees',
        nameKo: '총 재직자 수',
        nameEn: 'Total Employees',
        nameVi: 'Tổng số nhân viên',
        unit: '명',
        type: 'count',  // count or percentage
        weeklyKey: 'total_employees',
        calculateTeamValue: (teamMembers, monthData) => teamMembers.length,
        calculateTypeValue: (employees, monthData) => employees.length
    }},
    absence_rate: {{
        key: 'absence_rate',
        nameKo: '결근율',
        nameEn: 'Absence Rate',
        nameVi: 'Tỷ lệ vắng mặt',
        unit: '%',
        type: 'percentage',
        weeklyKey: 'absence_rate',
        calculateTeamValue: (teamMembers, monthData, teamName) => {{
            // Use team-specific absence rate if available
            if (monthData?.team_absence_rates && teamName) {{
                return monthData.team_absence_rates[teamName] || 0;
            }}

            // Calculate from team members
            if (!teamMembers || teamMembers.length === 0) return 0;

            let totalWorkingDays = 0;
            let totalAbsentDays = 0;

            teamMembers.forEach(member => {{
                const workingDays = parseFloat(member.working_days) || 0;
                const absentDays = parseFloat(member.absent_days) || 0;
                totalWorkingDays += workingDays;
                totalAbsentDays += absentDays;
            }});

            if (totalWorkingDays === 0) return 0;
            return parseFloat(((totalAbsentDays / totalWorkingDays) * 100).toFixed(1));
        }},
        calculateTypeValue: (employees, monthData) => {{
            return monthData?.absence_rate || 0;
        }}
    }},
    absence_rate_excl_maternity: {{
        key: 'absence_rate_excl_maternity',
        nameKo: '출산휴가 제외 결근율',
        nameEn: 'Absence Rate (excl. Maternity)',
        nameVi: 'Tỷ lệ vắng mặt (không bao gồm thai sản)',
        unit: '%',
        type: 'percentage',
        weeklyKey: 'absence_rate',  // Use same weekly key as absence_rate for now
        calculateTeamValue: (teamMembers, monthData, teamName) => {{
            // Use team-specific absence rate excluding maternity if available
            if (monthData?.team_absence_rates_excl_maternity && teamName) {{
                return monthData.team_absence_rates_excl_maternity[teamName] || 0;
            }}
            // Fallback to global rate
            return monthData?.absence_rate_excl_maternity || 0;
        }},
        calculateTypeValue: (employees, monthData, typeKey) => {{
            // Get TYPE-specific absence rate excluding maternity
            if (monthData?.type_absence_rates_excl_maternity && typeKey) {{
                return monthData.type_absence_rates_excl_maternity[typeKey] || 0;
            }}
            return monthData?.absence_rate_excl_maternity || 0;
        }}
    }},
    unauthorized_absence_rate: {{
        key: 'unauthorized_absence_rate',
        nameKo: '무단결근율',
        nameEn: 'Unauthorized Absence',
        nameVi: 'Vắng không phép',
        unit: '%',
        type: 'percentage',
        weeklyKey: 'absence_rate',  // Weekly metrics may not have this
        calculateTeamValue: (teamMembers, monthData, teamName) => {{
            // Use team-specific unauthorized absence rate if available
            if (monthData?.team_unauthorized_rates && teamName) {{
                return monthData.team_unauthorized_rates[teamName] || 0;
            }}
            // Fallback to global rate
            return monthData?.unauthorized_absence_rate || 0;
        }},
        calculateTypeValue: (employees, monthData) => monthData?.unauthorized_absence_rate || 0
    }},
    resignation_rate: {{
        key: 'resignation_rate',
        nameKo: '퇴사율',
        nameEn: 'Resignation Rate',
        nameVi: 'Tỷ lệ nghỉ việc',
        unit: '%',
        type: 'percentage',
        weeklyKey: 'resignations',
        calculateTeamValue: (teamMembers, monthData) => {{
            // Count members who resigned THIS MONTH (not all members with stop_date)
            const resignations = teamMembers.filter(m => {{
                if (!m.stop_date || m.stop_date === 'nan' || m.stop_date === '') return false;
                try {{
                    const stopDate = new Date(m.stop_date);
                    const targetDate = new Date(targetMonth + '-01');
                    return stopDate.getFullYear() === targetDate.getFullYear() &&
                           stopDate.getMonth() === targetDate.getMonth();
                }} catch (e) {{
                    return false;
                }}
            }}).length;

            // Total members at the start of the month (active + resigned this month)
            const totalMembers = teamMembers.length;
            return totalMembers > 0 ? parseFloat((resignations / totalMembers * 100).toFixed(1)) : 0;
        }},
        calculateTypeValue: (employees, monthData) => {{
            // Same logic for TYPE-level calculation
            const resignations = employees.filter(e => {{
                if (!e.stop_date || e.stop_date === 'nan' || e.stop_date === '') return false;
                try {{
                    const stopDate = new Date(e.stop_date);
                    const targetDate = new Date(targetMonth + '-01');
                    return stopDate.getFullYear() === targetDate.getFullYear() &&
                           stopDate.getMonth() === targetDate.getMonth();
                }} catch (e) {{
                    return false;
                }}
            }}).length;

            const totalEmployees = employees.length;
            return totalEmployees > 0 ? parseFloat((resignations / totalEmployees * 100).toFixed(1)) : 0;
        }}
    }},
    recent_hires: {{
        key: 'recent_hires',
        nameKo: '신규 입사자',
        nameEn: 'Recent Hires',
        nameVi: 'Nhân viên mới',
        unit: '명',
        type: 'count',
        weeklyKey: 'new_hires',
        calculateTeamValue: (teamMembers, monthData) => {{
            // Count members who joined this month
            return teamMembers.filter(m => {{
                if (!m.entrance_date) return false;
                const entranceDate = new Date(m.entrance_date);
                const targetDate = new Date(targetMonth + '-01');
                return entranceDate.getFullYear() === targetDate.getFullYear() &&
                       entranceDate.getMonth() === targetDate.getMonth();
            }}).length;
        }},
        calculateTypeValue: (employees, monthData) => {{
            return employees.filter(e => {{
                if (!e.entrance_date) return false;
                const entranceDate = new Date(e.entrance_date);
                const targetDate = new Date(targetMonth + '-01');
                return entranceDate.getFullYear() === targetDate.getFullYear() &&
                       entranceDate.getMonth() === targetDate.getMonth();
            }}).length;
        }}
    }},
    recent_resignations: {{
        key: 'recent_resignations',
        nameKo: '최근 퇴사자',
        nameEn: 'Recent Resignations',
        nameVi: 'Nghỉ việc gần đây',
        unit: '명',
        type: 'count',
        weeklyKey: 'resignations',
        calculateTeamValue: (teamMembers, monthData) => {{
            return teamMembers.filter(m => {{
                if (!m.stop_date) return false;
                const stopDate = new Date(m.stop_date);
                const targetDate = new Date(targetMonth + '-01');
                return stopDate.getFullYear() === targetDate.getFullYear() &&
                       stopDate.getMonth() === targetDate.getMonth();
            }}).length;
        }},
        calculateTypeValue: (employees, monthData) => {{
            return employees.filter(e => {{
                if (!e.stop_date) return false;
                const stopDate = new Date(e.stop_date);
                const targetDate = new Date(targetMonth + '-01');
                return stopDate.getFullYear() === targetDate.getFullYear() &&
                       stopDate.getMonth() === targetDate.getMonth();
            }}).length;
        }}
    }},
    under_60_days: {{
        key: 'under_60_days',
        nameKo: '60일 미만',
        nameEn: 'Under 60 Days',
        nameVi: 'Dưới 60 ngày',
        unit: '명',
        type: 'count',
        weeklyKey: 'total_employees',  // No specific weekly key
        calculateTeamValue: (teamMembers, monthData) => {{
            // Only count active employees with < 60 days tenure
            // 재직 중인 직원만 계산 (퇴사자 제외)
            const targetDate = new Date(targetMonth + '-01');
            return teamMembers.filter(m => {{
                if (!m.is_active || !m.entrance_date) return false;
                const entranceDate = new Date(m.entrance_date);
                const daysDiff = (targetDate - entranceDate) / (1000 * 60 * 60 * 24);
                return daysDiff > 0 && daysDiff < 60;
            }}).length;
        }},
        calculateTypeValue: (employees, monthData) => {{
            // Only count active employees with < 60 days tenure
            // 재직 중인 직원만 계산 (퇴사자 제외)
            const targetDate = new Date(targetMonth + '-01');
            return employees.filter(e => {{
                if (!e.is_active || !e.entrance_date) return false;
                const entranceDate = new Date(e.entrance_date);
                const daysDiff = (targetDate - entranceDate) / (1000 * 60 * 60 * 24);
                return daysDiff > 0 && daysDiff < 60;
            }}).length;
        }}
    }},
    post_assignment_resignations: {{
        key: 'post_assignment_resignations',
        nameKo: '배정 후 퇴사',
        nameEn: 'Post-Assignment',
        nameVi: 'Sau phân công',
        unit: '명',
        type: 'count',
        weeklyKey: 'resignations',
        calculateTeamValue: (teamMembers, monthData) => monthData?.post_assignment_resignations || 0,
        calculateTypeValue: (employees, monthData) => monthData?.post_assignment_resignations || 0
    }},
    perfect_attendance: {{
        key: 'perfect_attendance',
        nameKo: '개근 직원',
        nameEn: 'Perfect Attendance',
        nameVi: 'Chuyên cần hoàn hảo',
        unit: '명',
        type: 'count',
        weeklyKey: 'total_employees',
        calculateTeamValue: (teamMembers, monthData) => {{
            // Count team members with perfect attendance flag
            // 개근 플래그가 있는 팀원 수 계산
            return teamMembers.filter(m => m.is_active && m.perfect_attendance).length;
        }},
        calculateTypeValue: (employees, monthData) => {{
            // Count employees with perfect attendance by TYPE
            // TYPE별 개근자 수 계산
            return employees.filter(e => e.is_active && e.perfect_attendance).length;
        }}
    }},
    long_term_employees: {{
        key: 'long_term_employees',
        nameKo: '장기근속자',
        nameEn: 'Long-term (1yr+)',
        nameVi: 'Lâu năm (1 năm+)',
        unit: '명',
        type: 'count',
        weeklyKey: 'total_employees',
        calculateTeamValue: (teamMembers, monthData) => {{
            // Only count active employees with 1+ year tenure
            // 재직 중인 직원만 계산 (퇴사자 제외)
            const targetDate = new Date(targetMonth + '-01');
            return teamMembers.filter(m => {{
                if (!m.is_active || !m.entrance_date) return false;
                const entranceDate = new Date(m.entrance_date);
                const daysDiff = (targetDate - entranceDate) / (1000 * 60 * 60 * 24);
                return daysDiff >= 365;
            }}).length;
        }},
        calculateTypeValue: (employees, monthData) => {{
            // Only count active employees with 1+ year tenure
            // 재직 중인 직원만 계산 (퇴사자 제외)
            const targetDate = new Date(targetMonth + '-01');
            return employees.filter(e => {{
                if (!e.is_active || !e.entrance_date) return false;
                const entranceDate = new Date(e.entrance_date);
                const daysDiff = (targetDate - entranceDate) / (1000 * 60 * 60 * 24);
                return daysDiff >= 365;
            }}).length;
        }}
    }},
    data_errors: {{
        key: 'data_errors',
        nameKo: '데이터 오류',
        nameEn: 'Data Errors',
        nameVi: 'Lỗi dữ liệu',
        unit: '건',
        type: 'count',
        weeklyKey: 'total_employees',
        calculateTeamValue: (teamMembers, monthData) => monthData?.data_errors || 0,
        calculateTypeValue: (employees, monthData) => monthData?.data_errors || 0
    }},
    pregnant_employees: {{
        key: 'pregnant_employees',
        nameKo: '임신 직원',
        nameEn: 'Pregnant Employees',
        nameVi: 'Nhân viên mang thai',
        unit: '명',
        type: 'count',
        weeklyKey: 'total_employees',
        calculateTeamValue: (teamMembers, monthData) => {{
            return teamMembers.filter(m => m.is_pregnant === true).length;
        }},
        calculateTypeValue: (employees, monthData) => {{
            return employees.filter(e => e.is_pregnant === true).length;
        }}
    }}
}};

// Extract weekly data for any KPI
function extractWeeklyKPIData(kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config) return [];

    const allWeeklyData = [];
    const metricsArray = Object.entries(monthlyMetrics)
        .map(([month, data]) => ({{ month, ...data }}))
        .sort((a, b) => a.month.localeCompare(b.month));

    // Special handling for absence_rate_excl_maternity - use monthly data
    if (kpiKey === 'absence_rate_excl_maternity') {{
        // Use monthly data for maternity-excluded absence rate
        metricsArray.forEach(month => {{
            // Create synthetic weekly data points from monthly data
            const monthValue = month[kpiKey] || 0;

            // If there are weekly metrics for regular absence rate,
            // create corresponding points for excl_maternity
            if (month.weekly_metrics && typeof month.weekly_metrics === 'object') {{
                Object.entries(month.weekly_metrics).sort().forEach(([weekKey, weekData]) => {{
                    allWeeklyData.push({{
                        label: weekData.date || `${{month.month.substring(5)}} ${{weekKey}}`,
                        value: monthValue // Use monthly value for all weeks
                    }});
                }});
            }} else {{
                // Fallback to single monthly point
                allWeeklyData.push({{
                    label: month.month,
                    value: monthValue
                }});
            }}
        }});
        return allWeeklyData;
    }}

    // Regular processing for other KPIs
    metricsArray.forEach(month => {{
        if (month.weekly_metrics && typeof month.weekly_metrics === 'object') {{
            Object.entries(month.weekly_metrics).sort().forEach(([weekKey, weekData]) => {{
                let value = weekData[config.weeklyKey] || 0;

                // For percentage types, ensure it's a number
                if (config.type === 'percentage' && typeof value === 'number') {{
                    value = value.toFixed(1);
                }}

                allWeeklyData.push({{
                    label: weekData.date || `${{month.month.substring(5)}} ${{weekKey}}`,
                    value: value
                }});
            }});
        }}
    }});

    // Fallback to monthly data if no weekly data
    if (allWeeklyData.length === 0) {{
        metricsArray.forEach(month => {{
            allWeeklyData.push({{
                label: month.month,
                value: month[kpiKey] || 0
            }});
        }});
    }}

    return allWeeklyData;
}}

// Extract team-level data for any KPI
function extractTeamKPIData(kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config) return [];

    const metricsArray = Object.entries(monthlyMetrics)
        .map(([month, data]) => ({{ month, ...data }}))
        .sort((a, b) => a.month.localeCompare(b.month));

    const latestMonth = metricsArray[metricsArray.length - 1];

    const teamDistribution = Object.entries(teamData).map(([teamName, team]) => {{
        const members = team.members || [];

        // Special handling for absence_rate: use team.metrics.absence_rate if available
        let value;
        if (kpiKey === 'absence_rate' && team.metrics && typeof team.metrics.absence_rate !== 'undefined') {{
            value = team.metrics.absence_rate;
        }} else {{
            value = config.calculateTeamValue(members, latestMonth, teamName);
        }}

        return {{
            name: teamName,
            value: config.type === 'percentage' ? parseFloat(value) : value,
            count: members.length
        }};
    }}).sort((a, b) => b.value - a.value);

    return teamDistribution;
}}

// Extract TYPE-level data for any KPI
function extractTypeKPIData(kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config) return {{}};

    const typeCounts = {{ 'TYPE-1': [], 'TYPE-2': [], 'TYPE-3': [] }};

    Object.values(teamData).forEach(team => {{
        if (!team.members) return;
        team.members.forEach(member => {{
            const roleType = member.role_type || 'TYPE-3';
            if (typeCounts[roleType]) {{
                typeCounts[roleType].push(member);
            }}
        }});
    }});

    const metricsArray = Object.entries(monthlyMetrics)
        .map(([month, data]) => ({{ month, ...data }}))
        .sort((a, b) => a.month.localeCompare(b.month));
    const latestMonth = metricsArray[metricsArray.length - 1];

    const typeData = {{}};
    Object.entries(typeCounts).forEach(([type, employees]) => {{
        if (employees.length > 0) {{
            typeData[type] = config.calculateTypeValue(employees, latestMonth);
        }}
    }});

    return typeData;
}}

// Calculate month-over-month change for team KPI data
function calculateTeamKPIChange(kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config) return [];

    const metricsArray = Object.entries(monthlyMetrics)
        .map(([month, data]) => ({{ month, ...data }}))
        .sort((a, b) => a.month.localeCompare(b.month));

    if (metricsArray.length < 2) return [];

    const currentMonth = metricsArray[metricsArray.length - 1];
    const previousMonth = metricsArray[metricsArray.length - 2];

    const teamChanges = [];

    Object.entries(teamData).forEach(([teamName, team]) => {{
        const members = team.members || [];

        // Current month value
        // Special handling for absence_rate: use team.metrics.absence_rate if available
        let currentValue;
        if (kpiKey === 'absence_rate' && team.metrics && typeof team.metrics.absence_rate !== 'undefined') {{
            currentValue = team.metrics.absence_rate;
        }} else {{
            currentValue = config.calculateTeamValue(members, currentMonth, teamName);
        }}

        // Previous month value (calculate from members who were active then)
        let previousValue = 0;
        if (config.key === 'total_employees') {{
            // ✅ Use common countActiveEmployees function for consistency
            // Calculate month-end date for previous month
            const prevMonthDate = new Date(previousMonth.month + '-01');
            const prevMonthEnd = new Date(prevMonthDate);
            prevMonthEnd.setMonth(prevMonthEnd.getMonth() + 1);
            prevMonthEnd.setDate(0);

            debugLog(`🔍 [${{teamName}}] Calculating previous month (${{previousMonth.month}}) employee count:`);
            debugLog(`   Month-end: ${{prevMonthEnd.toISOString().split('T')[0]}}`);
            debugLog(`   Total members in team: ${{members.length}}`);

            // ✅ Use common function (month-end basis)
            previousValue = countActiveEmployees(members, prevMonthEnd);

            debugLog(`   ➡️ Result: ${{previousValue}} employees were active in ${{previousMonth.month}}`);
        }} else {{
            // For other metrics, calculate team-specific value from previous month
            previousValue = config.calculateTeamValue(members, previousMonth, teamName);
        }}

        const change = config.type === 'percentage'
            ? (parseFloat(currentValue) - parseFloat(previousValue)).toFixed(1)
            : currentValue - previousValue;

        teamChanges.push({{
            name: teamName,
            current: config.type === 'percentage' ? parseFloat(currentValue) : currentValue,
            previous: config.type === 'percentage' ? parseFloat(previousValue) : previousValue,
            change: parseFloat(change),
            changePercent: previousValue !== 0 ? ((change / previousValue) * 100).toFixed(1) : 0
        }});
    }});

    return teamChanges.sort((a, b) => b.current - a.current);
}}

// ============================================
// Shared Utility Functions (Reusable)
// ============================================

// CRITICAL: Universal date-based active member counter
// 모든 곳에서 재활용 가능한 입사/퇴사 날짜 기반 재직자 계산 함수
// 월말 기준 (Month-end basis) - Python _total_employees() 로직과 동일
function countActiveMembersForPeriod(members, startDate, endDate) {{
    // ✅ Use common parseDateSafe function for consistency
    return members.filter(member => {{
        const entranceDate = parseDateSafe(member.entrance_date);
        const stopDate = parseDateSafe(member.stop_date);

        // ✅ 월말 기준: entered before period end AND (no stop date OR stopped AFTER period end)
        // Python logic: stop_date > end_of_month (퇴사일이 월말보다 이후)
        const enteredBefore = !entranceDate || entranceDate <= endDate;
        const activeAfter = !stopDate || stopDate > endDate;  // Changed: >= to >

        return enteredBefore && activeAfter;
    }}).length;
}}

// Get month start and end dates for a given month key (YYYY-MM)
function getMonthDates(monthKey) {{
    const monthStart = new Date(monthKey + '-01');
    const monthEnd = new Date(monthStart);
    monthEnd.setMonth(monthEnd.getMonth() + 1);
    monthEnd.setDate(0); // Last day of the month
    return {{ start: monthStart, end: monthEnd }};
}}

// ============================================
// Team Detail Data Extraction Functions
// ============================================

// Extract team's monthly trend data (last 6 months)
function extractTeamMonthlyData(teamName, kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config || !teamData[teamName]) return [];

    const team = teamData[teamName];
    const members = team.members || [];

    // Convert monthlyMetrics object to array and get last 6 months
    const monthsArray = Object.keys(monthlyMetrics).sort().slice(-6);
    const monthlyData = monthsArray.map(monthKey => {{
        const month = monthlyMetrics[monthKey];
        let value = 0;

        if (config.key === 'total_employees') {{
            // ✅ Use common countActiveEmployees function for consistency
            // Month-end basis for consistency with main KPI
            const monthDates = getMonthDates(monthKey);
            value = countActiveEmployees(members, monthDates.end);
        }} else {{
            // For other metrics, calculate from current members
            value = config.calculateTeamValue(members, month, teamName);
        }}

        return {{
            month: monthKey,
            label: parseInt(monthKey.split('-')[1]) + '월',
            value: config.type === 'percentage' ? parseFloat(value).toFixed(1) : value
        }};
    }});

    return monthlyData;
}}

// Extract team's weekly trend data (last 20 weeks across all months)
function extractTeamWeeklyData(teamName, kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config || !teamData[teamName]) return [];

    const team = teamData[teamName];
    const members = team.members || [];

    const weeklyData = [];

    // Convert monthlyMetrics object to array
    const monthsArray = Object.keys(monthlyMetrics).sort();
    monthsArray.forEach(monthKey => {{
        const month = monthlyMetrics[monthKey];
        if (month.weekly_metrics && typeof month.weekly_metrics === 'object') {{
            Object.entries(month.weekly_metrics).sort().forEach(([weekKey, weekData]) => {{
                let value = 0;

                if (config.key === 'total_employees') {{
                    // ✅ Use common countActiveEmployees function for consistency
                    // Calculate actual active TEAM members for this week (팀별 주차별 인원)
                    const weekEndStr = weekData.date_full || weekData.date;

                    if (weekEndStr) {{
                        let weekEnd = parseDateSafe(weekEndStr);

                        // ✅ CRITICAL: Cap weekEnd at month-end to prevent cross-month counting
                        // Example: If week is 10/27-11/02, use 10/31 instead of 11/02
                        const monthDates = getMonthDates(monthKey);
                        if (weekEnd > monthDates.end) {{
                            weekEnd = monthDates.end;  // Cap at month end
                        }}

                        // ✅ Use common function (week-end basis: stopDate > weekEnd)
                        value = countActiveEmployees(members, weekEnd);
                    }} else {{
                        // Fallback to current team size (not ideal but better than wrong data)
                        value = members.length;
                    }}
                }} else {{
                    // For rates, use week's metric if available
                    value = weekData[config.weeklyKey] || 0;
                }}

                weeklyData.push({{
                    label: weekData.date || `${{monthKey.substring(5)}} ${{weekKey}}`,
                    value: config.type === 'percentage' ? parseFloat(value).toFixed(1) : value
                }});
            }});
        }}
    }});

    // Return last 20 weeks
    return weeklyData.slice(-20);
}}

// Extract team's role distribution data
function extractTeamRoleData(teamName, kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config || !teamData[teamName]) return [];

    const team = teamData[teamName];
    const members = team.members || [];

    // Get latest month from monthlyMetrics
    const monthsArray = Object.keys(monthlyMetrics).sort();
    const latestMonthKey = monthsArray[monthsArray.length - 1];
    const latestMonth = monthlyMetrics[latestMonthKey];

    // Get month period for accurate counting
    const monthDates = getMonthDates(latestMonthKey);

    // Group by role_type (ROLE TYPE STD field)
    const roleCounts = {{}};
    members.forEach(member => {{
        const role = member.role_type || member.TYPE || 'Unknown';
        if (!roleCounts[role]) {{
            roleCounts[role] = [];
        }}
        roleCounts[role].push(member);
    }});

    return Object.entries(roleCounts).map(([role, roleMembers]) => {{
        let value = 0;
        let count = 0;

        if (config.key === 'total_employees') {{
            // ✅ Use universal date-based counter (입사/퇴사 날짜 반영)
            count = countActiveMembersForPeriod(roleMembers, monthDates.start, monthDates.end);
            value = count;
        }} else {{
            // For rates, calculate from members
            count = roleMembers.length;
            value = config.calculateTeamValue(roleMembers, latestMonth, teamName);
        }}

        return {{
            role: role,
            count: count,
            value: config.type === 'percentage' ? parseFloat(value) : value
        }};
    }}).sort((a, b) => b.count - a.count);
}}

// Extract team members detailed data
function extractTeamMembersData(teamName, kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config || !teamData[teamName]) return [];

    const team = teamData[teamName];
    const members = team.members || [];

    // Get latest month from monthlyMetrics
    const monthsArray = Object.keys(monthlyMetrics).sort();
    const latestMonthKey = monthsArray[monthsArray.length - 1];
    const latestMonth = monthlyMetrics[latestMonthKey];

    return members.map(member => {{
        // Calculate tenure
        const entranceDate = member.entrance_date ? new Date(member.entrance_date) : null;
        let tenureDays = 0;
        if (entranceDate) {{
            const today = new Date();
            tenureDays = Math.floor((today - entranceDate) / (1000 * 60 * 60 * 24));
        }}

        // Get KPI value for this member
        let kpiValue = 0;
        if (config.key === 'total_employees') {{
            kpiValue = 1; // Active
        }} else if (config.key === 'absence_rate' || config.key === 'unauthorized_absence_rate') {{
            kpiValue = member.attendance_rate ? (100 - member.attendance_rate).toFixed(1) + '%' : '0%';
        }} else if (config.key === 'perfect_attendance') {{
            kpiValue = member.attendance_rate === 100 ? 'Yes' : 'No';
        }} else if (config.key === 'long_term_employees') {{
            kpiValue = tenureDays >= 365 ? 'Yes' : 'No';
        }} else {{
            kpiValue = '-';
        }}

        return {{
            id: member.id || member.employee_id || '-',
            name: member.name || '-',
            position: member.Position || '-',
            role: member.role || member.Position || '-',
            entrance_date: member.entrance_date || '-',
            tenure_days: tenureDays,
            kpi_value: kpiValue
        }};
    }});
}}

// ============================================
// Hierarchy Visualization Charts
// ============================================

let hierarchyBarChartInstance = null;
let hierarchyDonutChart1Instance = null;
let hierarchyDonutChart2Instance = null;

// Prepare hierarchy data
function prepareHierarchyData() {{
    const position1Counts = {{}};
    const position2Counts = {{}};
    const position1ToPosition2Map = {{}};  // Track which pos2 belongs to which pos1

    // Calculate month-end date for current month (same as team distribution logic)
    const currentMonthDate = new Date(targetMonth + '-01');
    const currentMonthEnd = new Date(currentMonthDate);
    currentMonthEnd.setMonth(currentMonthEnd.getMonth() + 1);
    currentMonthEnd.setDate(0);

    // Count by Position 1 and Position 2 (only active employees)
    Object.values(teamData).forEach(team => {{
        const teamName = team.name;

        // Count only active employees at month-end
        const activeMemberCount = team.members ? countActiveEmployees(team.members, currentMonthEnd) : 0;

        if (activeMemberCount > 0) {{
            position1Counts[teamName] = (position1Counts[teamName] || 0) + activeMemberCount;

            // Count sub-teams (Position 2) - also filter for active employees
            if (team.sub_teams) {{
                if (!position1ToPosition2Map[teamName]) {{
                    position1ToPosition2Map[teamName] = [];
                }}

                Object.values(team.sub_teams).forEach(subTeam => {{
                    const subTeamName = subTeam.name;
                    const activeSubMemberCount = subTeam.members ? countActiveEmployees(subTeam.members, currentMonthEnd) : 0;
                    position2Counts[subTeamName] = (position2Counts[subTeamName] || 0) + activeSubMemberCount;
                    position1ToPosition2Map[teamName].push(subTeamName);
                }});
            }}
        }}
    }});

    return {{
        position1: position1Counts,
        position2: position2Counts,
        position1ToPosition2Map: position1ToPosition2Map
    }};
}}

const hierarchyChartData = prepareHierarchyData();

// Chart 1: Horizontal Bar Chart
function renderHierarchyBarChart() {{
    const ctx = document.getElementById('hierarchyBarChart');
    if (!ctx) return;

    if (hierarchyBarChartInstance) hierarchyBarChartInstance.destroy();

    const labels = Object.keys(hierarchyChartData.position1);
    const data = Object.values(hierarchyChartData.position1);
    const total = data.reduce((a, b) => a + b, 0);

    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
    ];

    hierarchyBarChartInstance = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: labels,
            datasets: [{{
                label: '인원 수',
                data: data,
                backgroundColor: colors
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            const value = context.parsed.x;
                            const percent = ((value / total) * 100).toFixed(1);
                            return `${{value}}명 (${{percent}}%)`;
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    beginAtZero: true,
                    ticks: {{
                        callback: function(value) {{
                            return value + '명';
                        }}
                    }}
                }}
            }}
        }}
    }});
}}

// Chart 2: Sunburst Chart (Plotly.js)
function renderHierarchySunburstChart() {{
    const container = document.getElementById('hierarchySunburstChart');
    if (!container) return;

    const labels = [];
    const parents = [];
    const values = [];
    const colors = [];
    const ids = [];  // Unique IDs to prevent ambiguity

    // Calculate total - sum of all Position 1 values (which now include corrected totals)
    let rootTotal = 0;

    // First pass: calculate corrected Position 1 totals
    const correctedPosition1Values = {{}};
    Object.entries(hierarchyChartData.position1).forEach(([name, count]) => {{
        let actualTotal = count;
        if (hierarchyChartData.position1ToPosition2Map[name]) {{
            const subTeamNames = hierarchyChartData.position1ToPosition2Map[name];
            const subTeamTotal = subTeamNames.reduce((sum, subName) => {{
                return sum + (hierarchyChartData.position2[subName] || 0);
            }}, 0);
            actualTotal = Math.max(count, subTeamTotal);
        }}
        correctedPosition1Values[name] = actualTotal;
        rootTotal += actualTotal;
    }});

    // Root node with corrected total
    labels.push('전체');
    parents.push('');
    values.push(rootTotal);
    ids.push('root');
    colors.push('#CCCCCC');

    // Position 1 data
    const colorPalette = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
        '#9966FF', '#FF9F40', '#E74C3C', '#2ECC71'
    ];

    let colorIndex = 0;
    const position1Map = {{}};  // Store position1 IDs

    Object.entries(correctedPosition1Values).forEach(([name, actualTotal]) => {{
        const id = `pos1_${{colorIndex}}`;
        position1Map[name] = id;

        labels.push(name);
        parents.push('root');
        values.push(actualTotal);
        ids.push(id);
        colors.push(colorPalette[colorIndex % colorPalette.length]);
        colorIndex++;
    }});

    // Position 2 data (sub-teams) - make unique IDs to prevent ambiguity
    let pos2Index = 0;
    Object.entries(hierarchyChartData.position2).forEach(([subName, count]) => {{
        // Find parent position1
        let parentId = 'root';
        Object.values(teamData).forEach(team => {{
            if (team.sub_teams && team.sub_teams[subName]) {{
                parentId = position1Map[team.name] || 'root';
            }}
        }});

        const uniqueId = `pos2_${{pos2Index}}`;
        labels.push(subName);
        parents.push(parentId);
        values.push(count);
        ids.push(uniqueId);
        colors.push(colorPalette[colorIndex % colorPalette.length] + 'AA'); // Semi-transparent

        colorIndex++;
        pos2Index++;
    }});

    const data = [{{
        type: 'sunburst',
        labels: labels,
        parents: parents,
        values: values,
        ids: ids,  // Use unique IDs
        marker: {{
            colors: colors
        }},
        text: labels.map((label, i) => {{
            const value = values[i];
            // Don't show percentage for root
            if (ids[i] === 'root') {{
                return label;
            }}
            const percent = ((value / rootTotal) * 100).toFixed(1);
            return `${{label}}<br>${{percent}}%`;
        }}),
        customdata: labels.map((label, i) => {{
            const value = values[i];
            const parent = parents[i];

            // Calculate percentRoot
            const percentRoot = ((value / rootTotal) * 100).toFixed(1);

            // Calculate percentParent
            let percentParent = 100.0;
            if (parent && parent !== '') {{
                const parentIndex = ids.indexOf(parent);
                if (parentIndex >= 0) {{
                    const parentValue = values[parentIndex];
                    percentParent = ((value / parentValue) * 100).toFixed(1);
                }}
            }}

            return [percentRoot, percentParent];
        }}),
        hovertemplate: '<b>%{{label}}</b><br>인원: %{{value}}명<br>전체 대비: %{{customdata[0]}}%<br>부모 대비: %{{customdata[1]}}%<extra></extra>',
        textfont: {{ size: 11, color: 'white' }},
        textposition: 'inside',
        insidetextorientation: 'radial',
        branchvalues: 'total'  // Important: use 'total' to show correct percentages
    }}];

    const layout = {{
        margin: {{ l: 0, r: 0, b: 0, t: 0 }},
        height: 500,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        sunburstcolorway: colorPalette
    }};

    const config = {{
        responsive: true,
        displayModeBar: false
    }};

    Plotly.newPlot('hierarchySunburstChart', data, layout, config);
}}

// Chart 3: Nested Donut Charts
function renderHierarchyDonutCharts() {{
    // Donut 1: Position 1 distribution
    const ctx1 = document.getElementById('hierarchyDonutChart1');
    if (ctx1) {{
        if (hierarchyDonutChart1Instance) hierarchyDonutChart1Instance.destroy();

        const labels1 = Object.keys(hierarchyChartData.position1);
        const data1 = Object.values(hierarchyChartData.position1);

        hierarchyDonutChart1Instance = new Chart(ctx1, {{
            type: 'doughnut',
            data: {{
                labels: labels1,
                datasets: [{{
                    data: data1,
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                        '#9966FF', '#FF9F40', '#E74C3C', '#2ECC71'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            generateLabels: function(chart) {{
                                const data = chart.data;
                                const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                return data.labels.map((label, i) => {{
                                    const value = data.datasets[0].data[i];
                                    const percent = ((value / total) * 100).toFixed(1);
                                    return {{
                                        text: `${{label}}: ${{value}}명 (${{percent}}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i]
                                    }};
                                }});
                            }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.parsed;
                                const percent = ((value / total) * 100).toFixed(1);
                                return `${{context.label}}: ${{value}}명 (${{percent}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
    }}

    // Donut 2: Position 2 distribution
    const ctx2 = document.getElementById('hierarchyDonutChart2');
    if (ctx2) {{
        if (hierarchyDonutChart2Instance) hierarchyDonutChart2Instance.destroy();

        const labels2 = Object.keys(hierarchyChartData.position2);
        const data2 = Object.values(hierarchyChartData.position2);

        // Generate more colors for Position 2 (usually more items)
        const colors2 = [];
        const baseColors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#E74C3C', '#2ECC71'
        ];
        for (let i = 0; i < labels2.length; i++) {{
            colors2.push(baseColors[i % baseColors.length] + (i < 8 ? '' : '99'));
        }}

        hierarchyDonutChart2Instance = new Chart(ctx2, {{
            type: 'doughnut',
            data: {{
                labels: labels2,
                datasets: [{{
                    data: data2,
                    backgroundColor: colors2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            font: {{ size: 10 }},
                            generateLabels: function(chart) {{
                                const data = chart.data;
                                const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                return data.labels.map((label, i) => {{
                                    const value = data.datasets[0].data[i];
                                    const percent = ((value / total) * 100).toFixed(1);
                                    return {{
                                        text: `${{label}}: ${{value}}명 (${{percent}}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[i]
                                    }};
                                }});
                            }}
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.parsed;
                                const percent = ((value / total) * 100).toFixed(1);
                                return `${{context.label}}: ${{value}}명 (${{percent}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
    }}
}}

// Initialize all hierarchy charts
function initializeHierarchyCharts() {{
    renderHierarchyBarChart();
    renderHierarchySunburstChart();
    renderHierarchyDonutCharts();
    renderTeamSummaryCards();
}}

// Render team summary cards with comprehensive KPIs
function renderTeamSummaryCards() {{
    const container = document.getElementById('teamSummaryCards');
    if (!container) return;

    // Get teams sorted by employee count
    const teams = Object.entries(teamData).sort((a, b) =>
        (b[1].metrics?.active_members || 0) - (a[1].metrics?.active_members || 0)
    );

    const teamColors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2", "#FF9FF3"
    ];

    container.innerHTML = teams.map(([teamName, teamInfo], idx) => {{
        const metrics = teamInfo.metrics || {{}};
        const teamColor = teamColors[idx % teamColors.length];

        // Get previous month metrics for comparison
        const prevTeamInfo = previousMonthTeamData[teamName];
        const prevMetrics = prevTeamInfo?.metrics || {{}};

        // Helper function to format change indicator
        const formatChange = (current, previous, isNegativeBetter = true) => {{
            if (!previous || previous === 0) return '';
            const change = current - previous;
            if (Math.abs(change) < 0.01) return '';  // No change
            const changePercent = ((change / previous) * 100).toFixed(1);
            const isPositive = change > 0;
            const isBetter = isNegativeBetter ? !isPositive : isPositive;
            const color = isBetter ? 'success' : 'danger';
            const icon = isPositive ? '↑' : '↓';
            return `<small class="text-${{color}} ms-1">${{icon}} ${{Math.abs(changePercent)}}%</small>`;
        }};

        // Extract current KPI values
        const activeMembers = metrics.active_members || 0;
        const absenceRate = (metrics.absence_rate || 0).toFixed(1);
        const recentDayAbsence = (metrics.recent_day_absence_rate || 0).toFixed(1);
        const resignationRate = (metrics.resignation_rate || 0).toFixed(1);
        const pregnantCount = metrics.pregnant_count || 0;
        const under90Count = metrics.under_90_days_count || 0;
        const perfectAttendance = metrics.perfect_attendance_count || 0;
        const avgTenure = (metrics.avg_tenure_years || 0).toFixed(1);
        const resignationsThisMonth = metrics.resignations_this_month || 0;
        const highRiskCount = metrics.high_risk_count || 0;
        const avgAttendanceRate = (metrics.avg_attendance_rate || 0).toFixed(1);

        // Extract previous month KPI values for comparison
        const prevActiveMembers = prevMetrics.active_members || 0;
        const prevAbsenceRate = prevMetrics.absence_rate || 0;
        const prevRecentDayAbsence = prevMetrics.recent_day_absence_rate || 0;
        const prevResignationRate = prevMetrics.resignation_rate || 0;
        const prevPregnantCount = prevMetrics.pregnant_count || 0;
        const prevUnder90Count = prevMetrics.under_90_days_count || 0;
        const prevPerfectAttendance = prevMetrics.perfect_attendance_count || 0;
        const prevAvgTenure = prevMetrics.avg_tenure_years || 0;
        const prevHighRiskCount = prevMetrics.high_risk_count || 0;
        const prevAvgAttendanceRate = prevMetrics.avg_attendance_rate || 0;
        const prevTotalMembers = prevMetrics.total_members || 0;

        // XSS 방지: teamName sanitize / Prevent XSS: sanitize teamName
        const safeTeamName = sanitizeHTML(teamName);
        const escapedTeamName = teamName.replace(/'/g, "\\'").replace(/"/g, '\\"');

        return `
            <div class="col-12 mb-4">
                <div class="card shadow-sm" style="border-left: 5px solid ${{teamColor}};">
                    <div class="card-header" style="background: linear-gradient(135deg, ${{teamColor}}22 0%, ${{teamColor}}11 100%); border-bottom: 2px solid ${{teamColor}};">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="mb-0" style="color: ${{teamColor}}; font-weight: 600;">
                                <i class="fas fa-users me-2"></i>${{safeTeamName}}
                            </h5>
                            <button class="btn btn-sm btn-outline-primary" onclick="showTeamDetailModal('${{escapedTeamName}}', 'overview')">
                                <i class="fas fa-chart-line me-1"></i>
                                <span class="lang-text" data-ko="상세 분석" data-en="Detailed Analysis" data-vi="Phân tích chi tiết">상세 분석</span>
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="row g-3">
                            <!-- KPI 1: Active Members -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-user-check text-primary me-2"></i>
                                        <span class="lang-text" data-ko="재직 인원" data-en="Active Members" data-vi="Nhân viên hiện tại">재직 인원</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: ${{teamColor}};">${{activeMembers}}</strong>
                                        <span class="text-muted ms-1">명</span>
                                        ${{formatChange(activeMembers, prevActiveMembers, false)}}
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 2: Monthly Absence Rate -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-calendar-times text-warning me-2"></i>
                                        <span class="lang-text" data-ko="월 결근율" data-en="Monthly Absence" data-vi="Tỷ lệ vắng tháng">월 결근율</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: ${{absenceRate > 20 ? '#dc3545' : absenceRate > 10 ? '#ffc107' : '#28a745'}};">${{absenceRate}}%</strong>
                                        ${{formatChange(parseFloat(absenceRate), prevAbsenceRate, true)}}
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 3: Recent Day Absence Rate -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-calendar-day text-info me-2"></i>
                                        <span class="lang-text" data-ko="최근일 결근율" data-en="Recent Day Absence" data-vi="Vắng ngày gần nhất">최근일 결근율</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: ${{recentDayAbsence > 20 ? '#dc3545' : recentDayAbsence > 10 ? '#ffc107' : '#28a745'}};">${{recentDayAbsence}}%</strong>
                                        ${{formatChange(parseFloat(recentDayAbsence), prevRecentDayAbsence, true)}}
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 4: Monthly Resignation Rate -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-user-minus text-danger me-2"></i>
                                        <span class="lang-text" data-ko="월 퇴사율" data-en="Monthly Resignation" data-vi="Tỷ lệ nghỉ việc">월 퇴사율</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: ${{resignationRate > 15 ? '#dc3545' : resignationRate > 10 ? '#ffc107' : '#28a745'}};">${{resignationRate}}%</strong>
                                        ${{formatChange(parseFloat(resignationRate), prevResignationRate, true)}}
                                        <small class="text-muted d-block mt-1">${{resignationsThisMonth}}명 퇴사</small>
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 5: Pregnant Employees -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-female text-pink me-2"></i>
                                        <span class="lang-text" data-ko="임산부" data-en="Pregnant" data-vi="Mang thai">임산부</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: #e83e8c;">${{pregnantCount}}</strong>
                                        <span class="text-muted ms-1">명</span>
                                        ${{formatChange(pregnantCount, prevPregnantCount, false)}}
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 6: Under 90 Days Members -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-user-clock text-secondary me-2"></i>
                                        <span class="lang-text" data-ko="90일 미만" data-en="Under 90 Days" data-vi="Dưới 90 ngày">90일 미만</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: #6c757d;">${{under90Count}}</strong>
                                        <span class="text-muted ms-1">명</span>
                                        ${{formatChange(under90Count, prevUnder90Count, false)}}
                                        <small class="text-muted d-block mt-1">${{activeMembers > 0 ? ((under90Count / activeMembers * 100).toFixed(1)) : 0}}%</small>
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 7: Perfect Attendance -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-award text-success me-2"></i>
                                        <span class="lang-text" data-ko="개근자" data-en="Perfect Attendance" data-vi="Chuyên cần">개근자</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: #28a745;">${{perfectAttendance}}</strong>
                                        <span class="text-muted ms-1">명</span>
                                        ${{formatChange(perfectAttendance, prevPerfectAttendance, false)}}
                                        <small class="text-muted d-block mt-1">${{activeMembers > 0 ? ((perfectAttendance / activeMembers * 100).toFixed(1)) : 0}}%</small>
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 8: Average Tenure -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-history text-info me-2"></i>
                                        <span class="lang-text" data-ko="평균 근속연수" data-en="Avg Tenure" data-vi="Thâm niên TB">평균 근속연수</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: #17a2b8;">${{avgTenure}}</strong>
                                        <span class="text-muted ms-1">년</span>
                                        ${{formatChange(parseFloat(avgTenure), prevAvgTenure, false)}}
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 9: Attendance Rate -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-percentage text-primary me-2"></i>
                                        <span class="lang-text" data-ko="평균 출근율" data-en="Attendance Rate" data-vi="Tỷ lệ đi làm">평균 출근율</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: ${{avgAttendanceRate < 80 ? '#dc3545' : avgAttendanceRate < 90 ? '#ffc107' : '#28a745'}};">${{avgAttendanceRate}}%</strong>
                                        ${{formatChange(parseFloat(avgAttendanceRate), prevAvgAttendanceRate, false)}}
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 10: High Risk Count -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-exclamation-triangle text-danger me-2"></i>
                                        <span class="lang-text" data-ko="고위험 인원" data-en="High Risk" data-vi="Rủi ro cao">고위험 인원</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: ${{highRiskCount > 5 ? '#dc3545' : highRiskCount > 2 ? '#ffc107' : '#28a745'}};">${{highRiskCount}}</strong>
                                        <span class="text-muted ms-1">명</span>
                                        ${{formatChange(highRiskCount, prevHighRiskCount, true)}}
                                        <small class="text-muted d-block mt-1">결근율 >30% or 무단결근 >15%</small>
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 11: Total Members -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-users text-secondary me-2"></i>
                                        <span class="lang-text" data-ko="총 인원" data-en="Total Members" data-vi="Tổng nhân viên">총 인원</span>
                                    </div>
                                    <div class="kpi-value">
                                        <strong style="font-size: 1.5rem; color: #6c757d;">${{metrics.total_members || 0}}</strong>
                                        <span class="text-muted ms-1">명</span>
                                        ${{formatChange(metrics.total_members || 0, prevTotalMembers, false)}}
                                        <small class="text-muted d-block mt-1">재직 + 퇴사</small>
                                    </div>
                                </div>
                            </div>

                            <!-- KPI 12: TYPE Distribution -->
                            <div class="col-md-3 col-sm-6">
                                <div class="kpi-mini-card">
                                    <div class="kpi-label">
                                        <i class="fas fa-layer-group text-info me-2"></i>
                                        <span class="lang-text" data-ko="TYPE 분포" data-en="TYPE Distribution" data-vi="Phân bố TYPE">TYPE 분포</span>
                                    </div>
                                    <div class="kpi-value" style="font-size: 0.85rem;">
                                        ${{Object.entries(metrics.type_distribution || {{}}).map(([type, count]) =>
                                            `<div><strong>${{type}}:</strong> ${{count}}명</div>`
                                        ).join('')}}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }}).join('');
}}

// Call on page load
document.addEventListener('DOMContentLoaded', initializeHierarchyCharts);

// Re-render when switching tabs
document.querySelectorAll('#hierarchyChartTabs button').forEach(button => {{
    button.addEventListener('shown.bs.tab', function(e) {{
        const targetId = e.target.getAttribute('data-bs-target');
        if (targetId === '#sunburstChartView') {{
            // Slight delay to ensure container is visible
            setTimeout(renderHierarchySunburstChart, 100);
        }}
    }});
}});

// ============================================
// Main Trend Charts with Period Selector
// 기간 선택이 가능한 트렌드 차트
// ============================================

// Store chart instances for updating
// 업데이트를 위해 차트 인스턴스 저장
let trendCharts = {};
let currentTrendPeriod = 6; // Default: 6 months / 기본값: 6개월

// Get trend data filtered by period
// 기간으로 필터링된 트렌드 데이터 가져오기
function getTrendDataForPeriod(metricKey, period) {
    const data = availableMonths.map(month => monthlyMetrics[month][metricKey]);
    return data.slice(-period); // Last N months / 최근 N개월
}

// Get labels filtered by period
// 기간으로 필터링된 레이블 가져오기
function getLabelsForPeriod(period) {
    return monthLabels.slice(-period);
}

// Update all trend charts with new period
// 새 기간으로 모든 트렌드 차트 업데이트
function updateTrendPeriod(period) {
    currentTrendPeriod = period;

    // Update button states
    document.querySelectorAll('#periodSelector button').forEach(btn => {
        btn.classList.remove('active');
        if (parseInt(btn.dataset.period) === period) {
            btn.classList.add('active');
        }
    });

    const newLabels = getLabelsForPeriod(period);

    // Update each chart
    Object.keys(trendCharts).forEach(chartId => {
        const chart = trendCharts[chartId];
        if (chart) {
            chart.data.labels = newLabels;

            // Update each dataset based on chart type
            chart.data.datasets.forEach((dataset, index) => {
                const metricKey = getMetricKeyForChart(chartId, index);
                if (metricKey) {
                    dataset.data = getTrendDataForPeriod(metricKey, period);
                }
            });

            chart.update('active');
        }
    });
}

// Map chart IDs to metric keys
// 차트 ID를 메트릭 키에 매핑
function getMetricKeyForChart(chartId, datasetIndex) {
    const mapping = {
        'employeeTrend': ['total_employees'],
        'hiresResignations': ['recent_hires', 'recent_resignations', 'maternity_leave_count'],
        'resignationRate': ['resignation_rate'],
        'longTerm': ['long_term_employees'],
        'unauthorizedAbsence': ['unauthorized_absence_rate'],
        'absenceRate': ['absence_rate', 'absence_rate_excl_maternity']
    };
    return mapping[chartId] ? mapping[chartId][datasetIndex] : null;
}

// Chart 1: Employee Trend
trendCharts.employeeTrend = new Chart(document.getElementById('employeeTrendChart'), {
    type: 'line',
    data: {
        labels: monthLabels,
        datasets: [{
            label: '재직자 수 / Total Employees',
            data: getTrendData('total_employees'),
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
    }
});

// Chart 2: Hires vs Resignations vs Maternity Leave
trendCharts.hiresResignations = new Chart(document.getElementById('hiresResignationsChart'), {
    type: 'bar',
    data: {
        labels: monthLabels,
        datasets: [
            {
                label: '신규 입사 / New Hires',
                data: getTrendData('recent_hires'),
                backgroundColor: 'rgba(40, 167, 69, 0.7)',
                borderColor: '#28a745',
                borderWidth: 1
            },
            {
                label: '퇴사자 / Resignations',
                data: getTrendData('recent_resignations'),
                backgroundColor: 'rgba(220, 53, 69, 0.7)',
                borderColor: '#dc3545',
                borderWidth: 1
            },
            {
                label: '출산 휴가자 / Maternity Leave',
                data: getTrendData('maternity_leave_count'),
                backgroundColor: 'rgba(255, 105, 180, 0.7)',
                borderColor: '#ff69b4',
                borderWidth: 1
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    usePointStyle: true,
                    padding: 15
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.dataset.label + ': ' + context.parsed.y + '명';
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    stepSize: 5,
                    callback: function(value) {
                        return value + '명';
                    }
                }
            }
        }
    }
});

// Chart 3: Resignation Rate
trendCharts.resignationRate = new Chart(document.getElementById('resignationRateChart'), {
    type: 'line',
    data: {
        labels: monthLabels,
        datasets: [{
            label: '퇴사율 (%) / Resignation Rate',
            data: getTrendData('resignation_rate'),
            borderColor: '#dc3545',
            backgroundColor: 'rgba(220, 53, 69, 0.1)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
        scales: {
            y: {
                beginAtZero: true,
                ticks: { callback: function(value) { return value + '%'; } }
            }
        }
    }
});

// Chart 4: Long-term Employees
trendCharts.longTerm = new Chart(document.getElementById('longTermChart'), {
    type: 'bar',
    data: {
        labels: monthLabels,
        datasets: [{
            label: '장기근속자 (1년+) / Long-term Employees',
            data: getTrendData('long_term_employees'),
            backgroundColor: 'rgba(102, 126, 234, 0.7)',
            borderColor: '#667eea',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
    }
});

// Chart 5: Unauthorized Absence Rate (Mixed: Bar + Target Line)
trendCharts.unauthorizedAbsence = new Chart(document.getElementById('unauthorizedAbsenceChart'), {
    type: 'bar',
    data: {
        labels: monthLabels,
        datasets: [
            {
                label: '무단 결근율 (%) / Unauthorized Absence Rate',
                data: getTrendData('unauthorized_absence_rate'),
                backgroundColor: 'rgba(255, 99, 132, 0.7)',
                borderColor: '#ff6384',
                borderWidth: 1,
                order: 2
            },
            {
                label: '목표선 (2%) / Target (2%)',
                data: monthLabels.map(() => 2),
                type: 'line',
                borderColor: '#dc3545',
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [10, 5],
                pointRadius: 0,
                pointHoverRadius: 0,
                fill: false,
                tension: 0,
                order: 1
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'bottom' },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        if (context.dataset.label.includes('목표선') || context.dataset.label.includes('Target')) {
                            return '목표 / Target: 2%';
                        }
                        return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + '%';
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value.toFixed(1) + '%';
                    }
                }
            }
        }
    }
});

// Chart 6: Absence Rate (with Maternity Leave comparison)
trendCharts.absenceRate = new Chart(document.getElementById('absenceRateChart'), {
    type: 'line',
    data: {
        labels: monthLabels,
        datasets: [
            {
                label: '결근율 (출산휴가 포함) / Absence Rate (incl. Maternity)',
                data: getTrendData('absence_rate'),
                borderColor: '#ffa500',
                backgroundColor: 'rgba(255, 165, 0, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                borderWidth: 2
            },
            {
                label: '결근율 (출산휴가 제외) / Absence Rate (excl. Maternity)',
                data: getTrendData('absence_rate_excl_maternity'),
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                borderWidth: 2,
                borderDash: [5, 5]
            },
            {
                label: '목표선 (10%) / Target (10%)',
                data: monthLabels.map(() => 10),
                borderColor: '#dc3545',
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [10, 5],
                pointRadius: 0,
                pointHoverRadius: 0,
                fill: false,
                tension: 0
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    usePointStyle: true,
                    padding: 15
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        if (context.dataset.label.includes('목표선') || context.dataset.label.includes('Target')) {
                            return '목표 / Target: 10%';
                        }
                        return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value.toFixed(1) + '%';
                    }
                }
            }
        }
    }
});

// ============================================
// Modal Management & Performance Optimization
// ============================================

let modalCharts = {{}};
let chartLoadState = {{}}; // Track which charts have been loaded
let observerInstance = null; // Intersection Observer for lazy loading

/**
 * Performance Optimization: Lazy Loading with Intersection Observer
 * 차트가 뷰포트에 진입할 때만 렌더링하여 초기 로딩 성능 개선
 */
function initLazyChartLoading() {{
    if ('IntersectionObserver' in window) {{
        const options = {{
            root: null,
            rootMargin: '50px', // Load 50px before entering viewport
            threshold: 0.01 // Trigger when 1% visible
        }};

        observerInstance = new IntersectionObserver((entries, observer) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const chartContainer = entry.target;
                    const modalId = chartContainer.dataset.modalId;
                    const kpiKey = chartContainer.dataset.kpiKey;

                    if (modalId && kpiKey && !chartLoadState[modalId]) {{
                        debugLog(`🔍 Lazy loading charts for modal: ${{modalId}}`);
                        const modalNum = parseInt(modalId.replace('kpiModal', ''));
                        createUnifiedModalCharts(modalNum, kpiKey);
                        chartLoadState[modalId] = true;
                        observer.unobserve(chartContainer);
                    }}
                }}
            }});
        }}, options);

        // Observe all modal chart containers
        document.querySelectorAll('.modal-chart-container[data-modal-id]').forEach(container => {{
            observerInstance.observe(container);
        }});
    }}
}}

/**
 * Destroy all charts in a modal to free memory
 * 모달 닫을 때 차트 인스턴스 제거하여 메모리 최적화
 */
function destroyModalCharts(modalNum) {{
    const chartKeys = [
        `modal${{modalNum}}_weekly`,
        `modal${{modalNum}}_teams`,
        `modal${{modalNum}}_types`,
        `modal${{modalNum}}_change`,
        `modal${{modalNum}}_treemap`
    ];

    chartKeys.forEach(key => {{
        if (modalCharts[key]) {{
            try {{
                modalCharts[key].destroy();
                delete modalCharts[key];
                debugLog(`🗑️ Destroyed chart: ${{key}}`);
            }} catch (e) {{
                debugLog(`Failed to destroy chart ${{key}}:`, e);
            }}
        }}
    }});
}}

/**
 * Debounce function for resize events
 * 리사이즈 이벤트 최적화
 */
function debounce(func, wait) {{
    let timeout;
    return function executedFunction(...args) {{
        const later = () => {{
            clearTimeout(timeout);
            func(...args);
        }};
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    }};
}}

/**
 * Handle window resize for responsive charts
 * 반응형 차트 리사이즈 처리
 */
const handleChartResize = debounce(() => {{
    Object.values(modalCharts).forEach(chart => {{
        if (chart && typeof chart.resize === 'function') {{
            chart.resize();
        }}
    }});
    debugLog('📐 Charts resized for responsive layout');
}}, 250);

// ============================================
// Universal Modal Chart Creation Functions
// ============================================

/**
 * Create all 6 charts for a unified KPI modal
 * @param {{number}} modalNum - Modal number (1-11)
 * @param {{string}} kpiKey - KPI key from kpiConfig
 */
function createUnifiedModalCharts(modalNum, kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config) {{
        debugLog(`KPI config not found for: ${{kpiKey}}`);
        return;
    }}

    debugLog(`🎨 Creating unified modal charts for Modal ${{modalNum}} - ${{config.nameKo}}`);

    // 1. 주차별 KPI 트렌드
    createKPIWeeklyTrendChart(modalNum, kpiKey);

    // 1-1. 일별 결근율 트렌드 (absence rate modal only)
    if (kpiKey === 'absence_rate') {{
        createDailyAbsenceChart(modalNum);
    }}

    // 2. 팀별 KPI 분포
    createTeamDistributionChart(modalNum, kpiKey);

    // 3. 타입별 KPI 현황
    createTypeBreakdownChart(modalNum, kpiKey);

    // 4. 팀별 KPI 전월 대비 변화 (Bar)
    createTeamChangeBarChart(modalNum, kpiKey);

    // 5 & 6. 팀별 KPI 전월 대비 변화 (Treemap) + 상세 테이블
    createKPITreemapAndTable(modalNum, kpiKey);
}}

/**
 * Chart 1: 주차별 KPI 트렌드 (Line Chart + Trendline)
 */
function createKPIWeeklyTrendChart(modalNum, kpiKey) {{
    const config = kpiConfig[kpiKey];
    const weeklyData = extractWeeklyKPIData(kpiKey);

    if (weeklyData.length === 0) {{
        console.warn(`No weekly data for ${{kpiKey}}`);
        return;
    }}

    const weekLabels = weeklyData.map(w => w.label);
    const weekValues = weeklyData.map(w => parseFloat(w.value) || 0);

    // Calculate trendline (linear regression)
    const n = weekValues.length;
    const xValues = Array.from({{ length: n }}, (_, i) => i);
    const sumX = xValues.reduce((a, b) => a + b, 0);
    const sumY = weekValues.reduce((a, b) => a + b, 0);
    const sumXY = xValues.reduce((sum, x, i) => sum + x * weekValues[i], 0);
    const sumX2 = xValues.reduce((sum, x) => sum + x * x, 0);
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    const trendlineData = xValues.map(x => slope * x + intercept);

    // Prepare datasets
    const datasets = [
        {{
            label: kpiKey === 'absence_rate' ? '전체 결근율' : `주차별 ${{config.nameKo}}`,
            data: weekValues,
            borderColor: '#FF6B6B',
            backgroundColor: 'rgba(255, 107, 107, 0.1)',
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            fill: true
        }},
        {{
            label: '추세선',
            data: trendlineData,
            borderColor: '#45B7D1',
            borderDash: [10, 5],
            borderWidth: 2,
            fill: false,
            pointRadius: 0,
            pointHoverRadius: 0
        }}
    ];

    // Add maternity-excluded line for absence_rate modal
    if (kpiKey === 'absence_rate') {{
        const maternityExclData = extractWeeklyKPIData('absence_rate_excl_maternity');
        if (maternityExclData.length > 0) {{
            const maternityExclValues = maternityExclData.map(w => parseFloat(w.value) || 0);

            // Add maternity excluded absence rate line
            datasets.splice(1, 0, {{
                label: '출산휴가 제외 시 결근율',
                data: maternityExclValues,
                borderColor: '#4ECDC4',
                backgroundColor: 'rgba(78, 205, 196, 0.1)',
                tension: 0.3,
                borderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: true
            }});

            // Calculate trendline for maternity-excluded data
            const sumY2 = maternityExclValues.reduce((a, b) => a + b, 0);
            const sumXY2 = xValues.reduce((sum, x, i) => sum + x * maternityExclValues[i], 0);
            const slope2 = (n * sumXY2 - sumX * sumY2) / (n * sumX2 - sumX * sumX);
            const intercept2 = (sumY2 - slope2 * sumX) / n;
            const trendlineData2 = xValues.map(x => slope2 * x + intercept2);

            // Add trendline for maternity-excluded data
            datasets.push({{
                label: '추세선 (출산휴가 제외)',
                data: trendlineData2,
                borderColor: '#96CEB4',
                borderDash: [5, 3],
                borderWidth: 2,
                fill: false,
                pointRadius: 0,
                pointHoverRadius: 0
            }});
        }}
    }}

    const canvasId = `modalChart${{modalNum}}_weekly`;
    const ctx = document.getElementById(canvasId);
    if (!ctx) {{
        debugLog(`Canvas not found: ${{canvasId}}`);
        return;
    }}

    // Destroy existing chart
    const chartKey = `modal${{modalNum}}_weekly`;
    if (modalCharts[chartKey]) {{
        modalCharts[chartKey].destroy();
    }}

    modalCharts[chartKey] = new Chart(ctx.getContext('2d'), {{
        type: 'line',
        data: {{
            labels: weekLabels,
            datasets: datasets
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{
                    display: true,
                    text: `주차별 ${{config.nameKo}} 트렌드`,
                    align: 'start',
                    font: {{ size: 18, weight: 600 }},
                    padding: {{ bottom: 10 }},
                    color: '#333'
                }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            label += context.parsed.y;
                            if (config.type === 'percentage') label += '%';
                            else label += config.unit;
                            return label;
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: config.unit
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Calculate linear regression (trend line)
 */
function calculateTrendLine(data) {{
    const n = data.length;
    if (n < 2) return data; // Need at least 2 points

    // Calculate means
    const xMean = (n - 1) / 2;
    const yMean = data.reduce((sum, val) => sum + val, 0) / n;

    // Calculate slope and intercept
    let numerator = 0;
    let denominator = 0;

    for (let i = 0; i < n; i++) {{
        numerator += (i - xMean) * (data[i] - yMean);
        denominator += (i - xMean) * (i - xMean);
    }}

    const slope = denominator !== 0 ? numerator / denominator : 0;
    const intercept = yMean - slope * xMean;

    // Generate trend line data
    const trendData = [];
    for (let i = 0; i < n; i++) {{
        trendData.push(intercept + slope * i);
    }}

    return trendData;
}}

/**
 * Chart 1-1: Daily Absence Rate Chart (Last 30 Days)
 */
function createDailyAbsenceChart(modalNum) {{
    const canvasId = `modalChart${{modalNum}}_daily`;
    const canvas = document.getElementById(canvasId);

    if (!canvas) {{
        console.warn(`Canvas not found: ${{canvasId}}`);
        return;
    }}

    // Get the latest month's daily metrics
    const currentMonth = Object.keys(monthlyMetrics).sort().pop();
    if (!currentMonth || !monthlyMetrics[currentMonth].daily_metrics) {{
        const ctx = canvas.getContext('2d');
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('일별 데이터가 없습니다', canvas.width / 2, canvas.height / 2);
        return;
    }}

    const dailyData = monthlyMetrics[currentMonth].daily_metrics;
    const dates = Object.keys(dailyData).sort();

    const labels = dates.map(date => dailyData[date].date);
    const absenceRatesExclMaternity = dates.map(date => dailyData[date].absence_rate_excl_maternity);

    // Calculate trend line (excl. maternity only)
    const maternityExclTrend = calculateTrendLine(absenceRatesExclMaternity);

    // Create chart (excl. maternity only)
    modalCharts[canvasId] = new Chart(canvas, {{
        type: 'line',
        data: {{
            labels: labels,
            datasets: [
                {{
                    label: '결근율 (출산휴가 제외)',
                    data: absenceRatesExclMaternity,
                    borderColor: '#4ECDC4',
                    backgroundColor: 'rgba(78, 205, 196, 0.1)',
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                    tension: 0.3,
                    fill: true
                }},
                {{
                    label: '추세선',
                    data: maternityExclTrend,
                    borderColor: '#4ECDC4',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 0,
                    fill: false,
                    tension: 0
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{
                mode: 'index',
                intersect: false
            }},
            plugins: {{
                title: {{
                    display: true,
                    text: '최근 30일 일별 결근율 추이 (출산휴가 제외)',
                    align: 'start',
                    font: {{ size: 16, weight: 600 }},
                    padding: {{ bottom: 10 }},
                    color: '#333'
                }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            label += context.parsed.y.toFixed(1) + '%';
                            return label;
                        }}
                    }}
                }},
                legend: {{
                    display: true,
                    position: 'top',
                    labels: {{
                        usePointStyle: true,
                        padding: 20
                    }}
                }}
            }},
            scales: {{
                x: {{
                    title: {{
                        display: true,
                        text: '날짜'
                    }},
                    ticks: {{
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkipPadding: 10
                    }}
                }},
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: '결근율 (%)'
                    }},
                    ticks: {{
                        callback: function(value) {{
                            return value.toFixed(1) + '%';
                        }}
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Absence Reason Analysis Charts
 * 결근 사유 분석 차트들
 */

// Chart 1: 결근 사유 분포 (Doughnut Chart)
function createAbsenceReasonDistributionChart() {{
    const canvas = document.getElementById('modalChart2_reasonDistribution');
    if (!canvas) {{
        console.warn('Canvas not found: modalChart2_reasonDistribution');
        return;
    }}

    // Get data from modalData
    const reasonData = modalData.absence_reason_distribution || {{}};

    if (Object.keys(reasonData).length === 0) {{
        const ctx = canvas.getContext('2d');
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('결근 사유 데이터가 없습니다', canvas.width / 2, canvas.height / 2);
        return;
    }}

    const reasons = Object.keys(reasonData);
    const counts = Object.values(reasonData);

    // Color palette for different absence reasons
    const reasonColors = [
        '#FF6B6B',  // Maternity - Red
        '#4ECDC4',  // Annual Leave - Teal
        '#FFD93D',  // Unauthorized - Yellow
        '#95E1D3',  // Child Illness - Mint
        '#A8E6CF',  // Business Trip - Green
        '#FF9FF3',  // Medical - Pink
        '#B4A7D6',  // Card Issue - Purple
        '#C7CEEA'   // Other - Light Blue
    ];

    modalCharts['modal2_reasonDistribution'] = new Chart(canvas, {{
        type: 'doughnut',
        data: {{
            labels: reasons,
            datasets: [{{
                label: '결근 사유',
                data: counts,
                backgroundColor: reasonColors.slice(0, reasons.length),
                borderWidth: 2,
                borderColor: '#fff'
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    position: 'right',
                    labels: {{
                        font: {{ size: 12 }},
                        padding: 15,
                        generateLabels: function(chart) {{
                            const data = chart.data;
                            const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                            return data.labels.map((label, i) => {{
                                const value = data.datasets[0].data[i];
                                const percentage = ((value / total) * 100).toFixed(1);
                                return {{
                                    text: `${{label}}: ${{value}}일 (${{percentage}}%)`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    hidden: false,
                                    index: i
                                }};
                            }});
                        }}
                    }}
                }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${{label}}: ${{value}}일 (${{percentage}}%)`;
                        }}
                    }}
                }},
                title: {{
                    display: false
                }}
            }}
        }}
    }});
}}

// Chart 2: 월별 결근 사유 추이 (Stacked Bar Chart)
function createAbsenceReasonTrendsChart() {{
    const canvas = document.getElementById('modalChart2_reasonTrends');
    if (!canvas) {{
        console.warn('Canvas not found: modalChart2_reasonTrends');
        return;
    }}

    // Get data from modalData
    const monthlyData = modalData.monthly_absence_reasons || {{}};

    if (Object.keys(monthlyData).length === 0) {{
        const ctx = canvas.getContext('2d');
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('월별 결근 사유 데이터가 없습니다', canvas.width / 2, canvas.height / 2);
        return;
    }}

    const months = Object.keys(monthlyData).sort();
    const reasonSet = new Set();
    months.forEach(month => {{
        Object.keys(monthlyData[month]).forEach(reason => reasonSet.add(reason));
    }});
    const reasons = Array.from(reasonSet);

    // Color palette matching the doughnut chart
    const reasonColors = {{
        '출산휴가 (Maternity)': '#FF6B6B',
        '연차/유급휴가 (Annual Leave)': '#4ECDC4',
        '무단결근 (Unauthorized)': '#FFD93D',
        '자녀병가 (Child Illness)': '#95E1D3',
        '출장 (Business Trip)': '#A8E6CF',
        '병가 (Medical)': '#FF9FF3',
        '카드분실 (Card Issue)': '#B4A7D6',
        '기타 (Other)': '#C7CEEA'
    }};

    const datasets = reasons.map(reason => ({{
        label: reason,
        data: months.map(month => monthlyData[month][reason] || 0),
        backgroundColor: reasonColors[reason] || '#CCCCCC',
        borderWidth: 1,
        borderColor: '#fff'
    }}));

    modalCharts['modal2_reasonTrends'] = new Chart(canvas, {{
        type: 'bar',
        data: {{
            labels: months.map(m => {{
                const [year, month] = m.split('-');
                return `${{month}}월`;
            }}),
            datasets: datasets
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    position: 'top',
                    labels: {{
                        font: {{ size: 11 }},
                        padding: 10
                    }}
                }},
                tooltip: {{
                    mode: 'index',
                    callbacks: {{
                        footer: function(tooltipItems) {{
                            let total = 0;
                            tooltipItems.forEach(item => {{
                                total += item.parsed.y;
                            }});
                            return '총합: ' + total + '명';
                        }}
                    }}
                }},
                title: {{
                    display: false
                }}
            }},
            scales: {{
                x: {{
                    stacked: true,
                    grid: {{ display: false }}
                }},
                y: {{
                    stacked: true,
                    beginAtZero: true,
                    ticks: {{
                        callback: function(value) {{
                            return value + '명';
                        }}
                    }},
                    title: {{
                        display: true,
                        text: '결근 인원수'
                    }}
                }}
            }}
        }}
    }});
}}

// Chart 3: 팀별 결근 사유 분포 (Grouped Bar Chart)
function createTeamAbsenceReasonsChart() {{
    const canvas = document.getElementById('modalChart2_teamReasons');
    if (!canvas) {{
        console.warn('Canvas not found: modalChart2_teamReasons');
        return;
    }}

    // Get data from modalData
    const teamData = modalData.team_absence_reasons || {{}};

    if (Object.keys(teamData).length === 0) {{
        const ctx = canvas.getContext('2d');
        ctx.font = '16px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.fillText('팀별 결근 사유 데이터가 없습니다', canvas.width / 2, canvas.height / 2);
        return;
    }}

    const teams = Object.keys(teamData);
    const reasonSet = new Set();
    teams.forEach(team => {{
        Object.keys(teamData[team]).forEach(reason => reasonSet.add(reason));
    }});
    const reasons = Array.from(reasonSet);

    // Color palette matching the other charts
    const reasonColors = {{
        '출산휴가 (Maternity)': '#FF6B6B',
        '연차/유급휴가 (Annual Leave)': '#4ECDC4',
        '무단결근 (Unauthorized)': '#FFD93D',
        '자녀병가 (Child Illness)': '#95E1D3',
        '출장 (Business Trip)': '#A8E6CF',
        '병가 (Medical)': '#FF9FF3',
        '카드분실 (Card Issue)': '#B4A7D6',
        '기타 (Other)': '#C7CEEA'
    }};

    const datasets = reasons.map(reason => ({{
        label: reason,
        data: teams.map(team => teamData[team][reason] || 0),
        backgroundColor: reasonColors[reason] || '#CCCCCC',
        borderWidth: 1,
        borderColor: '#fff'
    }}));

    modalCharts['modal2_teamReasons'] = new Chart(canvas, {{
        type: 'bar',
        data: {{
            labels: teams,
            datasets: datasets
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    position: 'top',
                    labels: {{
                        font: {{ size: 11 }},
                        padding: 10
                    }}
                }},
                tooltip: {{
                    mode: 'index',
                    callbacks: {{
                        footer: function(tooltipItems) {{
                            let total = 0;
                            tooltipItems.forEach(item => {{
                                total += item.parsed.y;
                            }});
                            return '총합: ' + total + '명';
                        }}
                    }}
                }},
                title: {{
                    display: false
                }}
            }},
            scales: {{
                x: {{
                    grid: {{ display: false }}
                }},
                y: {{
                    beginAtZero: true,
                    ticks: {{
                        callback: function(value) {{
                            return value + '명';
                        }}
                    }},
                    title: {{
                        display: true,
                        text: '결근 인원수'
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Chart 2: 팀별 KPI 분포 (Horizontal Bar Chart, clickable)
 */
function createTeamDistributionChart(modalNum, kpiKey) {{
    const config = kpiConfig[kpiKey];
    const teamData = extractTeamKPIData(kpiKey);

    if (teamData.length === 0) {{
        console.warn(`No team data for ${{kpiKey}}`);
        return;
    }}

    const teamNames = teamData.map(t => t.name);
    const teamValues = teamData.map(t => t.value);
    const teamColors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2", "#FF9FF3"];

    const canvasId = `modalChart${{modalNum}}_teams`;
    const ctx = document.getElementById(canvasId);
    if (!ctx) {{
        debugLog(`Canvas not found: ${{canvasId}}`);
        return;
    }}

    const chartKey = `modal${{modalNum}}_teams`;
    if (modalCharts[chartKey]) {{
        modalCharts[chartKey].destroy();
    }}

    // Special handling for absence_rate - show grouped bar with maternity exclusion
    if (kpiKey === 'absence_rate' || kpiKey === 'absence_rate_excl_maternity') {{
        // Get both regular and maternity-excluded rates
        const regularData = extractTeamKPIData('absence_rate');
        const maternityExclData = extractTeamKPIData('absence_rate_excl_maternity');

        modalCharts[chartKey] = new Chart(ctx.getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: teamNames,
                datasets: [
                    {{
                        label: '결근율',
                        data: regularData.map(t => t.value),
                        backgroundColor: '#FF6B6B',
                        borderColor: '#FF6B6B',
                        borderWidth: 1
                    }},
                    {{
                        label: '출산휴가 제외 시 결근율',
                        data: maternityExclData.map(t => t.value || regularData.find(r => r.name === t.name)?.value || 0),
                        backgroundColor: '#4ECDC4',
                        borderColor: '#4ECDC4',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: '팀별 결근율 분포 (클릭하여 상세보기)',
                        align: 'start',
                        font: {{ size: 18, weight: 600 }},
                        padding: {{ bottom: 10 }},
                        color: '#333'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.x.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: '결근율 (%)'
                        }}
                    }}
                }}
            }}
        }});
    }} else {{
        // Original single bar chart for other KPIs
        modalCharts[chartKey] = new Chart(ctx.getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: teamNames,
                datasets: [{{
                    label: config.nameKo,
                    data: teamValues,
                    backgroundColor: teamColors
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                onClick: function(event, elements) {{
                    if (elements.length > 0) {{
                        const index = elements[0].index;
                        const teamName = teamNames[index];
                        showTeamDetailModal(teamName, 'total_employees');
                    }}
                }},
                plugins: {{
                    title: {{
                        display: true,
                        text: `팀별 ${{config.nameKo}} 분포 (클릭하여 상세보기)`,
                        align: 'start',
                        font: {{ size: 18, weight: 600 }},
                        padding: {{ bottom: 10 }},
                        color: '#333'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                let label = context.parsed.x;
                                if (config.type === 'percentage') label += '%';
                                else label += config.unit;
                                return label;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: config.unit
                        }}
                    }}
                }}
            }}
        }});
    }}
}}

/**
 * Chart 3: 타입별 KPI 트렌드 (Line Chart)
 */
function createTypeBreakdownChart(modalNum, kpiKey) {{
    const config = kpiConfig[kpiKey];

    // Get all months data for trend analysis
    const metricsArray = Object.entries(monthlyMetrics)
        .map(([month, data]) => ({{ month, ...data }}))
        .sort((a, b) => a.month.localeCompare(b.month));

    if (metricsArray.length === 0) {{
        console.warn(`No metrics data for ${{kpiKey}}`);
        return;
    }}

    // Prepare month labels (e.g., "7월", "8월", ...)
    const monthLabels = metricsArray.map(m => {{
        const monthNum = parseInt(m.month.split('-')[1]);
        return monthNum + '월';
    }});

    // Initialize data structure for each TYPE
    const typeData = {{
        'TYPE-1': [],
        'TYPE-2': [],
        'TYPE-3': []
    }};

    // Calculate TYPE data for each month
    metricsArray.forEach(monthData => {{
        const typeCounts = {{ 'TYPE-1': [], 'TYPE-2': [], 'TYPE-3': [] }};

        // Count employees by type for this month
        Object.values(teamData).forEach(team => {{
            if (!team.members) return;
            team.members.forEach(member => {{
                const roleType = member.role_type || 'TYPE-3';
                if (typeCounts[roleType]) {{
                    typeCounts[roleType].push(member);
                }}
            }});
        }});

        // Calculate metric value for each type
        Object.keys(typeData).forEach(type => {{
            const employees = typeCounts[type];
            if (employees.length > 0) {{
                const value = config.calculateTypeValue(employees, monthData, type);
                typeData[type].push(value);
            }} else {{
                typeData[type].push(0);
            }}
        }});
    }});

    const canvasId = `modalChart${{modalNum}}_types`;
    const ctx = document.getElementById(canvasId);
    if (!ctx) {{
        debugLog(`Canvas not found: ${{canvasId}}`);
        return;
    }}

    const chartKey = `modal${{modalNum}}_types`;
    if (modalCharts[chartKey]) {{
        modalCharts[chartKey].destroy();
    }}

    // Create line chart for trend visualization
    modalCharts[chartKey] = new Chart(ctx.getContext('2d'), {{
        type: 'line',
        data: {{
            labels: monthLabels,
            datasets: [
                {{
                    label: 'TYPE-1',
                    data: typeData['TYPE-1'],
                    borderColor: '#FF6B6B',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    borderWidth: 3,
                    tension: 0.3,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }},
                {{
                    label: 'TYPE-2',
                    data: typeData['TYPE-2'],
                    borderColor: '#4ECDC4',
                    backgroundColor: 'rgba(78, 205, 196, 0.1)',
                    borderWidth: 3,
                    tension: 0.3,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }},
                {{
                    label: 'TYPE-3',
                    data: typeData['TYPE-3'],
                    borderColor: '#FFEAA7',
                    backgroundColor: 'rgba(255, 234, 167, 0.1)',
                    borderWidth: 3,
                    tension: 0.3,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{
                mode: 'index',
                intersect: false
            }},
            plugins: {{
                title: {{
                    display: true,
                    text: `타입별 ${{config.nameKo}} 트렌드`,
                    align: 'start',
                    font: {{ size: 18, weight: 600 }},
                    padding: {{ bottom: 10 }},
                    color: '#333'
                }},
                legend: {{
                    display: true,
                    position: 'top'
                }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            label += context.parsed.y.toFixed(2);
                            if (config.type === 'percentage') label += '%';
                            else label += config.unit;
                            return label;
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: `${{config.nameKo}} (${{config.unit}})`
                    }}
                }},
                x: {{
                    title: {{
                        display: true,
                        text: '월별 Monthly'
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Chart 4: 팀별 KPI 전월 대비 변화 (Horizontal Bar Chart)
 */
function createTeamChangeBarChart(modalNum, kpiKey) {{
    const config = kpiConfig[kpiKey];
    const teamChanges = calculateTeamKPIChange(kpiKey);

    if (teamChanges.length === 0) {{
        console.warn(`No team change data for ${{kpiKey}}`);
        return;
    }}

    const teamNames = teamChanges.map(t => t.name);
    const changeValues = teamChanges.map(t => t.change);
    const changeColors = changeValues.map(v => v >= 0 ? '#4ECDC4' : '#FF6B6B');

    const canvasId = `modalChart${{modalNum}}_change`;
    const ctx = document.getElementById(canvasId);
    if (!ctx) {{
        debugLog(`Canvas not found: ${{canvasId}}`);
        return;
    }}

    const chartKey = `modal${{modalNum}}_change`;
    if (modalCharts[chartKey]) {{
        modalCharts[chartKey].destroy();
    }}

    // Get month labels
    const metricsArray = Object.entries(monthlyMetrics)
        .map(([month, data]) => ({{ month, ...data }}))
        .sort((a, b) => a.month.localeCompare(b.month));

    const currentMonth = metricsArray[metricsArray.length - 1];
    const previousMonth = metricsArray.length > 1 ? metricsArray[metricsArray.length - 2] : null;

    const currentMonthLabel = parseInt(currentMonth.month.split('-')[1]) + '월';
    const prevMonthLabel = previousMonth ? parseInt(previousMonth.month.split('-')[1]) + '월' : '';

    modalCharts[chartKey] = new Chart(ctx.getContext('2d'), {{
        type: 'bar',
        data: {{
            labels: teamNames,
            datasets: [{{
                label: `${{prevMonthLabel}} vs ${{currentMonthLabel}} 변화`,
                data: changeValues,
                backgroundColor: changeColors
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                title: {{
                    display: true,
                    text: `팀별 ${{config.nameKo}} 분포 및 전월 대비 변화 (${{prevMonthLabel}} vs ${{currentMonthLabel}})`,
                    align: 'start',
                    font: {{ size: 18, weight: 600 }},
                    padding: {{ bottom: 10 }},
                    color: '#333'
                }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            let label = context.parsed.x >= 0 ? '+' : '';
                            label += context.parsed.x;
                            if (config.type === 'percentage') label += '%';
                            else label += config.unit;
                            return label;
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    title: {{
                        display: true,
                        text: `변화량 (${{config.unit}})`
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Charts 5 & 6: 팀별 KPI 전월 대비 변화 (Treemap) + 상세 테이블
 */
/**
 * Charts 5 & 6: 팀별 KPI 전월 대비 변화 (D3 Treemap with 2-level hierarchy) + 상세 테이블
 * Enhanced with total employees modal's treemap structure
 * 총인원 모달의 트리맵 구조를 적용하여 개선 (2단계 계층, SVG 기반, 향상된 상호작용)
 */
function createKPITreemapAndTable(modalNum, kpiKey) {{
    const config = kpiConfig[kpiKey];
    const containerId = `treemapContainer${{modalNum}}`;
    const container = document.getElementById(containerId);

    if (!container) {{
        debugLog(`Container not found: ${{containerId}}`);
        return;
    }}

    container.innerHTML = '';

    const teamChanges = calculateTeamKPIChange(kpiKey);

    if (teamChanges.length === 0) {{
        container.innerHTML = '<p class="text-muted">데이터가 없습니다.</p>';
        return;
    }}

    // Get month labels
    const metricsArray = Object.entries(monthlyMetrics)
        .map(([month, data]) => ({{ month, ...data }}))
        .sort((a, b) => a.month.localeCompare(b.month));

    const currentMonth = metricsArray[metricsArray.length - 1];
    const previousMonth = metricsArray.length > 1 ? metricsArray[metricsArray.length - 2] : null;

    const currentMonthLabel = parseInt(currentMonth.month.split('-')[1]) + '월';
    const prevMonthLabel = previousMonth ? parseInt(previousMonth.month.split('-')[1]) + '월' : '';

    // Create title
    const title = document.createElement('h4');
    title.style.cssText = 'margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;';
    title.className = 'lang-text';
    title.setAttribute('data-ko', `팀별 ${{config.nameKo}} 분포 및 ${{prevMonthLabel}} 대비 변화`);
    title.setAttribute('data-en', `${{config.nameEn}} Distribution by Team and Changes from ${{prevMonthLabel || 'Previous Month'}}`);
    title.setAttribute('data-vi', `Phân bố ${{config.nameVi}} theo nhóm và thay đổi so với ${{prevMonthLabel || 'tháng trước'}}`);
    title.textContent = title.getAttribute(`data-${{currentLanguage}}`);
    container.appendChild(title);

    // Create treemap container with responsive width
    const treemapDiv = document.createElement('div');
    treemapDiv.id = `kpiTreemap${{modalNum}}`;
    treemapDiv.style.cssText = 'height: 600px; background: white; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; position: relative; width: 100%;';
    container.appendChild(treemapDiv);

    // Check if D3 is available
    if (typeof d3 === 'undefined') {{
        treemapDiv.innerHTML = '<div style="padding: 40px; text-align: center; color: #999;">D3 라이브러리를 로드할 수 없습니다.</div>';
        return;
    }}

    // Create detail table container (initially hidden)
    const detailTableDiv = document.createElement('div');
    detailTableDiv.id = `kpiPositionDetailTable${{modalNum}}`;
    detailTableDiv.style.cssText = 'display: none; margin-top: 20px; background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px;';
    container.appendChild(detailTableDiv);

    // Helper function: Simplify position names
    const simplifyPositionName = (position) => {{
        const positionMap = {{
            'ASSEMBLY LINE TQC': '조립 품질검사',
            'ASSEMBLY LINE RQC': '조립 품질관리',
            'STITCHING LINE TQC': '봉제 품질검사',
            'STITCHING LINE RQC': '봉제 품질관리',
            'STITCHING INLINE INSPECTOR': '봉제 인라인 검사',
            'CUTTING TQC': '재단 품질검사',
            'CUTTING RQC': '재단 품질관리',
            'LASTING TQC': '라스팅 품질검사',
            'LASTING RQC': '라스팅 품질관리',
            'STOCKFITTING TQC': '창고 품질검사',
            'STOCKFITTING RQC': '창고 품질관리',
            'OUTSOLE RQC': '아웃솔 품질관리',
            'QUALITY LINE AUDIT INSPECTOR': '품질 감사원',
            'FACTORY AUDIT LEADER': '공장 감사 리더',
            'QA MANAGER': 'QA 매니저',
            'QA TEAM LEADER': 'QA 팀 리더',
            'QA INSPECTOR': 'QA 검사원',
            'QIP MANAGER & QC': 'QIP 매니저',
            'SAMPLE PPC SUPERVISOR': '샘플 생산관리',
            'SAMPLE PRODUCTION MANAGER': '샘플 생산 매니저',
            'SAMPLE MOLD WORKER': '샘플 몰드',
            'SAMPLE CUTTING OPERATOR': '샘플 재단',
            'SAMPLE STITCHING OPERATOR': '샘플 봉제',
            'SAMPLE LASTING OPERATOR': '샘플 라스팅',
            'MAIN PRODUCTION PRODUCTION MANAGER': '생산 매니저',
            'ASSEMBLY LINE PRODUCTION LINE CHARGE': '조립 라인 담당',
            'STITCHING GROUP LEADER': '봉제 그룹 리더',
            'CUTTING LINE CHARGE': '재단 라인 담당',
            'LASTING LINE CHARGE': '라스팅 라인 담당',
            'STROBEL LINE CHARGE': '스트로벨 라인 담당',
            'ASSEMBLY': '조립부',
            'STITCHING': '봉제부',
            'CUTTING': '재단부',
            'LASTING': '라스팅부',
            'STOCKFITTING': '창고부',
            'BOTTOM': '바닥부',
            'REPACKING': '재포장부',
            'MTL': '자재부',
            'NEW': '신규부',
            'QSC': 'QSC부'
        }};
        return positionMap[position] || position.replace(/_/g, ' ').toLowerCase().replace(/\\b\\w/g, c => c.toUpperCase());
    }};

    // Helper function: Calculate all absence-related metrics for a member
    const calculateAllAbsenceMetrics = (member) => {{
        const workingDays = parseFloat(member.working_days) || 0;
        const absentDays = parseFloat(member.absent_days) || 0;
        const unauthorizedDays = parseFloat(member.unauthorized_absent_days) || 0;
        const isPregnant = (member.pregnant_vacation || '').toString().toLowerCase() === 'yes';

        if (workingDays === 0) {{
            return {{
                absence_rate: 0,
                absence_rate_excl_maternity: 0,
                unauthorized_absence_rate: 0
            }};
        }}

        const totalAbsenceRate = (absentDays / workingDays) * 100;
        const unauthorizedRate = (unauthorizedDays / workingDays) * 100;
        const maternityExclRate = isPregnant ? 0 : totalAbsenceRate;

        return {{
            absence_rate: parseFloat(totalAbsenceRate.toFixed(1)),
            absence_rate_excl_maternity: parseFloat(maternityExclRate.toFixed(1)),
            unauthorized_absence_rate: parseFloat(unauthorizedRate.toFixed(1))
        }};
    }};

    // Prepare team data with position groups and KPI values
    const teams = teamChanges.map(teamChange => {{
        const teamName = teamChange.name;
        const positionGroups = {{}};

        // Get team members and calculate position-level KPI values
        if (teamData[teamName] && teamData[teamName].members) {{
            const activeMembers = teamData[teamName].members.filter(member => {{
                const stopDate = member.stop_date;
                return !stopDate || stopDate === 'nan' || new Date(stopDate) > new Date();
            }});

            // Group by position_2nd or position_3rd
            activeMembers.forEach(member => {{
                let positionKey = member.position_2nd;
                if (!positionKey || positionKey === 'nan' || positionKey === '') {{
                    positionKey = member.position_3rd || 'Other';
                }}

                const simplifiedPosition = simplifyPositionName(positionKey);

                if (!positionGroups[simplifiedPosition]) {{
                    positionGroups[simplifiedPosition] = {{
                        name: simplifiedPosition,
                        originalPosition: positionKey,
                        value: 0,
                        count: 0,
                        employees: []
                    }};
                }}

                // Calculate KPI value based on metric type
                let memberKPIValue = 0;
                let allAbsenceMetrics = null;

                // For absence-related KPIs, calculate all three metrics
                const isAbsenceKPI = ['absence_rate', 'absence_rate_excl_maternity', 'unauthorized_absence_rate'].includes(kpiKey);

                if (isAbsenceKPI) {{
                    allAbsenceMetrics = calculateAllAbsenceMetrics(member);
                    memberKPIValue = allAbsenceMetrics[kpiKey];
                }} else if (config.type === 'percentage' || config.type === 'rate') {{
                    // For rates/percentages: use member's rate value directly
                    memberKPIValue = parseFloat(member[kpiKey]) || 0;
                }} else {{
                    // For counts: increment by 1
                    memberKPIValue = 1;
                }}

                positionGroups[simplifiedPosition].value += memberKPIValue;
                positionGroups[simplifiedPosition].count++;

                const employeeData = {{
                    name: member.full_name || member.employee_no,
                    kpiValue: memberKPIValue
                }};

                // Store all absence metrics if this is an absence-related KPI
                if (isAbsenceKPI && allAbsenceMetrics) {{
                    employeeData.allAbsenceMetrics = allAbsenceMetrics;
                }}

                positionGroups[simplifiedPosition].employees.push(employeeData);
            }});

            // For percentage/rate metrics, calculate average per position
            if (config.type === 'percentage' || config.type === 'rate') {{
                Object.values(positionGroups).forEach(group => {{
                    if (group.count > 0) {{
                        group.value = group.value / group.count;  // Average
                    }}
                }});
            }}
        }}

        // Convert position groups to array
        const positionGroupsArray = Object.values(positionGroups)
            .sort((a, b) => b.value - a.value);

        return {{
            name: teamName,
            displayName: teamName.replace(/_/g, ' '),
            total: teamChange.current,
            prev: teamChange.previous,
            change: teamChange.change,
            changePercent: teamChange.changePercent,
            children: positionGroupsArray
        }};
    }}).sort((a, b) => Math.abs(b.total) - Math.abs(a.total));

    // Build hierarchical data for D3
    const hierarchyData = {{
        name: config.nameKo,
        children: teams.map(team => ({{
            name: team.displayName,
            value: Math.abs(team.total),  // Use absolute value for sizing
            actualValue: team.total,  // Keep actual value for display
            change: team.change,
            changePercent: team.changePercent,
            prev: team.prev,
            children: team.children && team.children.length > 0 ? team.children : null
        }}))
    }};

    // Create D3 Treemap with responsive sizing
    const containerRect = treemapDiv.getBoundingClientRect();
    const width = Math.max(containerRect.width || treemapDiv.clientWidth || 800, 400);
    const height = 600;

    const svg = d3.select(`#kpiTreemap${{modalNum}}`)
        .append('svg')
        .attr('width', '100%')
        .attr('height', height)
        .attr('viewBox', `0 0 ${{width}} ${{height}}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .style('font', '10px sans-serif')
        .style('display', 'block')
        .style('max-width', '100%')
        .style('margin', '0 auto');

    // Add resize observer for responsive behavior
    if (typeof ResizeObserver !== 'undefined') {{
        const resizeObserver = new ResizeObserver(entries => {{
            for (let entry of entries) {{
                const newWidth = Math.max(entry.contentRect.width, 400);
                svg.attr('viewBox', `0 0 ${{newWidth}} ${{height}}`);
            }}
        }});
        resizeObserver.observe(treemapDiv);
    }}

    // Function to show position detail table
    const showPositionDetail = (positionData, teamName) => {{
        const detailDiv = document.getElementById(`kpiPositionDetailTable${{modalNum}}`);
        if (!detailDiv) return;

        const employees = positionData.employees || [];
        if (employees.length === 0) {{
            detailDiv.style.display = 'none';
            return;
        }}

        // Check if this is an absence-related KPI
        const isAbsenceKPI = ['absence_rate', 'absence_rate_excl_maternity', 'unauthorized_absence_rate'].includes(kpiKey);

        // Create detail table HTML
        let tableHTML = `
            <h5 style="margin: 0 0 15px 0; color: #333;">
                ${{positionData.name}} - 상세 정보 (${{employees.length}}명)
            </h5>
            <div style="overflow-x: auto;">
                <table class="table table-hover table-sm" style="font-size: 12px;">
                    <thead class="table-light">
                        <tr>
                            <th>이름</th>
        `;

        // For absence-related KPIs, show all three metrics
        if (isAbsenceKPI) {{
            tableHTML += `
                            <th>총 결근율</th>
                            <th>출산휴가 제외 결근율</th>
                            <th>무단 결근율</th>
            `;
        }} else {{
            tableHTML += `
                            <th>${{config.nameKo}}</th>
            `;
        }}

        tableHTML += `
                        </tr>
                    </thead>
                    <tbody>
        `;

        employees.forEach(emp => {{
            tableHTML += `<tr><td>${{emp.name}}</td>`;

            if (isAbsenceKPI && emp.allAbsenceMetrics) {{
                // Show all three absence metrics
                tableHTML += `
                    <td>${{emp.allAbsenceMetrics.absence_rate.toFixed(1)}}%</td>
                    <td>${{emp.allAbsenceMetrics.absence_rate_excl_maternity.toFixed(1)}}%</td>
                    <td>${{emp.allAbsenceMetrics.unauthorized_absence_rate.toFixed(1)}}%</td>
                `;
            }} else {{
                // Show single KPI value
                const displayValue = config.type === 'percentage' || config.type === 'rate' ?
                    emp.kpiValue.toFixed(1) + config.unit :
                    emp.kpiValue + config.unit;
                tableHTML += `<td>${{displayValue}}</td>`;
            }}

            tableHTML += `</tr>`;
        }});

        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;

        detailDiv.innerHTML = tableHTML;
        detailDiv.style.display = 'block';
        detailDiv.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }};

    // Create hierarchical layout
    const root = d3.hierarchy(hierarchyData)
        .sum(d => d.children ? 0 : (d.value || 1))
        .sort((a, b) => b.value - a.value);

    // Configure treemap layout
    d3.treemap()
        .size([width, height])
        .paddingOuter(3)
        .paddingTop(20)
        .paddingInner(2)
        .tile(d3.treemapSquarify.ratio(1.5))
        .round(true)
        (root);

    // Color functions based on change (like total employees modal)
    const getTeamColor = (change) => {{
        if (change > 0) return '#d94545';  // Red for increase (worse for rates like absence)
        if (change < 0) return '#4a9c5f';  // Green for decrease (better for rates)
        return '#6b7280';  // Gray for no change
    }};

    const getPositionColor = (teamChange) => {{
        if (teamChange > 0) return '#f4a5a5';  // Light red
        if (teamChange < 0) return '#a3d9a5';  // Light green
        return '#c0c5ce';  // Light gray
    }};

    // Draw team boxes (depth 1)
    const teamNodes = svg.selectAll('g.team')
        .data(root.descendants().filter(d => d.depth === 1))
        .join('g')
        .attr('class', 'team')
        .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

    // Add team rectangles
    teamNodes.append('rect')
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0)
        .attr('fill', d => getTeamColor(d.data.change))
        .attr('fill-opacity', 0.2)
        .attr('stroke', d => getTeamColor(d.data.change))
        .attr('stroke-width', 3)
        .attr('rx', 4)
        .style('cursor', 'pointer')
        .on('click', function(event, d) {{
            const originalName = teams.find(t => t.displayName === d.data.name)?.name;
            if (originalName) {{
                showTeamDetailModal(originalName, kpiKey);
            }}
        }})
        .on('mouseover', function(event, d) {{
            d3.select(this)
                .attr('stroke-width', 4)
                .attr('fill-opacity', 0.3);

            const changeText = d.data.change >= 0 ? `+${{d.data.change}}` : `${{d.data.change}}`;
            const changeColor = d.data.change > 0 ? '#f87171' : d.data.change < 0 ? '#4ade80' : '#d1d5db';
            const positionCount = d.data.children ? d.data.children.length : 0;

            const tooltip = d3.select('body').append('div')
                .attr('class', 'team-tooltip')
                .style('position', 'absolute')
                .style('visibility', 'visible')
                .style('background', 'rgba(0, 0, 0, 0.9)')
                .style('color', 'white')
                .style('padding', '12px')
                .style('border-radius', '6px')
                .style('font-size', '12px')
                .style('box-shadow', '0 4px 6px rgba(0, 0, 0, 0.2)')
                .style('max-width', '350px')
                .style('z-index', '10000')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px')
                .html(`
                    <div style="font-size: 14px; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #555; padding-bottom: 6px;">
                        ${{d.data.name}}
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>현재 ${{config.nameKo}}:</span>
                        <span style="font-weight: bold;">${{d.data.actualValue}}${{config.unit}}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>전월 ${{config.nameKo}}:</span>
                        <span>${{d.data.prev}}${{config.unit}}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>변화:</span>
                        <span style="color: ${{changeColor}}; font-weight: bold;">
                            ${{changeText}}${{config.unit}} (${{d.data.changePercent}}%)
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>포지션 그룹:</span>
                        <span>${{positionCount}}개</span>
                    </div>
                    <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #555; font-size: 11px; color: #aaa;">
                        클릭하여 팀 상세 정보 보기
                    </div>
                `);
        }})
        .on('mouseout', function(event, d) {{
            d3.select(this)
                .attr('stroke-width', 3)
                .attr('fill-opacity', 0.2);
            d3.selectAll('.team-tooltip').remove();
        }});

    // Helper function for team label configuration
    function getTeamLabelConfig(width, height) {{
        if (width < 50 || height < 40) return {{ show: false }};

        let fontSize, showBadge = true, labelContent = 'full';

        if (width < 120) {{
            fontSize = 10;
            labelContent = 'minimal';
            showBadge = width > 70;
        }} else if (width < 200) {{
            fontSize = 11;
            labelContent = 'medium';
        }} else {{
            fontSize = 12;
            labelContent = 'full';
        }}

        return {{
            show: true,
            fontSize: fontSize,
            showBadge: showBadge,
            labelContent: labelContent,
            badgeWidth: Math.min(width - 6, 250),
            badgeHeight: Math.min(18, height * 0.15)
        }};
    }}

    // Add team labels
    teamNodes.each(function(d) {{
        const node = d3.select(this);
        const width = d.x1 - d.x0;
        const height = d.y1 - d.y0;
        const labelConfig = getTeamLabelConfig(width, height);

        if (!labelConfig.show) return;

        if (labelConfig.showBadge) {{
            node.append('rect')
                .attr('width', labelConfig.badgeWidth)
                .attr('height', labelConfig.badgeHeight)
                .attr('x', 2)
                .attr('y', 2)
                .attr('rx', 2)
                .attr('fill', getTeamColor(d.data.change))
                .attr('fill-opacity', 0.9);
        }}

        const teamText = node.append('text')
            .attr('x', labelConfig.showBadge ? 6 : 4)
            .attr('y', labelConfig.showBadge ? 14 : 12)
            .attr('font-size', `${{labelConfig.fontSize}}px`)
            .attr('font-weight', 'bold')
            .attr('fill', labelConfig.showBadge ? '#fff' : '#333')
            .style('pointer-events', 'none')
            .style('user-select', 'none');

        const changeText = d.data.change >= 0 ? `+${{d.data.change}}` : d.data.change;
        let displayText = '';

        switch(labelConfig.labelContent) {{
            case 'minimal':
                displayText = width < 80 ? d.data.name : `${{d.data.name}} (${{d.data.actualValue}}${{config.unit}})`;
                break;
            case 'medium':
                displayText = `${{d.data.name}} - ${{d.data.actualValue}}${{config.unit}} (${{changeText}}${{config.unit}})`;
                break;
            case 'full':
                displayText = `${{d.data.name}} - ${{d.data.actualValue}}${{config.unit}} (${{changeText}}${{config.unit}}, ${{d.data.changePercent}}%)`;
                break;
        }}

        if (displayText.length * labelConfig.fontSize * 0.5 > width - 10) {{
            const maxChars = Math.floor((width - 10) / (labelConfig.fontSize * 0.5));
            displayText = displayText.substring(0, maxChars - 2) + '..';
        }}

        teamText.text(displayText);
    }});

    // Draw position group boxes (depth 2 - leaf nodes)
    const positionNodes = svg.selectAll('g.position-group')
        .data(root.leaves())
        .join('g')
        .attr('class', 'position-group')
        .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

    const getTeamChangeForPosition = (positionNode) => {{
        let parent = positionNode.parent;
        while (parent && parent.depth > 1) {{
            parent = parent.parent;
        }}
        return parent ? parent.data.change : 0;
    }};

    // Add position group rectangles
    positionNodes.append('rect')
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0)
        .attr('fill', d => getPositionColor(getTeamChangeForPosition(d)))
        .attr('fill-opacity', 0.6)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .attr('rx', 2)
        .style('cursor', 'pointer')
        .on('click', function(event, d) {{
            let parentTeam = d.parent;
            while (parentTeam && parentTeam.depth > 1) {{
                parentTeam = parentTeam.parent;
            }}
            if (parentTeam && parentTeam.data.name) {{
                const originalTeamName = teams.find(t => t.displayName === parentTeam.data.name)?.name;
                if (originalTeamName) {{
                    showPositionDetail(d.data, originalTeamName);
                }}
            }}
        }})
        .on('mouseover', function(event, d) {{
            d3.select(this)
                .attr('fill-opacity', 0.9)
                .attr('stroke-width', 2)
                .attr('stroke', '#333');

            // Get team-level KPI value for this position's parent team
            let parentTeam = d.parent;
            while (parentTeam && parentTeam.depth > 1) {{
                parentTeam = parentTeam.parent;
            }}
            const teamKPIValue = parentTeam ? parentTeam.data.actualValue : 0;

            const employeeList = d.data.employees && d.data.employees.length > 0 ?
                d.data.employees.slice(0, 5).map(e => `${{e.name}}`).join('<br/>') +
                (d.data.employees.length > 5 ? `<br/>... 외 ${{d.data.employees.length - 5}}명` : '') :
                '직원 정보 없음';

            const tooltip = d3.select('body').append('div')
                .attr('class', 'treemap-tooltip')
                .style('position', 'absolute')
                .style('visibility', 'visible')
                .style('background', 'rgba(0, 0, 0, 0.85)')
                .style('color', 'white')
                .style('padding', '10px')
                .style('border-radius', '4px')
                .style('font-size', '11px')
                .style('max-width', '300px')
                .style('z-index', '9999')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px')
                .html(`
                    <strong style="font-size: 13px;">${{d.data.name}}</strong><br/>
                    <div style="margin: 5px 0; border-bottom: 1px solid #666; padding-bottom: 5px;">
                        인원: <strong>${{d.data.count}}명</strong> | 팀 ${{config.nameKo}}: <strong>${{teamKPIValue}}${{config.unit}}</strong>
                    </div>
                    <div style="font-size: 10px; line-height: 1.4; color: #ddd;">
                        ${{employeeList}}
                    </div>
                    <div style="margin-top: 8px; font-size: 10px; color: #aaa;">
                        클릭하여 상세 정보 보기
                    </div>
                `);
        }})
        .on('mouseout', function(event, d) {{
            d3.select(this)
                .attr('fill-opacity', 0.6)
                .attr('stroke-width', 1.5)
                .attr('stroke', '#fff');
            d3.selectAll('.treemap-tooltip').remove();
        }});

    // Helper function for text configuration
    function getTextConfig(width, height) {{
        const minWidth = 45;
        const minHeight = 30;

        if (width < minWidth || height < minHeight) return {{ show: false }};

        let titleFontSize, countFontSize, maxTextLength, showCount = false;

        if (width < 80) {{
            titleFontSize = Math.min(9, height * 0.25);
            maxTextLength = Math.floor(width / 6);
            showCount = height > 40;
            countFontSize = 8;
        }} else if (width < 120) {{
            titleFontSize = Math.min(11, height * 0.28);
            maxTextLength = Math.floor(width / 5.5);
            showCount = height > 35;
            countFontSize = Math.min(10, height * 0.22);
        }} else {{
            titleFontSize = Math.min(13, height * 0.3);
            maxTextLength = Math.floor(width / 5);
            showCount = true;
            countFontSize = Math.min(12, height * 0.25);
        }}

        return {{
            show: true,
            titleFontSize: Math.round(titleFontSize),
            countFontSize: Math.round(countFontSize),
            maxTextLength: maxTextLength,
            showCount: showCount && height > 45,
            titleY: Math.min(16, height * 0.35),
            countY: Math.min(30, height * 0.65)
        }};
    }}

    function truncateText(text, maxLength) {{
        if (!text || text.length <= maxLength) return text;
        if (maxLength < 4) return text.substring(0, maxLength);

        const words = text.split(' ');
        if (words.length === 1) {{
            return text.substring(0, maxLength - 2) + '..';
        }}

        let result = words[0];
        for (let i = 1; i < words.length; i++) {{
            if ((result + ' ' + words[i]).length > maxLength) break;
            result += ' ' + words[i];
        }}

        return result.length < text.length ? result + '..' : result;
    }}

    // Add position labels
    positionNodes.each(function(d) {{
        const node = d3.select(this);
        const width = d.x1 - d.x0;
        const height = d.y1 - d.y0;
        const textConfig = getTextConfig(width, height);

        if (!textConfig.show) return;

        const truncatedName = truncateText(d.data.name, textConfig.maxTextLength);

        node.append('text')
            .attr('x', (d.x1 - d.x0) / 2)
            .attr('y', textConfig.titleY)
            .attr('text-anchor', 'middle')
            .attr('font-size', `${{textConfig.titleFontSize}}px`)
            .attr('font-weight', '600')
            .attr('fill', '#333')
            .attr('pointer-events', 'none')
            .style('user-select', 'none')
            .text(truncatedName);

        if (textConfig.showCount) {{
            node.append('text')
                .attr('x', (d.x1 - d.x0) / 2)
                .attr('y', textConfig.countY)
                .attr('text-anchor', 'middle')
                .attr('font-size', `${{textConfig.countFontSize}}px`)
                .attr('font-weight', 'bold')
                .attr('fill', '#666')
                .attr('pointer-events', 'none')
                .style('user-select', 'none')
                .text(`${{d.data.count}}명`);
        }}
    }});

    // Create comparison table
    const tableTitle = document.createElement('h6');
    tableTitle.className = 'mt-4 mb-3 lang-text';
    tableTitle.setAttribute('data-ko', `팀별 ${{config.nameKo}} 변화 상세`);
    tableTitle.setAttribute('data-en', `Detailed ${{config.nameEn}} Changes by Team`);
    tableTitle.setAttribute('data-vi', `Chi tiết thay đổi ${{config.nameVi}} theo nhóm`);
    tableTitle.textContent = tableTitle.getAttribute(`data-${{currentLanguage}}`);
    container.appendChild(tableTitle);

    const table = document.createElement('table');
    table.className = 'table table-sm table-hover';
    table.style.cssText = 'background: white;';

    const teamNameText = {{'ko': '팀명', 'en': 'Team', 'vi': 'Nhóm'}}[currentLanguage];
    const currentMonthText = {{'ko': `${{currentMonthLabel}} ${{config.nameKo}}`, 'en': `${{currentMonthLabel}} ${{config.nameEn}}`, 'vi': `${{currentMonthLabel}} ${{config.nameVi}}`}}[currentLanguage];
    const prevMonthText = {{'ko': `${{prevMonthLabel}} ${{config.nameKo}}`, 'en': `${{prevMonthLabel}} ${{config.nameEn}}`, 'vi': `${{prevMonthLabel}} ${{config.nameVi}}`}}[currentLanguage];
    const changeText = {{'ko': '증감', 'en': 'Change', 'vi': 'Thay đổi'}}[currentLanguage];
    const changeRateText = {{'ko': '증감율', 'en': 'Change %', 'vi': 'Tỷ lệ %'}}[currentLanguage];

    // Calculate totals for count-type metrics, weighted average for percentage-type metrics
    const isPercentageMetric = config.type === 'percentage' || config.type === 'rate';
    let totalCurrent, totalPrevious, totalChange, totalChangePercent;

    if (isPercentageMetric) {{
        // For percentage metrics: calculate weighted average based on team sizes
        const totalTeamSize = teamChanges.reduce((sum, team) => {{
            // Estimate team size from team data if available
            const teamSize = teamData[team.name]?.members?.filter(m => !m.stop_date || m.stop_date === 'nan' || new Date(m.stop_date) > new Date()).length || 1;
            return sum + teamSize;
        }}, 0);

        totalCurrent = teamChanges.reduce((sum, team) => {{
            const teamSize = teamData[team.name]?.members?.filter(m => !m.stop_date || m.stop_date === 'nan' || new Date(m.stop_date) > new Date()).length || 1;
            return sum + (team.current * teamSize / totalTeamSize);
        }}, 0).toFixed(2);

        totalPrevious = teamChanges.reduce((sum, team) => {{
            const teamSize = teamData[team.name]?.members?.filter(m => !m.stop_date || m.stop_date === 'nan' || new Date(m.stop_date) > new Date()).length || 1;
            return sum + (team.previous * teamSize / totalTeamSize);
        }}, 0).toFixed(2);

        totalChange = (totalCurrent - totalPrevious).toFixed(2);
        totalChangePercent = totalPrevious > 0 ? ((totalChange / totalPrevious) * 100).toFixed(1) : '0';
    }} else {{
        // For count metrics: simple sum
        totalCurrent = teamChanges.reduce((sum, team) => sum + team.current, 0);
        totalPrevious = teamChanges.reduce((sum, team) => sum + team.previous, 0);
        totalChange = teamChanges.reduce((sum, team) => sum + team.change, 0);
        totalChangePercent = totalPrevious > 0 ? ((totalChange / totalPrevious) * 100).toFixed(1) : '0';
    }}

    table.innerHTML = `
        <thead style="position: sticky; top: 0; background: #f5f5f5; z-index: 1;">
            <tr>
                <th class="lang-text" data-ko="팀명" data-en="Team" data-vi="Nhóm">${{teamNameText}}</th>
                <th class="lang-text" data-ko="${{currentMonthLabel}} ${{config.nameKo}}" data-en="${{currentMonthLabel}} ${{config.nameEn}}" data-vi="${{currentMonthLabel}} ${{config.nameVi}}">${{currentMonthText}}</th>
                <th class="lang-text" data-ko="${{prevMonthLabel}} ${{config.nameKo}}" data-en="${{prevMonthLabel}} ${{config.nameEn}}" data-vi="${{prevMonthLabel}} ${{config.nameVi}}">${{prevMonthText}}</th>
                <th class="lang-text" data-ko="증감" data-en="Change" data-vi="Thay đổi">${{changeText}}</th>
                <th class="lang-text" data-ko="증감율" data-en="Change %" data-vi="Tỷ lệ %">${{changeRateText}}</th>
            </tr>
        </thead>
        <tbody>
            ${{teamChanges.map(team => `
                <tr style="cursor: pointer;" onclick="showTeamDetailModal('${{team.name}}', '${{kpiKey}}')">
                    <td><strong>${{team.name}}</strong></td>
                    <td>${{team.current}}${{config.unit}}</td>
                    <td>${{team.previous}}${{config.unit}}</td>
                    <td style="color: ${{team.change >= 0 ? '#C62828' : '#2E7D32'}};">
                        ${{team.change >= 0 ? '+' : ''}}${{team.change}}${{config.unit}}
                    </td>
                    <td>
                        <span class="badge bg-${{team.change >= 0 ? 'danger' : 'success'}}">
                            ${{team.change >= 0 ? '+' : ''}}${{team.changePercent}}%
                        </span>
                    </td>
                </tr>
            `).join('')}}
        </tbody>
        <tfoot style="background: #f8f9fa; font-weight: bold; border-top: 2px solid #dee2e6;">
            <tr>
                <td class="lang-text" data-ko="Total" data-en="Total" data-vi="Tổng cộng"><strong>Total</strong></td>
                <td><strong>${{totalCurrent}}${{config.unit}}</strong></td>
                <td><strong>${{totalPrevious}}${{config.unit}}</strong></td>
                <td style="color: ${{totalChange >= 0 ? '#C62828' : '#2E7D32'}};">
                    <strong>${{totalChange >= 0 ? '+' : ''}}${{totalChange}}${{config.unit}}</strong>
                </td>
                <td>
                    <span class="badge bg-${{totalChange >= 0 ? 'danger' : 'success'}}">
                        <strong>${{totalChange >= 0 ? '+' : ''}}${{totalChangePercent}}%</strong>
                    </span>
                </td>
            </tr>
        </tfoot>
    `;

    container.appendChild(table);
}}

// ============================================
// Team Detail Modal Charts
// ============================================

let teamDetailCharts = {{}};

/**
 * Create all 6 charts for team detail modal
 */
function createTeamDetailCharts(teamName, kpiKey) {{
    const config = kpiConfig[kpiKey];
    if (!config) {{
        debugLog(`KPI config not found for: ${{kpiKey}}`);
        return;
    }}

    debugLog(`🎨 Creating team detail charts for ${{teamName}} - ${{config.nameKo}}`);

    // Update modal title
    document.getElementById('teamDetailModalTitle').textContent = `${{teamName}} - ${{config.nameKo}} 상세 분석`;

    // Create all 6 charts
    createTeamMonthlyTrendChart(teamName, kpiKey);
    createTeamWeeklyTrendChart(teamName, kpiKey);
    createTeamRoleTreemap(teamName, kpiKey);  // Changed from Donut to Treemap
    createTeamRoleBarChart(teamName, kpiKey);
    createTeamSunburstChart(teamName, kpiKey);
    createTeamMembersTable(teamName, kpiKey);
}}

/**
 * Chart 1: 월별 팀 [KPI] 트렌드 (최근 6개월)
 */
function createTeamMonthlyTrendChart(teamName, kpiKey) {{
    const config = kpiConfig[kpiKey];
    const monthlyData = extractTeamMonthlyData(teamName, kpiKey);

    const labels = monthlyData.map(d => d.label);
    const values = monthlyData.map(d => parseFloat(d.value) || 0);

    // Update title
    document.getElementById('teamDetailChart1Title').textContent = `월별 ${{teamName}} ${{config.nameKo}} 트렌드 (최근 6개월)`;

    // Destroy existing chart
    if (teamDetailCharts['monthly']) teamDetailCharts['monthly'].destroy();

    const ctx = document.getElementById('teamDetailChart_monthly');
    teamDetailCharts['monthly'] = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: labels,
            datasets: [{{
                label: `${{teamName}} ${{config.nameKo}}`,
                data: values,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            let label = context.parsed.y;
                            if (config.type === 'percentage') label += '%';
                            else label += config.unit;
                            return label;
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: config.unit
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Chart 2: 주차별 팀 [KPI] 트렌드 (20주)
 */
function createTeamWeeklyTrendChart(teamName, kpiKey) {{
    const config = kpiConfig[kpiKey];
    const weeklyData = extractTeamWeeklyData(teamName, kpiKey);

    const labels = weeklyData.map(d => d.label);
    const values = weeklyData.map(d => parseFloat(d.value) || 0);

    // Update title
    document.getElementById('teamDetailChart2Title').textContent = `주차별 ${{teamName}} ${{config.nameKo}} 트렌드 (20주)`;

    // Destroy existing chart
    if (teamDetailCharts['weekly']) teamDetailCharts['weekly'].destroy();

    const ctx = document.getElementById('teamDetailChart_weekly');
    teamDetailCharts['weekly'] = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: labels,
            datasets: [{{
                label: `${{teamName}} ${{config.nameKo}}`,
                data: values,
                borderColor: '#764ba2',
                backgroundColor: 'rgba(118, 75, 162, 0.1)',
                tension: 0.3,
                fill: true,
                pointRadius: 3,
                pointHoverRadius: 5
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            let label = context.parsed.y;
                            if (config.type === 'percentage') label += '%';
                            else label += config.unit;
                            return label;
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: config.unit
                    }}
                }},
                x: {{
                    ticks: {{
                        maxRotation: 45,
                        minRotation: 45
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Helper: Adjust color brightness for multi-level visualization
 */
function adjustBrightness(hex, brightness) {{
    // Remove # if present
    hex = hex.replace('#', '');

    // Convert hex to RGB
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);

    // Adjust brightness (0.0 - 1.0 scale, where 1.0 is original)
    const newR = Math.min(255, Math.floor(r * brightness));
    const newG = Math.min(255, Math.floor(g * brightness));
    const newB = Math.min(255, Math.floor(b * brightness));

    // Convert back to hex
    return '#' + ((1 << 24) + (newR << 16) + (newG << 8) + newB).toString(16).slice(1);
}}

/**
 * Chart 3: Interactive Treemap - 팀내 역할별 인원 분포 (MULTI-LEVEL HIERARCHY)
 */
function createTeamRoleTreemap(teamName, kpiKey) {{
    const config = kpiConfig[kpiKey];
    const team = teamData[teamName];
    if (!team || !team.members) return;

    const members = team.members || [];

    // Debug: Check team data structure
    debugLog(`🔍 Treemap Debug for ${{teamName}}:`, {{
        teamExists: !!team,
        membersExists: !!team.members,
        membersLength: members.length,
        teamKeys: Object.keys(team),
        firstMember: members[0]
    }});

    // Update title
    document.getElementById('teamDetailChart3Title').textContent = `${{teamName}} 역할별 인원 분포 (Interactive Treemap)`;

    // Clear previous content
    const container = document.getElementById('teamDetailTreemap');
    container.innerHTML = '';

    // Check if D3 is available
    if (typeof d3 === 'undefined') {{
        container.innerHTML = '<div style="padding: 40px; text-align: center; color: #999;">D3 라이브러리를 로드할 수 없습니다.</div>';
        return;
    }}

    // Role color mapping
    const roleColors = {{
        'INSPECTOR': '#FF6B6B',
        'TOP-MANAGEMENT': '#4ECDC4',
        'MID-MANAGEMENT': '#45B7D1',
        'SUPPORT': '#96CEB4',
        'PACKING': '#FFEAA7',
        'AUDITOR': '#DDA0DD',
        'REPORT': '#98D8C8',
        'OFFICE & OCPT': '#F7DC6F',
        'UNDEFINED': '#CCCCCC'
    }};

    // Use all team members (no date filtering - team data already filtered appropriately)
    const activeMembers = members;

    // Build hierarchical data structure for Treemap: Role → Position_3rd → Position_4th
    const hierarchyData = {{
        name: teamName,
        children: []
    }};

    // Group by Role → Position_3rd → Position_4th
    const roleMap = new Map();
    activeMembers.forEach(member => {{
        const role = member.role_type || member.role || 'UNDEFINED';
        const pos3rd = member.position_3rd || 'No Position 3rd';
        const pos4th = member.position_4th || 'No Position 4th';

        if (!roleMap.has(role)) {{
            roleMap.set(role, new Map());
        }}
        const pos3rdMap = roleMap.get(role);

        if (!pos3rdMap.has(pos3rd)) {{
            pos3rdMap.set(pos3rd, new Map());
        }}
        const pos4thMap = pos3rdMap.get(pos3rd);

        if (!pos4thMap.has(pos4th)) {{
            pos4thMap.set(pos4th, 0);
        }}
        pos4thMap.set(pos4th, pos4thMap.get(pos4th) + 1);
    }});

    // Convert Map structure to hierarchical data for D3
    roleMap.forEach((pos3rdMap, role) => {{
        const roleNode = {{
            name: role,
            color: roleColors[role] || '#888888',
            children: []
        }};

        pos3rdMap.forEach((pos4thMap, pos3rd) => {{
            const pos3rdNode = {{
                name: pos3rd,
                children: []
            }};

            pos4thMap.forEach((count, pos4th) => {{
                pos3rdNode.children.push({{
                    name: pos4th,
                    value: count
                }});
            }});

            roleNode.children.push(pos3rdNode);
        }});

        hierarchyData.children.push(roleNode);
    }});

    // Debug: Log hierarchy data structure
    debugLog(`📊 Treemap Data for ${{teamName}}:`, {{
        totalRoles: hierarchyData.children.length,
        activeMembers: activeMembers.length,
        hierarchyData: hierarchyData,
        sampleMember: activeMembers[0]
    }});

    // Create D3 Treemap with responsive sizing
    const containerRect = container.getBoundingClientRect();
    const width = Math.max(containerRect.width || container.clientWidth || 600, 400);
    const height = 500;

    const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', height)
        .attr('viewBox', `0 0 ${{width}} ${{height}}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .style('display', 'block')
        .style('font', '12px sans-serif');

    const root = d3.hierarchy(hierarchyData)
        .sum(d => d.value || 0)
        .sort((a, b) => b.value - a.value);

    d3.treemap()
        .size([width, height])
        .paddingOuter(3)
        .paddingTop(20)  // Space for role labels
        .paddingInner(2)
        .tile(d3.treemapSquarify.ratio(1.5))
        .round(true)
        (root);

    // Helper function for text configuration
    const getTextConfig = function(width, height) {{
        const minWidth = 35;
        const minHeight = 25;

        if (width < minWidth || height < minHeight) {{
            return {{ show: false }};
        }}

        let fontSize, showCount = false;
        let maxLength;

        if (width < 60) {{
            fontSize = 8;
            maxLength = Math.floor(width / 7);
        }} else if (width < 100) {{
            fontSize = 9;
            maxLength = Math.floor(width / 6);
            showCount = height > 35;
        }} else {{
            fontSize = 10;
            maxLength = Math.floor(width / 5.5);
            showCount = height > 40;
        }}

        return {{
            show: true,
            fontSize: fontSize,
            maxLength: maxLength,
            showCount: showCount,
            titleY: Math.min(14, height * 0.4),
            countY: Math.min(26, height * 0.7)
        }};
    }};

    const truncateText = function(text, maxLength) {{
        if (!text || text.length <= maxLength) return text;
        if (maxLength < 4) return text.substring(0, maxLength);
        if (maxLength < 8) return text.substring(0, maxLength - 2) + '..';
        return text.substring(0, maxLength - 3) + '...';
    }};

    // First, draw role group boxes (depth 1)
    const roleNodes = svg.selectAll('g.role')
        .data(root.descendants().filter(d => d.depth === 1))
        .join('g')
        .attr('class', 'role')
        .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

    // Add role rectangles with borders
    roleNodes.append('rect')
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0)
        .attr('fill', d => d.data.color || '#888888')
        .attr('fill-opacity', 0.2)
        .attr('stroke', d => d.data.color || '#888888')
        .attr('stroke-width', 2)
        .attr('rx', 3);

    // Add role labels at the top of each role box
    roleNodes.each(function(d) {{
        const node = d3.select(this);
        const width = d.x1 - d.x0;
        const height = d.y1 - d.y0;

        if (width > 50 && height > 30) {{
            // Add background for role label
            node.append('rect')
                .attr('width', Math.min(width - 4, 150))
                .attr('height', 16)
                .attr('x', 2)
                .attr('y', 2)
                .attr('rx', 2)
                .attr('fill', d.data.color || '#888888')
                .attr('fill-opacity', 0.8);

            // Add role text
            node.append('text')
                .attr('x', 5)
                .attr('y', 13)
                .attr('font-size', '10px')
                .attr('font-weight', 'bold')
                .attr('fill', '#fff')
                .text(d.data.name);
        }}
    }});

    // Now draw position boxes (leaf nodes)
    const leaf = svg.selectAll('g.position')
        .data(root.leaves())
        .join('g')
        .attr('class', 'position')
        .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

    // Add position rectangles
    leaf.append('rect')
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0)
        .attr('fill', d => {{
            let node = d;
            while (node.depth > 1) node = node.parent;
            return node.data.color || '#888888';
        }})
        .attr('fill-opacity', d => 0.5 + (d.depth * 0.1))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1)
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {{
            d3.select(this)
                .attr('fill-opacity', 0.8)
                .attr('stroke-width', 2)
                .attr('stroke', '#333');

            // Show tooltip with position info
            const role = d.ancestors().reverse()[1]?.data.name || 'Unknown';
            const pos3rd = d.parent?.data.name || 'Unknown';
            const pos4th = d.data.name;
            const total = activeMembers.length;
            const percentage = ((d.value / total) * 100).toFixed(1);

            const tooltip = d3.select('body').append('div')
                .attr('class', 'position-tooltip')
                .style('position', 'absolute')
                .style('visibility', 'visible')
                .style('background', 'rgba(0, 0, 0, 0.85)')
                .style('color', 'white')
                .style('padding', '10px')
                .style('border-radius', '4px')
                .style('font-size', '11px')
                .style('max-width', '300px')
                .style('z-index', '9999')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px')
                .html(`
                    <strong style="font-size: 12px;">${{pos4th}}</strong><br/>
                    <div style="margin: 5px 0;">
                        <span style="color: #aaa;">Role:</span> ${{role}}<br/>
                        <span style="color: #aaa;">Position:</span> ${{pos3rd}}<br/>
                        <span style="color: #aaa;">인원:</span> <strong>${{d.value}}명</strong> (${{percentage}}%)
                    </div>
                `);
        }})
        .on('mouseout', function(event, d) {{
            d3.select(this)
                .attr('fill-opacity', d => 0.5 + (d.depth * 0.1))
                .attr('stroke-width', 1)
                .attr('stroke', '#fff');

            // Remove tooltip
            d3.selectAll('.position-tooltip').remove();
        }});

    // Add text labels for position boxes
    leaf.each(function(d) {{
        const node = d3.select(this);
        const width = d.x1 - d.x0;
        const height = d.y1 - d.y0;
        const textConfig = getTextConfig(width, height);

        if (!textConfig.show) return;

        const pos4th = d.data.name;
        const value = d.value;

        // Add position text
        const titleText = node.append('text')
            .attr('x', 4)
            .attr('y', textConfig.titleY)
            .attr('font-size', `${{textConfig.fontSize}}px`)
            .attr('font-weight', '500')
            .attr('fill', '#fff')
            .attr('pointer-events', 'none')
            .style('text-shadow', '0 1px 2px rgba(0,0,0,0.7)')
            .style('user-select', 'none');

        // Truncate text based on available width
        const displayName = truncateText(pos4th, textConfig.maxLength);
        titleText.text(displayName);

        // Add count text if there's enough space
        if (textConfig.showCount) {{
            node.append('text')
                .attr('x', 4)
                .attr('y', textConfig.countY)
                .attr('font-size', `${{textConfig.fontSize + 2}}px`)
                .attr('font-weight', 'bold')
                .attr('fill', '#fff')
                .attr('pointer-events', 'none')
                .style('text-shadow', '0 1px 2px rgba(0,0,0,0.7)')
                .style('user-select', 'none')
                .text(`${{value}}명`);
        }}
    }});

    // Build detail table
    const tableBody = document.getElementById('treemapTableBody');
    const tableRows = [];

    // Get previous month for comparison
    const monthsArray = Object.keys(monthlyMetrics).sort();
    const prevMonthIdx = monthsArray.length - 2;
    const prevMonth = prevMonthIdx >= 0 ? monthsArray[prevMonthIdx] : null;
    const prevMonthDates = prevMonth ? getMonthDates(prevMonth) : null;

    roleMap.forEach((pos3rdMap, role) => {{
        pos3rdMap.forEach((pos4thMap, pos3rd) => {{
            pos4thMap.forEach((count, pos4th) => {{
                const percentage = ((count / activeMembers.length) * 100).toFixed(1);

                // Calculate previous month count
                let prevCount = 0;
                let changeText = '-';
                if (prevMonthDates) {{
                    const prevActiveMembers = members.filter(member => {{
                        const entranceDate = member.entrance_date ? new Date(member.entrance_date) : null;
                        const stopDate = member.stop_date ? new Date(member.stop_date) : null;
                        const enteredBefore = !entranceDate || entranceDate <= prevMonthDates.end;
                        const activeAfter = !stopDate || stopDate > prevMonthDates.end;

                        const matchRole = (member.role_type || member.role || 'UNDEFINED') === role;
                        const matchPos3rd = (member.position_3rd || 'No Position 3rd') === pos3rd;
                        const matchPos4th = (member.position_4th || 'No Position 4th') === pos4th;

                        return enteredBefore && activeAfter && matchRole && matchPos3rd && matchPos4th;
                    }});
                    prevCount = prevActiveMembers.length;

                    const change = count - prevCount;
                    if (change > 0) {{
                        changeText = `<span style="color: #28a745; font-weight: 500;">▲ ${{change}}</span>`;
                    }} else if (change < 0) {{
                        changeText = `<span style="color: #dc3545; font-weight: 500;">▼ ${{Math.abs(change)}}</span>`;
                    }} else {{
                        changeText = `<span style="color: #6c757d;">= 0</span>`;
                    }}
                }}

                const roleColor = roleColors[role] || '#888888';
                tableRows.push(`
                    <tr>
                        <td>
                            <span style="display: inline-block; width: 12px; height: 12px; background: ${{roleColor}}; border-radius: 2px; margin-right: 6px;"></span>
                            ${{role}}
                        </td>
                        <td>${{pos3rd}}</td>
                        <td>${{pos4th}}</td>
                        <td><strong>${{count}}명</strong></td>
                        <td>${{percentage}}%</td>
                        <td>${{changeText}}</td>
                    </tr>
                `);
            }});
        }});
    }});

    tableBody.innerHTML = tableRows.join('');
}}

/**
 * Chart 4: 팀내 역할별 [KPI] 현황
 */
function createTeamRoleBarChart(teamName, kpiKey) {{
    const config = kpiConfig[kpiKey];
    const roleData = extractTeamRoleData(teamName, kpiKey);

    const labels = roleData.map(r => r.role);
    const values = roleData.map(r => r.value);

    // Update title
    document.getElementById('teamDetailChart4Title').textContent = `${{teamName}} 역할별 ${{config.nameKo}} 현황`;

    // Destroy existing chart
    if (teamDetailCharts['roleBar']) teamDetailCharts['roleBar'].destroy();

    const ctx = document.getElementById('teamDetailChart_roleBar');
    teamDetailCharts['roleBar'] = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: labels,
            datasets: [{{
                label: config.nameKo,
                data: values,
                backgroundColor: '#667eea',
                borderColor: '#764ba2',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            let label = context.parsed.y;
                            if (config.type === 'percentage') label += '%';
                            else label += config.unit;
                            return label;
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: config.unit
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Chart 5: 5단계 계층 구조 Sunburst 차트 (PLOTLY)
 */
function createTeamSunburstChart(teamName, kpiKey) {{
    // Update title
    document.getElementById('teamDetailChart5Title').textContent = `${{teamName}} 5단계 계층 구조 Sunburst 차트`;

    const container = document.getElementById('teamDetailSunburst');
    container.innerHTML = ''; // Clear previous content

    // Check if Plotly is available
    if (typeof Plotly === 'undefined') {{
        container.innerHTML = '<div style="padding: 40px; text-align: center; color: #999;">Plotly 라이브러리를 로드할 수 없습니다.</div>';
        return;
    }}

    // Create layout with chart and legend side by side
    container.innerHTML = `
        <div style="display: flex; gap: 20px;">
            <div id="sunburstChart" style="flex: 1; min-width: 0;"></div>
            <div id="sunburstLegend" style="width: 250px; background: #fff; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-height: 600px; overflow-y: auto;">
                <h6 style="margin-bottom: 15px; font-weight: 600; border-bottom: 2px solid #e9ecef; padding-bottom: 8px;">계층 구조 범례</h6>
                <div id="legendContent"></div>
            </div>
        </div>
    `;

    const chartContainer = document.getElementById('sunburstChart');

    const team = teamData[teamName];
    if (!team || !team.members) {{
        container.innerHTML = '<div style="padding: 40px; text-align: center; color: #999;">팀 데이터를 찾을 수 없습니다.</div>';
        return;
    }}

    const members = team.members || [];

    // Build 5-level hierarchy: Team → Role → Position1 → Position2 → Position3
    const labels = [teamName];  // Root
    const parents = [''];
    const values = [members.length];
    const colors = [teamName];
    const customdata = [{{ level: 0, count: members.length }}];

    // Role color mapping
    const roleColors = {{
        'INSPECTOR': '#FF6B6B',
        'TOP-MANAGEMENT': '#4ECDC4',
        'MID-MANAGEMENT': '#45B7D1',
        'SUPPORT': '#96CEB4',
        'PACKING': '#FFEAA7',
        'AUDITOR': '#DDA0DD',
        'REPORT': '#98D8C8',
        'OFFICE & OCPT': '#F7DC6F',
        'UNDEFINED': '#CCCCCC'
    }};

    // Level 1: Group by Role (실제 필드명: role_type)
    const roleGroups = {{}};
    members.forEach(member => {{
        const role = member.role_type || member.role || 'UNDEFINED';
        if (!roleGroups[role]) roleGroups[role] = [];
        roleGroups[role].push(member);
    }});

    Object.entries(roleGroups).forEach(([role, roleMembers]) => {{
        labels.push(role);
        parents.push(teamName);
        values.push(roleMembers.length);
        colors.push(role);
        customdata.push({{ level: 1, count: roleMembers.length }});

        // Level 2: Group by Position_1st (실제 필드명: position_1st)
        const pos1Groups = {{}};
        roleMembers.forEach(member => {{
            const pos1 = member.position_1st || member.Position || 'UNDEFINED';
            const key = `${{role}}|${{pos1}}`;
            if (!pos1Groups[key]) pos1Groups[key] = [];
            pos1Groups[key].push(member);
        }});

        Object.entries(pos1Groups).forEach(([key, pos1Members]) => {{
            const pos1 = key.split('|')[1];
            const pos1Label = `${{role}}→${{pos1}}`;

            labels.push(pos1Label);
            parents.push(role);
            values.push(pos1Members.length);
            colors.push(role);
            customdata.push({{ level: 2, count: pos1Members.length }});

            // Level 3: Group by Position_2nd (실제 필드명: position_2nd)
            const pos2Groups = {{}};
            pos1Members.forEach(member => {{
                const pos2 = member.position_2nd || '';
                if (pos2) {{
                    const key2 = `${{pos1Label}}|${{pos2}}`;
                    if (!pos2Groups[key2]) pos2Groups[key2] = [];
                    pos2Groups[key2].push(member);
                }}
            }});

            if (Object.keys(pos2Groups).length > 0) {{
                Object.entries(pos2Groups).forEach(([key2, pos2Members]) => {{
                    const pos2 = key2.split('|')[1];
                    const pos2Label = `${{pos1Label}}→${{pos2}}`;

                    labels.push(pos2Label);
                    parents.push(pos1Label);
                    values.push(pos2Members.length);
                    colors.push(role);
                    customdata.push({{ level: 3, count: pos2Members.length }});

                    // Level 4: Group by Position_3rd (실제 필드명: position_3rd)
                    const pos3Groups = {{}};
                    pos2Members.forEach(member => {{
                        const pos3 = member.position_3rd || '';
                        if (pos3) {{
                            const key3 = `${{pos2Label}}|${{pos3}}`;
                            if (!pos3Groups[key3]) pos3Groups[key3] = [];
                            pos3Groups[key3].push(member);
                        }}
                    }});

                    if (Object.keys(pos3Groups).length > 0) {{
                        Object.entries(pos3Groups).forEach(([key3, pos3Members]) => {{
                            const pos3 = key3.split('|')[1];
                            const pos3Label = `${{pos2Label}}→${{pos3}}`;

                            labels.push(pos3Label);
                            parents.push(pos2Label);
                            values.push(pos3Members.length);
                            colors.push(role);
                            customdata.push({{ level: 4, count: pos3Members.length }});
                        }});
                    }}
                }});
            }}
        }});
    }});

    // Map colors based on role
    const mappedColors = colors.map(c => roleColors[c] || '#888888');

    const data = [{{
        type: 'sunburst',
        labels: labels,
        parents: parents,
        values: values,
        text: labels,
        hovertemplate: '<b>%{{label}}</b><br>인원: %{{value}}명<br><extra></extra>',
        marker: {{
            colors: mappedColors,
            line: {{ width: 2, color: '#fff' }}
        }},
        branchvalues: 'total'
    }}];

    const layout = {{
        margin: {{ t: 40, l: 40, r: 40, b: 40 }},
        height: 600,
        sunburstcolorway: Object.values(roleColors),
        extendsunburstcolors: true,
        font: {{ size: 11 }},  // Smaller font to prevent text clipping
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
    }};

    const config = {{
        responsive: true,
        displayModeBar: false
    }};

    Plotly.newPlot(chartContainer, data, layout, config);

    // Generate legend content
    const legendContent = document.getElementById('legendContent');
    const legendHTML = [];

    // Group by role for legend
    const roleStats = {{}};
    Object.entries(roleGroups).forEach(([role, members]) => {{
        roleStats[role] = {{
            count: members.length,
            color: roleColors[role] || '#888888',
            percentage: ((members.length / team.members.length) * 100).toFixed(1)
        }};
    }});

    // Sort by count descending
    const sortedRoles = Object.entries(roleStats).sort((a, b) => b[1].count - a[1].count);

    legendHTML.push('<div style="margin-bottom: 15px;">');
    legendHTML.push('<strong style="font-size: 0.85rem; color: #666;">레벨 1: 역할 (Role)</strong>');
    sortedRoles.forEach(([role, stats]) => {{
        legendHTML.push(`
            <div class="legend-item" style="display: flex; align-items: center; padding: 6px 0; font-size: 0.85rem; cursor: pointer; border-radius: 4px; transition: background 0.2s;"
                 onmouseover="this.style.background='#f8f9fa'"
                 onmouseout="this.style.background='transparent'"
                 data-role="${{role}}">
                <span style="width: 18px; height: 18px; background: ${{stats.color}}; border-radius: 3px; margin-right: 8px; border: 1px solid #ddd; flex-shrink: 0;"></span>
                <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${{role}}</span>
                <span style="font-weight: 600; margin-left: 8px; flex-shrink: 0;">${{stats.count}}명</span>
                <span style="font-size: 0.75rem; color: #666; margin-left: 4px; flex-shrink: 0;">(${{stats.percentage}}%)</span>
            </div>
        `);
    }});
    legendHTML.push('</div>');

    // Add interaction note
    legendHTML.push(`
        <div style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-left: 3px solid #2196F3; border-radius: 4px; font-size: 0.75rem; color: #1976d2;">
            <strong>💡 Tip:</strong> Sunburst 차트를 클릭하여 계층을 탐색하세요!
        </div>
    `);

    legendContent.innerHTML = legendHTML.join('');

    // Add click event to legend items to highlight corresponding sunburst section
    document.querySelectorAll('.legend-item').forEach(item => {{
        item.addEventListener('click', function() {{
            const role = this.getAttribute('data-role');
            debugLog('범례 클릭:', role);
            // Could add visual feedback on sunburst chart here
        }});
    }});
}}

/**
 * Chart 6: 팀원 상세 정보 테이블 (SORTABLE)
 */
function createTeamMembersTable(teamName, kpiKey) {{
    // Update title
    document.getElementById('teamDetailChart6Title').textContent = `${{teamName}} 팀원 상세 정보`;

    const team = teamData[teamName];
    if (!team || !team.members) return;

    const members = team.members || [];
    const tbody = document.getElementById('teamDetailMembersTableBody');
    tbody.innerHTML = '';

    members.forEach(member => {{
        const row = document.createElement('tr');
        row.style.cssText = 'transition: background-color 0.2s;';
        row.onmouseenter = function() {{ this.style.backgroundColor = '#f8f9fa'; }};
        row.onmouseleave = function() {{ this.style.backgroundColor = ''; }};

        // 실제 필드명 매핑 (소문자 언더스코어)
        const role = member.role_type || member.role || 'UNDEFINED';
        const pos1 = member.position_1st || member.Position || '';
        const pos2 = member.position_2nd || '';
        const name = member.full_name || member.name || '';
        const empNo = member.employee_no || member.id || '';
        const entranceDate = member.entrance_date || '';

        // Calculate Years of Service (근속년수)
        let yearsOfService = 0;
        if (entranceDate && entranceDate !== 'nan') {{
            const entrance = new Date(entranceDate);
            const today = new Date();
            if (!isNaN(entrance.getTime())) {{
                yearsOfService = ((today - entrance) / (1000 * 60 * 60 * 24 * 365)).toFixed(1);
            }}
        }}

        // Get attendance data
        const workingDays = member.working_days || 0;
        const absentDays = member.absent_days || 0;
        const absenceRate = workingDays > 0 ? ((absentDays / workingDays) * 100).toFixed(1) : '0.0';

        row.innerHTML = `
            <td style="padding: 8px;">${{role}}</td>
            <td style="padding: 8px;">${{pos1}}</td>
            <td style="padding: 8px;">${{pos2}}</td>
            <td style="padding: 8px;">${{name}}</td>
            <td style="padding: 8px; text-align: center;">${{empNo}}</td>
            <td style="padding: 8px; text-align: center;">${{entranceDate}}</td>
            <td style="padding: 8px; text-align: center;">${{yearsOfService}}</td>
            <td style="padding: 8px; text-align: center;">${{workingDays}}</td>
            <td style="padding: 8px; text-align: center;">${{absentDays}}</td>
            <td style="padding: 8px; text-align: center;">${{absenceRate}}%</td>
        `;
        tbody.appendChild(row);
    }});

    // Add Total row at the bottom
    if (members.length > 0) {{
        // Calculate totals and averages
        let totalWorkingDays = 0;
        let totalAbsentDays = 0;
        let totalYearsOfService = 0;
        let validYearsCount = 0;

        members.forEach(member => {{
            totalWorkingDays += member.working_days || 0;
            totalAbsentDays += member.absent_days || 0;

            const entranceDate = member.entrance_date;
            if (entranceDate && entranceDate !== 'nan') {{
                const entrance = new Date(entranceDate);
                const today = new Date();
                if (!isNaN(entrance.getTime())) {{
                    totalYearsOfService += (today - entrance) / (1000 * 60 * 60 * 24 * 365);
                    validYearsCount++;
                }}
            }}
        }});

        const avgYearsOfService = validYearsCount > 0 ? (totalYearsOfService / validYearsCount).toFixed(1) : '0.0';
        const avgWorkingDays = (totalWorkingDays / members.length).toFixed(1);
        const avgAbsentDays = (totalAbsentDays / members.length).toFixed(1);
        const avgAbsenceRate = totalWorkingDays > 0 ? ((totalAbsentDays / totalWorkingDays) * 100).toFixed(1) : '0.0';

        const totalRow = document.createElement('tr');
        totalRow.style.cssText = 'background-color: #e3f2fd; font-weight: 600; border-top: 2px solid #1976d2;';

        totalRow.innerHTML = `
            <td style="padding: 8px; font-weight: 700;">TOTAL</td>
            <td style="padding: 8px;">합계</td>
            <td style="padding: 8px;"></td>
            <td style="padding: 8px;"></td>
            <td style="padding: 8px; text-align: center; font-weight: 700;">${{members.length}}명</td>
            <td style="padding: 8px;"></td>
            <td style="padding: 8px; text-align: center;">${{avgYearsOfService}}</td>
            <td style="padding: 8px; text-align: center;">${{avgWorkingDays}}</td>
            <td style="padding: 8px; text-align: center;">${{avgAbsentDays}}</td>
            <td style="padding: 8px; text-align: center;">${{avgAbsenceRate}}%</td>
        `;
        tbody.appendChild(totalRow);
    }}
}}

/**
 * Sort Team Member Table
 */
function sortTeamMemberTable(header, columnIndex) {{
    const table = document.getElementById('teamDetailMembersTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // 현재 정렬 상태 확인
    const currentIcon = header.querySelector('span');
    const isAscending = currentIcon.innerHTML.includes('▼');

    // 모든 헤더 아이콘 초기화
    table.querySelectorAll('th span').forEach(span => {{
        span.innerHTML = '▼';
        span.style.color = '#666';
    }});

    // 클릭한 헤더 아이콘 업데이트
    currentIcon.innerHTML = isAscending ? '▲' : '▼';
    currentIcon.style.color = '#007bff';

    // 정렬
    rows.sort((a, b) => {{
        const aCell = a.cells[columnIndex];
        const bCell = b.cells[columnIndex];

        if (!aCell || !bCell) return 0;

        const aText = aCell.textContent.trim();
        const bText = bCell.textContent.trim();

        let compareResult = 0;

        // Employee No (column 4) - 숫자로 정렬
        if (columnIndex === 4) {{
            const aNum = parseInt(aText.replace(/\\D/g, '')) || 0;
            const bNum = parseInt(bText.replace(/\\D/g, '')) || 0;
            compareResult = aNum - bNum;
        }}
        // Entrance Date (column 5) - 날짜로 정렬
        else if (columnIndex === 5) {{
            const aDate = new Date(aText);
            const bDate = new Date(bText);
            compareResult = aDate - bDate;
        }}
        // Years of Service (column 6) - 숫자로 정렬
        else if (columnIndex === 6) {{
            const aNum = parseFloat(aText) || 0;
            const bNum = parseFloat(bText) || 0;
            compareResult = aNum - bNum;
        }}
        // Working Days (column 7) - 숫자로 정렬
        else if (columnIndex === 7) {{
            const aNum = parseInt(aText) || 0;
            const bNum = parseInt(bText) || 0;
            compareResult = aNum - bNum;
        }}
        // Absent Days (column 8) - 숫자로 정렬
        else if (columnIndex === 8) {{
            const aNum = parseInt(aText) || 0;
            const bNum = parseInt(bText) || 0;
            compareResult = aNum - bNum;
        }}
        // Absence Rate (column 9) - 숫자로 정렬
        else if (columnIndex === 9) {{
            const aNum = parseFloat(aText.replace('%', '')) || 0;
            const bNum = parseFloat(bText.replace('%', '')) || 0;
            compareResult = aNum - bNum;
        }}
        // 텍스트 정렬
        else {{
            compareResult = aText.localeCompare(bText);
        }}

        return isAscending ? compareResult : -compareResult;
    }});

    // 정렬된 행을 테이블에 다시 추가
    rows.forEach(row => tbody.appendChild(row));
}}

// Modal 1: Total Employees
function showModal1() {{
    // Destroy existing charts
    if (modalCharts['modal1_monthly']) modalCharts['modal1_monthly'].destroy();
    if (modalCharts['modal1_weekly']) modalCharts['modal1_weekly'].destroy();
    if (modalCharts['modal1_teams']) modalCharts['modal1_teams'].destroy();

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('modal1'));
    modal.show();

    // Create charts after modal is shown
    setTimeout(() => {
        createEnhancedTotalEmployeesCharts();
    }, 300);
}

function createEnhancedTotalEmployeesCharts() {
    // Convert monthlyMetrics object to array and sort by date
    const metricsArray = Object.entries(monthlyMetrics)
        .map(([month, data]) => ({
            month: month,
            month_label: month,
            ...data
        }))
        .sort((a, b) => a.month.localeCompare(b.month));

    // 1. 월별 총 재직자 수 트렌드 (using chart_utils.js)
    const monthLabels = metricsArray.map(m => {
        const parts = m.month.split('-');
        return parseInt(parts[1]) + '월';
    });
    const monthValues = metricsArray.map(m => m.total_employees || 0);

    modalCharts['modal1_monthly'] = createMonthlyTrendChart(
        'modalChart1_monthly',
        monthLabels,
        monthValues,
        {
            title: '월별 총 재직자 수 트렌드',
            lineColor: '#FF6B6B',
            lineBackgroundColor: 'rgba(255, 107, 107, 0.1)',
            trendlineColor: '#45B7D1'
        }
    );

    // 2. 주차별 총 재직자 수 트렌드 (using chart_utils.js)
    // Extract weekly data inline - only include weeks with actual data
    const allWeeklyData = [];
    metricsArray.forEach((month) => {
        if (month.weekly_metrics && typeof month.weekly_metrics === 'object') {
            Object.entries(month.weekly_metrics).sort().forEach(([weekKey, weekData]) => {
                const employeeCount = weekData.total_employees || 0;
                // Only include weeks with actual employee data (> 0)
                if (employeeCount > 0) {
                    allWeeklyData.push({
                        label: weekData.date || `${month.month.substring(5)} ${weekKey}`,
                        value: employeeCount
                    });
                }
            });
        } else if (Array.isArray(month.weekly_metrics)) {
            month.weekly_metrics.forEach((week, weekIdx) => {
                const employeeCount = week.total_employees || 0;
                // Only include weeks with actual employee data (> 0)
                if (employeeCount > 0) {
                    allWeeklyData.push({
                        label: `${month.month.substring(5)} W${weekIdx + 1}`,
                        value: employeeCount
                    });
                }
            });
        }
    });

    debugLog('주차별 데이터 확인:', allWeeklyData.length, 'weeks');

    if (allWeeklyData.length > 0) {
        modalCharts['modal1_weekly'] = createWeeklyTrendChart(
            'modalChart1_weekly',
            allWeeklyData,
            {
                title: '주차별 총 재직자 수 트렌드',
                lineColor: '#4ECDC4',
                lineBackgroundColor: 'rgba(78, 205, 196, 0.1)',
                trendlineColor: '#95E1D3'
            }
        );
    } else {
        // Show no data message
        const canvas = document.getElementById('modalChart1_weekly');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.font = '16px Arial';
            ctx.fillStyle = '#666';
            ctx.textAlign = 'center';
            ctx.fillText('주차별 데이터가 없습니다', canvas.width / 2, canvas.height / 2);
        }
    }

    // 3. 팀별 인원 분포 (Horizontal Bar Chart)
    // ✅ Use common countActiveEmployees function
    const latestMonth = metricsArray[metricsArray.length - 1];

    // Calculate month-end date for current month
    const currentMonthDate = new Date(targetMonth + '-01');
    const currentMonthEnd = new Date(currentMonthDate);
    currentMonthEnd.setMonth(currentMonthEnd.getMonth() + 1);
    currentMonthEnd.setDate(0);

    const teamDistribution = Object.entries(teamData)
        .map(([name, data]) => {{
            // ✅ Use common function: count active employees at month-end
            const activeCount = data.members ? countActiveEmployees(data.members, currentMonthEnd) : 0;

            return {{
                name: name,
                total: activeCount,
                percentage: (activeCount / latestMonth.total_employees * 100).toFixed(1)
            }};
        }})
        .sort((a, b) => b.total - a.total);

    const teamNames = teamDistribution.map(t => t.name);
    const teamCounts = teamDistribution.map(t => t.total);
    const teamPercentages = teamDistribution.map(t => t.percentage);
    const teamColors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2", "#FF9FF3"];

    const ctx2 = document.getElementById('modalChart1_teams').getContext('2d');

    // Destroy existing chart if it exists to prevent stuck tooltips
    if (modalCharts['modal1_teams']) {
        modalCharts['modal1_teams'].destroy();
    }

    modalCharts['modal1_teams'] = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: teamNames,
            datasets: [{
                label: '인원 수',
                data: teamCounts,
                backgroundColor: teamColors
            }]
        },
        options: {
            indexAxis: 'y',  // Horizontal bar chart
            responsive: true,
            maintainAspectRatio: false,
            onClick: function(event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const teamName = teamNames[index];
                    showTeamDetailModal(teamName, 'total_employees');
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '팀별 인원 분포 (클릭하여 상세보기)',
                    align: 'start',
                    font: { size: 18, weight: 600 },
                    padding: { bottom: 10 },
                    color: '#333'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            const count = teamCounts[index];
                            const percent = teamPercentages[index];
                            return count + '명 (' + percent + '%)';
                        }
                    }
                },
                legend: { display: false }
            },
            scales: {
                x: { beginAtZero: true }
            }
        }
    });

    // 3. 팀별 인원 변화 (전월 대비) - Grouped Bar Chart
    // ✅ FIXED: Calculate actual employee counts using entrance/stop dates instead of ratio estimation
    const currentMonthIdx = metricsArray.findIndex(m => m.month === targetMonth);
    const previousMonthData = currentMonthIdx > 0 ? metricsArray[currentMonthIdx - 1] : null;

    if (previousMonthData) {{
        // Calculate team counts for previous and current month
        const prevTeamCounts = {{}};
        const currentTeamCounts = {{}};

        // Get team counts from teamData for current month (already calculated above)
        teamNames.forEach((teamName, idx) => {{
            currentTeamCounts[teamName] = teamCounts[idx];
        }});

        // Use pre-calculated monthlyTeamCounts for previous month (consistent with table)
        const prevMonthStats = monthlyTeamCounts[previousMonthData.month] || {{}};

        Object.entries(prevMonthStats).forEach(([teamName, count]) => {{
            prevTeamCounts[teamName] = count;
        }});

        // Calculate changes
        const teamChanges = teamNames.map(teamName => {
            const prev = prevTeamCounts[teamName] || 0;
            const current = currentTeamCounts[teamName] || 0;
            return current - prev;
        });

        // Format month labels (e.g., "2025-08" -> "8월", remove leading zero)
        const prevMonthLabel = parseInt(previousMonthData.month.split('-')[1]) + '월';
        const currentMonthLabel = parseInt(targetMonth.split('-')[1]) + '월';

        const ctx4 = document.getElementById('modalChart1_change').getContext('2d');

        // Destroy existing chart if it exists to prevent stuck tooltips
        if (modalCharts['modal1_change']) {
            modalCharts['modal1_change'].destroy();
        }

        modalCharts['modal1_change'] = new Chart(ctx4, {
            type: 'bar',
            data: {
                labels: teamNames,
                datasets: [
                    {
                        label: prevMonthLabel,
                        data: teamNames.map(name => prevTeamCounts[name] || 0),
                        backgroundColor: '#FFD93D'
                    },
                    {
                        label: currentMonthLabel,
                        data: teamCounts,
                        backgroundColor: '#6BCB77'
                    }
                ]
            },
            options: {
                indexAxis: 'y',  // Horizontal grouped bar chart
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `팀별 인원 분포 및 전월 대비 변화 (${prevMonthLabel} vs ${currentMonthLabel})`,
                        align: 'start',
                        font: { size: 18, weight: 600 },
                        padding: { bottom: 10 },
                        color: '#333'
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'point',
                        intersect: true,
                        animation: {
                            duration: 200
                        },
                        callbacks: {
                            label: function(context) {
                                const teamName = teamNames[context.dataIndex];
                                const value = context.parsed.x;
                                const change = teamChanges[context.dataIndex];
                                const changeText = change >= 0 ? `(+${change})` : `(${change})`;
                                return context.dataset.label + ': ' + value + '명 ' + changeText;
                            },
                            afterLabel: function(context) {
                                // Only show change for current month dataset
                                if (context.datasetIndex === 1) {
                                    const change = teamChanges[context.dataIndex];
                                    const changePercent = prevTeamCounts[teamNames[context.dataIndex]] ?
                                        ((change / prevTeamCounts[teamNames[context.dataIndex]]) * 100).toFixed(1) : '0.0';
                                    const sign = change >= 0 ? '+' : '';
                                    return `전월 대비: ${sign}${change}명 (${sign}${changePercent}%)`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 20
                        }
                    }
                }
            }
        });
    } else {
        // If previous month data not available, show message
        const ctx4 = document.getElementById('modalChart1_change').getContext('2d');
        ctx4.font = '16px Arial';
        ctx4.fillStyle = '#666';
        ctx4.textAlign = 'center';
        ctx4.fillText('전월 데이터가 없습니다', ctx4.canvas.width / 2, ctx4.canvas.height / 2);
    }

    // 5. Treemap Chart and Comparison Table
    createTreemapAndTable();
}

function createTreemapAndTable() {{
    const container = document.getElementById('treemapContainer');
    if (!container) return;

    container.innerHTML = '';  // Clear existing content

    // Get current and previous month data
    const metricsArray = Object.entries(monthlyMetrics)
        .map(([month, data]) => ({{ month, ...data }}))
        .sort((a, b) => a.month.localeCompare(b.month));

    if (metricsArray.length === 0) return;

    const currentMonth = metricsArray[metricsArray.length - 1];
    const previousMonth = metricsArray.length > 1 ? metricsArray[metricsArray.length - 2] : null;

    debugLog('Treemap Debug:');
    debugLog('  metricsArray months:', metricsArray.map(m => m.month));
    debugLog('  currentMonth:', currentMonth.month);
    debugLog('  previousMonth:', previousMonth ? previousMonth.month : 'none');

    // Format month labels (remove leading zero)
    const currentMonthLabel = parseInt(currentMonth.month.split('-')[1]) + '월';
    const prevMonthLabel = previousMonth ? parseInt(previousMonth.month.split('-')[1]) + '월' : '';

    debugLog('  currentMonthLabel:', currentMonthLabel);
    debugLog('  prevMonthLabel:', prevMonthLabel);

    // Determine reference date labels dynamically based on report generation date
    const reportDate = new Date('{report_date_str}');  // Report generation date from Python
    const currentMonthStart = new Date(currentMonth.month + '-01');
    const currentMonthEnd = new Date(currentMonth.month + '-01');
    currentMonthEnd.setMonth(currentMonthEnd.getMonth() + 1);
    currentMonthEnd.setDate(0);  // Last day of month

    const prevMonthStart = previousMonth ? new Date(previousMonth.month + '-01') : null;
    const prevMonthEnd = previousMonth ? new Date(previousMonth.month + '-01') : null;
    if (prevMonthEnd) {{
        prevMonthEnd.setMonth(prevMonthEnd.getMonth() + 1);
        prevMonthEnd.setDate(0);  // Last day of month
    }}

    // Dynamic reference date labels
    let currentRefLabel = '';
    let prevRefLabel = '';

    // Current month: Check if report date is within current month
    if (reportDate >= currentMonthStart && reportDate <= currentMonthEnd) {{
        // Report generated during current month - uses report date
        const reportDay = reportDate.getDate();
        currentRefLabel = `(${{reportDay}}일 기준)`;
    }} else {{
        // Report generated outside current month - uses month end
        currentRefLabel = '(말일 기준)';
    }}

    // Previous month: Always uses month end (report date can't be in past month)
    prevRefLabel = '(말일 기준)';

    // Use pre-calculated team counts from Python
    const currentTeamStats = monthlyTeamCounts[currentMonth.month] || {{}};
    const prevTeamStats = previousMonth ? (monthlyTeamCounts[previousMonth.month] || {{}}) : {{}};

    debugLog('  Using pre-calculated monthlyTeamCounts');
    debugLog('  currentMonth:', currentMonth.month, 'stats:', currentTeamStats);
    debugLog('  previousMonth:', previousMonth ? previousMonth.month : 'none', 'stats:', prevTeamStats);

    debugLog('  currentTeamStats:', currentTeamStats);

    // Create title
    const title = document.createElement('h4');
    title.style.cssText = 'margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;';
    title.textContent = `팀별 인원 분포 및 ${{prevMonthLabel || '전월'}} 대비 변화`;
    container.appendChild(title);

    // Create treemap container with responsive width
    const treemapDiv = document.createElement('div');
    treemapDiv.id = 'teamDistributionTreemap';
    treemapDiv.style.cssText = 'height: 600px; background: white; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; position: relative; width: 100%;';
    container.appendChild(treemapDiv);

    // Check if D3 is available
    if (typeof d3 === 'undefined') {{
        treemapDiv.innerHTML = '<div style="padding: 40px; text-align: center; color: #999;">D3 라이브러리를 로드할 수 없습니다.</div>';
        return;
    }}

    // Create detail table container (initially hidden)
    const detailTableDiv = document.createElement('div');
    detailTableDiv.id = 'positionDetailTable';
    detailTableDiv.style.cssText = 'display: none; margin-top: 20px; background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px;';
    container.appendChild(detailTableDiv);

    // Function to simplify position names (코드를 직관적인 이름으로 변환)
    const simplifyPositionName = (position) => {{
        // Map complex position codes to simple names
        const positionMap = {{
            // Quality positions
            'ASSEMBLY LINE TQC': '조립 품질검사',
            'ASSEMBLY LINE RQC': '조립 품질관리',
            'STITCHING LINE TQC': '봉제 품질검사',
            'STITCHING LINE RQC': '봉제 품질관리',
            'STITCHING INLINE INSPECTOR': '봉제 인라인 검사',
            'CUTTING TQC': '재단 품질검사',
            'CUTTING RQC': '재단 품질관리',
            'LASTING TQC': '라스팅 품질검사',
            'LASTING RQC': '라스팅 품질관리',
            'STOCKFITTING TQC': '창고 품질검사',
            'STOCKFITTING RQC': '창고 품질관리',
            'OUTSOLE RQC': '아웃솔 품질관리',
            'QUALITY LINE AUDIT INSPECTOR': '품질 감사원',
            'FACTORY AUDIT LEADER': '공장 감사 리더',
            'QA MANAGER': 'QA 매니저',
            'QA TEAM LEADER': 'QA 팀 리더',
            'QA INSPECTOR': 'QA 검사원',
            'QIP MANAGER & QC': 'QIP 매니저',

            // Production positions
            'SAMPLE PPC SUPERVISOR': '샘플 생산관리',
            'SAMPLE PRODUCTION MANAGER': '샘플 생산 매니저',
            'SAMPLE MOLD WORKER': '샘플 몰드',
            'SAMPLE CUTTING OPERATOR': '샘플 재단',
            'SAMPLE STITCHING OPERATOR': '샘플 봉제',
            'SAMPLE LASTING OPERATOR': '샘플 라스팅',
            'MAIN PRODUCTION PRODUCTION MANAGER': '생산 매니저',
            'ASSEMBLY LINE PRODUCTION LINE CHARGE': '조립 라인 담당',
            'STITCHING GROUP LEADER': '봉제 그룹 리더',
            'CUTTING LINE CHARGE': '재단 라인 담당',
            'LASTING LINE CHARGE': '라스팅 라인 담당',
            'STROBEL LINE CHARGE': '스트로벨 라인 담당',

            // Department level positions (position_2nd)
            'ASSEMBLY': '조립부',
            'STITCHING': '봉제부',
            'CUTTING': '재단부',
            'LASTING': '라스팅부',
            'STOCKFITTING': '창고부',
            'BOTTOM': '바닥부',
            'REPACKING': '재포장부',
            'MTL': '자재부',
            'NEW': '신규부',
            'QSC': 'QSC부'
        }};

        return positionMap[position] || position.replace(/_/g, ' ').toLowerCase().replace(/\\b\\w/g, c => c.toUpperCase());
    }};

    // Prepare team data with position groups instead of individual employees
    const teams = Object.entries(currentTeamStats).map(([name, current]) => {{
        const prev = prevTeamStats[name] || 0;
        const change = current - prev;
        const changePercent = prev > 0 ? ((change / prev) * 100).toFixed(1) : 0;

        // Group team members by position/role instead of individual names
        const positionGroups = {{}};

        if (teamData[name] && teamData[name].members) {{
            const activeMembers = teamData[name].members.filter(member => {{
                const stopDate = member.stop_date;
                return !stopDate || stopDate === 'nan' || new Date(stopDate) > new Date();
            }});

            // Group by position_2nd or position_3rd
            activeMembers.forEach(member => {{
                // Use position_2nd as primary grouping, fallback to position_3rd
                let positionKey = member.position_2nd;

                // If no position_2nd or it's generic, use position_3rd
                if (!positionKey || positionKey === 'nan' || positionKey === '') {{
                    positionKey = member.position_3rd || 'Other';
                }}

                // Simplify the position name
                const simplifiedPosition = simplifyPositionName(positionKey);

                if (!positionGroups[simplifiedPosition]) {{
                    positionGroups[simplifiedPosition] = {{
                        name: simplifiedPosition,
                        originalPosition: positionKey,
                        value: 0,
                        employees: []
                    }};
                }}

                positionGroups[simplifiedPosition].value++;
                positionGroups[simplifiedPosition].employees.push(member.full_name || member.employee_no);
            }});
        }}

        // Convert position groups to array for D3 hierarchy
        const positionGroupsArray = Object.values(positionGroups)
            .sort((a, b) => b.value - a.value); // Sort by count

        return {{
            name,
            displayName: name.replace(/_/g, ' '),  // Display name without underscores
            total: current,
            prev,
            change,
            changePercent: parseFloat(changePercent),
            children: positionGroupsArray  // Position groups instead of individual members
        }};
    }}).sort((a, b) => b.total - a.total);

    // Build hierarchical data for D3 with nested structure
    const hierarchyData = {{
        name: '전체 인원',
        children: teams.map(team => ({{
            name: team.displayName,
            value: team.total,
            change: team.change,
            changePercent: team.changePercent,
            prev: team.prev,
            children: team.children && team.children.length > 0 ? team.children : null  // Add position groups as children
        }}))
    }};

    // Create D3 Treemap with truly responsive width
    const containerRect = treemapDiv.getBoundingClientRect();
    const width = Math.max(containerRect.width || treemapDiv.clientWidth || 800, 400);  // Minimum width of 400px
    const height = 600;

    const svg = d3.select('#teamDistributionTreemap')
        .append('svg')
        .attr('width', '100%')
        .attr('height', height)
        .attr('viewBox', `0 0 ${{width}} ${{height}}`)
        .attr('preserveAspectRatio', 'xMidYMid meet')
        .style('font', '10px sans-serif')
        .style('display', 'block')
        .style('max-width', '100%')
        .style('margin', '0 auto');

    // Add resize observer for better responsive behavior
    if (typeof ResizeObserver !== 'undefined') {{
        const resizeObserver = new ResizeObserver(entries => {{
            for (let entry of entries) {{
                const newWidth = Math.max(entry.contentRect.width, 400);
                svg.attr('viewBox', `0 0 ${{newWidth}} ${{height}}`);
            }}
        }});
        resizeObserver.observe(treemapDiv);
    }} else {{
        // Fallback to window resize event
        let resizeTimeout;
        window.addEventListener('resize', function() {{
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {{
                const newRect = treemapDiv.getBoundingClientRect();
                const newWidth = Math.max(newRect.width || treemapDiv.clientWidth, 400);
                svg.attr('viewBox', `0 0 ${{newWidth}} ${{height}}`);
            }}, 250);
        }});
    }}

    // Function to show position detail table
    const showPositionDetail = (positionData, teamName) => {{
        const detailDiv = document.getElementById('positionDetailTable');
        if (!detailDiv) return;

        // Get employees for this position group
        const employees = positionData.employees || [];

        if (employees.length === 0) {{
            detailDiv.style.display = 'none';
            return;
        }}

        // Get full employee data
        const teamEmployees = teamData[teamName] && teamData[teamName].members ?
            teamData[teamName].members.filter(member => {{
                const stopDate = member.stop_date;
                const isActive = !stopDate || stopDate === 'nan' || new Date(stopDate) > new Date();
                return isActive && employees.includes(member.full_name || member.employee_no);
            }}) : [];

        if (teamEmployees.length === 0) {{
            detailDiv.style.display = 'none';
            return;
        }}

        // Create detail table HTML
        let tableHTML = `
            <h5 style="margin: 0 0 15px 0; color: #333;">
                ${{positionData.name}} - 상세 정보 (${{teamEmployees.length}}명)
            </h5>
            <div style="overflow-x: auto;">
                <table class="table table-hover table-sm" style="font-size: 12px;">
                    <thead class="table-light">
                        <tr>
                            <th style="position: sticky; left: 0; background: #f8f9fa;">이름</th>
                            <th>사번</th>
                            <th>Role Category</th>
                            <th>Position 1st</th>
                            <th>Position 2nd</th>
                            <th>입사일</th>
                            <th>근속일수</th>
                            <th>근무일수</th>
                            <th>결근일수</th>
                            <th>결근율(%)</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        teamEmployees.forEach(emp => {{
            const absenceRate = emp.working_days > 0 ?
                ((emp.absent_days / emp.working_days) * 100).toFixed(1) : '0.0';

            tableHTML += `
                <tr>
                    <td style="position: sticky; left: 0; background: white;">${{emp.full_name || 'N/A'}}</td>
                    <td>${{emp.employee_no || 'N/A'}}</td>
                    <td>${{emp.role_type || 'N/A'}}</td>
                    <td>${{emp.position_1st || 'N/A'}}</td>
                    <td>${{emp.position_2nd || 'N/A'}}</td>
                    <td>${{emp.entrance_date || 'N/A'}}</td>
                    <td>${{emp.years_of_service || 'N/A'}}</td>
                    <td>${{emp.working_days || 0}}</td>
                    <td>${{emp.absent_days || 0}}</td>
                    <td>${{absenceRate}}%</td>
                </tr>
            `;
        }});

        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;

        detailDiv.innerHTML = tableHTML;
        detailDiv.style.display = 'block';

        // Scroll to detail table
        detailDiv.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }};

    // Create hierarchical layout
    const root = d3.hierarchy(hierarchyData)
        .sum(d => d.children ? 0 : (d.value || 1))  // Only count leaf nodes
        .sort((a, b) => b.value - a.value);

    // Configure treemap layout with padding for nested structure
    d3.treemap()
        .size([width, height])
        .paddingOuter(3)
        .paddingTop(20)  // Space for team labels
        .paddingInner(2)
        .tile(d3.treemapSquarify.ratio(1.5))
        .round(true)
        (root);

    // Color functions
    const getTeamColor = (change) => {{
        if (change > 0) return '#4a9c5f';  // Darker green for team increase
        if (change < 0) return '#d94545';  // Darker red for team decrease
        return '#6b7280';  // Gray for no change
    }};

    const getEmployeeColor = (teamChange) => {{
        if (teamChange > 0) return '#a3d9a5';  // Light green for employee in growing team
        if (teamChange < 0) return '#f4a5a5';  // Light red for employee in shrinking team
        return '#c0c5ce';  // Light gray for stable team
    }};

    // First, draw team boxes (depth 1)
    const teamNodes = svg.selectAll('g.team')
        .data(root.descendants().filter(d => d.depth === 1))
        .join('g')
        .attr('class', 'team')
        .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

    // Add team rectangles with borders and hover effects
    teamNodes.append('rect')
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0)
        .attr('fill', d => getTeamColor(d.data.change))
        .attr('fill-opacity', 0.2)
        .attr('stroke', d => getTeamColor(d.data.change))
        .attr('stroke-width', 3)
        .attr('rx', 4)
        .style('cursor', 'pointer')
        .on('click', function(event, d) {{
            const originalName = teams.find(t => t.displayName === d.data.name)?.name;
            if (originalName) {{
                showTeamDetailModal(originalName, 'total_employees');
            }}
        }})
        .on('mouseover', function(event, d) {{
            // Enhance border on hover
            d3.select(this)
                .attr('stroke-width', 4)
                .attr('fill-opacity', 0.3);

            // Calculate statistics for tooltip
            const changeText = d.data.change >= 0 ? `+${{d.data.change}}` : `${{d.data.change}}`;
            const changeColor = d.data.change > 0 ? '#4ade80' : d.data.change < 0 ? '#f87171' : '#d1d5db';

            // Count positions within the team
            const positionCount = d.data.children ? d.data.children.length : 0;

            // Create formatted tooltip content
            const tooltip = d3.select('body').append('div')
                .attr('class', 'team-tooltip')
                .style('position', 'absolute')
                .style('visibility', 'visible')
                .style('background', 'rgba(0, 0, 0, 0.9)')
                .style('color', 'white')
                .style('padding', '12px')
                .style('border-radius', '6px')
                .style('font-size', '12px')
                .style('box-shadow', '0 4px 6px rgba(0, 0, 0, 0.2)')
                .style('max-width', '350px')
                .style('z-index', '10000')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px')
                .html(`
                    <div style="font-size: 14px; font-weight: bold; margin-bottom: 8px; border-bottom: 1px solid #555; padding-bottom: 6px;">
                        ${{d.data.name}}
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>현재 인원:</span>
                        <span style="font-weight: bold;">${{d.data.value}}명</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>전월 인원:</span>
                        <span>${{d.data.prev}}명</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>변화:</span>
                        <span style="color: ${{changeColor}}; font-weight: bold;">
                            ${{changeText}} (${{d.data.changePercent}}%)
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span>포지션 그룹:</span>
                        <span>${{positionCount}}개</span>
                    </div>
                    <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #555; font-size: 11px; color: #aaa;">
                        클릭하여 팀 상세 정보 보기
                    </div>
                `);
        }})
        .on('mouseout', function(event, d) {{
            // Reset border on mouseout
            d3.select(this)
                .attr('stroke-width', 3)
                .attr('fill-opacity', 0.2);

            // Remove tooltip
            d3.selectAll('.team-tooltip').remove();
        }});

    // Helper function to calculate team label configuration
    function getTeamLabelConfig(width, height) {{
        // Minimum dimensions for showing team label
        if (width < 50 || height < 40) {{
            return {{ show: false }};
        }}

        let fontSize, showBadge = true;
        let labelContent = 'full';  // full, medium, minimal

        // Small boxes (50-120px width)
        if (width < 120) {{
            fontSize = 10;
            labelContent = 'minimal';
            showBadge = width > 70;
        }}
        // Medium boxes (120-200px width)
        else if (width < 200) {{
            fontSize = 11;
            labelContent = 'medium';
        }}
        // Large boxes (200px+ width)
        else {{
            fontSize = 12;
            labelContent = 'full';
        }}

        return {{
            show: true,
            fontSize: fontSize,
            showBadge: showBadge,
            labelContent: labelContent,
            badgeWidth: Math.min(width - 6, 250),
            badgeHeight: Math.min(18, height * 0.15)
        }};
    }}

    // Add team labels at the top of each team box with improved rendering
    teamNodes.each(function(d) {{
        const node = d3.select(this);
        const width = d.x1 - d.x0;
        const height = d.y1 - d.y0;
        const labelConfig = getTeamLabelConfig(width, height);

        if (!labelConfig.show) return;

        // Add background badge for team label if space permits
        if (labelConfig.showBadge) {{
            node.append('rect')
                .attr('width', labelConfig.badgeWidth)
                .attr('height', labelConfig.badgeHeight)
                .attr('x', 2)
                .attr('y', 2)
                .attr('rx', 2)
                .attr('fill', getTeamColor(d.data.change))
                .attr('fill-opacity', 0.9);
        }}

        // Add team label text
        const teamText = node.append('text')
            .attr('x', labelConfig.showBadge ? 6 : 4)
            .attr('y', labelConfig.showBadge ? 14 : 12)
            .attr('font-size', `${{labelConfig.fontSize}}px`)
            .attr('font-weight', 'bold')
            .attr('fill', labelConfig.showBadge ? '#fff' : '#333')
            .style('pointer-events', 'none')
            .style('user-select', 'none');

        // Format text based on available space
        const changeText = d.data.change >= 0 ? `+${{d.data.change}}` : d.data.change;
        let displayText = '';

        switch(labelConfig.labelContent) {{
            case 'minimal':
                // Just team name and count
                displayText = width < 80 ?
                    `${{d.data.name}}` :
                    `${{d.data.name}} (${{d.data.value}})`;
                break;
            case 'medium':
                // Team name, count, and change
                displayText = `${{d.data.name}} - ${{d.data.value}}명 (${{changeText}})`;
                break;
            case 'full':
                // Everything including percentage
                displayText = `${{d.data.name}} - ${{d.data.value}}명 (${{changeText}}, ${{d.data.changePercent}}%)`;
                break;
        }}

        // Truncate if still too long
        if (displayText.length * labelConfig.fontSize * 0.5 > width - 10) {{
            const maxChars = Math.floor((width - 10) / (labelConfig.fontSize * 0.5));
            displayText = displayText.substring(0, maxChars - 2) + '..';
        }}

        teamText.text(displayText);
    }});

    // Now draw position group boxes (depth 2 - leaf nodes)
    const positionNodes = svg.selectAll('g.position-group')
        .data(root.leaves())
        .join('g')
        .attr('class', 'position-group')
        .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

    // Get team change for coloring position group boxes
    const getTeamChangeForPosition = (positionNode) => {{
        // Find the parent team node
        let parent = positionNode.parent;
        while (parent && parent.depth > 1) {{
            parent = parent.parent;
        }}
        return parent ? parent.data.change : 0;
    }};

    // Add position group rectangles with click event
    positionNodes.append('rect')
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0)
        .attr('fill', d => getEmployeeColor(getTeamChangeForPosition(d)))
        .attr('fill-opacity', 0.6)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .attr('rx', 2)
        .style('cursor', 'pointer')
        .on('click', function(event, d) {{
            // Find parent team name
            let parentTeam = d.parent;
            while (parentTeam && parentTeam.depth > 1) {{
                parentTeam = parentTeam.parent;
            }}
            if (parentTeam && parentTeam.data.name) {{
                // Get original team name from mapping
                const originalTeamName = teams.find(t => t.displayName === parentTeam.data.name)?.name;
                if (originalTeamName) {{
                    showPositionDetail(d.data, originalTeamName);
                }}
            }}
        }})
        .on('mouseover', function(event, d) {{
            d3.select(this)
                .attr('fill-opacity', 0.9)
                .attr('stroke-width', 2)
                .attr('stroke', '#333');

            // Show tooltip with employee list
            const employeeList = d.data.employees && d.data.employees.length > 0 ?
                d.data.employees.slice(0, 5).join('<br/>') +
                (d.data.employees.length > 5 ? `<br/>... 외 ${{d.data.employees.length - 5}}명` : '') :
                '직원 정보 없음';

            const tooltip = d3.select('body').append('div')
                .attr('class', 'treemap-tooltip')
                .style('position', 'absolute')
                .style('visibility', 'visible')
                .style('background', 'rgba(0, 0, 0, 0.85)')
                .style('color', 'white')
                .style('padding', '10px')
                .style('border-radius', '4px')
                .style('font-size', '11px')
                .style('max-width', '300px')
                .style('z-index', '9999')
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px')
                .html(`
                    <strong style="font-size: 13px;">${{d.data.name}}</strong><br/>
                    <div style="margin: 5px 0; border-bottom: 1px solid #666; padding-bottom: 5px;">
                        인원: <strong>${{d.data.value}}명</strong>
                    </div>
                    <div style="font-size: 10px; line-height: 1.4;">
                        ${{employeeList}}
                    </div>
                    <div style="margin-top: 8px; font-size: 10px; color: #aaa;">
                        클릭하여 상세 정보 보기
                    </div>
                `);
        }})
        .on('mouseout', function(event, d) {{
            d3.select(this)
                .attr('fill-opacity', 0.6)
                .attr('stroke-width', 1.5)
                .attr('stroke', '#fff');

            // Remove tooltip
            d3.selectAll('.treemap-tooltip').remove();
        }});

    // Helper function to calculate optimal text properties
    function getTextConfig(width, height) {{
        // Minimum dimensions for showing any text
        const minWidth = 45;
        const minHeight = 30;

        if (width < minWidth || height < minHeight) {{
            return {{ show: false }};
        }}

        // Calculate font sizes based on box dimensions
        let titleFontSize, countFontSize;
        let maxTextLength;
        let showCount = false;

        // Small boxes (45-80px width)
        if (width < 80) {{
            titleFontSize = Math.min(9, height * 0.25);
            maxTextLength = Math.floor(width / 6);
            showCount = height > 40;
            countFontSize = 8;
        }}
        // Medium boxes (80-120px width)
        else if (width < 120) {{
            titleFontSize = Math.min(11, height * 0.28);
            maxTextLength = Math.floor(width / 5.5);
            showCount = height > 35;
            countFontSize = Math.min(10, height * 0.22);
        }}
        // Large boxes (120px+ width)
        else {{
            titleFontSize = Math.min(13, height * 0.3);
            maxTextLength = Math.floor(width / 5);
            showCount = true;
            countFontSize = Math.min(12, height * 0.25);
        }}

        return {{
            show: true,
            titleFontSize: Math.round(titleFontSize),
            countFontSize: Math.round(countFontSize),
            maxTextLength: maxTextLength,
            showCount: showCount && height > 45,
            titleY: Math.min(16, height * 0.35),
            countY: Math.min(30, height * 0.65)
        }};
    }}

    // Helper function to truncate text intelligently
    function truncateText(text, maxLength) {{
        if (!text || text.length <= maxLength) return text;

        // For very short allowed lengths
        if (maxLength < 4) {{
            return text.substring(0, maxLength);
        }}

        // For short allowed lengths
        if (maxLength < 8) {{
            return text.substring(0, maxLength - 2) + '..';
        }}

        // For longer allowed lengths, use ellipsis
        return text.substring(0, maxLength - 3) + '...';
    }}

    // Add position group labels with improved text rendering
    positionNodes.each(function(d) {{
        const node = d3.select(this);
        const width = d.x1 - d.x0;
        const height = d.y1 - d.y0;
        const textConfig = getTextConfig(width, height);

        if (!textConfig.show) return;

        const name = d.data.name;
        const value = d.data.value;

        // Add position name text
        const titleText = node.append('text')
            .attr('x', 5)
            .attr('y', textConfig.titleY)
            .attr('font-size', `${{textConfig.titleFontSize}}px`)
            .attr('font-weight', '600')
            .attr('fill', '#333')
            .attr('pointer-events', 'none')
            .style('user-select', 'none');

        // Truncate text based on available width
        const displayName = truncateText(name, textConfig.maxTextLength);
        titleText.text(displayName);

        // Add count text if there's enough space
        if (textConfig.showCount) {{
            const countText = node.append('text')
                .attr('x', 5)
                .attr('y', textConfig.countY)
                .attr('font-size', `${{textConfig.countFontSize}}px`)
                .attr('font-weight', 'bold')
                .attr('fill', '#555')
                .attr('pointer-events', 'none')
                .style('user-select', 'none')
                .text(`${{value}}명`);
        }}

        // If text is truncated, show full name in tooltip
        if (displayName !== name) {{
            node.select('rect').attr('title', name);
        }}
    }});

    // Create comparison table
    const tableTitle = document.createElement('h5');
    tableTitle.className = 'lang-text';
    tableTitle.setAttribute('data-ko', '팀별 인원 변화 상세');
    tableTitle.setAttribute('data-en', 'Team Headcount Changes');
    tableTitle.setAttribute('data-vi', 'Thay đổi số lượng nhân viên theo nhóm');
    tableTitle.style.cssText = 'margin: 20px 0 10px 0; font-size: 16px; font-weight: 600; color: #333;';
    tableTitle.textContent = '팀별 인원 변화 상세';
    container.appendChild(tableTitle);

    const table = document.createElement('table');
    table.style.cssText = 'width: 100%; border-collapse: collapse; background: white; border-radius: 5px; overflow: hidden;';

    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr style="background: #f1f3f5;">
            <th class="lang-text" data-ko="팀명" data-en="Team" data-vi="Nhóm" style="padding: 10px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6;">팀명</th>
            <th class="lang-text" data-ko="${{currentMonthLabel}} 인원 ${{currentRefLabel}}" data-en="${{currentMonthLabel}} Headcount ${{currentRefLabel}}" data-vi="Số lượng tháng ${{currentMonthLabel}} ${{currentRefLabel}}" style="padding: 10px; text-align: center; font-weight: 600; border-bottom: 2px solid #dee2e6;">${{currentMonthLabel}} 인원 ${{currentRefLabel}}</th>
            <th class="lang-text" data-ko="${{prevMonthLabel || '전월'}} 인원 ${{prevRefLabel}}" data-en="${{prevMonthLabel || 'Previous Month'}} Headcount ${{prevRefLabel}}" data-vi="Số lượng tháng ${{prevMonthLabel || 'trước'}} ${{prevRefLabel}}" style="padding: 10px; text-align: center; font-weight: 600; border-bottom: 2px solid #dee2e6;">${{prevMonthLabel || '전월'}} 인원 ${{prevRefLabel}}</th>
            <th class="lang-text" data-ko="증감 인원" data-en="Change" data-vi="Thay đổi" style="padding: 10px; text-align: center; font-weight: 600; border-bottom: 2px solid #dee2e6;">증감 인원</th>
            <th class="lang-text" data-ko="증감율" data-en="Change %" data-vi="Tỷ lệ %" style="padding: 10px; text-align: center; font-weight: 600; border-bottom: 2px solid #dee2e6;">증감율</th>
        </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    teams.forEach(team => {{
        const row = document.createElement('tr');
        row.style.cssText = 'cursor: pointer; transition: background 0.2s;';
        row.addEventListener('mouseenter', function() {{ this.style.background = '#f8f9fa'; }});
        row.addEventListener('mouseleave', function() {{ this.style.background = 'transparent'; }});
        row.addEventListener('click', function() {{ showTeamDetailModal(team.name, 'total_employees'); }});

        const changeColor = team.change > 0 ? '#28a745' : team.change < 0 ? '#dc3545' : '#6c757d';
        const changeSign = team.change > 0 ? '+' : '';

        row.innerHTML = `
            <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">
                <a href="javascript:void(0)" style="color: #0066cc; text-decoration: none; font-weight: 500;">${{team.name}}</a>
            </td>
            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6; font-weight: 600;">${{team.total}}명</td>
            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6;">${{team.prev}}명</td>
            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6; color: ${{changeColor}}; font-weight: 600;">
                ${{changeSign}}${{team.change}}명
            </td>
            <td style="padding: 10px; text-align: center; border-bottom: 1px solid #dee2e6; color: ${{changeColor}}; font-weight: 600;">
                ${{changeSign}}${{team.changePercent}}%
            </td>
        `;
        tbody.appendChild(row);
    }});

    // Add Total row
    const totalRow = document.createElement('tr');
    totalRow.style.cssText = 'background: #e3f2fd; font-weight: 700; border-top: 2px solid #1976d2;';

    const totalCurrent = teams.reduce((sum, team) => sum + team.total, 0);
    const totalPrev = teams.reduce((sum, team) => sum + team.prev, 0);
    const totalChange = totalCurrent - totalPrev;
    const totalChangePercent = totalPrev !== 0 ? ((totalChange / totalPrev) * 100).toFixed(1) : '0.0';
    const totalChangeColor = totalChange > 0 ? '#28a745' : totalChange < 0 ? '#dc3545' : '#6c757d';
    const totalChangeSign = totalChange > 0 ? '+' : '';

    totalRow.innerHTML = `
        <td style="padding: 12px; border-bottom: 2px solid #1976d2; font-size: 15px; color: #1565c0;">
            Total
        </td>
        <td style="padding: 12px; text-align: center; border-bottom: 2px solid #1976d2; font-size: 15px;">
            ${{totalCurrent}}명
        </td>
        <td style="padding: 12px; text-align: center; border-bottom: 2px solid #1976d2; font-size: 15px;">
            ${{totalPrev}}명
        </td>
        <td style="padding: 12px; text-align: center; border-bottom: 2px solid #1976d2; color: ${{totalChangeColor}}; font-size: 15px;">
            ${{totalChangeSign}}${{totalChange}}명
        </td>
        <td style="padding: 12px; text-align: center; border-bottom: 2px solid #1976d2; color: ${{totalChangeColor}}; font-size: 15px;">
            ${{totalChangeSign}}${{totalChangePercent}}%
        </td>
    `;
    tbody.appendChild(totalRow);

    table.appendChild(tbody);

    container.appendChild(table);
}}

/**
 * Show team detail modal with KPI-specific analysis
 * @param {string} teamName - The name of the team
 * @param {string} kpiKey - The KPI key to analyze (e.g., 'absence_rate', 'total_employees')
 */
function showTeamDetailModal(teamName, kpiKey) {{
    debugLog(`📊 Opening team detail modal for: ${{teamName}}, KPI: ${{kpiKey}}`);

    // Validate inputs
    if (!teamData[teamName]) {{
        debugLog('Team data not found for:', teamName);
        alert('팀 데이터를 찾을 수 없습니다: ' + teamName);
        return;
    }}

    if (!kpiConfig[kpiKey]) {{
        debugLog('KPI config not found for:', kpiKey);
        alert('KPI 설정을 찾을 수 없습니다: ' + kpiKey);
        return;
    }}

    // Destroy existing charts
    Object.keys(teamDetailCharts).forEach(key => {{
        if (teamDetailCharts[key] && typeof teamDetailCharts[key].destroy === 'function') {{
            teamDetailCharts[key].destroy();
        }}
    }});

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('teamDetailModal'));
    modal.show();

    // Create charts after modal is shown (delay for rendering)
    setTimeout(() => {{
        createTeamDetailCharts(teamName, kpiKey);
    }}, 300);
}}

// OLD VERSION - Kept for reference
function showTeamDetailModal_OLD(teamName) {
    debugLog('Opening team detail modal for:', teamName);

    // Get team data
    const team = teamData[teamName];
    if (!team || !team.members) {
        debugLog('Team data not found for:', teamName);
        alert('팀 데이터를 찾을 수 없습니다: ' + teamName);
        return;
    }

    const cleanName = teamName.replace(/[^a-zA-Z0-9]/g, '_');

    // Clean up existing charts
    if (teamDetailCharts[cleanName]) {
        teamDetailCharts[cleanName].forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        teamDetailCharts[cleanName] = [];
    }

    // Remove existing modal if present
    let existingModal = document.getElementById('teamDetailModal_OLD');
    if (existingModal) {
        existingModal.remove();
    }

    // Create modal HTML with card-style layout
    // XSS 방지: teamName sanitize / Prevent XSS: sanitize teamName
    const safeTeamName = sanitizeHTML(teamName);
    const modalHtml = `
        <div class="modal fade show" id="teamDetailModal_OLD" tabindex="-1" style="display: block; background: rgba(0,0,0,0.5);">
            <div class="modal-dialog modal-xl" style="max-width: 90%;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${safeTeamName} 팀 상세 정보</h5>
                        <button type="button" class="btn-close btn-close-white" onclick="closeTeamDetailModal()"></button>
                    </div>
                    <div class="modal-body" style="max-height: 80vh; overflow-y: auto; background: #f5f5f5;">
                        <!-- 1. 월별 팀 인원 트렌드 -->
                        <div class="card mb-3">
                            <div class="card-body">
                                <div class="modal-chart-container">
                                    <canvas id="teamChart_monthly_${cleanName}"></canvas>
                                </div>
                            </div>
                        </div>

                        <!-- 2. 주차별 팀 인원 트렌드 -->
                        <div class="card mb-3">
                            <div class="card-body">
                                <div class="modal-chart-container">
                                    <canvas id="teamChart_weekly_${cleanName}"></canvas>
                                </div>
                            </div>
                        </div>

                        <!-- 3. Multi-Level Donut - 팀내 역할별 인원 분포 -->
                        <div class="card mb-3">
                            <div class="card-body">
                                <div class="modal-chart-container">
                                    <canvas id="teamChart_roleDonut_${cleanName}"></canvas>
                                </div>
                            </div>
                        </div>

                        <!-- 4. 팀내 역할별 만근율 현황 -->
                        <div class="card mb-3">
                            <div class="card-body">
                                <div class="modal-chart-container">
                                    <canvas id="teamChart_roleAttendance_${cleanName}"></canvas>
                                </div>
                            </div>
                        </div>

                        <!-- 5. 5단계 계층 구조 Sunburst 차트 -->
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">5단계 계층 구조 Sunburst 차트 - 팀내 역할별 인원 분포</h5>
                                <div id="teamChart_sunburst_${cleanName}" style="height: 500px;"></div>
                            </div>
                        </div>

                        <!-- 6. 팀원 상세 정보 -->
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">팀원 상세 정보 (총 ${team.members.length}명)</h5>
                                <div style="max-height: 500px; overflow-y: auto;">
                                    <table class="table table-sm table-striped table-hover sortable-table" style="font-size: 12px;">
                                        <thead style="position: sticky; top: 0; background: #f8f9fa; z-index: 10;">
                                            <tr>
                                                <th onclick="sortTeamTable(0, '${cleanName}')" style="cursor: pointer;">사번 <span class="sort-icon">⇅</span></th>
                                                <th onclick="sortTeamTable(1, '${cleanName}')" style="cursor: pointer;">이름 <span class="sort-icon">⇅</span></th>
                                                <th onclick="sortTeamTable(2, '${cleanName}')" style="cursor: pointer;">Position 1st <span class="sort-icon">⇅</span></th>
                                                <th onclick="sortTeamTable(3, '${cleanName}')" style="cursor: pointer;">Position 2nd <span class="sort-icon">⇅</span></th>
                                                <th onclick="sortTeamTable(4, '${cleanName}')" style="cursor: pointer;">Position 3rd <span class="sort-icon">⇅</span></th>
                                                <th onclick="sortTeamTable(5, '${cleanName}')" style="cursor: pointer;">입사일 <span class="sort-icon">⇅</span></th>
                                                <th onclick="sortTeamTable(6, '${cleanName}')" style="cursor: pointer;">근속(일) <span class="sort-icon">⇅</span></th>
                                                <th onclick="sortTeamTable(7, '${cleanName}')" style="cursor: pointer;">근무일 <span class="sort-icon">⇅</span></th>
                                                <th onclick="sortTeamTable(8, '${cleanName}')" style="cursor: pointer;">결근 <span class="sort-icon">⇅</span></th>
                                                <th onclick="sortTeamTable(9, '${cleanName}')" style="cursor: pointer;">결근율(%) <span class="sort-icon">⇅</span></th>
                                            </tr>
                                        </thead>
                                        <tbody id="teamMemberTableBody_${cleanName}">
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Initialize charts
    setTimeout(() => {
        createTeamDetailCharts(teamName, cleanName, team);
        populateTeamMemberTable(cleanName, team.members);
    }, 100);
}

function closeTeamDetailModal() {
    const modal = document.getElementById('teamDetailModal');
    if (modal) {
        modal.remove();
    }
}

function sortTeamTable(columnIndex, cleanName) {
    const tbody = document.getElementById(`teamMemberTableBody_${cleanName}`);
    if (!tbody) return;

    const data = window[`teamTableData_${cleanName}`] || [];
    if (data.length === 0) return;

    // Toggle sort direction
    if (!window[`sortDir_${cleanName}`]) {
        window[`sortDir_${cleanName}`] = {};
    }
    const currentDir = window[`sortDir_${cleanName}`][columnIndex] || 'asc';
    const newDir = currentDir === 'asc' ? 'desc' : 'asc';
    window[`sortDir_${cleanName}`][columnIndex] = newDir;

    // Column field mapping
    const fields = ['employee_no', 'full_name', 'position_1st', 'position_2nd', 'position_3rd',
                    'entrance_date', 'years_of_service', 'working_days', 'absent_days'];

    const field = fields[columnIndex];

    // Sort data
    data.sort((a, b) => {
        let valA = a[field];
        let valB = b[field];

        // Handle numeric fields
        if (columnIndex >= 6) {  // years_of_service, working_days, absent_days
            valA = parseFloat(valA) || 0;
            valB = parseFloat(valB) || 0;
        }

        if (valA < valB) return newDir === 'asc' ? -1 : 1;
        if (valA > valB) return newDir === 'asc' ? 1 : -1;
        return 0;
    });

    // Rebuild table
    let html = '';
    data.forEach(member => {
        const absenceRate = member.working_days > 0 ?
            ((member.absent_days / member.working_days) * 100).toFixed(1) : '0.0';

        html += `
            <tr>
                <td>${member.employee_no}</td>
                <td>${member.full_name}</td>
                <td>${member.position_1st}</td>
                <td>${member.position_2nd}</td>
                <td>${member.position_3rd}</td>
                <td>${member.entrance_date}</td>
                <td>${member.years_of_service}</td>
                <td>${member.working_days}</td>
                <td>${member.absent_days}</td>
                <td>${absenceRate}%</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    // Update sort icons
    const table = tbody.closest('table');
    const headers = table.querySelectorAll('th');
    headers.forEach((th, idx) => {
        const icon = th.querySelector('.sort-icon');
        if (icon) {
            if (idx === columnIndex) {
                icon.textContent = newDir === 'asc' ? '↑' : '↓';
            } else {
                icon.textContent = '⇅';
            }
        }
    });
}

// Modal 2: Absence Rate
// Modal 2: Absence Rate (Unified)
function showModal2() {{
    // Destroy existing charts
    ['weekly', 'daily', 'teams', 'types', 'change', 'reasonDistribution', 'reasonTrends', 'teamReasons'].forEach(type => {{
        const chartKey = `modal2_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});

    // Populate summary metrics (excl. maternity only)
    if (modalData.absence_metrics) {{
        const metrics = modalData.absence_metrics;
        document.getElementById('maternityExcludedRate').textContent = metrics.excluding_maternity_rate + '%';
        document.getElementById('maternityExcludedCount').textContent =
            `${{metrics.non_pregnant_absences}} absences (excluding maternity)`;
    }}

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('modal2'));
    modal.show();

    // Create charts after modal is shown (all using excl. maternity data)
    setTimeout(() => {{
        createUnifiedModalCharts(2, 'absence_rate_excl_maternity');
        // Add daily absence chart
        createDailyAbsenceChart(2);
        // Add absence reason analysis charts
        createAbsenceReasonDistributionChart();
        createAbsenceReasonTrendsChart();
        createTeamAbsenceReasonsChart();
    }}, 300);
}}

// Modal 3: Unauthorized Absence (Unified)
function showModal3() {{
    // Clear existing charts
    ['trend', 'diverging', 'donut'].forEach(type => {{
        const chartKey = `modal3_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});

    // Get team-level unauthorized rates from metrics
    const currentMonth = Object.keys(monthlyMetrics).sort().pop();
    const previousMonth = Object.keys(monthlyMetrics).sort()[Object.keys(monthlyMetrics).length - 2];
    const teamRates = monthlyMetrics[currentMonth]?.team_unauthorized_rates || {{}};
    const prevTeamRates = previousMonth ? (monthlyMetrics[previousMonth]?.team_unauthorized_rates || {{}}) : {{}};

    // Calculate statistics
    const ratesArray = Object.values(teamRates).filter(r => r > 0);
    const avgRate = ratesArray.length > 0 ? (ratesArray.reduce((a, b) => a + b, 0) / ratesArray.length).toFixed(2) : 0;
    const overallRate = monthlyMetrics[currentMonth]?.unauthorized_absence_rate || 0;

    // Find highest and lowest teams
    let highestTeam = '-', highestRate = 0;
    let lowestTeam = '-', lowestRate = 100;

    for (const [team, rate] of Object.entries(teamRates)) {{
        if (rate > highestRate) {{
            highestRate = rate;
            highestTeam = team;
        }}
        if (rate < lowestRate && rate > 0) {{
            lowestRate = rate;
            lowestTeam = team;
        }}
    }}

    // Populate summary metrics
    document.getElementById('overallUnauthorizedRate').textContent = overallRate + '%';
    document.getElementById('vsAverage').textContent = (overallRate > avgRate ? '+' : '') + (overallRate - avgRate).toFixed(2) + '%';
    document.getElementById('teamAverage').textContent = avgRate + '%';
    document.getElementById('highestTeam').textContent = highestTeam;
    document.getElementById('highestRate').textContent = highestRate + '%';
    document.getElementById('lowestTeam').textContent = lowestTeam;
    document.getElementById('lowestRate').textContent = lowestRate + '%';

    // Count anomalies (teams with rates > 2 standard deviations from mean)
    const stdDev = Math.sqrt(ratesArray.reduce((sum, r) => sum + Math.pow(r - avgRate, 2), 0) / ratesArray.length);
    const anomalyThreshold = parseFloat(avgRate) + (2 * stdDev);
    const anomalies = Object.values(teamRates).filter(r => r > anomalyThreshold).length;
    document.getElementById('anomalyCount').textContent = anomalies + '개 팀';

    // Create visualizations
    setTimeout(() => {{
        createUnauthorizedTrendChart();
        createDivergingBarChart(teamRates, avgRate);
        createAbsenceTypeDonut();
        populateTeamDetailTable(teamRates, prevTeamRates);
    }}, 300);

    const modal = new bootstrap.Modal(document.getElementById('modal3'));
    modal.show();
}}

// Create trend chart with anomaly detection
function createUnauthorizedTrendChart() {{
    const ctx = document.getElementById('modalChart3_trend').getContext('2d');

    // Get monthly trend data
    const months = Object.keys(monthlyMetrics).sort();
    const trendData = months.map(month => monthlyMetrics[month]?.unauthorized_absence_rate || 0);

    modalCharts['modal3_trend'] = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: months.map(m => {{
                const [year, month] = m.split('-');
                return `${{month}}월`;
            }}),
            datasets: [{{
                label: '무단결근율 (%)',
                data: trendData,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.3,
                fill: true
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: (context) => `무단결근율: ${{context.parsed.y}}%`
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    ticks: {{ callback: (value) => value + '%' }}
                }}
            }}
        }}
    }});
}}

// Create diverging bar chart for team comparison
function createDivergingBarChart(teamRates, avgRate) {{
    const ctx = document.getElementById('modalChart3_diverging').getContext('2d');

    const teams = Object.keys(teamRates);
    const deviations = teams.map(team => (teamRates[team] - avgRate).toFixed(2));
    const colors = deviations.map(d => d > 0 ? 'rgba(255, 99, 132, 0.8)' : 'rgba(75, 192, 192, 0.8)');

    modalCharts['modal3_diverging'] = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: teams,
            datasets: [{{
                label: '평균 대비 편차 (%)',
                data: deviations,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 1
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: (context) => {{
                            const team = context.label;
                            const rate = teamRates[team];
                            const deviation = context.parsed.x;
                            return [`실제: ${{rate}}%`, `평균 대비: ${{deviation > 0 ? '+' : ''}}${{deviation}}%`];
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    grid: {{
                        color: (context) => context.tick.value === 0 ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.05)'
                    }},
                    ticks: {{
                        callback: (value) => value + '%'
                    }}
                }}
            }}
        }}
    }});
}}

// Create absence type distribution donut chart
function createAbsenceTypeDonut() {{
    const ctx = document.getElementById('modalChart3_donut').getContext('2d');

    // Mock data for absence types (would be calculated from actual data)
    const type1Count = Math.floor(Math.random() * 50) + 10;
    const type2Count = Math.floor(Math.random() * 100) + 50;
    const type3Count = Math.floor(Math.random() * 200) + 100;
    const total = type1Count + type2Count + type3Count;

    // Update table
    document.getElementById('type1Count').textContent = type1Count;
    document.getElementById('type1Rate').textContent = ((type1Count/total)*100).toFixed(1) + '%';
    document.getElementById('type2Count').textContent = type2Count;
    document.getElementById('type2Rate').textContent = ((type2Count/total)*100).toFixed(1) + '%';
    document.getElementById('type3Count').textContent = type3Count;
    document.getElementById('type3Rate').textContent = ((type3Count/total)*100).toFixed(1) + '%';

    modalCharts['modal3_donut'] = new Chart(ctx, {{
        type: 'doughnut',
        data: {{
            labels: ['무단결근', '병가', '승인결근'],
            datasets: [{{
                data: [type1Count, type2Count, type3Count],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)'
                ],
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{
                legend: {{
                    position: 'bottom',
                    labels: {{ boxWidth: 12, padding: 8, font: {{ size: 10 }} }}
                }}
            }}
        }}
    }});
}}

// Populate team detail table
function populateTeamDetailTable(teamRates, prevTeamRates) {{
    const tbody = document.getElementById('teamDetailTable');
    tbody.innerHTML = '';

    const teams = Object.keys(teamRates).sort((a, b) => teamRates[b] - teamRates[a]);

    teams.forEach(team => {{
        const rate = teamRates[team];
        const prevRate = prevTeamRates[team] || 0;
        const change = rate - prevRate;
        const changeText = change > 0 ? `+${{change.toFixed(2)}}%` : `${{change.toFixed(2)}}%`;
        const changeClass = change > 0 ? 'text-danger' : change < 0 ? 'text-success' : 'text-muted';

        const status = rate > 1.0 ? '<span class="badge bg-danger">주의</span>' :
                      rate > 0.5 ? '<span class="badge bg-warning">관찰</span>' :
                      '<span class="badge bg-success">양호</span>';

        const row = `
            <tr>
                <td>${{team}}</td>
                <td><strong>${{rate}}%</strong></td>
                <td>${{Math.floor(Math.random() * 50) + 20}}</td>
                <td>${{Math.floor(rate * 5)}}</td>
                <td class="${{changeClass}}">${{changeText}}</td>
                <td>${{status}}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    }});
}}

// Modal 4: Resignation Rate (Unified)
function showModal4() {{
    ['weekly', 'teams', 'types', 'change'].forEach(type => {{
        const chartKey = `modal4_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});
    const modal = new bootstrap.Modal(document.getElementById('modal4'));
    modal.show();
    setTimeout(() => {{ createUnifiedModalCharts(4, 'resignation_rate'); }}, 300);
}}

// Modal 5: Recent Hires (Custom Comprehensive Analysis)
function showModal5() {{
    // Clear existing charts
    ['recentHiresMonthlyTrend', 'recentHiresWeeklyTrend', 'recentHiresDailyTrend',
     'recentHiresAbsence', 'recentHiresReasons', 'recentHiresRetention', 'recentHiresTeam'].forEach(chartKey => {{
        if (modalCharts[chartKey]) {{
            modalCharts[chartKey].destroy();
            delete modalCharts[chartKey];
        }}
    }});

    const modal = new bootstrap.Modal(document.getElementById('modal5'));
    modal.show();

    // Create comprehensive analysis after modal is shown
    setTimeout(() => {{ createRecentHiresAnalysis(); }}, 300);
}}

/**
 * Recent Hires Comprehensive Analysis
 * 신규 입사자 종합 분석
 */
function createRecentHiresAnalysis() {{
    debugLog('📊 Creating Recent Hires Comprehensive Analysis');

    // Get recent hires data
    const recentHires = employeeDetails.filter(e => e.hired_this_month);
    debugLog(`Total recent hires: ${{recentHires.length}}`);

    if (recentHires.length === 0) {{
        document.getElementById('recentHiresOverview').innerHTML = '<div class="col-12"><p class="text-muted text-center">신규 입사자 데이터가 없습니다.</p></div>';
        return;
    }}

    // 1. Create Overview Cards
    createRecentHiresOverviewCards(recentHires);

    // 2. Create Hiring Trends
    createRecentHiresMonthlyTrendChart();
    createRecentHiresWeeklyTrendChart();
    createRecentHiresDailyTrendChart();

    // 3. Create Performance Charts
    createRecentHiresAbsenceChart(recentHires);
    createRecentHiresReasonsChart(recentHires);

    // 4. Create Retention Analysis
    createRecentHiresRetentionChart(recentHires);
    createRecentHiresTeamChart(recentHires);

    // 5. Populate Detail Table
    populateRecentHiresTable(recentHires);
}}

/**
 * Create Overview Cards
 * 개요 카드 생성
 */
function createRecentHiresOverviewCards(recentHires) {{
    const totalHires = recentHires.length;
    const activeHires = recentHires.filter(e => e.is_active).length;
    const resignedHires = recentHires.filter(e => e.resigned_this_month).length;

    // Calculate average tenure days
    const avgTenure = recentHires.reduce((sum, e) => sum + (e.tenure_days || 0), 0) / totalHires;

    // Calculate absence rates
    const totalWorkingDays = recentHires.reduce((sum, e) => sum + (e.working_days || 0), 0);
    const totalAbsentDays = recentHires.reduce((sum, e) => sum + (e.absent_days || 0), 0);
    const avgAbsenceRate = totalWorkingDays > 0 ? ((totalAbsentDays / totalWorkingDays) * 100).toFixed(1) : 0;

    // Calculate early resignation rate (within 90 days)
    const earlyResignations = recentHires.filter(e => {{
        if (!e.resigned_this_month) return false;
        const tenure = e.tenure_days || 0;
        return tenure < 90;
    }}).length;
    const earlyResignationRate = ((earlyResignations / totalHires) * 100).toFixed(1);

    const cards = [
        {{
            title: '총 신규 입사자',
            titleEn: 'Total New Hires',
            titleVi: 'Tổng nhân viên mới',
            value: totalHires,
            unit: '명',
            detail: `재직: ${{activeHires}}명 | 퇴사: ${{resignedHires}}명`,
            detailEn: `Active: ${{activeHires}} | Resigned: ${{resignedHires}}`,
            detailVi: `Đang làm: ${{activeHires}} | Nghỉ: ${{resignedHires}}`,
            color: '#667eea'
        }},
        {{
            title: '평균 결근율',
            titleEn: 'Avg Absence Rate',
            titleVi: 'Tỷ lệ vắng trung bình',
            value: avgAbsenceRate,
            unit: '%',
            detail: `전체 평균: ${{monthlyMetrics[targetMonth]?.absence_rate?.toFixed(1) || 0}}%`,
            detailEn: `Overall: ${{monthlyMetrics[targetMonth]?.absence_rate?.toFixed(1) || 0}}%`,
            detailVi: `Trung bình: ${{monthlyMetrics[targetMonth]?.absence_rate?.toFixed(1) || 0}}%`,
            color: avgAbsenceRate > (monthlyMetrics[targetMonth]?.absence_rate || 0) ? '#dc3545' : '#28a745'
        }},
        {{
            title: '조기 퇴사율 (90일 이내)',
            titleEn: 'Early Resignation (<90d)',
            titleVi: 'Nghỉ sớm (<90 ngày)',
            value: earlyResignationRate,
            unit: '%',
            detail: `${{earlyResignations}}명 / ${{totalHires}}명`,
            detailEn: `${{earlyResignations}} / ${{totalHires}}`,
            detailVi: `${{earlyResignations}} / ${{totalHires}}`,
            color: earlyResignationRate > 10 ? '#dc3545' : '#28a745'
        }}
    ];

    const overviewHTML = cards.map(card => `
        <div class="col-md-4">
            <div class="card" style="border-left: 4px solid ${{card.color}};">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted lang-text" data-ko="${{card.title}}" data-en="${{card.titleEn}}" data-vi="${{card.titleVi}}">${{card.title}}</h6>
                    <h3 class="card-title mb-1" style="color: ${{card.color}};">${{card.value}}${{card.unit}}</h3>
                    <p class="card-text small text-muted lang-text" data-ko="${{card.detail}}" data-en="${{card.detailEn}}" data-vi="${{card.detailVi}}">${{card.detail}}</p>
                </div>
            </div>
        </div>
    `).join('');

    document.getElementById('recentHiresOverview').innerHTML = overviewHTML;
}}

/**
 * Create Absence Rate Comparison Chart
 * 결근율 비교 차트 생성
 */
function createRecentHiresAbsenceChart(recentHires) {{
    const canvas = document.getElementById('recentHiresAbsenceChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Calculate metrics for recent hires
    const totalWorkingDays = recentHires.reduce((sum, e) => sum + (e.working_days || 0), 0);
    const totalAbsentDays = recentHires.reduce((sum, e) => sum + (e.absent_days || 0), 0);
    const newHiresAbsenceRate = totalWorkingDays > 0 ? ((totalAbsentDays / totalWorkingDays) * 100).toFixed(1) : 0;

    // Calculate unauthorized absence for new hires
    const unauthorizedCount = recentHires.filter(e => e.has_unauthorized_absence).length;
    const newHiresUnauthorizedRate = ((unauthorizedCount / recentHires.length) * 100).toFixed(1);

    // Overall metrics
    const overallAbsenceRate = monthlyMetrics[targetMonth]?.absence_rate?.toFixed(1) || 0;
    const overallUnauthorizedRate = monthlyMetrics[targetMonth]?.unauthorized_absence_rate?.toFixed(1) || 0;

    modalCharts.recentHiresAbsence = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: ['총 결근율', '무단 결근율'],
            datasets: [
                {{
                    label: '신규 입사자',
                    data: [newHiresAbsenceRate, newHiresUnauthorizedRate],
                    backgroundColor: 'rgba(102, 126, 234, 0.7)',
                    borderColor: '#667eea',
                    borderWidth: 1
                }},
                {{
                    label: '전체 직원',
                    data: [overallAbsenceRate, overallUnauthorizedRate],
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: '#dc3545',
                    borderWidth: 1
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: true }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            return context.dataset.label + ': ' + context.parsed.y + '%';
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: '비율 (%)'
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Create Absence Reasons Distribution Chart
 * 결근 사유 분포 차트 생성
 */
function createRecentHiresReasonsChart(recentHires) {{
    const canvas = document.getElementById('recentHiresReasonsChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Get absence reason data for recent hires
    const reasonCounts = {{}};
    const monthlyReasonData = modalData.monthly_absence_reasons || {{}};
    const currentMonthReasons = monthlyReasonData[targetMonth] || {{}};

    // Categorize absence reasons (simplified)
    const categories = {{
        '병가 (Sick Leave)': currentMonthReasons['병가 (Sick Leave)'] || 0,
        '개인 사유 (Personal)': currentMonthReasons['개인 사유 (Personal)'] || 0,
        '무단 결근 (Unauthorized)': currentMonthReasons['무단 결근 (Unauthorized)'] || 0,
        '가족 사유 (Family)': currentMonthReasons['가족 사유 (Family)'] || 0,
        '기타 (Other)': currentMonthReasons['기타 (Other)'] || 0
    }};

    const labels = Object.keys(categories);
    const data = Object.values(categories);

    modalCharts.recentHiresReasons = new Chart(ctx, {{
        type: 'doughnut',
        data: {{
            labels: labels,
            datasets: [{{
                data: data,
                backgroundColor: [
                    '#FF6B6B',
                    '#4ECDC4',
                    '#FFE66D',
                    '#95E1D3',
                    '#C7CEEA'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ position: 'right' }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                            return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                        }}
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Create Retention Analysis Chart - Early Resignation Analysis
 * 조기 퇴사율 분석 차트 생성 - 입사 90일 이내 직원 분석
 *
 * Purpose: Show status of employees hired within last 90 days
 * 목적: 최근 90일 이내 입사한 직원들의 현황 분석
 */
function createRecentHiresRetentionChart(recentHires) {{
    const canvas = document.getElementById('recentHiresRetentionChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Get all employees with tenure <= 90 days (hired within last 90 days)
    // 최근 90일 이내 입사한 모든 직원 (tenure_days <= 90)
    const employeesUnder90Days = employeeDetails.filter(e => e.tenure_days > 0 && e.tenure_days <= 90);

    // Separate into resigned and active groups
    // 퇴사자와 재직자로 분류
    const resignedUnder90 = employeesUnder90Days.filter(e => !e.is_active);
    const activeUnder90 = employeesUnder90Days.filter(e => e.is_active);

    // Count resigned employees by tenure period (when they resigned)
    // 퇴사자를 근속 기간별로 분류 (퇴사 시점 기준)
    const resigned_0_30 = resignedUnder90.filter(e => e.tenure_days <= 30).length;
    const resigned_30_60 = resignedUnder90.filter(e => e.tenure_days > 30 && e.tenure_days <= 60).length;
    const resigned_60_90 = resignedUnder90.filter(e => e.tenure_days > 60 && e.tenure_days <= 90).length;

    // Also include employees who worked more than 90 days before resigning (for comparison)
    // 90일 이상 근무 후 퇴사한 직원도 포함 (비교용)
    const allResigned = employeeDetails.filter(e => !e.is_active && e.resigned_this_month);
    const resigned_90_plus = allResigned.filter(e => e.tenure_days > 90).length;

    // Active employees (still working, hired within 90 days)
    // 재직중인 직원 (90일 이내 입사)
    const activeCount = activeUnder90.length;

    // Total for percentage calculation (all hired within 90 days)
    // 전체 인원 (90일 이내 입사자 기준)
    const total = employeesUnder90Days.length;

    modalCharts.recentHiresRetention = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: ['0-30일', '31-60일', '61-90일', '90일+', '재직중'],
            datasets: [{{
                label: '인원',
                data: [resigned_0_30, resigned_30_60, resigned_60_90, resigned_90_plus, activeCount],
                backgroundColor: [
                    'rgba(220, 53, 69, 0.7)',    // 0-30: Red (critical)
                    'rgba(255, 193, 7, 0.7)',    // 31-60: Yellow (warning)
                    'rgba(255, 152, 0, 0.7)',    // 61-90: Orange (caution)
                    'rgba(156, 39, 176, 0.7)',   // 90+: Purple (longer tenure)
                    'rgba(40, 167, 69, 0.7)'     // Active: Green (retained)
                ],
                borderWidth: 1,
                borderColor: '#fff'
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                title: {{
                    display: true,
                    text: `90일 이내 입사자 분석 (총 ${{total}}명)`,
                    font: {{ size: 14 }}
                }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            const value = context.parsed.y;
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `인원: ${{value}}명 (${{percentage}}%)`;
                        }},
                        afterLabel: function(context) {{
                            const index = context.dataIndex;
                            if (index === 4) {{
                                return '✅ 현재 재직중';
                            }} else if (index === 3) {{
                                return '⚠️ 장기 근무 후 퇴사';
                            }} else {{
                                return '❌ 조기 퇴사';
                            }}
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: '인원 (명)'
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Create Team Distribution Chart - New Hires by Team
 * 팀별 신규 입사자 분포 차트 생성
 *
 * Purpose: Show distribution of employees hired THIS MONTH by team
 * 목적: 이번 달에 입사한 신규 직원들의 팀별 분포 표시
 *
 * This helps identify which teams are receiving most new hires
 * 어느 팀이 가장 많은 신규 인력을 받고 있는지 파악
 */
function createRecentHiresTeamChart(recentHires) {{
    const canvas = document.getElementById('recentHiresTeamChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Count by team (이번 달 입사자의 팀별 집계)
    const teamCounts = {{}};
    recentHires.forEach(e => {{
        const team = e.team || 'QIP_MANAGER_OFFICE_OCPT';  // Fallback to manager/office instead of "Unknown"
        teamCounts[team] = (teamCounts[team] || 0) + 1;
    }});

    // Sort by count descending
    const sortedTeams = Object.entries(teamCounts).sort((a, b) => b[1] - a[1]);
    const labels = sortedTeams.map(t => t[0]);
    const data = sortedTeams.map(t => t[1]);

    modalCharts.recentHiresTeam = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: labels,
            datasets: [{{
                label: '신규 입사자',
                data: data,
                backgroundColor: 'rgba(102, 126, 234, 0.7)',
                borderColor: '#667eea',
                borderWidth: 1
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                title: {{
                    display: true,
                    text: `이번 달 신규 입사자 팀별 분포 (총 ${{recentHires.length}}명)`,
                    font: {{ size: 14 }}
                }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            const percentage = recentHires.length > 0 ?
                                ((context.parsed.x / recentHires.length) * 100).toFixed(1) : 0;
                            return `인원: ${{context.parsed.x}}명 (${{percentage}}%)`;
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: '신규 입사자 수 (명)'
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Populate Recent Hires Detail Table
 * 신규 입사자 상세 테이블 채우기
 */
function populateRecentHiresTable(recentHires) {{
    const tbody = document.getElementById('recentHiresTableBody');
    if (!tbody) return;

    // Sort by entrance date descending
    const sortedHires = recentHires.sort((a, b) => {{
        const dateA = new Date(a.entrance_date);
        const dateB = new Date(b.entrance_date);
        return dateB - dateA;
    }});

    const rows = sortedHires.map(e => {{
        // Calculate absence rates
        const absenceRate = e.working_days > 0 ? ((e.absent_days / e.working_days) * 100).toFixed(1) : 0;
        const unauthorizedRate = e.has_unauthorized_absence ? 'Yes' : 'No';

        // Status badge
        let statusBadge = '';
        if (e.is_active) {{
            statusBadge = '<span class="badge bg-success">재직중</span>';
        }} else if (e.resigned_this_month) {{
            const tenure = e.tenure_days || 0;
            if (tenure < 30) {{
                statusBadge = '<span class="badge bg-danger">퇴사 (30일 이내)</span>';
            }} else if (tenure < 90) {{
                statusBadge = '<span class="badge bg-warning">퇴사 (90일 이내)</span>';
            }} else {{
                statusBadge = '<span class="badge bg-secondary">퇴사</span>';
            }}
        }}

        return `
            <tr>
                <td>${{e.employee_no || ''}}</td>
                <td>${{e.full_name || ''}}</td>
                <td>${{e.team || ''}}</td>
                <td>${{e.position || ''}}</td>
                <td>${{e.entrance_date || ''}}</td>
                <td>${{e.tenure_days || 0}}일</td>
                <td>${{absenceRate}}%</td>
                <td>${{unauthorizedRate}}</td>
                <td>${{statusBadge}}</td>
            </tr>
        `;
    }}).join('');

    tbody.innerHTML = rows;
}}

/**
 * Create Monthly Hiring Trend Chart
 * 월별 신규 입사자 트렌드 차트 생성
 */
function createRecentHiresMonthlyTrendChart() {{
    const canvas = document.getElementById('recentHiresMonthlyTrendChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Get last 6 months
    const months = availableMonths.slice(-6);

    // Count hires per month
    const monthlyHireCounts = months.map(month => {{
        const [year, monthNum] = month.split('-');
        return employeeDetails.filter(e => {{
            if (!e.entrance_date) return false;
            const entranceDate = new Date(e.entrance_date);
            return entranceDate.getFullYear() === parseInt(year) &&
                   (entranceDate.getMonth() + 1) === parseInt(monthNum);
        }}).length;
    }});

    // Format labels
    const labels = months.map(m => {{
        const [year, month] = m.split('-');
        return `${{year}}년 ${{parseInt(month)}}월`;
    }});

    modalCharts.recentHiresMonthlyTrend = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: labels,
            datasets: [{{
                label: '신규 입사자',
                data: monthlyHireCounts,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            return '신규 입사자: ' + context.parsed.y + '명';
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    ticks: {{ stepSize: 5 }},
                    title: {{
                        display: true,
                        text: '인원 (명)'
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Create Weekly Hiring Trend Chart
 * 주별 신규 입사자 트렌드 차트 생성
 */
function createRecentHiresWeeklyTrendChart() {{
    const canvas = document.getElementById('recentHiresWeeklyTrendChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Get all entrance dates from last 12 weeks
    const today = new Date(targetMonth + '-01');
    today.setMonth(today.getMonth() + 1);
    today.setDate(0); // Last day of target month

    const twelveWeeksAgo = new Date(today);
    twelveWeeksAgo.setDate(today.getDate() - (12 * 7));

    // Create weekly bins
    const weeklyData = [];
    const weekLabels = [];

    for (let i = 0; i < 12; i++) {{
        const weekStart = new Date(twelveWeeksAgo);
        weekStart.setDate(twelveWeeksAgo.getDate() + (i * 7));
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6);

        const count = employeeDetails.filter(e => {{
            if (!e.entrance_date) return false;
            const entranceDate = new Date(e.entrance_date);
            return entranceDate >= weekStart && entranceDate <= weekEnd;
        }}).length;

        weeklyData.push(count);
        weekLabels.push(`W${{i + 1}}`);
    }}

    modalCharts.recentHiresWeeklyTrend = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: weekLabels,
            datasets: [{{
                label: '주별 신규 입사자',
                data: weeklyData,
                borderColor: '#48c774',
                backgroundColor: 'rgba(72, 199, 116, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            return '신규 입사자: ' + context.parsed.y + '명';
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    ticks: {{ stepSize: 2 }},
                    title: {{
                        display: true,
                        text: '인원 (명)'
                    }}
                }}
            }}
        }}
    }});
}}

/**
 * Create Daily Hiring Trend Chart
 * 일별 신규 입사자 차트 생성 (당월)
 */
function createRecentHiresDailyTrendChart() {{
    const canvas = document.getElementById('recentHiresDailyTrendChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Get current month's hire dates
    const [year, month] = targetMonth.split('-');
    const daysInMonth = new Date(parseInt(year), parseInt(month), 0).getDate();

    // Create daily bins
    const dailyData = [];
    const dayLabels = [];

    for (let day = 1; day <= daysInMonth; day++) {{
        const targetDate = `${{year}}-${{month.padStart(2, '0')}}-${{day.toString().padStart(2, '0')}}`;
        const count = employeeDetails.filter(e => e.entrance_date === targetDate).length;
        dailyData.push(count);
        dayLabels.push(`${{day}}일`);
    }}

    modalCharts.recentHiresDailyTrend = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: dayLabels,
            datasets: [{{
                label: '일별 신규 입사자',
                data: dailyData,
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: '#667eea',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            return '신규 입사자: ' + context.parsed.y + '명';
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    ticks: {{ stepSize: 1 }},
                    title: {{
                        display: true,
                        text: '인원 (명)'
                    }}
                }},
                x: {{
                    ticks: {{
                        maxRotation: 45,
                        minRotation: 45
                    }}
                }}
            }}
        }}
    }});
}}

// Modal 6: Recent Resignations (Unified)
function showModal6() {{
    ['weekly', 'teams', 'types', 'change'].forEach(type => {{
        const chartKey = `modal6_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});
    const modal = new bootstrap.Modal(document.getElementById('modal6'));
    modal.show();
    setTimeout(() => {{ createUnifiedModalCharts(6, 'recent_resignations'); }}, 300);
}}

// Modal 7: Under 60 Days (Unified)
function showModal7() {{
    ['weekly', 'teams', 'types', 'change'].forEach(type => {{
        const chartKey = `modal7_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});
    const modal = new bootstrap.Modal(document.getElementById('modal7'));
    modal.show();
    setTimeout(() => {{ createUnifiedModalCharts(7, 'under_60_days'); }}, 300);
}}

// Modal 8: Post-Assignment Resignations (Unified)
function showModal8() {{
    ['weekly', 'teams', 'types', 'change'].forEach(type => {{
        const chartKey = `modal8_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});
    const modal = new bootstrap.Modal(document.getElementById('modal8'));
    modal.show();
    setTimeout(() => {{ createUnifiedModalCharts(8, 'post_assignment_resignations'); }}, 300);
}}

// Modal 9: Perfect Attendance (Unified)
function showModal9() {{
    ['weekly', 'teams', 'types', 'change'].forEach(type => {{
        const chartKey = `modal9_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});
    const modal = new bootstrap.Modal(document.getElementById('modal9'));
    modal.show();
    setTimeout(() => {{ createUnifiedModalCharts(9, 'perfect_attendance'); }}, 300);
}}

// Modal 10: Long-term Employees (Unified)
function showModal10() {{
    ['weekly', 'teams', 'types', 'change'].forEach(type => {{
        const chartKey = `modal10_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});
    const modal = new bootstrap.Modal(document.getElementById('modal10'));
    modal.show();
    setTimeout(() => {{ createUnifiedModalCharts(10, 'long_term_employees'); }}, 300);
}}

// Modal 11: Data Errors (Unified)
function showModal11() {{
    ['weekly', 'teams', 'types', 'change'].forEach(type => {{
        const chartKey = `modal11_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});
    const modal = new bootstrap.Modal(document.getElementById('modal11'));
    modal.show();
    setTimeout(() => {{ createUnifiedModalCharts(11, 'data_errors'); }}, 300);
}}

// Modal 12: Pregnant Employees (Unified)
function showModal12() {{
    ['weekly', 'teams', 'types', 'change'].forEach(type => {{
        const chartKey = `modal12_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});
    const modal = new bootstrap.Modal(document.getElementById('modal12'));
    modal.show();
    setTimeout(() => {{ createUnifiedModalCharts(12, 'pregnant_employees'); }}, 300);
}}

// Modal 13: Team Absence Breakdown (팀별 결근 분석)
function showModal13() {{
    // Destroy existing charts
    // 기존 차트 제거
    ['totalRate', 'comparison', 'days', 'authorizedBreakdown'].forEach(type => {{
        const chartKey = `modal13_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});

    const modal = new bootstrap.Modal(document.getElementById('modal13'));
    modal.show();

    setTimeout(() => {{
        const targetData = monthlyMetrics[targetMonth];
        if (!targetData || !targetData.team_absence_breakdown) {{
            debugLog('No team absence breakdown data found');
            return;
        }}

        const teamData = targetData.team_absence_breakdown;
        const teams = Object.keys(teamData).sort();

        // Calculate summary metrics
        // 요약 메트릭 계산
        const totalRates = teams.map(t => teamData[t].total_absence_rate || 0);
        const unauthorizedRates = teams.map(t => teamData[t].unauthorized_absence_rate || 0);
        const authorizedRates = teams.map(t => teamData[t].authorized_absence_rate || 0);

        const avgTotal = totalRates.reduce((a, b) => a + b, 0) / totalRates.length;
        const avgUnauthorized = unauthorizedRates.reduce((a, b) => a + b, 0) / unauthorizedRates.length;
        const avgAuthorized = authorizedRates.reduce((a, b) => a + b, 0) / authorizedRates.length;

        document.getElementById('avgTotalAbsenceRate').textContent = avgTotal.toFixed(1) + '%';
        document.getElementById('avgUnauthorizedRate').textContent = avgUnauthorized.toFixed(1) + '%';
        document.getElementById('avgAuthorizedRate').textContent = avgAuthorized.toFixed(1) + '%';

        // Chart 1: Total Absence Rate by Team (Bar Chart)
        // 차트 1: 팀별 전체 결근율 (막대 차트)
        modalCharts['modal13_totalRate'] = new Chart(document.getElementById('modalChart13_totalRate'), {{
            type: 'bar',
            data: {{
                labels: teams,
                datasets: [{{
                    label: currentLanguage === 'ko' ? '전체 결근율 (%)' :
                           currentLanguage === 'vi' ? 'Tỷ lệ vắng (%)' : 'Total Absence Rate (%)',
                    data: totalRates,
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: true }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: currentLanguage === 'ko' ? '결근율 (%)' :
                                  currentLanguage === 'vi' ? 'Tỷ lệ (%)' : 'Absence Rate (%)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: currentLanguage === 'ko' ? '팀' :
                                  currentLanguage === 'vi' ? 'Nhóm' : 'Team'
                        }}
                    }}
                }}
            }}
        }});

        // Chart 2: Unauthorized vs Authorized by Team (Grouped Bar Chart)
        // 차트 2: 팀별 무단 vs 승인 결근율 (그룹 막대 차트)
        modalCharts['modal13_comparison'] = new Chart(document.getElementById('modalChart13_comparison'), {{
            type: 'bar',
            data: {{
                labels: teams,
                datasets: [
                    {{
                        label: currentLanguage === 'ko' ? '무단 결근율 (%)' :
                               currentLanguage === 'vi' ? 'Vắng không phép (%)' : 'Unauthorized Rate (%)',
                        data: unauthorizedRates,
                        backgroundColor: 'rgba(255, 193, 7, 0.7)',
                        borderColor: 'rgba(255, 193, 7, 1)',
                        borderWidth: 2
                    }},
                    {{
                        label: currentLanguage === 'ko' ? '승인 결근율 (%)' :
                               currentLanguage === 'vi' ? 'Vắng có phép (%)' : 'Authorized Rate (%)',
                        data: authorizedRates,
                        backgroundColor: 'rgba(13, 202, 240, 0.7)',
                        borderColor: 'rgba(13, 202, 240, 1)',
                        borderWidth: 2
                    }},
                    {{
                        label: currentLanguage === 'ko' ? '전체 결근율 (%)' :
                               currentLanguage === 'vi' ? 'Tổng vắng (%)' : 'Total Rate (%)',
                        data: totalRates,
                        backgroundColor: 'rgba(220, 53, 69, 0.4)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 2,
                        type: 'line'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: true }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: currentLanguage === 'ko' ? '결근율 (%)' :
                                  currentLanguage === 'vi' ? 'Tỷ lệ (%)' : 'Absence Rate (%)'
                        }}
                    }}
                }}
            }}
        }});

        // Chart 3: Absence Days Distribution (Stacked Bar Chart)
        // 차트 3: 팀별 결근 일수 분포 (누적 막대 차트)
        const unauthorizedDays = teams.map(t => teamData[t].unauthorized_days || 0);
        const authorizedDays = teams.map(t => teamData[t].authorized_days || 0);

        modalCharts['modal13_days'] = new Chart(document.getElementById('modalChart13_days'), {{
            type: 'bar',
            data: {{
                labels: teams,
                datasets: [
                    {{
                        label: currentLanguage === 'ko' ? '무단 결근 일수' :
                               currentLanguage === 'vi' ? 'Ngày vắng không phép' : 'Unauthorized Days',
                        data: unauthorizedDays,
                        backgroundColor: 'rgba(255, 193, 7, 0.7)',
                        borderColor: 'rgba(255, 193, 7, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: currentLanguage === 'ko' ? '승인 결근 일수' :
                               currentLanguage === 'vi' ? 'Ngày vắng có phép' : 'Authorized Days',
                        data: authorizedDays,
                        backgroundColor: 'rgba(13, 202, 240, 0.7)',
                        borderColor: 'rgba(13, 202, 240, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: true }},
                    tooltip: {{
                        mode: 'index',
                        callbacks: {{
                            footer: function(tooltipItems) {{
                                let total = 0;
                                tooltipItems.forEach(item => {{ total += item.parsed.y; }});
                                return (currentLanguage === 'ko' ? '합계: ' :
                                        currentLanguage === 'vi' ? 'Tổng: ' : 'Total: ') + total + (currentLanguage === 'ko' ? '일' :
                                        currentLanguage === 'vi' ? ' ngày' : ' days');
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ stacked: true }},
                    y: {{
                        stacked: true,
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: currentLanguage === 'ko' ? '결근 일수' :
                                  currentLanguage === 'vi' ? 'Ngày vắng' : 'Absence Days'
                        }}
                    }}
                }}
            }}
        }});

        // Chart 4: Authorized Absence Breakdown (Stacked Bar Chart)
        // 차트 4: 승인 결근 사유 세부 분석 (누적 막대 차트)
        const maternityDays = teams.map(t => teamData[t].authorized_breakdown?.maternity_days || 0);
        const annualLeaveDays = teams.map(t => teamData[t].authorized_breakdown?.annual_leave_days || 0);
        const sickLeaveDays = teams.map(t => teamData[t].authorized_breakdown?.sick_leave_days || 0);
        const otherAuthorizedDays = teams.map(t => teamData[t].authorized_breakdown?.other_authorized_days || 0);

        modalCharts['modal13_authorizedBreakdown'] = new Chart(document.getElementById('modalChart13_authorizedBreakdown'), {{
            type: 'bar',
            data: {{
                labels: teams,
                datasets: [
                    {{
                        label: currentLanguage === 'ko' ? '출산휴가' :
                               currentLanguage === 'vi' ? 'Thai sản' : 'Maternity Leave',
                        data: maternityDays,
                        backgroundColor: 'rgba(220, 53, 69, 0.7)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: currentLanguage === 'ko' ? '연차' :
                               currentLanguage === 'vi' ? 'Nghỉ phép' : 'Annual Leave',
                        data: annualLeaveDays,
                        backgroundColor: 'rgba(13, 202, 240, 0.7)',
                        borderColor: 'rgba(13, 202, 240, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: currentLanguage === 'ko' ? '병가' :
                               currentLanguage === 'vi' ? 'Nghỉ ốm' : 'Sick Leave',
                        data: sickLeaveDays,
                        backgroundColor: 'rgba(25, 135, 84, 0.7)',
                        borderColor: 'rgba(25, 135, 84, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: currentLanguage === 'ko' ? '기타 승인' :
                               currentLanguage === 'vi' ? 'Khác có phép' : 'Other Authorized',
                        data: otherAuthorizedDays,
                        backgroundColor: 'rgba(108, 117, 125, 0.7)',
                        borderColor: 'rgba(108, 117, 125, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: true }},
                    tooltip: {{
                        mode: 'index',
                        callbacks: {{
                            footer: function(tooltipItems) {{
                                let total = 0;
                                tooltipItems.forEach(item => {{ total += item.parsed.y; }});
                                return (currentLanguage === 'ko' ? '합계: ' :
                                        currentLanguage === 'vi' ? 'Tổng: ' : 'Total: ') + total + (currentLanguage === 'ko' ? '일' :
                                        currentLanguage === 'vi' ? ' ngày' : ' days');
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ stacked: true }},
                    y: {{
                        stacked: true,
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: currentLanguage === 'ko' ? '승인 결근 일수' :
                                  currentLanguage === 'vi' ? 'Ngày vắng có phép' : 'Authorized Days'
                        }}
                    }}
                }}
            }}
        }});
    }}, 300);
}}

// ============================================
// Modal 14: Punctuality Issues (Come Late / Leave Early)
// 모달 14: 지각/조퇴 상세
// ============================================

function showModal14() {{
    // Destroy existing charts / 기존 차트 제거
    ['comparison', 'team'].forEach(type => {{
        const chartKey = `modal14_${{type}}`;
        if (modalCharts[chartKey]) modalCharts[chartKey].destroy();
    }});

    const modal = new bootstrap.Modal(document.getElementById('modal14'));
    modal.show();

    setTimeout(() => {{
        // Get punctuality data from modalData / modalData에서 지각/조퇴 데이터 가져오기
        const punctualityData = modalData.punctuality_metrics;
        const punctualityDetails = modalData.punctuality_details || [];

        if (!punctualityData) {{
            debugLog('No punctuality data found');
            return;
        }}

        // Update summary cards / 요약 카드 업데이트
        document.getElementById('totalComeLate').textContent = punctualityData.come_late_total || 0;
        document.getElementById('totalLeaveEarly').textContent = punctualityData.leave_early_total || 0;
        document.getElementById('punctualityAffected').textContent = punctualityData.affected_employees || 0;

        // Chart 1: Come Late vs Leave Early Comparison (Doughnut)
        // 차트 1: 지각 vs 조퇴 비교 (도넛 차트)
        const comeLate = punctualityData.come_late_total || 0;
        const leaveEarly = punctualityData.leave_early_total || 0;

        modalCharts['modal14_comparison'] = new Chart(document.getElementById('modalChart14_comparison'), {{
            type: 'doughnut',
            data: {{
                labels: [
                    currentLanguage === 'ko' ? '지각' : currentLanguage === 'vi' ? 'Đi muộn' : 'Come Late',
                    currentLanguage === 'ko' ? '조퇴' : currentLanguage === 'vi' ? 'Về sớm' : 'Leave Early'
                ],
                datasets: [{{
                    data: [comeLate, leaveEarly],
                    backgroundColor: ['rgba(255, 193, 7, 0.8)', 'rgba(23, 162, 184, 0.8)'],
                    borderColor: ['rgba(255, 193, 7, 1)', 'rgba(23, 162, 184, 1)'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    title: {{
                        display: true,
                        text: currentLanguage === 'ko' ? '지각 vs 조퇴 비율' :
                              currentLanguage === 'vi' ? 'Tỷ lệ đi muộn vs về sớm' : 'Come Late vs Leave Early Ratio'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const total = comeLate + leaveEarly;
                                const percentage = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                                const countLabel = currentLanguage === 'ko' ? '건' :
                                                   currentLanguage === 'vi' ? 'lần' : 'times';
                                return `${{context.label}}: ${{context.raw}}${{countLabel}} (${{percentage}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Populate employee table / 직원 테이블 채우기
        const tbody = document.getElementById('punctualityEmployeeList');
        tbody.innerHTML = '';

        if (punctualityDetails.length === 0) {{
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">
                ${{currentLanguage === 'ko' ? '지각/조퇴 데이터가 없습니다' :
                   currentLanguage === 'vi' ? 'Không có dữ liệu đi muộn/về sớm' : 'No punctuality issues found'}}
            </td></tr>`;
        }} else {{
            // Use document fragment for better performance / 더 나은 성능을 위해 document fragment 사용
            const fragment = document.createDocumentFragment();
            punctualityDetails.forEach((emp, index) => {{
                const totalBadge = emp.total_issues >= 5 ? 'bg-danger' :
                                  emp.total_issues >= 3 ? 'bg-warning' : 'bg-info';
                const row = document.createElement('tr');
                // Sanitize user-controlled strings to prevent XSS / XSS 방지를 위해 사용자 데이터 새니타이즈
                row.innerHTML = `
                    <td>${{index + 1}}</td>
                    <td>${{sanitizeHTML(emp.employee_name || emp.employee_id)}}</td>
                    <td>${{sanitizeHTML(emp.team || '-')}}</td>
                    <td class="text-center">
                        <span class="badge bg-warning text-dark">${{emp.come_late}}</span>
                    </td>
                    <td class="text-center">
                        <span class="badge bg-info">${{emp.leave_early}}</span>
                    </td>
                    <td class="text-center">
                        <span class="badge ${{totalBadge}}">${{emp.total_issues}}</span>
                    </td>
                `;
                fragment.appendChild(row);
            }});
            tbody.appendChild(fragment);  // Single DOM reflow / 단일 DOM 리플로우
        }}
    }}, 300);
}}

// ============================================
// Issue Summary Modal Function
// 이슈 요약 모달 함수
// ============================================

function showIssueSummaryModal(type, index) {{
    debugLog('📊 Opening Issue Summary Modal:', type, index);

    // Get executive summary data from modalData
    // modalData에서 경영진 요약 데이터 가져오기
    const summaryData = modalData.executive_summary;
    if (!summaryData) {{
        debugLog('No executive summary data found');
        return;
    }}

    let item, modalTitle, modalIcon, detailColor;

    if (type === 'issue') {{
        item = summaryData.issues[index];
        if (!item) return;
        modalTitle = currentLanguage === 'ko' ? '이슈 상세 분석' :
                     currentLanguage === 'vi' ? 'Phân tích chi tiết vấn đề' : 'Issue Detail Analysis';
        modalIcon = item.severity || '⚠️';
        detailColor = '#dc3545';
    }} else if (type === 'positive') {{
        item = summaryData.positive_changes[index];
        if (!item) return;
        modalTitle = currentLanguage === 'ko' ? '긍정적 변화 상세' :
                     currentLanguage === 'vi' ? 'Chi tiết thay đổi tích cực' : 'Positive Change Details';
        modalIcon = item.icon || '✅';
        detailColor = '#28a745';
    }} else {{
        return;
    }}

    // Get description based on language
    // 언어별 설명 가져오기
    const description = item[currentLanguage] || item['ko'];

    // Build metrics HTML if details available
    // 상세 데이터가 있으면 메트릭 HTML 생성
    let metricsHtml = '';
    if (item.details) {{
        const d = item.details;
        const current = (d.current !== undefined && d.current !== null) ? d.current : '-';
        const previous = (d.previous !== undefined && d.previous !== null) ? d.previous : '-';
        const change = d.change;

        let changeText = '-';
        let changeColor = '#6c757d';
        if (change) {{
            const absChange = Math.abs(change.absolute);
            const sign = change.absolute >= 0 ? '+' : '';
            changeText = `${{sign}}${{change.absolute.toFixed(1)}}`;

            // Color based on type (for issues, increase is bad; for positive, increase is good)
            if (type === 'issue') {{
                changeColor = change.absolute > 0 ? '#dc3545' : '#28a745';
            }} else {{
                changeColor = change.absolute > 0 ? '#28a745' : '#dc3545';
            }}
        }}

        const currentLabel = currentLanguage === 'ko' ? '현재' :
                            currentLanguage === 'vi' ? 'Hiện tại' : 'Current';
        const previousLabel = currentLanguage === 'ko' ? '전월' :
                             currentLanguage === 'vi' ? 'Tháng trước' : 'Previous';
        const changeLabel = currentLanguage === 'ko' ? '변화' :
                           currentLanguage === 'vi' ? 'Thay đổi' : 'Change';

        metricsHtml = `
            <div class="issue-detail-metrics mt-3">
                <div class="issue-metric-box">
                    <div class="issue-metric-value" style="color: ${{detailColor}}">${{typeof current === 'number' ? current.toFixed(1) : current}}</div>
                    <div class="issue-metric-label">${{currentLabel}}</div>
                </div>
                <div class="issue-metric-box">
                    <div class="issue-metric-value" style="color: #6c757d">${{typeof previous === 'number' ? previous.toFixed(1) : previous}}</div>
                    <div class="issue-metric-label">${{previousLabel}}</div>
                </div>
                <div class="issue-metric-box">
                    <div class="issue-metric-value" style="color: ${{changeColor}}">${{changeText}}</div>
                    <div class="issue-metric-label">${{changeLabel}}</div>
                </div>
            </div>
        `;
    }}

    // Build action suggestions based on issue type
    // 이슈 유형별 조치 제안 생성
    let actionHtml = '';
    const actionTitle = currentLanguage === 'ko' ? '권장 조치' :
                       currentLanguage === 'vi' ? 'Hành động đề xuất' : 'Recommended Actions';

    if (item.type) {{
        const actions = getActionSuggestions(item.type, currentLanguage);
        if (actions.length > 0) {{
            actionHtml = `
                <div class="mt-4">
                    <h6 class="fw-bold"><span style="color: ${{detailColor}}">📋</span> ${{actionTitle}}</h6>
                    <ul class="list-unstyled mt-2">
                        ${{actions.map(a => `<li class="mb-2">• ${{a}}</li>`).join('')}}
                    </ul>
                </div>
            `;
        }}
    }}

    // Build related KPI link
    // 관련 KPI 링크 생성
    let relatedKpiHtml = '';
    const relatedKpiTitle = currentLanguage === 'ko' ? '관련 KPI 상세 보기' :
                           currentLanguage === 'vi' ? 'Xem chi tiết KPI' : 'View Related KPI Details';

    if (item.details && item.details.metric) {{
        const metricToModal = {{
            'resignation_rate': 4,
            'absence_rate_excl_maternity': 2,
            'unauthorized_absence_rate': 3,
            'under_60_days': 7,
            'perfect_attendance': 9,
            'long_term_employees': 10,
            'total_employees': 1,
            'data_errors': 11
        }};
        const modalNum = metricToModal[item.details.metric];
        if (modalNum) {{
            relatedKpiHtml = `
                <div class="text-center mt-4">
                    <button class="btn btn-outline-primary btn-sm" onclick="document.getElementById('issueSummaryModal').querySelector('.btn-close').click(); setTimeout(() => showModal${{modalNum}}(), 300);">
                        <i class="bi bi-graph-up"></i> ${{relatedKpiTitle}} →
                    </button>
                </div>
            `;
        }}
    }}

    // Set modal content
    // 모달 내용 설정
    document.getElementById('issueSummaryModalTitle').innerHTML = `${{modalIcon}} ${{modalTitle}}`;
    document.getElementById('issueSummaryModalBody').innerHTML = `
        <div class="issue-detail-card" style="border-left: 4px solid ${{detailColor}}">
            <div class="issue-detail-title">
                <span style="font-size: 24px;">${{modalIcon}}</span>
                <span>${{description}}</span>
            </div>
            ${{metricsHtml}}
            ${{actionHtml}}
            ${{relatedKpiHtml}}
        </div>
    `;

    // Show modal
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('issueSummaryModal'));
    modal.show();
}}

// Get action suggestions based on issue type
// 이슈 유형별 조치 제안
function getActionSuggestions(issueType, lang) {{
    const suggestions = {{
        'resignation_high': {{
            ko: ['퇴사 면담 실시 및 원인 분석', '복리후생 개선 검토', '직무 만족도 설문 조사 실시'],
            en: ['Conduct exit interviews to analyze causes', 'Review benefits and compensation', 'Survey job satisfaction'],
            vi: ['Thực hiện phỏng vấn nghỉ việc', 'Xem xét cải thiện phúc lợi', 'Khảo sát mức độ hài lòng']
        }},
        'resignation_improved': {{
            ko: ['현재 유지 정책 지속', '긍정적 요인 파악 및 확대 적용', '직원 만족도 추적 모니터링'],
            en: ['Continue current retention policies', 'Identify positive factors and expand', 'Track employee satisfaction'],
            vi: ['Tiếp tục chính sách giữ chân', 'Xác định yếu tố tích cực', 'Theo dõi sự hài lòng']
        }},
        'absence_high': {{
            ko: ['결근 패턴 분석 및 원인 파악', '근무 환경 개선 검토', '출퇴근 관리 강화'],
            en: ['Analyze absence patterns', 'Review work environment', 'Strengthen attendance management'],
            vi: ['Phân tích mẫu vắng mặt', 'Xem xét môi trường làm việc', 'Tăng cường quản lý chuyên cần']
        }},
        'absence_improved': {{
            ko: ['현재 출퇴근 관리 정책 유지', '우수 팀 사례 공유', '개선 요인 문서화'],
            en: ['Maintain current attendance policies', 'Share best team practices', 'Document improvement factors'],
            vi: ['Duy trì chính sách hiện tại', 'Chia sẻ thực tiễn tốt nhất', 'Ghi chép yếu tố cải thiện']
        }},
        'unauthorized_high': {{
            ko: ['무단 결근자 개별 면담 실시', '근태 관리 정책 재검토', '경고 조치 및 교육 실시'],
            en: ['Individual interviews with absentees', 'Review attendance policy', 'Issue warnings and provide training'],
            vi: ['Phỏng vấn cá nhân với người vắng', 'Xem lại chính sách', 'Đưa ra cảnh báo và đào tạo']
        }},
        'early_resignation': {{
            ko: ['신입사원 온보딩 프로그램 강화', '멘토링 제도 도입 검토', '조기 적응 지원 프로그램 개발'],
            en: ['Strengthen onboarding program', 'Consider mentoring system', 'Develop early adaptation support'],
            vi: ['Tăng cường chương trình hội nhập', 'Xem xét hệ thống cố vấn', 'Phát triển hỗ trợ thích ứng']
        }},
        'under60_high': {{
            ko: ['신규 입사자 집중 관리', '이탈 방지 프로그램 가동', '1:1 면담으로 고충 파악'],
            en: ['Focus on new employee management', 'Activate retention program', 'Conduct 1:1 interviews'],
            vi: ['Tập trung quản lý NV mới', 'Kích hoạt chương trình giữ chân', 'Phỏng vấn 1:1']
        }},
        'retention_improved': {{
            ko: ['현재 신입사원 관리 정책 유지', '성공적인 온보딩 요소 분석', '우수 사례 전파'],
            en: ['Continue new hire management', 'Analyze successful onboarding', 'Share best practices'],
            vi: ['Tiếp tục quản lý NV mới', 'Phân tích hội nhập thành công', 'Chia sẻ thực tiễn tốt']
        }},
        'attendance_improved': {{
            ko: ['개근자 인센티브 프로그램 유지', '출석률 우수 팀 표창', '근무 환경 만족도 지속 모니터링'],
            en: ['Continue perfect attendance incentives', 'Recognize high-attendance teams', 'Monitor work satisfaction'],
            vi: ['Duy trì khuyến khích chuyên cần', 'Công nhận nhóm xuất sắc', 'Theo dõi sự hài lòng']
        }},
        'headcount_growth': {{
            ko: ['신규 인력 온보딩 프로세스 점검', '조직 역량 강화 계획 수립', '성장에 따른 인프라 확충 검토'],
            en: ['Review onboarding process', 'Plan organizational capability', 'Review infrastructure for growth'],
            vi: ['Xem xét quy trình hội nhập', 'Lập kế hoạch năng lực', 'Xem xét cơ sở hạ tầng']
        }},
        'loyalty_improved': {{
            ko: ['장기근속자 유지 전략 강화', '경력 개발 프로그램 확대', '장기근속 보상 제도 검토'],
            en: ['Strengthen retention for long-term employees', 'Expand career development', 'Review tenure rewards'],
            vi: ['Tăng cường giữ chân NV lâu năm', 'Mở rộng phát triển nghề nghiệp', 'Xem xét phần thưởng']
        }},
        'data_errors': {{
            ko: ['데이터 입력 프로세스 점검', '담당자 교육 실시', '자동 검증 시스템 도입 검토'],
            en: ['Review data entry process', 'Train responsible staff', 'Consider automated validation'],
            vi: ['Xem xét quy trình nhập liệu', 'Đào tạo nhân viên', 'Xem xét xác thực tự động']
        }}
    }};

    return suggestions[issueType]?.[lang] || suggestions[issueType]?.['en'] || [];
}}

// ============================================
// Enhanced Modal Functions for Management Insights
// ============================================

// Show enhanced resignation rate modal
function showEnhancedResignationModal() {{
    const modal = new bootstrap.Modal(document.getElementById('modal_resignation_enhanced'));
    modal.show();
}}

// Show enhanced absence rate modal
function showEnhancedAbsenceModal() {{
    const modal = new bootstrap.Modal(document.getElementById('modal_absence_enhanced'));
    modal.show();
}}

// Show enhanced unauthorized absence modal
function showEnhancedUnauthorizedModal() {{
    const modal = new bootstrap.Modal(document.getElementById('modal_unauthorized_enhanced'));
    modal.show();
}}

// Show enhanced early resignation modal
function showEnhancedEarlyResignationModal() {{
    const modal = new bootstrap.Modal(document.getElementById('modal_early_resignation_enhanced'));
    modal.show();
}}

// ============================================
// Modal Team Filtering
// ============================================

// Store original modal data for filtering
const originalModalData = {
    absence: modalData.absence_details || [],
    unauthorized: modalData.unauthorized_details || []
};

// Populate team filter dropdown for a specific modal
function populateTeamFilter(modalNum) {
    const select = document.getElementById(`modalTeamFilter${modalNum}`);
    if (!select) return;

    // Get unique teams from employee details
    const teams = new Set();
    employeeDetails.forEach(emp => {
        if (emp.team_name) teams.add(emp.team_name);
    });

    // Clear and recreate "전체 팀" option with language attributes and current language text
    const allTeamsText = currentLanguage === 'ko' ? '전체 팀' :
                        currentLanguage === 'en' ? 'All Teams' : 'Tất cả nhóm';

    select.innerHTML = `<option value="all" class="lang-option" data-ko="전체 팀" data-en="All Teams" data-vi="Tất cả nhóm">${allTeamsText}</option>`;

    // Add team options sorted alphabetically
    Array.from(teams).sort().forEach(team => {
        const option = document.createElement('option');
        option.value = team;
        option.textContent = team;
        select.appendChild(option);
    });
}

// Filter modal data by selected team
function filterModalByTeam(modalNum) {
    const select = document.getElementById(`modalTeamFilter${modalNum}`);
    if (!select) return;

    const selectedTeam = select.value;

    // Re-render modal with filtered data
    if (modalNum === 2) {
        showModal2(selectedTeam);
    } else if (modalNum === 3) {
        showModal3(selectedTeam);
    } else if (modalNum >= 4 && modalNum <= 11) {
        // For modals 4-11, we need to filter employeeDetails
        const modal = document.getElementById(`modal${modalNum}`);
        if (modal && modal.classList.contains('show')) {
            // Modal is already open, just update the content
            updateModalContent(modalNum, selectedTeam);
        }
    }
}

// Update modal content with team filter
function updateModalContent(modalNum, teamFilter) {
    let filteredEmployees = employeeDetails;

    if (teamFilter && teamFilter !== 'all') {
        filteredEmployees = employeeDetails.filter(e => e.team_name === teamFilter);
    }

    const tbody = document.getElementById(`modalTableBody${modalNum}`);
    if (!tbody) return;

    // Update table based on modal number
    switch(modalNum) {
        case 4: // Resignation Rate
            filteredEmployees = filteredEmployees.filter(e => e.resigned_this_month);
            tbody.innerHTML = filteredEmployees.map(e => `
                <tr>
                    <td>${e.employee_no}</td>
                    <td>${e.full_name}</td>
                    <td>${e.position_1st || 'N/A'}</td>
                    <td>${e.stop_working_date || 'N/A'}</td>
                </tr>
            `).join('');
            break;

        case 5: // Recent Hires
            filteredEmployees = filteredEmployees.filter(e => e.hired_this_month);
            tbody.innerHTML = filteredEmployees.map(e => `
                <tr>
                    <td>${e.employee_no}</td>
                    <td>${e.full_name}</td>
                    <td>${e.position_1st || 'N/A'}</td>
                    <td>${e.entrance_date || 'N/A'}</td>
                </tr>
            `).join('');
            break;

        case 6: // Recent Resignations
            filteredEmployees = filteredEmployees.filter(e => e.resigned_this_month);
            tbody.innerHTML = filteredEmployees.map(e => `
                <tr>
                    <td>${e.employee_no}</td>
                    <td>${e.full_name}</td>
                    <td>${e.position_1st || 'N/A'}</td>
                    <td>${e.stop_working_date || 'N/A'}</td>
                </tr>
            `).join('');
            break;

        case 7: // Under 60 Days
            filteredEmployees = filteredEmployees.filter(e => e.tenure_days < 60 && e.is_active);
            tbody.innerHTML = filteredEmployees.map(e => `
                <tr>
                    <td>${e.employee_no}</td>
                    <td>${e.full_name}</td>
                    <td>${e.position_1st || 'N/A'}</td>
                    <td>${e.tenure_days} days</td>
                </tr>
            `).join('');
            break;

        case 8: // Post-Assignment Resignations (30-60 days after hire)
            // 배정 후 퇴사자: 입사 후 30-60일 사이에 퇴사한 직원
            filteredEmployees = filteredEmployees.filter(e => e.post_assignment_resignation);
            tbody.innerHTML = filteredEmployees.map(e => `
                <tr>
                    <td>${e.employee_no}</td>
                    <td>${e.full_name}</td>
                    <td>${e.position_1st || 'N/A'}</td>
                    <td>${e.entrance_date || 'N/A'}</td>
                    <td>${e.stop_working_date || 'N/A'}</td>
                </tr>
            `).join('');
            break;

        case 9: // Perfect Attendance
            // 개근자: is_active && perfect_attendance 조건 (퇴사자 제외)
            filteredEmployees = filteredEmployees.filter(e => e.is_active && e.perfect_attendance);
            tbody.innerHTML = filteredEmployees.map(e => `
                <tr>
                    <td>${e.employee_no}</td>
                    <td>${e.full_name}</td>
                    <td>${e.position_1st || 'N/A'}</td>
                    <td>${e.attendance_rate?.toFixed(1) || '100.0'}%</td>
                </tr>
            `).join('');
            break;

        case 10: // Long-term Employees
            filteredEmployees = filteredEmployees.filter(e => e.tenure_days >= 365 && e.is_active);
            tbody.innerHTML = filteredEmployees.map(e => `
                <tr>
                    <td>${e.employee_no}</td>
                    <td>${e.full_name}</td>
                    <td>${e.position_1st || 'N/A'}</td>
                    <td>${Math.floor(e.tenure_days / 365)} years</td>
                </tr>
            `).join('');
            break;

        case 11: // Data Errors
            filteredEmployees = filteredEmployees.filter(e => e.has_data_error);
            tbody.innerHTML = filteredEmployees.map(e => `
                <tr>
                    <td>${e.employee_no}</td>
                    <td>${e.full_name}</td>
                    <td>${e.error_type || 'Unknown'}</td>
                    <td>${e.error_description || 'N/A'}</td>
                </tr>
            `).join('');
            break;

        case 12: // Pregnant Employees
            // 임신 직원: is_pregnant 플래그가 true인 직원
            filteredEmployees = filteredEmployees.filter(e => e.is_pregnant === true);
            tbody.innerHTML = filteredEmployees.map(e => `
                <tr>
                    <td>${e.employee_no}</td>
                    <td>${e.full_name}</td>
                    <td>${e.position_1st || 'N/A'}</td>
                    <td>${e.team || 'N/A'}</td>
                </tr>
            `).join('');
            break;
    }

    // Update chart with filtered data count
    updateModalChart(modalNum, filteredEmployees.length);
}

// Update modal chart with filtered data
function updateModalChart(modalNum, filteredCount) {
    if (modalCharts[`modal${modalNum}`]) {
        // For simplicity, we'll just note that the chart reflects filtered data
        // Full chart re-rendering with filtered trend data would require more complex logic
        debugLog(`Modal ${modalNum} filtered to ${filteredCount} records`);
    }
}

// ============================================
// Table Sorting
// ============================================

let modalSortStates = {};

function sortModalTable(modalNum, columnIndex) {
    const tableId = 'modalTable' + modalNum;
    const tbody = document.getElementById('modalTableBody' + modalNum);
    const rows = Array.from(tbody.getElementsByTagName('tr'));

    // Initialize sort state
    if (!modalSortStates[tableId]) {
        modalSortStates[tableId] = { column: -1, asc: true };
    }

    // Toggle sort direction
    if (modalSortStates[tableId].column === columnIndex) {
        modalSortStates[tableId].asc = !modalSortStates[tableId].asc;
    } else {
        modalSortStates[tableId].column = columnIndex;
        modalSortStates[tableId].asc = true;
    }

    const asc = modalSortStates[tableId].asc;

    rows.sort((a, b) => {
        const aText = a.getElementsByTagName('td')[columnIndex].textContent.trim();
        const bText = b.getElementsByTagName('td')[columnIndex].textContent.trim();

        // Try numeric comparison first
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return asc ? aNum - bNum : bNum - aNum;
        }

        // String comparison
        return asc ? aText.localeCompare(bText) : bText.localeCompare(aText);
    });

    rows.forEach(row => tbody.appendChild(row));
}

// ============================================
// Employee Details Tab Functions
// ============================================

let currentFilter = 'all';
let currentTeamFilter = 'all';
let currentSortColumn = -1;
let currentSortAsc = true;
// Multi-column sort support (Shift+click for secondary sort)
// 다중 컬럼 정렬 지원 (Shift+클릭으로 2차 정렬)
let secondarySortColumn = -1;
let secondarySortAsc = true;
let currentPage = 1;
let pageSize = 50;
let searchTerm = '';
let searchTimeout = null;
let selectedEmployees = new Set();
// Default column visibility: hide Building(4), Line(5), Boss(6), StopDate(11) for cleaner view
// 기본 열 표시 설정: 깔끔한 화면을 위해 건물(4), 라인(5), 상사(6), 퇴사일(11) 숨김
// Columns: ID(0), Name(1), Position(2), Type(3), Building(4), Line(5), Boss(6), WorkDays(7), Absent(8), Unauth(9), Start(10), Stop(11), Tenure(12), Status(13)
let columnVisibility = [true, true, true, true, false, false, false, true, true, true, true, false, true, true];
let filteredEmployees = [];

// Column field mapping for sorting
// 정렬을 위한 컬럼 필드 매핑
const sortColumnMap = [
    'employee_id',           // Column 0: 사번/ID
    'employee_name',         // Column 1: 이름/Name
    'position',              // Column 2: 직급/Position
    'role_type',             // Column 3: 유형/Type
    'building',              // Column 4: 건물/Building
    'line',                  // Column 5: 라인/Line
    'boss_name',             // Column 6: 상사/Boss
    'working_days',          // Column 7: 근무일/Work Days (numeric)
    'absent_days',           // Column 8: 결근/Absent Days (numeric)
    'unauthorized_absent_days', // Column 9: 무단/Unauthorized (numeric)
    'entrance_date',         // Column 10: 입사일/Start
    'stop_date',             // Column 11: 퇴사일/End
    'tenure_days'            // Column 12: 재직기간/Tenure (numeric)
];

// Apply sorting to employee array
// 직원 배열에 정렬 적용
function applySortToData(employees) {{
    if (currentSortColumn < 0 || currentSortColumn >= sortColumnMap.length) {{
        return employees;
    }}

    const field = sortColumnMap[currentSortColumn];
    const numericFields = ['tenure_days', 'working_days', 'absent_days', 'unauthorized_absent_days'];

    // Helper function to compare two values
    // 두 값을 비교하는 헬퍼 함수
    function compareValues(aVal, bVal, fieldName, ascending) {{
        if (numericFields.includes(fieldName)) {{
            aVal = parseInt(aVal) || 0;
            bVal = parseInt(bVal) || 0;
            return ascending ? aVal - bVal : bVal - aVal;
        }}
        aVal = String(aVal || '').toLowerCase();
        bVal = String(bVal || '').toLowerCase();
        return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }}

    const sorted = [...employees].sort((a, b) => {{
        // Primary sort
        // 1차 정렬
        let aVal = a[field] || '';
        let bVal = b[field] || '';
        let result = compareValues(aVal, bVal, field, currentSortAsc);

        // Secondary sort if primary values are equal
        // 1차 값이 같으면 2차 정렬 적용
        if (result === 0 && secondarySortColumn >= 0 && secondarySortColumn < sortColumnMap.length) {{
            const secondaryField = sortColumnMap[secondarySortColumn];
            let aVal2 = a[secondaryField] || '';
            let bVal2 = b[secondaryField] || '';
            result = compareValues(aVal2, bVal2, secondaryField, secondarySortAsc);
        }}

        return result;
    }});

    return sorted;
}}

// Update sort indicator visuals (supports multi-column sort)
// 정렬 표시 시각적 업데이트 (다중 컬럼 정렬 지원)
function updateSortIndicators() {{
    document.querySelectorAll('.sort-indicator').forEach((el, idx) => {{
        if (idx === currentSortColumn) {{
            // Primary sort indicator with "1" prefix for multi-sort
            // 다중 정렬 시 "1" 접두사가 붙은 1차 정렬 표시
            const prefix = secondarySortColumn >= 0 ? '¹' : '';
            el.textContent = prefix + (currentSortAsc ? '↑' : '↓');
        }} else if (idx === secondarySortColumn) {{
            // Secondary sort indicator with "2" prefix
            // "2" 접두사가 붙은 2차 정렬 표시
            el.textContent = '²' + (secondarySortAsc ? '↑' : '↓');
        }} else {{
            el.textContent = '';
        }}
    }});

    document.querySelectorAll('th.sortable').forEach((th, idx) => {{
        th.classList.remove('sorted', 'sorted-secondary');
        if (idx === currentSortColumn) {{
            th.classList.add('sorted');
        }} else if (idx === secondarySortColumn) {{
            th.classList.add('sorted-secondary');
        }}
    }});
}}

function renderEmployeeTable(employees = null) {
    const tbody = document.getElementById('employeeTableBody');
    if (!tbody) return;

    let displayEmployees = employees || employeeDetails;

    // Apply sorting BEFORE pagination
    // 페이지네이션 전에 정렬 적용
    displayEmployees = applySortToData(displayEmployees);

    // Apply pagination
    filteredEmployees = displayEmployees;
    const totalPages = pageSize === -1 ? 1 : Math.ceil(filteredEmployees.length / pageSize);

    if (pageSize !== -1) {
        const start = (currentPage - 1) * pageSize;
        const end = start + pageSize;
        displayEmployees = filteredEmployees.slice(start, end);
    }

    // Update pagination UI
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
    document.getElementById('prevPageBtn').disabled = currentPage === 1;
    document.getElementById('nextPageBtn').disabled = currentPage >= totalPages || pageSize === -1;

    if (displayEmployees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="15" class="text-center text-muted py-4">직원이 없습니다.</td></tr>';
        updateEmployeeCount(0);
        updateQuickStats([]);
        return;
    }

    let html = '';
    displayEmployees.forEach(emp => {
        // Improved tenure display: years/months format for better readability
        // 재직기간 표시 개선: 가독성을 위해 년/월 형식으로 표시
        const tenureDays = emp.tenure_days || 0;
        const tenureYears = Math.floor(tenureDays / 365);
        const tenureMonths = Math.floor((tenureDays % 365) / 30);
        let tenureDisplay = '-';
        if (tenureDays > 0) {
            if (tenureYears >= 1) {
                tenureDisplay = tenureMonths > 0 ? `${tenureYears}년 ${tenureMonths}개월` : `${tenureYears}년`;
            } else if (tenureMonths >= 1) {
                tenureDisplay = `${tenureMonths}개월`;
            } else {
                tenureDisplay = `${tenureDays}일`;
            }
        }

        // Determine row class based on employee status
        let rowClass = '';
        if (emp.resigned_this_month) rowClass = 'row-resigned';
        else if (emp.hired_this_month) rowClass = 'row-new';
        else if (emp.perfect_attendance) rowClass = 'row-perfect';
        else if (emp.is_active) rowClass = 'row-active';

        if (selectedEmployees.has(emp.employee_id)) {
            rowClass += ' row-selected';
        }

        // Status badges with multilingual support (uses currentLanguage)
        // 다국어 지원 상태 배지 (currentLanguage 사용)
        const badgeText = (ko, en, vi) => {{
            const texts = {{ ko, en, vi }};
            return texts[currentLanguage] || ko;
        }};

        let statusBadges = [];
        if (emp.is_active) {{
            statusBadges.push(`<span class="badge bg-success badge-status lang-badge" data-ko="재직" data-en="Active" data-vi="Đang làm">${{badgeText('재직', 'Active', 'Đang làm')}}</span>`);
        }} else {{
            statusBadges.push(`<span class="badge bg-secondary badge-status lang-badge" data-ko="퇴사" data-en="Resigned" data-vi="Nghỉ việc">${{badgeText('퇴사', 'Resigned', 'Nghỉ việc')}}</span>`);
        }}
        if (emp.hired_this_month) {{
            statusBadges.push(`<span class="badge bg-info badge-status lang-badge" data-ko="신입" data-en="New" data-vi="Mới">${{badgeText('신입', 'New', 'Mới')}}</span>`);
        }}
        if (emp.perfect_attendance) {{
            statusBadges.push(`<span class="badge bg-primary badge-status lang-badge" data-ko="개근" data-en="Perfect" data-vi="Hoàn hảo">${{badgeText('개근', 'Perfect', 'Hoàn hảo')}}</span>`);
        }}
        if (emp.long_term) {{
            statusBadges.push(`<span class="badge bg-warning text-dark badge-status lang-badge" data-ko="장기" data-en="Long-term" data-vi="Lâu năm">${{badgeText('장기', 'Long-term', 'Lâu năm')}}</span>`);
        }}
        if (emp.is_pregnant) {{
            statusBadges.push(`<span class="badge bg-danger badge-status lang-badge" data-ko="임신" data-en="Pregnant" data-vi="Mang thai">${{badgeText('임신', 'Pregnant', 'Mang thai')}}</span>`);
        }}
        if (emp.under_60_days) {{
            statusBadges.push(`<span class="badge bg-light text-dark badge-status lang-badge" data-ko="60일미만" data-en="<60 Days" data-vi="<60 Ngày">${{badgeText('60일미만', '<60 Days', '<60 Ngày')}}</span>`);
        }}

        // P2-1: Add turnover risk indicator
        // P2-1: 이직 위험 지표 추가
        const riskBadge = getTurnoverRiskBadge(emp, currentLanguage);
        if (riskBadge) {{
            statusBadges.push(riskBadge);
        }}

        const isChecked = selectedEmployees.has(emp.employee_id) ? 'checked' : '';

        // Attendance data with visual indicators
        // 출결 데이터 시각적 표시
        const workingDays = emp.working_days || 0;
        const absentDays = emp.absent_days || 0;
        const unauthorizedDays = emp.unauthorized_absent_days || 0;

        // Absent days badge color based on count
        const absentBadgeClass = absentDays === 0 ? 'bg-success' : (absentDays >= 3 ? 'bg-danger' : 'bg-warning text-dark');
        const unauthorizedBadgeClass = unauthorizedDays === 0 ? 'bg-light text-muted' : 'bg-danger';

        // Apply search highlighting to searchable fields
        // 검색 가능한 필드에 검색 하이라이팅 적용
        const hl = (val) => currentSearchTerm ? highlightText(val, currentSearchTerm) : (val || '');

        html += `
            <tr class="${rowClass}">
                <td onclick="event.stopPropagation()"><input type="checkbox" class="employee-checkbox" value="${emp.employee_id}" ${isChecked} onchange="toggleEmployeeSelection('${emp.employee_id}')"></td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${hl(emp.employee_id)}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${hl(emp.employee_name)}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${hl(emp.position)}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;"><span class="badge bg-light text-dark">${hl(emp.role_type)}</span></td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${hl(emp.building)}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${hl(emp.line)}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${hl(emp.boss_name)}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${workingDays}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;"><span class="badge ${absentBadgeClass}">${absentDays}</span></td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;"><span class="badge ${unauthorizedBadgeClass}">${unauthorizedDays}</span></td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${emp.entrance_date || ''}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${emp.stop_date || '-'}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${tenureDisplay}</td>
                <td onclick="showEmployeeDetailModal('${emp.employee_id}')" style="cursor: pointer;">${statusBadges.join(' ')}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
    updateEmployeeCount(filteredEmployees.length);
    updateQuickStats(filteredEmployees);
}

function toggleEmployeeSelection(employeeId) {
    if (selectedEmployees.has(employeeId)) {
        selectedEmployees.delete(employeeId);
    } else {
        selectedEmployees.add(employeeId);
    }
    updateSelectionUI();
    renderEmployeeTable(filteredEmployees);
}

function filterEmployees(filter) {
    currentFilter = filter;

    // Update filter chip states (new design)
    // 필터 칩 상태 업데이트 (새 디자인)
    document.querySelectorAll('.filter-chip').forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-pressed', 'false');
    });

    // Also update legacy button states for compatibility
    // 호환성을 위한 레거시 버튼 상태도 업데이트
    document.querySelectorAll('.btn-group button').forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-pressed', 'false');
    });

    // Find and activate the correct filter chip
    // 올바른 필터 칩 찾아서 활성화
    const filterChip = document.querySelector(`.filter-chip[data-filter="${{filter}}"]`);
    if (filterChip) {{
        filterChip.classList.add('active');
        filterChip.setAttribute('aria-pressed', 'true');
    }}

    // Legacy button activation
    const activeBtn = document.getElementById(`filter${{filter.charAt(0).toUpperCase() + filter.slice(1)}}`);
    if (activeBtn) {{
        activeBtn.classList.add('active');
        activeBtn.setAttribute('aria-pressed', 'true');
    }}

    let filtered = employeeDetails;
    let filterName = filter; // For screen reader announcement / 스크린 리더 알림용

    switch(filter) {{
        case 'all': filtered = employeeDetails; filterName = 'all employees'; break;
        case 'active': filtered = employeeDetails.filter(e => e.is_active); filterName = 'active employees'; break;
        case 'hired': filtered = employeeDetails.filter(e => e.hired_this_month); filterName = 'new hires'; break;
        case 'resigned': filtered = employeeDetails.filter(e => e.resigned_this_month); filterName = 'resigned employees'; break;
        case 'perfect': filtered = employeeDetails.filter(e => e.perfect_attendance); filterName = 'perfect attendance'; break;
        case 'absent': filtered = employeeDetails.filter(e => e.absent_days > 0); filterName = 'employees with absences'; break;
        case 'unauthorized': filtered = employeeDetails.filter(e => e.has_unauthorized_absence); filterName = 'unauthorized absences'; break;
        case 'longterm': filtered = employeeDetails.filter(e => e.long_term); filterName = 'long-term employees'; break;
        case 'new60': filtered = employeeDetails.filter(e => e.under_60_days); filterName = 'employees under 60 days'; break;
        case 'pregnant': filtered = employeeDetails.filter(e => e.is_pregnant); filterName = 'pregnant employees'; break;
        // Bug Fix: Added long_absence and data_error cases
        // 버그 수정: long_absence와 data_error 케이스 추가
        case 'long_absence': filtered = employeeDetails.filter(e => e.absent_days >= 5); filterName = 'employees with 5+ absent days'; break;
        case 'data_error': filtered = employeeDetails.filter(e => e.has_data_error); filterName = 'employees with data errors'; break;
        // New: Turnover risk filter / 새로운: 이탈 위험 필터
        case 'turnover_risk':
            filtered = employeeDetails.filter(e => {{
                const risk = calculateTurnoverRisk(e);
                return risk.level === 'high' || risk.level === 'medium';
            }});
            filterName = 'turnover risk employees';
            break;
    }}

    // Update active filters bar / 활성 필터 바 업데이트
    updateActiveFiltersBar(filter);

    // Announce filter change to screen readers
    // 스크린 리더에 필터 변경 알림
    announceFilterChange(filterName, filtered.length);

    // P0 Fix: Save filter state to localStorage
    // P0 수정: 필터 상태를 localStorage에 저장
    savePreferencesToStorage();

    renderEmployeeTable(filtered);
}}

// Update active filters bar display
// 활성 필터 바 표시 업데이트
function updateActiveFiltersBar(filter) {{
    const activeFiltersBar = document.getElementById('activeFiltersBar');
    const activeFilterChips = document.getElementById('activeFilterChips');

    if (!activeFiltersBar || !activeFilterChips) return;

    if (filter === 'all') {{
        activeFiltersBar.classList.add('d-none');
        return;
    }}

    activeFiltersBar.classList.remove('d-none');

    // Get filter display name
    // 필터 표시 이름 가져오기
    const lang = localStorage.getItem('selectedLanguage') || 'ko';
    const filterNames = {{
        active: {{ ko: '재직자', en: 'Active', vi: 'Đang làm' }},
        hired: {{ ko: '신규입사', en: 'New Hires', vi: 'Mới' }},
        resigned: {{ ko: '퇴사자', en: 'Resigned', vi: 'Đã nghỉ' }},
        perfect: {{ ko: '개근', en: 'Perfect', vi: 'Đầy đủ' }},
        absent: {{ ko: '결근자', en: 'Absent', vi: 'Vắng' }},
        unauthorized: {{ ko: '무단결근', en: 'Unauthorized', vi: 'K.phép' }},
        longterm: {{ ko: '장기근속', en: 'Long-term', vi: 'Lâu năm' }},
        new60: {{ ko: '60일 미만', en: 'Under 60d', vi: '<60 ngày' }},
        pregnant: {{ ko: '임신', en: 'Pregnant', vi: 'Thai sản' }},
        turnover_risk: {{ ko: '이탈위험', en: 'At Risk', vi: 'Nguy cơ' }}
    }};

    const displayName = filterNames[filter] ? filterNames[filter][lang] : filter;

    activeFilterChips.innerHTML = `
        <span class="active-filter-tag">
            ${{displayName}}
            <span class="remove-filter" onclick="resetAllFilters()" title="Remove filter">×</span>
        </span>
    `;
}}

// Reset all filters to default
// 모든 필터를 기본값으로 초기화
function resetAllFilters() {{
    filterEmployees('all');
}}

// Announce filter changes for accessibility
// 접근성을 위한 필터 변경 알림
function announceFilterChange(filterName, count) {
    const announcement = document.createElement('div');
    announcement.className = 'visually-hidden';
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.textContent = `Showing ${count} ${filterName}`;
    document.body.appendChild(announcement);

    // Remove after announcement
    // 알림 후 제거
    setTimeout(() => announcement.remove(), 1500);
}

// Filter from Executive Summary - switches to Details tab and applies filter
// Executive Summary에서 필터 - Details 탭으로 전환 후 필터 적용
function filterEmployeeDetails(filterType) {
    // Switch to Details tab
    // Details 탭으로 전환
    const detailsTab = document.getElementById('details-tab');
    if (detailsTab) {
        const tab = new bootstrap.Tab(detailsTab);
        tab.show();
    }

    // Apply appropriate filter based on filterType
    // filterType에 따라 적절한 필터 적용
    // Bug Fix: Now using filterEmployees for consistent UI state
    // 버그 수정: 일관된 UI 상태를 위해 filterEmployees 사용
    setTimeout(() => {
        switch(filterType) {
            case 'long_absence':
                filterEmployees('long_absence');
                break;
            case 'unauthorized':
                filterEmployees('unauthorized');
                break;
            case 'data_error':
                filterEmployees('data_error');
                break;
            case 'active':
                filterEmployees('active');
                break;
            case 'resigned':
                filterEmployees('resigned');
                break;
            case 'perfect':
                filterEmployees('perfect');
                break;
            case 'absent':
                filterEmployees('absent');
                break;
            case 'longterm':
                filterEmployees('longterm');
                break;
            case 'new60':
                filterEmployees('new60');
                break;
            case 'pregnant':
                filterEmployees('pregnant');
                break;
            case 'hired':
                filterEmployees('hired');
                break;
            default:
                filterEmployees('all');
        }
    }, 300);
}

function updateFilterCounts() {{
    // Update count badges for each filter
    // 각 필터의 카운트 배지 업데이트
    const safeUpdate = (id, count) => {{
        const el = document.getElementById(id);
        if (el) el.textContent = count;
    }};

    safeUpdate('countAll', employeeDetails.length);
    safeUpdate('countActive', employeeDetails.filter(e => e.is_active).length);
    safeUpdate('countHired', employeeDetails.filter(e => e.hired_this_month).length);
    safeUpdate('countResigned', employeeDetails.filter(e => e.resigned_this_month).length);
    safeUpdate('countPerfect', employeeDetails.filter(e => e.perfect_attendance).length);
    safeUpdate('countAbsent', employeeDetails.filter(e => e.absent_days > 0).length);
    safeUpdate('countUnauthorized', employeeDetails.filter(e => e.has_unauthorized_absence).length);
    safeUpdate('countLongTerm', employeeDetails.filter(e => e.long_term).length);
    safeUpdate('countNew60', employeeDetails.filter(e => e.under_60_days).length);
    safeUpdate('countPregnant', employeeDetails.filter(e => e.is_pregnant).length);

    // New: Turnover risk count / 새로운: 이탈 위험 카운트
    const turnoverRiskCount = employeeDetails.filter(e => {{
        const risk = calculateTurnoverRisk(e);
        return risk.level === 'high' || risk.level === 'medium';
    }}).length;
    safeUpdate('countTurnoverRisk', turnoverRiskCount);
}}

// Current search term for highlighting
// 하이라이팅을 위한 현재 검색어
let currentSearchTerm = '';

// P1 Fix: Highlight matching text in search results
// P1 수정: 검색 결과에서 일치하는 텍스트 하이라이팅
function highlightText(text, searchTerm) {{
    if (!searchTerm || !text) return sanitizeHTML(String(text));
    const safeText = sanitizeHTML(String(text));
    const escapedTerm = searchTerm.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
    const regex = new RegExp(`(${{escapedTerm}})`, 'gi');
    return safeText.replace(regex, '<mark class="search-highlight">$1</mark>');
}}

function searchEmployees() {{
    // Search employees by multiple fields (ID, Name, Position, Type, Building, Line)
    // 여러 필드로 직원 검색 (사번, 이름, 직급, 유형, 건물, 라인)
    const searchTerm = document.getElementById('employeeSearch').value.toLowerCase();
    currentSearchTerm = searchTerm;

    // Save search preference
    // 검색 환경설정 저장
    savePreferencesToStorage();

    if (!searchTerm) {{
        renderEmployeeTable(employeeDetails);
        return;
    }}

    const filtered = employeeDetails.filter(emp => {{
        return (
            (emp.employee_id && emp.employee_id.toLowerCase().includes(searchTerm)) ||
            (emp.employee_name && emp.employee_name.toLowerCase().includes(searchTerm)) ||
            (emp.position && emp.position.toLowerCase().includes(searchTerm)) ||
            (emp.role_type && emp.role_type.toLowerCase().includes(searchTerm)) ||
            (emp.building && emp.building.toLowerCase().includes(searchTerm)) ||
            (emp.line && emp.line.toLowerCase().includes(searchTerm)) ||
            (emp.boss_name && emp.boss_name.toLowerCase().includes(searchTerm))
        );
    }});

    renderEmployeeTable(filtered);
}}

function sortTable(columnIndex, event) {
    // Check if Shift key is pressed for secondary sort
    // Shift 키가 눌렸는지 확인하여 2차 정렬 결정
    const isShiftClick = event && event.shiftKey;

    if (isShiftClick && currentSortColumn >= 0 && currentSortColumn !== columnIndex) {
        // Shift+click: Add/modify secondary sort
        // Shift+클릭: 2차 정렬 추가/수정
        if (secondarySortColumn === columnIndex) {
            // Toggle secondary sort direction
            secondarySortAsc = !secondarySortAsc;
        } else {
            // Set new secondary sort column
            secondarySortColumn = columnIndex;
            secondarySortAsc = true;
        }

        // Show multi-sort hint toast
        showMultiSortHint();
    } else {
        // Normal click: Primary sort
        // 일반 클릭: 1차 정렬
        if (currentSortColumn === columnIndex) {
            // Toggle sort direction if clicking same column
            currentSortAsc = !currentSortAsc;
        } else {
            // New primary sort column - reset secondary sort
            currentSortColumn = columnIndex;
            currentSortAsc = true;
            secondarySortColumn = -1;
            secondarySortAsc = true;
        }
    }

    // Re-render table with current filter applied (sorting happens in renderEmployeeTable)
    // 현재 필터 적용된 상태로 테이블 다시 렌더링 (정렬은 renderEmployeeTable에서 수행)
    filterEmployees(currentFilter);

    // Update sort indicators after rendering
    // 렌더링 후 정렬 표시 업데이트
    updateSortIndicators();

    // Save preferences to localStorage
    // localStorage에 환경설정 저장
    savePreferencesToStorage();
}

// Show hint for multi-sort feature
// 다중 정렬 기능 힌트 표시
function showMultiSortHint() {
    const existingHint = document.querySelector('.multi-sort-hint');
    if (existingHint) existingHint.remove();

    const hint = document.createElement('div');
    hint.className = 'multi-sort-hint';
    hint.innerHTML = `
        <div style="
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #343a40 0%, #495057 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            z-index: 9999;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 8px;
        ">
            <span style="font-size: 16px;">🔢</span>
            <span>다중 정렬 적용됨 | Multi-sort active</span>
            <span style="opacity: 0.7; font-size: 11px;">(일반 클릭으로 초기화)</span>
        </div>
    `;
    document.body.appendChild(hint);

    setTimeout(() => {
        hint.style.opacity = '0';
        hint.style.transition = 'opacity 0.3s';
        setTimeout(() => hint.remove(), 300);
    }, 2000);
}

function updateEmployeeCount(count) {
    const badge = document.getElementById('employeeCount');
    if (badge) {
        badge.textContent = `Total: ${count}`;
    }

    // Update export dropdown badges
    // 내보내기 드롭다운 배지 업데이트
    updateExportBadges();
}

function updateExportBadges() {
    // Update filtered count badge in export dropdown
    // 내보내기 드롭다운의 필터링된 개수 배지 업데이트
    const filteredBadge = document.getElementById('filteredCountBadge');
    const totalBadge = document.getElementById('totalCountBadge');

    if (filteredBadge) {
        const filteredCount = filteredEmployees ? filteredEmployees.length : 0;
        filteredBadge.textContent = filteredCount;
    }

    if (totalBadge) {
        const totalCount = employeeDetails ? employeeDetails.length : 0;
        totalBadge.textContent = totalCount;
    }
}

// P2-1: Calculate turnover risk score for an employee
// P2-1: 직원의 이직 위험 점수 계산
function calculateTurnoverRisk(emp) {
    if (!emp || !emp.is_active) return { score: 0, level: 'none', factors: [] };

    let score = 0;
    const factors = [];
    const tenureDays = emp.tenure_days || 0;
    const absentDays = emp.absent_days || 0;
    const unauthorizedDays = emp.unauthorized_absent_days || 0;

    // Factor 1: New employee (under 60 days) - 신입 직원 (60일 미만)
    if (tenureDays < 60) {
        score += 30;
        factors.push({ ko: '신입 (60일 미만)', en: 'New hire (<60 days)', weight: 30 });
    }

    // Factor 2: Post-assignment period (30-60 days) - 보직 후 기간 (30-60일)
    if (tenureDays >= 30 && tenureDays <= 60) {
        score += 20;
        factors.push({ ko: '보직 부여 기간', en: 'Post-assignment period', weight: 20 });
    }

    // Factor 3: Unauthorized absences - 무단결근
    if (unauthorizedDays > 0) {
        const uaScore = Math.min(unauthorizedDays * 15, 45);
        score += uaScore;
        factors.push({ ko: `무단결근 ${unauthorizedDays}일`, en: `${unauthorizedDays} unauthorized absences`, weight: uaScore });
    }

    // Factor 4: High absence rate - 높은 결근율
    if (absentDays >= 3) {
        const absScore = Math.min((absentDays - 2) * 10, 30);
        score += absScore;
        factors.push({ ko: `결근 ${absentDays}일`, en: `${absentDays} absent days`, weight: absScore });
    }

    // Factor 5: Short tenure with absences - 짧은 재직기간 + 결근
    if (tenureDays < 90 && absentDays > 0) {
        score += 15;
        factors.push({ ko: '단기 재직 + 결근', en: 'Short tenure + absences', weight: 15 });
    }

    // Determine risk level based on score
    // 점수에 따른 위험 수준 결정
    let level = 'low';
    if (score >= 70) level = 'critical';
    else if (score >= 50) level = 'high';
    else if (score >= 30) level = 'medium';

    return { score: Math.min(score, 100), level, factors };
}

// Get turnover risk badge HTML
// 이직 위험 배지 HTML 생성
function getTurnoverRiskBadge(emp, lang = 'ko') {
    const risk = calculateTurnoverRisk(emp);
    if (risk.level === 'none' || risk.level === 'low') return '';

    const badges = {
        critical: { class: 'bg-danger', icon: '🚨', ko: '위험', en: 'Critical' },
        high: { class: 'bg-warning text-dark', icon: '⚠️', ko: '주의', en: 'High' },
        medium: { class: 'bg-info', icon: 'ℹ️', ko: '관심', en: 'Medium' }
    };

    const badge = badges[risk.level];
    const tooltip = risk.factors.map(f => f[lang] || f.ko).join(', ');

    return `<span class="badge ${badge.class} badge-risk ms-1"
        title="${tooltip}"
        data-bs-toggle="tooltip"
        data-risk-score="${risk.score}">
        ${badge.icon} ${badge[lang] || badge.ko}
    </span>`;
}

function showEmployeeDetailModal(employeeId) {
    // Find employee in employeeDetails array
    const employee = employeeDetails.find(emp => emp.employee_id === employeeId || emp.employee_no === employeeId);

    if (!employee) {
        debugLog('Employee not found:', employeeId);
        return;
    }

    // Populate basic information
    document.getElementById('empDetailId').textContent = employee.employee_id || '-';
    document.getElementById('empDetailName').textContent = employee.employee_name || '-';
    document.getElementById('empDetailPosition').textContent = employee.position || '-';
    document.getElementById('empDetailType').textContent = employee.role_type || '-';
    document.getElementById('empDetailTeam').textContent = employee.team_name || employee.team || '-';
    document.getElementById('empDetailBuilding').textContent = employee.building || '-';
    document.getElementById('empDetailLine').textContent = employee.line || '-';
    document.getElementById('empDetailBoss').textContent = employee.boss_name || '-';
    document.getElementById('empDetailEntrance').textContent = employee.entrance_date || '-';

    // Calculate and display tenure
    const tenureDays = employee.tenure_days || 0;
    const tenureMonths = Math.floor(tenureDays / 30);
    const tenureYears = Math.floor(tenureDays / 365);
    let tenureDisplay = '-';
    if (tenureDays > 0) {
        if (tenureYears > 0) {
            tenureDisplay = `${tenureDays}일 (${tenureYears}년 ${tenureMonths % 12}개월)`;
        } else {
            tenureDisplay = `${tenureDays}일 (${tenureMonths}개월)`;
        }
    }
    document.getElementById('empDetailTenure').textContent = tenureDisplay;

    // Populate status badges
    const statusBadges = [];
    if (employee.is_active) {
        statusBadges.push('<span class="badge bg-success badge-status">재직</span>');
    } else {
        statusBadges.push('<span class="badge bg-secondary badge-status">퇴사</span>');
    }
    if (employee.hired_this_month) {
        statusBadges.push('<span class="badge bg-info badge-status">신입</span>');
    }
    if (employee.resigned_this_month) {
        statusBadges.push('<span class="badge bg-danger badge-status">퇴사</span>');
    }
    if (employee.perfect_attendance) {
        statusBadges.push('<span class="badge bg-success badge-status">개근</span>');
    }
    if (employee.long_term) {
        statusBadges.push('<span class="badge bg-warning badge-status">장기</span>');
    }
    if (employee.is_pregnant) {
        statusBadges.push('<span class="badge bg-warning badge-status">임신</span>');
    }
    if (employee.under_60_days) {
        statusBadges.push('<span class="badge bg-info badge-status">60일 미만</span>');
    }
    document.getElementById('empDetailStatusBadges').innerHTML = statusBadges.join(' ');

    // Populate attendance information
    const workingDays = employee.working_days || 0;
    const absentDays = employee.absent_days || 0;
    const attendanceRate = workingDays > 0 ? ((workingDays - absentDays) / workingDays * 100).toFixed(1) : 0;

    document.getElementById('empDetailWorkingDays').textContent = workingDays;
    document.getElementById('empDetailAbsentDays').textContent = absentDays;
    document.getElementById('empDetailAttendanceRate').textContent = attendanceRate + '%';

    // Set attendance rate color based on value
    const attendanceRateEl = document.getElementById('empDetailAttendanceRate');
    if (attendanceRate >= 95) {
        attendanceRateEl.className = 'fs-4 fw-bold text-success';
    } else if (attendanceRate >= 85) {
        attendanceRateEl.className = 'fs-4 fw-bold text-warning';
    } else {
        attendanceRateEl.className = 'fs-4 fw-bold text-danger';
    }

    // Show unauthorized absence status
    const unauthorizedEl = document.getElementById('empDetailUnauthorized');
    if (employee.has_unauthorized_absence) {
        unauthorizedEl.textContent = '있음';
        unauthorizedEl.className = 'fs-4 fw-bold text-danger';
    } else {
        unauthorizedEl.textContent = '없음';
        unauthorizedEl.className = 'fs-4 fw-bold text-success';
    }

    // Show additional attendance info
    let additionalInfo = '<div class="alert alert-light mb-0">';
    if (employee.perfect_attendance) {
        additionalInfo += '<p class="mb-1"><strong>✅ 개근:</strong> 해당 월에 결근 없음</p>';
    }
    if (employee.has_unauthorized_absence) {
        additionalInfo += '<p class="mb-1"><strong>⚠️ 무단결근:</strong> 무단결근 기록이 있습니다</p>';
    }
    if (absentDays > 0 && !employee.has_unauthorized_absence) {
        additionalInfo += '<p class="mb-1"><strong>📋 결근:</strong> 사유 있는 결근</p>';
    }
    if (workingDays === 0) {
        additionalInfo += '<p class="mb-1"><strong>ℹ️ 정보 없음:</strong> 해당 월 출결 데이터가 없습니다</p>';
    }
    additionalInfo += '</div>';
    document.getElementById('empDetailAttendanceInfo').innerHTML = additionalInfo;

    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('employeeDetailModal'));
    modal.show();
}

// ============================================
// New Enhanced Functions
// ============================================

function applyFilters() {
    currentPage = 1;
    filterEmployees(currentFilter);
}

// Switch to Employee Details tab and filter by team
// 직원 상세 탭으로 이동하고 팀별로 필터링
function switchToTeamAnalysis(teamName) {
    // Switch to Employee Details tab
    // 직원 상세 탭으로 전환
    const employeeTab = document.querySelector('#employeeDetailsTab');
    const overviewTab = document.querySelector('#overviewTab');
    const trendsTab = document.querySelector('#trendsTab');

    if (employeeTab) {
        // Deactivate other tabs
        if (overviewTab) {
            overviewTab.classList.remove('active');
            document.getElementById('overview')?.classList.remove('show', 'active');
        }
        if (trendsTab) {
            trendsTab.classList.remove('active');
            document.getElementById('trends')?.classList.remove('show', 'active');
        }

        // Activate Employee Details tab
        employeeTab.classList.add('active');
        const employeePane = document.getElementById('employeeDetails');
        if (employeePane) {
            employeePane.classList.add('show', 'active');
        }
    }

    // Apply team filter
    // 팀 필터 적용
    const teamSelect = document.getElementById('filterTeam');
    if (teamSelect) {
        // Find matching option
        for (let option of teamSelect.options) {
            if (option.value === teamName || option.text === teamName) {
                teamSelect.value = option.value;
                break;
            }
        }
    }

    // Apply filters and show results
    // 필터 적용 및 결과 표시
    applyFilters();

    // Scroll to the table
    // 테이블로 스크롤
    setTimeout(() => {
        const tableContainer = document.querySelector('.table-responsive');
        if (tableContainer) {
            tableContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100);

    // Show toast notification
    // 토스트 알림 표시
    showTeamFilterToast(teamName);
}

// Show toast when team filter is applied
// 팀 필터 적용 시 토스트 표시
function showTeamFilterToast(teamName) {
    const existingToast = document.querySelector('.team-filter-toast');
    if (existingToast) existingToast.remove();

    const toast = document.createElement('div');
    toast.className = 'team-filter-toast';
    toast.innerHTML = `
        <div style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideInRight 0.3s ease-out;
        ">
            <span style="font-size: 18px;">👥</span>
            <div>
                <div style="font-weight: 600; font-size: 13px;">${teamName}</div>
                <div style="font-size: 11px; opacity: 0.9;">팀 필터가 적용되었습니다</div>
            </div>
        </div>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function handleSearchInput() {
    clearTimeout(searchTimeout);

    // Show/hide clear button based on input
    // 입력에 따라 지우기 버튼 표시/숨기기
    const searchInput = document.getElementById('employeeSearch');
    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) {
        clearBtn.style.display = searchInput.value.length > 0 ? 'block' : 'none';
    }

    searchTimeout = setTimeout(() => {
        searchEmployees();

        // Announce search results to screen readers
        // 스크린 리더에 검색 결과 알림
        const resultCount = document.getElementById('searchResultCount');
        if (resultCount && filteredEmployees) {
            resultCount.textContent = `${filteredEmployees.length} employees found`;
        }
    }, 300); // Debounce 300ms
}

// Clear search and reset
// 검색 지우기 및 초기화
function clearSearch() {
    const searchInput = document.getElementById('employeeSearch');
    const clearBtn = document.getElementById('clearSearchBtn');

    if (searchInput) {
        searchInput.value = '';
        currentSearchTerm = '';
    }
    if (clearBtn) {
        clearBtn.style.display = 'none';
    }

    // Trigger filter refresh
    // 필터 새로고침 트리거
    searchEmployees();
    savePreferencesToStorage();
}

function toggleColumn(colIndex) {
    columnVisibility[colIndex] = !columnVisibility[colIndex];
    const table = document.getElementById('employeeTable');
    const headers = table.querySelectorAll('thead th');
    const rows = table.querySelectorAll('tbody tr');

    // +1 to account for checkbox column
    const actualColIndex = colIndex + 1;

    if (columnVisibility[colIndex]) {
        headers[actualColIndex]?.classList.remove('column-hidden');
        rows.forEach(row => {
            row.querySelectorAll('td')[actualColIndex]?.classList.remove('column-hidden');
        });
    } else {
        headers[actualColIndex]?.classList.add('column-hidden');
        rows.forEach(row => {
            row.querySelectorAll('td')[actualColIndex]?.classList.add('column-hidden');
        });
    }

    // Save to localStorage
    // localStorage에 저장
    savePreferencesToStorage();
}

// Toggle all columns visibility
// 모든 컬럼 표시/숨김 토글
function toggleAllColumns(show) {
    const table = document.getElementById('employeeTable');
    const headers = table.querySelectorAll('thead th');
    const rows = table.querySelectorAll('tbody tr');
    const checkboxes = document.querySelectorAll('#columnToggleMenu input[type="checkbox"]');

    // Update all column visibility
    // 모든 컬럼 표시 상태 업데이트
    for (let i = 0; i < columnVisibility.length; i++) {
        columnVisibility[i] = show;
        const actualColIndex = i + 1; // +1 for checkbox column

        if (show) {
            headers[actualColIndex]?.classList.remove('column-hidden');
            rows.forEach(row => {
                row.querySelectorAll('td')[actualColIndex]?.classList.remove('column-hidden');
            });
        } else {
            headers[actualColIndex]?.classList.add('column-hidden');
            rows.forEach(row => {
                row.querySelectorAll('td')[actualColIndex]?.classList.add('column-hidden');
            });
        }
    }

    // Update checkboxes
    // 체크박스 상태 업데이트
    checkboxes.forEach(cb => {
        cb.checked = show;
    });

    savePreferencesToStorage();
}

// Reset column visibility to default (all visible)
// 컬럼 표시 상태를 기본값(모두 표시)으로 초기화
function resetColumnVisibility() {
    toggleAllColumns(true);
}

// Save preferences to localStorage
// localStorage에 환경설정 저장
function savePreferencesToStorage() {{
    try {{
        const searchInput = document.getElementById('employeeSearch');
        const prefs = {{
            columnVisibility: columnVisibility,
            sortColumn: currentSortColumn,
            sortAsc: currentSortAsc,
            pageSize: pageSize,
            language: currentLanguage,
            // P0 Fix: Preserve filter state across sessions
            // P0 수정: 세션 간 필터 상태 유지
            currentFilter: currentFilter,
            searchTerm: searchInput ? searchInput.value : '',
            // Preserve selection across pagination
            // 페이지네이션 간 선택 유지
            selectedEmployees: Array.from(selectedEmployees)
        }};
        localStorage.setItem('hrDashboardPrefs', JSON.stringify(prefs));
    }} catch (e) {{
        console.warn('Failed to save preferences to localStorage:', e);
    }}
}}

// Load preferences from localStorage
// localStorage에서 환경설정 로드
function loadPreferencesFromStorage() {{
    try {{
        const saved = localStorage.getItem('hrDashboardPrefs');
        if (saved) {{
            const prefs = JSON.parse(saved);

            // Restore column visibility
            // 컬럼 표시 복원
            if (prefs.columnVisibility && Array.isArray(prefs.columnVisibility)) {{
                columnVisibility = prefs.columnVisibility;
                applyColumnVisibility();
            }}

            // Restore sort settings
            // 정렬 설정 복원
            if (typeof prefs.sortColumn === 'number') {{
                currentSortColumn = prefs.sortColumn;
                currentSortAsc = prefs.sortAsc !== false;
                updateSortIndicators();
            }}

            // Restore page size
            // 페이지 크기 복원
            if (typeof prefs.pageSize === 'number') {{
                pageSize = prefs.pageSize;
                const pageSizeSelect = document.getElementById('pageSizeSelect');
                if (pageSizeSelect) {{
                    pageSizeSelect.value = pageSize.toString();
                }}
            }}

            // Restore language (if different from default)
            // 언어 복원 (기본값과 다른 경우)
            if (prefs.language && ['ko', 'en', 'vi'].includes(prefs.language)) {{
                currentLanguage = prefs.language;
                updateLanguageSelector();
            }}

            // P0 Fix: Restore filter state
            // P0 수정: 필터 상태 복원
            if (prefs.currentFilter && typeof prefs.currentFilter === 'string') {{
                currentFilter = prefs.currentFilter;
                // Delay filter application to ensure DOM is ready
                // DOM이 준비될 때까지 필터 적용 지연
                setTimeout(() => {{
                    filterEmployees(currentFilter);
                }}, 100);
            }}

            // Restore search term
            // 검색어 복원
            if (prefs.searchTerm && typeof prefs.searchTerm === 'string') {{
                const searchInput = document.getElementById('employeeSearch');
                if (searchInput) {{
                    searchInput.value = prefs.searchTerm;
                    if (prefs.searchTerm.length > 0) {{
                        setTimeout(() => searchEmployees(), 150);
                    }}
                }}
            }}

            // Restore selected employees
            // 선택된 직원 복원
            if (prefs.selectedEmployees && Array.isArray(prefs.selectedEmployees)) {{
                selectedEmployees = new Set(prefs.selectedEmployees);
                updateSelectionUI();
            }}
        }}
    }} catch (e) {{
        console.warn('Failed to load preferences from localStorage:', e);
    }}
}}

// Apply saved column visibility
// 저장된 컬럼 표시 적용
function applyColumnVisibility() {{
    const table = document.getElementById('employeeTable');
    if (!table) return;

    const headers = table.querySelectorAll('thead th');
    const rows = table.querySelectorAll('tbody tr');

    columnVisibility.forEach((visible, colIndex) => {{
        const actualColIndex = colIndex + 1; // +1 for checkbox column

        // Update header
        if (headers[actualColIndex]) {{
            if (visible) {{
                headers[actualColIndex].classList.remove('column-hidden');
            }} else {{
                headers[actualColIndex].classList.add('column-hidden');
            }}
        }}

        // Update rows
        rows.forEach(row => {{
            const td = row.querySelectorAll('td')[actualColIndex];
            if (td) {{
                if (visible) {{
                    td.classList.remove('column-hidden');
                }} else {{
                    td.classList.add('column-hidden');
                }}
            }}
        }});

        // Update dropdown checkbox
        const checkbox = document.querySelector(`input[data-column="${{colIndex}}"]`);
        if (checkbox) {{
            checkbox.checked = visible;
        }}
    }});
}}

// Update language selector to match loaded preference
// 로드된 환경설정에 맞게 언어 선택기 업데이트
function updateLanguageSelector() {{
    const langBtn = document.getElementById('langDropdownBtn');
    const langNames = {{ ko: '한국어', en: 'English', vi: 'Tiếng Việt' }};
    if (langBtn && langNames[currentLanguage]) {{
        langBtn.textContent = langNames[currentLanguage];
    }}
}}

function changePage(direction) {
    currentPage += direction;
    if (currentPage < 1) currentPage = 1;
    applyFilters();
}

function changePageSize() {
    const select = document.getElementById('pageSizeSelect');
    pageSize = parseInt(select.value);
    currentPage = 1;
    applyFilters();
}

function toggleSelectAll() {
    const headerCheckbox = document.getElementById('headerCheckbox');
    const checkboxes = document.querySelectorAll('.employee-checkbox');

    if (headerCheckbox.checked) {
        checkboxes.forEach(cb => {
            cb.checked = true;
            selectedEmployees.add(cb.value);
        });
    } else {
        checkboxes.forEach(cb => {
            cb.checked = false;
        });
        selectedEmployees.clear();
    }

    updateSelectionUI();
}

function updateSelectionUI() {
    const count = selectedEmployees.size;
    const countElement = document.getElementById('selectedCount');
    const langLabel = countElement.querySelector('.lang-label');

    // Update count text based on current language
    // 현재 언어에 따라 선택 수 텍스트 업데이트
    if (langLabel) {
        langLabel.setAttribute('data-ko', `${count} 선택됨`);
        langLabel.setAttribute('data-en', `${count} selected`);
        langLabel.setAttribute('data-vi', `Đã chọn ${count}`);
        langLabel.textContent = currentLanguage === 'en' ? `${count} selected` :
                                currentLanguage === 'vi' ? `Đã chọn ${count}` : `${count} 선택됨`;
    } else {
        countElement.textContent = `${count} 선택됨`;
    }

    document.getElementById('exportSelectedBtn').disabled = count === 0;
    document.getElementById('printSelectedBtn').disabled = count === 0;
}

function exportFiltered(format) {
    // Export only currently filtered/visible employees
    // 현재 필터링/표시된 직원만 내보내기
    debugLog(`Exporting filtered data (${filteredEmployees.length} employees) as ${format}`);

    if (!filteredEmployees || filteredEmployees.length === 0) {
        const msg = currentLanguage === 'ko' ? '내보낼 데이터가 없습니다.' :
                    currentLanguage === 'vi' ? 'Không có dữ liệu để xuất.' :
                    'No data to export.';
        alert(msg);
        return;
    }

    if (format === 'csv') exportToCSV(filteredEmployees, 'HR_Filtered');
    if (format === 'json') exportToJSON(filteredEmployees, 'HR_Filtered');
    if (format === 'pdf') alert('PDF export feature coming soon!');
}

function exportSelected(format) {
    // Stub - export selected rows only
    debugLog(`Exporting ${selectedEmployees.size} selected employees as ${format}`);
}

function printSelected() {
    // Stub - print selected employees
    debugLog(`Printing ${selectedEmployees.size} selected employees`);
}

function updateQuickStats(employees) {
    if (!employees || !employees.length) return;

    const active = employees.filter(e => e.is_active).length;
    const resigned = employees.filter(e => e.resigned_this_month).length;
    const absentCount = employees.filter(e => (e.absent_days || 0) > 0).length;
    const unauthorizedCount = employees.filter(e => e.has_unauthorized_absence).length;

    document.getElementById('statsShowing').textContent = employees.length;
    document.getElementById('statsActiveResigned').textContent = `${active}/${resigned}`;
    document.getElementById('statsAbsentCount').textContent = `${absentCount}명`;
    document.getElementById('statsUnauthorizedCount').textContent = `${unauthorizedCount}명`;
}

function populateTeamFilter() {
    const select = document.getElementById('teamFilter');
    if (!select) return;

    const teams = [...new Set(employeeDetails.map(e => e.team || e.team_name).filter(t => t))].sort();

    teams.forEach(team => {
        const option = document.createElement('option');
        option.value = team;
        option.textContent = team;
        select.appendChild(option);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Load saved preferences from localStorage first
    // localStorage에서 저장된 환경설정 먼저 로드
    loadPreferencesFromStorage();

    const detailsTab = document.getElementById('details-tab');
    if (detailsTab) {
        detailsTab.addEventListener('shown.bs.tab', function() {
            renderEmployeeTable();
            updateFilterCounts();
            populateTeamFilter();
            updateQuickStats(employeeDetails);
            // Apply column visibility after table renders
            // 테이블 렌더링 후 컬럼 표시 적용
            setTimeout(applyColumnVisibility, 100);
        });
    }

    // ============================================
    // Phase 3: Performance Optimization & Mobile Support Initialization
    // ============================================

    debugLog('🚀 Initializing Phase 3 optimizations...');

    // 1. Initialize Lazy Chart Loading with Intersection Observer
    initLazyChartLoading();

    // 2. Initialize Organization Chart
    const orgTab = document.getElementById('org-tab');
    if (orgTab) {{
        orgTab.addEventListener('shown.bs.tab', function() {{
            if (currentOrgView === '') {{
                currentOrgView = 'network';
                initOrgChart();
            }}
        }});
    }}

    // 3. Add window resize listener with debounce for responsive charts
    window.addEventListener('resize', handleChartResize);

    // 3. Modal close event listeners to destroy charts and free memory
    document.querySelectorAll('.modal').forEach(modalEl => {{
        modalEl.addEventListener('hidden.bs.modal', function() {{
            const modalId = this.id;
            const modalNum = parseInt(modalId.replace(/\\D/g, '')); // Extract number from ID
            if (modalNum) {{
                destroyModalCharts(modalNum);
                debugLog(`🗑️ Cleaned up charts for modal ${{modalNum}}`);
            }}
        }});
    }});

    // 4. Touch event optimization for mobile devices
    if ('ontouchstart' in window) {{
        debugLog('📱 Touch device detected - enabling mobile optimizations');

        // Add touch event listeners to KPI cards for better mobile UX
        document.querySelectorAll('.kpi-card').forEach(card => {{
            card.addEventListener('touchstart', function() {{
                this.style.transform = 'scale(0.98)';
            }}, {{ passive: true }});

            card.addEventListener('touchend', function() {{
                this.style.transform = 'scale(1)';
            }}, {{ passive: true }});
        }});

        // Enable smooth scrolling for tables on mobile
        document.querySelectorAll('.table-responsive').forEach(table => {{
            table.style.webkitOverflowScrolling = 'touch';
        }});

        // Add touch feedback to modal chart containers
        document.querySelectorAll('.modal-chart-container').forEach(container => {{
            container.addEventListener('touchstart', function() {{
                this.style.opacity = '0.95';
            }}, {{ passive: true }});

            container.addEventListener('touchend', function() {{
                this.style.opacity = '1';
            }}, {{ passive: true }});
        }});
    }}

    // 5. Prevent chart canvas text selection on mobile
    document.querySelectorAll('canvas').forEach(canvas => {{
        canvas.style.webkitUserSelect = 'none';
        canvas.style.userSelect = 'none';
        canvas.style.webkitTouchCallout = 'none';
    }});

    // 6. Log device and viewport info for debugging
    debugLog('📐 Viewport:', {{
        width: window.innerWidth,
        height: window.innerHeight,
        devicePixelRatio: window.devicePixelRatio,
        isMobile: window.innerWidth < 768,
        isTablet: window.innerWidth >= 768 && window.innerWidth < 1024
    }});

    // 7. Performance monitoring
    if (window.performance && window.performance.memory) {{
        debugLog('💾 Memory usage:', {{
            usedJSHeapSize: (window.performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
            totalJSHeapSize: (window.performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB'
        }});
    }}

    debugLog('✅ Phase 3 optimizations initialized successfully!');
});

// ============================================
// Export Functions
// ============================================

function exportToCSV(data = null, filenamePrefix = 'HR_Employees') {{
    // Use filtered data if provided, otherwise use all employees
    // 제공된 경우 필터링된 데이터 사용, 그렇지 않으면 전체 직원 사용
    const exportData = data || employeeDetails;
    const suffix = data ? '_filtered' : '';
    const filename = `${{filenamePrefix}}${{suffix}}_${{targetMonth}}.csv`;
    const headers = ['사번,이름,직급,유형,팀,입사일,퇴사일,재직기간(일),출근일,결근일,출근률,상태'];

    const rows = exportData.map(emp => {{
        const status = [
            emp.is_active ? '재직' : '퇴사',
            emp.hired_this_month ? '신입' : '',
            emp.perfect_attendance ? '개근' : '',
            emp.long_term ? '장기' : ''
        ].filter(s => s).join('|');

        return [
            emp.employee_id || '',
            emp.employee_name || '',
            emp.position || '',
            emp.role_type || '',
            emp.team_name || '',
            emp.entrance_date || '',
            emp.stop_date || '',
            emp.tenure_days || '0',
            emp.actual_working_days || '0',
            emp.absent_days || '0',
            emp.attendance_rate ? `${{emp.attendance_rate.toFixed(1)}}%` : '',
            status
        ].map(field => `"${{field}}"`).join(',');
    }});

    const csv = headers.concat(rows).join('\\n');
    downloadFile(csv, filename, 'text/csv;charset=utf-8;');

    // Show download toast notification
    // 다운로드 토스트 알림 표시
    showDownloadToast(filename, exportData.length);

    debugLog(`✅ Exported ${{exportData.length}} employees to CSV`);
}}

function exportToJSON(data = null, filenamePrefix = 'HR_Employees') {{
    // Use filtered data if provided, otherwise use all employees
    // 제공된 경우 필터링된 데이터 사용, 그렇지 않으면 전체 직원 사용
    const exportData = data || employeeDetails;
    const suffix = data ? '_filtered' : '';
    const filename = `${{filenamePrefix}}${{suffix}}_${{targetMonth}}.json`;
    const json = JSON.stringify(exportData, null, 2);
    downloadFile(json, filename, 'application/json');

    // Show download toast notification
    // 다운로드 토스트 알림 표시
    showDownloadToast(filename, exportData.length);

    debugLog(`✅ Exported ${{exportData.length}} employees to JSON`);
}}

// Export only the currently filtered and visible data
// 현재 필터링되어 표시된 데이터만 내보내기
function exportFilteredData(format) {{
    if (!filteredEmployees || filteredEmployees.length === 0) {{
        alert(currentLanguage === 'ko' ? '내보낼 데이터가 없습니다. 필터를 확인하세요.' :
              currentLanguage === 'vi' ? 'Không có dữ liệu để xuất. Vui lòng kiểm tra bộ lọc.' :
              'No data to export. Please check your filters.');
        return;
    }}

    if (format === 'csv') {{
        exportToCSV(filteredEmployees, 'HR_Filtered');
    }} else if (format === 'json') {{
        exportToJSON(filteredEmployees, 'HR_Filtered');
    }}
}}

// Show download toast notification
// 다운로드 토스트 알림 표시
function showDownloadToast(filename, count) {{
    const messages = {{
        ko: `${{count}}명의 직원 데이터가 다운로드되었습니다.`,
        en: `Downloaded data for ${{count}} employees.`,
        vi: `Đã tải dữ liệu của ${{count}} nhân viên.`
    }};
    const message = messages[currentLanguage] || messages.en;

    // Create toast if it doesn't exist
    let toast = document.getElementById('downloadToast');
    if (!toast) {{
        toast = document.createElement('div');
        toast.id = 'downloadToast';
        toast.className = 'download-toast';
        toast.innerHTML = `
            <div class="download-toast-icon">📥</div>
            <div class="download-toast-content">
                <div class="download-toast-message"></div>
                <div class="download-toast-filename"></div>
            </div>
        `;
        document.body.appendChild(toast);
    }}

    toast.querySelector('.download-toast-message').textContent = message;
    toast.querySelector('.download-toast-filename').textContent = filename;

    // Show toast
    toast.classList.add('show');

    // Hide after 3 seconds
    setTimeout(() => {{
        toast.classList.remove('show');
    }}, 3000);
}}

function exportMetricsToJSON() {
    const filename = `HR_Metrics_${targetMonth}.json`;

    const exportData = {
        target_month: targetMonth,
        available_months: availableMonths,
        month_labels: monthLabels,
        metrics: monthlyMetrics,
        generated_at: new Date().toISOString()
    };

    const json = JSON.stringify(exportData, null, 2);
    downloadFile(json, filename, 'application/json');

    debugLog(`✅ Exported metrics for ${availableMonths.length} months to JSON`);
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
}

// ============================================
// Organization Chart Functions
// ============================================

let currentOrgView = 'network';
let orgNetworkChart = null;

// Initialize Organization Chart
function initOrgChart() {{
    calculateOrgStats();
    renderOrgNetworkChart();
}}

// Calculate organization statistics
function calculateOrgStats() {{
    const allEmployees = employeeDetails || [];

    // Count positions
    const positions = new Set(allEmployees.map(e => e.position_1st).filter(p => p));
    document.getElementById('totalPositionsCount').textContent = positions.size;

    // Count departments (Position 2nd)
    const departments = new Set(allEmployees.map(e => e.position_2nd).filter(p => p));
    document.getElementById('totalDepartmentsCount').textContent = departments.size;

    // Count managers (employees with subordinates)
    const managers = hierarchyData ? countManagers(hierarchyData) : 0;
    document.getElementById('totalManagersCount').textContent = managers;

    // Calculate average team size
    const avgSize = departments.size > 0 ? Math.round(allEmployees.length / departments.size) : 0;
    document.getElementById('avgTeamSize').textContent = avgSize;
}}

function countManagers(nodes) {{
    let count = 0;
    nodes.forEach(node => {{
        if (node.children && node.children.length > 0) {{
            count++;
            count += countManagers(node.children);
        }}
    }});
    return count;
}}

function setOrgChartView(viewType) {{
    currentOrgView = viewType;

    // Update button states
    ['viewNetwork', 'viewHierarchy', 'viewStats'].forEach(id => {{
        document.getElementById(id).classList.remove('active');
    }});
    document.getElementById('view' + viewType.charAt(0).toUpperCase() + viewType.slice(1)).classList.add('active');

    // Show/hide views
    document.getElementById('orgChartNetwork').style.display = viewType === 'network' ? 'block' : 'none';
    document.getElementById('orgChartHierarchy').style.display = viewType === 'hierarchy' ? 'block' : 'none';
    document.getElementById('orgChartStats').style.display = viewType === 'stats' ? 'block' : 'none';

    // Render appropriate view
    if (viewType === 'network') {{
        renderOrgNetworkChart();
    }} else if (viewType === 'hierarchy') {{
        renderOrgHierarchyTree();
    }} else if (viewType === 'stats') {{
        renderOrgStatsCharts();
    }}
}}

// Network Chart Rendering
function renderOrgNetworkChart() {{
    const container = document.getElementById('orgNetworkChart');
    if (!container) return;

    container.innerHTML = '';

    const allEmployees = employeeDetails || [];
    if (allEmployees.length === 0) {{
        container.innerHTML = '<p class="text-muted text-center">데이터가 없습니다.</p>';
        return;
    }}

    // Build nodes and links from employee data
    const nodes = allEmployees.map(emp => ({{
        id: emp.id_no,
        name: emp.name || '미정',
        position: emp.position_1st || '직급 미정',
        department: emp.position_2nd || '부서 미정',
        is_manager: (emp.boss_id === null || emp.boss_id === '') && allEmployees.some(e => e.boss_id === emp.id_no)
    }}));

    const links = allEmployees
        .filter(emp => emp.boss_id && allEmployees.find(e => e.id_no === emp.boss_id))
        .map(emp => ({{
            source: emp.boss_id,
            target: emp.id_no
        }}));

    // D3.js force-directed graph
    const width = container.offsetWidth || 800;
    const height = 600;

    const svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));

    // Links
    const link = svg.append('g')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 2);

    // Nodes
    const node = svg.append('g')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    node.append('circle')
        .attr('r', d => d.is_manager ? 15 : 10)
        .attr('fill', d => d.is_manager ? '#667eea' : '#4ECDC4')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);

    node.append('text')
        .text(d => d.name)
        .attr('x', 0)
        .attr('y', -20)
        .attr('text-anchor', 'middle')
        .style('font-size', '11px')
        .style('font-weight', 'bold')
        .style('fill', '#333');

    node.append('title')
        .text(d => `${{d.name}}\\n${{d.position}}\\n${{d.department}}`);

    simulation.on('tick', () => {{
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
    }});

    function dragstarted(event, d) {{
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }}

    function dragged(event, d) {{
        d.fx = event.x;
        d.fy = event.y;
    }}

    function dragended(event, d) {{
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }}
}}

function filterOrgNetwork() {{
    const filterValue = document.getElementById('orgNetworkFilter').value;
    // Re-render with filter (simplified - just re-render for now)
    renderOrgNetworkChart();
}}

// Hierarchy Tree Rendering
function renderOrgHierarchyTree() {{
    const container = document.getElementById('orgHierarchyTree');
    if (!container) return;

    container.innerHTML = '';

    if (!hierarchyData || hierarchyData.length === 0) {{
        container.innerHTML = '<p class="text-muted text-center">조직 계층 데이터가 없습니다.</p>';
        return;
    }}

    // Render each root node
    hierarchyData.forEach(rootNode => {{
        container.appendChild(createHierarchyNode(rootNode, 0));
    }});
}}

function createHierarchyNode(node, level) {{
    const nodeDiv = document.createElement('div');
    nodeDiv.className = 'hierarchy-node';
    nodeDiv.style.marginLeft = (level * 30) + 'px';

    const hasChildren = node.children && node.children.length > 0;
    const teamSize = countTeamMembers(node);

    nodeDiv.innerHTML = `
        <div class="hierarchy-node-card" onclick="toggleHierarchyNode(this)">
            <div class="d-flex align-items-center">
                ${{hasChildren ? '<i class="fas fa-chevron-right me-2 toggle-icon"></i>' : '<i class="fas fa-user me-2"></i>'}}
                <div class="flex-grow-1">
                    <strong>${{node.name || '미정'}}</strong>
                    <small class="text-muted ms-2">${{node.position || '직급 미정'}}</small>
                </div>
                ${{hasChildren ? `<span class="badge bg-primary">${{teamSize}}명</span>` : ''}}
            </div>
        </div>
    `;

    if (hasChildren) {{
        const childrenDiv = document.createElement('div');
        childrenDiv.className = 'hierarchy-children';
        childrenDiv.style.display = 'none';

        node.children.forEach(child => {{
            childrenDiv.appendChild(createHierarchyNode(child, level + 1));
        }});

        nodeDiv.appendChild(childrenDiv);
    }}

    return nodeDiv;
}}

function toggleHierarchyNode(element) {{
    const childrenDiv = element.parentElement.querySelector('.hierarchy-children');
    const icon = element.querySelector('.toggle-icon');

    if (childrenDiv) {{
        const isHidden = childrenDiv.style.display === 'none';
        childrenDiv.style.display = isHidden ? 'block' : 'none';
        icon.className = isHidden ? 'fas fa-chevron-down me-2 toggle-icon' : 'fas fa-chevron-right me-2 toggle-icon';
    }}
}}

function countTeamMembers(node) {{
    let count = 1;
    if (node.children) {{
        node.children.forEach(child => {{
            count += countTeamMembers(child);
        }});
    }}
    return count;
}}

// Statistics Charts Rendering
function renderOrgStatsCharts() {{
    renderPositionDistChart();
    renderDepartmentHeadcountChart();
    renderManagerTable();
}}

function renderPositionDistChart() {{
    const canvas = document.getElementById('positionDistChart');
    if (!canvas) return;

    const allEmployees = employeeDetails || [];
    const positionCounts = {{}};

    allEmployees.forEach(emp => {{
        const pos = emp.position_1st || '미정';
        positionCounts[pos] = (positionCounts[pos] || 0) + 1;
    }});

    const sortedPositions = Object.entries(positionCounts)
        .sort((a, b) => b[1] - a[1]);

    new Chart(canvas, {{
        type: 'bar',
        data: {{
            labels: sortedPositions.map(p => p[0]),
            datasets: [{{
                label: '인원 수',
                data: sortedPositions.map(p => p[1]),
                backgroundColor: '#667eea',
                borderColor: '#764ba2',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                title: {{
                    display: true,
                    text: '직급별 인원 분포'
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    ticks: {{ stepSize: 1 }}
                }}
            }}
        }}
    }});
}}

function renderDepartmentHeadcountChart() {{
    const canvas = document.getElementById('deptHeadcountChart');
    if (!canvas) return;

    const allEmployees = employeeDetails || [];
    const deptCounts = {{}};

    allEmployees.forEach(emp => {{
        const dept = emp.position_2nd || '미정';
        deptCounts[dept] = (deptCounts[dept] || 0) + 1;
    }});

    const sortedDepts = Object.entries(deptCounts)
        .sort((a, b) => b[1] - a[1]);

    new Chart(canvas, {{
        type: 'horizontalBar',
        data: {{
            labels: sortedDepts.map(d => d[0]),
            datasets: [{{
                label: '인원 수',
                data: sortedDepts.map(d => d[1]),
                backgroundColor: '#4ECDC4',
                borderColor: '#45B7D1',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {{
                legend: {{ display: false }},
                title: {{
                    display: true,
                    text: '부서별 인원 현황'
                }}
            }},
            scales: {{
                x: {{
                    beginAtZero: true,
                    ticks: {{ stepSize: 1 }}
                }}
            }}
        }}
    }});
}}

function renderManagerTable() {{
    const tbody = document.getElementById('managerTableBody');
    if (!tbody) return;

    const allEmployees = employeeDetails || [];

    // Find managers (employees who have direct reports)
    const managers = allEmployees
        .filter(emp => allEmployees.some(e => e.boss_id === emp.id_no))
        .map(manager => {{
            const directReports = allEmployees.filter(e => e.boss_id === manager.id_no);
            return {{
                name: manager.name || '미정',
                position: manager.position_1st || '미정',
                department: manager.position_2nd || '미정',
                teamSize: directReports.length
            }};
        }})
        .sort((a, b) => b.teamSize - a.teamSize);

    tbody.innerHTML = managers.map(m => `
        <tr>
            <td>${{m.name}}</td>
            <td>${{m.position}}</td>
            <td>${{m.department}}</td>
            <td><span class="badge bg-primary">${{m.teamSize}}</span></td>
        </tr>
    `).join('');
}}

function renderOrgChartTree() {{
    const container = document.getElementById('orgChartTree');
    container.innerHTML = '<div class="tree-content"></div>';

    const treeContent = container.querySelector('.tree-content');

    if (!hierarchyData || hierarchyData.length === 0) {{
        treeContent.innerHTML = '<p class="text-muted">조직 계층 데이터가 없습니다.</p>';
        return;
    }}

    // Render each root node
    hierarchyData.forEach(node => {{
        treeContent.appendChild(createTreeNode(node));
    }});
}}

function createTreeNode(node) {{
    const nodeDiv = document.createElement('div');
    nodeDiv.className = 'org-tree-node';

    const hasChildren = node.children && node.children.length > 0;
    const teamMetrics = node.team_metrics || {{}};

    // Calculate health status
    const avgAttendance = teamMetrics.avg_attendance_rate || 0;
    const healthClass = avgAttendance >= 90 ? 'health-good' : avgAttendance >= 70 ? 'health-warning' : 'health-danger';

    nodeDiv.innerHTML = `
        <div class="node-card ${{healthClass}}" onclick="showTeamDashboard('${{node.id}}')">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="mb-1">${{node.name}}</h6>
                    <small class="text-muted">${{node.position}}</small>
                </div>
                ${{hasChildren ? `
                <div class="node-metrics">
                    <span class="badge bg-primary">${{node.children.length}} 부하</span>
                    <span class="badge bg-info">${{avgAttendance.toFixed(1)}}% 출근율</span>
                </div>
                ` : ''}}
            </div>
            ${{hasChildren ? `
            <div class="mini-chart mt-2">
                <canvas id="miniChart_${{node.id}}" height="40"></canvas>
            </div>
            ` : ''}}
        </div>
    `;

    if (hasChildren) {{
        const childrenDiv = document.createElement('div');
        childrenDiv.className = 'node-children';

        node.children.forEach(child => {{
            childrenDiv.appendChild(createTreeNode(child));
        }});

        nodeDiv.appendChild(childrenDiv);

        // Render mini chart after DOM is ready
        setTimeout(() => {{
            renderMiniChart(node);
        }}, 100);
    }}

    return nodeDiv;
}}

function renderMiniChart(node) {{
    const canvas = document.getElementById('miniChart_' + node.id);
    if (!canvas || !node.team_metrics) return;

    const metrics = node.team_metrics;

    new Chart(canvas, {{
        type: 'bar',
        data: {{
            labels: ['출근율', '개근', '고위험'],
            datasets: [{{
                data: [
                    metrics.avg_attendance_rate || 0,
                    (metrics.perfect_attendance_count / metrics.total_members * 100) || 0,
                    (metrics.high_risk_count / metrics.total_members * 100) || 0
                ],
                backgroundColor: ['#28a745', '#17a2b8', '#dc3545']
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                y: {{ display: false, max: 100 }},
                x: {{ ticks: {{ font: {{ size: 10 }} }} }}
            }}
        }}
    }});
}}

function renderOrgChartHeatmap() {{
    const container = document.getElementById('orgChartHeatmap');
    container.innerHTML = '<div class="heatmap-grid"></div>';

    const grid = container.querySelector('.heatmap-grid');

    // Flatten hierarchy to get all managers
    const managers = [];

    function collectManagers(node) {{
        if (node.children && node.children.length > 0) {{
            managers.push(node);
            node.children.forEach(child => collectManagers(child));
        }}
    }}

    hierarchyData.forEach(node => collectManagers(node));

    if (managers.length === 0) {{
        grid.innerHTML = '<p class="text-muted">관리자 데이터가 없습니다.</p>';
        return;
    }}

    grid.innerHTML = managers.map(manager => {{
        const metrics = manager.team_metrics || {{}};
        const avgAttendance = metrics.avg_attendance_rate || 0;
        const heatColor = avgAttendance >= 90 ? '#28a745' : avgAttendance >= 70 ? '#ffc107' : '#dc3545';

        return `
            <div class="heatmap-cell" style="background-color: ${{heatColor}}33; border-color: ${{heatColor}};"
                 onclick="showTeamDashboard('${{manager.id}}')">
                <div class="heatmap-name">${{manager.name}}</div>
                <div class="heatmap-position">${{manager.position}}</div>
                <div class="heatmap-value">${{avgAttendance.toFixed(1)}}%</div>
                <div class="heatmap-team">${{manager.children.length}} 부하</div>
            </div>
        `;
    }}).join('');
}}

function renderOrgChartComparison() {{
    const container = document.getElementById('orgChartComparison');
    container.innerHTML = `
        <div class="comparison-section">
            <h5 class="mb-3">직급별 팀 성과 비교</h5>
            <div id="comparisonChart" style="height: 400px;">
                <canvas id="positionComparisonCanvas"></canvas>
            </div>
        </div>
    `;

    // Group by position
    const positionGroups = {{}};

    function groupByPosition(node) {{
        if (node.children && node.children.length > 0 && node.team_metrics) {{
            const pos = node.position || 'Unknown';
            if (!positionGroups[pos]) {{
                positionGroups[pos] = [];
            }}
            positionGroups[pos].push({{
                name: node.name,
                attendance: node.team_metrics.avg_attendance_rate || 0,
                teamSize: node.children.length
            }});

            node.children.forEach(child => groupByPosition(child));
        }}
    }}

    hierarchyData.forEach(node => groupByPosition(node));

    const positions = Object.keys(positionGroups);
    const avgAttendanceByPos = positions.map(pos => {{
        const teams = positionGroups[pos];
        const avg = teams.reduce((sum, t) => sum + t.attendance, 0) / teams.length;
        return avg;
    }});

    new Chart(document.getElementById('positionComparisonCanvas'), {{
        type: 'bar',
        data: {{
            labels: positions,
            datasets: [{{
                label: '평균 출근율 (%)',
                data: avgAttendanceByPos,
                backgroundColor: 'rgba(102, 126, 234, 0.7)',
                borderColor: '#667eea',
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ position: 'bottom' }},
                tooltip: {{
                    callbacks: {{
                        afterLabel: function(context) {{
                            const pos = context.label;
                            const teams = positionGroups[pos];
                            return `팀 수: ${{teams.length}}`;
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{ beginAtZero: true, max: 100 }}
            }}
        }}
    }});
}}

function showTeamDashboard(managerId) {{
    // Find manager node
    let manager = null;

    function findNode(node, id) {{
        if (node.id === id) return node;
        if (node.children) {{
            for (const child of node.children) {{
                const found = findNode(child, id);
                if (found) return found;
            }}
        }}
        return null;
    }}

    for (const root of hierarchyData) {{
        manager = findNode(root, managerId);
        if (manager) break;
    }}

    if (!manager || !manager.children || manager.children.length === 0) {{
        alert('팀 정보를 찾을 수 없습니다.');
        return;
    }}

    // Open modal with team dashboard
    const modal = new bootstrap.Modal(document.getElementById('teamDashboardModal'));
    populateTeamDashboardModal(manager);
    modal.show();
}}

function populateTeamDashboardModal(manager) {{
    const metrics = manager.team_metrics || {{}};

    // Update modal title
    document.getElementById('teamDashboardTitle').textContent =
        `${{manager.name}}님의 팀 대시보드 (${{manager.position}})`;

    // Update KPI cards
    document.getElementById('teamTotalMembers').textContent = metrics.total_members || 0;
    document.getElementById('teamAvgAttendance').textContent =
        (metrics.avg_attendance_rate || 0).toFixed(1) + '%';
    document.getElementById('teamPerfectAttendance').textContent =
        metrics.perfect_attendance_count || 0;
    document.getElementById('teamHighRisk').textContent = metrics.high_risk_count || 0;

    // Render Team Type Distribution Chart
    const typeDistCtx = document.getElementById('teamTypeDistributionChart');
    if (window.teamTypeChart) window.teamTypeChart.destroy();

    const typeData = metrics.type_distribution || {{}};
    window.teamTypeChart = new Chart(typeDistCtx, {{
        type: 'doughnut',
        data: {{
            labels: Object.keys(typeData),
            datasets: [{{
                data: Object.values(typeData),
                backgroundColor: ['#667eea', '#17a2b8', '#28a745'],
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ position: 'bottom' }}
            }}
        }}
    }});

    // Render Team Attendance Status Chart
    const attendanceCtx = document.getElementById('teamAttendanceStatusChart');
    if (window.teamAttendanceChart) window.teamAttendanceChart.destroy();

    window.teamAttendanceChart = new Chart(attendanceCtx, {{
        type: 'bar',
        data: {{
            labels: ['개근', '출근 양호', '고위험'],
            datasets: [{{
                label: '인원 수',
                data: [
                    metrics.perfect_attendance_count || 0,
                    (metrics.total_members - metrics.perfect_attendance_count - metrics.high_risk_count) || 0,
                    metrics.high_risk_count || 0
                ],
                backgroundColor: ['#28a745', '#17a2b8', '#dc3545'],
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }}
            }}
        }}
    }});

    // Populate team members table
    const tbody = document.getElementById('teamMembersTableBody');
    tbody.innerHTML = '';

    if (manager.children && manager.children.length > 0) {{
        manager.children.forEach(member => {{
            const row = document.createElement('tr');

            // Calculate attendance rate for member
            const memberAttendance = '95.2%'; // Placeholder - should come from actual data

            row.innerHTML = `
                <td>${{member.id}}</td>
                <td>${{member.name}}</td>
                <td>${{member.position}}</td>
                <td>${{member.entrance_date || '-'}}</td>
                <td>-</td>
                <td>${{memberAttendance}}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="showEmployeeDetail('${{member.id}}')">
                        상세
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        }});
    }} else {{
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">팀원 정보가 없습니다.</td></tr>';
    }}
}}

function showEmployeeDetail(employeeId) {{
    // Find employee in employeeDetails
    const employee = employeeDetails.find(e => e.employee_id === employeeId);

    if (!employee) {{
        alert('직원 정보를 찾을 수 없습니다.');
        return;
    }}

    // ✅ Implemented 2nd level modal for employee details
    createEmployeeDetailModal(employee);
}}

function createEmployeeDetailModal(employee) {{
    // Create or get modal container
    let modal = document.getElementById('employeeDetailModal');

    if (!modal) {{
        modal = document.createElement('div');
        modal.id = 'employeeDetailModal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', 'employeeDetailModalLabel');
        modal.setAttribute('aria-hidden', 'true');
        document.body.appendChild(modal);
    }}

    // Calculate employment duration
    const entranceDate = parseDateSafe(employee.entrance_date);
    const stopDate = parseDateSafe(employee.stop_date);
    const currentDate = stopDate || new Date();
    const durationDays = entranceDate ? Math.floor((currentDate - entranceDate) / (1000 * 60 * 60 * 24)) : 0;
    const durationYears = (durationDays / 365).toFixed(1);

    // Employment status
    const isActive = !stopDate || stopDate > new Date();
    const statusBadge = isActive
        ? '<span class="badge bg-success">재직중</span>'
        : '<span class="badge bg-secondary">퇴사</span>';

    // Attendance summary
    const attendanceRate = employee.attendance_rate || 0;
    const attendanceColor = attendanceRate >= 95 ? 'success' : attendanceRate >= 85 ? 'warning' : 'danger';

    // Modal content
    modal.innerHTML = `
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title" id="employeeDetailModalLabel">
                        <i class="bi bi-person-badge me-2"></i>
                        <span class="lang-text" data-ko="직원 상세 정보" data-en="Employee Details" data-vi="Chi tiết nhân viên">직원 상세 정보</span>
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <!-- Employee Header -->
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <h3 class="mb-3">
                                ${{employee.full_name || employee.name || 'N/A'}}
                                ${{statusBadge}}
                            </h3>
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-body">
                                            <h6 class="text-muted mb-2">
                                                <i class="bi bi-hash me-1"></i>
                                                <span class="lang-text" data-ko="사번" data-en="ID" data-vi="Mã NV">사번</span>
                                            </h6>
                                            <p class="h5 mb-0">${{employee.employee_id || 'N/A'}}</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-body">
                                            <h6 class="text-muted mb-2">
                                                <i class="bi bi-diagram-3 me-1"></i>
                                                <span class="lang-text" data-ko="팀" data-en="Team" data-vi="Nhóm">팀</span>
                                            </h6>
                                            <p class="h5 mb-0">${{employee.team || employee.position_1st || 'N/A'}}</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-body">
                                            <h6 class="text-muted mb-2">
                                                <i class="bi bi-award me-1"></i>
                                                <span class="lang-text" data-ko="직급" data-en="Position" data-vi="Chức vụ">직급</span>
                                            </h6>
                                            <p class="h5 mb-0">${{employee.position_2nd || employee.position_3rd || 'N/A'}}</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card border-0 shadow-sm">
                                        <div class="card-body">
                                            <h6 class="text-muted mb-2">
                                                <i class="bi bi-briefcase me-1"></i>
                                                <span class="lang-text" data-ko="TYPE" data-en="TYPE" data-vi="LOẠI">TYPE</span>
                                            </h6>
                                            <p class="h5 mb-0">${{employee.type || 'N/A'}}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card border-0 shadow h-100">
                                <div class="card-body text-center">
                                    <div class="display-1 mb-3">
                                        <i class="bi bi-person-circle text-primary"></i>
                                    </div>
                                    <h4 class="lang-text" data-ko="근속 기간" data-en="Tenure" data-vi="Thời gian làm việc">근속 기간</h4>
                                    <h2 class="text-primary mb-2">${{durationYears}}</h2>
                                    <p class="lang-text" data-ko="년" data-en="years" data-vi="năm">년</p>
                                    <small class="text-muted">(${{durationDays}} <span class="lang-text" data-ko="일" data-en="days" data-vi="ngày">일</span>)</small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Employment Timeline -->
                    <div class="card border-0 shadow-sm mb-4">
                        <div class="card-body">
                            <h5 class="card-title mb-3">
                                <i class="bi bi-calendar-event me-2"></i>
                                <span class="lang-text" data-ko="재직 정보" data-en="Employment Timeline" data-vi="Thời gian công tác">재직 정보</span>
                            </h5>
                            <div class="row g-3">
                                <div class="col-md-4">
                                    <div class="d-flex align-items-center">
                                        <div class="flex-shrink-0">
                                            <div class="rounded-circle bg-success bg-opacity-10 p-3">
                                                <i class="bi bi-door-open text-success fs-4"></i>
                                            </div>
                                        </div>
                                        <div class="flex-grow-1 ms-3">
                                            <h6 class="mb-1 lang-text" data-ko="입사일" data-en="Entrance Date" data-vi="Ngày vào làm">입사일</h6>
                                            <p class="mb-0 fw-bold">${{employee.entrance_date ? new Date(entranceDate).toLocaleDateString('ko-KR') : 'N/A'}}</p>
                                        </div>
                                    </div>
                                </div>
                                ${{stopDate ? `
                                <div class="col-md-4">
                                    <div class="d-flex align-items-center">
                                        <div class="flex-shrink-0">
                                            <div class="rounded-circle bg-danger bg-opacity-10 p-3">
                                                <i class="bi bi-door-closed text-danger fs-4"></i>
                                            </div>
                                        </div>
                                        <div class="flex-grow-1 ms-3">
                                            <h6 class="mb-1 lang-text" data-ko="퇴사일" data-en="Exit Date" data-vi="Ngày nghỉ việc">퇴사일</h6>
                                            <p class="mb-0 fw-bold">${{new Date(stopDate).toLocaleDateString('ko-KR')}}</p>
                                        </div>
                                    </div>
                                </div>
                                ` : ''}}
                                <div class="col-md-4">
                                    <div class="d-flex align-items-center">
                                        <div class="flex-shrink-0">
                                            <div class="rounded-circle bg-info bg-opacity-10 p-3">
                                                <i class="bi bi-clock-history text-info fs-4"></i>
                                            </div>
                                        </div>
                                        <div class="flex-grow-1 ms-3">
                                            <h6 class="mb-1 lang-text" data-ko="상태" data-en="Status" data-vi="Trạng thái">상태</h6>
                                            <p class="mb-0 fw-bold">${{isActive ? '재직중' : '퇴사'}}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Attendance Summary -->
                    <div class="card border-0 shadow-sm mb-4">
                        <div class="card-body">
                            <h5 class="card-title mb-3">
                                <i class="bi bi-graph-up me-2"></i>
                                <span class="lang-text" data-ko="출근 요약" data-en="Attendance Summary" data-vi="Tóm tắt chuyên cần">출근 요약</span>
                            </h5>
                            <div class="row g-3">
                                <div class="col-md-3">
                                    <div class="text-center p-3 border rounded">
                                        <h3 class="text-${{attendanceColor}} mb-2">${{attendanceRate.toFixed(1)}}%</h3>
                                        <p class="mb-0 small lang-text" data-ko="출근율" data-en="Attendance Rate" data-vi="Tỷ lệ chuyên cần">출근율</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center p-3 border rounded">
                                        <h3 class="text-primary mb-2">${{employee.total_working_days || 0}}</h3>
                                        <p class="mb-0 small lang-text" data-ko="총 근무일" data-en="Total Days" data-vi="Tổng số ngày">총 근무일</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center p-3 border rounded">
                                        <h3 class="text-success mb-2">${{employee.actual_working_days || 0}}</h3>
                                        <p class="mb-0 small lang-text" data-ko="실제 출근일" data-en="Actual Days" data-vi="Ngày thực tế">실제 출근일</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center p-3 border rounded">
                                        <h3 class="text-danger mb-2">${{(employee.total_working_days || 0) - (employee.actual_working_days || 0)}}</h3>
                                        <p class="mb-0 small lang-text" data-ko="결근일" data-en="Absent Days" data-vi="Ngày vắng mặt">결근일</p>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-3">
                                <div class="progress" style="height: 25px;">
                                    <div class="progress-bar bg-${{attendanceColor}}" role="progressbar"
                                         style="width: ${{attendanceRate}}%"
                                         aria-valuenow="${{attendanceRate}}"
                                         aria-valuemin="0"
                                         aria-valuemax="100">
                                        ${{attendanceRate.toFixed(1)}}%
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Additional Info -->
                    ${{employee.note ? `
                    <div class="card border-0 shadow-sm">
                        <div class="card-body">
                            <h5 class="card-title mb-3">
                                <i class="bi bi-sticky me-2"></i>
                                <span class="lang-text" data-ko="비고" data-en="Notes" data-vi="Ghi chú">비고</span>
                            </h5>
                            <p class="mb-0">${{employee.note}}</p>
                        </div>
                    </div>
                    ` : ''}}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        <span class="lang-text" data-ko="닫기" data-en="Close" data-vi="Đóng">닫기</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();

    // Apply current language to modal content
    if (typeof applyLanguage === 'function') {{
        applyLanguage(currentLanguage);
    }}
}}

function exportTeamData() {{
    // ✅ Implemented team data export functionality
    // Get currently displayed team from modal
    const modalTitle = document.querySelector('#teamDetailModal .modal-title');
    if (!modalTitle) {{
        alert('활성 팀 모달을 찾을 수 없습니다.');
        return;
    }}

    const titleText = modalTitle.textContent.trim();
    const teamMatch = titleText.match(/(.+)\\s+-\\s+총\\s+재직자\\s+수\\s+상세\\s+분석/);
    const teamName = teamMatch ? teamMatch[1].trim() : 'Unknown_Team';

    // Find team data
    const team = teamData[teamName];
    if (!team || !team.members) {{
        alert('팀 데이터를 찾을 수 없습니다.');
        return;
    }}

    // Prepare export data with comprehensive information
    const exportData = team.members.map(member => {{
        const entranceDate = parseDateSafe(member.entrance_date);
        const stopDate = parseDateSafe(member.stop_date);
        const isActive = !stopDate || stopDate > new Date();
        const durationDays = entranceDate ? Math.floor((new Date() - entranceDate) / (1000 * 60 * 60 * 24)) : 0;

        return {{
            '사번': member.employee_id || '',
            '이름': member.full_name || member.name || '',
            '팀': member.team || team.position_1st || '',
            '직급': member.position_2nd || member.position_3rd || '',
            'TYPE': member.type || '',
            '입사일': member.entrance_date || '',
            '퇴사일': member.stop_date || '',
            '상태': isActive ? '재직중' : '퇴사',
            '근속일수': durationDays,
            '출근율': member.attendance_rate ? member.attendance_rate.toFixed(1) + '%' : '0%',
            '총근무일': member.total_working_days || 0,
            '실제출근일': member.actual_working_days || 0,
            '결근일': (member.total_working_days || 0) - (member.actual_working_days || 0),
            '비고': member.note || ''
        }};
    }});

    // Create CSV content
    const headers = Object.keys(exportData[0]);
    const csvContent = [
        headers.join(','),
        ...exportData.map(row => headers.map(header => {{
            const value = row[header];
            // Escape commas and quotes
            const escaped = String(value).replace(/"/g, '""');
            return `"${{escaped}}"`;
        }}).join(','))
    ].join('\\n');

    // Create downloadable file
    const blob = new Blob([new Uint8Array([0xEF, 0xBB, 0xBF]), csvContent], {{ type: 'text/csv;charset=utf-8;' }});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `팀데이터_${{teamName}}_${{new Date().toISOString().split('T')[0]}}.csv`);
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    // Show success message
    showToast('팀 데이터 내보내기 완료', `${{teamName}} 팀의 ${{exportData.length}}명 데이터가 CSV 파일로 저장되었습니다.`, 'success');
}}

function exportTeamDataJSON() {{
    // Export team data as JSON format
    const modalTitle = document.querySelector('#teamDetailModal .modal-title');
    if (!modalTitle) {{
        alert('활성 팀 모달을 찾을 수 없습니다.');
        return;
    }}

    const titleText = modalTitle.textContent.trim();
    const teamMatch = titleText.match(/(.+)\\s+-\\s+총\\s+재직자\\s+수\\s+상세\\s+분석/);
    const teamName = teamMatch ? teamMatch[1].trim() : 'Unknown_Team';

    const team = teamData[teamName];
    if (!team) {{
        alert('팀 데이터를 찾을 수 없습니다.');
        return;
    }}

    // Prepare comprehensive team export
    const exportPackage = {{
        team_name: teamName,
        export_date: new Date().toISOString(),
        summary: {{
            total_members: team.members ? team.members.length : 0,
            active_members: team.members ? team.members.filter(m => !parseDateSafe(m.stop_date) || parseDateSafe(m.stop_date) > new Date()).length : 0,
            position_1st: team.position_1st || '',
            position_2nd: team.position_2nd || '',
            position_3rd: team.position_3rd || ''
        }},
        members: team.members || [],
        monthly_metrics: team.monthly || {{}},
        weekly_metrics: team.weekly || {{}}
    }};

    const jsonContent = JSON.stringify(exportPackage, null, 2);
    const blob = new Blob([jsonContent], {{ type: 'application/json' }});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `팀데이터_${{teamName}}_${{new Date().toISOString().split('T')[0]}}.json`);
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showToast('팀 데이터 내보내기 완료', `${{teamName}} 팀 데이터가 JSON 파일로 저장되었습니다.`, 'success');
}}

function showToast(title, message, type = 'info') {{
    // Simple toast notification
    const toastColors = {{
        success: '#28a745',
        info: '#17a2b8',
        warning: '#ffc107',
        error: '#dc3545'
    }};

    const toast = document.createElement('div');
    toast.className = 'position-fixed top-0 end-0 p-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="toast show" role="alert">
            <div class="toast-header" style="background-color: ${{toastColors[type]}}; color: white;">
                <strong class="me-auto">${{title}}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${{message}}
            </div>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {{
        toast.remove();
    }}, 5000);
}}

// Initialize org chart on tab switch (null check to prevent error)
// 조직도 탭 전환시 초기화 (오류 방지를 위한 null 체크)
const orgchartTab = document.getElementById('orgchart-tab');
if (orgchartTab) {{
    orgchartTab.addEventListener('shown.bs.tab', function() {{
        if (currentOrgView === 'tree') {{
            renderOrgChartTree();
        }}
    }});
}}

// ============================================
// Team Analysis Functions
// ============================================

let teamAnalysisCharts = {{}};

function initTeamAnalysis() {{
    // Populate team position selector
    const positionSelect = document.getElementById('teamPositionSelect');
    const positions = new Set();

    Object.keys(teamData).forEach(teamKey => {{
        const team = teamData[teamKey];
        positions.add(team.position_1st || 'Unknown');
    }});

    Array.from(positions).sort().forEach(position => {{
        const option = document.createElement('option');
        option.value = position;
        option.textContent = position;
        positionSelect.appendChild(option);
    }});

    // Initial load
    filterTeamsByPosition();
}}

function filterTeamsByPosition() {{
    const positionSelect = document.getElementById('teamPositionSelect');
    const teamSelect = document.getElementById('teamNameSelect');
    const selectedPosition = positionSelect.value;

    // Clear team selector
    teamSelect.innerHTML = '<option value="all" selected>\ud300 \uc120\ud0dd...</option>';

    // Filter teams by position
    const filteredTeams = Object.keys(teamData).filter(teamKey => {{
        if (selectedPosition === 'all') return true;
        return teamData[teamKey].position_1st === selectedPosition;
    }});

    // Populate team selector
    filteredTeams.forEach(teamKey => {{
        const team = teamData[teamKey];
        const option = document.createElement('option');
        option.value = teamKey;
        option.textContent = `${{team.position_1st}} - ${{teamKey}}`;
        teamSelect.appendChild(option);
    }});

    // Update overview
    updateTeamOverview(selectedPosition);
    renderTeamCharts(selectedPosition);
    renderTeamDetailsTable(selectedPosition);
}}

function selectTeam() {{
    const teamSelect = document.getElementById('teamNameSelect');
    const selectedTeam = teamSelect.value;

    if (selectedTeam === 'all') {{
        filterTeamsByPosition();
    }} else {{
        // Show specific team analysis
        updateTeamOverview(null, selectedTeam);
        renderTeamCharts(null, selectedTeam);
        renderTeamDetailsTable(null, selectedTeam);
    }}
}}

function updateTeamOverview(position = 'all', specificTeam = null) {{
    let teamsToAnalyze = Object.keys(teamData);

    if (specificTeam) {{
        teamsToAnalyze = [specificTeam];
    }} else if (position && position !== 'all') {{
        teamsToAnalyze = teamsToAnalyze.filter(key => teamData[key].position_1st === position);
    }}

    // Calculate aggregated metrics
    let totalTeams = teamsToAnalyze.length;
    let totalMembers = 0;
    let sumAttendance = 0;
    let topTeam = {{ name: '-', attendance: 0 }};

    teamsToAnalyze.forEach(teamKey => {{
        const team = teamData[teamKey];
        const metrics = team.metrics || {{}};

        totalMembers += metrics.total_members || 0;
        const attendance = metrics.avg_attendance_rate || 0;
        sumAttendance += attendance;

        if (attendance > topTeam.attendance) {{
            topTeam = {{ name: teamKey, attendance: attendance }};
        }}
    }});

    const avgAttendance = totalTeams > 0 ? (sumAttendance / totalTeams) : 0;

    // Update cards
    document.getElementById('totalTeamsCount').textContent = totalTeams;
    document.getElementById('totalTeamMembersCount').textContent = totalMembers;
    document.getElementById('avgTeamAttendance').textContent = avgAttendance.toFixed(1) + '%';
    document.getElementById('topPerformingTeam').textContent = topTeam.name;
}}

function renderTeamCharts(position = 'all', specificTeam = null) {{
    let teamsToAnalyze = Object.keys(teamData);

    if (specificTeam) {{
        teamsToAnalyze = [specificTeam];
    }} else if (position && position !== 'all') {{
        teamsToAnalyze = teamsToAnalyze.filter(key => teamData[key].position_1st === position);
    }}

    // Sort teams by name for consistent ordering
    teamsToAnalyze.sort();

    // Chart 1: Team Attendance Comparison
    const attendanceCtx = document.getElementById('teamAttendanceComparisonChart');
    if (teamAnalysisCharts.attendance) teamAnalysisCharts.attendance.destroy();

    const attendanceData = teamsToAnalyze.map(key => {{
        return teamData[key].metrics?.avg_attendance_rate || 0;
    }});

    teamAnalysisCharts.attendance = new Chart(attendanceCtx, {{
        type: 'bar',
        data: {{
            labels: teamsToAnalyze,
            datasets: [{{
                label: '\ucd9c\uadfc\uc728 (%)',
                data: attendanceData,
                backgroundColor: 'rgba(102, 126, 234, 0.7)',
                borderColor: '#667eea',
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ position: 'bottom' }} }},
            scales: {{
                y: {{ beginAtZero: true, max: 100 }}
            }}
        }}
    }});

    // Chart 2: Team Size Distribution
    const sizeCtx = document.getElementById('teamSizeDistributionChart');
    if (teamAnalysisCharts.size) teamAnalysisCharts.size.destroy();

    const sizeData = teamsToAnalyze.map(key => {{
        return teamData[key].metrics?.total_members || 0;
    }});

    teamAnalysisCharts.size = new Chart(sizeCtx, {{
        type: 'doughnut',
        data: {{
            labels: teamsToAnalyze,
            datasets: [{{
                data: sizeData,
                backgroundColor: [
                    '#667eea', '#764ba2', '#f093fb', '#4facfe',
                    '#43e97b', '#fa709a', '#fee140', '#30cfd0'
                ],
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ position: 'right' }} }}
        }}
    }});

    // Chart 3: TYPE Breakdown (aggregated)
    const typeCtx = document.getElementById('teamTypeBreakdownChart');
    if (teamAnalysisCharts.type) teamAnalysisCharts.type.destroy();

    const typeAggregated = {{}};
    teamsToAnalyze.forEach(key => {{
        const dist = teamData[key].metrics?.type_distribution || {{}};
        Object.keys(dist).forEach(type => {{
            typeAggregated[type] = (typeAggregated[type] || 0) + dist[type];
        }});
    }});

    teamAnalysisCharts.type = new Chart(typeCtx, {{
        type: 'bar',
        data: {{
            labels: Object.keys(typeAggregated),
            datasets: [{{
                label: '\uc778\uc6d0 \uc218',
                data: Object.values(typeAggregated),
                backgroundColor: ['#667eea', '#17a2b8', '#28a745'],
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{
                y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }}
            }}
        }}
    }});

    // Chart 4: Team Tenure
    const tenureCtx = document.getElementById('teamTenureChart');
    if (teamAnalysisCharts.tenure) teamAnalysisCharts.tenure.destroy();

    const tenureData = teamsToAnalyze.map(key => {{
        return teamData[key].metrics?.avg_tenure_years || 0;
    }});

    teamAnalysisCharts.tenure = new Chart(tenureCtx, {{
        type: 'line',
        data: {{
            labels: teamsToAnalyze,
            datasets: [{{
                label: '\ud3c9\uade0 \uadfc\uc18d\uc5f0\uc218',
                data: tenureData,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4,
                fill: true
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ position: 'bottom' }} }},
            scales: {{
                y: {{ beginAtZero: true }}
            }}
        }}
    }});
}}

function renderTeamDetailsTable(position = 'all', specificTeam = null) {{
    const tbody = document.getElementById('teamDetailsTableBody');
    tbody.innerHTML = '';

    let teamsToShow = Object.keys(teamData);

    if (specificTeam) {{
        teamsToShow = [specificTeam];
    }} else if (position && position !== 'all') {{
        teamsToShow = teamsToShow.filter(key => teamData[key].position_1st === position);
    }}

    teamsToShow.sort().forEach(teamKey => {{
        const team = teamData[teamKey];
        const metrics = team.metrics || {{}};

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${{team.position_1st || '-'}}</td>
            <td>${{teamKey}}</td>
            <td>${{metrics.total_members || 0}}</td>
            <td>${{(metrics.avg_attendance_rate || 0).toFixed(1)}}%</td>
            <td>${{metrics.perfect_attendance_count || 0}}</td>
            <td>${{metrics.high_risk_count || 0}}</td>
            <td>${{(metrics.avg_tenure_years || 0).toFixed(2)}} \ub144</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="viewTeamDetail('${{teamKey}}')">
                    \ubcf4\uae30
                </button>
            </td>
        `;
        tbody.appendChild(row);
    }});
}}

function viewTeamDetail(teamKey) {{
    // Open the team detail modal with default KPI
    showTeamDetailModal(teamKey, 'total_employees');
}}

function exportTeamAnalysis() {{
    /**
     * Export team analysis data to CSV
     * 팀 분석 데이터를 CSV로 내보내기
     */
    try {{
        // Build export data from teamData
        // teamData에서 내보내기 데이터 구성
        const exportRows = [];

        // Header row
        const headers = [
            '팀명 (Team)',
            '총 인원 (Total)',
            '결근율 (%) (Absence Rate)',
            '무단결근율 (%) (Unauthorized)',
            '완벽출근 (Perfect Attendance)',
            '완벽출근율 (%) (Perfect Rate)',
            '전월 대비 (vs Previous)',
            '상태 (Status)'
        ];
        exportRows.push(headers.join(','));

        // Get team names sorted
        const teamNames = Object.keys(teamData).sort((a, b) => {{
            const countA = teamData[a].members ? teamData[a].members.length : 0;
            const countB = teamData[b].members ? teamData[b].members.length : 0;
            return countB - countA;
        }});

        let grandTotal = 0;
        let grandAbsent = 0;
        let grandUnauthorized = 0;
        let grandPerfect = 0;

        teamNames.forEach(teamName => {{
            const team = teamData[teamName];
            const members = team.members || [];
            const memberCount = members.length;

            if (memberCount === 0) return;

            grandTotal += memberCount;

            // Calculate metrics
            let absentCount = 0;
            let unauthorizedCount = 0;
            let perfectCount = 0;

            members.forEach(member => {{
                const absentDays = member.absent_days || 0;
                const unauthorizedDays = member.unauthorized_absent_days || 0;

                if (absentDays > 0) absentCount++;
                if (unauthorizedDays > 0) unauthorizedCount++;
                if (absentDays === 0) perfectCount++;
            }});

            grandAbsent += absentCount;
            grandUnauthorized += unauthorizedCount;
            grandPerfect += perfectCount;

            const absenceRate = memberCount > 0 ? ((absentCount / memberCount) * 100).toFixed(1) : '0.0';
            const unauthorizedRate = memberCount > 0 ? ((unauthorizedCount / memberCount) * 100).toFixed(1) : '0.0';
            const perfectRate = memberCount > 0 ? ((perfectCount / memberCount) * 100).toFixed(1) : '0.0';

            // Calculate month-over-month change
            let momChange = '-';
            let status = '정상';

            if (previousMonthTeamData && previousMonthTeamData[teamName]) {{
                const prevMembers = previousMonthTeamData[teamName].members || [];
                const prevCount = prevMembers.length;
                if (prevCount > 0) {{
                    const change = memberCount - prevCount;
                    const changePercent = ((change / prevCount) * 100).toFixed(1);
                    momChange = change >= 0 ? `+${{change}} (+${{changePercent}}%)` : `${{change}} (${{changePercent}}%)`;
                }}
            }}

            // Determine status based on unauthorized rate
            const uRate = parseFloat(unauthorizedRate);
            if (uRate >= 5) {{
                status = '경고';
            }} else if (uRate >= 2) {{
                status = '주의';
            }} else {{
                status = '양호';
            }}

            // Escape and format CSV row
            const row = [
                `"${{teamName}}"`,
                memberCount,
                absenceRate,
                unauthorizedRate,
                perfectCount,
                perfectRate,
                `"${{momChange}}"`,
                status
            ];
            exportRows.push(row.join(','));
        }});

        // Add summary row
        const totalAbsenceRate = grandTotal > 0 ? ((grandAbsent / grandTotal) * 100).toFixed(1) : '0.0';
        const totalUnauthorizedRate = grandTotal > 0 ? ((grandUnauthorized / grandTotal) * 100).toFixed(1) : '0.0';
        const totalPerfectRate = grandTotal > 0 ? ((grandPerfect / grandTotal) * 100).toFixed(1) : '0.0';

        exportRows.push('');  // Empty row
        exportRows.push([
            '"전체 (Total)"',
            grandTotal,
            totalAbsenceRate,
            totalUnauthorizedRate,
            grandPerfect,
            totalPerfectRate,
            '"-"',
            '"-"'
        ].join(','));

        // Create CSV content with BOM for Excel Korean support
        const csvContent = '\\ufeff' + exportRows.join('\\n');

        // Create and download file
        const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        // Generate filename with current date
        const now = new Date();
        const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
        const filename = `Team_Analysis_${{dateStr}}.csv`;

        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        // Show success message
        showToast(
            '팀 분석 내보내기 완료',
            `${{teamNames.length}}개 팀 데이터가 CSV 파일로 저장되었습니다.`,
            'success'
        );

    }} catch (error) {{
        debugLog('Export error:', error);
        showToast('내보내기 오류', '팀 분석 데이터 내보내기 중 오류가 발생했습니다.', 'error');
    }}
}}

function exportTeamAnalysisJSON() {{
    /**
     * Export team analysis data to JSON
     * 팀 분석 데이터를 JSON으로 내보내기
     */
    try {{
        const exportData = {{}};

        Object.keys(teamData).forEach(teamName => {{
            const team = teamData[teamName];
            const members = team.members || [];

            if (members.length === 0) return;

            let absentCount = 0;
            let unauthorizedCount = 0;
            let perfectCount = 0;

            members.forEach(member => {{
                if ((member.absent_days || 0) > 0) absentCount++;
                if (member.has_unauthorized_absence) unauthorizedCount++;
                if ((member.absent_days || 0) === 0) perfectCount++;
            }});

            exportData[teamName] = {{
                total_employees: members.length,
                absence_count: absentCount,
                absence_rate: members.length > 0 ? ((absentCount / members.length) * 100).toFixed(2) : 0,
                unauthorized_count: unauthorizedCount,
                unauthorized_rate: members.length > 0 ? ((unauthorizedCount / members.length) * 100).toFixed(2) : 0,
                perfect_attendance_count: perfectCount,
                perfect_attendance_rate: members.length > 0 ? ((perfectCount / members.length) * 100).toFixed(2) : 0,
                members: members.map(m => ({{
                    employee_no: m.employee_no,
                    name: m.name,
                    position: m.position_1st,
                    tenure_days: m.tenure_days,
                    absent_days: m.absent_days || 0,
                    unauthorized_absent_days: m.unauthorized_absent_days || 0
                }}))
            }};
        }});

        const jsonContent = JSON.stringify(exportData, null, 2);
        const blob = new Blob([jsonContent], {{ type: 'application/json;charset=utf-8;' }});
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        const now = new Date();
        const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
        const filename = `Team_Analysis_${{dateStr}}.json`;

        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        showToast(
            '팀 분석 내보내기 완료',
            `${{Object.keys(exportData).length}}개 팀 데이터가 JSON 파일로 저장되었습니다.`,
            'success'
        );

    }} catch (error) {{
        debugLog('Export error:', error);
        showToast('내보내기 오류', '팀 분석 데이터 내보내기 중 오류가 발생했습니다.', 'error');
    }}
}}

// Initialize team analysis on tab switch (null check to prevent error)
// 팀 분석 탭 전환시 초기화 (오류 방지를 위한 null 체크)
const teamanalysisTab = document.getElementById('teamanalysis-tab');
if (teamanalysisTab) {{
    teamanalysisTab.addEventListener('shown.bs.tab', function() {{
        initTeamAnalysis();
    }});
}}

// ============================================
// Individual Attendance Tab Functions
// 개인 출결 조회 탭 기능
// ============================================

let currentEmployeeAttendance = [];

function searchEmployeeAttendance() {{
    const searchInput = document.getElementById('attendanceEmployeeSearch');
    const employeeNo = searchInput.value.trim();

    if (!employeeNo) {{
        showToast('알림', '사원번호를 입력해주세요', 'warning');
        return;
    }}

    // Filter attendance data for this employee
    // 해당 직원의 출결 데이터 필터링
    const employeeRecords = attendanceData.filter(record =>
        record.employee_no === employeeNo ||
        record.employee_no.includes(employeeNo)
    );

    // Update UI based on results
    // 결과에 따라 UI 업데이트
    document.getElementById('attendanceInitialState').classList.add('d-none');
    document.getElementById('attendanceNoResults').classList.add('d-none');
    document.getElementById('attendanceResults').classList.add('d-none');

    if (employeeRecords.length === 0) {{
        document.getElementById('attendanceNoResults').classList.remove('d-none');
        return;
    }}

    currentEmployeeAttendance = employeeRecords;
    document.getElementById('attendanceResults').classList.remove('d-none');

    // Display results
    // 결과 표시
    displayAttendanceResults(employeeRecords);
}}

function displayAttendanceResults(records) {{
    // Get employee name from first record
    // 첫 번째 레코드에서 직원 이름 가져오기
    const employeeName = records[0].employee_name || records[0].employee_no;
    const employeeNo = records[0].employee_no;

    // Update header with employee info
    // 직원 정보로 헤더 업데이트
    const lang = localStorage.getItem('selectedLanguage') || 'ko';
    const headerText = lang === 'ko' ? `👤 ${{employeeName}} (${{employeeNo}})` :
                       lang === 'en' ? `👤 ${{employeeName}} (${{employeeNo}})` :
                       `👤 ${{employeeName}} (${{employeeNo}})`;
    document.getElementById('attendanceEmployeeName').innerHTML = headerText;

    // Calculate summary statistics
    // 요약 통계 계산
    const totalDays = records.length;
    const presentDays = records.filter(r => r.status === 'present').length;
    const absentDays = records.filter(r => r.status === 'absent').length;
    const attendanceRate = totalDays > 0 ? ((presentDays / totalDays) * 100).toFixed(1) : 0;
    const absenceRate = totalDays > 0 ? ((absentDays / totalDays) * 100).toFixed(1) : 0;

    // Update stat boxes
    // 통계 박스 업데이트
    document.getElementById('attendancePresentDays').textContent = presentDays;
    document.getElementById('attendanceAbsentDays').textContent = absentDays;
    document.getElementById('attendanceRate').textContent = attendanceRate + '%';
    document.getElementById('attendanceAbsenceRate').textContent = absenceRate + '%';

    // Analyze day of week pattern
    // 요일별 패턴 분석
    displayDayPattern(records);

    // Analyze absence reasons
    // 결근 사유 분석
    displayReasonBreakdown(records);

    // Generate insights
    // 인사이트 생성
    displayAttendanceInsights(records, presentDays, absentDays, attendanceRate);

    // Display daily records table
    // 일별 기록 테이블 표시
    displayDailyRecords(records);
}}

function displayDayPattern(records) {{
    const lang = localStorage.getItem('selectedLanguage') || 'ko';
    const dayNames = {{
        ko: ['월', '화', '수', '목', '금', '토', '일'],
        en: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        vi: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
    }};

    // Count absences by day of week
    // 요일별 결근 횟수 계산
    const dayCount = {{'월': 0, '화': 0, '수': 0, '목': 0, '금': 0, '토': 0, '일': 0}};
    const dayTotal = {{'월': 0, '화': 0, '수': 0, '목': 0, '금': 0, '토': 0, '일': 0}};

    records.forEach(record => {{
        const day = record.day_of_week;
        if (day && dayTotal.hasOwnProperty(day)) {{
            dayTotal[day]++;
            if (record.status === 'absent') {{
                dayCount[day]++;
            }}
        }}
    }});

    // Build day pattern HTML
    // 요일 패턴 HTML 생성
    let html = '<div class="d-flex flex-wrap gap-2">';
    const dayOrder = ['월', '화', '수', '목', '금', '토'];
    const dayIndex = {{'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5}};

    dayOrder.forEach((day, idx) => {{
        const count = dayCount[day] || 0;
        const total = dayTotal[day] || 0;
        const rate = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
        const displayDay = dayNames[lang] ? dayNames[lang][idx] : day;

        let badgeClass = 'bg-success';
        if (rate >= 30) badgeClass = 'bg-danger';
        else if (rate >= 15) badgeClass = 'bg-warning text-dark';
        else if (rate >= 5) badgeClass = 'bg-info';

        html += `
            <div class="text-center p-2 border rounded" style="min-width: 60px;">
                <div class="fw-bold">${{displayDay}}</div>
                <div class="badge ${{badgeClass}}">${{count}}/${{total}}</div>
                <div class="small text-muted">${{rate}}%</div>
            </div>
        `;
    }});
    html += '</div>';

    document.getElementById('attendanceDayPattern').innerHTML = html;
}}

function displayReasonBreakdown(records) {{
    const lang = localStorage.getItem('selectedLanguage') || 'ko';

    // Count by reason
    // 사유별 횟수 계산
    const reasonCount = {{}};
    const absentRecords = records.filter(r => r.status === 'absent');

    absentRecords.forEach(record => {{
        const reason = lang === 'ko' ? (record.reason_ko || record.reason || '미지정') :
                       lang === 'en' ? (record.reason_en || record.reason || 'Unspecified') :
                       (record.reason_vi || record.reason || 'Không xác định');
        reasonCount[reason] = (reasonCount[reason] || 0) + 1;
    }});

    if (Object.keys(reasonCount).length === 0) {{
        const noAbsenceText = lang === 'ko' ? '결근 기록이 없습니다 ✨' :
                              lang === 'en' ? 'No absence records ✨' :
                              'Không có ngày nghỉ ✨';
        document.getElementById('attendanceReasonBreakdown').innerHTML =
            `<div class="alert alert-success mb-0">${{noAbsenceText}}</div>`;
        return;
    }}

    // Sort by count descending
    // 횟수 내림차순 정렬
    const sortedReasons = Object.entries(reasonCount)
        .sort((a, b) => b[1] - a[1]);

    // Build reason breakdown HTML
    // 사유 분석 HTML 생성
    let html = '<div class="list-group">';
    sortedReasons.forEach(([reason, count]) => {{
        const percentage = ((count / absentRecords.length) * 100).toFixed(0);
        html += `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>${{reason}}</span>
                <div>
                    <span class="badge bg-danger rounded-pill me-2">${{count}}</span>
                    <span class="small text-muted">${{percentage}}%</span>
                </div>
            </div>
        `;
    }});
    html += '</div>';

    document.getElementById('attendanceReasonBreakdown').innerHTML = html;
}}

function displayAttendanceInsights(records, presentDays, absentDays, attendanceRate) {{
    const lang = localStorage.getItem('selectedLanguage') || 'ko';
    let insights = [];

    // Insight 1: Overall attendance assessment
    // 인사이트 1: 전체 출결 평가
    if (parseFloat(attendanceRate) >= 95) {{
        insights.push({{
            icon: '🌟',
            text: lang === 'ko' ? `출근율 ${{attendanceRate}}%로 우수합니다!` :
                  lang === 'en' ? `Excellent attendance rate of ${{attendanceRate}}%!` :
                  `Tỷ lệ đi làm tuyệt vời ${{attendanceRate}}%!`,
            type: 'success'
        }});
    }} else if (parseFloat(attendanceRate) < 85) {{
        insights.push({{
            icon: '⚠️',
            text: lang === 'ko' ? `출근율 ${{attendanceRate}}%로 관리가 필요합니다` :
                  lang === 'en' ? `Attendance rate of ${{attendanceRate}}% needs attention` :
                  `Tỷ lệ đi làm ${{attendanceRate}}% cần chú ý`,
            type: 'warning'
        }});
    }}

    // Insight 2: Check for day pattern
    // 인사이트 2: 요일 패턴 확인
    const dayCount = {{}};
    records.filter(r => r.status === 'absent').forEach(r => {{
        dayCount[r.day_of_week] = (dayCount[r.day_of_week] || 0) + 1;
    }});

    const maxDay = Object.entries(dayCount).sort((a, b) => b[1] - a[1])[0];
    if (maxDay && maxDay[1] >= 2) {{
        insights.push({{
            icon: '📅',
            text: lang === 'ko' ? `${{maxDay[0]}}요일에 결근이 집중됩니다 (${{maxDay[1]}}회)` :
                  lang === 'en' ? `Absences concentrated on ${{maxDay[0]}} (${{maxDay[1]}} times)` :
                  `Nghỉ tập trung vào ${{maxDay[0]}} (${{maxDay[1]}} lần)`,
            type: 'info'
        }});
    }}

    // Insight 3: Check for common reason
    // 인사이트 3: 주요 사유 확인
    const reasonCount = {{}};
    records.filter(r => r.status === 'absent').forEach(r => {{
        const reason = r.reason_ko || r.reason || '미지정';
        reasonCount[reason] = (reasonCount[reason] || 0) + 1;
    }});

    const maxReason = Object.entries(reasonCount).sort((a, b) => b[1] - a[1])[0];
    if (maxReason && maxReason[1] >= 2) {{
        insights.push({{
            icon: '📋',
            text: lang === 'ko' ? `주요 결근 사유: ${{maxReason[0]}} (${{maxReason[1]}}회)` :
                  lang === 'en' ? `Main absence reason: ${{maxReason[0]}} (${{maxReason[1]}} times)` :
                  `Lý do nghỉ chính: ${{maxReason[0]}} (${{maxReason[1]}} lần)`,
            type: 'info'
        }});
    }}

    // Build insights HTML
    // 인사이트 HTML 생성
    if (insights.length === 0) {{
        insights.push({{
            icon: '✅',
            text: lang === 'ko' ? '특이사항 없음' :
                  lang === 'en' ? 'No notable patterns' :
                  'Không có điều đáng chú ý',
            type: 'success'
        }});
    }}

    let html = '<div class="d-flex flex-wrap gap-3">';
    insights.forEach(insight => {{
        const bgClass = insight.type === 'success' ? 'bg-success-subtle' :
                       insight.type === 'warning' ? 'bg-warning-subtle' :
                       'bg-info-subtle';
        html += `
            <div class="p-2 rounded ${{bgClass}}" style="flex: 1; min-width: 200px;">
                <span class="me-2">${{insight.icon}}</span>
                <span>${{insight.text}}</span>
            </div>
        `;
    }});
    html += '</div>';

    document.getElementById('attendanceInsights').innerHTML = html;
}}

function displayDailyRecords(records) {{
    const lang = localStorage.getItem('selectedLanguage') || 'ko';
    const tbody = document.getElementById('attendanceDetailBody');

    // Sort records by date
    // 날짜순 정렬
    const sortedRecords = [...records].sort((a, b) => {{
        return a.work_date.localeCompare(b.work_date);
    }});

    let html = '';
    sortedRecords.forEach(record => {{
        const statusClass = record.status === 'present' ? 'text-success' :
                           record.status === 'absent' ? 'text-danger' : 'text-secondary';
        const statusIcon = record.status === 'present' ? '✅' :
                          record.status === 'absent' ? '❌' : '➖';
        const statusText = lang === 'ko' ? record.status_ko :
                          lang === 'en' ? record.status_en : record.status_vi;

        const reason = lang === 'ko' ? record.reason_ko :
                      lang === 'en' ? record.reason_en : record.reason_vi;
        const reasonDisplay = record.status === 'absent' && reason ? reason : '-';

        const dayText = lang === 'ko' ? record.day_of_week :
                       lang === 'en' ? record.day_of_week_en : record.day_of_week_vi;

        html += `
            <tr class="${{record.status === 'absent' ? 'table-danger' : ''}}">
                <td class="text-center">${{record.work_date}}</td>
                <td class="text-center">${{dayText || '-'}}</td>
                <td class="text-center ${{statusClass}} fw-bold">
                    ${{statusIcon}} ${{statusText}}
                </td>
                <td>${{reasonDisplay}}</td>
                <td class="text-center">${{record.work_time || '-'}}</td>
            </tr>
        `;
    }});

    tbody.innerHTML = html;
}}

function exportAttendanceCSV() {{
    if (currentEmployeeAttendance.length === 0) {{
        showToast('알림', '내보낼 데이터가 없습니다', 'warning');
        return;
    }}

    const employeeNo = currentEmployeeAttendance[0].employee_no;
    const employeeName = currentEmployeeAttendance[0].employee_name;

    // Create CSV content
    // CSV 내용 생성
    let csvContent = '\\uFEFF';  // BOM for Excel UTF-8 support
    csvContent += '날짜,요일,출결상태,사유,근무시간\\n';

    currentEmployeeAttendance.forEach(record => {{
        const row = [
            record.work_date,
            record.day_of_week || '',
            record.status_ko || record.status,
            record.reason_ko || record.reason || '',
            record.work_time || ''
        ].map(field => `"${{(field || '').toString().replace(/"/g, '""')}}"`);
        csvContent += row.join(',') + '\\n';
    }});

    // Download file
    // 파일 다운로드
    const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `attendance_${{employeeNo}}_${{employeeName}}_${{targetMonth}}.csv`;
    link.click();

    showToast('완료', 'CSV 파일이 다운로드되었습니다', 'success');
}}

debugLog('✅ Dashboard initialized');
debugLog('📊 Months:', availableMonths);
debugLog('👥 Employees:', employeeDetails.length);
debugLog('📋 Modal data:', modalData);
"""


def main():
    """Build and save dashboard"""
    import argparse

    parser = argparse.ArgumentParser(description='Build Complete HR Dashboard')
    parser.add_argument('--month', '-m', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--year', '-y', type=int, required=True, help='Target year')
    parser.add_argument('--language', '-l', default='ko', choices=['ko', 'en', 'vi'])

    args = parser.parse_args()

    target_month = f"{args.year}-{args.month:02d}"

    builder = CompleteDashboardBuilder(target_month, args.language)
    html = builder.build()

    # Save dashboard
    output_dir = Path(__file__).parent.parent.parent / 'output_files'
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"HR_Dashboard_Complete_{target_month.replace('-', '_')}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ Dashboard saved: {output_path}")
    print(f"🌐 Opening in browser...")

    import webbrowser
    webbrowser.open(f"file://{output_path.absolute()}")


if __name__ == '__main__':
    main()
