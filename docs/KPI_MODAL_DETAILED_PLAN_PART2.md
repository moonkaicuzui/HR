# KPI 모달 상세 구현 계획서 - Part 2
# KPI Modal Detailed Implementation Plan - Part 2

**작성일 / Date**: 2025-10-06
**버전 / Version**: 2.0
**대상 KPI / Target KPIs**: 5번~11번

---

## 5️⃣ 신규 입사자 (Recent Hires) 모달

### 모달 제목
```
한국어: "신규 입사자 상세 분석"
English: "Recent Hires - Detailed Analysis"
Vietnamese: "Phân tích nhân viên mới tuyển dụng"
```

### 섹션 1: 현황 요약 카드
```html
<div class="modal-stat-grid">
    <div class="stat-card">
        <div class="stat-icon">🎉</div>
        <div class="stat-label">9월 신규 입사자 / New Hires (Sep)</div>
        <div class="stat-value">7명</div>
        <div class="stat-sublabel">전월 대비 -3명</div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-label">3개월 평균 / 3M Average</div>
        <div class="stat-value">9명/월</div>
        <div class="stat-sublabel">총 27명 입사</div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-label">온보딩 완료율 / Onboarding Rate</div>
        <div class="stat-value">85.7%</div>
        <div class="stat-sublabel">6명 / 7명 완료</div>
    </div>
</div>
```

### 섹션 2: 월별 채용 추세 (3개월)
```javascript
const hiringTrendData = {
    labels: ['7월 July', '8월 August', '9월 September'],
    datasets: [
        {
            label: '신규 입사자 / New Hires',
            data: [11, 9, 7],
            backgroundColor: 'rgba(102, 126, 234, 0.7)',
            borderColor: '#667eea',
            borderWidth: 2
        },
        {
            label: '채용 목표 / Target',
            data: [10, 10, 10],
            type: 'line',
            borderColor: '#10b981',
            borderDash: [5, 5],
            borderWidth: 2,
            pointRadius: 0,
            fill: false
        }
    ]
};

const hiringChartOptions = {
    responsive: true,
    plugins: {
        title: {
            display: true,
            text: '월별 채용 추세 (최근 3개월)',
            font: { size: 16, weight: 'bold' }
        },
        legend: {
            display: true,
            position: 'bottom'
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            ticks: {
                stepSize: 2,
                callback: function(value) {
                    return value + '명';
                }
            }
        }
    }
};
```

### 섹션 3: 직급별 채용 분포
```html
<div class="position-hiring-distribution">
    <h6>직급별 신규 입사자 분포 (9월) / Position Distribution (Sep)</h6>

    <div class="row">
        <div class="col-md-6">
            <canvas id="positionHiringPieChart"></canvas>
        </div>
        <div class="col-md-6">
            <div class="position-breakdown">
                <div class="position-item">
                    <div class="position-header">
                        <span class="position-badge bg-primary">A.INSPECTOR</span>
                        <span class="position-count">4명 (57.1%)</span>
                    </div>
                    <div class="position-detail">
                        Team A: 2명 | Team B: 1명 | Team C: 1명
                    </div>
                </div>

                <div class="position-item">
                    <div class="position-header">
                        <span class="position-badge bg-info">LINE LEADER</span>
                        <span class="position-count">2명 (28.6%)</span>
                    </div>
                    <div class="position-detail">
                        Team A: 1명 | Team B: 1명
                    </div>
                </div>

                <div class="position-item">
                    <div class="position-header">
                        <span class="position-badge bg-secondary">기타 / Others</span>
                        <span class="position-count">1명 (14.3%)</span>
                    </div>
                    <div class="position-detail">
                        A.MANAGER: 1명
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 섹션 4: 팀별 배정 현황
```html
<div class="team-assignment-status">
    <h6>팀별 배정 현황 / Team Assignment Status</h6>

    <div class="team-cards-grid">
        <div class="team-assignment-card">
            <div class="team-header">
                <span class="team-name">Team A</span>
                <span class="team-badge bg-success">3명</span>
            </div>
            <div class="team-progress">
                <div class="progress">
                    <div class="progress-bar bg-success" style="width: 100%">
                        100% 배정 완료
                    </div>
                </div>
            </div>
            <div class="team-detail">
                A.INSPECTOR (2) | LINE LEADER (1)
            </div>
        </div>

        <div class="team-assignment-card">
            <div class="team-header">
                <span class="team-name">Team B</span>
                <span class="team-badge bg-success">2명</span>
            </div>
            <div class="team-progress">
                <div class="progress">
                    <div class="progress-bar bg-success" style="width: 100%">
                        100% 배정 완료
                    </div>
                </div>
            </div>
            <div class="team-detail">
                A.INSPECTOR (1) | LINE LEADER (1)
            </div>
        </div>

        <div class="team-assignment-card">
            <div class="team-header">
                <span class="team-name">Team C</span>
                <span class="team-badge bg-warning">2명</span>
            </div>
            <div class="team-progress">
                <div class="progress">
                    <div class="progress-bar bg-warning" style="width: 50%">
                        50% 배정 진행중
                    </div>
                </div>
            </div>
            <div class="team-detail">
                A.INSPECTOR (1) | 배정대기 (1)
            </div>
        </div>
    </div>
