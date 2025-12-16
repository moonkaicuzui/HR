#!/usr/bin/env python3
"""
get_employee_details.py - Get detailed info for specific employees
특정 직원 상세 정보 조회
"""

import pandas as pd
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.monthly_data_collector import MonthlyDataCollector


def get_employee_details():
    """Get details for QIP SAP & INCOMING REPORT and LINE LEADER employees"""

    hr_root = Path(__file__).parent
    collector = MonthlyDataCollector(hr_root)

    target_month = '2025-10'
    data = collector.load_month_data(target_month)
    df = data.get('basic_manpower', pd.DataFrame())

    if df.empty:
        print(f"❌ No data for {target_month}")
        return

    print("=" * 100)
    print("🔍 확인 필요 직원 상세 정보")
    print("=" * 100)

    # Target position_3rd values
    target_pos3 = [
        'QIP SAP & INCOMING QUALITY REPORT ',
        'LINE LEADER(GROUP LEADER SUCCESSOR)'
    ]

    for pos3 in target_pos3:
        employees = df[df['QIP POSITION 3RD  NAME'] == pos3]

        if employees.empty:
            print(f"\n❌ {pos3}: 데이터 없음")
            continue

        print(f"\n{'='*100}")
        print(f"📌 Position 3rd: {pos3}")
        print(f"   인원: {len(employees)}명")
        print(f"{'='*100}")

        for idx, row in employees.iterrows():
            print(f"\n직원 #{employees.index.get_loc(idx) + 1}:")
            print("-" * 100)

            # Basic info
            print(f"📋 기본 정보:")
            print(f"   • Employee No: {row.get('Employee No', '')}")
            print(f"   • Full Name: {row.get('Full Name', '')}")
            print(f"   • Entrance Date: {row.get('Entrance Date', '')}")
            print(f"   • Stop Working Date: {row.get('Stop working Date', '')}")

            # Position info
            print(f"\n📊 직급 정보:")
            print(f"   • Position 1st: {row.get('QIP POSITION 1ST  NAME', '')}")
            print(f"   • Position 2nd: {row.get('QIP POSITION 2ND  NAME', '')}")
            print(f"   • Position 3rd: {row.get('QIP POSITION 3RD  NAME', '')}")

            # Boss info
            print(f"\n👔 보고 체계:")
            print(f"   • MST direct boss name: {row.get('MST direct boss name', '')}")
            print(f"   • MST direct boss ID: {row.get('Direct_Manager_ID', '')}")

            # Role info
            print(f"\n🎯 역할:")
            print(f"   • ROLE TYPE STD: {row.get('ROLE TYPE STD', '')}")
            print(f"   • Department: {row.get('Department', '')}")
            print(f"   • Section: {row.get('Section', '')}")

            # Work location
            print(f"\n🏢 근무지:")
            print(f"   • Building: {row.get('Building', '')}")
            print(f"   • Floor: {row.get('Floor', '')}")

            # Additional columns that might be helpful
            if 'Job Title' in row:
                print(f"\n💼 추가 정보:")
                print(f"   • Job Title: {row.get('Job Title', '')}")

            # Check if there are any keywords in name or position that hint at team
            full_name = str(row.get('Full Name', ''))
            pos1 = str(row.get('QIP POSITION 1ST  NAME', ''))
            pos2 = str(row.get('QIP POSITION 2ND  NAME', ''))

            print(f"\n🔍 팀 배정 힌트:")

            # Analyze position keywords
            if 'INCOMING' in pos3.upper() or 'SAP' in pos3.upper():
                print(f"   ⭐ 'INCOMING', 'SAP' 키워드 → OSC 팀 가능성")

            if 'REPORT' in pos3.upper() or 'REPORT' in pos2.upper():
                print(f"   ⭐ 'REPORT' 키워드 → OFFICE & OCPT 팀 가능성")

            if 'LINE LEADER' in pos3.upper() or 'LINE LEADER' in pos1.upper():
                print(f"   ⭐ 'LINE LEADER' → 관리직, OFFICE & OCPT 가능성")
                if 'ASSEMBLY' in pos2.upper():
                    print(f"   ⭐ Position 2nd에 'ASSEMBLY' 없음 → ASSEMBLY 팀 아님")
                elif 'STITCHING' in pos2.upper():
                    print(f"   ⭐ Position 2nd에 'STITCHING' 없음 → STITCHING 팀 아님")
                else:
                    print(f"   ⭐ 일반 LINE LEADER → OFFICE & OCPT 팀 추천")

    print(f"\n{'='*100}")
    print("💡 권장사항:")
    print("=" * 100)
    print("\n1. QIP SAP & INCOMING QUALITY REPORT:")
    print("   • 'INCOMING' 키워드가 있으면 → OSC 팀")
    print("   • 'REPORT' 역할이 강하면 → OFFICE & OCPT 팀")
    print("   • 직원의 실제 업무 내용에 따라 결정 필요")

    print("\n2. LINE LEADER(GROUP LEADER SUCCESSOR):")
    print("   • 특정 생산 라인 담당이면 → 해당 팀 (ASSEMBLY/STITCHING)")
    print("   • 일반 관리/감독 역할이면 → OFFICE & OCPT 팀")
    print("   • Position 2nd가 'LINE LEADER(GROUP LEADER SUCCESSOR)'로 동일 → OFFICE & OCPT 추천")

    print(f"\n{'='*100}")


if __name__ == '__main__':
    get_employee_details()
