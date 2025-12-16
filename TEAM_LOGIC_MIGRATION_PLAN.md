# 팀 로직 마이그레이션 계획 - Team Logic Migration Plan

## 📋 Executive Summary (요약)

**질문**: 원조 management_dashboard의 팀 로직을 최신 HR_Dashboard에 적용할 수 있는가?

**답변**: ⚠️ **조건부 가능** (86.2% 매핑 성공, 70명 미분류)

**권장사항**: **Option C (하이브리드)** - 명확한 팀 이름 + 동적 유연성 결합

---

## 🔍 현황 분석

### 원조 방식 (management_dashboard_2025_09.html)

**특징**:
- ✅ 12개 하드코딩된 팀 이름
- ✅ 명확한 팀 구조 (ASSEMBLY, OSC, QA 등)
- ✅ 간단한 JavaScript 처리 (`Object.keys()`)
- ❌ Python에서 사전 그룹화 필요
- ❌ 팀 변경 시 코드 수정 필요

**데이터 구조**:
```javascript
centralizedData = {
    "current_month": {
        "team_stats": {
            "ASSEMBLY": {"total": 119, "active": 119, "new": 0, "resigned": 0},
            "OSC": {"total": 25, "active": 25, "new": 0, "resigned": 0},
            // ... 12 teams
        },
        "team_members": {
            "ASSEMBLY": [{id, name, position, ...}, ...],
            "OSC": [{...}, ...],
            // ...
        }
    }
}
```

**팀 목록** (12개):
1. OFFICE & OCPT (4명)
2. OSC (25명)
3. ASSEMBLY (119명)
4. BOTTOM (32명)
5. QA (20명)
6. MTL (30명)
7. AQL (23명)
8. STITCHING (94명)
9. HWK QIP (1명)
10. CUTTING (8명)
11. REPACKING (17명)
12. NEW (20명)

**총원**: 393명

---

### 현재 방식 (HR_Dashboard_2025_10.html)

**특징**:
- ✅ 완전 자동화 (position_1st 기반)
- ✅ 데이터 변경 시 자동 반영
- ✅ boss_id 계층 구조
- ✅ 2단계 계층 (position_1st → position_2nd)
- ❌ 팀 이름이 직급명 (ASSEMBLY INSPECTOR, LINE LEADER 등)

**데이터 구조**:
```python
team_data = {
    "ASSEMBLY INSPECTOR": {
        "name": "ASSEMBLY INSPECTOR",
        "members": [{employee_no, full_name, position_1st, position_2nd, ...}, ...],
        "sub_teams": {
            "SHOES INSPECTOR": {"name": "...", "members": [...]},
            "UPPER INSPECTOR": {...}
        },
        "metrics": {...}
    },
    // ... 18 teams
}
```

**팀 목록** (18개 직급):
1. ASSEMBLY INSPECTOR (153명)
2. STITCHING INSPECTOR (106명)
3. NEW (55명)
4. BOTTOM INSPECTOR (39명)
5. MTL INSPECTOR (32명)
6. OSC INSPECTOR (27명)
7. AQL INSPECTOR (23명)
8. LINE LEADER (14명)
9. (V) SUPERVISOR (14명)
10. QA TEAM (9명)
11. GROUP LEADER (9명)
12. AUDIT & TRAINING TEAM (8명)
13. CUTTING INSPECTOR (7명)
14. MODEL MASTER (3명)
15. RQC (3명)
16. A.MANAGER (2명)
17. MANAGER (1명)
18. OCPT STFF (1명)

**총원**: 506명

---

## 🎯 매핑 분석 결과

### Position 3rd → 원조 12개 팀 매핑

**성공률**: 86.2% (436명/506명)

| 원조 팀 | 매핑 인원 | Position 3rd 값 개수 | 상태 |
|---------|-----------|---------------------|------|
| ASSEMBLY | 137명 | 7개 | ✅ 성공 |
| STITCHING | 117명 | 6개 | ✅ 성공 |
| NEW | 55명 | 1개 | ✅ 성공 |
| BOTTOM | 41명 | 5개 | ✅ 성공 |
| REPACKING | 27명 | 5개 | ✅ 성공 |
| AQL | 20명 | 4개 | ✅ 성공 |
| OSC | 18명 | 8개 | ✅ 성공 |
| QA | 10명 | 3개 | ✅ 성공 |
| CUTTING | 8명 | 2개 | ✅ 성공 |
| OFFICE & OCPT | 2명 | 2개 | ✅ 성공 |
| HWK QIP | 1명 | 1개 | ✅ 성공 |
| **MTL** | **0명** | **0개** | ❌ **실패** |
| **UNKNOWN** | **70명** | **18개** | ⚠️ **미분류** |

