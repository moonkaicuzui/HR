#!/usr/bin/env python3
"""
test_new_trend_charts.py - Verify new trend charts (Unauthorized Absence & Absence Rate)
새로운 추세 차트 검증 (무단 결근 차트 & 결근율 차트)
"""

import re
from pathlib import Path


def test_new_charts():
    """Test that the two new trend charts are properly implemented"""

    html_path = Path('output_files/HR_Dashboard_2025_10.html')

    if not html_path.exists():
        print(f"❌ Dashboard file not found: {html_path}")
        return False

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print("=" * 70)
    print("🧪 Testing New Trend Charts Implementation")
    print("=" * 70)

    results = {
        'passed': [],
        'failed': []
    }

    # Test 1: Canvas elements exist
    print("\n📋 Test 1: HTML Canvas Elements")
    print("-" * 70)

    unauthorized_canvas = 'id="unauthorizedAbsenceChart"' in html_content
    absence_rate_canvas = 'id="absenceRateChart"' in html_content

    if unauthorized_canvas:
        results['passed'].append("✅ Unauthorized Absence canvas element found")
        print("✅ Unauthorized Absence canvas element found")
    else:
        results['failed'].append("❌ Unauthorized Absence canvas element NOT found")
        print("❌ Unauthorized Absence canvas element NOT found")

    if absence_rate_canvas:
        results['passed'].append("✅ Absence Rate canvas element found")
        print("✅ Absence Rate canvas element found")
    else:
        results['failed'].append("❌ Absence Rate canvas element NOT found")
        print("❌ Absence Rate canvas element NOT found")

    # Test 2: Chart 5 JavaScript implementation
    print("\n📊 Test 2: Chart 5 - Unauthorized Absence Chart JavaScript")
    print("-" * 70)

    chart5_pattern = r"// Chart 5: Unauthorized Absence\s+new Chart\(document\.getElementById\('unauthorizedAbsenceChart'\)"
    chart5_match = re.search(chart5_pattern, html_content)

    if chart5_match:
        results['passed'].append("✅ Chart 5 JavaScript implementation found")
        print("✅ Chart 5 JavaScript implementation found")

        # Check key features
        if "getTrendData('unauthorized_absence_count')" in html_content:
            results['passed'].append("✅ Chart 5 uses correct data source (unauthorized_absence_count)")
            print("   ✓ Uses correct data source (unauthorized_absence_count)")
        else:
            results['failed'].append("❌ Chart 5 data source incorrect")
            print("   ✗ Data source incorrect")

        if "'무단 결근 / Unauthorized Absence'" in html_content:
            results['passed'].append("✅ Chart 5 has bilingual label")
            print("   ✓ Has bilingual label (Korean/English)")
        else:
            results['failed'].append("❌ Chart 5 label missing")
            print("   ✗ Label missing")

        if "return value + '건';" in html_content:
            results['passed'].append("✅ Chart 5 has Korean unit formatting (건)")
            print("   ✓ Has Korean unit formatting (건)")
        else:
            results['failed'].append("❌ Chart 5 unit formatting missing")
            print("   ✗ Unit formatting missing")
    else:
        results['failed'].append("❌ Chart 5 JavaScript implementation NOT found")
        print("❌ Chart 5 JavaScript implementation NOT found")

    # Test 3: Chart 6 JavaScript implementation
    print("\n📈 Test 3: Chart 6 - Absence Rate Chart JavaScript")
    print("-" * 70)

    chart6_pattern = r"// Chart 6: Absence Rate\s+new Chart\(document\.getElementById\('absenceRateChart'\)"
    chart6_match = re.search(chart6_pattern, html_content)

    if chart6_match:
        results['passed'].append("✅ Chart 6 JavaScript implementation found")
        print("✅ Chart 6 JavaScript implementation found")

        # Check key features
        if "getTrendData('absence_rate')" in html_content:
            results['passed'].append("✅ Chart 6 uses correct data source (absence_rate)")
            print("   ✓ Uses correct data source (absence_rate)")
        else:
            results['failed'].append("❌ Chart 6 data source incorrect")
            print("   ✗ Data source incorrect")

        if "'결근율 (%) / Absence Rate'" in html_content:
            results['passed'].append("✅ Chart 6 has bilingual label")
            print("   ✓ Has bilingual label (Korean/English)")
        else:
            results['failed'].append("❌ Chart 6 label missing")
            print("   ✗ Label missing")

        if "return value.toFixed(1) + '%';" in html_content:
            results['passed'].append("✅ Chart 6 has percentage formatting")
            print("   ✓ Has percentage formatting")
        else:
            results['failed'].append("❌ Chart 6 percentage formatting missing")
            print("   ✗ Percentage formatting missing")

        if "type: 'line'" in html_content[chart6_match.start():chart6_match.start()+1000]:
            results['passed'].append("✅ Chart 6 is line chart (correct type)")
            print("   ✓ Is line chart (correct type)")
        else:
            results['failed'].append("❌ Chart 6 type incorrect")
            print("   ✗ Chart type incorrect")
    else:
        results['failed'].append("❌ Chart 6 JavaScript implementation NOT found")
        print("❌ Chart 6 JavaScript implementation NOT found")

    # Test 4: Row 3 structure
    print("\n🏗️  Test 4: Row 3 HTML Structure")
    print("-" * 70)

    row3_pattern = r'<!-- Row 3: Unauthorized Absence & Absence Rate -->'
    if re.search(row3_pattern, html_content):
        results['passed'].append("✅ Row 3 HTML comment found")
        print("✅ Row 3 HTML comment found")

        # Check that both charts are in Row 3
        row3_section = html_content[html_content.find('<!-- Row 3:'):html_content.find('<!-- Row 3:')+2000]

        if 'unauthorizedAbsenceChart' in row3_section and 'absenceRateChart' in row3_section:
            results['passed'].append("✅ Both charts in Row 3 structure")
            print("   ✓ Both charts properly placed in Row 3")
        else:
            results['failed'].append("❌ Charts not properly placed in Row 3")
            print("   ✗ Charts not properly placed in Row 3")
    else:
        results['failed'].append("❌ Row 3 HTML structure NOT found")
        print("❌ Row 3 HTML structure NOT found")

    # Final Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
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
        print("🎉 All tests passed! Both new trend charts are properly implemented.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")

    print("=" * 70)

    return success


if __name__ == '__main__':
    success = test_new_charts()
    exit(0 if success else 1)