</div>
```

### 섹션 5: 온보딩 진행 현황
```html
<div class="onboarding-progress">
    <h6>온보딩 진행 현황 / Onboarding Progress</h6>

    <div class="onboarding-timeline">
        <div class="timeline-stages">
            <div class="stage completed">
                <div class="stage-icon">✓</div>
                <div class="stage-name">입사 서류</div>
                <div class="stage-count">7/7</div>
            </div>
            <div class="stage completed">
                <div class="stage-icon">✓</div>
                <div class="stage-name">오리엔테이션</div>
                <div class="stage-count">7/7</div>
            </div>
            <div class="stage in-progress">
                <div class="stage-icon">⏳</div>
                <div class="stage-name">직무 교육</div>
                <div class="stage-count">6/7</div>
            </div>
            <div class="stage pending">
                <div class="stage-icon">○</div>
                <div class="stage-name">OJT</div>
                <div class="stage-count">4/7</div>
            </div>
            <div class="stage pending">
                <div class="stage-icon">○</div>
                <div class="stage-name">평가</div>
                <div class="stage-count">0/7</div>
            </div>
        </div>
    </div>

    <div class="onboarding-details">
        <h6>개인별 진행 상황</h6>
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>사번</th>
                    <th>이름</th>
                    <th>팀</th>
                    <th>입사일</th>
                    <th>진행 단계</th>
                    <th>완료율</th>
                    <th>담당 멘토</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>E12345</td>
                    <td>홍길동</td>
                    <td>Team A</td>
                    <td>2025-09-01</td>
                    <td>
                        <span class="badge bg-warning">OJT 진행중</span>
                    </td>
                    <td>
                        <div class="progress progress-sm">
                            <div class="progress-bar" style="width: 80%">80%</div>
                        </div>
                    </td>
                    <td>김멘토</td>
                </tr>
                <!-- More rows... -->
            </tbody>
        </table>
    </div>
</div>
```

### 섹션 6: 신규 입사자 명단
```html
<div class="new-hires-list">
    <h6>9월 신규 입사자 명단 (7명) / New Hires List (Sep - 7)</h6>

    <table class="table table-hover">
        <thead>
            <tr>
                <th>사번 / ID</th>
                <th>이름 / Name</th>
                <th>직급 / Position</th>
                <th>팀 / Team</th>
                <th>입사일 / Hire Date</th>
                <th>재직일수 / Days</th>
                <th>온보딩 / Onboarding</th>
                <th>멘토 / Mentor</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>E12345</td>
                <td>홍길동</td>
                <td><span class="badge bg-primary">A.INSPECTOR</span></td>
                <td>Team A</td>
                <td>2025-09-01</td>
                <td>29일</td>
                <td>
                    <span class="badge bg-warning">80% 진행중</span>
                </td>
                <td>김멘토</td>
            </tr>
            <tr>
                <td>E12346</td>
                <td>김철수</td>
                <td><span class="badge bg-info">LINE LEADER</span></td>
                <td>Team A</td>
                <td>2025-09-05</td>
                <td>25일</td>
                <td>
                    <span class="badge bg-success">100% 완료</span>
                </td>
                <td>이멘토</td>
            </tr>
            <!-- More rows... -->
        </tbody>
    </table>
</div>
```

### 섹션 7: 조기 이탈 위험 분석
```html
<div class="early-departure-risk">
    <h6>⚠️ 조기 이탈 위험 분석 / Early Departure Risk Analysis</h6>

    <div class="alert alert-info">
        <strong>ℹ️ 위험 지표 기반 분석</strong>
        <p>출근율, 교육 참여도, 멘토 피드백을 종합하여 조기 이탈 위험도 산출</p>
    </div>

    <div class="risk-cards-grid">
        <div class="risk-card low">
            <div class="risk-level">낮음 / Low</div>
            <div class="risk-count">5명 (71.4%)</div>
            <div class="risk-indicator">✓ 안정적</div>
        </div>

        <div class="risk-card medium">
            <div class="risk-level">보통 / Medium</div>
            <div class="risk-count">1명 (14.3%)</div>
            <div class="risk-indicator">⚠️ 주의 관찰</div>
        </div>

        <div class="risk-card high">
            <div class="risk-level">높음 / High</div>
            <div class="risk-count">1명 (14.3%)</div>
            <div class="risk-indicator">🚨 조치 필요</div>
        </div>
    </div>

    <div class="risk-details">
        <h6>위험군 상세 / High Risk Details</h6>
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>사번</th>
                    <th>이름</th>
                    <th>위험도</th>
                    <th>출근율</th>
                    <th>교육 참여</th>
                    <th>멘토 피드백</th>
                    <th>권장 조치</th>
                </tr>
            </thead>
            <tbody>
                <tr class="table-danger">
                    <td>E12347</td>
                    <td>이영희</td>
                    <td><span class="badge bg-danger">높음</span></td>
                    <td class="text-danger">85%</td>
                    <td class="text-warning">보통</td>
                    <td class="text-warning">의욕 저하</td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger">
                            1:1 면담 필요
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
```

---

## 6️⃣ 최근 퇴사자 (Recent Resignations) 모달

### 모달 제목
```
한국어: "최근 퇴사자 상세 분석"
English: "Recent Resignations - Detailed Analysis"
Vietnamese: "Phân tích nhân viên nghỉ việc gần đây"
```

### 섹션 1: 현황 요약 카드
```html
<div class="modal-stat-grid">
    <div class="stat-card alert-warning">
        <div class="stat-icon">📉</div>
        <div class="stat-label">9월 퇴사자 / Resignations (Sep)</div>
        <div class="stat-value">8명</div>
        <div class="stat-sublabel">전월 대비 +1명</div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-label">평균 재직기간 / Avg Tenure</div>
        <div class="stat-value">8.5개월</div>
        <div class="stat-sublabel">258일</div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">💰</div>
        <div class="stat-label">대체 비용 추정 / Replacement Cost</div>
        <div class="stat-value">$24,000</div>
        <div class="stat-sublabel">8명 × $3,000</div>
    </div>
</div>
```

### 섹션 2: 월별 퇴사 추세 (3개월)
```javascript
const resignationsTrendData = {
    labels: ['7월 July', '8월 August', '9월 September'],
    datasets: [
        {
            label: '퇴사자 수 / Resignations',
            data: [10, 7, 8],
            backgroundColor: 'rgba(239, 68, 68, 0.7)',
            borderColor: '#ef4444',
            borderWidth: 2
        },
        {
            label: '신규 입사자 / New Hires',
            data: [11, 9, 7],
            backgroundColor: 'rgba(16, 185, 129, 0.7)',
            borderColor: '#10b981',
            borderWidth: 2
        }
    ]
};

