#!/usr/bin/env python3
"""
analyze_team_mapping_feasibility.py - Analyze feasibility of applying original team logic
원조 팀 로직 적용 가능성 분석
"""

import pandas as pd
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.monthly_data_collector import MonthlyDataCollector


def analyze_position_fields():
    """Analyze position fields to see if we can map to 12 original teams"""

    hr_root = Path(__file__).parent
    collector = MonthlyDataCollector(hr_root)

    target_month = '2025-10'
    data = collector.load_month_data(target_month)
    df = data.get('basic_manpower', pd.DataFrame())

    if df.empty:
        print(f"❌ No data for {target_month}")
        return

    print("=" * 80)
    print("🔍 원조 팀 로직 적용 가능성 분석")
    print("=" * 80)

    # Original 12 teams from management_dashboard
    original_teams = [
        "OFFICE & OCPT",
        "OSC",
        "ASSEMBLY",
        "BOTTOM",
        "QA",
        "MTL",
        "AQL",
        "STITCHING",
        "HWK QIP",
        "CUTTING",
        "REPACKING",
        "NEW"
    ]

    print(f"\n📋 원조 대시보드 12개 팀:")
    for i, team in enumerate(original_teams, 1):
        print(f"   {i}. {team}")

    # Analyze current position fields
    print(f"\n📊 현재 데이터의 Position 필드 분석 ({target_month}):")
    print("-" * 80)

    # Position 1st (직급)
    print("\n1️⃣ QIP POSITION 1ST NAME (직급):")
    pos1_counts = df['QIP POSITION 1ST  NAME'].value_counts()
    for pos, count in pos1_counts.items():
        print(f"   • {pos}: {count}명")

    # Position 2nd (팀)
    print("\n2️⃣ QIP POSITION 2ND NAME (팀):")
    pos2_counts = df['QIP POSITION 2ND  NAME'].value_counts()
    for pos, count in pos2_counts.items():
        print(f"   • {pos}: {count}명")

    # Position 3rd (부서) - This is KEY for team mapping
    print("\n3️⃣ QIP POSITION 3RD NAME (부서) - ⭐ 팀 매핑 키:")
    pos3_counts = df['QIP POSITION 3RD  NAME'].value_counts()
    print(f"\n총 {len(pos3_counts)}개 고유 값:")
    for pos, count in pos3_counts.items():
        print(f"   • {pos}: {count}명")

    # Try to map position_3rd to original teams
    print("\n" + "=" * 80)
    print("🔍 Position 3rd → 원조 12개 팀 매핑 분석")
    print("=" * 80)

    # Create mapping dictionary (based on pattern analysis)
    team_mapping = {}

    for idx, row in df.iterrows():
        pos3 = str(row.get('QIP POSITION 3RD  NAME', ''))
        pos2 = str(row.get('QIP POSITION 2ND  NAME', ''))
        pos1 = str(row.get('QIP POSITION 1ST  NAME', ''))

        if pos3 and pos3 != 'nan':
            # Analyze patterns
            pos3_upper = pos3.upper()

            # Try keyword matching
            if 'ASSEMBLY' in pos3_upper or 'GIÀY' in pos3_upper:
                team_name = 'ASSEMBLY'
            elif 'OSC' in pos3_upper or 'MTL' in pos3_upper:
                team_name = 'OSC'
            elif 'BOTTOM' in pos3_upper or 'ĐẾ' in pos3_upper:
                team_name = 'BOTTOM'
            elif 'STITCHING' in pos3_upper or 'MAY' in pos3_upper:
                team_name = 'STITCHING'
            elif 'AQL' in pos3_upper:
                team_name = 'AQL'
            elif 'CUTTING' in pos3_upper or 'CẮT' in pos3_upper:
                team_name = 'CUTTING'
            elif 'REPACKING' in pos3_upper:
                team_name = 'REPACKING'
            elif 'OFFICE' in pos3_upper or 'REPORT' in pos3_upper:
                team_name = 'OFFICE & OCPT'
            elif 'HWK' in pos3_upper:
                team_name = 'HWK QIP'
            elif 'NEW' in pos3_upper or pos1 == 'NEW QIP':
                team_name = 'NEW'
            elif 'QA' in pos3_upper:
                team_name = 'QA'
            else:
                team_name = 'UNKNOWN'

            if team_name not in team_mapping:
                team_mapping[team_name] = {
                    'count': 0,
                    'pos3_values': set(),
                    'examples': []
                }

            team_mapping[team_name]['count'] += 1
            team_mapping[team_name]['pos3_values'].add(pos3)

            if len(team_mapping[team_name]['examples']) < 3:
                team_mapping[team_name]['examples'].append({
                    'name': row.get('Full Name', ''),
                    'pos1': pos1,
                    'pos2': pos2,
                    'pos3': pos3
                })

    # Display mapping results
    print("\n매핑 결과:")
    print("-" * 80)

    total_mapped = 0
    total_employees = len(df)

    for team in original_teams:
        if team in team_mapping:
            info = team_mapping[team]
            total_mapped += info['count']
            print(f"\n✅ {team}: {info['count']}명")
            print(f"   Position 3rd 값들:")
            for val in sorted(info['pos3_values']):
                print(f"      • {val}")
            print(f"   예시:")
            for ex in info['examples'][:2]:
                print(f"      • {ex['name']}: {ex['pos1']} / {ex['pos2']} / {ex['pos3']}")
        else:
            print(f"\n❌ {team}: 0명 (매핑 실패)")

    if 'UNKNOWN' in team_mapping:
        info = team_mapping['UNKNOWN']
        print(f"\n⚠️  UNKNOWN (미분류): {info['count']}명")
        print(f"   Position 3rd 값들:")
        for val in sorted(info['pos3_values']):
            print(f"      • {val}")

    # Summary
    print("\n" + "=" * 80)
    print("📊 매핑 요약")
    print("=" * 80)
    print(f"총 직원 수: {total_employees}명")
    print(f"매핑 성공: {total_mapped}명 ({total_mapped/total_employees*100:.1f}%)")

    if 'UNKNOWN' in team_mapping:
        unknown_count = team_mapping['UNKNOWN']['count']
        print(f"미분류: {unknown_count}명 ({unknown_count/total_employees*100:.1f}%)")

    # Feasibility assessment
    print("\n" + "=" * 80)
    print("💡 적용 가능성 평가")
    print("=" * 80)

    coverage = (total_mapped / total_employees * 100) if total_employees > 0 else 0

    if coverage >= 95:
        print("✅ 매우 높음 (95%+ 커버리지)")
        print("   → 원조 팀 로직 적용 권장")
    elif coverage >= 85:
        print("⚠️  중간 (85-95% 커버리지)")
        print("   → 미분류 항목 처리 후 적용 가능")
    else:
        print("❌ 낮음 (<85% 커버리지)")
        print("   → 현재 동적 방식 유지 권장")

    # Comparison with current approach
    print("\n" + "=" * 80)
    print("🔄 현재 방식 vs 원조 방식 비교")
    print("=" * 80)

    current_teams = df['QIP POSITION 1ST  NAME'].nunique()
    print(f"\n현재 방식 (position_1st):")
    print(f"   • 팀 수: {current_teams}개")
    print(f"   • 장점: 완전 자동, 데이터 변경 시 자동 반영")
    print(f"   • 단점: 팀 이름이 직급명 (ASSEMBLY INSPECTOR, LINE LEADER 등)")

    print(f"\n원조 방식 (position_3rd 매핑):")
    print(f"   • 팀 수: 12개 (고정)")
    print(f"   • 장점: 명확한 팀 이름 (ASSEMBLY, OSC, QA 등)")
    print(f"   • 단점: 매핑 로직 관리 필요, 신규 팀 추가 시 코드 수정")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    analyze_position_fields()
