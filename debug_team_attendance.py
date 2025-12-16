#!/usr/bin/env python3
"""
Debug team attendance rate calculation
팀 출근율 계산 디버깅
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from src.data.monthly_data_collector import MonthlyDataCollector

def main():
    # Initialize collector
    hr_root = Path(__file__).parent
    collector = MonthlyDataCollector(hr_root)

    # Load October 2025 data
    target_month = "2025-10"
    print(f"Loading data for {target_month}...")

    data = collector.load_month_data(target_month)

    # Check basic_manpower
    df = data.get('basic_manpower', pd.DataFrame())
    print(f"\n✅ Basic manpower loaded: {len(df)} rows")
    if not df.empty:
        print(f"   Columns: {list(df.columns)[:10]}...")

    # Check attendance
    attendance_df = data.get('attendance', pd.DataFrame())
    print(f"\n✅ Attendance loaded: {len(attendance_df)} rows")

    if attendance_df.empty:
        print("❌ Attendance DataFrame is EMPTY!")
        return

    print(f"   Columns: {list(attendance_df.columns)}")

    # Check for required columns
    has_id_no = 'ID No' in attendance_df.columns
    has_compadd = 'compAdd' in attendance_df.columns

    print(f"\n   Has 'ID No' column: {has_id_no}")
    print(f"   Has 'compAdd' column: {has_compadd}")

    if has_id_no:
        unique_ids = attendance_df['ID No'].unique()
        print(f"   Unique employee IDs: {len(unique_ids)}")
        print(f"   Sample IDs: {unique_ids[:5]}")

    if has_compadd:
        # Count attendance types
        absent_count = len(attendance_df[attendance_df['compAdd'] == 'Vắng mặt'])
        present_count = len(attendance_df[attendance_df['compAdd'] == 'Đi làm'])
        total_count = len(attendance_df)

        print(f"\n   Total records: {total_count}")
        print(f"   Đi làm (Present): {present_count}")
        print(f"   Vắng mặt (Absent): {absent_count}")
        print(f"   Overall attendance rate: {((total_count - absent_count) / total_count * 100):.1f}%")

    # Test with a sample team
    if not df.empty and has_id_no:
        # Show all columns
        print(f"\n📋 All columns in basic_manpower:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")

        # Check for ID No column in basic_manpower
        id_col_basic = None
        for col in df.columns:
            if 'Employee No' in col or 'ID No' in col or 'Personnel Number' in col:
                print(f"\n   Potential ID column found: '{col}'")
                id_col_basic = col
                break

        # Check if IDs match between basic_manpower and attendance
        if id_col_basic:
            basic_ids = set(df[id_col_basic].dropna().astype(str).unique())
            attendance_ids = set(attendance_df['ID No'].dropna().astype(str).unique())

            print(f"\n   Basic manpower IDs: {len(basic_ids)}")
            print(f"   Attendance IDs: {len(attendance_ids)}")
            print(f"   Matching IDs: {len(basic_ids & attendance_ids)}")
            print(f"   IDs only in basic_manpower: {len(basic_ids - attendance_ids)}")
            print(f"   IDs only in attendance: {len(attendance_ids - basic_ids)}")

            # Sample comparison
            print(f"\n   Sample basic_manpower IDs: {list(basic_ids)[:5]}")
            print(f"   Sample attendance IDs: {list(attendance_ids)[:5]}")

            # Check data types
            basic_sample = df[id_col_basic].dropna().iloc[0]
            attendance_sample = attendance_df['ID No'].dropna().iloc[0]

            print(f"\n   Data type in basic_manpower: {type(basic_sample)} = {basic_sample}")
            print(f"   Data type in attendance: {type(attendance_sample)} = {attendance_sample}")

            # Test the actual filtering logic used in the dashboard
            print(f"\n🧪 Testing actual dashboard filtering logic:")
            test_ids = df[id_col_basic].dropna().unique().tolist()[:10]  # First 10 IDs
            print(f"   Test employee IDs (first 10): {test_ids}")
            print(f"   Type of test_ids[0]: {type(test_ids[0])}")

            # Try filtering like the dashboard does
            filtered = attendance_df[attendance_df['ID No'].isin(test_ids)]
            print(f"   Filtered attendance records: {len(filtered)}")

            # Try with string conversion
            test_ids_str = [str(x) for x in test_ids]
            attendance_ids_col = attendance_df['ID No'].astype(str)
            filtered_str = attendance_df[attendance_ids_col.isin(test_ids_str)]
            print(f"   Filtered with string conversion: {len(filtered_str)}")

            # Test the EXACT problematic scenario: string IDs vs int column
            print(f"\n❌ Testing problematic scenario (string IDs vs int column):")
            test_ids_as_strings = [str(x) for x in test_ids]  # Convert to strings like dashboard does
            print(f"   Test IDs as strings: {test_ids_as_strings[:3]}")
            # Try to filter int column with string list (THIS IS THE BUG)
            filtered_bug = attendance_df[attendance_df['ID No'].isin(test_ids_as_strings)]
            print(f"   ❌ Filtered (string list vs int column): {len(filtered_bug)} records")
            print(f"   This is why avg_attendance_rate = 0!")
        else:
            print("\n❌ Could not find ID column in basic_manpower data")

if __name__ == '__main__':
    main()
