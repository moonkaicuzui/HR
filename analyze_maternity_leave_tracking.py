#!/usr/bin/env python3
"""
analyze_maternity_leave_tracking.py - Analyze maternity leave tracking feasibility
출산 휴가자 추적 가능성 분석
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def analyze_maternity_tracking():
    """Analyze if we can track maternity leave employees across months"""

    print("=" * 70)
    print("🔍 출산 휴가자 월별 추적 가능성 분석")
    print("=" * 70)

    months = ['july', 'august', 'september', 'october']
    month_names_ko = ['7월', '8월', '9월', '10월']

    maternity_data = {}

    for month, month_ko in zip(months, month_names_ko):
        file_path = Path(f"input_files/attendance/converted/attendance data {month}_converted.csv")

        if not file_path.exists():
            print(f"\n⚠️  {month_ko} 데이터 없음: {file_path}")
            continue

        df = pd.read_csv(file_path)

        # Find maternity leave records
        maternity_keywords = ['Sinh', 'sinh', 'Dưỡng sinh', 'Khám thai']
        maternity_mask = df['Reason Description'].str.contains(
            '|'.join(maternity_keywords), na=False, case=False
        )

        maternity_records = df[maternity_mask]

        if not maternity_records.empty:
            # Get unique employees on maternity leave
            maternity_employees = maternity_records['ID No'].unique()

            maternity_data[month_ko] = {
                'count': len(maternity_employees),
                'employees': set(maternity_employees),
                'records': len(maternity_records),
                'reasons': maternity_records['Reason Description'].value_counts().to_dict()
            }

            print(f"\n📊 {month_ko} 출산 휴가 데이터:")
            print(f"   • 출산 휴가자 수: {len(maternity_employees)}명")
            print(f"   • 출산 휴가 레코드: {len(maternity_records)}건")
            print(f"\n   사유별 분포:")
            for reason, count in maternity_records['Reason Description'].value_counts().items():
                print(f"      - {reason}: {count}건")

    # Analysis
    print("\n" + "=" * 70)
    print("📈 월별 출산 휴가자 추이 분석")
    print("=" * 70)

    if maternity_data:
        print("\n월별 출산 휴가자 수:")
        for month_ko in month_names_ko:
            if month_ko in maternity_data:
                count = maternity_data[month_ko]['count']
                print(f"   • {month_ko}: {count}명")

        # Check for long-term maternity leave (same person across months)
        print("\n" + "=" * 70)
        print("🔄 장기 출산 휴가자 분석 (월간 지속)")
        print("=" * 70)

        if len(maternity_data) >= 2:
            months_list = list(maternity_data.keys())
            for i in range(len(months_list) - 1):
                month1 = months_list[i]
                month2 = months_list[i + 1]

                common_employees = maternity_data[month1]['employees'] & maternity_data[month2]['employees']

                if common_employees:
                    print(f"\n{month1} → {month2} 지속 출산 휴가자:")
                    print(f"   • 인원: {len(common_employees)}명")
                    print(f"   • ID: {sorted(common_employees)}")

    # Feasibility assessment
    print("\n" + "=" * 70)
    print("✅ 가능성 평가 및 권장사항")
    print("=" * 70)

    print("\n1️⃣  데이터 추출 가능성: ✅ 가능")
    print("   • Reason Description에서 출산 휴가 키워드로 필터링 가능")
    print("   • 월별 출산 휴가자 수 집계 가능")

    print("\n2️⃣  차트 구현 방식 제안:")

    print("\n   📊 Option A: 기존 차트 확장 (추천)")
    print("   ┌─────────────────────────────────────────────┐")
    print("   │  신규 입사자 / 퇴사자 / 출산 휴가자          │")
    print("   │                                             │")
    print("   │  📈 Bar chart (grouped)                     │")
    print("   │  • 신규 입사 (녹색)                         │")
    print("   │  • 퇴사자 (빨강)                            │")
    print("   │  • 출산 휴가자 (분홍색) ← NEW              │")
    print("   └─────────────────────────────────────────────┘")

    print("\n   📊 Option B: 별도 차트 생성")
    print("   ┌─────────────────────────────────────────────┐")
    print("   │  기존: 신규 입사자 / 퇴사자                 │")
    print("   └─────────────────────────────────────────────┘")
    print("   ┌─────────────────────────────────────────────┐")
    print("   │  신규: 출산 휴가자 추이                     │")
    print("   └─────────────────────────────────────────────┘")

    print("\n3️⃣  메트릭 추가 필요사항:")
    print("   • hr_metric_calculator.py에 추가할 메트릭:")
    print("     - maternity_leave_count: 출산 휴가자 수")
    print("     - maternity_leave_rate: 출산 휴가율 (%)")

    print("\n4️⃣  구현 난이도: ⭐⭐ (쉬움)")
    print("   • 기존 코드 구조 활용 가능")
    print("   • 새로운 메트릭 추가만 필요")
    print("   • 차트 dataset 하나 추가")

    print("\n5️⃣  비즈니스 가치:")
    print("   • 출산 휴가는 6-7개월 장기 휴가")
    print("   • 인력 운영 계획에 중요한 지표")
    print("   • 복귀 예정일 관리 가능")

    print("\n" + "=" * 70)
    print("💡 최종 권장사항")
    print("=" * 70)

    print("\n✅ 신규 입사자/퇴사자 차트에 출산 휴가자 추가 추천")
    print("\n이유:")
    print("   1. 데이터 추출 가능 ✅")
    print("   2. 구현 난이도 낮음 ✅")
    print("   3. 비즈니스 가치 높음 ✅")
    print("   4. 인력 운영 가시성 향상 ✅")

    print("\n구현 순서:")
    print("   1. hr_metric_calculator.py에 maternity_leave_count 메트릭 추가")
    print("   2. complete_dashboard_builder.py의 Chart 2에 dataset 추가")
    print("   3. 분홍색 (#ff69b4) 색상으로 구분")
    print("   4. 라벨: '출산 휴가자 / Maternity Leave'")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    analyze_maternity_tracking()
