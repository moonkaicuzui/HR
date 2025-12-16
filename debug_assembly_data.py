#!/usr/bin/env python3
"""
ASSEMBLY 팀 데이터 구조 분석 스크립트
원본 데이터에서 ASSEMBLY가 어떻게 표현되는지 확인
"""

import pandas as pd
import sys

def analyze_assembly_data(file_path):
    """ASSEMBLY 팀 데이터 구조 분석"""
    print("=" * 80)
    print(f"Analyzing ASSEMBLY team data from: {file_path}")
    print("=" * 80)

    # CSV 로드
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        print(f"\n✓ Loaded {len(df)} rows")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return

    # 컬럼 확인
    print("\n[1] Available columns:")
    position_cols = [col for col in df.columns if 'POSITION' in col.upper() or 'QIP' in col.upper()]
    for col in position_cols:
        print(f"  - {col}")

    # ASSEMBLY 키워드 검색 (모든 Position 컬럼)
    print("\n[2] Searching for 'ASSEMBLY' keyword...")
    assembly_mask = pd.Series([False] * len(df))

    for col in position_cols:
        col_mask = df[col].astype(str).str.contains('ASSEMBLY', case=False, na=False)
        assembly_mask = assembly_mask | col_mask
        count = col_mask.sum()
        if count > 0:
            print(f"  - {col}: {count} rows contain 'ASSEMBLY'")

    assembly_df = df[assembly_mask].copy()
    print(f"\n✓ Total ASSEMBLY employees found: {len(assembly_df)}")

    if len(assembly_df) == 0:
        print("\n⚠️  NO ASSEMBLY EMPLOYEES FOUND!")
        print("\nTrying alternative keywords...")

        # 대안 키워드 검색
        keywords = ['ASSEM', 'A1A', 'A1B', 'FINAL', 'PACKING']
        for keyword in keywords:
            mask = pd.Series([False] * len(df))
            for col in position_cols:
                mask = mask | df[col].astype(str).str.contains(keyword, case=False, na=False)
            count = mask.sum()
            if count > 0:
                print(f"  - '{keyword}': {count} rows found")

        return

    # ASSEMBLY 팀 Position 구조 분석
    print("\n[3] ASSEMBLY team position structure:")

    # Position 1ST
    if 'QIP POSITION 1ST  NAME' in assembly_df.columns:
        print("\n  Position 1ST (관리 계층):")
        pos_1st_counts = assembly_df['QIP POSITION 1ST  NAME'].value_counts()
        for pos, count in pos_1st_counts.items():
            print(f"    - {pos}: {count}명")

    # Position 2ND
    if 'QIP POSITION 2ND  NAME' in assembly_df.columns:
        print("\n  Position 2ND (역할 세분화):")
        pos_2nd_counts = assembly_df['QIP POSITION 2ND  NAME'].value_counts()
        for pos, count in pos_2nd_counts.items():
            print(f"    - {pos}: {count}명")

    # Position 3RD
    if 'QIP POSITION 3RD  NAME' in assembly_df.columns:
        print("\n  Position 3RD (기능 영역):")
        pos_3rd_counts = assembly_df['QIP POSITION 3RD  NAME'].value_counts()
        for pos, count in pos_3rd_counts.items():
            print(f"    - {pos}: {count}명")

    # Position CODE
    if 'FINAL QIP POSITION NAME CODE' in assembly_df.columns:
        print("\n  Position CODE:")
        code_counts = assembly_df['FINAL QIP POSITION NAME CODE'].value_counts()
        for code, count in code_counts.items():
            print(f"    - {code}: {count}명")

    # 샘플 데이터 출력
    print("\n[4] Sample ASSEMBLY employee data (first 5):")
    sample_cols = ['QIP POSITION 1ST  NAME', 'QIP POSITION 2ND  NAME',
                   'QIP POSITION 3RD  NAME', 'FINAL QIP POSITION NAME CODE']
    available_sample_cols = [col for col in sample_cols if col in assembly_df.columns]

    if available_sample_cols:
        print(assembly_df[available_sample_cols].head(5).to_string(index=False))

    # 문제 진단
    print("\n" + "=" * 80)
    print("DIAGNOSTIC RESULTS:")
    print("=" * 80)

    if len(assembly_df) > 0:
        print(f"✓ ASSEMBLY team data EXISTS ({len(assembly_df)} employees)")
        print("\nPossible issues:")
        print("  1. Team filtering logic may be case-sensitive")
        print("  2. Position 3RD might have unexpected format")
        print("  3. JavaScript data binding may need adjustment")
    else:
        print("❌ NO ASSEMBLY team data found")
        print("\nAction required:")
        print("  1. Check if team name is spelled differently")
        print("  2. Verify Position columns contain team information")
        print("  3. Review data collection process")

    print("\n")

if __name__ == '__main__':
    # 최신 데이터 파일 사용
    file_path = 'input_files/5prs data october.csv'
    analyze_assembly_data(file_path)