### 미분류 항목 상세 (70명)

**MTL 관련 (원래 OSC에 포함)**: 32명
- LEATHER TQC (8명)
- TEXTILE TQC (10명)
- SUBSI TQC (11명)
- HAPPO TQC (3명)

**특수 기능팀**: 18명
- AUDIT & TRAINING TEAM (8명)
- MODEL MASTER (3명)
- INHOUSE PRINTING/HF/NO-SEW (14명)

**기타**: 20명
- FG WH, SCAN PACK, ALL B-GRADE, etc.

---

## 💡 적용 옵션 분석

### Option A: 현재 방식 유지 (No Change)

**장점**:
- ✅ 코드 변경 없음
- ✅ 완전 자동화 유지
- ✅ 리스크 제로

**단점**:
- ❌ 팀 이름이 직급명 (비직관적)
- ❌ 18개 팀 (너무 세분화)
- ❌ 사용자 혼란 가능

**변경사항**: 없음

**권장 시나리오**: 현재 사용자가 만족하는 경우

---

### Option B: 원조 방식 완전 적용 (Full Migration)

**장점**:
- ✅ 명확한 12개 팀 이름
- ✅ 직관적인 구조
- ✅ 원조와 일관성

**단점**:
- ❌ 70명 미분류 처리 필요
- ❌ Python 코드 대규모 수정
- ❌ JavaScript 차트 로직 변경
- ❌ 매핑 로직 관리 오버헤드
- ❌ 유연성 감소

**변경사항**:

#### Python Backend (`complete_dashboard_builder.py`)

**1. 새 매핑 함수 추가**:
```python
def _map_to_original_teams(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
    """Map employees to 12 original teams"""

    TEAM_MAPPING = {
        'ASSEMBLY': [
            'ASSEMBLY LINE TQC', 'ASSEMBLY LINE RQC',
            '12 ASSEMBLY LINE QUALITY IN CHARGE',
            '2 ASSEMBLY BUILDING QUALITY IN CHARGE',
            '1 ASSEMBLY BUILDING QUALITY IN CHARGE',
            'ALL ASSEMBLY BUILDING QUALITY IN CHARGE',
            'ASSEMBLY LINE PO COMPLETION QUALITY'
        ],
        'STITCHING': [
            'STITCHING LINE TQC', 'STITCHING LINE RQC',
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
            'SUBSI MTL TEAM LEADER'
        ],
        'MTL': [
            'LEATHER TQC', 'TEXTILE TQC', 'SUBSI TQC', 'HAPPO TQC'
        ],
        'BOTTOM': [
            'BOTTOM INSPECTION TQC', 'BOTTOM INSPECTION RQC',
            'BOTTOM REPAIRING & PACKING TQC',
            '1 BUILDING BOTTOM QUALITY IN CHARGE',
            'ALL BUILDING BOTTOM QUALITY IN CHARGE'
        ],
        'AQL': [
            'AQL INSPECTOR', 'AQL ROOM PACKING TQC',
            'AQL INPUT CARTON TQC', 'AQL REPORT TEAM'
        ],
        'REPACKING': [
            'REPACKING LINE TQC', 'REPACKING LINE PACKING TQC',
            'REPACKING LINE REPAIRING TQC',
            'REPACKING AREA INPUT-OUTPUT CARTON TQC',
            'REPACKING LINE PO COMPLETION QUALITY'
        ],
        'QA': [
            'QA TEAM STAFF', 'QA TEAM HEAD', 'QA TEAM IN CHARGE'
        ],
        'CUTTING': [
            'CUTTING INSPECTOR', 'ALL CUTTING BUILDING QUALITY IN CHARGE'
        ],
        'HWK QIP': [
            'HWK QUALITY IN CHARGE'
        ],
        'OFFICE & OCPT': [
            'OCPT AND OFFICE TEAM LEADER',
            'QIP SAP & INCOMING QUALITY REPORT',
            'OCPT TEAM STAFF'
        ],
        'NEW': [
            'NEW'
        ]
    }

    # Build reverse mapping: position_3rd -> team_name
    reverse_mapping = {}
    for team_name, pos3_list in TEAM_MAPPING.items():
        for pos3 in pos3_list:
            reverse_mapping[pos3] = team_name

    # Group employees by team
    team_members = {team: [] for team in TEAM_MAPPING.keys()}
    team_members['UNKNOWN'] = []  # For unmapped employees

    for idx, row in df.iterrows():
        pos3 = str(row.get('QIP POSITION 3RD  NAME', ''))

        if pos3 in reverse_mapping:
            team_name = reverse_mapping[pos3]
        else:
            team_name = 'UNKNOWN'

        employee_info = {
            'employee_no': str(row.get('Employee No', '')),
            'full_name': str(row.get('Full Name', '')),
            'position_1st': str(row.get('QIP POSITION 1ST  NAME', '')),
            'position_2nd': str(row.get('QIP POSITION 2ND  NAME', '')),
            'position_3rd': pos3,
            # ... other fields
        }

        team_members[team_name].append(employee_info)

    return team_members
```

