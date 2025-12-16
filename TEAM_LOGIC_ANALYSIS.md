# 팀 정보 로직 분석 - management_dashboard_2025_09.html

## 📊 핵심 발견: 11개 팀별 분석 구조

### 1. 데이터 구조 (centralizedData)

```javascript
const centralizedData = {
    "current_month": {
        "total_employees": 393,
        "team_stats": {
            "OFFICE & OCPT": {"total": 4, "new": 0, "resigned": 0, "active": 4},
            "OSC": {"total": 25, "new": 0, "resigned": 0, "active": 25},
            "ASSEMBLY": {"total": 119, "new": 0, "resigned": 0, "active": 119},
            "BOTTOM": {"total": 32, "new": 0, "resigned": 0, "active": 32},
            "QA": {"total": 20, "new": 0, "resigned": 0, "active": 20},
            "MTL": {"total": 30, "new": 0, "resigned": 0, "active": 30},
            "AQL": {"total": 23, "new": 0, "resigned": 0, "active": 23},
            "STITCHING": {"total": 94, "new": 0, "resigned": 0, "active": 94},
            "HWK QIP": {"total": 1, "new": 0, "resigned": 0, "active": 1},
            "CUTTING": {"total": 8, "new": 0, "resigned": 0, "active": 8},
            "REPACKING": {"total": 17, "new": 0, "resigned": 0, "active": 17},
            "NEW": {"total": 20, "new": 0, "resigned": 0, "active": 20}
        },
        "team_members": {
            "OFFICE & OCPT": [
                {
                    "id": 617100049,
                    "name": "ĐINH KIM NGOAN",
                    "position": "GROUP LEADER",
                    "position_1st": "GROUP LEADER",
                    "position_2nd": "REPORT TEAM",
                    "position_3rd": "TEAM OPERATION MANAGEMENT",
                    "role": "REPORT",
                    "join_date": "2017-10-24",
                    "total_days": 13.0,
                    "actual_days": 13.0,
                    "absence_days": 0,
                    "is_full_attendance": "Y"
                },
                // ... more members
            ],
            "OSC": [ /* 25 members */ ],
            "ASSEMBLY": [ /* 119 members */ ],
            // ... 다른 팀들
        }
    }
}
```

### 2. 팀 분류 로직

**11개 팀**:
1. OFFICE & OCPT (4명)
2. OSC (25명)
3. ASSEMBLY (119명) - 가장 큰 팀
4. BOTTOM (32명)
5. QA (20명)
6. MTL (30명)
7. AQL (23명)
8. STITCHING (94명)
9. HWK QIP (1명)
10. CUTTING (8명)
11. REPACKING (17명)
12. NEW (20명) - 신규 QIP

**총 인원**: 393명

### 3. 팀 구분 기준

#### 방법 1: position_3rd 필드 기반
```javascript
// position_3rd가 팀을 나타냄
"TEAM OPERATION MANAGEMENT"
"HWK OSC/MTL QUALITY IN CHARGE"
"INHOUSE PRINTING INSPECTION RQC"
"ALL ASSEMBLY QUALITY IN CHARGE"
"12 ASSEMBLY LINE QUALITY IN CHARGE"
// ...
```

#### 방법 2: 직접 team_members 객체의 키
```javascript
const teamNames = Object.keys(centralizedData.current_month.team_members);
// ["OFFICE & OCPT", "OSC", "ASSEMBLY", "BOTTOM", ...]
```

### 4. 팀별 메트릭 계산

```javascript
// team_stats에서 직접 추출
const teamStats = centralizedData.current_month.team_stats;

Object.entries(teamStats).forEach(([teamName, stats]) => {
    console.log(`${teamName}:`, stats.total, '명');
    // OFFICE & OCPT: 4 명
    // OSC: 25 명
    // ASSEMBLY: 119 명
    // ...
});
```

### 5. 팀별 상세 정보 (team_members)

각 팀원 정보:
- **id**: 사원번호 (int)
- **name**: 이름
- **position**: 직급 (position_1st, position_2nd, position_3rd)
- **role**: 역할 (TOP-MANAGEMENT, MID-MANAGEMENT, INSPECTOR, REPORT)
- **join_date**: 입사일
- **total_days**: 총 근무일
- **actual_days**: 실제 출근일
- **absence_days**: 결근일
- **is_full_attendance**: 개근 여부 (Y/N)

### 6. 팀별 분석 차트 구현 방법

```javascript
// 1. 팀 목록 추출
const teamNames = Object.keys(teamStats);

// 2. 팀별 데이터 수집
const teamSizes = teamNames.map(name => teamStats[name].total);
const teamActiveCount = teamNames.map(name => teamStats[name].active);

// 3. Chart.js로 시각화
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: teamNames,
        datasets: [{
            label: '팀별 인원',
            data: teamSizes,
            backgroundColor: 'rgba(54, 162, 235, 0.7)'
        }]
    }
});
```

### 7. 팀별 출근율 계산

```javascript
function calculateTeamAttendance(teamName) {
    const members = centralizedData.current_month.team_members[teamName];

    let totalDays = 0;
    let actualDays = 0;

    members.forEach(member => {
        totalDays += member.total_days;
        actualDays += member.actual_days;
    });

    const attendanceRate = (actualDays / totalDays) * 100;
    return attendanceRate;
}
```

### 8. 팀별 개근자 비율

```javascript
function calculateFullAttendanceRate(teamName) {
    const members = centralizedData.current_month.team_members[teamName];
    const fullAttendanceCount = members.filter(m => m.is_full_attendance === 'Y').length;
    const totalMembers = members.length;

    return (fullAttendanceCount / totalMembers) * 100;
}
```

## 💡 핵심 인사이트

### 데이터 구조의 장점:
1. **중앙 집중식**: `centralizedData` 하나로 모든 데이터 관리
2. **계층 구조**: team_stats (요약) + team_members (상세)
3. **필터링 완료**: 이미 팀별로 분류된 상태
4. **메트릭 사전 계산**: total, new, resigned, active 값 포함

### 데이터 구조의 단점:
1. **하드코딩된 팀 이름**: 팀 이름이 변경되면 수동 업데이트 필요
2. **position 필드 중복**: position_1st, position_2nd, position_3rd, position2, position3
3. **JSON 크기**: 전체 직원 정보를 HTML에 embedded (691KB)

## 🔄 HR_Dashboard_2025_10.html과의 차이점

### management_dashboard (원조):
- **팀 분류**: 하드코딩된 12개 팀 이름
- **데이터 소스**: `centralizedData.current_month.team_members`
- **팀 추출**: `Object.keys(team_members)`

### HR_Dashboard_2025_10 (현재):
- **팀 분류**: `position_1st` 필드 기반 동적 그룹화
- **데이터 소스**: `basic_manpower` + `boss_id` 관계
- **팀 추출**: 계층 구조 재구성 (`_build_hierarchy_data()`)

## 📝 결론

**management_dashboard의 팀 로직**은:
1. Python에서 미리 팀별로 데이터를 그룹화
2. `team_stats`와 `team_members`를 JSON으로 생성
3. JavaScript에서 Object.keys()로 팀 이름 추출
4. 팀별 루프로 카드/차트 생성

**장점**: 간단하고 직관적
**단점**: 팀 구조 변경시 Python 코드 수정 필요

**HR_Dashboard의 개선점**:
- 동적 계층 구조 재구성
- boss_id 기반 자동 팀 감지
- position 필드 기반 유연한 그룹화
