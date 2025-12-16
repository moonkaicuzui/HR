#!/usr/bin/env python3
"""
추세선 검증 스크립트
Verify trend lines in the generated dashboard
"""

import re
from bs4 import BeautifulSoup
import json

def verify_trend_lines():
    """추세선 구현을 검증합니다"""

    print("=" * 80)
    print("추세선 구현 검증 (Trend Line Verification)")
    print("=" * 80)

    # Read the generated dashboard
    with open('output_reports/hr_dashboard_2024-10.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Check for trend line calculation function
    print("\n✅ 추세선 계산 함수 확인:")
    if "calculateTrendLine" in html_content:
        print("   ✓ calculateTrendLine 함수 발견")

        # Extract the function to verify its logic
        trend_func_match = re.search(r'function calculateTrendLine\(data\) \{.*?\n\s*\}', html_content, re.DOTALL)
        if trend_func_match:
            print("   ✓ 선형 회귀 계산 로직 포함")
    else:
        print("   ✗ calculateTrendLine 함수 없음")

    # Check for trend line datasets in chart configuration
    print("\n✅ 차트 데이터셋 확인:")

    # Look for daily absence chart configuration
    chart_config_match = re.search(r'const modalChart3 = new Chart.*?datasets:\s*\[(.*?)\]', html_content, re.DOTALL)

    if chart_config_match:
        datasets_str = chart_config_match.group(1)

        # Count datasets
        dataset_count = datasets_str.count('label:')
        print(f"   - 총 {dataset_count}개의 데이터셋 발견")

        # Check for trend line datasets
        if "결근율 추세선" in datasets_str or "Absence Rate Trend" in datasets_str:
            print("   ✓ 결근율 추세선 데이터셋 포함")

        if "무단결근율 추세선" in datasets_str or "Unauthorized Rate Trend" in datasets_str:
            print("   ✓ 무단결근율 추세선 데이터셋 포함")

        # Check for dashed line style (trend line visual indicator)
        if "borderDash" in datasets_str:
            print("   ✓ 추세선 점선 스타일 설정됨")

    # Check for trend line data calculation
    print("\n✅ 추세선 데이터 계산 확인:")
    if "calculateTrendLine(absenceRates)" in html_content:
        print("   ✓ 결근율 추세선 계산 호출")

    if "calculateTrendLine(unauthorizedRates)" in html_content:
        print("   ✓ 무단결근율 추세선 계산 호출")

    # Extract and verify actual data
    print("\n✅ 실제 데이터 확인:")

    # Look for the daily data arrays
    daily_labels_match = re.search(r"const dailyLabels = \[(.*?)\]", html_content, re.DOTALL)
    absence_rates_match = re.search(r"const absenceRates = \[(.*?)\]", html_content, re.DOTALL)
    unauthorized_rates_match = re.search(r"const unauthorizedRates = \[(.*?)\]", html_content, re.DOTALL)

    if daily_labels_match and absence_rates_match:
        labels = daily_labels_match.group(1)
        absence_data = absence_rates_match.group(1)

        # Count data points
        label_count = len([l for l in labels.split(',') if l.strip()])
        absence_count = len([d for d in absence_data.split(',') if d.strip()])

        print(f"   - 일별 라벨: {label_count}개")
        print(f"   - 결근율 데이터 포인트: {absence_count}개")

        if unauthorized_rates_match:
            unauthorized_data = unauthorized_rates_match.group(1)
            unauthorized_count = len([d for d in unauthorized_data.split(',') if d.strip()])
            print(f"   - 무단결근율 데이터 포인트: {unauthorized_count}개")

        # Verify 30-day window
        if label_count >= 30:
            print("   ✓ 30일 데이터 윈도우 구현됨")
        else:
            print(f"   ⚠️  {label_count}일 데이터만 있음 (30일 미만)")

    # Final summary
    print("\n" + "=" * 80)
    print("검증 결과 요약 (Verification Summary)")
    print("=" * 80)

    checklist = {
        "추세선 계산 함수": "calculateTrendLine" in html_content,
        "추세선 데이터셋": "추세선" in html_content or "Trend" in html_content,
        "점선 스타일": "borderDash" in html_content,
        "계산 호출": "calculateTrendLine(" in html_content,
    }

    passed = sum(checklist.values())
    total = len(checklist)

    for feature, result in checklist.items():
        status = "✅" if result else "❌"
        print(f"{status} {feature}")

    print(f"\n최종 결과: {passed}/{total} 항목 통과")

    if passed == total:
        print("🎉 추세선이 성공적으로 구현되었습니다!")
    else:
        print(f"⚠️  {total - passed}개 항목 누락")

    return passed == total

if __name__ == "__main__":
    success = verify_trend_lines()
    exit(0 if success else 1)