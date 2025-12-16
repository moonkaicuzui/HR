# 팀 로직 마이그레이션 최종 실행 계획 - Final Migration Plan

**날짜**: 2025-10-07
**목표**: 원조 management_dashboard의 12개 팀 로직을 최신 HR_Dashboard에 적용
**매핑률**: 100% (506명 전원)
**예상 소요 시간**: 2-3일

---

## 🎯 Executive Summary

### 현재 상태
- ❌ 18개 직급 기반 팀 (ASSEMBLY INSPECTOR, LINE LEADER 등)
- ❌ 팀 이름이 직관적이지 않음
- ✅ 완전 자동화 (position_1st 기반)

### 목표 상태
- ✅ 12개 명확한 팀 이름 (ASSEMBLY, OSC, MTL 등)
- ✅ 100% 매핑 완료 (UNKNOWN 0명)
- ✅ MTL 독립 팀 복원 (33명)
- ✅ 원조 대시보드와 일관성

### 선택한 방법
**Option C - 하이브리드 접근** ⭐⭐⭐⭐⭐
- 12개 원조 팀 + 동적 sub_teams
- 단일 함수 교체 (`_collect_team_data()`)
- 기존 기능 모두 보존

---

## 📋 Phase 1: 준비 단계 (4시간)

### 1.1 백업 생성 ✅ 필수

```bash
cd "/Users/ksmoon/Downloads/대시보드 인센티브 테스트12_1_9월 25일 _맥북용/HR"

# 1. 핵심 파일 백업
cp src/visualization/complete_dashboard_builder.py \
   src/visualization/complete_dashboard_builder_backup_20251007.py

# 2. 현재 대시보드 백업
cp output_files/HR_Dashboard_2025_10.html \
   output_files/HR_Dashboard_2025_10_BEFORE_MIGRATION.html

# 3. 백업 확인
ls -lh src/visualization/*backup*
ls -lh output_files/*BEFORE_MIGRATION*
```

### 1.2 테스트 환경 준비

```bash
# 1. 의존성 확인
python -c "import pandas, numpy; print('Dependencies OK')"

# 2. 데이터 파일 확인
python -c "
from src.data.monthly_data_collector import MonthlyDataCollector
collector = MonthlyDataCollector('.')
data = collector.load_month_data('2025-10')
print(f'Basic manpower: {len(data.get(\"basic_manpower\", []))} records')
print(f'Attendance: {len(data.get(\"attendance\", []))} records')
"

# 3. 현재 팀 수 확인
python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder
builder = CompleteDashboardBuilder('2025-10')
team_data = builder._collect_team_data()
print(f'Current teams: {len(team_data)}')
print(f'Team names: {list(team_data.keys())}')
"
```

### 1.3 매핑 규칙 검증

`FINAL_TEAM_MAPPING.md` 파일 확인:
- ✅ 12개 팀 정의 완료
- ✅ Position 3rd → 팀 매핑 규칙 정의
- ✅ 506명 전원 매핑 (100%)

---

## 📝 Phase 2: 구현 단계 (1일)

### 2.1 TEAM_MAPPING 상수 정의

`src/visualization/complete_dashboard_builder.py` 파일 상단에 추가:

```python
# Team mapping configuration - Based on FINAL_TEAM_MAPPING.md
TEAM_MAPPING = {
    'ASSEMBLY': [
        'ASSEMBLY LINE TQC',
        'ASSEMBLY LINE RQC',
        '12 ASSEMBLY LINE QUALITY IN CHARGE',
        '2 ASSEMBLY BUILDING QUALITY IN CHARGE',
        '1 ASSEMBLY BUILDING QUALITY IN CHARGE',
        'ALL ASSEMBLY BUILDING QUALITY IN CHARGE',
        'ASSEMBLY LINE PO COMPLETION QUALITY',
        'SCAN PACK AREA TQC',
        'ALL B-GRADE CONTROL & PACKING'
    ],
    'STITCHING': [
        'STITCHING LINE TQC',
        'STITCHING LINE RQC',
        '1 STITCHING BUILDING QUALITY IN CHARGE',
        'ALL STITCHING BUILDING QUALITY IN CHARGE',
        '1 STITCHING BUILDING QIP LEADER\'S SUCCESSOR 1',
        '1 STITCHING BUILDING QIP LEADER\'S SUCCESSOR 2'
    ],
    'OSC': [
        'INCOMING WH OSC INSPECTION TQC',
        'INCOMING WH OSC INSPECTION RQC',
        'HWK OSC/MTL QUALITY IN CHARGE',
        'MTL QUALITY IN CHARGE',
        'INCOMING OSC WH QUALITY IN CHARGE',
        'LEATHER MTL TEAM LEADER',
        'TEXTILE MTL TEAM LEADER',
        'SUBSI MTL TEAM LEADER',
        'INHOUSE HF/ NO-SEW INSPECTION TQC',
        'INHOUSE HF/ NO-SEW INSPECTION RQC',
        'INHOUSE PRINTING INSPECTION TQC',
        'INHOUSE PRINTING INSPECTION RQC'
    ],
    'MTL': [
        'LEATHER TQC',
        'TEXTILE TQC',
        'SUBSI TQC',
        'HAPPO TQC',
        'LINE LEADER(GROUP LEADER SUCCESSOR)'
    ],
    'BOTTOM': [
        'BOTTOM INSPECTION TQC',
        'BOTTOM INSPECTION RQC',
        'BOTTOM REPAIRING & PACKING TQC',
        '1 BUILDING BOTTOM QUALITY IN CHARGE',
        'ALL BUILDING BOTTOM QUALITY IN CHARGE'
    ],
    'AQL': [
        'AQL INSPECTOR',
        'AQL ROOM PACKING TQC',
        'AQL INPUT CARTON TQC',
        'AQL REPORT TEAM',
        'FG WH CARTON PACKING TQC',
        'FG WH INPUT-OUTPUT CARTON RQC'
    ],
    'REPACKING': [
        'REPACKING LINE TQC',
        'REPACKING LINE PACKING TQC',
        'REPACKING LINE REPAIRING TQC',
        'REPACKING AREA INPUT-OUTPUT CARTON TQC',
        'REPACKING LINE PO COMPLETION QUALITY'
    ],
    'QA': [
        'QA TEAM STAFF',
        'QA TEAM HEAD',
        'QA TEAM IN CHARGE',
        'AUDITOR & TRAININER',
        'MODEL MASTER',
        'AUDIT & TRAINING TEAM LEADER'
    ],
    'CUTTING': [
        'CUTTING INSPECTOR',
        'ALL CUTTING BUILDING QUALITY IN CHARGE'
    ],
    'HWK QIP': [
        'HWK QUALITY IN CHARGE'
    ],
    'OFFICE & OCPT': [
        'OCPT AND OFFICE TEAM LEADER',
        'OCPT TEAM STAFF',
        'TEAM OPERATION MANAGEMENT',
        'QIP SAP & INCOMING QUALITY REPORT '
    ],
    'NEW': [
        'NEW'
    ]
}
```

### 2.2 _collect_team_data() 함수 교체

**기존 함수 이름 변경** (백업용):

```python
def _collect_team_data_legacy(self):
    """
    Legacy: Collect team data based on position_1st (동적 그룹화)
    Kept for rollback purposes
    """
    # ... 기존 코드 그대로 유지 ...
```

**새로운 함수 구현**:

