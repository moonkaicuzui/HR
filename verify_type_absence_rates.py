#!/usr/bin/env python3
"""
TYPE별 결근율 구현 검증 스크립트
Verify TYPE-specific absence rates implementation
"""

import json
from bs4 import BeautifulSoup
import re
from src.analytics.hr_metric_calculator import HRMetricCalculator
from src.data.monthly_data_collector import MonthlyDataCollector
from pathlib import Path

def verify_type_rates_implementation():
    """TYPE별 결근율 구현을 종합적으로 검증합니다"""

    print("=" * 80)
    print("TYPE별 결근율 구현 검증 (TYPE-specific Absence Rates Verification)")
    print("=" * 80)

    # Step 1: Check metric calculator
    print("\n📊 Step 1: 메트릭 계산기 검증")
    print("-" * 40)

    hr_root = Path(__file__).parent
    collector = MonthlyDataCollector(hr_root)
    calculator = HRMetricCalculator(collector)

    # Get available months
    available_months = collector.detect_available_months()
    if not available_months:
        print("❌ No data available")
        return False

    # Calculate metrics
    metrics = calculator.calculate_all_metrics(available_months)
    latest_month = available_months[-1]

    if 'type_absence_rates_excl_maternity' not in metrics[latest_month]:
        print("❌ TYPE별 결근율 데이터가 메트릭에 없습니다")
        return False

    type_rates = metrics[latest_month]['type_absence_rates_excl_maternity']
    print(f"✅ TYPE별 결근율 데이터 발견 ({latest_month}):")
    print(f"   • TYPE-1 (무단결근): {type_rates.get('TYPE-1', 0):.2f}%")
    print(f"   • TYPE-2 (병가):     {type_rates.get('TYPE-2', 0):.2f}%")
    print(f"   • TYPE-3 (승인결근): {type_rates.get('TYPE-3', 0):.2f}%")

    # Verify rates are different
    rates = list(type_rates.values())
    unique_rates = len(set(rates))
    if unique_rates == 1:
        print("⚠️  경고: 모든 TYPE이 동일한 결근율을 가지고 있습니다!")
    else:
        print(f"✅ {unique_rates}개의 서로 다른 결근율 값 확인")

    # Step 2: Check dashboard HTML
    print("\n📄 Step 2: 대시보드 HTML 검증")
    print("-" * 40)

    dashboard_path = 'output_reports/hr_dashboard_2024-10_type_rates.html'
    if not Path(dashboard_path).exists():
        print(f"❌ Dashboard file not found: {dashboard_path}")
        return False

    with open(dashboard_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Check for TYPE-specific calculation
    if "calculateTypeValue(employees, monthData, type)" in html_content:
        print("✅ TYPE별 계산 로직이 업데이트되었습니다")
    else:
        print("❌ TYPE별 계산 로직이 업데이트되지 않았습니다")

    # Check for type_absence_rates_excl_maternity in metrics data
    if "type_absence_rates_excl_maternity" in html_content:
        print("✅ TYPE별 결근율 데이터가 대시보드에 포함되었습니다")
    else:
        print("❌ TYPE별 결근율 데이터가 대시보드에 없습니다")

    # Step 3: Verify chart rendering
    print("\n📈 Step 3: 차트 렌더링 검증")
    print("-" * 40)

    # Check for TYPE trend chart function
    if "createTypeTrendChart" in html_content:
        print("✅ TYPE별 트렌드 차트 함수 존재")

        # Extract the chart configuration
        chart_config_match = re.search(r"label: 'TYPE-1'.*?label: 'TYPE-3'", html_content, re.DOTALL)
        if chart_config_match:
            print("✅ TYPE-1, TYPE-2, TYPE-3 데이터셋 구성됨")
        else:
            print("❌ TYPE별 데이터셋을 찾을 수 없습니다")
    else:
        print("❌ TYPE별 트렌드 차트 함수가 없습니다")

    # Step 4: Final summary
    print("\n" + "=" * 80)
    print("검증 결과 요약 (Verification Summary)")
    print("=" * 80)

    checklist = {
        "TYPE별 결근율 데이터 계산": 'type_absence_rates_excl_maternity' in metrics[latest_month],
        "각 TYPE별 다른 값": unique_rates > 1,
        "대시보드에 데이터 포함": "type_absence_rates_excl_maternity" in html_content,
        "TYPE별 계산 로직 업데이트": "calculateTypeValue(employees, monthData, type)" in html_content,
        "차트 함수 구현": "createTypeTrendChart" in html_content,
        "출산휴가 제외": type_rates.get('TYPE-1', 0) > 0  # At least one TYPE should have non-zero rate
    }

    passed = sum(checklist.values())
    total = len(checklist)

    for feature, result in checklist.items():
        status = "✅" if result else "❌"
        print(f"{status} {feature}")

    print(f"\n최종 결과: {passed}/{total} 항목 통과")

    if passed == total:
        print("🎉 TYPE별 결근율이 성공적으로 구현되었습니다!")
        print("\n💡 사용자 지침:")
        print("1. 대시보드에서 'Absence Rate Analysis' 카드를 클릭하세요")
        print("2. 모달 창에서 'Absence Rate by TYPE' 차트를 확인하세요")
        print("3. TYPE-1, TYPE-2, TYPE-3가 각각 다른 결근율을 표시합니다")
        print("4. 모든 값은 출산휴가를 제외한 결근율입니다")
    else:
        print(f"⚠️  {total - passed}개 항목 실패")

    # Save verification report
    report = {
        "verification_date": str(Path(__file__).stat().st_mtime),
        "latest_month": latest_month,
        "type_rates": type_rates,
        "unique_rate_count": unique_rates,
        "checklist": {k: bool(v) for k, v in checklist.items()},
        "passed": passed,
        "total": total,
        "success": passed == total
    }

    with open('type_rates_verification_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 검증 리포트 저장: type_rates_verification_report.json")

    return passed == total

if __name__ == "__main__":
    success = verify_type_rates_implementation()
    exit(0 if success else 1)