#!/usr/bin/env python3
"""
test_charts_final_verification.py - Final verification of both trend charts
두 개의 추세 차트 최종 검증
"""

import json
import re
from pathlib import Path


def final_verification():
    """Final comprehensive verification of both new charts"""

    html_path = Path('output_files/HR_Dashboard_2025_10.html')

    if not html_path.exists():
        print(f"❌ Dashboard file not found: {html_path}")
        return False

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print("=" * 70)
    print("🎯 Final Verification: 무단 결근율 & 결근율 차트")
    print("=" * 70)

    # Extract monthlyMetrics
    metrics_pattern = r'const monthlyMetrics =\s*(\{.*?\})\s*;'
    metrics_match = re.search(metrics_pattern, html_content, re.DOTALL)

    if not metrics_match:
        print("❌ Could not find monthlyMetrics")
        return False

    monthly_metrics = json.loads(metrics_match.group(1))

    results = {
        'passed': [],
        'failed': []
    }

    # Test Chart 5: Unauthorized Absence Rate
    print("\n📊 Chart 5: 무단 결근율 차트 (Unauthorized Absence Rate)")
    print("-" * 70)

    # Check data source
    if "getTrendData('unauthorized_absence_rate')" in html_content:
        results['passed'].append("✅ Chart 5 uses correct data source")
        print("✅ Data Source: 'unauthorized_absence_rate' (올바름)")

        # Show actual data values
        print("\n   📈 실제 데이터 값:")
        for month in sorted(monthly_metrics.keys()):
            value = monthly_metrics[month]['unauthorized_absence_rate']
            print(f"      {month}: {value}%")
    else:
        results['failed'].append("❌ Chart 5 data source incorrect")
        print("❌ Data Source: INCORRECT")

    # Check label
    if "'무단 결근율 (%) / Unauthorized Absence Rate'" in html_content:
        results['passed'].append("✅ Chart 5 has correct bilingual label")
        print("\n✅ Label: '무단 결근율 (%) / Unauthorized Absence Rate'")
    else:
        results['failed'].append("❌ Chart 5 label incorrect")
        print("\n❌ Label: INCORRECT")

    # Check percentage formatting in tooltip
    chart5_section = html_content[html_content.find("Chart 5:"):html_content.find("Chart 5:")+2000]
    if "context.parsed.y.toFixed(2) + '%'" in chart5_section:
        results['passed'].append("✅ Chart 5 tooltip shows percentages (2 decimals)")
        print("✅ Tooltip Format: value.toFixed(2) + '%' (예: 1.02%)")
    else:
        results['failed'].append("❌ Chart 5 tooltip format incorrect")
        print("❌ Tooltip Format: INCORRECT")

    # Check Y-axis formatting
    if "return value.toFixed(1) + '%';" in chart5_section:
        results['passed'].append("✅ Chart 5 Y-axis shows percentages")
        print("✅ Y-axis Format: value.toFixed(1) + '%' (예: 1.0%)")
    else:
        results['failed'].append("❌ Chart 5 Y-axis format incorrect")
        print("❌ Y-axis Format: INCORRECT")

    # Check chart type
    if "type: 'bar'" in chart5_section:
        results['passed'].append("✅ Chart 5 is bar chart")
        print("✅ Chart Type: Bar chart")
    else:
        results['failed'].append("❌ Chart 5 type incorrect")
        print("❌ Chart Type: INCORRECT")

    # Test Chart 6: Absence Rate
    print("\n📈 Chart 6: 결근율 차트 (Absence Rate)")
    print("-" * 70)

    # Check data source
    if "getTrendData('absence_rate')" in html_content:
        results['passed'].append("✅ Chart 6 uses correct data source")
        print("✅ Data Source: 'absence_rate' (올바름)")

        # Show actual data values
        print("\n   📈 실제 데이터 값:")
        for month in sorted(monthly_metrics.keys()):
            value = monthly_metrics[month]['absence_rate']
            print(f"      {month}: {value}%")
    else:
        results['failed'].append("❌ Chart 6 data source incorrect")
        print("❌ Data Source: INCORRECT")

    # Check label
    if "'결근율 (%) / Absence Rate'" in html_content:
        results['passed'].append("✅ Chart 6 has correct bilingual label")
        print("\n✅ Label: '결근율 (%) / Absence Rate'")
    else:
        results['failed'].append("❌ Chart 6 label incorrect")
        print("\n❌ Label: INCORRECT")

    # Check chart type
    chart6_section = html_content[html_content.find("Chart 6:"):html_content.find("Chart 6:")+2000]
    if "type: 'line'" in chart6_section:
        results['passed'].append("✅ Chart 6 is line chart")
        print("✅ Chart Type: Line chart")
    else:
        results['failed'].append("❌ Chart 6 type incorrect")
        print("❌ Chart Type: INCORRECT")

    # Check canvas elements exist
    print("\n🏗️  HTML Structure")
    print("-" * 70)

    if 'id="unauthorizedAbsenceChart"' in html_content:
        results['passed'].append("✅ Canvas for Chart 5 exists")
        print("✅ Canvas #unauthorizedAbsenceChart: EXISTS")
    else:
        results['failed'].append("❌ Canvas for Chart 5 missing")
        print("❌ Canvas #unauthorizedAbsenceChart: MISSING")

    if 'id="absenceRateChart"' in html_content:
        results['passed'].append("✅ Canvas for Chart 6 exists")
        print("✅ Canvas #absenceRateChart: EXISTS")
    else:
        results['failed'].append("❌ Canvas for Chart 6 missing")
        print("❌ Canvas #absenceRateChart: MISSING")

    # Data comparison
    print("\n📊 데이터 비교 (Data Comparison)")
    print("-" * 70)
    print("차이점: 무단 결근율 vs 전체 결근율")
    print("")
    print("Month       | 무단 결근율    | 전체 결근율    | 차이")
    print("-" * 70)

    for month in sorted(monthly_metrics.keys()):
        unauth = monthly_metrics[month]['unauthorized_absence_rate']
        total = monthly_metrics[month]['absence_rate']
        diff = total - unauth
        print(f"{month}  | {unauth:>6}%      | {total:>6}%      | {diff:>6.2f}%")

    print("")
    print("💡 무단 결근율은 전체 결근율의 부분집합입니다.")
    print("   (Unauthorized absence is a subset of total absence)")

    # Final Summary
    print("\n" + "=" * 70)
    print("📊 최종 검증 결과 (Final Verification Results)")
    print("=" * 70)
    print(f"✅ Passed: {len(results['passed'])} tests")
    print(f"❌ Failed: {len(results['failed'])} tests")

    if results['failed']:
        print("\n❌ Failed Tests:")
        for failure in results['failed']:
            print(f"   {failure}")

    print("\n" + "=" * 70)

    success = len(results['failed']) == 0

    if success:
        print("🎉 완벽합니다! 두 차트 모두 정상 작동합니다.")
        print("   (Perfect! Both charts are working correctly.)")
        print("")
        print("📌 요약:")
        print("   • Chart 5: 무단 결근율 (%) - Bar chart with percentage")
        print("   • Chart 6: 결근율 (%) - Line chart with percentage")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        print("   (Some tests failed.)")

    print("=" * 70)

    return success


if __name__ == '__main__':
    success = final_verification()
    exit(0 if success else 1)