```python
def _collect_team_data(self):
    """
    Collect team data using 12 original teams + sub-teams (Hybrid approach)
    원조 12개 팀 + 동적 하위팀 하이브리드 방식

    Based on: FINAL_TEAM_MAPPING.md
    Mapping rate: 100% (506 employees)
    """
    data = self.collector.load_month_data(self.target_month)
    df = data.get('basic_manpower', pd.DataFrame())
    attendance_df = data.get('attendance', pd.DataFrame())

    if df.empty:
        return {}

    # Build reverse mapping: position_3rd -> team_name
    reverse_mapping = {}
    for team_name, pos3_list in TEAM_MAPPING.items():
        for pos3 in pos3_list:
            reverse_mapping[pos3] = team_name

    # Initialize team structure (12 teams)
    team_data = {}
    for team_name in TEAM_MAPPING.keys():
        team_data[team_name] = {
            'name': team_name,
            'members': [],
            'sub_teams': {}
        }

    # Process each employee
    for idx, row in df.iterrows():
        employee_no = str(row.get('Employee No', ''))
        if not employee_no or employee_no == 'nan':
            continue

        pos1 = str(row.get('QIP POSITION 1ST  NAME', ''))
        pos2 = str(row.get('QIP POSITION 2ND  NAME', ''))
        pos3 = str(row.get('QIP POSITION 3RD  NAME', ''))

        # Map to team using position_3rd
        team_name = reverse_mapping.get(pos3, None)

        if not team_name:
            # Unmapped employee - should not happen with 100% mapping
            print(f"⚠️  Warning: Unmapped employee {employee_no} - {row.get('Full Name')} (pos3: {pos3})")
            continue

        # Extract boss_id
        boss_id = ''
        if 'MST direct boss name' in row and pd.notna(row['MST direct boss name']):
            boss_val = row['MST direct boss name']
            try:
                boss_id = str(int(float(boss_val)))
            except (ValueError, TypeError):
                boss_id = str(boss_val).replace('.0', '')

        if boss_id in ['nan', '0', '', 'None']:
            boss_id = ''

        # Build employee info
        employee_info = {
            'employee_no': employee_no,
            'full_name': str(row.get('Full Name', '')),
            'position_1st': pos1,
            'position_2nd': pos2,
            'position_3rd': pos3,
            'boss_id': boss_id,
            'role_type': str(row.get('ROLE TYPE STD', '')),
            'entrance_date': row.get('Entrance Date', ''),
            'stop_date': row.get('Stop working Date', '')
        }

        # Add to team
        team_data[team_name]['members'].append(employee_info)

        # Add to sub-team (position_2nd) - preserve hierarchy
        if pos2 and pos2 != 'nan':
            if pos2 not in team_data[team_name]['sub_teams']:
                team_data[team_name]['sub_teams'][pos2] = {
                    'name': pos2,
                    'members': []
                }
            team_data[team_name]['sub_teams'][pos2]['members'].append(employee_info)

    # Calculate metrics for each team
    for team_name, team_info in team_data.items():
        team_info['metrics'] = self._calculate_team_metrics(
            team_info['members'],
            attendance_df
        )

        # Calculate metrics for sub-teams
        for sub_team_name, sub_team_info in team_info.get('sub_teams', {}).items():
            sub_team_info['metrics'] = self._calculate_team_metrics(
                sub_team_info['members'],
                attendance_df
            )

    # Remove empty teams (should not happen with NEW always having members)
    team_data = {k: v for k, v in team_data.items() if v['members']}

    return team_data
```

### 2.3 검증 로직 추가

함수 끝에 검증 로직 추가:

```python
# Validation: Check mapping coverage
total_mapped = sum(len(team['members']) for team in team_data.values())
print(f"✅ Team mapping complete: {total_mapped} employees across {len(team_data)} teams")

# Expected: 506 employees, 12 teams
if total_mapped != 506:
    print(f"⚠️  Warning: Expected 506 employees, got {total_mapped}")
if len(team_data) != 12:
    print(f"⚠️  Warning: Expected 12 teams, got {len(team_data)}")
    print(f"   Teams: {list(team_data.keys())}")
```

---

## 🧪 Phase 3: 테스트 단계 (1일)

### 3.1 유닛 테스트

