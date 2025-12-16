#!/usr/bin/env python3
"""
두 CSV 파일 구조 비교 및 ASSEMBLY 데이터 확인
"""

import pandas as pd

def compare_csv_structures():
    """두 CSV 파일의 구조 비교"""
    print("=" * 80)
    print("CSV FILES STRUCTURE COMPARISON")
    print("=" * 80)

    files = {
        '5prs data': 'input_files/5prs data october.csv',
        'basic manpower': 'input_files/basic manpower data october.csv'
    }

    for name, path in files.items():
        print(f"\n[{name}]")
        print(f"File: {path}")

        try:
            df = pd.read_csv(path, encoding='utf-8-sig')
            print(f"Rows: {len(df)}")
            print(f"Columns: {len(df.columns)}")
            print("\nColumn names:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i}. {col}")

            # Position 컬럼 확인
            position_cols = [col for col in df.columns if 'POSITION' in col.upper() or 'QIP' in col.upper()]
            if position_cols:
                print(f"\n✓ Position columns found: {len(position_cols)}")
                for col in position_cols:
                    print(f"    - {col}")

                # ASSEMBLY 검색
                assembly_mask = pd.Series([False] * len(df))
                for col in position_cols:
                    assembly_mask = assembly_mask | df[col].astype(str).str.contains('ASSEMBLY', case=False, na=False)

                assembly_count = assembly_mask.sum()
                print(f"\n✓ ASSEMBLY employees: {assembly_count}")

                if assembly_count > 0:
                    print("\nSample ASSEMBLY data (first 3):")
                    sample_cols = ['QIP POSITION 1ST  NAME', 'QIP POSITION 2ND  NAME',
                                   'QIP POSITION 3RD  NAME', 'FINAL QIP POSITION NAME CODE']
                    available = [c for c in sample_cols if c in df.columns]
                    if 'Employee_Name' in df.columns:
                        available.insert(0, 'Employee_Name')

                    assembly_df = df[assembly_mask]
                    print(assembly_df[available].head(3).to_string(index=False))

            else:
                print("\n❌ NO Position columns found!")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "-" * 80)

if __name__ == '__main__':
    compare_csv_structures()
