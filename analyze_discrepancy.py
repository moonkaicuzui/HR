#!/usr/bin/env python3
"""
Analyze metric discrepancies between source CSV and dashboard
소스 CSV와 대시보드 간 메트릭 불일치 분석
"""
import json
import re
import pandas as pd
from datetime import datetime

print("=" * 70)
print("Discrepancy Analysis / 불일치 분석")
print("=" * 70)

# Load dashboard data
with open('docs/HR_Dashboard_Complete_2025_12.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

match = re.search(r'const employeeDetails\s*=\s*\n?(\[)', html_content)
start_idx = match.start(1)
bracket_count = 0
end_idx = start_idx
for i, char in enumerate(html_content[start_idx:]):
    if char == '[':
        bracket_count += 1
    elif char == ']':
        bracket_count -= 1
        if bracket_count == 0:
            end_idx = start_idx + i + 1
            break
json_str = html_content[start_idx:end_idx]
dashboard_employees = json.loads(json_str)

# Load source data
basic_df = pd.read_csv('input_files/basic manpower data december.csv')

print(f"\n📊 Data Counts:")
print(f"   - Source CSV rows: {len(basic_df)}")
print(f"   - Dashboard employees: {len(dashboard_employees)}")

# =============================================================================
# RESIGNED THIS MONTH Analysis
# =============================================================================
print("\n" + "=" * 70)
print("1. RESIGNED THIS MONTH Analysis / 이번달 퇴사자 분석")
print("=" * 70)

end_of_month = datetime(2025, 12, 31)

# Source calculation - USE dayfirst=True for D/M/YYYY format
# 소스 계산 - D/M/YYYY 형식을 위해 dayfirst=True 사용
basic_df['stop_date'] = pd.to_datetime(basic_df['Stop working Date'], errors='coerce', dayfirst=True)
source_resigned = basic_df[
    (basic_df['stop_date'].notna()) &
    (basic_df['stop_date'].dt.year == 2025) &
    (basic_df['stop_date'].dt.month == 12)
]
print(f"\n[Source CSV] Resigned this month: {len(source_resigned)}")
print("Resigned employees:")
for _, row in source_resigned.iterrows():
    print(f"   - {row['Employee No']}: {row.get('Full Name', 'N/A')} (Stop: {row['stop_date'].strftime('%Y-%m-%d') if pd.notna(row['stop_date']) else 'N/A'})")

# Dashboard calculation
dashboard_resigned = [e for e in dashboard_employees if e.get('resigned_this_month', False)]
print(f"\n[Dashboard] Resigned this month: {len(dashboard_resigned)}")
print("Resigned employees:")
for e in dashboard_resigned:
    print(f"   - {e['employee_id']}: {e.get('employee_name', 'N/A')} (Stop: {e.get('stop_date', 'N/A')})")

# Find difference
source_resigned_ids = set(source_resigned['Employee No'].astype(str))
dashboard_resigned_ids = set(e['employee_id'] for e in dashboard_resigned)

only_in_dashboard = dashboard_resigned_ids - source_resigned_ids
only_in_source = source_resigned_ids - dashboard_resigned_ids

print(f"\n⚠️  Discrepancy:")
print(f"   - Only in Dashboard (not in source): {only_in_dashboard}")
print(f"   - Only in Source (not in dashboard): {only_in_source}")

# Check if extra dashboard resigned are in source at all
print(f"\n🔍 Checking extra dashboard resigned in source:")
for emp_id in only_in_dashboard:
    source_match = basic_df[basic_df['Employee No'].astype(str) == emp_id]
    if len(source_match) > 0:
        row = source_match.iloc[0]
        stop_date = row['Stop working Date']
        print(f"   - {emp_id}: Stop Date in source = '{stop_date}'")
    else:
        print(f"   - {emp_id}: NOT FOUND in source CSV")

# =============================================================================
# UNDER 60 DAYS Analysis
# =============================================================================
print("\n" + "=" * 70)
print("2. UNDER 60 DAYS Analysis / 60일 미만 재직자 분석")
print("=" * 70)

# Source calculation - USE dayfirst=True for D/M/YYYY format
# 소스 계산 - D/M/YYYY 형식을 위해 dayfirst=True 사용
basic_df['entrance_date'] = pd.to_datetime(basic_df['Entrance Date'], errors='coerce', dayfirst=True)
basic_df['tenure_days'] = (end_of_month - basic_df['entrance_date']).dt.days
basic_df['is_active'] = (basic_df['stop_date'].isna()) | (basic_df['stop_date'] > end_of_month)

source_under_60 = basic_df[
    (basic_df['is_active']) &
    (basic_df['tenure_days'] > 0) &
    (basic_df['tenure_days'] < 60)
]
print(f"\n[Source CSV] Under 60 days (active): {len(source_under_60)}")
print("Employees:")
for _, row in source_under_60.iterrows():
    print(f"   - {row['Employee No']}: {row.get('Full Name', 'N/A')} (Tenure: {row['tenure_days']} days, Entrance: {row['entrance_date'].strftime('%Y-%m-%d') if pd.notna(row['entrance_date']) else 'N/A'})")

# Dashboard calculation
dashboard_under_60 = [e for e in dashboard_employees if e.get('is_active', False) and e.get('under_60_days', False)]
print(f"\n[Dashboard] Under 60 days (active): {len(dashboard_under_60)}")
print("Employees:")
for e in dashboard_under_60:
    print(f"   - {e['employee_id']}: {e.get('employee_name', 'N/A')} (Tenure: {e.get('tenure_days', 'N/A')} days, Entrance: {e.get('entrance_date', 'N/A')})")

# Find difference
source_under60_ids = set(source_under_60['Employee No'].astype(str))
dashboard_under60_ids = set(e['employee_id'] for e in dashboard_under_60)

only_in_dashboard_60 = dashboard_under60_ids - source_under60_ids
only_in_source_60 = source_under60_ids - dashboard_under60_ids

print(f"\n⚠️  Discrepancy:")
print(f"   - Only in Dashboard (not in source): {only_in_dashboard_60}")
print(f"   - Only in Source (not in dashboard): {only_in_source_60}")

# Check missing from dashboard
print(f"\n🔍 Checking employees missing from dashboard under_60_days:")
for emp_id in only_in_source_60:
    # Find in dashboard
    dashboard_match = [e for e in dashboard_employees if e['employee_id'] == emp_id]
    if dashboard_match:
        e = dashboard_match[0]
        print(f"   - {emp_id}: is_active={e.get('is_active')}, under_60_days={e.get('under_60_days')}, tenure_days={e.get('tenure_days')}")
    else:
        print(f"   - {emp_id}: NOT FOUND in dashboard")

print("\n" + "=" * 70)
print("Root Cause Summary / 근본 원인 요약")
print("=" * 70)