```bash
# Test 1: 팀 매핑 검증
python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder

builder = CompleteDashboardBuilder('2025-10')
team_data = builder._collect_team_data()

print('='*80)
print('📊 팀 매핑 검증')
print('='*80)

# Check team count
print(f'\\n1. 팀 수: {len(team_data)} (예상: 12)')
assert len(team_data) == 12, f'Expected 12 teams, got {len(team_data)}'

# Check team names
expected_teams = [
    'ASSEMBLY', 'STITCHING', 'OSC', 'MTL', 'BOTTOM', 'AQL',
    'REPACKING', 'QA', 'CUTTING', 'HWK QIP', 'OFFICE & OCPT', 'NEW'
]
actual_teams = sorted(team_data.keys())
print(f'\\n2. 팀 이름: {actual_teams}')
for team in expected_teams:
    assert team in team_data, f'Missing team: {team}'

# Check total employees
total = sum(len(team['members']) for team in team_data.values())
print(f'\\n3. 총 인원: {total}명 (예상: 506)')
assert total == 506, f'Expected 506 employees, got {total}'

# Check team sizes
print(f'\\n4. 팀별 인원:')
for team, data in sorted(team_data.items(), key=lambda x: len(x[1]['members']), reverse=True):
    print(f'   • {team}: {len(data[\"members\"])}명')

# Check MTL team
mtl_count = len(team_data['MTL']['members'])
print(f'\\n5. MTL 독립 팀: {mtl_count}명 (예상: 33)')
assert mtl_count == 33, f'Expected 33 MTL members, got {mtl_count}'

print('\\n✅ All tests passed!')
"
```

### 3.2 대시보드 생성 테스트

```bash
# Test 2: 테스트 대시보드 생성
python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder

builder = CompleteDashboardBuilder('2025-10')
output_file = 'output_files/HR_Dashboard_2025_10_MIGRATION_TEST.html'

print('📊 테스트 대시보드 생성 중...')
builder.build_dashboard(output_file)

import os
file_size = os.path.getsize(output_file)
print(f'✅ 대시보드 생성 완료!')
print(f'   파일: {output_file}')
print(f'   크기: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)')
"

# Test 3: HTML 파일 검증
ls -lh output_files/HR_Dashboard_2025_10_MIGRATION_TEST.html

# Test 4: 브라우저에서 수동 확인
open output_files/HR_Dashboard_2025_10_MIGRATION_TEST.html
```

### 3.3 데이터 일관성 검증

```bash
# Test 5: 팀별 데이터 일관성
python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder

builder = CompleteDashboardBuilder('2025-10')
team_data = builder._collect_team_data()

print('='*80)
print('📊 팀별 데이터 일관성 검증')
print('='*80)

errors = []

for team_name, team_info in team_data.items():
    members = team_info['members']
    metrics = team_info['metrics']

    # Check members vs metrics consistency
    if len(members) != metrics.get('total_members', 0):
        errors.append(f'{team_name}: Members count mismatch ({len(members)} vs {metrics[\"total_members\"]})')

    # Check sub_teams
    sub_teams = team_info.get('sub_teams', {})
    sub_total = sum(len(st['members']) for st in sub_teams.values())

    if sub_total > 0 and sub_total != len(members):
        errors.append(f'{team_name}: Sub-teams total ({sub_total}) != Team total ({len(members)})')

if errors:
    print('\\n❌ Errors found:')
    for err in errors:
        print(f'   • {err}')
else:
    print('\\n✅ All data consistent!')
"
```

### 3.4 비교 검증

```bash
# Test 6: 원조 대시보드와 비교
python -c "
print('='*80)
print('📊 원조 vs 현재 대시보드 팀 구성 비교')
print('='*80)

original = {
    'ASSEMBLY': 119, 'STITCHING': 94, 'OSC': 25, 'MTL': 30,
    'BOTTOM': 32, 'AQL': 23, 'QA': 20, 'REPACKING': 17,
    'CUTTING': 8, 'OFFICE & OCPT': 4, 'HWK QIP': 1, 'NEW': 20
}

from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder
builder = CompleteDashboardBuilder('2025-10')
team_data = builder._collect_team_data()

current = {team: len(data['members']) for team, data in team_data.items()}

print(f'\\n{\"팀\":20} | {\"원조 (2025-09)\":>15} | {\"현재 (2025-10)\":>15} | {\"변화\":>10}')
print('-'*80)

for team in sorted(original.keys()):
    orig = original[team]
    curr = current.get(team, 0)
    diff = curr - orig
    sign = '+' if diff > 0 else ''
    print(f'{team:20} | {orig:>15} | {curr:>15} | {sign}{diff:>9}')

orig_total = sum(original.values())
curr_total = sum(current.values())
diff_total = curr_total - orig_total

print('-'*80)
print(f'{\"총계\":20} | {orig_total:>15} | {curr_total:>15} | +{diff_total:>9}')
print('\\n✅ 비교 완료')
"
```