const resignationsChartOptions = {
    responsive: true,
    plugins: {
        title: {
            display: true,
            text: '입사 vs 퇴사 추세 (최근 3개월)',
            font: { size: 16, weight: 'bold' }
        },
        legend: {
            display: true,
            position: 'bottom'
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            ticks: {
                stepSize: 2,
                callback: function(value) {
                    return value + '명';
                }
            }
        }
    }
};
```

### 섹션 3: 퇴사 사유 상세 분석
```html
<div class="resignation-reasons-detail">
    <h6>퇴사 사유 상세 분석 / Resignation Reasons Detailed Analysis</h6>

    <div class="row">
        <div class="col-md-5">
            <canvas id="resignationReasonsPieChart"></canvas>
        </div>
        <div class="col-md-7">
            <div class="reasons-breakdown">
                <div class="reason-card primary">
                    <div class="reason-header">
                        <span class="reason-icon">👤</span>
                        <span class="reason-title">자발적 퇴사 / Voluntary</span>
                        <span class="reason-badge">5명 (62.5%)</span>
                    </div>
                    <div class="reason-details">
                        <div class="reason-sub-item">
                            <span class="sub-reason">💰 급여 불만</span>
                            <span class="sub-count">2명</span>
                        </div>
                        <div class="reason-sub-item">
                            <span class="sub-reason">🏢 근무환경</span>
                            <span class="sub-count">2명</span>
                        </div>
                        <div class="reason-sub-item">
                            <span class="sub-reason">👨‍👩‍👧 개인사정</span>
                            <span class="sub-count">1명</span>
                        </div>
                    </div>
                    <div class="reason-action">
                        <button class="btn btn-sm btn-outline-primary">
                            급여 체계 재검토
                        </button>
                    </div>
                </div>

                <div class="reason-card secondary">
                    <div class="reason-header">
                        <span class="reason-icon">📄</span>
                        <span class="reason-title">계약 만료 / Contract End</span>
                        <span class="reason-badge">2명 (25.0%)</span>
                    </div>
                    <div class="reason-details">
                        <div class="reason-sub-item">
                            <span class="sub-reason">정규직 전환 실패</span>
                            <span class="sub-count">1명</span>
                        </div>
                        <div class="reason-sub-item">
                            <span class="sub-reason">계약 갱신 거부</span>
                            <span class="sub-count">1명</span>
                        </div>
                    </div>
                    <div class="reason-action">
                        <button class="btn btn-sm btn-outline-warning">
                            전환 프로세스 개선
                        </button>
                    </div>
                </div>

                <div class="reason-card danger">
                    <div class="reason-header">
                        <span class="reason-icon">🚫</span>
                        <span class="reason-title">해고 / Termination</span>
                        <span class="reason-badge">1명 (12.5%)</span>
                    </div>
                    <div class="reason-details">
                        <div class="reason-sub-item">
                            <span class="sub-reason">무단결근 3회 이상</span>
                            <span class="sub-count">1명</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 섹션 4: 재직기간별 퇴사 분포
```html
<div class="tenure-resignation-distribution">
    <h6>재직기간별 퇴사 분포 / Tenure Distribution of Resignees</h6>

    <canvas id="tenureResignationBarChart"></canvas>

    <div class="tenure-analysis-grid">
        <div class="tenure-analysis-card danger">
            <div class="card-icon">⚠️</div>
            <div class="card-content">
                <div class="card-title">조기 이탈 심각</div>
                <div class="card-metric">3명 (37.5%)</div>
                <div class="card-desc">6개월 미만 재직 후 퇴사</div>
                <div class="card-recommendation">
                    <strong>권장 조치:</strong> 온보딩 프로세스 전면 재검토
                </div>
            </div>
        </div>

        <div class="tenure-analysis-card warning">
            <div class="card-icon">📊</div>
            <div class="card-content">
                <div class="card-title">1년차 이탈</div>
                <div class="card-metric">2명 (25.0%)</div>
                <div class="card-desc">6개월~1년 재직 후 퇴사</div>
                <div class="card-recommendation">
                    <strong>권장 조치:</strong> 경력 개발 프로그램 강화
                </div>
            </div>
        </div>

        <div class="tenure-analysis-card info">
            <div class="card-icon">📈</div>
            <div class="card-content">
                <div class="card-title">장기 재직</div>
                <div class="card-metric">3명 (37.5%)</div>
                <div class="card-desc">1년 이상 재직 후 퇴사</div>
                <div class="card-recommendation">
                    <strong>참고:</strong> 주로 급여 및 승진 관련 사유
                </div>
            </div>
        </div>
    </div>
</div>
```

