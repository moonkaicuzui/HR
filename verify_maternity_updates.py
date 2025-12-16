#!/usr/bin/env python3
"""
verify_maternity_updates.py - Verify maternity leave updates in dashboard
출산 휴가 업데이트 검증
"""

import json
import re
from pathlib import Path


def verify_updates():
    """Verify all maternity leave related updates"""

    html_path = Path('output_files/HR_Dashboard_2025_10.html')

    if not html_path.exists():
        print(f"❌ Dashboard file not found: {html_path}")
        return False

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print("=" * 70)
    print("🔍 출산 휴가 업데이트 검증")
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

    # Test 1: New metrics exist
    print("\n📊 Test 1: 새로운 메트릭 존재 확인")
    print("-" * 70)

    sample_month = '2025-10'
    metrics = monthly_metrics[sample_month]

    if 'absence_rate_excl_maternity' in metrics:
        results['passed'].append("✅ absence_rate_excl_maternity metric exists")
        print(f"✅ absence_rate_excl_maternity: {metrics['absence_rate_excl_maternity']}%")
    else:
        results['failed'].append("❌ absence_rate_excl_maternity metric NOT found")
        print("❌ absence_rate_excl_maternity NOT found")

    if 'maternity_leave_count' in metrics:
        results['passed'].append("✅ maternity_leave_count metric exists")
        print(f"✅ maternity_leave_count: {metrics['maternity_leave_count']}명")
    else:
        results['failed'].append("❌ maternity_leave_count metric NOT found")
        print("❌ maternity_leave_count NOT found")

    # Test 2: Chart 6 has two lines
    print("\n📈 Test 2: Chart 6 (결근율 차트) - 두 개의 라인 확인")
    print("-" * 70)

    chart6_section = html_content[html_content.find("Chart 6:"):html_content.find("Chart 6:")+2000]

    if "'absence_rate_excl_maternity'" in chart6_section:
        results['passed'].append("✅ Chart 6 uses absence_rate_excl_maternity")
        print("✅ Chart 6 uses absence_rate_excl_maternity data source")
    else:
        results['failed'].append("❌ Chart 6 missing absence_rate_excl_maternity")
        print("❌ Chart 6 missing absence_rate_excl_maternity")

    if "결근율 (출산휴가 포함)" in chart6_section:
        results['passed'].append("✅ Chart 6 has '출산휴가 포함' label")
        print("✅ Chart 6 label: '결근율 (출산휴가 포함)'")
    else:
        results['failed'].append("❌ Chart 6 missing '출산휴가 포함' label")
        print("❌ Chart 6 missing '출산휴가 포함' label")

    if "결근율 (출산휴가 제외)" in chart6_section:
        results['passed'].append("✅ Chart 6 has '출산휴가 제외' label")
        print("✅ Chart 6 label: '결근율 (출산휴가 제외)'")
    else:
        results['failed'].append("❌ Chart 6 missing '출산휴가 제외' label")
        print("❌ Chart 6 missing '출산휴가 제외' label")

    if "borderDash: [5, 5]" in chart6_section:
        results['passed'].append("✅ Chart 6 has dashed line for excl. maternity")
        print("✅ Chart 6 uses dashed line (borderDash: [5, 5])")
    else:
        results['failed'].append("❌ Chart 6 missing dashed line")
        print("❌ Chart 6 missing dashed line")

    # Test 3: Chart 2 has maternity leave dataset
    print("\n👶 Test 3: Chart 2 (신규 입사/퇴사 차트) - 출산 휴가자 추가 확인")
    print("-" * 70)

    chart2_section = html_content[html_content.find("Chart 2:"):html_content.find("Chart 2:")+2000]

    if "'maternity_leave_count'" in chart2_section:
        results['passed'].append("✅ Chart 2 uses maternity_leave_count")
        print("✅ Chart 2 uses maternity_leave_count data source")
    else:
        results['failed'].append("❌ Chart 2 missing maternity_leave_count")
        print("❌ Chart 2 missing maternity_leave_count")

    if "출산 휴가자 / Maternity Leave" in chart2_section:
        results['passed'].append("✅ Chart 2 has '출산 휴가자' label")
        print("✅ Chart 2 label: '출산 휴가자 / Maternity Leave'")
    else:
        results['failed'].append("❌ Chart 2 missing '출산 휴가자' label")
        print("❌ Chart 2 missing '출산 휴가자' label")

    if "#ff69b4" in chart2_section:
        results['passed'].append("✅ Chart 2 uses pink color for maternity")
        print("✅ Chart 2 color: Pink (#ff69b4)")
    else:
        results['failed'].append("❌ Chart 2 missing pink color")
        print("❌ Chart 2 missing pink color")

    # Test 4: Data validation
    print("\n📊 Test 4: 데이터 정확성 검증")
    print("-" * 70)

    print("\n월별 출산 휴가자 수:")
    for month in sorted(monthly_metrics.keys()):
        count = monthly_metrics[month].get('maternity_leave_count', 0)
        print(f"   • {month}: {count}명")

    print("\n월별 결근율 비교:")
    print("Month       | 포함     | 제외     | 차이")
    print("-" * 60)
    for month in sorted(monthly_metrics.keys()):
        incl = monthly_metrics[month].get('absence_rate', 0)
        excl = monthly_metrics[month].get('absence_rate_excl_maternity', 0)
        diff = incl - excl
        print(f"{month}  | {incl:>6}% | {excl:>6}% | {diff:>6.1f}%")

    # Final summary
    print("\n" + "=" * 70)
    print("📊 검증 결과 요약")
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
        print("🎉 모든 업데이트가 정상적으로 적용되었습니다!")
        print("\n📌 변경사항 요약:")
        print("   1. Chart 6: 결근율 차트에 두 개의 라인")
        print("      • 주황색 실선: 출산휴가 포함")
        print("      • 녹색 점선: 출산휴가 제외")
        print("   2. Chart 2: 신규 입사/퇴사 차트에 출산휴가자 추가")
        print("      • 분홍색 bar: 출산 휴가자")
    else:
        print("⚠️  일부 업데이트가 누락되었습니다.")

    print("=" * 70)

    return success


if __name__ == '__main__':
    success = verify_updates()
    exit(0 if success else 1)
