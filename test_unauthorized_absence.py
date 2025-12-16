#!/usr/bin/env python3
"""
Test script for validating the Unauthorized Absence Analysis improvements
무단결근 분석 개선사항 검증 스크립트
"""

import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.monthly_data_collector import MonthlyDataCollector
from src.analytics.hr_metric_calculator import HRMetricCalculator
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder


def main():
    print("=" * 80)
    print("무단결근율 분석 개선사항 검증 (Unauthorized Absence Analysis Validation)")
    print("=" * 80)

    # Initialize components
    hr_root = Path(__file__).parent
    collector = MonthlyDataCollector(hr_root)

    # Detect available months
    available_months = collector.detect_available_months()
    print(f"\n📅 사용 가능한 월 (Available months): {available_months}")

    if not available_months:
        print("❌ No data available")
        return

    # Calculate metrics
    calculator = HRMetricCalculator(collector)
    metrics = calculator.calculate_all_metrics(available_months)

    # Get the latest month
    latest_month = available_months[-1]
    print(f"\n🎯 검증 대상 월 (Target month): {latest_month}")

    # Validation Checklist
    print("\n" + "=" * 80)
    print("검증 체크리스트 (Validation Checklist)")
    print("=" * 80)

    checklist = {
        "1. 데이터 완전성 (Data Completeness)": False,
        "2. 팀별 차별화된 무단결근율 (Team-specific Rates)": False,
        "3. 언어 일관성 (Language Consistency)": False,
        "4. 시각화 요소 (Visualization Elements)": False,
        "5. 데이터 신뢰도 (Data Reliability)": False
    }

    # Test 1: Data Completeness
    print("\n✅ Test 1: 데이터 완전성 검사")
    if latest_month in metrics:
        month_data = metrics[latest_month]
        required_fields = ['unauthorized_absence_rate', 'team_unauthorized_rates']
        missing = [f for f in required_fields if f not in month_data]

        if not missing:
            print("   ✓ 모든 필수 필드 존재")
            checklist["1. 데이터 완전성 (Data Completeness)"] = True
        else:
            print(f"   ✗ 누락된 필드: {missing}")

    # Test 2: Team-specific Rates
    print("\n✅ Test 2: 팀별 무단결근율 차별화 검사")
    if 'team_unauthorized_rates' in metrics[latest_month]:
        team_rates = metrics[latest_month]['team_unauthorized_rates']
        unique_rates = set(team_rates.values())

        print(f"   팀 수: {len(team_rates)}")
        print(f"   고유한 무단결근율 값 수: {len(unique_rates)}")

        if len(unique_rates) > 1:
            print("   ✓ 팀별로 차별화된 무단결근율 확인")
            checklist["2. 팀별 차별화된 무단결근율 (Team-specific Rates)"] = True

            # Show team rates
            print("\n   팀별 무단결근율:")
            for team, rate in sorted(team_rates.items(), key=lambda x: x[1], reverse=True):
                status = "⚠️" if rate > 0.5 else "✅"
                print(f"      {status} {team:30s}: {rate:5.2f}%")
        else:
            print("   ✗ 모든 팀이 동일한 무단결근율 (문제 발견!)")

    # Test 3: Language Consistency
    print("\n✅ Test 3: 언어 일관성 검사")
    builder = CompleteDashboardBuilder(latest_month)
    html_content = builder.build()

    # Check for mixed language patterns
    korean_english_mixed = [
        ("Unauthorized Absence Analysis", "무단결근율"),
        ("Overall Unauthorized Rate", "전체 무단결근율")
    ]

    issues = []
    for eng, kor in korean_english_mixed:
        if eng in html_content and kor not in html_content:
            issues.append(f"English only: {eng}")
        elif eng not in html_content and kor in html_content:
            issues.append(f"Korean only: {kor}")

    if not issues:
        print("   ✓ 언어 정책 준수 (Korean primary, English secondary)")
        checklist["3. 언어 일관성 (Language Consistency)"] = True
    else:
        print(f"   ✗ 언어 일관성 문제: {issues}")

    # Test 4: Visualization Elements
    print("\n✅ Test 4: 시각화 요소 검사")
    required_elements = [
        'modalChart3_trend',      # Trend chart
        'modalChart3_diverging',  # Diverging bar chart
        'modalChart3_donut',      # Donut chart
        'teamDetailTable'         # Team detail table
    ]

    missing_elements = [elem for elem in required_elements if elem not in html_content]

    if not missing_elements:
        print("   ✓ 모든 시각화 요소 구현됨")
        checklist["4. 시각화 요소 (Visualization Elements)"] = True
    else:
        print(f"   ✗ 누락된 요소: {missing_elements}")

    # Test 5: Data Reliability
    print("\n✅ Test 5: 데이터 신뢰도 검사")
    if 'team_unauthorized_rates' in metrics[latest_month]:
        team_rates = metrics[latest_month]['team_unauthorized_rates']

        # Check for reasonable rates (0-10% range typically)
        unreasonable = [t for t, r in team_rates.items() if r > 10 or r < 0]

        if not unreasonable:
            print("   ✓ 모든 무단결근율이 합리적인 범위 내 (0-10%)")
            checklist["5. 데이터 신뢰도 (Data Reliability)"] = True
        else:
            print(f"   ✗ 비정상적인 무단결근율 발견: {unreasonable}")

    # Summary
    print("\n" + "=" * 80)
    print("검증 결과 요약 (Validation Summary)")
    print("=" * 80)

    passed = sum(checklist.values())
    total = len(checklist)

    for test, result in checklist.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test}")

    print(f"\n최종 결과: {passed}/{total} 테스트 통과")

    if passed == total:
        print("🎉 모든 검증 통과! 개선사항이 성공적으로 구현되었습니다.")
    else:
        print(f"⚠️  {total - passed}개 테스트 실패. 추가 수정이 필요합니다.")

    # Save test report
    report_path = hr_root / "test_report_unauthorized_absence.json"
    report = {
        "test_date": str(Path(__file__).stat().st_mtime),
        "target_month": latest_month,
        "checklist": checklist,
        "team_rates": metrics[latest_month].get('team_unauthorized_rates', {}),
        "overall_rate": metrics[latest_month].get('unauthorized_absence_rate', 0),
        "passed": passed,
        "total": total
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 검증 리포트 저장: {report_path}")


if __name__ == "__main__":
    main()