### 섹션 5: 퇴사자 상세 명단
```html
<div class="resignees-detailed-list">
    <h6>9월 퇴사자 상세 명단 / Detailed Resignees List (Sep - 8)</h6>

    <div class="table-controls mb-3">
        <div class="row">
            <div class="col-md-4">
                <input type="text" class="form-control form-control-sm"
                       placeholder="검색... / Search..."
                       onkeyup="filterResigneesTable(this.value)">
            </div>
            <div class="col-md-3">
                <select class="form-select form-select-sm"
                        onchange="filterByReason(this.value)">
                    <option value="">전체 사유 / All Reasons</option>
                    <option value="voluntary">자발적 퇴사</option>
                    <option value="contract">계약 만료</option>
                    <option value="termination">해고</option>
                </select>
            </div>
            <div class="col-md-3">
                <select class="form-select form-select-sm"
                        onchange="filterByTenure(this.value)">
                    <option value="">전체 재직기간 / All Tenure</option>
                    <option value="<6m">6개월 미만</option>
                    <option value="6m-1y">6개월~1년</option>
                    <option value=">1y">1년 이상</option>
                </select>
            </div>
            <div class="col-md-2">
                <button class="btn btn-sm btn-outline-success w-100"
                        onclick="exportResigneesData()">
                    <i class="bi bi-download"></i> Excel
                </button>
            </div>
        </div>
    </div>

    <div class="table-responsive">
        <table class="table table-hover table-sm" id="resigneesTable">
            <thead class="sticky-header">
                <tr>
                    <th onclick="sortResigneesTable(0)">사번 / ID
                        <i class="bi bi-arrow-down-up"></i>
                    </th>
                    <th onclick="sortResigneesTable(1)">이름 / Name
                        <i class="bi bi-arrow-down-up"></i>
                    </th>
                    <th onclick="sortResigneesTable(2)">직급 / Position
                        <i class="bi bi-arrow-down-up"></i>
                    </th>
                    <th onclick="sortResigneesTable(3)">팀 / Team
                        <i class="bi bi-arrow-down-up"></i>
                    </th>
                    <th onclick="sortResigneesTable(4)">입사일 / Hire Date
                        <i class="bi bi-arrow-down-up"></i>
                    </th>
                    <th onclick="sortResigneesTable(5)">퇴사일 / Exit Date
                        <i class="bi bi-arrow-down-up"></i>
                    </th>
                    <th onclick="sortResigneesTable(6)">재직일수 / Days
                        <i class="bi bi-arrow-down-up"></i>
                    </th>
                    <th onclick="sortResigneesTable(7)">재직기간 / Tenure
                        <i class="bi bi-arrow-down-up"></i>
                    </th>
                    <th>퇴사 사유 / Reason</th>
                    <th>엑시트 인터뷰 / Exit Interview</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>E12345</td>
                    <td>홍길동</td>
                    <td><span class="badge bg-primary">A.INSPECTOR</span></td>
                    <td>Team A</td>
                    <td>2025-03-15</td>
                    <td>2025-09-20</td>
                    <td>189일</td>
                    <td>
                        <span class="badge bg-warning">6.3개월</span>
                    </td>
                    <td>
                        <span class="badge bg-danger">자발적 퇴사</span>
                        <br><small class="text-muted">급여 불만</small>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary"
                                onclick="viewExitInterview('E12345')">
                            <i class="bi bi-file-text"></i> 보기
                        </button>
                    </td>
                </tr>
                <!-- More rows... -->
            </tbody>
        </table>
    </div>

    <div class="table-pagination">
        <div class="showing-info">
            Showing <span id="showingResigneesCount">8</span> of 8 resignees
        </div>
    </div>
</div>
```

### 섹션 6: 엑시트 인터뷰 분석
```html
<div class="exit-interview-analysis">
    <h6>엑시트 인터뷰 주요 피드백 분석 / Exit Interview Feedback Analysis</h6>

    <div class="row">
        <div class="col-md-6">
            <div class="feedback-frequency">
                <h6>언급 빈도 Top 5</h6>
                <div class="feedback-tags-cloud">
                    <span class="tag tag-xl">급여 불만 (5건)</span>
                    <span class="tag tag-lg">근무환경 (4건)</span>
                    <span class="tag tag-md">성장 기회 부족 (3건)</span>
                    <span class="tag tag-md">업무 강도 (3건)</span>
                    <span class="tag tag-sm">직급 체계 (2건)</span>
                </div>
            </div>
        </div>

        <div class="col-md-6">
            <div class="feedback-sentiment">
                <h6>긍정/부정 의견 비율</h6>
                <canvas id="sentimentPieChart"></canvas>
                <div class="sentiment-legend">
                    <div class="legend-item">
                        <span class="color-box bg-danger"></span>
                        <span>부정 의견: 65%</span>
                    </div>
                    <div class="legend-item">
                        <span class="color-box bg-warning"></span>
                        <span>중립 의견: 25%</span>
                    </div>
                    <div class="legend-item">
                        <span class="color-box bg-success"></span>
                        <span>긍정 의견: 10%</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="feedback-quotes">
        <h6>주요 피드백 발췌 / Key Feedback Quotes</h6>
        <div class="quote-cards">
            <div class="quote-card negative">
                <div class="quote-header">
                    <span class="quote-icon">💬</span>
                    <span class="quote-category">급여</span>
                    <span class="quote-sentiment bg-danger">부정</span>
                </div>
                <div class="quote-text">
                    "동일 업계 타사 대비 급여가 20% 낮습니다.
                    성과급 체계도 불명확하여 동기부여가 어렵습니다."
                </div>
                <div class="quote-footer">
                    <span>E12345 홍길동 (A.INSPECTOR, 6개월 재직)</span>
                </div>
            </div>

            <div class="quote-card negative">
                <div class="quote-header">
                    <span class="quote-icon">💬</span>
                    <span class="quote-category">근무환경</span>
                    <span class="quote-sentiment bg-danger">부정</span>
                </div>
                <div class="quote-text">
                    "야근이 잦고 휴식 공간이 부족합니다.
                    작업 환경 개선이 시급합니다."
                </div>
                <div class="quote-footer">
                    <span>E12346 김철수 (LINE LEADER, 8개월 재직)</span>
                </div>
            </div>

            <div class="quote-card neutral">
                <div class="quote-header">
                    <span class="quote-icon">💬</span>
                    <span class="quote-category">성장</span>
                    <span class="quote-sentiment bg-warning">중립</span>
                </div>
                <div class="quote-text">
                    "교육 프로그램은 있으나 실질적인 승진 기회가 제한적입니다."
                </div>
                <div class="quote-footer">
                    <span>E12347 이영희 (A.INSPECTOR, 1.2년 재직)</span>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 섹션 7: 개선 액션 플랜
```html
<div class="improvement-action-plan">
    <h6>📋 개선 액션 플랜 / Improvement Action Plan</h6>

    <div class="action-items">
        <div class="action-item priority-high">
            <div class="action-header">
                <span class="priority-badge bg-danger">최우선</span>
                <span class="action-title">급여 체계 재검토</span>
            </div>
            <div class="action-body">
                <div class="action-description">
                    동일 업계 급여 조사 후 competitive package 설계
                </div>
                <div class="action-meta">
                    <span class="action-owner">담당: HR팀</span>
                    <span class="action-deadline">기한: 2025-10-31</span>
                    <span class="action-budget">예산: $50,000</span>
                </div>
            </div>
            <div class="action-progress">
                <div class="progress">
                    <div class="progress-bar bg-danger" style="width: 10%">10%</div>
                </div>
            </div>
        </div>

        <div class="action-item priority-medium">
            <div class="action-header">
                <span class="priority-badge bg-warning">중요</span>
                <span class="action-title">온보딩 프로세스 개선</span>
            </div>
            <div class="action-body">
                <div class="action-description">
                    6개월 미만 조기 이탈 방지 위한 멘토링 강화
                </div>
                <div class="action-meta">
                    <span class="action-owner">담당: 각 팀장</span>
                    <span class="action-deadline">기한: 2025-10-15</span>
                    <span class="action-budget">예산: $5,000</span>
                </div>
            </div>
            <div class="action-progress">
                <div class="progress">
                    <div class="progress-bar bg-warning" style="width: 40%">40%</div>
                </div>
            </div>
        </div>

        <div class="action-item priority-low">
            <div class="action-header">
                <span class="priority-badge bg-info">보통</span>
                <span class="action-title">근무환경 개선</span>
            </div>
            <div class="action-body">
                <div class="action-description">
                    휴게 공간 확충 및 근무 설비 업그레이드
                </div>
                <div class="action-meta">
                    <span class="action-owner">담당: 시설팀</span>
                    <span class="action-deadline">기한: 2025-11-30</span>
                    <span class="action-budget">예산: $15,000</span>
                </div>
            </div>
            <div class="action-progress">
                <div class="progress">
                    <div class="progress-bar bg-info" style="width: 0%">계획중</div>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## 7️⃣ 재직 60일 미만 (Under 60 Days) 모달

