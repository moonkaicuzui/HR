#!/usr/bin/env python3
"""
Check absence types in attendance data
결근 유형 확인 스크립트
"""

import pandas as pd
from pathlib import Path
import json

def check_absence_types():
    """attendance 데이터의 결근 유형 분석"""

    # Find all attendance CSV files
    attendance_dir = Path('input_files/attendance/converted')
    csv_files = list(attendance_dir.glob('*.csv'))

    print("=" * 80)
    print("결근 유형 분석 (Absence Type Analysis)")
    print("=" * 80)

    all_reasons = set()
    reason_counts = {}

    for csv_file in csv_files:
        print(f"\n📄 파일: {csv_file.name}")

        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
        except:
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
            except:
                continue

        if 'Reason Description' not in df.columns:
            print("   ⚠️ 'Reason Description' 컬럼 없음")
            continue

        # Get unique reason descriptions
        reasons = df['Reason Description'].dropna().unique()

        # Add to all reasons
        for reason in reasons:
            all_reasons.add(str(reason))
            reason_counts[str(reason)] = reason_counts.get(str(reason), 0) + 1

    # Sort by frequency
    sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)

    print("\n" + "=" * 80)
    print("결근 사유 유형 분류 (Absence Reason Classification)")
    print("=" * 80)

    # Classify reasons into types
    type_1_unauthorized = []  # 무단결근
    type_2_sick = []  # 병가
    type_3_approved = []  # 승인결근
    maternity_leave = []  # 출산휴가

    for reason, count in sorted_reasons:
        reason_lower = reason.lower()

        # TYPE-1: Unauthorized (무단결근)
        if any(pattern in reason_lower for pattern in ['ar1', 'ar2', 'không phép', 'unauthorized', '무단', 'vắng không phép']):
            type_1_unauthorized.append((reason, count))
        # Maternity (출산휴가)
        elif any(pattern in reason_lower for pattern in ['maternity', '출산', 'thai sản', 'birth', 'pregnancy']):
            maternity_leave.append((reason, count))
        # TYPE-2: Sick leave (병가)
        elif any(pattern in reason_lower for pattern in ['sick', 'ill', 'medical', '병', 'ốm', 'bệnh', 'health']):
            type_2_sick.append((reason, count))
        # TYPE-3: Approved absence (승인결근)
        elif any(pattern in reason_lower for pattern in ['có phép', 'approved', '승인', 'authorized', 'annual', 'vacation', 'personal']):
            type_3_approved.append((reason, count))
        else:
            # 분류되지 않은 기타
            type_3_approved.append((reason, count))  # Default to approved

    # Print classification results
    print("\n🔴 TYPE-1: 무단결근 (Unauthorized Absence)")
    print("-" * 40)
    for reason, count in type_1_unauthorized:
        print(f"   • {reason:40s} ({count}회)")

    print("\n🟡 TYPE-2: 병가 (Sick Leave)")
    print("-" * 40)
    for reason, count in type_2_sick:
        print(f"   • {reason:40s} ({count}회)")

    print("\n🟢 TYPE-3: 승인결근 (Approved Absence)")
    print("-" * 40)
    for reason, count in type_3_approved[:10]:  # Show only first 10
        print(f"   • {reason:40s} ({count}회)")
    if len(type_3_approved) > 10:
        print(f"   ... 외 {len(type_3_approved)-10}개 유형")

    print("\n🔵 출산휴가 (Maternity Leave)")
    print("-" * 40)
    for reason, count in maternity_leave:
        print(f"   • {reason:40s} ({count}회)")

    # Save classification mapping
    classification = {
        'TYPE-1': [r[0] for r in type_1_unauthorized],
        'TYPE-2': [r[0] for r in type_2_sick],
        'TYPE-3': [r[0] for r in type_3_approved],
        'MATERNITY': [r[0] for r in maternity_leave]
    }

    with open('absence_type_classification.json', 'w', encoding='utf-8') as f:
        json.dump(classification, f, ensure_ascii=False, indent=2)

    print("\n📄 분류 결과 저장: absence_type_classification.json")

    return classification

if __name__ == "__main__":
    classification = check_absence_types()