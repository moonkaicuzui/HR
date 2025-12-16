#!/usr/bin/env python3
"""
모든 팀의 position_4th 필드 및 데이터 완성도 검증
"""

import json
import re

def verify_all_teams():
    """생성된 HTML에서 모든 팀 데이터 검증"""
    html_file = 'output_files/HR_Dashboard_Complete_2025_10.html'

    print("=" * 80)
    print("ALL TEAMS DATA VERIFICATION")
    print("=" * 80)

    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract teamData JSON
    match = re.search(r'const teamData =\s*(\{[\s\S]*?\n\s*\});', content)
    if not match:
        print("❌ teamData not found in HTML")
        return

    team_data_str = match.group(1)
    team_data = json.loads(team_data_str)

    print(f"\n📊 Total teams found: {len(team_data)}\n")

    # Check each team
    all_teams_ok = True

    for team_name, team_info in team_data.items():
        members = team_info.get('members', [])
        member_count = len(members)

        print(f"\n{'=' * 60}")
        print(f"🏢 {team_name}")
        print(f"{'=' * 60}")
        print(f"Total members: {member_count}")

        if member_count == 0:
            print("❌ NO MEMBERS FOUND!")
            all_teams_ok = False
            continue

        # Check position_4th field presence
        has_position_4th = 0
        missing_position_4th = 0
        position_4th_values = set()

        # Check first 5 members
        sample_size = min(5, member_count)
        print(f"\nSample data (first {sample_size} members):")
        print("-" * 60)

        for i, member in enumerate(members[:sample_size]):
            emp_no = member.get('employee_no', 'N/A')
            name = member.get('full_name', 'N/A')
            pos3 = member.get('position_3rd', 'N/A')
            pos4 = member.get('position_4th', '')

            if pos4 and pos4 != 'nan':
                has_position_4th += 1
                position_4th_values.add(pos4)
                status = "✅"
            else:
                missing_position_4th += 1
                status = "❌"

            print(f"  {status} {emp_no:12s} | {name[:20]:20s} | P4: {pos4:10s}")

        # Check all members for position_4th
        total_with_pos4 = sum(1 for m in members if m.get('position_4th') and m.get('position_4th') != 'nan')
        total_without_pos4 = member_count - total_with_pos4

        print(f"\n📈 Position 4th Statistics:")
        print(f"  With position_4th:    {total_with_pos4:3d} ({total_with_pos4/member_count*100:.1f}%)")
        print(f"  Without position_4th: {total_without_pos4:3d} ({total_without_pos4/member_count*100:.1f}%)")

        if position_4th_values:
            print(f"\n🏷️  Unique position_4th codes: {len(position_4th_values)}")
            sorted_codes = sorted(position_4th_values)
            print(f"  Examples: {', '.join(sorted_codes[:10])}")

        # Team status
        if total_with_pos4 == member_count:
            print(f"\n✅ {team_name}: ALL GOOD - 100% complete")
        elif total_with_pos4 > 0:
            print(f"\n⚠️  {team_name}: PARTIAL - {total_with_pos4}/{member_count} have position_4th")
            all_teams_ok = False
        else:
            print(f"\n❌ {team_name}: CRITICAL - No position_4th data")
            all_teams_ok = False

    # Extract monthlyTeamCounts
    print(f"\n\n{'=' * 80}")
    print("📅 MONTHLY TREND DATA VERIFICATION")
    print("=" * 80)

    match = re.search(r'const monthlyTeamCounts =\s*(\{[\s\S]*?\n\s*\});', content)
    if match:
        monthly_data = json.loads(match.group(1))
        months = sorted(monthly_data.keys())

        print(f"\nMonths available: {len(months)}")
        print(f"Range: {months[0]} to {months[-1]}")

        # Check last month data
        last_month = months[-1]
        last_month_data = monthly_data[last_month]

        print(f"\n{last_month} Team Counts:")
        print("-" * 60)
        for team, count in sorted(last_month_data.items(), key=lambda x: -x[1]):
            print(f"  {team:30s}: {count:3d} members")
    else:
        print("❌ monthlyTeamCounts not found")
        all_teams_ok = False

    # Final summary
    print(f"\n\n{'=' * 80}")
    print("FINAL VERIFICATION RESULT")
    print("=" * 80)

    if all_teams_ok:
        print("✅ ALL TEAMS: Data complete and position_4th field present")
        print("✅ Charts and tables should render correctly for all teams")
    else:
        print("⚠️  SOME ISSUES FOUND: Check details above")

    print("\n")

if __name__ == '__main__':
    verify_all_teams()