**2. `_collect_team_data()` 대체**:
```python
def _collect_team_data(self):
    """Collect team data using original 12-team structure"""
    data = self.collector.load_month_data(self.target_month)
    df = data.get('basic_manpower', pd.DataFrame())
    attendance_df = data.get('attendance', pd.DataFrame())

    if df.empty:
        return {}

    # Use new mapping function
    team_members = self._map_to_original_teams(df)

    # Build team_data structure
    team_data = {}
    for team_name, members in team_members.items():
        if not members:
            continue

        team_data[team_name] = {
            'name': team_name,
            'members': members,
            'metrics': self._calculate_team_metrics(members, attendance_df)
        }

    return team_data
```

#### JavaScript Frontend

**변경 불필요** - 이미 team_data를 순회하므로 팀 이름만 바뀜

**권장 시나리오**: 사용자가 명확한 12개 팀 구조를 강력히 원하는 경우

---

### Option C: 하이브리드 접근 (Recommended ⭐)

**장점**:
- ✅ 명확한 팀 이름
- ✅ 동적 유연성 유지
- ✅ 미분류 항목 자동 처리
- ✅ 최소 코드 변경
- ✅ 미래 확장성

**단점**:
- ⚠️ 약간의 복잡도 증가

**핵심 아이디어**:
- **1단계 그룹**: 12개 원조 팀 + UNKNOWN
- **2단계 그룹**: position_2nd 기반 sub_teams (현재 방식 유지)
- **자동 매핑**: 명확한 position_3rd는 매핑, 나머지는 UNKNOWN으로

**변경사항**:

#### Python Backend (`complete_dashboard_builder.py`)

```python
def _collect_team_data_hybrid(self):
    """
    Hybrid approach: 12 original teams + dynamic sub-teams
    원조 12개 팀 + 동적 하위팀 결합
    """
    data = self.collector.load_month_data(self.target_month)
    df = data.get('basic_manpower', pd.DataFrame())
    attendance_df = data.get('attendance', pd.DataFrame())

    if df.empty:
        return {}

    # Define team mapping (same as Option B)
    TEAM_MAPPING = { ... }  # See Option B

    # Build reverse mapping
    reverse_mapping = {}
    for team_name, pos3_list in TEAM_MAPPING.items():
        for pos3 in pos3_list:
            reverse_mapping[pos3] = team_name

    # Initialize team structure
    team_data = {team: {'name': team, 'members': [], 'sub_teams': {}}
                 for team in TEAM_MAPPING.keys()}
    team_data['UNKNOWN'] = {'name': 'UNKNOWN', 'members': [], 'sub_teams': {}}

    # Process each employee
    for idx, row in df.iterrows():
        pos3 = str(row.get('QIP POSITION 3RD  NAME', ''))
        pos2 = str(row.get('QIP POSITION 2ND  NAME', ''))

        # Map to team
        team_name = reverse_mapping.get(pos3, 'UNKNOWN')

        employee_info = {
            'employee_no': str(row.get('Employee No', '')),
            'full_name': str(row.get('Full Name', '')),
            'position_1st': str(row.get('QIP POSITION 1ST  NAME', '')),
            'position_2nd': pos2,
            'position_3rd': pos3,
            'boss_id': self._extract_boss_id(row),
            # ... other fields
        }

        # Add to team
        team_data[team_name]['members'].append(employee_info)

        # Add to sub-team (position_2nd)
        if pos2 and pos2 != 'nan':
            if pos2 not in team_data[team_name]['sub_teams']:
                team_data[team_name]['sub_teams'][pos2] = {
                    'name': pos2,
                    'members': []
                }
            team_data[team_name]['sub_teams'][pos2]['members'].append(employee_info)

    # Calculate metrics
    for team_name, team_info in team_data.items():
        team_info['metrics'] = self._calculate_team_metrics(
            team_info['members'], attendance_df
        )

        # Calculate sub-team metrics
        for sub_team_name, sub_team_info in team_info.get('sub_teams', {}).items():
            sub_team_info['metrics'] = self._calculate_team_metrics(
                sub_team_info['members'], attendance_df
            )

    # Remove empty teams
    team_data = {k: v for k, v in team_data.items() if v['members']}

    return team_data
```