### 모달 제목
```
한국어: "재직 60일 미만 직원 분석"
English: "Employees Under 60 Days - Analysis"
Vietnamese: "Phân tích nhân viên dưới 60 ngày"
```

### 섹션 1: 현황 요약
```html
<div class="modal-stat-grid">
    <div class="stat-card">
        <div class="stat-icon">👶</div>
        <div class="stat-label">60일 미만 재직자 / Under 60 Days</div>
        <div class="stat-value">45명</div>
        <div class="stat-sublabel">전체의 11.5%</div>
    </div>

    <div class="stat-card warning">
        <div class="stat-icon">⚠️</div>
        <div class="stat-label">조기 이탈 위험군 / At-Risk</div>
        <div class="stat-value">5명</div>
        <div class="stat-sublabel">11.1% 위험</div>
    </div>

    <div class="stat-card success">
        <div class="stat-icon">✅</div>
        <div class="stat-label">온보딩 완료율 / Onboarding Rate</div>
        <div class="stat-value">82.2%</div>
        <div class="stat-sublabel">37/45명 완료</div>
    </div>
</div>
```

### 섹션 2: 재직일수 분포
```html
<div class="tenure-days-distribution">
    <h6>재직일수 분포 / Days Distribution</h6>

    <canvas id="tenureDaysHistogram"></canvas>

    <div class="distribution-stats">
        <div class="stat-box">
            <span class="stat-label">평균 재직일수</span>
            <span class="stat-value">32일</span>
        </div>
        <div class="stat-box">
            <span class="stat-label">중앙값</span>
            <span class="stat-value">28일</span>
        </div>
        <div class="stat-box">
            <span class="stat-label">최소/최대</span>
            <span class="stat-value">5일 / 59일</span>
        </div>
    </div>
</div>
```

### 섹션 3: 온보딩 진행 현황
```html
<div class="onboarding-pipeline">
    <h6>온보딩 단계별 현황 / Onboarding Pipeline Status</h6>

    <div class="pipeline-visualization">
        <div class="pipeline-stage">
            <div class="stage-header">
                <span class="stage-name">입사 등록</span>
                <span class="stage-count">45/45</span>
            </div>
            <div class="stage-bar">
                <div class="bar-fill bg-success" style="width: 100%">100%</div>
            </div>
        </div>

        <div class="pipeline-stage">
            <div class="stage-header">
                <span class="stage-name">오리엔테이션</span>
                <span class="stage-count">43/45</span>
            </div>
            <div class="stage-bar">
                <div class="bar-fill bg-success" style="width: 95.6%">95.6%</div>
            </div>
        </div>

        <div class="pipeline-stage">
            <div class="stage-header">
                <span class="stage-name">직무 교육</span>
                <span class="stage-count">37/45</span>
            </div>
            <div class="stage-bar">
                <div class="bar-fill bg-warning" style="width: 82.2%">82.2%</div>
            </div>
        </div>

        <div class="pipeline-stage">
            <div class="stage-header">
                <span class="stage-name">OJT</span>
                <span class="stage-count">25/45</span>
            </div>
            <div class="stage-bar">
                <div class="bar-fill bg-warning" style="width: 55.6%">55.6%</div>
            </div>
        </div>

        <div class="pipeline-stage">
            <div class="stage-header">
                <span class="stage-name">평가 완료</span>
                <span class="stage-count">8/45</span>
            </div>
            <div class="stage-bar">
                <div class="bar-fill bg-danger" style="width: 17.8%">17.8%</div>
            </div>
        </div>
    </div>

    <div class="alert alert-info mt-3">
        <strong>ℹ️ 지연 안내</strong>
        <p>8명이 오리엔테이션 미완료 상태 - HR팀 확인 필요</p>
    </div>
</div>
```