---

## 🚀 Phase 4: 배포 단계 (0.5일)

### 4.1 최종 검증

```bash
# 1. 모든 테스트 통과 확인
echo "✅ Phase 3의 모든 테스트 통과 확인"

# 2. 테스트 대시보드 수동 검토
# - 12개 팀 모두 표시되는지
# - 팀별 인원 수 정확한지
# - 차트 정상 작동하는지
# - MTL 팀 존재하는지

# 3. 코드 리뷰
# - TEAM_MAPPING 상수 정확한지
# - 주석 명확한지
# - 에러 처리 적절한지
```

### 4.2 프로덕션 배포

```bash
# 1. 최종 백업 (배포 직전)
cp output_files/HR_Dashboard_2025_10.html \
   output_files/HR_Dashboard_2025_10_FINAL_BACKUP_$(date +%Y%m%d_%H%M%S).html

# 2. 프로덕션 대시보드 생성
python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder

builder = CompleteDashboardBuilder('2025-10')
output_file = 'output_files/HR_Dashboard_2025_10.html'

print('📊 프로덕션 대시보드 생성 중...')
builder.build_dashboard(output_file)

import os
file_size = os.path.getsize(output_file)
print(f'✅ 배포 완료!')
print(f'   파일: {output_file}')
print(f'   크기: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)')
"

# 3. 파일 검증
ls -lh output_files/HR_Dashboard_2025_10.html

# 4. 브라우저에서 최종 확인
open output_files/HR_Dashboard_2025_10.html
```

### 4.3 문서화

```bash
# 1. 변경 로그 작성
cat >> CHANGELOG.md << 'EOF'

## [2025-10-07] Team Logic Migration

### Added
- 12개 원조 팀 로직 적용 (ASSEMBLY, STITCHING, OSC, MTL 등)
- MTL 독립 팀 복원 (33명)
- 100% 팀 매핑 달성 (506명 전원)

### Changed
- `_collect_team_data()` 함수: position_1st → position_3rd 기반 매핑
- 팀 구조: 18개 직급 → 12개 명확한 팀

### Technical
- Added TEAM_MAPPING 상수 (62개 position_3rd 값)
- Preserved sub_teams hierarchy (position_2nd)
- Kept legacy function for rollback: `_collect_team_data_legacy()`

### References
- FINAL_TEAM_MAPPING.md - 최종 매핑 정보
- TEAM_LOGIC_MIGRATION_FINAL_PLAN.md - 마이그레이션 계획
- TEAM_LOGIC_ANALYSIS.md - 원조 로직 분석

EOF

# 2. README 업데이트
echo "
## Team Structure

The dashboard now uses the original 12-team structure:

1. ASSEMBLY (141명) - 27.9%
2. STITCHING (117명) - 23.1%
3. NEW (55명) - 10.9%
4. BOTTOM (41명) - 8.1%
5. OSC (33명) - 6.5%
6. MTL (33명) - 6.5%
7. REPACKING (27명) - 5.3%
8. AQL (24명) - 4.7%
9. QA (21명) - 4.2%
10. CUTTING (8명) - 1.6%
11. OFFICE & OCPT (5명) - 1.0%
12. HWK QIP (1명) - 0.2%

Total: 506 employees (100% mapped)
" >> README.md
```

---

## 🔄 Phase 5: 롤백 계획 (비상용)

