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
from typing import Dict, List, Any
from datetime import datetime, timedelta
import sys
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.monthly_data_collector import MonthlyDataCollector
from src.analytics.hr_metric_calculator import HRMetricCalculator


# Team mapping configuration - Based on FINAL_TEAM_MAPPING_V2.md
# 11 teams with 100% coverage (506 employees)
TEAM_MAPPING = {
    'ASSEMBLY': [
        'ASSEMBLY LINE TQC',
        'ASSEMBLY LINE RQC',
        '12 ASSEMBLY LINE QUALITY IN CHARGE',
        '2 ASSEMBLY BUILDING QUALITY IN CHARGE',
        '1 ASSEMBLY BUILDING QUALITY IN CHARGE',
        'ALL ASSEMBLY BUILDING QUALITY IN CHARGE',
        'ASSEMBLY LINE PO COMPLETION QUALITY',
        'SCAN PACK AREA TQC',
        'ALL B-GRADE CONTROL & PACKING'
    ],
    'STITCHING': [
        'STITCHING LINE TQC',
        'STITCHING LINE RQC',
        '1 STITCHING BUILDING QUALITY IN CHARGE',
        'ALL STITCHING BUILDING QUALITY IN CHARGE',
        '1 STITCHING BUILDING QIP LEADER\'S SUCCESSOR 1',
        '1 STITCHING BUILDING QIP LEADER\'S SUCCESSOR 2'
    ],
    'OSC': [
        'INCOMING WH OSC INSPECTION TQC',
        'INCOMING WH OSC INSPECTION RQC',
        'HWK OSC/MTL QUALITY IN CHARGE',
        'MTL QUALITY IN CHARGE',
        'INCOMING OSC WH QUALITY IN CHARGE',
        'LEATHER MTL TEAM LEADER',
        'TEXTILE MTL TEAM LEADER',
        'SUBSI MTL TEAM LEADER',
        'INHOUSE HF/ NO-SEW INSPECTION TQC',
        'INHOUSE HF/ NO-SEW INSPECTION RQC',
        'INHOUSE PRINTING INSPECTION TQC',
        'INHOUSE PRINTING INSPECTION RQC'
    ],
    'MTL': [
        'LEATHER TQC',
        'TEXTILE TQC',
        'SUBSI TQC',
        'HAPPO TQC',
        'LINE LEADER(GROUP LEADER SUCCESSOR)'
    ],
    'BOTTOM': [
        'BOTTOM INSPECTION TQC',
        'BOTTOM INSPECTION RQC',
        'BOTTOM REPAIRING & PACKING TQC',
        '1 BUILDING BOTTOM QUALITY IN CHARGE',
        'ALL BUILDING BOTTOM QUALITY IN CHARGE'
    ],
    'AQL': [
        'AQL INSPECTOR',
        'AQL ROOM PACKING TQC',
        'AQL INPUT CARTON TQC',
        'AQL REPORT TEAM',
        'FG WH CARTON PACKING TQC',
        'FG WH INPUT-OUTPUT CARTON RQC'
    ],
    'REPACKING': [
        'REPACKING LINE TQC',
        'REPACKING LINE PACKING TQC',
        'REPACKING LINE REPAIRING TQC',
        'REPACKING AREA INPUT-OUTPUT CARTON TQC',
        'REPACKING LINE PO COMPLETION QUALITY'
    ],
    'QA': [
        'QA TEAM STAFF',
        'QA TEAM HEAD',
        'QA TEAM IN CHARGE',
        'AUDITOR & TRAININER',
        'MODEL MASTER',
        'AUDIT & TRAINING TEAM LEADER'
    ],
    'CUTTING': [
        'CUTTING INSPECTOR',
        'ALL CUTTING BUILDING QUALITY IN CHARGE'
    ],
    'QIP MANAGER & OFFICE & OCPT': [
        'OCPT AND OFFICE TEAM LEADER',
        'OCPT TEAM STAFF',
        'TEAM OPERATION MANAGEMENT',
        'QIP SAP & INCOMING QUALITY REPORT ',
        'HWK QUALITY IN CHARGE'
    ],
    'NEW': [
        'NEW'
    ]
}