### 섹션 4: 조기 이탈 위험 분석
```html
<div class="early-exit-risk-analysis">
    <h6>⚠️ 조기 이탈 위험 분석 / Early Exit Risk Analysis</h6>

    <div class="risk-model-explanation">
        <div class="alert alert-info">
            <strong>🔍 위험도 산출 모델</strong>
            <ul>
                <li>출근율 (30%) - 95% 미만 시 감점</li>
                <li>교육 참여도 (25%) - 참석률 80% 미만 시 감점</li>
                <li>멘토 피드백 (25%) - 부정적 피드백 시 감점</li>
                <li>무단결근 여부 (20%) - 1회당 20점 감점</li>
            </ul>
        </div>
    </div>

    <div class="risk-distribution">
        <canvas id="riskScoreDistribution"></canvas>
    </div>

    <div class="high-risk-employees">
        <h6>고위험군 직원 (5명) / High-Risk Employees (5)</h6>

        <table class="table table-sm table-hover">
            <thead>
                <tr>
                    <th>사번</th>
                    <th>이름</th>
                    <th>팀</th>
                    <th>재직일수</th>
                    <th>위험점수</th>
                    <th>출근율</th>
                    <th>교육 참여</th>
                    <th>멘토 피드백</th>
                    <th>액션</th>
                </tr>
            </thead>
            <tbody>
                <tr class="table-danger">
                    <td>E12345</td>
                    <td>홍길동</td>
                    <td>Team B</td>
                    <td>35일</td>
                    <td>
                        <span class="badge bg-danger">75점</span>
                    </td>
                    <td class="text-danger">88%</td>
                    <td class="text-warning">75%</td>
                    <td class="text-danger">의욕 저하</td>
                    <td>
                        <button class="btn btn-sm btn-danger"
                                onclick="scheduleIntervention('E12345')">
                            긴급 면담
                        </button>
                    </td>
                </tr>
                <!-- More high-risk employees... -->
            </tbody>
        </table>
    </div>

    <div class="intervention-timeline">
        <h6>개입 조치 이력 / Intervention History</h6>
        <div class="timeline">
            <div class="timeline-item">
                <div class="timeline-date">2025-09-25</div>
                <div class="timeline-badge bg-warning">면담</div>
                <div class="timeline-content">
                    <strong>E12345 홍길동</strong> - 팀장 1:1 면담 진행
                    <br><small>참석 독려 및 애로사항 청취</small>
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-date">2025-09-20</div>
                <div class="timeline-badge bg-info">알림</div>
                <div class="timeline-content">
                    <strong>3명</strong> - 출근율 경고 문자 발송
                </div>
            </div>
        </div>
    </div>
</div>
```

### 섹션 5: 전체 명단
```html
<div class="under-60-days-list">
    <h6>전체 명단 (45명) / Full List (45)</h6>

    <div class="table-controls mb-3">
        <div class="row">
            <div class="col-md-4">
                <input type="text" class="form-control form-control-sm"
                       placeholder="검색..."
                       onkeyup="filterUnder60Table(this.value)">
            </div>
            <div class="col-md-3">
                <select class="form-select form-select-sm"
                        onchange="filterByRisk(this.value)">
                    <option value="">전체 위험도</option>
                    <option value="high">높음</option>
                    <option value="medium">보통</option>
                    <option value="low">낮음</option>
                </select>
            </div>
            <div class="col-md-3">
                <select class="form-select form-select-sm"
                        onchange="filterByOnboarding(this.value)">
                    <option value="">전체 온보딩 상태</option>
                    <option value="completed">완료</option>
                    <option value="in-progress">진행중</option>
                    <option value="delayed">지연</option>
                </select>
            </div>
        </div>
    </div>

    <div class="table-responsive">
        <table class="table table-sm table-hover" id="under60Table">
            <thead class="sticky-header">
                <tr>
                    <th>사번</th>
                    <th>이름</th>
                    <th>직급</th>
                    <th>팀</th>
                    <th>입사일</th>
                    <th>재직일수</th>
                    <th>온보딩</th>
                    <th>위험도</th>
                    <th>멘토</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>E12345</td>
                    <td>홍길동</td>
                    <td>A.INSPECTOR</td>
                    <td>Team A</td>
                    <td>2025-08-20</td>
                    <td>40일</td>
                    <td>
                        <span class="badge bg-success">완료</span>
                    </td>
                    <td>
                        <span class="badge bg-success">낮음</span>
                    </td>
                    <td>김멘토</td>
                </tr>
                <!-- More rows... -->
            </tbody>
        </table>
    </div>
</div>
```

---

## 8️⃣ 배정 후 퇴사자 (Post-Assignment Resignations) 모달

### 모달 제목
```
한국어: "배정 후 퇴사자 분석"
English: "Post-Assignment Resignations - Analysis"
Vietnamese: "Phân tích nghỉ việc sau phân công"
```

### 섹션 1: 현황 요약
```html
<div class="modal-stat-grid">
    <div class="stat-card alert-danger">
        <div class="stat-icon">📤</div>
        <div class="stat-label">배정 후 퇴사자 / Post-Assignment</div>
        <div class="stat-value">92명</div>
        <div class="stat-sublabel">누적 (7-9월)</div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">⏱️</div>
        <div class="stat-label">평균 배정~퇴사 / Avg Days</div>
        <div class="stat-value">45일</div>
        <div class="stat-sublabel">1.5개월</div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">💸</div>
        <div class="stat-label">손실 비용 추정 / Est. Loss</div>
        <div class="stat-value">$276,000</div>
        <div class="stat-sublabel">92명 × $3,000</div>
    </div>
</div>
```

### 섹션 2: 월별 추세
```javascript
const postAssignmentTrendData = {
    labels: ['7월', '8월', '9월'],
    datasets: [
        {
            label: '배정 후 퇴사자',
            data: [32, 34, 26],
            backgroundColor: 'rgba(239, 68, 68, 0.7)',
            borderColor: '#ef4444',
            borderWidth: 2
        }
    ]
};
```

