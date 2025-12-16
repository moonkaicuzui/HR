#!/usr/bin/env python3
"""
analyze_absence_calculation.py - Analyze absence rate calculation logic
결근율 계산 로직 분석 (출산 휴가 포함 여부 확인)
"""

import pandas as pd
from pathlib import Path


def analyze_absence_calculation():
    """Analyze how absence rate is calculated and if maternity leave is included"""

    print("=" * 70)
    print("🔍 결근율 계산 로직 분석 (Absence Rate Calculation Analysis)")
    print("=" * 70)

    # Load October 2025 attendance data
    attendance_file = Path("input_files/attendance/converted/attendance data october_converted.csv")

    if not attendance_file.exists():
        print(f"❌ Attendance file not found: {attendance_file}")
        return

    df = pd.read_csv(attendance_file)
    print(f"\n✅ Loaded attendance data: {len(df)} records")

    # Analyze 'compAdd' column (absence marker)
    print("\n" + "=" * 70)
    print("📊 Step 1: compAdd 컬럼 분석 (Absence Marker Column)")
    print("=" * 70)

    if 'compAdd' not in df.columns:
        print("❌ 'compAdd' column not found!")
        return

    print("\ncompAdd 값 분포:")
    compadd_counts = df['compAdd'].value_counts()
    for value, count in compadd_counts.items():
        print(f"   • '{value}': {count}건")

    # Count absences
    total_records = len(df)
    absences = len(df[df['compAdd'] == 'Vắng mặt'])
    absence_rate = (absences / total_records) * 100 if total_records > 0 else 0

    print(f"\n현재 계산 방식:")
    print(f"   • 전체 레코드: {total_records:,}건")
    print(f"   • 결근 (Vắng mặt): {absences:,}건")
    print(f"   • 결근율: {absence_rate:.1f}%")

    # Analyze Reason Description for absences
    print("\n" + "=" * 70)
    print("📋 Step 2: 결근 사유 분석 (Absence Reasons)")
    print("=" * 70)

    absent_records = df[df['compAdd'] == 'Vắng mặt']

    if not absent_records.empty and 'Reason Description' in df.columns:
        print(f"\n결근 {len(absent_records)}건의 사유 분석:")
        reason_counts = absent_records['Reason Description'].value_counts()

        # Categorize reasons
        maternity_reasons = []
        sick_reasons = []
        authorized_reasons = []
        unauthorized_reasons = []
        other_reasons = []

        for reason, count in reason_counts.items():
            reason_str = str(reason).lower()

            if 'sinh' in reason_str or 'dưỡng sinh' in reason_str or 'khám thai' in reason_str:
                maternity_reasons.append((reason, count))
            elif 'ar1' in reason_str or 'vắng không phép' in reason_str:
                unauthorized_reasons.append((reason, count))
            elif 'ar2' in reason_str or 'ốm' in reason_str:
                sick_reasons.append((reason, count))
            elif 'phép' in reason_str or 'vắng có phép' in reason_str:
                authorized_reasons.append((reason, count))
            else:
                other_reasons.append((reason, count))

        # Show categorized results
        print("\n🤰 출산 관련 휴가 (Maternity Leave):")
        maternity_total = 0
        if maternity_reasons:
            for reason, count in maternity_reasons:
                print(f"   • {reason}: {count}건")
                maternity_total += count
            print(f"   📊 출산 휴가 합계: {maternity_total}건")
        else:
            print("   없음")

        print("\n🚫 무단 결근 (Unauthorized Absence):")
        unauthorized_total = 0
        if unauthorized_reasons:
            for reason, count in unauthorized_reasons:
                print(f"   • {reason}: {count}건")
                unauthorized_total += count
            print(f"   📊 무단 결근 합계: {unauthorized_total}건")
        else:
            print("   없음")

        print("\n✅ 유급 휴가 (Authorized Leave):")
        authorized_total = 0
        if authorized_reasons:
            for reason, count in authorized_reasons:
                print(f"   • {reason}: {count}건")
                authorized_total += count
            print(f"   📊 유급 휴가 합계: {authorized_total}건")
        else:
            print("   없음")

        print("\n🏥 병가 (Sick Leave):")
        sick_total = 0
        if sick_reasons:
            for reason, count in sick_reasons:
                print(f"   • {reason}: {count}건")
                sick_total += count
            print(f"   📊 병가 합계: {sick_total}건")
        else:
            print("   없음")

        print("\n❓ 기타 (Others):")
        other_total = 0
        if other_reasons:
            for reason, count in other_reasons:
                print(f"   • {reason}: {count}건")
                other_total += count
            print(f"   📊 기타 합계: {other_total}건")
        else:
            print("   없음")

    # Current calculation logic
    print("\n" + "=" * 70)
    print("⚙️  Step 3: 현재 결근율 계산 로직")
    print("=" * 70)

    print("\n📝 현재 코드:")
    print("""
    def _absence_rate(self, attendance_df: pd.DataFrame) -> float:
        total_records = len(attendance_df)
        absences = len(attendance_df[attendance_df['compAdd'] == 'Vắng mặt'])
        return round((absences / total_records) * 100, 1)
    """)

    print(f"\n📊 현재 계산 결과:")
    print(f"   • 결근율 (Absence Rate): {absence_rate:.1f}%")
    print(f"   • 이 값은 'compAdd == Vắng mặt' 인 모든 레코드를 포함합니다.")

    # Problem identification
    print("\n" + "=" * 70)
    print("⚠️  Step 4: 문제점 식별")
    print("=" * 70)

    if maternity_total > 0:
        print(f"\n🚨 문제 발견!")
        print(f"   현재 결근율 계산에 출산 휴가 {maternity_total}건이 포함되어 있습니다.")
        print(f"\n   출산 휴가는 법적으로 보호받는 휴가이므로")
        print(f"   결근으로 계산하는 것은 부적절합니다.")

        # Calculate corrected absence rate
        actual_absences = absences - maternity_total
        corrected_rate = (actual_absences / total_records) * 100 if total_records > 0 else 0

        print(f"\n📊 수정된 계산:")
        print(f"   • 전체 레코드: {total_records:,}건")
        print(f"   • 결근 (Vắng mặt): {absences:,}건")
        print(f"   • 출산 휴가: {maternity_total}건 (제외 필요)")
        print(f"   • 실제 결근: {actual_absences}건")
        print(f"   • 현재 결근율: {absence_rate:.1f}%")
        print(f"   • 수정 결근율: {corrected_rate:.1f}%")
        print(f"   • 차이: {absence_rate - corrected_rate:.1f}%p")
    else:
        print("\n✅ 10월 데이터에는 출산 휴가가 없습니다.")

    # Recommendations
    print("\n" + "=" * 70)
    print("💡 권장사항 (Recommendations)")
    print("=" * 70)

    print("\n1️⃣  출산 휴가를 결근율에서 제외하는 방법:")
    print("""
    def _absence_rate(self, attendance_df: pd.DataFrame) -> float:
        if attendance_df.empty or 'compAdd' not in attendance_df.columns:
            return 0.0

        total_records = len(attendance_df)

        # 결근 중에서 출산 휴가 제외
        absences_df = attendance_df[attendance_df['compAdd'] == 'Vắng mặt']

        # 출산 휴가 키워드 ('Sinh', 'Dưỡng sinh', 'Khám thai')
        maternity_keywords = ['Sinh', 'sinh', 'Dưỡng sinh', 'Khám thai']
        maternity_mask = absences_df['Reason Description'].str.contains(
            '|'.join(maternity_keywords), na=False, case=False
        )

        # 출산 휴가 제외한 실제 결근
        actual_absences = len(absences_df[~maternity_mask])

        if total_records == 0:
            return 0.0

        return round((actual_absences / total_records) * 100, 1)
    """)

    print("\n2️⃣  별도의 출산 휴가율 지표 추가:")
    print("   • maternity_leave_rate: 출산 휴가율")
    print("   • sick_leave_rate: 병가율")
    print("   • authorized_leave_rate: 유급 휴가율")
    print("   • unauthorized_absence_rate: 무단 결근율 (이미 존재)")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    analyze_absence_calculation()