class CompleteDashboardBuilder:
    """Build complete HR dashboard with all enhanced features"""

    def __init__(self, target_month: str, language: str = 'ko'):
        """
        Args:
            target_month: 'YYYY-MM' format
            language: 'ko', 'en', or 'vi'
        """
        self.target_month = target_month
        self.language = language
        self.hr_root = Path(__file__).parent.parent.parent

        # Initialize components
        self.collector = MonthlyDataCollector(self.hr_root)
        self.calculator = HRMetricCalculator(self.collector)

        # Data storage
        self.available_months: List[str] = []
        self.month_labels: List[str] = []
        self.monthly_metrics: Dict[str, Dict[str, Any]] = {}
        self.employee_details: List[Dict[str, Any]] = []
        self.modal_data: Dict[str, Any] = {}  # NEW: Store detailed modal data
        self.team_data: Dict[str, Any] = {}  # NEW: Team-based analysis data
        self.hierarchy_data: List[Dict[str, Any]] = []  # NEW: Organization hierarchy data

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

        # Step 3: Collect employee details
        self._collect_employee_details()
        print(f"👥 Employee details: {len(self.employee_details)} employees")

        # Step 4: Collect modal-specific data
        self._collect_modal_data()
        print(f"📋 Modal data collected")

        # Step 4.5: Collect team-based data
        self.team_data = self._collect_team_data()
        print(f"🏢 Team data collected: {len(self.team_data)} teams")

        # Step 4.6: Build organization hierarchy
        self.hierarchy_data = self._build_hierarchy_data()
        print(f"🌳 Organization hierarchy built: {len(self.hierarchy_data)} root nodes")

        # Step 5: Generate HTML
        html = self._generate_html()

        # Step 6: Fix JavaScript template literals (convert {{ to { and }} to })
        # This fixes the issue where JavaScript code has double braces from Python string formatting
        html = html.replace('{{', '{').replace('}}', '}')
        print(f"✅ Dashboard HTML generated")

        return html

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

        # Build attendance lookup
        absent_employees = set()
        unauthorized_absent_employees = set()
        if not attendance_df.empty and 'ID No' in attendance_df.columns:
            if 'compAdd' in attendance_df.columns:
                absent_employees = set(attendance_df[attendance_df['compAdd'] == 'Vắng mặt']['ID No'].unique())
            if 'Reason Description' in attendance_df.columns:
                unauthorized_absent_employees = set(
                    attendance_df[attendance_df['Reason Description'].str.contains('AR1', na=False)]['ID No'].unique()
                )

        for _, row in df.iterrows():
            employee_id = row.get('Employee No', '')
            entrance_date = pd.to_datetime(row.get('Entrance Date', ''), errors='coerce')
            stop_date = pd.to_datetime(row.get('Stop working Date', ''), errors='coerce')

            # Calculate tenure days (from month end)
            tenure_days = 0
            if pd.notna(entrance_date):
                tenure_days = (end_of_month - entrance_date).days

            # Calculate assignment date (entrance + 30 days)
            assignment_date = None
            if pd.notna(entrance_date):
                assignment_date = entrance_date + timedelta(days=30)

            # Determine employee status
            is_active = pd.isna(stop_date) or stop_date > end_of_month
            hired_this_month = pd.notna(entrance_date) and entrance_date.year == year_num and entrance_date.month == month_num
            resigned_this_month = pd.notna(stop_date) and stop_date.year == year_num and stop_date.month == month_num
            under_60_days = tenure_days < 60 if tenure_days > 0 else False
            long_term = (start_of_month - entrance_date).days >= 365 if pd.notna(entrance_date) else False
            perfect_attendance = employee_id not in absent_employees
            has_unauthorized_absence = employee_id in unauthorized_absent_employees

            # Post-assignment resignation (resigned after assignment date)
            post_assignment_resignation = False
            if pd.notna(stop_date) and assignment_date is not None:
                post_assignment_resignation = stop_date >= assignment_date

            self.employee_details.append({
                'employee_id': str(employee_id),
                'employee_name': row.get('Full Name', ''),
                'position': row.get('FINAL QIP POSITION NAME CODE', ''),
                'role_type': row.get('ROLE TYPE STD', ''),
                'entrance_date': entrance_date.strftime('%Y-%m-%d') if pd.notna(entrance_date) else '',
                'stop_date': stop_date.strftime('%Y-%m-%d') if pd.notna(stop_date) else '',
                'assignment_date': assignment_date.strftime('%Y-%m-%d') if assignment_date else '',
                'tenure_days': int(tenure_days) if tenure_days > 0 else 0,
                'is_active': is_active,
                'hired_this_month': hired_this_month,
                'resigned_this_month': resigned_this_month,
                'under_60_days': under_60_days,
                'long_term': long_term,
                'perfect_attendance': perfect_attendance,
                'has_unauthorized_absence': has_unauthorized_absence,
                'post_assignment_resignation': post_assignment_resignation
            })

    def _collect_modal_data(self):
        """Collect detailed data for each modal"""
        data = self.collector.load_month_data(self.target_month)
        attendance_df = data.get('attendance', pd.DataFrame())

        # Modal 2 & 3: Attendance data
        if not attendance_df.empty:
            # Absence details
            if 'compAdd' in attendance_df.columns and 'ID No' in attendance_df.columns:
                absence_records = attendance_df[attendance_df['compAdd'] == 'Vắng mặt'].copy()

                self.modal_data['absence_details'] = []
                for emp_id in absence_records['ID No'].unique():
                    emp_absences = absence_records[absence_records['ID No'] == emp_id]
                    emp_name = emp_absences['Last name'].iloc[0] if 'Last name' in emp_absences.columns else ''

                    self.modal_data['absence_details'].append({
                        'employee_id': str(emp_id),
                        'employee_name': emp_name,
                        'absence_count': len(emp_absences),
                        'dates': emp_absences['Work Date'].tolist() if 'Work Date' in emp_absences.columns else []
                    })

            # Unauthorized absence details
            if 'Reason Description' in attendance_df.columns:
                unauthorized_records = attendance_df[
                    attendance_df['Reason Description'].str.contains('AR1', na=False)
                ].copy()

                self.modal_data['unauthorized_details'] = []
                for emp_id in unauthorized_records['ID No'].unique():
                    emp_records = unauthorized_records[unauthorized_records['ID No'] == emp_id]
                    emp_name = emp_records['Last name'].iloc[0] if 'Last name' in emp_records.columns else ''

                    self.modal_data['unauthorized_details'].append({
                        'employee_id': str(emp_id),
                        'employee_name': emp_name,
                        'unauthorized_count': len(emp_records),
                        'dates': emp_records['Work Date'].tolist() if 'Work Date' in emp_records.columns else [],
                        'reasons': emp_records['Reason Description'].tolist()
                    })

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
        """
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

        # Process each employee
        for idx, row in df.iterrows():
            employee_no = str(row.get('Employee No', ''))
            if not employee_no or employee_no == 'nan':
                continue

            pos1 = str(row.get('QIP POSITION 1ST  NAME', ''))
            pos2 = str(row.get('QIP POSITION 2ND  NAME', ''))
            pos3 = str(row.get('QIP POSITION 3RD  NAME', ''))

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

            # Build employee info
            employee_info = {
                'employee_no': employee_no,
                'full_name': str(row.get('Full Name', '')),
                'position_1st': pos1,
                'position_2nd': pos2,
                'position_3rd': pos3,
                'boss_id': boss_id,
                'role_type': str(row.get('ROLE TYPE STD', '')),
                'entrance_date': row.get('Entrance Date', ''),
                'stop_date': row.get('Stop working Date', '')
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
                    stop_date = pd.to_datetime(stop_date_str, errors='coerce')
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
                absent_employees = set()
                if 'compAdd' in team_attendance.columns:
                    absent_employees = set(team_attendance[team_attendance['compAdd'] == 'Vắng mặt']['ID No'].unique())

                all_team_employees = set(employee_ids_int)
                perfect_attendance_count = len(all_team_employees - absent_employees)

                # High risk employees (attendance < 60%)
                for emp_id in employee_ids_int:
                    emp_records = team_attendance[team_attendance['ID No'] == emp_id]
                    if len(emp_records) > 0:
                        emp_absences = len(emp_records[emp_records['compAdd'] == 'Vắng mặt'])
                        emp_attendance_rate = ((len(emp_records) - emp_absences) / len(emp_records) * 100)
                        if emp_attendance_rate < 60:
                            high_risk_count += 1

        return {
            'total_members': total_members,
            'active_members': active_members,
            'avg_attendance_rate': round(avg_attendance_rate, 1),
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

        # Build employee map
        employee_map = {}

        for idx, row in df.iterrows():
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

    def _generate_html(self) -> str:
        """Generate complete HTML with all components"""
        target_metrics = self.monthly_metrics.get(self.target_month, {})

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR Dashboard - {self.target_month}</title>

    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

    <!-- Plotly.js for Sunburst Chart -->
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>

    {self._generate_css()}
</head>
<body>
    {self._generate_header()}

    <div class="container-xl px-4 py-4">
        <!-- Tab Navigation -->
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
                <button class="nav-link lang-tab" id="orgchart-tab" data-bs-toggle="tab" data-bs-target="#orgchart"
                        type="button" role="tab" aria-controls="orgchart" aria-selected="false"
                        data-ko="🌳 Organization Chart" data-en="🌳 Organization Chart" data-vi="🌳 Sơ đồ tổ chức">
                    🌳 Organization Chart
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link lang-tab" id="teamanalysis-tab" data-bs-toggle="tab" data-bs-target="#teamanalysis"
                        type="button" role="tab" aria-controls="teamanalysis" aria-selected="false"
                        data-ko="🏢 Team Analysis" data-en="🏢 Team Analysis" data-vi="🏢 Phân tích nhóm">
                    🏢 Team Analysis
                </button>
            </li>
        </ul>

        <!-- Tab Content -->
        <div class="tab-content" id="dashboardTabContent">
            <!-- Overview Tab -->
            <div class="tab-pane fade show active" id="overview" role="tabpanel" aria-labelledby="overview-tab">
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

            <!-- Organization Chart Tab -->
            <div class="tab-pane fade" id="orgchart" role="tabpanel" aria-labelledby="orgchart-tab">
                {self._generate_orgchart_tab()}
            </div>

            <!-- Team Analysis Tab -->
            <div class="tab-pane fade" id="teamanalysis" role="tabpanel" aria-labelledby="teamanalysis-tab">
                {self._generate_teamanalysis_tab()}
            </div>
        </div>
    </div>

    {self._generate_modals()}

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
        const hierarchyData =
{self._safe_json_dumps(self.hierarchy_data, ensure_ascii=False, indent=2)}
;

        {self._generate_javascript()}
    </script>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        return html

    def _generate_css(self) -> str:
        """Generate CSS styles"""
        return """
<style>
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --card-shadow: 0 4px 6px rgba(0,0,0,0.07);
        --card-hover-shadow: 0 8px 16px rgba(0,0,0,0.12);
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background: #f8f9fa;
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

    /* Language Switcher */
    .language-switcher {
        position: absolute;
        top: 20px;
        right: 20px;
        display: flex;
        gap: 8px;
        z-index: 10;
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
        transition: all 0.2s ease;
    }

    .modal-table tbody tr:hover {
        background: rgba(102, 126, 234, 0.05);
        transform: scale(1.01);
    }

    .modal-chart-container {
        position: relative;
        height: 300px;
        margin: 20px 0;
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
        transition: all 0.2s ease;
    }

    #employeeTable tbody tr:hover {
        background: rgba(102, 126, 234, 0.05);
        transform: scale(1.01);
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

    #teamDetailsTable tbody tr:hover {
        background-color: #f8f9fa;
    }
</style>
"""

    def _generate_header(self) -> str:
        """Generate dashboard header with language switcher"""
        year, month = self.target_month.split('-')
        return f"""