### 섹션 3: 배정~퇴사 기간 분포
```html
<div class="assignment-to-resignation-period">
    <h6>배정 후 퇴사까지 기간 분포 / Days from Assignment to Resignation</h6>

    <canvas id="assignmentPeriodHistogram"></canvas>

    <div class="period-insights">
        <div class="insight-card danger">
            <div class="insight-icon">🚨</div>
            <div class="insight-title">즉시 이탈 (1-7일)</div>
            <div class="insight-value">15명 (16.3%)</div>
            <div class="insight-desc">
                배정 직후 즉시 퇴사 - 배정 프로세스 문제 의심
            </div>
        </div>

        <div class="insight-card warning">
            <div class="insight-icon">⚠️</div>
            <div class="insight-title">조기 이탈 (8-30일)</div>
            <div class="insight-value">42명 (45.7%)</div>
            <div class="insight-desc">
                1개월 내 이탈 - 업무 적응 지원 필요
            </div>
        </div>

        <div class="insight-card info">
            <div class="insight-icon">📊</div>
            <div class="insight-title">중기 이탈 (31-60일)</div>
            <div class="insight-value">25명 (27.2%)</div>
            <div class="insight-desc">
                2개월 내 이탈 - 업무 난이도 또는 환경 문제
            </div>
        </div>

        <div class="insight-card success">
            <div class="insight-icon">✓</div>
            <div class="insight-title">장기 근무 후 이탈 (60일+)</div>
            <div class="insight-value">10명 (10.9%)</div>
            <div class="insight-desc">
                2개월 이상 근무 - 일반적인 퇴사
            </div>
        </div>
    </div>
</div>
```

### 섹션 4: 직급별 배정 후 퇴사 분석
```html
<div class="position-assignment-analysis">
    <h6>직급별 배정 후 퇴사 현황 / Position-wise Post-Assignment Resignations</h6>

    <table class="table">
        <thead>
            <tr>
                <th>직급 / Position</th>
                <th>배정 인원 / Assigned</th>
                <th>퇴사 인원 / Resigned</th>
                <th>퇴사율 / Rate</th>
                <th>평균 기간 / Avg Days</th>
                <th>상태 / Status</th>
            </tr>
        </thead>
        <tbody>
            <tr class="table-danger">
                <td><span class="badge bg-primary">A.INSPECTOR</span></td>
                <td>180명</td>
                <td>52명</td>
                <td>
                    <strong class="text-danger">28.9%</strong>
                </td>
                <td>42일</td>
                <td>
                    <span class="badge bg-danger">높음</span>
                </td>
            </tr>
            <tr class="table-warning">
                <td><span class="badge bg-info">LINE LEADER</span></td>
                <td>85명</td>
                <td>25명</td>
                <td>
                    <strong class="text-warning">29.4%</strong>
                </td>
                <td>38일</td>
                <td>
                    <span class="badge bg-warning">주의</span>
                </td>
            </tr>
            <tr>
                <td><span class="badge bg-secondary">A.MANAGER</span></td>
                <td>45명</td>
                <td>8명</td>
                <td>17.8%</td>
                <td>58일</td>
                <td>
                    <span class="badge bg-success">양호</span>
                </td>
            </tr>
            <!-- More positions... -->
        </tbody>
    </table>

    <div class="alert alert-danger">
        <strong>🚨 A.INSPECTOR 및 LINE LEADER 배정 후 퇴사율 심각</strong>
        <p>양 직급 모두 약 29%의 높은 배정 후 퇴사율 기록</p>
        <p>업무 난이도, 교육 체계, 근무 환경 전반적 재검토 필요</p>
    </div>
</div>
```

### 섹션 5: 상세 명단
```html
<div class="post-assignment-resignees-list">
    <h6>배정 후 퇴사자 상세 명단 (92명) / Detailed List (92)</h6>

    <div class="table-responsive">
        <table class="table table-sm table-hover">
            <thead class="sticky-header">
                <tr>
                    <th>사번</th>
                    <th>이름</th>
                    <th>직급</th>
                    <th>팀</th>
                    <th>배정일</th>
                    <th>퇴사일</th>
                    <th>배정~퇴사</th>
                    <th>퇴사 사유</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>E12345</td>
                    <td>홍길동</td>
                    <td>A.INSPECTOR</td>
                    <td>Team A</td>
                    <td>2025-08-01</td>
                    <td>2025-08-05</td>
                    <td>
                        <span class="badge bg-danger">4일</span>
                    </td>
                    <td>업무 부적응</td>
                </tr>
                <!-- More rows... -->
            </tbody>
        </table>
    </div>
</div>
```

---

## 9️⃣ 개근 직원 (Perfect Attendance) 모달

### 모달 제목
```
한국어: "개근 직원 분석"
English: "Perfect Attendance - Analysis"
Vietnamese: "Phân tích chuyên cần hoàn hảo"
```

### 섹션 1: 현황 요약
```html
<div class="modal-stat-grid">
    <div class="stat-card success">
        <div class="stat-icon">🎉</div>
        <div class="stat-label">9월 개근자 / Perfect (Sep)</div>
        <div class="stat-value">350명</div>
        <div class="stat-sublabel">전체의 89.1%</div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">🏆</div>
        <div class="stat-label">연속 개근 (3개월) / Consecutive 3M</div>
        <div class="stat-value">285명</div>
        <div class="stat-sublabel">81.4% 유지</div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-label">포상 대상 / Award Eligible</div>
        <div class="stat-value">285명</div>
        <div class="stat-sublabel">3개월 연속</div>
    </div>
</div>
```

