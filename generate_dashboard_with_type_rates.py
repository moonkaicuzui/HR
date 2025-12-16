#!/usr/bin/env python3
"""
TYPE별 결근율이 포함된 대시보드 생성 스크립트
Dashboard generation with TYPE-specific absence rates
"""

from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder
from src.analytics.hr_metric_calculator import HRMetricCalculator
from src.data.monthly_data_collector import MonthlyDataCollector
from datetime import datetime
from pathlib import Path
import json
import os

def verify_type_rates():
    """TYPE별 결근율 데이터 확인"""

    # Initialize data collector and calculator
    hr_root = Path(__file__).parent
    collector = MonthlyDataCollector(hr_root)
    calculator = HRMetricCalculator(collector)

    # Get available months
    available_months = collector.detect_available_months()
    print(f"📅 사용 가능한 월: {available_months}")

    if available_months:
        # Calculate metrics for all available months
        metrics = calculator.calculate_all_metrics(available_months)

        # Check latest month's TYPE rates
        latest_month = available_months[-1]
        print(f"\n📊 {latest_month} TYPE별 결근율 확인:")

        if 'type_absence_rates_excl_maternity' in metrics[latest_month]:
            type_rates = metrics[latest_month]['type_absence_rates_excl_maternity']
            print("\n🔴 TYPE별 출산휴가 제외 결근율:")
            print("-" * 40)
            print(f"   TYPE-1 (무단결근): {type_rates.get('TYPE-1', 0):.2f}%")
            print(f"   TYPE-2 (병가):     {type_rates.get('TYPE-2', 0):.2f}%")
            print(f"   TYPE-3 (승인결근): {type_rates.get('TYPE-3', 0):.2f}%")

            # Verify that rates are different
            rates = list(type_rates.values())
            if len(set(rates)) == 1:
                print("\n⚠️  경고: 모든 TYPE이 동일한 결근율을 가지고 있습니다!")
            else:
                print("\n✅ TYPE별로 다른 결근율이 계산되었습니다.")
        else:
            print("❌ TYPE별 결근율 데이터가 없습니다.")

def main():
    # Generate dashboard for October 2024
    target_month = '2024-10'
    print(f"\nGenerating dashboard for {target_month} with TYPE-specific rates...")
    print("=" * 80)

    # Verify TYPE rates first
    verify_type_rates()

    print("\n" + "=" * 80)
    print("대시보드 생성 중...")
    print("=" * 80)

    # Create dashboard builder
    builder = CompleteDashboardBuilder(target_month)

    # Build the dashboard
    html_content = builder.build()

    # Create output directory if it doesn't exist
    os.makedirs('output_reports', exist_ok=True)

    # Save the dashboard
    output_path = f'output_reports/hr_dashboard_{target_month}_type_rates.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ Dashboard generated successfully!")
    print(f"   - 파일 크기: {len(html_content):,} characters")
    print(f"   - 위치: {output_path}")
    print(f"   - 특징: TYPE별 결근율, 출산휴가 제외, 30일 윈도우, 추세선")

    # Verify TYPE chart code is present
    if "createTypeTrendChart" in html_content:
        print("   ✓ TYPE별 차트 함수 포함")

    if "type_absence_rates_excl_maternity" in html_content:
        print("   ✓ TYPE별 결근율 데이터 포함")

    # Check if TYPE rates are used correctly
    if "calculateTypeValue(employees, monthData, type)" in html_content:
        print("   ✓ TYPE별 계산 로직 업데이트됨")

    return output_path

if __name__ == "__main__":
    dashboard_path = main()
    print(f"\n🎯 브라우저에서 대시보드 열기: file://{os.path.abspath(dashboard_path)}")
    print("\n💡 Absence Rate Analysis 모달을 클릭한 후,")
    print("   'Absence Rate by TYPE' 차트를 확인하세요.")
    print("   TYPE-1, TYPE-2, TYPE-3가 각각 다른 값을 표시해야 합니다.")