<div class="dashboard-header">
    <div class="container-xl position-relative">
        <!-- Language Switcher -->
        <div class="language-switcher">
            <button class="lang-btn active" data-lang="ko" onclick="switchLanguage('ko')" title="한국어">🇰🇷</button>
            <button class="lang-btn" data-lang="en" onclick="switchLanguage('en')" title="English">🇺🇸</button>
            <button class="lang-btn" data-lang="vi" onclick="switchLanguage('vi')" title="Tiếng Việt">🇻🇳</button>
        </div>

        <h1 class="lang-title" data-ko="👥 HR 대시보드" data-en="👥 HR Dashboard" data-vi="👥 Bảng điều khiển HR">👥 HR 대시보드</h1>
        <p class="mb-0 lang-subtitle"
           data-ko="인사 현황 대시보드 - {year}년 {int(month)}월"
           data-en="Human Resources Dashboard - {year}/{int(month)}"
           data-vi="Bảng điều khiển Nhân sự - {int(month)}/{year}">
           인사 현황 대시보드 - {year}년 {int(month)}월
        </p>
    </div>
</div>
"""

    def _generate_summary_cards(self, metrics: Dict[str, Any]) -> str:
        """Generate summary cards grid with Vietnamese support"""
        cards = [
            (1, 'total_employees', '총 재직자 수', '명', 'Total Employees', 'Tổng số nhân viên'),
            (2, 'absence_rate', '결근율', '%', 'Absence Rate', 'Tỷ lệ vắng mặt'),
            (3, 'unauthorized_absence_rate', '무단결근율', '%', 'Unauthorized Absence', 'Vắng không phép'),
            (4, 'resignation_rate', '퇴사율', '%', 'Resignation Rate', 'Tỷ lệ nghỉ việc'),
            (5, 'recent_hires', '신규 입사자', '명', 'Recent Hires', 'Nhân viên mới'),
            (6, 'recent_resignations', '최근 퇴사자', '명', 'Recent Resignations', 'Nghỉ việc gần đây'),
            (7, 'under_60_days', '60일 미만', '명', 'Under 60 Days', 'Dưới 60 ngày'),
            (8, 'post_assignment_resignations', '배정 후 퇴사', '명', 'Post-Assignment', 'Sau phân công'),
            (9, 'perfect_attendance', '개근 직원', '명', 'Perfect Attendance', 'Chuyên cần hoàn hảo'),
            (10, 'long_term_employees', '장기근속자', '명', 'Long-term (1yr+)', 'Lâu năm (1 năm+)'),
            (11, 'data_errors', '데이터 오류', '건', 'Data Errors', 'Lỗi dữ liệu')
        ]

        html_parts = ['<div class="row g-3">']

        for num, key, title_ko, unit, title_en, title_vi in cards:
            value = metrics.get(key, 0)
            change = self.calculator.get_month_over_month_change(key, self.target_month)

            change_html = ''
            if change:
                sign = '+' if change['absolute'] >= 0 else ''
                change_class = 'positive' if change['absolute'] >= 0 else 'negative'
                abs_val = round(change["absolute"], 2) if isinstance(change["absolute"], float) else change["absolute"]
                change_html = f'<div class="card-change {change_class}">{sign}{abs_val} ({sign}{change["percentage"]:.1f}%)</div>'

            html_parts.append(f"""
<div class="col-md-6 col-lg-4 col-xl-3">
    <div class="summary-card" onclick="showModal{num}()">
        <div class="card-number">{num}</div>
        <div class="card-title lang-card-title" data-ko="{title_ko}" data-en="{title_en}" data-vi="{title_vi}">
            {title_ko}<br><small class="lang-card-subtitle" data-ko="{title_en}" data-en="{title_en}" data-vi="{title_vi}">{title_en}</small>
        </div>
        <div class="card-value">{value}<small class="ms-2">{unit}</small></div>
        {change_html}
    </div>
</div>
""")

        html_parts.append('</div>')
        return '\n'.join(html_parts)

    def _generate_charts_section(self) -> str:
        """Generate charts section with 2-column grid"""
        return """
<div class="charts-section">
    <h4 class="mb-4 lang-section-title" data-ko="📈 월별 추세 분석" data-en="📈 Monthly Trends" data-vi="📈 Xu hướng hàng tháng">📈 월별 추세 분석</h4>

    <!-- Row 1: Employee Trend & Hires/Resignations -->
    <div class="row">
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="employeeTrendChart"></canvas>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="hiresResignationsChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Row 2: Resignation Rate & Long-term Employees -->
    <div class="row">
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="resignationRateChart"></canvas>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="longTermChart"></canvas>
            </div>
        </div>
    </div>

    <!-- Row 3: Unauthorized Absence & Absence Rate -->
    <div class="row">
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="unauthorizedAbsenceChart"></canvas>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="absenceRateChart"></canvas>
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
</div>
"""

    def _generate_details_tab(self) -> str:
        """Generate employee details table with filters"""
        return """
