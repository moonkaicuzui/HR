#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Integrity Audit Script
데이터 정합성 검증 스크립트

Compares source CSV data calculations with dashboard display values
원본 CSV 데이터 계산값과 대시보드 표시값 비교
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from bs4 import BeautifulSoup
import json

class DataIntegrityAuditor:
    """Data integrity validation between source data and dashboard"""

    def __init__(self):
        self.base_path = Path("/Users/ksmoon/Coding/HR")
        self.results = []

    def load_source_data(self):
        """Load all source CSV files"""
        print("📁 Loading source data files...")

        # December manpower
        self.dec_manpower = pd.read_csv(
            self.base_path / "input_files/basic manpower data december.csv"
        )
        print(f"  ✓ December manpower: {len(self.dec_manpower)} records")

        # November manpower
        self.nov_manpower = pd.read_csv(
            self.base_path / "input_files/basic manpower data november.csv"
        )
        print(f"  ✓ November manpower: {len(self.nov_manpower)} records")

        # December attendance
        self.dec_attendance = pd.read_csv(
            self.base_path / "input_files/attendance/converted/attendance data december_converted.csv"
        )
        print(f"  ✓ December attendance: {len(self.dec_attendance)} records")

        # November attendance
        self.nov_attendance = pd.read_csv(
            self.base_path / "input_files/attendance/converted/attendance data november_converted.csv"
        )
        print(f"  ✓ November attendance: {len(self.nov_attendance)} records")

    def load_dashboard_data(self):
        """Extract data from dashboard HTML"""
        print("\n📊 Loading dashboard data...")

        dashboard_path = self.base_path / "docs/HR_Dashboard_Complete_2025_12.html"
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract embedded data from script tags
        script_tags = soup.find_all('script')
        for script in script_tags:
            if 'dashboardData' in str(script):
                # Extract the dashboardData object
                script_content = str(script)
                # Find the dashboardData JSON
                match = re.search(r'const dashboardData = ({.*?});', script_content, re.DOTALL)
                if match:
                    self.dashboard_data = json.loads(match.group(1))
                    print(f"  ✓ Dashboard data extracted")
                    return

        print("  ⚠ Could not extract dashboard data")
        self.dashboard_data = None

    def calculate_total_headcount(self, df):
        """Calculate total active headcount"""
        # Active = STATUS is not '퇴사' or NaN in proper date columns
        active = df[
            (df['STATUS'].notna()) &
            (df['STATUS'] != '퇴사')
        ]
        return len(active)

    def calculate_team_distribution(self, df):
        """Calculate top 5 teams by headcount"""
        active = df[
            (df['STATUS'].notna()) &
            (df['STATUS'] != '퇴사')
        ]

        if 'TEAM' not in active.columns:
            return {}

        team_counts = active['TEAM'].value_counts().head(5)
        return team_counts.to_dict()

    def calculate_absence_rate(self, attendance_df):
        """Calculate absence rate from attendance data"""
        if attendance_df.empty:
            return 0.0

        # 결근율 = (총 결근일 / 총 근무일) * 100
        total_actual = attendance_df['ACTUAL_WORKING_DAYS'].sum()
        total_expected = attendance_df['TOTAL_WORKING_DAYS'].sum()

        if total_expected == 0:
            return 0.0

        total_absent = total_expected - total_actual
        return (total_absent / total_expected) * 100

    def calculate_turnover_rate(self, df, month_days=31):
        """Calculate monthly turnover rate"""
        # 퇴사율 = (이번달 퇴사자 수 / 월초 재직자 수) * 100
        active_start = len(df[
            (df['STATUS'].notna()) &
            (df['STATUS'] != '퇴사')
        ])

        # Count employees who left this month
        if 'LAST_DAY' in df.columns:
            left_this_month = df[
                (df['LAST_DAY'].notna()) &
                (df['LAST_DAY'].str.contains('2025-12', na=False))
            ]
            resignations = len(left_this_month)
        else:
            resignations = 0

        if active_start == 0:
            return 0.0

        return (resignations / active_start) * 100

    def calculate_perfect_attendance(self, attendance_df):
        """Calculate number of employees with perfect attendance"""
        if attendance_df.empty:
            return 0

        # 만근 = ACTUAL_WORKING_DAYS >= TOTAL_WORKING_DAYS
        perfect = attendance_df[
            attendance_df['ACTUAL_WORKING_DAYS'] >= attendance_df['TOTAL_WORKING_DAYS']
        ]
        return len(perfect)

    def calculate_monthly_changes(self):
        """Calculate month-over-month changes"""
        dec_total = self.calculate_total_headcount(self.dec_manpower)
        nov_total = self.calculate_total_headcount(self.nov_manpower)

        headcount_change = dec_total - nov_total

        # New hires in December
        if 'FIRST_DAY' in self.dec_manpower.columns:
            new_hires = len(self.dec_manpower[
                (self.dec_manpower['FIRST_DAY'].notna()) &
                (self.dec_manpower['FIRST_DAY'].str.contains('2025-12', na=False))
            ])
        else:
            new_hires = 0

        # Resignations in December
        if 'LAST_DAY' in self.dec_manpower.columns:
            resignations = len(self.dec_manpower[
                (self.dec_manpower['LAST_DAY'].notna()) &
                (self.dec_manpower['LAST_DAY'].str.contains('2025-12', na=False))
            ])
        else:
            resignations = 0

        return {
            'headcount_change': headcount_change,
            'new_hires': new_hires,
            'resignations': resignations
        }

    def verify_metric(self, metric_name, calculated_value, dashboard_value, tolerance=0.1):
        """Verify a single metric with tolerance for floating point"""
        if isinstance(calculated_value, float) and isinstance(dashboard_value, float):
            match = abs(calculated_value - dashboard_value) <= tolerance
            diff = calculated_value - dashboard_value
        else:
            match = calculated_value == dashboard_value
            diff = calculated_value - dashboard_value if isinstance(calculated_value, (int, float)) else 'N/A'

        result = {
            'metric': metric_name,
            'calculated': calculated_value,
            'dashboard': dashboard_value,
            'match': match,
            'diff': diff
        }
        self.results.append(result)
        return result

    def run_audit(self):
        """Run complete data integrity audit"""
        print("\n" + "="*80)
        print("🔍 DATA INTEGRITY AUDIT REPORT")
        print("   데이터 정합성 검증 보고서")
        print("="*80)

        # Load data
        self.load_source_data()
        self.load_dashboard_data()

        print("\n" + "-"*80)
        print("📋 METRIC CALCULATIONS")
        print("-"*80)

        # Calculate metrics from source data
        dec_total = self.calculate_total_headcount(self.dec_manpower)
        print(f"\n✓ Total Headcount (December): {dec_total}")

        dec_teams = self.calculate_team_distribution(self.dec_manpower)
        print(f"✓ Top 5 Teams: {dec_teams}")

        dec_absence_rate = self.calculate_absence_rate(self.dec_attendance)
        print(f"✓ Absence Rate: {dec_absence_rate:.2f}%")

        dec_turnover_rate = self.calculate_turnover_rate(self.dec_manpower)
        print(f"✓ Turnover Rate: {dec_turnover_rate:.2f}%")

        perfect_attendance = self.calculate_perfect_attendance(self.dec_attendance)
        print(f"✓ Perfect Attendance Count: {perfect_attendance}")

        monthly_changes = self.calculate_monthly_changes()
        print(f"✓ Monthly Changes:")
        print(f"  - Headcount Change: {monthly_changes['headcount_change']:+d}")
        print(f"  - New Hires: {monthly_changes['new_hires']}")
        print(f"  - Resignations: {monthly_changes['resignations']}")

        # If dashboard data extracted, compare
        if self.dashboard_data:
            print("\n" + "-"*80)
            print("⚖️  VERIFICATION AGAINST DASHBOARD")
            print("-"*80)

            # Extract dashboard values (this depends on dashboard structure)
            # For now, show what we calculated
            print("\n⚠️  Dashboard data structure analysis needed")
            print("   Current dashboard data keys:", list(self.dashboard_data.keys())[:10])

        # Summary
        print("\n" + "="*80)
        print("📊 AUDIT SUMMARY")
        print("="*80)

        if self.results:
            total_checks = len(self.results)
            passed = sum(1 for r in self.results if r['match'])
            failed = total_checks - passed
            accuracy = (passed / total_checks * 100) if total_checks > 0 else 0

            print(f"\nTotal Checks: {total_checks}")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            print(f"Accuracy: {accuracy:.1f}%")

            if failed > 0:
                print("\n⚠️  DISCREPANCIES FOUND:")
                for r in self.results:
                    if not r['match']:
                        print(f"  - {r['metric']}: Calculated={r['calculated']}, Dashboard={r['dashboard']}, Diff={r['diff']}")
        else:
            print("\n✓ Source data calculations completed successfully")
            print("⚠️  Dashboard comparison requires manual verification")
            print("   (Dashboard data extraction needs refinement)")

        print("\n" + "="*80)
        print("✅ AUDIT COMPLETE")
        print("="*80)

        # Save detailed report
        self.save_report()

    def save_report(self):
        """Save detailed audit report"""
        report_path = self.base_path / "data_integrity_audit_report.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("DATA INTEGRITY AUDIT REPORT\n")
            f.write("데이터 정합성 검증 보고서\n")
            f.write("="*80 + "\n\n")

            f.write("1. DECEMBER CALCULATIONS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Headcount: {self.calculate_total_headcount(self.dec_manpower)}\n")
            f.write(f"Absence Rate: {self.calculate_absence_rate(self.dec_attendance):.2f}%\n")
            f.write(f"Turnover Rate: {self.calculate_turnover_rate(self.dec_manpower):.2f}%\n")
            f.write(f"Perfect Attendance: {self.calculate_perfect_attendance(self.dec_attendance)}\n")

            f.write("\n2. MONTHLY CHANGES\n")
            f.write("-"*80 + "\n")
            changes = self.calculate_monthly_changes()
            f.write(f"Headcount Change: {changes['headcount_change']:+d}\n")
            f.write(f"New Hires: {changes['new_hires']}\n")
            f.write(f"Resignations: {changes['resignations']}\n")

            if self.results:
                f.write("\n3. VERIFICATION RESULTS\n")
                f.write("-"*80 + "\n")
                for r in self.results:
                    status = "✓" if r['match'] else "✗"
                    f.write(f"{status} {r['metric']}: Calc={r['calculated']}, Dash={r['dashboard']}, Diff={r['diff']}\n")

        print(f"\n📄 Detailed report saved to: {report_path}")

if __name__ == '__main__':
    auditor = DataIntegrityAuditor()
    auditor.run_audit()