**코드 변경**: 단일 함수 교체만 필요

**결과**:
- 13개 팀 (12 original + UNKNOWN 70명)
- 각 팀 내 sub_teams 유지
- 계층 구조 보존

---

## 📊 옵션 비교표

| 기준 | Option A (현재) | Option B (완전) | Option C (하이브리드) ⭐ |
|------|----------------|----------------|----------------------|
| **팀 수** | 18개 (직급) | 12개 (고정) | 13개 (12+UNKNOWN) |
| **팀 이름** | 직급명 | 명확한 이름 | 명확한 이름 |
| **코드 변경** | 없음 | 대규모 | 최소 (1개 함수) |
| **미분류 처리** | N/A | 수동 매핑 필요 | 자동 (UNKNOWN) |
| **유지보수** | 쉬움 | 어려움 | 중간 |
| **유연성** | 최고 | 최저 | 높음 |
| **직관성** | 낮음 | 최고 | 높음 |
| **리스크** | 없음 | 높음 | 낮음 |
| **권장도** | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 권장 실행 계획 (Option C)

### Phase 1: 준비 (1일)

1. **매핑 검증 스크립트 작성**
   - UNKNOWN 70명 상세 분석
   - MTL vs OSC 구분 명확화
   - 사용자 확인 필요 항목 리스트업

2. **백업 생성**
   ```bash
   cp src/visualization/complete_dashboard_builder.py \
      src/visualization/complete_dashboard_builder_backup.py
   ```

### Phase 2: 구현 (1일)

1. **`_collect_team_data_hybrid()` 함수 추가**
   - 위 코드 복사
   - TEAM_MAPPING 상수 정의
   - 기존 `_collect_team_data()` 유지 (롤백용)

2. **함수 호출 변경**
   ```python
   # In build_dashboard() method
   # Old:
   # team_data = self._collect_team_data()

   # New:
   team_data = self._collect_team_data_hybrid()
   ```

3. **테스트 대시보드 생성**
   ```bash
   python src/visualization/complete_dashboard_builder.py \
       --month 10 --year 2025 \
       --output output_files/HR_Dashboard_2025_10_HYBRID_TEST.html
   ```

### Phase 3: 검증 (1일)

1. **팀 수 확인**
   - 13개 팀 (12 + UNKNOWN) 생성 확인
   - 각 팀 인원 수 검증

2. **차트 동작 확인**
   - 모든 차트 정상 렌더링
   - 데이터 일관성 검증

3. **미분류 항목 검토**
   - UNKNOWN 70명 리스트 확인
   - 필요시 추가 매핑 규칙 작성

### Phase 4: 배포 (0.5일)

1. **기존 함수 대체**
   ```python
   # Rename old function
   def _collect_team_data_legacy(self):
       # ... old code

   # Use new function as default
   def _collect_team_data(self):
       return self._collect_team_data_hybrid()
   ```

2. **프로덕션 대시보드 생성**
   ```bash
   python src/visualization/complete_dashboard_builder.py \
       --month 10 --year 2025
   ```

3. **검증**
   ```bash
   python verify_maternity_updates.py  # 기존 검증 도구 사용
   ```

---

## ⚠️ 주의사항

### MTL 팀 정의 명확화 필요

