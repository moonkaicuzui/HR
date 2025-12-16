#!/usr/bin/env python3
"""
최종 검증: 모든 11개 주요 팀의 position_4th 완성도
"""

def verify_teams():
    """HTML에서 11개 팀 검증"""

    main_teams = [
        'ASSEMBLY', 'STITCHING', 'OSC', 'MTL', 'BOTTOM',
        'AQL', 'REPACKING', 'QA', 'CUTTING',
        'QIP MANAGER & OFFICE & OCPT', 'NEW'
    ]

    html_file = 'output_files/HR_Dashboard_Complete_2025_10.html'

    with open(html_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("=" * 80)
    print("FINAL VERIFICATION: ALL 11 MAIN TEAMS")
    print("=" * 80)
    print()

    team_results = {}

    for team in main_teams:
        # Find team section
        team_start = None
        for i, line in enumerate(lines):
            if f'"{team}": {{' in line:
                team_start = i
                break

        if team_start is None:
            print(f"❌ {team:30s}: NOT FOUND in HTML")
            team_results[team] = {'found': False}
            continue

        # Extract next 30 lines (2 members worth of data)
        team_section = ''.join(lines[team_start:team_start+30])

        # Count position_4th
        pos4_count = team_section.count('"position_4th":')

        # Extract sample position_4th values
        import re
        pos4_values = re.findall(r'"position_4th":\s*"([^"]*)"', team_section)

        if pos4_count > 0:
            unique_codes = set(pos4_values)
            status = "✅"
            codes_display = ', '.join(sorted(unique_codes)[:3])
            team_results[team] = {
                'found': True,
                'has_position_4th': True,
                'sample_codes': list(unique_codes)[:3]
            }
        else:
            status = "❌"
            codes_display = "NO position_4th"
            team_results[team] = {
                'found': True,
                'has_position_4th': False
            }

        print(f"{status} {team:30s}: position_4th = [{codes_display}]")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    found_teams = sum(1 for r in team_results.values() if r['found'])
    complete_teams = sum(1 for r in team_results.values() if r.get('has_position_4th', False))

    print(f"Teams found:        {found_teams}/11")
    print(f"With position_4th:  {complete_teams}/11")

    if complete_teams == 11:
        print()
        print("✅ SUCCESS: ALL 11 teams have position_4th field!")
        print("✅ Treemap and Sunburst charts will render for all teams")
    elif complete_teams > 0:
        print()
        print(f"⚠️  PARTIAL: {complete_teams}/11 teams have position_4th")
        print("⚠️  Some teams may have chart rendering issues")
    else:
        print()
        print("❌ CRITICAL: NO teams have position_4th")
        print("❌ Charts will NOT render")

    print()

if __name__ == '__main__':
    verify_teams()
