#!/usr/bin/env python3
"""
verify_chart_data_sources.py - Verify data sources for new trend charts
새로운 추세 차트의 데이터 소스 검증
"""

import json
import re
from pathlib import Path


def verify_data_sources():
    """Verify that chart data sources exist in monthlyMetrics"""

    html_path = Path('output_files/HR_Dashboard_2025_10.html')

    if not html_path.exists():
        print(f"❌ Dashboard file not found: {html_path}")
        return False

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print("=" * 70)
    print("🔍 Verifying Chart Data Sources")
    print("=" * 70)

    # Extract monthlyMetrics JSON
    metrics_pattern = r'const monthlyMetrics =\s*(\{.*?\})\s*;'
    metrics_match = re.search(metrics_pattern, html_content, re.DOTALL)

    if not metrics_match:
        print("❌ Could not find monthlyMetrics in HTML")
        return False

    try:
        monthly_metrics = json.loads(metrics_match.group(1))
        print(f"✅ Found monthlyMetrics with {len(monthly_metrics)} months")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse monthlyMetrics: {e}")
        return False

    # Get one month's data to see available keys
    sample_month = list(monthly_metrics.keys())[0]
    available_keys = list(monthly_metrics[sample_month].keys())

    print(f"\n📊 Available metrics in monthlyMetrics['{sample_month}']:")
    print("-" * 70)
    for key in sorted(available_keys):
        value = monthly_metrics[sample_month][key]
        print(f"   • {key}: {value}")

    # Check what Chart 5 is requesting
    print("\n🔍 Chart 5: Unauthorized Absence Chart")
    print("-" * 70)

    chart5_pattern = r"getTrendData\('([^']+)'\)[^}]*?// Chart 5"
    chart5_matches = re.findall(r"getTrendData\('([^']+)'\)", html_content[30000:31100])

    if chart5_matches:
        requested_key = chart5_matches[0]
        print(f"   Requested data: '{requested_key}'")

        if requested_key in available_keys:
            print(f"   ✅ '{requested_key}' exists in monthlyMetrics")

            # Show actual values
            print(f"\n   📈 Actual values:")
            for month in sorted(monthly_metrics.keys()):
                value = monthly_metrics[month][requested_key]
                print(f"      {month}: {value}")
        else:
            print(f"   ❌ '{requested_key}' NOT found in monthlyMetrics")
            print(f"\n   💡 Suggestions:")
            print(f"      - Available: {', '.join(available_keys)}")

            # Suggest correct key
            if 'unauthorized_absence_rate' in available_keys:
                print(f"      - Did you mean 'unauthorized_absence_rate'?")
            if 'unauthorized_absence' in available_keys:
                print(f"      - Did you mean 'unauthorized_absence'?")
    else:
        print("   ❌ Could not find Chart 5 data source")

    # Check what Chart 6 is requesting
    print("\n🔍 Chart 6: Absence Rate Chart")
    print("-" * 70)

    chart6_pattern = r"label: '결근율.*?data: getTrendData\('([^']+)'\)"
    chart6_match = re.search(chart6_pattern, html_content, re.DOTALL)

    if chart6_match:
        requested_key = chart6_match.group(1)
        print(f"   Requested data: '{requested_key}'")

        if requested_key in available_keys:
            print(f"   ✅ '{requested_key}' exists in monthlyMetrics")

            # Show actual values
            print(f"\n   📈 Actual values:")
            for month in sorted(monthly_metrics.keys()):
                value = monthly_metrics[month][requested_key]
                print(f"      {month}: {value}%")
        else:
            print(f"   ❌ '{requested_key}' NOT found in monthlyMetrics")
            print(f"\n   💡 Suggestions:")
            print(f"      - Available: {', '.join(available_keys)}")
    else:
        print("   ❌ Could not find Chart 6 data source")

    print("\n" + "=" * 70)
    print("💡 Recommendation")
    print("=" * 70)

    if 'unauthorized_absence_count' not in available_keys:
        print("⚠️  'unauthorized_absence_count' does NOT exist in the data!")
        print("")
        print("Available options for unauthorized absence:")
        if 'unauthorized_absence_rate' in available_keys:
            print("   • unauthorized_absence_rate (현재 사용 가능) - 무단 결근율 (%)")
        print("")
        print("🔧 Recommendation:")
        print("   Chart 5 should use 'unauthorized_absence_rate' instead of")
        print("   'unauthorized_absence_count' since count data is not available.")
        print("")
        print("   Or, the backend needs to calculate and add")
        print("   'unauthorized_absence_count' to monthlyMetrics.")

    print("=" * 70)


if __name__ == '__main__':
    verify_data_sources()
