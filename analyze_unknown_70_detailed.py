#!/usr/bin/env python3
"""
analyze_unknown_70_detailed.py - Detailed analysis of 70 unmapped employees
미분류 70명 상세 분석 및 팀 매핑 제안
"""

import pandas as pd
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.monthly_data_collector import MonthlyDataCollector


def analyze_unknown_employees():
    """Analyze UNKNOWN 70 employees in detail"""

    hr_root = Path(__file__).parent
    collector = MonthlyDataCollector(hr_root)

    target_month = '2025-10'
    data = collector.load_month_data(target_month)
    df = data.get('basic_manpower', pd.DataFrame())

    if df.empty:
        print(f"❌ No data for {target_month}")
        return

    print("=" * 100)
    print("🔍 UNKNOWN 70명 상세 분석 및 팀 매핑 제안")
    print("=" * 100)

    # Define currently mapped position_3rd values
    MAPPED_POS3 = [
        # ASSEMBLY
        'ASSEMBLY LINE TQC', 'ASSEMBLY LINE RQC', '12 ASSEMBLY LINE QUALITY IN CHARGE',
        '2 ASSEMBLY BUILDING QUALITY IN CHARGE', '1 ASSEMBLY BUILDING QUALITY IN CHARGE',
        'ALL ASSEMBLY BUILDING QUALITY IN CHARGE', 'ASSEMBLY LINE PO COMPLETION QUALITY',
        # STITCHING
        'STITCHING LINE TQC', 'STITCHING LINE RQC', '1 STITCHING BUILDING QUALITY IN CHARGE',
        'ALL STITCHING BUILDING QUALITY IN CHARGE',
        '1 STITCHING BUILDING QIP LEADER\'S SUCCESSOR 1',
        '1 STITCHING BUILDING QIP LEADER\'S SUCCESSOR 2',
        # OSC
        'INCOMING WH OSC INSPECTION TQC', 'INCOMING WH OSC INSPECTION RQC',
        'HWK OSC/MTL QUALITY IN CHARGE', 'MTL QUALITY IN CHARGE',
        'INCOMING OSC WH QUALITY IN CHARGE', 'LEATHER MTL TEAM LEADER',
        'TEXTILE MTL TEAM LEADER', 'SUBSI MTL TEAM LEADER',
        # BOTTOM
        'BOTTOM INSPECTION TQC', 'BOTTOM INSPECTION RQC', 'BOTTOM REPAIRING & PACKING TQC',
        '1 BUILDING BOTTOM QUALITY IN CHARGE', 'ALL BUILDING BOTTOM QUALITY IN CHARGE',
        # AQL
        'AQL INSPECTOR', 'AQL ROOM PACKING TQC', 'AQL INPUT CARTON TQC', 'AQL REPORT TEAM',
        # REPACKING
        'REPACKING LINE TQC', 'REPACKING LINE PACKING TQC', 'REPACKING LINE REPAIRING TQC',
        'REPACKING AREA INPUT-OUTPUT CARTON TQC', 'REPACKING LINE PO COMPLETION QUALITY',
        # QA
        'QA TEAM STAFF', 'QA TEAM HEAD', 'QA TEAM IN CHARGE',
        # CUTTING
        'CUTTING INSPECTOR', 'ALL CUTTING BUILDING QUALITY IN CHARGE',
        # HWK QIP
        'HWK QUALITY IN CHARGE',
        # OFFICE & OCPT
        'OCPT AND OFFICE TEAM LEADER', 'QIP SAP & INCOMING QUALITY REPORT', 'OCPT TEAM STAFF',
        # NEW
        'NEW'
    ]

    # Find unmapped employees
    unmapped = df[~df['QIP POSITION 3RD  NAME'].isin(MAPPED_POS3)]

    print(f"\n📊 총 미분류 인원: {len(unmapped)}명")
    print("\n" + "=" * 100)

    # Group by position_3rd
    pos3_groups = unmapped.groupby('QIP POSITION 3RD  NAME')

    # Analyze each group
    recommendations = {}

    for pos3, group in pos3_groups:
        print(f"\n{'='*100}")
        print(f"📌 Position 3rd: {pos3}")
        print(f"   인원: {len(group)}명")
        print(f"   Position 1st: {group['QIP POSITION 1ST  NAME'].unique().tolist()}")
        print(f"   Position 2nd: {group['QIP POSITION 2ND  NAME'].unique().tolist()}")

        # Show sample employees
        print(f"\n   직원 목록:")
        for idx, row in group.iterrows():
            emp_no = row.get('Employee No', '')
            name = row.get('Full Name', '')
            pos1 = row.get('QIP POSITION 1ST  NAME', '')
            pos2 = row.get('QIP POSITION 2ND  NAME', '')
            print(f"      • {emp_no} - {name}: {pos1} / {pos2}")

        # Analyze and recommend team
        pos3_upper = str(pos3).upper()
        pos1_list = group['QIP POSITION 1ST  NAME'].unique()
        pos2_list = group['QIP POSITION 2ND  NAME'].unique()

        recommended_team = None
        reason = ""

        # MTL-related keywords
        if any(kw in pos3_upper for kw in ['LEATHER', 'TEXTILE', 'SUBSI', 'HAPPO', 'MTL']):
            recommended_team = 'MTL'
            reason = "MTL 관련 키워드 포함 (Material/Leather/Textile/Subsi/Happo)"

        # OSC-related
        elif any(kw in pos3_upper for kw in ['OSC', 'INCOMING']):
            recommended_team = 'OSC'
            reason = "OSC/Incoming 관련"

        # ASSEMBLY-related
        elif any(kw in pos3_upper for kw in ['ASSEMBLY', 'GIÀY', 'SHOES']):
            recommended_team = 'ASSEMBLY'
            reason = "Assembly 관련"

        # STITCHING-related
        elif any(kw in pos3_upper for kw in ['STITCHING', 'MAY', 'UPPER']):
            recommended_team = 'STITCHING'
            reason = "Stitching 관련"

        # REPACKING-related
        elif any(kw in pos3_upper for kw in ['REPACKING', 'REPAIRING', 'PACKING', 'FG WH', 'CARTON']):
            recommended_team = 'REPACKING'
            reason = "Repacking/Packing/창고 관련"

        # QA-related
        elif any(kw in pos3_upper for kw in ['AUDIT', 'TRAINING', 'B-GRADE', 'TEST SAMPLE']):
            recommended_team = 'QA'
            reason = "QA/Audit/Training 관련"

        # OFFICE-related
        elif any(kw in pos3_upper for kw in ['OFFICE', 'REPORT', 'OCPT', 'TEAM OPERATION']):
            recommended_team = 'OFFICE & OCPT'
            reason = "Office/Report 관련"

        # Inhouse inspection - could be ASSEMBLY or STITCHING
        elif 'INHOUSE' in pos3_upper:
            if 'PRINTING' in pos3_upper:
                recommended_team = 'ASSEMBLY'
                reason = "Inhouse Printing → Assembly 공정"
            elif any(kw in pos3_upper for kw in ['HF', 'NO-SEW']):
                recommended_team = 'ASSEMBLY'
                reason = "Inhouse HF/No-Sew → Assembly 공정"
            else:
                recommended_team = 'ASSEMBLY'
                reason = "Inhouse 검사 → Assembly"

        # Model Master - special role
        elif 'MODEL MASTER' in pos3_upper:
            recommended_team = 'QA'
            reason = "Model Master → QA (품질 샘플 관리)"

        # Scan Pack
        elif 'SCAN PACK' in pos3_upper:
            recommended_team = 'REPACKING'
            reason = "Scan Pack → Repacking 공정"

        # LINE LEADER successor
        elif 'LINE LEADER' in pos3_upper or 'GROUP LEADER' in pos3_upper:
            # Check position_1st to determine team
            if len(pos1_list) > 0:
                pos1 = str(pos1_list[0])
                if 'ASSEMBLY' in pos1:
                    recommended_team = 'ASSEMBLY'
                    reason = "Line Leader (Assembly Inspector)"
                elif 'STITCHING' in pos1:
                    recommended_team = 'STITCHING'
                    reason = "Line Leader (Stitching Inspector)"
                else:
                    recommended_team = 'OFFICE & OCPT'
                    reason = "Line Leader (관리직)"
            else:
                recommended_team = 'OFFICE & OCPT'
                reason = "Line Leader"

        else:
            recommended_team = 'UNKNOWN'
            reason = "명확한 분류 기준 없음 - 수동 검토 필요"

        recommendations[pos3] = {
            'team': recommended_team,
            'reason': reason,
            'count': len(group),
            'employees': group[['Employee No', 'Full Name', 'QIP POSITION 1ST  NAME', 'QIP POSITION 2ND  NAME']].to_dict('records')
        }

        print(f"\n   ✅ 권장 팀: {recommended_team}")
        print(f"   이유: {reason}")

    # Summary by recommended team
    print("\n" + "=" * 100)
    print("📊 팀별 매핑 요약")
    print("=" * 100)

    team_summary = {}
    for pos3, rec in recommendations.items():
        team = rec['team']
        if team not in team_summary:
            team_summary[team] = {'count': 0, 'pos3_list': []}
        team_summary[team]['count'] += rec['count']
        team_summary[team]['pos3_list'].append(f"{pos3} ({rec['count']}명)")

    for team in sorted(team_summary.keys()):
        info = team_summary[team]
        print(f"\n{'='*50}")
        print(f"🎯 {team}: {info['count']}명")
        for pos3 in info['pos3_list']:
            print(f"   • {pos3}")

    # Final verification
    total_recommended = sum(info['count'] for info in team_summary.values())
    print(f"\n{'='*100}")
    print(f"✅ 총 매핑 제안: {total_recommended}명")
    print(f"   기존 매핑: 436명")
    print(f"   신규 매핑: {total_recommended}명")
    print(f"   총계: {436 + total_recommended}명")

    if 'UNKNOWN' in team_summary:
        print(f"\n⚠️  여전히 UNKNOWN: {team_summary['UNKNOWN']['count']}명")
        print(f"   → 수동 검토 필요")
    else:
        print(f"\n🎉 100% 매핑 완료!")

    # Export recommendations to JSON
    import json
    output_file = 'unknown_70_mapping_recommendations.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, ensure_ascii=False, indent=2)

    print(f"\n📁 매핑 권장사항 저장: {output_file}")

    return recommendations


if __name__ == '__main__':
    analyze_unknown_employees()