### 롤백 조건
- 테스트 실패
- 데이터 불일치 발견
- 차트 오류 발생
- 성능 문제

### 롤백 절차

```bash
# 1. 백업 파일 복원
cp src/visualization/complete_dashboard_builder_backup_20251007.py \
   src/visualization/complete_dashboard_builder.py

# 2. 이전 대시보드 복원
cp output_files/HR_Dashboard_2025_10_BEFORE_MIGRATION.html \
   output_files/HR_Dashboard_2025_10.html

# 3. 검증
python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder
builder = CompleteDashboardBuilder('2025-10')
team_data = builder._collect_team_data()
print(f'Rollback verified: {len(team_data)} teams')
"

# 4. 문서화
echo "⚠️  Rollback performed at $(date)" >> ROLLBACK_LOG.txt
```

### 대안: 레거시 함수 사용

코드 내에서 함수만 전환:

```python
# In complete_dashboard_builder.py, build_dashboard() method:

# Use new mapping (default)
team_data = self._collect_team_data()

# To rollback without file restore:
# team_data = self._collect_team_data_legacy()
```

---

## 📊 Phase 6: 모니터링 (배포 후 1주일)

### 6.1 성능 모니터링

```bash
# 1. 대시보드 생성 시간 측정
time python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder
builder = CompleteDashboardBuilder('2025-10')
builder.build_dashboard('output_files/test_performance.html')
"

# Expected: < 30 seconds

# 2. 파일 크기 비교
ls -lh output_files/HR_Dashboard_2025_10_BEFORE_MIGRATION.html
ls -lh output_files/HR_Dashboard_2025_10.html

# Expected: Similar size (±10%)
```

### 6.2 데이터 정확성 모니터링

```bash
# 주간 검증 스크립트
cat > verify_weekly.sh << 'EOF'
#!/bin/bash
echo "🔍 Weekly Team Mapping Verification"
echo "=================================="

python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder

builder = CompleteDashboardBuilder('2025-10')
team_data = builder._collect_team_data()

# Check basics
total = sum(len(team['members']) for team in team_data.values())
print(f'Teams: {len(team_data)} (expected: 12)')
print(f'Total: {total} (expected: 506)')
print(f'MTL: {len(team_data[\"MTL\"][\"members\"])} (expected: 33)')

# Alert if mismatch
if len(team_data) != 12 or total != 506:
    print('⚠️  WARNING: Data mismatch detected!')
    exit(1)
else:
    print('✅ All checks passed')
"
EOF

chmod +x verify_weekly.sh
```

### 6.3 사용자 피드백 수집

**체크리스트**:
- [ ] 팀 이름이 명확한가?
- [ ] 팀별 인원 수가 정확한가?
- [ ] MTL 팀이 독립적으로 표시되는가?
- [ ] 차트가 정상 작동하는가?
- [ ] 로딩 속도는 적절한가?

---

## 📈 성공 기준

### 필수 요구사항 (Must Have)
- ✅ 12개 팀 정확히 생성
- ✅ 506명 전원 매핑 (100%)
- ✅ MTL 독립 팀 복원 (33명)
- ✅ 기존 차트 모두 정상 작동
- ✅ 에러 0건

### 선택 요구사항 (Nice to Have)
- ⭐ 대시보드 생성 시간 < 30초
- ⭐ 파일 크기 증가 < 10%
- ⭐ 코드 가독성 향상
- ⭐ 문서화 완료

---

## 🎯 타임라인

| 단계 | 소요 시간 | 담당 | 완료 조건 |
|------|----------|------|----------|
| **Phase 1: 준비** | 4시간 | 개발자 | 백업 완료, 매핑 검증 |
| **Phase 2: 구현** | 1일 | 개발자 | 코드 작성 완료 |
| **Phase 3: 테스트** | 1일 | 개발자 | 모든 테스트 통과 |
| **Phase 4: 배포** | 4시간 | 개발자 | 프로덕션 배포 완료 |
| **Phase 5: 롤백** | 필요시 | 개발자 | N/A |
| **Phase 6: 모니터링** | 1주일 | 개발자 | 안정성 확인 |
| **총계** | **2-3일** | | |