**원조**: MTL 30명 (별도 팀)
**현재**: MTL INSPECTOR 32명이지만 OSC 카테고리에 포함

**질문 (사용자 확인 필요)**:
1. MTL을 독립 팀으로 유지할 것인가?
2. 아니면 OSC에 통합할 것인가?

**제안**:
- **Option 1**: MTL을 독립 팀으로 복원
  ```python
  'MTL': [
      'LEATHER TQC', 'TEXTILE TQC', 'SUBSI TQC', 'HAPPO TQC',
      'LEATHER MTL TEAM LEADER', 'TEXTILE MTL TEAM LEADER',
      'SUBSI MTL TEAM LEADER', 'MTL QUALITY IN CHARGE'
  ]
  ```
  → 결과: OSC 18명, MTL 32명 = 50명 총합 (원조 55명과 유사)

- **Option 2**: OSC에 통합 유지 (현재 방식)
  → 결과: OSC 50명, MTL 제거

### UNKNOWN 처리 전략

**UNKNOWN 70명 구성**:
- Audit & Training (8명) - 특수 기능팀
- Inhouse 관련 (14명) - 내부 검사팀
- Model Master (3명) - 특수 역할
- FG WH, Scan Pack 등 (20명) - 창고/포장

**옵션**:
1. **UNKNOWN 유지** - 가장 안전, 향후 분류 가능
2. **새 팀 생성** - "SPECIAL FUNCTIONS" 팀 추가
3. **기존 팀 확장** - 관련성 높은 팀에 강제 배정

**권장**: Option 1 (UNKNOWN 유지) → 사용자가 직접 분류 결정

---

## 🚀 즉시 실행 가능 명령어

```bash
# 1. 현재 상태 백업
cd "/Users/ksmoon/Downloads/대시보드 인센티브 테스트12_1_9월 25일 _맥북용/HR"
cp src/visualization/complete_dashboard_builder.py \
   src/visualization/complete_dashboard_builder_backup_$(date +%Y%m%d).py

# 2. 매핑 분석 재확인
python analyze_team_mapping_feasibility.py > team_mapping_report.txt

# 3. (사용자 승인 후) 하이브리드 구현 적용
# Edit complete_dashboard_builder.py with hybrid function

# 4. 테스트 대시보드 생성
python -c "
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder
builder = CompleteDashboardBuilder('2025-10')
builder.build_dashboard('output_files/HR_Dashboard_2025_10_HYBRID_TEST.html')
"

# 5. 검증
ls -lh output_files/HR_Dashboard_2025_10_HYBRID_TEST.html
```

---

## 📝 결론 및 권장사항

**질문**: 원조 팀 로직을 적용할 수 있는가?

**답변**: ✅ **예, Option C (하이브리드) 방식으로 가능합니다**

**이유**:
1. ✅ 86.2% 매핑 성공 (충분히 높은 커버리지)
2. ✅ 명확한 12개 팀 이름 제공 (원조와 일관성)
3. ✅ UNKNOWN으로 미분류 안전 처리
4. ✅ 최소 코드 변경 (1개 함수)
5. ✅ 기존 기능 모두 보존 (sub_teams, boss_id 계층)
6. ✅ 롤백 용이 (legacy 함수 유지)

**변경 범위**:
- **Python**: `complete_dashboard_builder.py` 1개 함수 (`_collect_team_data()`)
- **JavaScript**: 변경 없음 (기존 로직 그대로 사용)
- **데이터**: 변경 없음 (매핑만 추가)

**예상 작업 시간**: 2-3일
- Day 1: 매핑 검증 및 구현
- Day 2: 테스트 및 검증
- Day 3: 배포 및 모니터링

**다음 단계**:
1. 사용자 승인 대기
2. MTL 팀 처리 방침 결정 (독립 vs OSC 통합)
3. UNKNOWN 처리 전략 선택
4. 구현 및 배포

---

## 📎 참고 문서

- `TEAM_LOGIC_ANALYSIS.md` - 원조 팀 로직 상세 분석
- `analyze_team_mapping_feasibility.py` - 매핑 가능성 분석 스크립트
- `src/visualization/complete_dashboard_builder.py` - 현재 구현체
- `output_files/management_dashboard_2025_09.html` - 원조 대시보드

---

**작성일**: 2025-10-07
**작성자**: Claude Code
**버전**: 1.0
