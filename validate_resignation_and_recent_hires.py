#!/usr/bin/env python3
"""
Resignation Rate and Recent Hires Data Validation Script
퇴사율 및 신규 입사자 데이터 검증 스크립트

Validates:
1. Resignation Rate calculation (should count only resignations in target month)
2. Recent Hires data extraction and metrics
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime


def load_basic_data(year: int, month: int):
    """Load basic manpower data"""
    month_names = {
        1: 'january', 2: 'february', 3: 'march', 4: 'april',
        5: 'may', 6: 'june', 7: 'july', 8: 'august',
        9: 'september', 10: 'october', 11: 'november', 12: 'december'
    }
    month_name = month_names.get(month, str(month))
    file_path = Path(f"input_files/basic manpower data {month_name}.csv")
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path)


def load_attendance_data(year: int, month: int):
    """Load attendance data"""
    month_names = {
        1: 'january', 2: 'february', 3: 'march', 4: 'april',
        5: 'may', 6: 'june', 7: 'july', 8: 'august',
        9: 'september', 10: 'october', 11: 'november', 12: 'december'
    }
    month_name = month_names.get(month, str(month))
    file_path = Path(f"input_files/attendance/converted/attendance data {month_name}_converted.csv")
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path)


def parse_date(date_val):
    """Parse date value"""
    if pd.isna(date_val) or date_val == '' or date_val == 'nan':
        return pd.NaT
    try:
        return pd.to_datetime(date_val, errors='coerce', dayfirst=True)
    except:
        return pd.NaT


def validate_resignation_rate(year: int, month: int):
    """
    Validate resignation rate calculation for target month
    대상 월의 퇴사율 계산 검증
    """
    print(f"\n{'='*80}")
    print(f"📊 Resignation Rate Validation for {year}-{month:02d}")
    print(f"{'='*80}\n")

    target_month = f"{year}-{month:02d}"

    # Load data
    basic_data = load_basic_data(year, month)

    if basic_data.empty:
        print("❌ No basic data found")
        return

    print(f"📋 Total employees in data: {len(basic_data)}")

    # Parse dates
    basic_data['entrance_date'] = basic_data.get('Entrance Date', pd.Series()).apply(parse_date)
    basic_data['stop_date'] = basic_data.get('Stop working Date', pd.Series()).apply(parse_date)

    # Count resignations in target month
    target_date = pd.Timestamp(f"{year}-{month:02d}-01")

    resignations_this_month = basic_data[
        (basic_data['stop_date'].notna()) &
        (basic_data['stop_date'].dt.year == target_date.year) &
        (basic_data['stop_date'].dt.month == target_date.month)
    ]

    print(f"\n✅ Resignations in {target_month}: {len(resignations_this_month)} employees")

    if len(resignations_this_month) > 0:
        print(f"\n📋 Resignation Details:")
        cols_to_show = ['Employee No', 'Full Name', 'stop_date']
        if 'Team' in basic_data.columns:
            cols_to_show.insert(2, 'Team')
        elif 'ROLE TYPE STD' in basic_data.columns:
            cols_to_show.insert(2, 'ROLE TYPE STD')
        print(resignations_this_month[cols_to_show].to_string(index=False))

    # Calculate resignation rate by team
    print(f"\n{'='*80}")
    print(f"📊 Resignation Rate by Team")
    print(f"{'='*80}\n")

    teams = basic_data['Team'].unique()
    team_stats = []

    for team in sorted(teams):
        if pd.isna(team):
            continue

        team_members = basic_data[basic_data['Team'] == team]
        team_resignations = resignations_this_month[resignations_this_month['Team'] == team]

        total = len(team_members)
        resigned = len(team_resignations)
        rate = (resigned / total * 100) if total > 0 else 0

        team_stats.append({
            'Team': team,
            'Total': total,
            'Resigned': resigned,
            'Rate (%)': round(rate, 1)
        })

    team_df = pd.DataFrame(team_stats).sort_values('Rate (%)', ascending=False)
    print(team_df.to_string(index=False))

    # Overall resignation rate
    total_employees = len(basic_data)
    total_resignations = len(resignations_this_month)
    overall_rate = (total_resignations / total_employees * 100) if total_employees > 0 else 0

    print(f"\n{'='*80}")
    print(f"📊 Overall Resignation Rate: {overall_rate:.1f}%")
    print(f"   Total Employees: {total_employees}")
    print(f"   Resignations in {target_month}: {total_resignations}")
    print(f"{'='*80}\n")


def validate_recent_hires(year: int, month: int):
    """
    Validate recent hires data extraction
    신규 입사자 데이터 추출 검증
    """
    print(f"\n{'='*80}")
    print(f"📊 Recent Hires Validation for {year}-{month:02d}")
    print(f"{'='*80}\n")

    target_month = f"{year}-{month:02d}"

    # Load data
    basic_data = load_basic_data(year, month)
    attendance_data = load_attendance_data(year, month)

    if basic_data.empty:
        print("❌ No basic data found")
        return

    # Parse entrance dates
    basic_data['entrance_date'] = basic_data.get('Entrance Date', pd.Series()).apply(parse_date)
    basic_data['stop_date'] = basic_data.get('Stop working Date', pd.Series()).apply(parse_date)

    # Filter recent hires (hired in target month)
    target_date = pd.Timestamp(f"{year}-{month:02d}-01")

    recent_hires = basic_data[
        (basic_data['entrance_date'].notna()) &
        (basic_data['entrance_date'].dt.year == target_date.year) &
        (basic_data['entrance_date'].dt.month == target_date.month)
    ].copy()

    print(f"✅ Total Recent Hires in {target_month}: {len(recent_hires)} employees")

    if len(recent_hires) == 0:
        print("ℹ️  No recent hires found for this month")
        return

    # Check who resigned in the same month
    recent_hires['resigned_this_month'] = (
        (recent_hires['stop_date'].notna()) &
        (recent_hires['stop_date'].dt.year == target_date.year) &
        (recent_hires['stop_date'].dt.month == target_date.month)
    )

    # Calculate tenure days for those who resigned
    recent_hires['tenure_days'] = (
        recent_hires['stop_date'] - recent_hires['entrance_date']
    ).dt.days

    active_hires = recent_hires[~recent_hires['resigned_this_month']]
    resigned_hires = recent_hires[recent_hires['resigned_this_month']]

    print(f"\n📊 Recent Hires Breakdown:")
    print(f"   Active: {len(active_hires)} employees")
    print(f"   Resigned in same month: {len(resigned_hires)} employees")

    if len(resigned_hires) > 0:
        print(f"\n⚠️  Early Resignations (within same month):")
        early_resign_df = resigned_hires[['Employee No', 'Full name', 'Team', 'entrance_date', 'stop_date', 'tenure_days']]
        print(early_resign_df.to_string(index=False))

        # Group by tenure ranges
        print(f"\n📊 Early Resignation by Tenure:")
        tenure_groups = {
            '0-30 days': len(resigned_hires[resigned_hires['tenure_days'] <= 30]),
            '31-60 days': len(resigned_hires[(resigned_hires['tenure_days'] > 30) & (resigned_hires['tenure_days'] <= 60)]),
            '61-90 days': len(resigned_hires[(resigned_hires['tenure_days'] > 60) & (resigned_hires['tenure_days'] <= 90)]),
            '90+ days': len(resigned_hires[resigned_hires['tenure_days'] > 90])
        }
        for tenure_range, count in tenure_groups.items():
            print(f"   {tenure_range}: {count} employees")

    # Merge with attendance data
    if not attendance_data.empty:
        print(f"\n📊 Absence Rate Analysis for Recent Hires:")

        # Calculate absence metrics
        attendance_merged = recent_hires.merge(
            attendance_data,
            left_on='Employee No',
            right_on='Employee No',
            how='left',
            suffixes=('', '_att')
        )

        # Calculate average absence rate
        if 'Working Days' in attendance_merged.columns and 'Absent days' in attendance_merged.columns:
            attendance_merged['working_days'] = pd.to_numeric(attendance_merged['Working Days'], errors='coerce')
            attendance_merged['absent_days'] = pd.to_numeric(attendance_merged['Absent days'], errors='coerce')

            attendance_merged['absence_rate'] = (
                attendance_merged['absent_days'] / attendance_merged['working_days'] * 100
            ).fillna(0)

            avg_absence = attendance_merged['absence_rate'].mean()
            print(f"   Average Absence Rate: {avg_absence:.1f}%")

            # Count unauthorized absences
            if 'TYPE-0 (무단결근)' in attendance_merged.columns:
                attendance_merged['unauth_days'] = pd.to_numeric(attendance_merged['TYPE-0 (무단결근)'], errors='coerce').fillna(0)
                total_unauth = attendance_merged['unauth_days'].sum()
                employees_with_unauth = (attendance_merged['unauth_days'] > 0).sum()
                print(f"   Employees with Unauthorized Absence: {employees_with_unauth}/{len(recent_hires)}")
                print(f"   Total Unauthorized Absence Days: {total_unauth:.0f}")

    # Team distribution
    print(f"\n📊 Recent Hires by Team:")
    team_counts = recent_hires['Team'].value_counts()
    for team, count in team_counts.items():
        print(f"   {team}: {count} employees")

    print(f"\n{'='*80}\n")


def main():
    """Main validation function"""
    year = 2025
    month = 10

    print(f"\n{'#'*80}")
    print(f"# Resignation Rate & Recent Hires Data Validation")
    print(f"# 퇴사율 및 신규 입사자 데이터 검증")
    print(f"{'#'*80}")

    # Validate Resignation Rate
    validate_resignation_rate(year, month)

    # Validate Recent Hires
    validate_recent_hires(year, month)

    print(f"\n✅ Validation Complete!")


if __name__ == "__main__":
    main()