---

## 🔧 트러블슈팅

### Issue 1: 매핑되지 않은 직원 발견

**증상**: "⚠️ Warning: Unmapped employee..." 메시지

**원인**: TEAM_MAPPING에 없는 position_3rd 값

**해결**:
1. 직원 정보 확인
2. 적절한 팀 결정
3. TEAM_MAPPING 업데이트
4. 재실행

### Issue 2: 팀 인원 수 불일치

**증상**: 예상 인원과 실제 인원 불일치

**원인**: 데이터 변경 또는 매핑 오류

**해결**:
```bash
python analyze_team_mapping_feasibility.py
# 결과 확인 후 TEAM_MAPPING 조정
```

### Issue 3: 대시보드 생성 오류

**증상**: HTML 생성 실패

**원인**: 함수 오류 또는 데이터 문제

**해결**:
```bash
# 레거시 함수로 전환
# complete_dashboard_builder.py에서:
team_data = self._collect_team_data_legacy()
```

### Issue 4: 차트 표시 오류

**증상**: JavaScript 에러 또는 빈 차트

**원인**: 팀 데이터 구조 변경

**해결**:
- team_data 구조가 변경되지 않았는지 확인
- 기존 JavaScript는 team_data.keys()만 사용하므로 호환성 유지

---

## 📝 체크리스트

### 배포 전
- [ ] 백업 완료
- [ ] TEAM_MAPPING 검증
- [ ] 코드 리뷰 완료
- [ ] 유닛 테스트 통과
- [ ] 통합 테스트 통과
- [ ] 성능 테스트 통과
- [ ] 문서 작성 완료

### 배포 시
- [ ] 프로덕션 대시보드 생성
- [ ] 파일 크기 확인
- [ ] 브라우저 수동 테스트
- [ ] 12개 팀 확인
- [ ] MTL 팀 확인
- [ ] 차트 동작 확인

### 배포 후
- [ ] 사용자 교육
- [ ] 피드백 수집
- [ ] 주간 모니터링 설정
- [ ] CHANGELOG 업데이트
- [ ] README 업데이트

---

## 🎉 완료 기념

배포 완료 후:

```bash
echo "
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║  🎉 팀 로직 마이그레이션 완료!                              ║
║                                                           ║
║  ✅ 12개 원조 팀 복원                                       ║
║  ✅ MTL 독립 팀 복원 (33명)                                 ║
║  ✅ 100% 매핑 달성 (506명)                                  ║
║  ✅ UNKNOWN 0명                                            ║
║                                                           ║
║  원조 management_dashboard의 명확한 팀 구조를               ║
║  현대적인 동적 시스템과 결합 성공!                           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
" | tee MIGRATION_SUCCESS.txt

# 팀별 인원 출력
python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder

builder = CompleteDashboardBuilder('2025-10')
team_data = builder._collect_team_data()

print('\n📊 최종 팀 구성:\n')
for team, data in sorted(team_data.items(), key=lambda x: len(x[1]['members']), reverse=True):
    count = len(data['members'])
    pct = count / 506 * 100
    print(f'   {team:20} {count:3}명 ({pct:5.1f}%)')
"
```

---

**작성자**: Claude Code
**최종 수정**: 2025-10-07
**버전**: 1.0 - Final Implementation Plan
**기반 문서**: FINAL_TEAM_MAPPING.md

---

## 📎 참고 문서

1. **FINAL_TEAM_MAPPING.md** - 100% 매핑 정보
2. **TEAM_LOGIC_ANALYSIS.md** - 원조 로직 분석
3. **TEAM_LOGIC_MIGRATION_PLAN.md** - 초기 계획 (Option 비교)
4. **unknown_70_mapping_recommendations.json** - 미분류 직원 분석
5. **analyze_team_mapping_feasibility.py** - 매핑 검증 스크립트
6. **get_employee_details.py** - 개별 직원 조회 도구