### 섹션 2: 월별 개근률 추세
```javascript
const perfectAttendanceTrendData = {
    labels: ['7월', '8월', '9월'],
    datasets: [
        {
            label: '개근률 (%)',
            data: [87.5, 88.2, 89.1],
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.4,
            fill: true
        },
        {
            label: '목표 (90%)',
            data: [90, 90, 90],
            borderColor: '#667eea',
            borderDash: [5, 5],
            borderWidth: 2,
            pointRadius: 0
        }
    ]
};
```

### 섹션 3: 연속 개근 현황
```html
<div class="consecutive-attendance">
    <h6>연속 개근 현황 / Consecutive Perfect Attendance</h6>

    <div class="consecutive-grid">
        <div class="consecutive-card gold">
            <div class="card-icon">🥇</div>
            <div class="card-title">12개월 연속</div>
            <div class="card-count">15명</div>
            <div class="card-reward">특별 포상 대상</div>
        </div>

        <div class="consecutive-card silver">
            <div class="card-icon">🥈</div>
            <div class="card-title">6개월 연속</div>
            <div class="card-count">42명</div>
            <div class="card-reward">우수 포상 대상</div>
        </div>

        <div class="consecutive-card bronze">
            <div class="card-icon">🥉</div>
            <div class="card-title">3개월 연속</div>
            <div class="card-count">228명</div>
            <div class="card-reward">일반 포상 대상</div>
        </div>

        <div class="consecutive-card">
            <div class="card-icon">✓</div>
            <div class="card-title">이번 달만</div>
            <div class="card-count">65명</div>
            <div class="card-reward">격려</div>
        </div>
    </div>
</div>
```

### 섹션 4: 팀별 개근률 비교
```html
<div class="team-attendance-comparison">
    <h6>팀별 개근률 비교 (9월) / Team Comparison (Sep)</h6>

    <div class="team-comparison-bars">
        <div class="team-bar-row">
            <div class="team-label">Team A</div>
            <div class="team-bar-wrapper">
                <div class="team-bar bg-success" style="width: 95%">
                    <span>95.1%</span>
                </div>
            </div>
            <div class="team-stats">
                <span>135/142명</span>
                <span class="badge bg-success">최우수</span>
            </div>
        </div>

        <div class="team-bar-row">
            <div class="team-label">Team B</div>
            <div class="team-bar-wrapper">
                <div class="team-bar bg-warning" style="width: 85%">
                    <span>85.2%</span>
                </div>
            </div>
            <div class="team-stats">
                <span>92/108명</span>
                <span class="badge bg-warning">개선 필요</span>
            </div>
        </div>

        <div class="team-bar-row">
            <div class="team-label">Team C</div>
            <div class="team-bar-wrapper">
                <div class="team-bar bg-success" style="width: 90%">
                    <span>90.5%</span>
                </div>
            </div>
            <div class="team-stats">
                <span>86/95명</span>
                <span class="badge bg-info">우수</span>
            </div>
        </div>
    </div>
</div>
```

### 섹션 5: 개근자 명단
```html
<div class="perfect-attendance-list">
    <h6>9월 개근자 명단 (350명) / Perfect Attendance List (350)</h6>

    <div class="table-controls mb-3">
        <div class="row">
            <div class="col-md-4">
                <input type="text" class="form-control form-control-sm"
                       placeholder="검색..."
                       onkeyup="filterPerfectTable(this.value)">
            </div>
            <div class="col-md-3">
                <select class="form-select form-select-sm"
                        onchange="filterByConsecutive(this.value)">
                    <option value="">전체 연속 개근</option>
                    <option value="12m">12개월 연속</option>
                    <option value="6m">6개월 연속</option>
                    <option value="3m">3개월 연속</option>
                    <option value="1m">이번 달만</option>
                </select>
            </div>
            <div class="col-md-3">
                <select class="form-select form-select-sm"
                        onchange="filterByAward(this.value)">
                    <option value="">전체 포상</option>
                    <option value="special">특별 포상</option>
                    <option value="excellent">우수 포상</option>
                    <option value="general">일반 포상</option>
                </select>
            </div>
            <div class="col-md-2">
                <button class="btn btn-sm btn-success w-100"
                        onclick="exportAwardList()">
                    <i class="bi bi-trophy"></i> 포상 명단
                </button>
            </div>
        </div>
    </div>

    <div class="table-responsive">
        <table class="table table-sm table-hover" id="perfectTable">
            <thead class="sticky-header">
                <tr>
                    <th>사번</th>
                    <th>이름</th>
                    <th>직급</th>
                    <th>팀</th>
                    <th>연속 개근</th>
                    <th>포상 등급</th>
                    <th>포상 금액</th>
                </tr>
            </thead>
            <tbody>
                <tr class="table-warning">
                    <td>E12345</td>
                    <td>홍길동</td>
                    <td>A.INSPECTOR</td>
                    <td>Team A</td>
                    <td>
                        <span class="badge bg-warning">12개월</span>
                    </td>
                    <td>
                        <span class="badge bg-warning">🥇 특별</span>
                    </td>
                    <td>
                        <strong>$500</strong>
                    </td>
                </tr>
                <!-- More rows... -->
            </tbody>
        </table>
    </div>

    <div class="award-summary mt-3">
        <div class="alert alert-success">
            <strong>💰 총 포상 금액 추정</strong>
            <ul>
                <li>특별 포상 (12개월): 15명 × $500 = $7,500</li>
                <li>우수 포상 (6개월): 42명 × $300 = $12,600</li>
                <li>일반 포상 (3개월): 228명 × $100 = $22,800</li>
                <li><strong>총계: $42,900</strong></li>
            </ul>
        </div>
    </div>
</div>
```

---

## 🔟 장기근속자 (Long-term Employees) 모달

*(계속...)*

**파일이 매우 길어졌습니다. 다음 파일로 계속 작성하시겠습니까?**
- 10번: 장기근속자
- 11번: 데이터 오류
- 공통 CSS 스타일
- 공통 JavaScript 함수

다음 단계로 진행할까요?
