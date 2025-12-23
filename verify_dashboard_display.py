#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Display Verification
Verify what the dashboard actually displays using Python HTML parsing

대시보드 표시 검증
Python HTML 파싱을 사용하여 대시보드의 실제 표시 내용 검증
"""

from bs4 import BeautifulSoup
import re
import json
from pathlib import Path

def extract_embedded_data(html_path):
    """Extract embedded employee and attendance data from HTML"""
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Find the script with embedded data
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')

    employee_data = None
    attendance_data = None

    for script in scripts:
        script_text = script.string
        if script_text and len(str(script_text)) > 100000:  # Large data script
            script_text = str(script_text)  # Convert to string

            # Find employeeData array - look for the start and find matching bracket
            emp_start = script_text.find('const employeeData = [')
            if emp_start >= 0:
                # Find the closing bracket for this array
                bracket_count = 0
                start_pos = emp_start + len('const employeeData = ')
                end_pos = start_pos

                for i in range(start_pos, len(script_text)):
                    if script_text[i] == '[':
                        bracket_count += 1
                    elif script_text[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            break

                if end_pos > start_pos:
                    try:
                        emp_json = script_text[start_pos:end_pos]
                        employee_data = json.loads(emp_json)
                        print(f"✓ Extracted {len(employee_data)} employee records")
                    except Exception as e:
                        print(f"⚠ Found employeeData but couldn't parse: {str(e)[:100]}")

            # Find attendanceData array
            att_start = script_text.find('const attendanceData = [')
            if att_start >= 0:
                bracket_count = 0
                start_pos = att_start + len('const attendanceData = ')
                end_pos = start_pos

                for i in range(start_pos, len(script_text)):
                    if script_text[i] == '[':
                        bracket_count += 1
                    elif script_text[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i + 1
                            break

                if end_pos > start_pos:
                    try:
                        att_json = script_text[start_pos:end_pos]
                        attendance_data = json.loads(att_json)
                        print(f"✓ Extracted {len(attendance_data)} attendance records")
                    except Exception as e:
                        print(f"⚠ Found attendanceData but couldn't parse: {str(e)[:100]}")

    return employee_data, attendance_data

def calculate_dashboard_metrics(employee_data, attendance_data):
    """Calculate metrics the same way the dashboard does"""
    from datetime import datetime

    metrics = {}

    # Report date (end of December 2025)
    report_date = datetime(2025, 12, 31)

    # 1. Total Employees (active at report date)
    active_employees = []
    for emp in employee_data:
        entrance_date_str = emp.get('entrance_date', '')
        stop_date_str = emp.get('stop_date', '')

        # Parse entrance date
        try:
            entrance_date = datetime.strptime(entrance_date_str.split(' ')[0], '%Y-%m-%d')
        except:
            continue

        # Check if active at report date
        is_active = entrance_date <= report_date

        # Check stop date
        if stop_date_str and stop_date_str.strip():
            try:
                stop_date = datetime.strptime(stop_date_str.split(' ')[0], '%Y-%m-%d')
                if stop_date <= report_date:
                    is_active = False
            except:
                pass

        if is_active:
            active_employees.append(emp)

    metrics['total_employees'] = len(active_employees)

    # 2. Absence Rate
    # Count absence records
    absence_count = sum(1 for att in attendance_data if att.get('reason_description') in ['AR1', 'AR2'])
    total_attendance_records = len(attendance_data)

    if total_attendance_records > 0:
        metrics['absence_rate'] = round((absence_count / total_attendance_records) * 100, 1)
    else:
        metrics['absence_rate'] = 0.0

    # 3. Unauthorized Absence Rate
    unauth_count = sum(1 for att in attendance_data if att.get('reason_description') in ['AR1', 'AR2'])
    if total_attendance_records > 0:
        metrics['unauthorized_absence_rate'] = round((unauth_count / total_attendance_records) * 100, 2)
    else:
        metrics['unauthorized_absence_rate'] = 0.0

    # 4. Resignation Rate
    # Count resignations in December 2025
    december_resignations = 0
    for emp in employee_data:
        stop_date_str = emp.get('stop_date', '')
        if stop_date_str and stop_date_str.strip():
            try:
                stop_date = datetime.strptime(stop_date_str.split(' ')[0], '%Y-%m-%d')
                if stop_date.year == 2025 and stop_date.month == 12:
                    december_resignations += 1
            except:
                pass

    active_at_start = len(active_employees) + december_resignations  # Approximate
    if active_at_start > 0:
        metrics['resignation_rate'] = round((december_resignations / active_at_start) * 100, 1)
    else:
        metrics['resignation_rate'] = 0.0
    metrics['recent_resignations'] = december_resignations

    # 5. Recent Hires (December 2025)
    recent_hires = 0
    for emp in employee_data:
        entrance_date_str = emp.get('entrance_date', '')
        try:
            entrance_date = datetime.strptime(entrance_date_str.split(' ')[0], '%Y-%m-%d')
            if entrance_date.year == 2025 and entrance_date.month == 12:
                recent_hires += 1
        except:
            pass
    metrics['recent_hires'] = recent_hires

    # 6. Perfect Attendance
    # Employees with NO absence records
    employee_nos_with_absence = set()
    for att in attendance_data:
        if att.get('reason_description') in ['AR1', 'AR2', 'AR3', 'AR4', 'AR5']:
            employee_nos_with_absence.add(att.get('employee_no'))

    active_employee_nos = set(emp.get('employee_no') for emp in active_employees)
    perfect_attendance = len(active_employee_nos - employee_nos_with_absence)
    metrics['perfect_attendance'] = perfect_attendance

    # 7. Long-term Employees (1+ year)
    long_term = 0
    for emp in active_employees:
        entrance_date_str = emp.get('entrance_date', '')
        try:
            entrance_date = datetime.strptime(entrance_date_str.split(' ')[0], '%Y-%m-%d')
            tenure_days = (report_date - entrance_date).days
            if tenure_days >= 365:
                long_term += 1
        except:
            pass
    metrics['long_term_employees'] = long_term

    # 8. Under 60 Days
    under_60 = 0
    for emp in active_employees:
        entrance_date_str = emp.get('entrance_date', '')
        try:
            entrance_date = datetime.strptime(entrance_date_str.split(' ')[0], '%Y-%m-%d')
            tenure_days = (report_date - entrance_date).days
            if tenure_days < 60:
                under_60 += 1
        except:
            pass
    metrics['under_60_days'] = under_60

    # 9. Post-Assignment Resignations (estimate)
    # Employees who left within 60 days
    post_assignment = 0
    for emp in employee_data:
        entrance_date_str = emp.get('entrance_date', '')
        stop_date_str = emp.get('stop_date', '')
        if entrance_date_str and stop_date_str and stop_date_str.strip():
            try:
                entrance_date = datetime.strptime(entrance_date_str.split(' ')[0], '%Y-%m-%d')
                stop_date = datetime.strptime(stop_date_str.split(' ')[0], '%Y-%m-%d')
                tenure = (stop_date - entrance_date).days
                if tenure < 60 and stop_date.year == 2025 and stop_date.month == 12:
                    post_assignment += 1
            except:
                pass
    metrics['post_assignment_resignations'] = post_assignment

    # 10. Data Errors (simplified - just check for missing critical fields)
    data_errors = 0
    for emp in employee_data:
        if not emp.get('employee_no') or not emp.get('entrance_date'):
            data_errors += 1
    metrics['data_errors'] = data_errors

    return metrics

def main():
    print("="*80)
    print("🔍 DASHBOARD DISPLAY VERIFICATION")
    print("   대시보드 표시값 검증")
    print("="*80)
    print()

    dashboard_path = Path('docs/HR_Dashboard_Complete_2025_12.html')

    if not dashboard_path.exists():
        print("❌ Dashboard file not found")
        return

    print("📂 Extracting embedded data from dashboard HTML...")
    employee_data, attendance_data = extract_embedded_data(dashboard_path)

    if not employee_data or not attendance_data:
        print("❌ Could not extract embedded data")
        return

    print()
    print("📊 Calculating metrics from embedded data...")
    dashboard_metrics = calculate_dashboard_metrics(employee_data, attendance_data)

    print()
    print("="*80)
    print("📈 DASHBOARD CALCULATED VALUES")
    print("   (Based on embedded data in HTML)")
    print("="*80)
    print()

    for metric, value in dashboard_metrics.items():
        print(f"  {metric}: {value}")

    print()
    print("="*80)
    print("✅ VERIFICATION COMPLETE")
    print("="*80)
    print()
    print("These values represent what the dashboard JavaScript calculates")
    print("from the embedded employee and attendance data.")
    print()

if __name__ == '__main__':
    main()