<div class="details-section">
    <h4 class="mb-4 lang-section-title" data-ko="👥 직원 상세 정보" data-en="👥 Employee Details" data-vi="👥 Chi tiết nhân viên">👥 직원 상세 정보</h4>

    <!-- Filter Buttons -->
    <div class="btn-toolbar mb-4" role="toolbar">
        <div class="btn-group me-2" role="group">
            <button type="button" class="btn btn-outline-primary active" id="filterAll" onclick="filterEmployees('all')">
                <span class="lang-filter" data-ko="전체" data-en="All" data-vi="Tất cả">전체</span>
            </button>
            <button type="button" class="btn btn-outline-success" id="filterActive" onclick="filterEmployees('active')">
                <span class="lang-filter" data-ko="재직자" data-en="Active" data-vi="Đang làm">재직자</span>
            </button>
            <button type="button" class="btn btn-outline-info" id="filterHired" onclick="filterEmployees('hired')">
                <span class="lang-filter" data-ko="신규입사" data-en="New Hires" data-vi="Mới vào">신규입사</span>
            </button>
            <button type="button" class="btn btn-outline-warning" id="filterResigned" onclick="filterEmployees('resigned')">
                <span class="lang-filter" data-ko="퇴사자" data-en="Resigned" data-vi="Đã nghỉ">퇴사자</span>
            </button>
        </div>
        <div class="btn-group me-2" role="group">
            <button type="button" class="btn btn-outline-primary" id="filterPerfect" onclick="filterEmployees('perfect')">
                <span class="lang-filter" data-ko="개근" data-en="Perfect" data-vi="Chuyên cần">개근</span>
            </button>
            <button type="button" class="btn btn-outline-info" id="filterLongTerm" onclick="filterEmployees('longterm')">
                <span class="lang-filter" data-ko="장기근속" data-en="Long-term" data-vi="Lâu năm">장기근속</span>
            </button>
            <button type="button" class="btn btn-outline-secondary" id="filterNew" onclick="filterEmployees('new60')">
                <span class="lang-filter" data-ko="60일 미만" data-en="Under 60d" data-vi="Dưới 60 ngày">60일 미만</span>
            </button>
        </div>
    </div>

    <!-- Search Box and Export Buttons -->
    <div class="row mb-3 align-items-center">
        <div class="col-md-6">
            <input type="text" class="form-control lang-search" id="employeeSearch"
                   placeholder="🔍 Search by ID, Name, Position..." onkeyup="searchEmployees()"
                   data-ko="🔍 사번, 이름, 직급으로 검색..."
                   data-en="🔍 Search by ID, Name, Position..."
                   data-vi="🔍 Tìm theo ID, Tên, Vị trí...">
        </div>
        <div class="col-md-6 text-end">
            <div class="btn-group me-2" role="group">
                <button type="button" class="btn btn-sm btn-outline-success" onclick="exportToCSV()" title="Export to CSV">
                    📥 CSV
                </button>
                <button type="button" class="btn btn-sm btn-outline-primary" onclick="exportToJSON()" title="Export to JSON">
                    📥 JSON
                </button>
                <button type="button" class="btn btn-sm btn-outline-warning" onclick="exportMetricsToJSON()" title="Export Metrics">
                    📊 Metrics
                </button>
            </div>
            <span class="badge bg-info fs-6" id="employeeCount">Total: 0</span>
        </div>
    </div>

    <!-- Employee Table -->
    <div class="table-responsive">
        <table class="table table-striped table-hover" id="employeeTable">
            <thead class="table-light sticky-top">
                <tr>
                    <th onclick="sortTable(0)"><span class="lang-th" data-ko="사번" data-en="ID" data-vi="Mã NV">사번</span> ▼</th>
                    <th onclick="sortTable(1)"><span class="lang-th" data-ko="이름" data-en="Name" data-vi="Tên">이름</span> ▼</th>
                    <th onclick="sortTable(2)"><span class="lang-th" data-ko="직급" data-en="Position" data-vi="Vị trí">직급</span> ▼</th>
                    <th onclick="sortTable(3)"><span class="lang-th" data-ko="유형" data-en="Type" data-vi="Loại">유형</span> ▼</th>
                    <th onclick="sortTable(4)"><span class="lang-th" data-ko="입사일" data-en="Entrance" data-vi="Ngày vào">입사일</span> ▼</th>
                    <th onclick="sortTable(5)"><span class="lang-th" data-ko="퇴사일" data-en="Stop" data-vi="Ngày nghỉ">퇴사일</span> ▼</th>
                    <th onclick="sortTable(6)"><span class="lang-th" data-ko="재직기간" data-en="Tenure" data-vi="Thâm niên">재직기간</span> ▼</th>
                    <th><span class="lang-th" data-ko="상태" data-en="Status" data-vi="Trạng thái">상태</span></th>
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
            <button type="button" class="btn btn-sm btn-outline-primary active" onclick="setOrgChartView('tree')" id="viewTree">
                <span class="lang-btn" data-ko="🌲 트리뷰" data-en="🌲 Tree View" data-vi="🌲 Xem cây">🌲 트리뷰</span>
            </button>
            <button type="button" class="btn btn-sm btn-outline-info" onclick="setOrgChartView('heatmap')" id="viewHeatmap">
                <span class="lang-btn" data-ko="🗺️ 히트맵" data-en="🗺️ Heatmap" data-vi="🗺️ Bản đồ nhiệt">🗺️ 히트맵</span>
            </button>
            <button type="button" class="btn btn-sm btn-outline-success" onclick="setOrgChartView('comparison')" id="viewComparison">
                <span class="lang-btn" data-ko="📊 비교뷰" data-en="📊 Comparison" data-vi="📊 So sánh">📊 비교뷰</span>
            </button>
        </div>
    </div>

    <!-- Organization Chart Tree View -->
    <div id="orgChartTree" class="org-tree-container">
        <!-- Populated by JavaScript -->
    </div>

    <!-- Organization Chart Heatmap View -->
    <div id="orgChartHeatmap" class="org-heatmap-container" style="display: none;">
        <!-- Populated by JavaScript -->
    </div>

    <!-- Organization Chart Comparison View -->
    <div id="orgChartComparison" class="org-comparison-container" style="display: none;">
        <!-- Populated by JavaScript -->
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
            <select class="form-select" id="teamPositionSelect" onchange="filterTeamsByPosition()">
                <option value="all" selected>전체 직급</option>
                <!-- Populated by JavaScript -->
            </select>
            <select class="form-select ms-2" id="teamNameSelect" onchange="selectTeam()">
                <option value="all" selected>팀 선택...</option>
                <!-- Populated by JavaScript -->
            </select>
        </div>
    </div>

    <!-- Team Overview KPI Cards -->
    <div class="row mb-4" id="teamOverviewCards">
        <div class="col-md-3">
            <div class="card border-primary h-100">
                <div class="card-body text-center">
                    <h6 class="text-muted mb-2">총 팀 수</h6>
                    <h2 class="mb-0" id="totalTeamsCount">0</h2>
                    <small class="text-muted">Total Teams</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-success h-100">
                <div class="card-body text-center">
                    <h6 class="text-muted mb-2">총 팀원 수</h6>
                    <h2 class="mb-0" id="totalTeamMembersCount">0</h2>
                    <small class="text-muted">Total Members</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-info h-100">
                <div class="card-body text-center">
                    <h6 class="text-muted mb-2">평균 출근율</h6>
                    <h2 class="mb-0" id="avgTeamAttendance">0%</h2>
                    <small class="text-muted">Average Attendance</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-warning h-100">
                <div class="card-body text-center">
                    <h6 class="text-muted mb-2">최고 성과 팀</h6>
                    <h5 class="mb-0" id="topPerformingTeam">-</h5>
                    <small class="text-muted">Top Team</small>
                </div>
            </div>
        </div>
    </div>

    <!-- Team Performance Charts -->
    <div class="row mb-4">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">팀별 출근율 비교</h6>
                </div>
                <div class="card-body">
                    <canvas id="teamAttendanceComparisonChart" height="250"></canvas>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">팀별 인원 분포</h6>
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
                    <h6 class="mb-0">팀별 TYPE 분포</h6>
                </div>
                <div class="card-body">
                    <canvas id="teamTypeBreakdownChart" height="250"></canvas>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">팀별 근속연수</h6>
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
            <h6 class="mb-0">팀 상세 정보</h6>
            <button class="btn btn-sm btn-outline-primary" onclick="exportTeamAnalysis()">
                📥 내보내기
            </button>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover" id="teamDetailsTable">
                    <thead class="table-light">
                        <tr>
                            <th>직급</th>
                            <th>팀명</th>
                            <th>팀원 수</th>
                            <th>평균 출근율</th>
                            <th>개근자</th>
                            <th>고위험</th>
                            <th>평균 근속</th>
                            <th>액션</th>
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

    def _generate_modals(self) -> str:
        """Generate modals with detailed data, charts, and language support"""
        modals_html = []

        # Modal 1: Total Employees (Enhanced with 3 charts)
        modals_html.append("""
<div class="modal fade" id="modal1" tabindex="-1">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="총 재직자 수 상세 분석" data-en="Total Employees Analysis" data-vi="Phân tích số nhân viên">총 재직자 수 상세 분석</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body" id="modalContent1">
                <!-- Charts will be dynamically generated by JavaScript -->
                <div class="modal-chart-container mb-4">
                    <canvas id="modalChart1_monthly"></canvas>
                </div>
                <div class="modal-chart-container mb-4">
                    <canvas id="modalChart1_weekly"></canvas>
                </div>
                <div class="modal-chart-container mb-4">
                    <canvas id="modalChart1_teams"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 2: Absence Rate
        modals_html.append("""
<div class="modal fade" id="modal2" tabindex="-1">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="결근율" data-en="Absence Rate" data-vi="Tỷ lệ vắng mặt">결근율</h5>
                <div class="d-flex align-items-center gap-2">
                    <select class="form-select form-select-sm" id="modalTeamFilter2" onchange="filterModalByTeam(2)" style="width: 200px;">
                        <option value="all" class="lang-option" data-ko="전체 팀" data-en="All Teams" data-vi="Tất cả nhóm">전체 팀</option>
                        <!-- Populated by JavaScript -->
                    </select>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
            </div>
            <div class="modal-body">
                <h6 class="lang-calc-method" data-ko="📋 계산 방법" data-en="📋 Calculation Method" data-vi="📋 Phương pháp tính">📋 계산 방법</h6>
                <p class="lang-calc-desc" data-ko="결근율 (%) = (결근 레코드 수 / 전체 출근 레코드 수) × 100"
                   data-en="Absence Rate (%) = (Absence Records / Total Attendance Records) × 100"
                   data-vi="Tỷ lệ vắng mặt (%) = (Số lần vắng / Tổng số bản ghi) × 100">
                   결근율 (%) = (결근 레코드 수 / 전체 출근 레코드 수) × 100
                </p>
                <hr>
                <div id="modalContent2">
                    <div class="modal-chart-container">
                        <canvas id="modalChart2"></canvas>
                    </div>
                    <table class="table table-sm table-hover modal-table" id="modalTable2">
                        <thead>
                            <tr>
                                <th onclick="sortModalTable(2, 0)" class="lang-th" data-ko="사번" data-en="ID" data-vi="Mã NV">사번 <span class="sort-icon">▼</span></th>
                                <th onclick="sortModalTable(2, 1)" class="lang-th" data-ko="이름" data-en="Name" data-vi="Tên">이름 <span class="sort-icon">▼</span></th>
                                <th onclick="sortModalTable(2, 2)" class="lang-th" data-ko="결근 횟수" data-en="Absence Count" data-vi="Số lần vắng">결근 횟수 <span class="sort-icon">▼</span></th>
                            </tr>
                        </thead>
                        <tbody id="modalTableBody2"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 3: Unauthorized Absence
        modals_html.append("""
<div class="modal fade" id="modal3" tabindex="-1">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="무단결근율" data-en="Unauthorized Absence Rate" data-vi="Vắng không phép">무단결근율</h5>
                <div class="d-flex align-items-center gap-2">
                    <select class="form-select form-select-sm" id="modalTeamFilter3" onchange="filterModalByTeam(3)" style="width: 200px;">
                        <option value="all" class="lang-option" data-ko="전체 팀" data-en="All Teams" data-vi="Tất cả nhóm">전체 팀</option>
                    </select>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
            </div>
            <div class="modal-body">
                <h6 class="lang-calc-method" data-ko="📋 계산 방법" data-en="📋 Calculation Method" data-vi="📋 Phương pháp tính">📋 계산 방법</h6>
                <p class="lang-calc-desc" data-ko="무단결근율 (%) = (무단결근 레코드 수 / 전체 출근 레코드 수) × 100 (AR1 코드)"
                   data-en="Unauthorized Absence (%) = (Unauthorized Records / Total Records) × 100 (AR1 code)"
                   data-vi="Vắng không phép (%) = (Số lần vắng không phép / Tổng số bản ghi) × 100 (Mã AR1)">
                   무단결근율 (%) = (무단결근 레코드 수 / 전체 출근 레코드 수) × 100
                </p>
                <hr>
                <div id="modalContent3">
                    <div class="modal-chart-container">
                        <canvas id="modalChart3"></canvas>
                    </div>
                    <table class="table table-sm table-hover modal-table" id="modalTable3">
                        <thead>
                            <tr>
                                <th onclick="sortModalTable(3, 0)" class="lang-th" data-ko="사번" data-en="ID" data-vi="Mã NV">사번 <span class="sort-icon">▼</span></th>
                                <th onclick="sortModalTable(3, 1)" class="lang-th" data-ko="이름" data-en="Name" data-vi="Tên">이름 <span class="sort-icon">▼</span></th>
                                <th onclick="sortModalTable(3, 2)" class="lang-th" data-ko="무단결근 횟수" data-en="Unauthorized Count" data-vi="Số lần vắng không phép">무단결근 횟수 <span class="sort-icon">▼</span></th>
                            </tr>
                        </thead>
                        <tbody id="modalTableBody3"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Modal 4-11: Similar structure for other modals
        modal_configs = [
            (4, "퇴사율", "Resignation Rate", "Tỷ lệ nghỉ việc", "resignation_rate"),
            (5, "신규 입사자", "Recent Hires", "Nhân viên mới", "recent_hires"),
            (6, "최근 퇴사자", "Recent Resignations", "Nghỉ việc gần đây", "recent_resignations"),
            (7, "60일 미만 재직자", "Under 60 Days", "Dưới 60 ngày", "under_60_days"),
            (8, "배정 후 퇴사자", "Post-Assignment Resignations", "Nghỉ sau phân công", "post_assignment"),
            (9, "개근 직원", "Perfect Attendance", "Chuyên cần hoàn hảo", "perfect_attendance"),
            (10, "장기근속자 (1년 이상)", "Long-term Employees (1yr+)", "Nhân viên lâu năm (1 năm+)", "long_term"),
            (11, "데이터 오류", "Data Errors", "Lỗi dữ liệu", "data_errors")
        ]

        for modal_num, title_ko, title_en, title_vi, metric_key in modal_configs:
            modals_html.append(f"""
<div class="modal fade" id="modal{modal_num}" tabindex="-1">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title lang-modal-title" data-ko="{title_ko}" data-en="{title_en}" data-vi="{title_vi}">{title_ko}</h5>
                <div class="d-flex align-items-center gap-2">
                    <select class="form-select form-select-sm" id="modalTeamFilter{modal_num}" onchange="filterModalByTeam({modal_num})" style="width: 200px;">
                        <option value="all" class="lang-option" data-ko="전체 팀" data-en="All Teams" data-vi="Tất cả nhóm">전체 팀</option>
                    </select>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
            </div>
            <div class="modal-body">
                <div id="modalContent{modal_num}">
                    <div class="modal-chart-container">
                        <canvas id="modalChart{modal_num}"></canvas>
                    </div>
                    <table class="table table-sm table-hover modal-table" id="modalTable{modal_num}">
                        <thead>
                            <tr id="modalTableHeader{modal_num}">
                                <!-- Populated by JavaScript -->
                            </tr>
                        </thead>
                        <tbody id="modalTableBody{modal_num}"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
""")

        # Team Dashboard Modal (1st Level Modal)
        modals_html.append("""
<div class="modal fade" id="teamDashboardModal" tabindex="-1">
    <div class="modal-dialog modal-xl">
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
                                <th>사번</th>
                                <th>이름</th>
                                <th>직급</th>
                                <th>입사일</th>
                                <th>재직기간</th>
                                <th>출근율</th>
                                <th>상세</th>
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

        return '\n'.join(modals_html)

    def _generate_javascript(self) -> str:
        """Generate JavaScript for charts, interactivity, and modal management"""
        return """
// ============================================
// Language Switching
// ============================================

let currentLanguage = 'ko';

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

    console.log(`✅ Language switched to: ${lang}`);
}

// Load saved language preference on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedLang = localStorage.getItem('dashboard_language');
    if (savedLang && ['ko', 'en', 'vi'].includes(savedLang)) {
        switchLanguage(savedLang);
    }
});

// ============================================
// Helper Functions
// ============================================

function getTrendData(metricKey) {
    return availableMonths.map(month => monthlyMetrics[month][metricKey]);
}

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

    // Count by Position 1 and Position 2
    Object.values(teamData).forEach(team => {{
        const teamName = team.name;
        const memberCount = team.members ? team.members.length : 0;

        if (memberCount > 0) {{
            position1Counts[teamName] = (position1Counts[teamName] || 0) + memberCount;

            // Count sub-teams (Position 2)
            if (team.sub_teams) {{
                if (!position1ToPosition2Map[teamName]) {{
                    position1ToPosition2Map[teamName] = [];
                }}

                Object.values(team.sub_teams).forEach(subTeam => {{
                    const subTeamName = subTeam.name;
                    const subMemberCount = subTeam.members ? subTeam.members.length : 0;
                    position2Counts[subTeamName] = (position2Counts[subTeamName] || 0) + subMemberCount;
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
// Main Trend Charts
// ============================================

// Chart 1: Employee Trend
new Chart(document.getElementById('employeeTrendChart'), {
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
new Chart(document.getElementById('hiresResignationsChart'), {
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
new Chart(document.getElementById('resignationRateChart'), {
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
new Chart(document.getElementById('longTermChart'), {
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

// Chart 5: Unauthorized Absence Rate
new Chart(document.getElementById('unauthorizedAbsenceChart'), {
    type: 'bar',
    data: {
        labels: monthLabels,
        datasets: [{
            label: '무단 결근율 (%) / Unauthorized Absence Rate',
            data: getTrendData('unauthorized_absence_rate'),
            backgroundColor: 'rgba(255, 99, 132, 0.7)',
            borderColor: '#ff6384',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'bottom' },
            tooltip: {
                callbacks: {
                    label: function(context) {
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
new Chart(document.getElementById('absenceRateChart'), {
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
// Modal Management
// ============================================

let modalCharts = {};

// Modal 1: Total Employees
function showModal1() {
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

    // 1. 월별 트렌드 차트 (Bar Chart)
    const monthLabels = metricsArray.map(m => m.month_label);
    const monthEmployees = metricsArray.map(m => m.total_employees || 0);

    const ctx1 = document.getElementById('modalChart1_monthly').getContext('2d');
    modalCharts['modal1_monthly'] = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: monthLabels,
            datasets: [{
                label: '총인원',
                data: monthEmployees,
                backgroundColor: ['#FFEAA7', '#74B9FF', '#A29BFE', '#FD79A8', '#FDCB6E', '#45B7D1']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '월별 총인원 비교',
                    align: 'start',
                    font: { size: 18, weight: 600 },
                    padding: { bottom: 10 },
                    color: '#333'
                },
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // 2. 주차별 트렌드 차트 (Line Chart with Trendline)
    // Collect all weekly data points across months
    const allWeeklyData = [];
    metricsArray.forEach((month, monthIdx) => {
        if (month.weekly_metrics) {
            month.weekly_metrics.forEach((week, weekIdx) => {
                allWeeklyData.push({
                    label: `${month.month_label.substring(5)} W${weekIdx + 1}`,
                    value: week.total_employees || 0
                });
            });
        }
    });

    const weekLabels = allWeeklyData.map(w => w.label);
    const weekValues = allWeeklyData.map(w => w.value);

    // Calculate trendline (linear regression)
    const n = weekValues.length;
    const xValues = Array.from({ length: n }, (_, i) => i);
    const sumX = xValues.reduce((a, b) => a + b, 0);
    const sumY = weekValues.reduce((a, b) => a + b, 0);
    const sumXY = xValues.reduce((sum, x, i) => sum + x * weekValues[i], 0);
    const sumX2 = xValues.reduce((sum, x) => sum + x * x, 0);
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    const trendlineData = xValues.map(x => slope * x + intercept);

    const ctx2 = document.getElementById('modalChart1_weekly').getContext('2d');
    modalCharts['modal1_weekly'] = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: weekLabels,
            datasets: [
                {
                    label: '주차별 총인원',
                    data: weekValues,
                    borderColor: '#FF6B6B',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    tension: 0.3,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: '추세선',
                    data: trendlineData,
                    borderColor: '#45B7D1',
                    borderDash: [10, 5],
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '주차별 총인원 트렌드',
                    align: 'start',
                    font: { size: 18, weight: 600 },
                    padding: { bottom: 10 },
                    color: '#333'
                }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // 3. 팀별 인원 분포 (Horizontal Bar Chart)
    const latestMonth = metricsArray[metricsArray.length - 1];
    const teamDistribution = Object.entries(teamData)
        .map(([name, data]) => ({
            name: name,
            total: data.members ? data.members.length : 0,
            percentage: ((data.members ? data.members.length : 0) / latestMonth.total_employees * 100).toFixed(1)
        }))
        .sort((a, b) => b.total - a.total);

    const teamNames = teamDistribution.map(t => t.name);
    const teamCounts = teamDistribution.map(t => t.total);
    const teamPercentages = teamDistribution.map(t => t.percentage);
    const teamColors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2", "#FF9FF3"];

    const ctx3 = document.getElementById('modalChart1_teams').getContext('2d');
    modalCharts['modal1_teams'] = new Chart(ctx3, {
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
                    showTeamDetailModal(teamName);
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
}

// Modal 2: Absence Rate
function showModal2(teamFilter = 'all') {
    let absenceData = modalData.absence_details || [];

    // Filter by team if specified
    if (teamFilter && teamFilter !== 'all') {
        absenceData = absenceData.filter(a => {
            const emp = employeeDetails.find(e => e.employee_no === a.employee_id);
            return emp && emp.team_name === teamFilter;
        });
    }

    const tbody = document.getElementById('modalTableBody2');
    tbody.innerHTML = absenceData.map(a => `
        <tr>
            <td>${a.employee_id}</td>
            <td>${a.employee_name}</td>
            <td>${a.absence_count}</td>
        </tr>
    `).join('');

    const modal = new bootstrap.Modal(document.getElementById('modal2'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(2);

    setTimeout(() => {
        if (modalCharts['modal2']) modalCharts['modal2'].destroy();

        // Top 10 absent employees chart
        const top10 = absenceData.sort((a, b) => b.absence_count - a.absence_count).slice(0, 10);

        const ctx = document.getElementById('modalChart2').getContext('2d');
        modalCharts['modal2'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: top10.map(a => a.employee_name),
                datasets: [{
                    label: '결근 횟수 / Absence Count',
                    data: top10.map(a => a.absence_count),
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: '#dc3545',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }, 300);
}

// Modal 3: Unauthorized Absence
function showModal3(teamFilter = 'all') {
    let unauthorizedData = modalData.unauthorized_details || [];

    // Filter by team if specified
    if (teamFilter && teamFilter !== 'all') {
        unauthorizedData = unauthorizedData.filter(u => {
            const emp = employeeDetails.find(e => e.employee_no === u.employee_id);
            return emp && emp.team_name === teamFilter;
        });
    }

    const tbody = document.getElementById('modalTableBody3');
    tbody.innerHTML = unauthorizedData.map(u => `
        <tr>
            <td>${u.employee_id}</td>
            <td>${u.employee_name}</td>
            <td>${u.unauthorized_count}</td>
        </tr>
    `).join('');

    const modal = new bootstrap.Modal(document.getElementById('modal3'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(3);

    setTimeout(() => {
        if (modalCharts['modal3']) modalCharts['modal3'].destroy();

        const top10 = unauthorizedData.sort((a, b) => b.unauthorized_count - a.unauthorized_count).slice(0, 10);

        const ctx = document.getElementById('modalChart3').getContext('2d');
        modalCharts['modal3'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: top10.map(u => u.employee_name),
                datasets: [{
                    label: '무단결근 횟수 / Unauthorized Absence',
                    data: top10.map(u => u.unauthorized_count),
                    backgroundColor: 'rgba(255, 159, 64, 0.7)',
                    borderColor: '#ff9f40',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }, 300);
}

// Modal 4: Resignation Rate
function showModal4() {
    const employees = employeeDetails.filter(e => e.resigned_this_month);

    const tbody = document.getElementById('modalTableBody4');
    const thead = document.getElementById('modalTableHeader4');

    thead.innerHTML = `
        <th onclick="sortModalTable(4, 0)">사번 / ID <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(4, 1)">이름 / Name <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(4, 2)">직급 / Position <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(4, 3)">입사일 / Entrance <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(4, 4)">퇴사일 / Stop <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(4, 5)">재직기간 / Tenure <span class="sort-icon">▼</span></th>
    `;

    tbody.innerHTML = employees.map(e => `
        <tr>
            <td>${e.employee_id}</td>
            <td>${e.employee_name}</td>
            <td>${e.position}</td>
            <td>${e.entrance_date}</td>
            <td>${e.stop_date}</td>
            <td>${e.tenure_days}일</td>
        </tr>
    `).join('');

    const modal = new bootstrap.Modal(document.getElementById('modal4'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(4);

    setTimeout(() => {
        if (modalCharts['modal4']) modalCharts['modal4'].destroy();

        const ctx = document.getElementById('modalChart4').getContext('2d');
        modalCharts['modal4'] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: '월별 퇴사율 / Monthly Resignation Rate',
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
                scales: { y: { beginAtZero: true, ticks: { callback: v => v + '%' } } }
            }
        });
    }, 300);
}

// Modal 5: Recent Hires
function showModal5() {
    const employees = employeeDetails.filter(e => e.hired_this_month);

    const tbody = document.getElementById('modalTableBody5');
    const thead = document.getElementById('modalTableHeader5');

    thead.innerHTML = `
        <th onclick="sortModalTable(5, 0)">사번 / ID <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(5, 1)">이름 / Name <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(5, 2)">직급 / Position <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(5, 3)">유형 / Type <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(5, 4)">입사일 / Entrance <span class="sort-icon">▼</span></th>
    `;

    tbody.innerHTML = employees.map(e => `
        <tr>
            <td>${e.employee_id}</td>
            <td>${e.employee_name}</td>
            <td>${e.position}</td>
            <td>${e.role_type}</td>
            <td>${e.entrance_date}</td>
        </tr>
    `).join('');

    const modal = new bootstrap.Modal(document.getElementById('modal5'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(5);

    setTimeout(() => {
        if (modalCharts['modal5']) modalCharts['modal5'].destroy();

        const ctx = document.getElementById('modalChart5').getContext('2d');
        modalCharts['modal5'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: '월별 신규 입사자 / Monthly New Hires',
                    data: getTrendData('recent_hires'),
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: '#28a745',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }, 300);
}

// Modal 6: Recent Resignations
function showModal6() {
    const employees = employeeDetails.filter(e => e.resigned_this_month);

    const tbody = document.getElementById('modalTableBody6');
    const thead = document.getElementById('modalTableHeader6');

    thead.innerHTML = `
        <th onclick="sortModalTable(6, 0)">사번 / ID <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(6, 1)">이름 / Name <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(6, 2)">직급 / Position <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(6, 3)">입사일 / Entrance <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(6, 4)">퇴사일 / Stop <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(6, 5)">재직기간 / Tenure <span class="sort-icon">▼</span></th>
    `;

    tbody.innerHTML = employees.map(e => `
        <tr>
            <td>${e.employee_id}</td>
            <td>${e.employee_name}</td>
            <td>${e.position}</td>
            <td>${e.entrance_date}</td>
            <td>${e.stop_date}</td>
            <td>${e.tenure_days}일</td>
        </tr>
    `).join('');

    const modal = new bootstrap.Modal(document.getElementById('modal6'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(6);

    setTimeout(() => {
        if (modalCharts['modal6']) modalCharts['modal6'].destroy();

        const ctx = document.getElementById('modalChart6').getContext('2d');
        modalCharts['modal6'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: '월별 퇴사자 / Monthly Resignations',
                    data: getTrendData('recent_resignations'),
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: '#dc3545',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }, 300);
}

// Modal 7: Under 60 Days
function showModal7() {
    const employees = employeeDetails.filter(e => e.under_60_days && e.is_active);

    const tbody = document.getElementById('modalTableBody7');
    const thead = document.getElementById('modalTableHeader7');

    thead.innerHTML = `
        <th onclick="sortModalTable(7, 0)">사번 / ID <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(7, 1)">이름 / Name <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(7, 2)">직급 / Position <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(7, 3)">입사일 / Entrance <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(7, 4)">재직기간 / Tenure <span class="sort-icon">▼</span></th>
    `;

    tbody.innerHTML = employees.map(e => `
        <tr>
            <td>${e.employee_id}</td>
            <td>${e.employee_name}</td>
            <td>${e.position}</td>
            <td>${e.entrance_date}</td>
            <td>${e.tenure_days}일</td>
        </tr>
    `).join('');

    const modal = new bootstrap.Modal(document.getElementById('modal7'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(7);

    setTimeout(() => {
        if (modalCharts['modal7']) modalCharts['modal7'].destroy();

        const ctx = document.getElementById('modalChart7').getContext('2d');
        modalCharts['modal7'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: '60일 미만 재직자 / Under 60 Days',
                    data: getTrendData('under_60_days'),
                    backgroundColor: 'rgba(255, 193, 7, 0.7)',
                    borderColor: '#ffc107',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }, 300);
}

// Modal 8: Post-Assignment Resignations
function showModal8() {
    const employees = employeeDetails.filter(e => e.post_assignment_resignation);

    const tbody = document.getElementById('modalTableBody8');
    const thead = document.getElementById('modalTableHeader8');

    thead.innerHTML = `
        <th onclick="sortModalTable(8, 0)">사번 / ID <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(8, 1)">이름 / Name <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(8, 2)">입사일 / Entrance <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(8, 3)">배정일 / Assignment <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(8, 4)">퇴사일 / Stop <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(8, 5)">재직기간 / Tenure <span class="sort-icon">▼</span></th>
    `;

    tbody.innerHTML = employees.map(e => `
        <tr>
            <td>${e.employee_id}</td>
            <td>${e.employee_name}</td>
            <td>${e.entrance_date}</td>
            <td>${e.assignment_date}</td>
            <td>${e.stop_date}</td>
            <td>${e.tenure_days}일</td>
        </tr>
    `).join('');

    const modal = new bootstrap.Modal(document.getElementById('modal8'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(8);

    setTimeout(() => {
        if (modalCharts['modal8']) modalCharts['modal8'].destroy();

        const ctx = document.getElementById('modalChart8').getContext('2d');
        modalCharts['modal8'] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['배정 후 퇴사 / Post-Assignment', '기타 퇴사 / Other Resignations'],
                datasets: [{
                    data: [
                        employees.length,
                        employeeDetails.filter(e => e.resigned_this_month && !e.post_assignment_resignation).length
                    ],
                    backgroundColor: ['#ff6384', '#36a2eb']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }, 300);
}

// Modal 9: Perfect Attendance
function showModal9() {
    const employees = employeeDetails.filter(e => e.perfect_attendance && e.is_active);

    const tbody = document.getElementById('modalTableBody9');
    const thead = document.getElementById('modalTableHeader9');

    thead.innerHTML = `
        <th onclick="sortModalTable(9, 0)">사번 / ID <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(9, 1)">이름 / Name <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(9, 2)">직급 / Position <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(9, 3)">유형 / Type <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(9, 4)">입사일 / Entrance <span class="sort-icon">▼</span></th>
    `;

    tbody.innerHTML = employees.map(e => `
        <tr>
            <td>${e.employee_id}</td>
            <td>${e.employee_name}</td>
            <td>${e.position}</td>
            <td>${e.role_type}</td>
            <td>${e.entrance_date}</td>
        </tr>
    `).join('');

    const modal = new bootstrap.Modal(document.getElementById('modal9'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(9);

    setTimeout(() => {
        if (modalCharts['modal9']) modalCharts['modal9'].destroy();

        const ctx = document.getElementById('modalChart9').getContext('2d');
        modalCharts['modal9'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: '개근 직원 / Perfect Attendance',
                    data: getTrendData('perfect_attendance'),
                    backgroundColor: 'rgba(75, 192, 192, 0.7)',
                    borderColor: '#4bc0c0',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }, 300);
}

// Modal 10: Long-term Employees
function showModal10() {
    const employees = employeeDetails.filter(e => e.long_term && e.is_active);

    const tbody = document.getElementById('modalTableBody10');
    const thead = document.getElementById('modalTableHeader10');

    thead.innerHTML = `
        <th onclick="sortModalTable(10, 0)">사번 / ID <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(10, 1)">이름 / Name <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(10, 2)">직급 / Position <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(10, 3)">유형 / Type <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(10, 4)">입사일 / Entrance <span class="sort-icon">▼</span></th>
        <th onclick="sortModalTable(10, 5)">재직기간 / Tenure <span class="sort-icon">▼</span></th>
    `;

    tbody.innerHTML = employees.map(e => `
        <tr>
            <td>${e.employee_id}</td>
            <td>${e.employee_name}</td>
            <td>${e.position}</td>
            <td>${e.role_type}</td>
            <td>${e.entrance_date}</td>
            <td>${e.tenure_days}일 (${Math.floor(e.tenure_days/365)}년)</td>
        </tr>
    `).join('');

    const modal = new bootstrap.Modal(document.getElementById('modal10'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(10);

    setTimeout(() => {
        if (modalCharts['modal10']) modalCharts['modal10'].destroy();

        const ctx = document.getElementById('modalChart10').getContext('2d');
        modalCharts['modal10'] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: '장기근속자 (1년+) / Long-term Employees',
                    data: getTrendData('long_term_employees'),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }, 300);
}

// Modal 11: Data Errors
function showModal11() {
    const modal = new bootstrap.Modal(document.getElementById('modal11'));
    modal.show();

    // Populate team filter dropdown
    populateTeamFilter(11);

    setTimeout(() => {
        if (modalCharts['modal11']) modalCharts['modal11'].destroy();

        const ctx = document.getElementById('modalChart11').getContext('2d');
        modalCharts['modal11'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: '데이터 오류 / Data Errors',
                    data: getTrendData('data_errors'),
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: '#dc3545',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }, 300);
}

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

        case 9: // Perfect Attendance
            filteredEmployees = filteredEmployees.filter(e => e.perfect_attendance);
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
    }

    // Update chart with filtered data count
    updateModalChart(modalNum, filteredEmployees.length);
}

// Update modal chart with filtered data
function updateModalChart(modalNum, filteredCount) {
    if (modalCharts[`modal${modalNum}`]) {
        // For simplicity, we'll just note that the chart reflects filtered data
        // Full chart re-rendering with filtered trend data would require more complex logic
        console.log(`Modal ${modalNum} filtered to ${filteredCount} records`);
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
let currentSortColumn = -1;
let currentSortAsc = true;

function renderEmployeeTable(employees = null) {
    const tbody = document.getElementById('employeeTableBody');
    if (!tbody) return;

    const displayEmployees = employees || employeeDetails;

    if (displayEmployees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">직원이 없습니다.</td></tr>';
        updateEmployeeCount(0);
        return;
    }

    let html = '';
    displayEmployees.forEach(emp => {
        const tenureMonths = Math.floor((emp.tenure_days || 0) / 30);
        const tenureDisplay = emp.tenure_days ? `${emp.tenure_days}일 (${tenureMonths}개월)` : '-';

        let statusBadges = [];
        if (emp.is_active) {
            statusBadges.push('<span class="badge bg-success badge-status">재직</span>');
        } else {
            statusBadges.push('<span class="badge bg-secondary badge-status">퇴사</span>');
        }
        if (emp.hired_this_month) {
            statusBadges.push('<span class="badge bg-info badge-status">신입</span>');
        }
        if (emp.perfect_attendance) {
            statusBadges.push('<span class="badge bg-primary badge-status">개근</span>');
        }
        if (emp.long_term) {
            statusBadges.push('<span class="badge bg-warning badge-status">장기</span>');
        }

        html += `
            <tr>
                <td>${emp.employee_id || ''}</td>
                <td>${emp.employee_name || ''}</td>
                <td>${emp.position || ''}</td>
                <td><span class="badge bg-light text-dark">${emp.role_type || ''}</span></td>
                <td>${emp.entrance_date || ''}</td>
                <td>${emp.stop_date || '-'}</td>
                <td>${tenureDisplay}</td>
                <td>${statusBadges.join(' ')}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
    updateEmployeeCount(displayEmployees.length);
}

function filterEmployees(filter) {
    currentFilter = filter;

    document.querySelectorAll('.btn-group button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`filter${filter.charAt(0).toUpperCase() + filter.slice(1)}`).classList.add('active');

    let filtered = employeeDetails;

    switch(filter) {
        case 'all': filtered = employeeDetails; break;
        case 'active': filtered = employeeDetails.filter(e => e.is_active); break;
        case 'hired': filtered = employeeDetails.filter(e => e.hired_this_month); break;
        case 'resigned': filtered = employeeDetails.filter(e => e.resigned_this_month); break;
        case 'perfect': filtered = employeeDetails.filter(e => e.perfect_attendance); break;
        case 'longterm': filtered = employeeDetails.filter(e => e.long_term); break;
        case 'new60': filtered = employeeDetails.filter(e => e.under_60_days); break;
    }

    renderEmployeeTable(filtered);
}

function searchEmployees() {
    const searchTerm = document.getElementById('employeeSearch').value.toLowerCase();

    if (!searchTerm) {
        renderEmployeeTable(employeeDetails);
        return;
    }

    const filtered = employeeDetails.filter(emp => {
        return (
            (emp.employee_id && emp.employee_id.toLowerCase().includes(searchTerm)) ||
            (emp.employee_name && emp.employee_name.toLowerCase().includes(searchTerm)) ||
            (emp.position && emp.position.toLowerCase().includes(searchTerm)) ||
            (emp.role_type && emp.role_type.toLowerCase().includes(searchTerm))
        );
    });

    renderEmployeeTable(filtered);
}

function sortTable(columnIndex) {
    const tbody = document.getElementById('employeeTableBody');
    const rows = Array.from(tbody.getElementsByTagName('tr'));

    if (currentSortColumn === columnIndex) {
        currentSortAsc = !currentSortAsc;
    } else {
        currentSortColumn = columnIndex;
        currentSortAsc = true;
    }

    rows.sort((a, b) => {
        const aText = a.getElementsByTagName('td')[columnIndex].textContent.trim();
        const bText = b.getElementsByTagName('td')[columnIndex].textContent.trim();

        if (columnIndex === 6) {
            const aNum = parseInt(aText) || 0;
            const bNum = parseInt(bText) || 0;
            return currentSortAsc ? aNum - bNum : bNum - aNum;
        }

        return currentSortAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
    });

    rows.forEach(row => tbody.appendChild(row));
}

function updateEmployeeCount(count) {
    const badge = document.getElementById('employeeCount');
    if (badge) {
        badge.textContent = `Total: ${count}`;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const detailsTab = document.getElementById('details-tab');
    if (detailsTab) {
        detailsTab.addEventListener('shown.bs.tab', function() {
            renderEmployeeTable();
        });
    }
});

// ============================================
// Export Functions
// ============================================

function exportToCSV() {
    const filename = `HR_Employees_${targetMonth}.csv`;
    const headers = ['사번,이름,직급,유형,입사일,퇴사일,재직기간(일),상태'];

    const rows = employeeDetails.map(emp => {
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
            emp.entrance_date || '',
            emp.stop_date || '',
            emp.tenure_days || '0',
            status
        ].map(field => `"${field}"`).join(',');
    });

    const csv = headers.concat(rows).join('\\n');
    downloadFile(csv, filename, 'text/csv;charset=utf-8;');

    console.log(`✅ Exported ${employeeDetails.length} employees to CSV`);
}

function exportToJSON() {
    const filename = `HR_Employees_${targetMonth}.json`;
    const json = JSON.stringify(employeeDetails, null, 2);
    downloadFile(json, filename, 'application/json');

    console.log(`✅ Exported ${employeeDetails.length} employees to JSON`);
}

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

    console.log(`✅ Exported metrics for ${availableMonths.length} months to JSON`);
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

let currentOrgView = 'tree';

function setOrgChartView(viewType) {{
    currentOrgView = viewType;

    // Update button states
    ['viewTree', 'viewHeatmap', 'viewComparison'].forEach(id => {{
        document.getElementById(id).classList.remove('active');
    }});
    document.getElementById('view' + viewType.charAt(0).toUpperCase() + viewType.slice(1)).classList.add('active');

    // Show/hide views
    document.getElementById('orgChartTree').style.display = viewType === 'tree' ? 'block' : 'none';
    document.getElementById('orgChartHeatmap').style.display = viewType === 'heatmap' ? 'block' : 'none';
    document.getElementById('orgChartComparison').style.display = viewType === 'comparison' ? 'block' : 'none';

    // Render appropriate view
    if (viewType === 'tree') {{
        renderOrgChartTree();
    }} else if (viewType === 'heatmap') {{
        renderOrgChartHeatmap();
    }} else if (viewType === 'comparison') {{
        renderOrgChartComparison();
    }}
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

    // Show employee detail modal (2nd level modal)
    alert(`직원 상세 정보: ${{employee.full_name}} (${{employeeId}})`);
    // TODO: Implement 2nd level modal for employee details
}}

function exportTeamData() {{
    // Export current team data to CSV
    alert('팀 데이터 내보내기 기능은 개발 중입니다.');
    // TODO: Implement team data export functionality
}}

// Initialize org chart on tab switch
document.getElementById('orgchart-tab').addEventListener('shown.bs.tab', function() {{
    if (currentOrgView === 'tree') {{
        renderOrgChartTree();
    }}
}});

// ============================================
// Team Analysis Functions
// ============================================

let currentTeamFilter = 'all';
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
    alert(`\ud300 \uc0c1\uc138 \uc815\ubcf4: ${{teamKey}}`);
    // TODO: Open modal or expand details
}}

function exportTeamAnalysis() {{
    alert('\ud300 \ubd84\uc11d \ub370\uc774\ud130 \ub0b4\ubcf4\ub0b4\uae30 \uae30\ub2a5\uc740 \uac1c\ubc1c \uc911\uc785\ub2c8\ub2e4.');
    // TODO: Implement export functionality
}}

// Initialize team analysis on tab switch
document.getElementById('teamanalysis-tab').addEventListener('shown.bs.tab', function() {{
    initTeamAnalysis();
}});

console.log('✅ Dashboard initialized');
console.log('📊 Months:', availableMonths);
console.log('👥 Employees:', employeeDetails.length);
console.log('📋 Modal data:', modalData);
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
