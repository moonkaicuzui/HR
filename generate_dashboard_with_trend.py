#!/usr/bin/env python3
"""
대시보드 생성 스크립트 - 추세선 포함
Dashboard generation script with trend lines
"""

from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder
from datetime import datetime
import os

def main():
    # Generate dashboard for October 2024
    target_month = '2024-10'
    print(f"Generating dashboard for {target_month} with trend lines...")

    # Create dashboard builder
    builder = CompleteDashboardBuilder(target_month)

    # Build the dashboard
    html_content = builder.build()

    # Create output directory if it doesn't exist
    os.makedirs('output_reports', exist_ok=True)

    # Save the dashboard
    output_path = f'output_reports/hr_dashboard_{target_month}.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Dashboard generated successfully!")
    print(f"   - File size: {len(html_content):,} characters")
    print(f"   - Location: {output_path}")
    print(f"   - Features: 30-day rolling window, trend lines, 1-hour auto-refresh from Google Drive")

    # Verify trend line code is present
    if "calculateTrendLine" in html_content:
        print("   ✓ Trend line calculation function included")

    if "Trend" in html_content and "borderDash" in html_content:
        print("   ✓ Trend line visualization configured")

    return output_path

if __name__ == "__main__":
    dashboard_path = main()
    print(f"\n🎯 Open the dashboard in your browser: file://{os.path.abspath(dashboard_path)}")