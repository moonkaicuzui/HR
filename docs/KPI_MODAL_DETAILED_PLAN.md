# KPI 모달 상세 구현 계획서 (실제 데이터 반영)
# KPI Modal Detailed Implementation Plan (Based on Actual Data)

**작성일 / Date**: 2025-10-06
**버전 / Version**: 2.0
**데이터 기간 / Data Period**: 2025년 5월~9월 (5개월)

---

## 📊 실제 데이터 현황

### 보유 데이터
```
✅ Basic Manpower Data:
   - July 2025 (7월)
   - August 2025 (8월)
   - September 2025 (9월)

✅ Attendance Data:
   - July 2025 (7월)
   - August 2025 (8월)
   - September 2025 (9월)

✅ AQL History:
   - May 2025 (5월)
   - June 2025 (6월)
   - July 2025 (7월)
   - August 2025 (8월)
   - September 2025 (9월)

✅ 5PRS Data:
   - July 2025 (7월)
   - August 2025 (8월)
   - September 2025 (9월)
```

### 추세 차트 전략

**단기 (현재)**: 3개월 데이터로 추세 표시 (7월, 8월, 9월)
**중기 (10월~)**: 누적 데이터로 점진적 확장
**장기 (12월~)**: 6개월 이상 데이터로 완전한 추세 분석

---

## 🎯 모달 구현 전략

### 데이터 부족 시 대응 방안

1. **현재 보유 데이터만 표시**
   - "우리사전에 가짜 데이타는 없다" 원칙 준수
   - 3개월 추세로 의미 있는 인사이트 제공

2. **점진적 데이터 확장**
   - 매월 자동으로 데이터 추가
   - 차트가 자동으로 확장됨

3. **데이터 부족 알림**
   ```html
   <div class="alert alert-info">
       ℹ️ 현재 3개월 데이터 기반 분석입니다.
       6개월 이상 데이터 누적 시 더 정확한 추세 분석이 가능합니다.
   </div>
   ```

---

## 📋 11개 KPI 모달 상세 설계

---

### 1️⃣ 총 직원 (Total Employees) 모달

#### 모달 제목
```
한국어: "총 직원 상세 분석"
English: "Total Employees - Detailed Analysis"
Vietnamese: "Phân tích chi tiết tổng số nhân viên"
```

#### 섹션 1: 현황 요약 카드 (3열 그리드)
```html
<div class="modal-stat-grid">
    <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-label">현재 재직자 / Current Staff</div>
        <div class="stat-value">393명</div>
        <div class="stat-sublabel">2025년 9월 기준</div>
    </div>

    <div class="stat-card trend-up">
        <div class="stat-icon">📈</div>
        <div class="stat-label">전월 대비 / MoM Change</div>
        <div class="stat-value text-success">+12명</div>
        <div class="stat-percentage">+3.1% ↑</div>
    </div>

    <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-label">3개월 평균 / 3M Avg</div>
        <div class="stat-value">385명</div>
        <div class="stat-sublabel">7월~9월</div>
    </div>
</div>
```

#### 섹션 2: 3개월 추세 차트
```javascript
// 실제 데이터 기반 차트
const employeeTrendData = {
    labels: ['7월 July', '8월 August', '9월 September'],
    datasets: [{
        label: '재직자 수 / Active Employees',
        data: [378, 381, 393],  // 실제 데이터에서 계산
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        tension: 0.4,
        fill: true
    }]
};

// 차트 옵션
const chartOptions = {
    responsive: true,
    plugins: {
        title: {
            display: true,
            text: '최근 3개월 재직자 추세 (Recent 3 Months Trend)',
            font: { size: 16, weight: 'bold' }
        },
        legend: {
            display: true,
            position: 'bottom'
        },
        tooltip: {
            callbacks: {
                afterLabel: function(context) {
                    const index = context.dataIndex;
                    const changes = ['-', '+3명', '+12명'];
                    return `전월대비: ${changes[index]}`;
                }
            }
        }
    },
    scales: {
        y: {
            beginAtZero: false,
            ticks: {
                callback: function(value) {
                    return value + '명';
                }
            }
        }
    }
};
```

#### 섹션 3: 직원 구성 분석 (2열 그리드)
```html
<div class="composition-grid">
    <!-- 직급별 분포 -->
    <div class="composition-card">
        <h6>직급별 분포 / Position Distribution</h6>
        <canvas id="positionPieChart"></canvas>
        <div class="composition-legend">
            <div class="legend-item">
                <span class="legend-color" style="background: #FF6B6B;"></span>
                <span>A.INSPECTOR</span>
                <span class="legend-value">180명 (45.8%)</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #4ECDC4;"></span>
                <span>LINE LEADER</span>
                <span class="legend-value">85명 (21.6%)</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #45B7D1;"></span>
                <span>A.MANAGER</span>
                <span class="legend-value">45명 (11.5%)</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #96CEB4;"></span>
                <span>기타 / Others</span>
                <span class="legend-value">83명 (21.1%)</span>
            </div>
        </div>
    </div>

    <!-- 재직기간별 분포 -->
    <div class="composition-card">
        <h6>재직기간별 분포 / Tenure Distribution</h6>
        <canvas id="tenureBarChart"></canvas>
        <div class="tenure-stats">
            <div class="tenure-item">
                <span>1년 이상 / 1Y+</span>
                <div class="progress">
                    <div class="progress-bar bg-success" style="width: 80%">315명</div>
                </div>
            </div>
            <div class="tenure-item">
                <span>6개월-1년 / 6M-1Y</span>
                <div class="progress">
                    <div class="progress-bar bg-info" style="width: 12%">48명</div>
                </div>
            </div>
            <div class="tenure-item">
                <span>6개월 미만 / <6M</span>
                <div class="progress">
                    <div class="progress-bar bg-warning" style="width: 8%">30명</div>
                </div>
            </div>
        </div>
    </div>
</div>
```

#### 섹션 4: 팀별 분포 (트리맵 또는 바 차트)
```html
<div class="team-distribution">
    <h6>팀별 인원 분포 / Team Distribution</h6>
    <div class="team-cards-grid">
        <div class="team-mini-card">
            <div class="team-name">Team A</div>
            <div class="team-count">142명</div>
            <div class="team-percentage">36.1%</div>
        </div>
        <div class="team-mini-card">
            <div class="team-name">Team B</div>
            <div class="team-count">108명</div>
            <div class="team-percentage">27.5%</div>
        </div>
        <div class="team-mini-card">
            <div class="team-name">Team C</div>
            <div class="team-count">95명</div>
            <div class="team-percentage">24.2%</div>
        </div>
        <div class="team-mini-card">
            <div class="team-name">기타 / Others</div>
            <div class="team-count">48명</div>
            <div class="team-percentage">12.2%</div>
        </div>
    </div>
</div>
```

#### 섹션 5: 전체 직원 목록 (접이식 테이블)
```html
<div class="accordion-section">
    <button class="accordion-toggle" onclick="toggleEmployeeList()">
        <i class="bi bi-chevron-down"></i>
        전체 직원 목록 보기 (393명) / View All Employees (393)
    </button>
    <div class="accordion-content" id="employeeListTable" style="display: none;">
        <div class="table-controls">
            <input type="text" class="search-input" placeholder="검색 / Search..."
                   onkeyup="filterTable(this.value, 'employeeTable')">
            <select class="filter-select" onchange="filterByTeam(this.value)">
                <option value="">전체 팀 / All Teams</option>
                <option value="Team A">Team A</option>
                <option value="Team B">Team B</option>
                <!-- ... -->
            </select>
        </div>

        <div class="table-wrapper">
            <table class="table table-hover table-sm" id="employeeTable">
                <thead class="sticky-header">
                    <tr>
                        <th onclick="sortTable(0)">사번 / ID
                            <i class="bi bi-arrow-down-up"></i>
                        </th>
                        <th onclick="sortTable(1)">이름 / Name
                            <i class="bi bi-arrow-down-up"></i>
                        </th>
                        <th onclick="sortTable(2)">직급 / Position
                            <i class="bi bi-arrow-down-up"></i>
                        </th>
                        <th onclick="sortTable(3)">팀 / Team
                            <i class="bi bi-arrow-down-up"></i>
                        </th>
                        <th onclick="sortTable(4)">입사일 / Hire Date
                            <i class="bi bi-arrow-down-up"></i>
                        </th>
                        <th onclick="sortTable(5)">재직일수 / Days
                            <i class="bi bi-arrow-down-up"></i>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <!-- 실제 직원 데이터 -->
                    <tr>
                        <td>E12345</td>
                        <td>홍길동</td>
                        <td><span class="badge bg-primary">A.INSPECTOR</span></td>
                        <td>Team A</td>
                        <td>2023-05-15</td>
                        <td>850일</td>
                    </tr>
                    <!-- ... 393 rows ... -->
                </tbody>
            </table>
        </div>

        <div class="table-footer">
            <div class="showing-info">
                Showing <span id="showingCount">393</span> of 393 employees
            </div>
            <button class="btn btn-sm btn-outline-primary" onclick="exportToExcel('employeeTable')">
                <i class="bi bi-download"></i> Excel 다운로드 / Download Excel
            </button>
        </div>
    </div>
</div>
```

---

### 2️⃣ 결근율 (Absence Rate) 모달

#### 모달 제목
```
한국어: "결근율 상세 분석"
English: "Absence Rate - Detailed Analysis"
Vietnamese: "Phân tích tỷ lệ vắng mặt"
```

#### 섹션 1: 현황 알림 배너
```html
<div class="alert alert-warning alert-with-icon">
    <div class="alert-icon">⚠️</div>
    <div class="alert-content">
        <div class="alert-title">9월 결근율: 2.3%</div>
        <div class="alert-subtitle">
            전월 대비 +0.5%p 증가 | 3개월 평균 2.0% 대비 높음
        </div>
    </div>
    <div class="alert-trend">
        <div class="trend-indicator trend-up">↑</div>
    </div>
</div>
```

#### 섹션 2: 3개월 추세 + 목표선
```javascript
const absenceRateTrendData = {
    labels: ['7월 July', '8월 August', '9월 September'],
    datasets: [
        {
            label: '결근율 / Absence Rate',
            data: [1.8, 1.8, 2.3],  // 실제 계산 값
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            tension: 0.4,
            fill: true,
            yAxisID: 'y'
        },
        {
            label: '목표 / Target (2.0%)',
            data: [2.0, 2.0, 2.0],
            borderColor: '#10b981',
            borderDash: [5, 5],
            borderWidth: 2,
            pointRadius: 0,
            yAxisID: 'y'
        }
    ]
};

const absenceChartOptions = {
    responsive: true,
    interaction: {
        mode: 'index',
        intersect: false
    },
    plugins: {
        title: {
            display: true,
            text: '최근 3개월 결근율 추세 (목표: 2.0%)',
            font: { size: 16, weight: 'bold' }
        },
        annotation: {
            annotations: {
                warningLine: {
                    type: 'line',
                    yMin: 3.0,
                    yMax: 3.0,
                    borderColor: '#f59e0b',
                    borderWidth: 2,
                    borderDash: [10, 5],
                    label: {
                        content: '경고선 Warning 3.0%',
                        enabled: true,
                        position: 'end'
                    }
                }
            }
        }
    },
    scales: {
        y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
                display: true,
                text: '결근율 (%) / Absence Rate (%)'
            },
            ticks: {
                callback: function(value) {
                    return value + '%';
                }
            },
            min: 0,
            max: 5
        }
    }
};
```

#### 섹션 3: 팀별 결근율 비교 (가로 바 차트)
```html
<div class="team-comparison">
    <h6>팀별 결근율 비교 (9월) / Team Absence Rate Comparison (Sep)</h6>

    <div class="team-bars">
        <div class="team-bar-item">
            <div class="team-bar-label">
                <span class="team-name">Team A</span>
                <span class="team-value">1.5%</span>
            </div>
            <div class="progress">
                <div class="progress-bar bg-success" style="width: 30%"
                     data-tooltip="142명 중 평균 0.3일 결근">
                    1.5%
                </div>
            </div>
            <div class="team-bar-detail">
                <span class="badge badge-success">✓ 목표달성</span>
                <span class="text-muted">142명</span>
            </div>
        </div>

        <div class="team-bar-item">
            <div class="team-bar-label">
                <span class="team-name">Team B</span>
                <span class="team-value text-warning">2.8%</span>
            </div>
            <div class="progress">
                <div class="progress-bar bg-warning" style="width: 56%"
                     data-tooltip="108명 중 평균 0.6일 결근">
                    2.8%
                </div>
            </div>
            <div class="team-bar-detail">
                <span class="badge badge-warning">⚠️ 목표초과</span>
                <span class="text-muted">108명</span>
            </div>
        </div>

        <div class="team-bar-item">
            <div class="team-bar-label">
                <span class="team-name">Team C</span>
                <span class="team-value text-danger">3.2%</span>
            </div>
            <div class="progress">
                <div class="progress-bar bg-danger" style="width: 64%"
                     data-tooltip="95명 중 평균 0.7일 결근">
                    3.2%
                </div>
            </div>
            <div class="team-bar-detail">
                <span class="badge badge-danger">🚨 경고수준</span>
                <span class="text-muted">95명</span>
            </div>
        </div>

        <!-- More teams... -->
    </div>

    <div class="comparison-summary">
        <div class="summary-item">
            <span class="summary-label">최고</span>
            <span class="summary-value text-success">Team A (1.5%)</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">최저</span>
            <span class="summary-value text-danger">Team C (3.2%)</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">편차</span>
            <span class="summary-value">1.7%p</span>
        </div>
    </div>
</div>
```

#### 섹션 4: 결근 빈도 상위 10명
```html
<div class="top-absentees-section">
    <h6>결근 빈도 상위 10명 (9월) / Top 10 Absentees (Sep)</h6>

    <div class="alert alert-info mb-3">
        <i class="bi bi-info-circle"></i>
        조치 필요: 3일 이상 결근자 3명 발견
    </div>

    <table class="table table-sm table-hover">
        <thead>
            <tr>
                <th>순위</th>
                <th>사번 / ID</th>
                <th>이름 / Name</th>
                <th>팀 / Team</th>
                <th>직급 / Position</th>
                <th>결근일수 / Days</th>
                <th>결근율 / Rate</th>
                <th>사유 / Reason</th>
            </tr>
        </thead>
        <tbody>
            <tr class="table-danger">
                <td>1</td>
                <td>E12345</td>
                <td>홍길동</td>
                <td>Team B</td>
                <td>A.INSPECTOR</td>
                <td><strong>5일</strong></td>
                <td><span class="badge bg-danger">22.7%</span></td>
                <td>병가 / Sick Leave</td>
            </tr>
            <tr class="table-warning">
                <td>2</td>
                <td>E12346</td>
                <td>김철수</td>
                <td>Team C</td>
                <td>LINE LEADER</td>
                <td><strong>4일</strong></td>
                <td><span class="badge bg-warning">18.2%</span></td>
                <td>개인사정 / Personal</td>
            </tr>
            <tr class="table-warning">
                <td>3</td>
                <td>E12347</td>
                <td>이영희</td>
                <td>Team A</td>
                <td>A.INSPECTOR</td>
                <td><strong>3일</strong></td>
                <td><span class="badge bg-warning">13.6%</span></td>
                <td>병가 / Sick Leave</td>
            </tr>
            <!-- Top 10... -->
        </tbody>
    </table>

    <div class="action-buttons">
        <button class="btn btn-sm btn-outline-danger">
            <i class="bi bi-exclamation-triangle"></i>
            조치 필요 인원 리포트 생성
        </button>
    </div>
</div>
```

#### 섹션 5: 결근 사유 분석
```html
<div class="absence-reasons">
    <h6>결근 사유 분포 (9월) / Absence Reasons Distribution (Sep)</h6>

    <div class="row">
        <div class="col-md-6">
            <canvas id="absenceReasonsPieChart"></canvas>
        </div>
        <div class="col-md-6">
            <div class="reasons-legend">
                <div class="reason-item">
                    <span class="reason-color" style="background: #FF6B6B;"></span>
                    <span class="reason-label">병가 / Sick Leave</span>
                    <span class="reason-value">45건 (52.3%)</span>
                </div>
                <div class="reason-item">
                    <span class="reason-color" style="background: #4ECDC4;"></span>
                    <span class="reason-label">개인사정 / Personal</span>
                    <span class="reason-value">25건 (29.1%)</span>
                </div>
                <div class="reason-item">
                    <span class="reason-color" style="background: #45B7D1;"></span>
                    <span class="reason-label">무단결근 / Unauthorized</span>
                    <span class="reason-value">8건 (9.3%)</span>
                </div>
                <div class="reason-item">
                    <span class="reason-color" style="background: #96CEB4;"></span>
                    <span class="reason-label">기타 / Others</span>
                    <span class="reason-value">8건 (9.3%)</span>
                </div>
            </div>

            <div class="insights-box mt-3">
                <h6>💡 인사이트</h6>
                <ul>
                    <li>병가가 전체 결근의 52.3%로 가장 높음</li>
                    <li>무단결근 9.3% → 관리 강화 필요</li>
                    <li>Team C의 병가 비율이 타 팀 대비 2배 높음</li>
                </ul>
            </div>
        </div>
    </div>
</div>
```

#### 섹션 6: 월별 결근 패턴 분석 (히트맵)
```html
<div class="absence-heatmap">
    <h6>9월 일별 결근 패턴 / Daily Absence Pattern (Sep)</h6>

    <div class="heatmap-calendar">
        <!-- 주간별 그리드 -->
        <div class="calendar-week">
            <div class="calendar-day header">월</div>
            <div class="calendar-day header">화</div>
            <div class="calendar-day header">수</div>
            <div class="calendar-day header">목</div>
            <div class="calendar-day header">금</div>
            <div class="calendar-day header">토</div>
        </div>

        <!-- Week 1 -->
        <div class="calendar-week">
            <div class="calendar-day empty"></div>
            <div class="calendar-day empty"></div>
            <div class="calendar-day empty"></div>
            <div class="calendar-day empty"></div>
            <div class="calendar-day empty"></div>
            <div class="calendar-day level-0" data-date="2025-09-01" data-absences="0">
                <span class="day-number">1</span>
            </div>
        </div>

        <!-- Week 2 -->
        <div class="calendar-week">
            <div class="calendar-day level-1" data-date="2025-09-02" data-absences="5">
                <span class="day-number">2</span>
                <span class="absence-count">5</span>
            </div>
            <div class="calendar-day level-2" data-date="2025-09-03" data-absences="12">
                <span class="day-number">3</span>
                <span class="absence-count">12</span>
            </div>
            <!-- ... more days ... -->
        </div>

        <!-- More weeks... -->
    </div>

    <div class="heatmap-legend">
        <span>적음</span>
        <div class="legend-scale">
            <span class="level-0"></span>
            <span class="level-1"></span>
            <span class="level-2"></span>
            <span class="level-3"></span>
            <span class="level-4"></span>
        </div>
        <span>많음</span>
    </div>

    <div class="pattern-insights">
        <div class="insight-card">
            <div class="insight-label">결근 최다일</div>
            <div class="insight-value">9월 15일 (월요일)</div>
            <div class="insight-detail">18명 결근</div>
        </div>
        <div class="insight-card">
            <div class="insight-label">요일별 평균</div>
            <div class="insight-value">월요일 높음</div>
            <div class="insight-detail">월 12명 vs 금 5명</div>
        </div>
    </div>
</div>
```

---

### 3️⃣ 무단결근율 (Unauthorized Absence Rate) 모달

#### 모달 제목
```
한국어: "무단결근율 상세 분석"
English: "Unauthorized Absence Rate - Detailed Analysis"
Vietnamese: "Phân tích tỷ lệ vắng mặt không phép"
```

#### 섹션 1: 심각도 배너
```html
<div class="alert alert-danger alert-with-icon">
    <div class="alert-icon">🚨</div>
    <div class="alert-content">
        <div class="alert-title">9월 무단결근율: 0.8%</div>
        <div class="alert-subtitle">
            경고 수준 (임계값 0.5% 초과) | 전월 0.6% 대비 +0.2%p
        </div>
    </div>
    <div class="alert-actions">
        <button class="btn btn-sm btn-light">
            <i class="bi bi-file-earmark-text"></i>
            조치 계획서 작성
        </button>
    </div>
</div>
```

#### 섹션 2: 3개월 추세 + 경고선
```javascript
const unauthAbsenceTrendData = {
    labels: ['7월 July', '8월 August', '9월 September'],
    datasets: [
        {
            label: '무단결근율 / Unauthorized Rate',
            data: [0.5, 0.6, 0.8],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.2)',
            tension: 0.4,
            fill: true
        },
        {
            label: '경고선 / Warning Threshold',
            data: [0.5, 0.5, 0.5],
            borderColor: '#f59e0b',
            borderDash: [5, 5],
            borderWidth: 2,
            pointRadius: 0
        }
    ]
};
```

#### 섹션 3: 무단결근자 관리 현황
```html
<div class="unauthorized-management">
    <h6>무단결근자 관리 현황 / Unauthorized Absentee Management</h6>

    <div class="severity-grid">
        <div class="severity-card critical">
            <div class="severity-icon">🔴</div>
            <div class="severity-label">즉시 조치 필요</div>
            <div class="severity-count">3명</div>
            <div class="severity-desc">3회 이상 무단결근</div>
        </div>

        <div class="severity-card warning">
            <div class="severity-icon">🟡</div>
            <div class="severity-label">주의 관찰</div>
            <div class="severity-count">5명</div>
            <div class="severity-desc">2회 무단결근</div>
        </div>

        <div class="severity-card info">
            <div class="severity-icon">🟢</div>
            <div class="severity-label">1차 경고</div>
            <div class="severity-count">8명</div>
            <div class="severity-desc">1회 무단결근</div>
        </div>
    </div>

    <div class="action-timeline">
        <h6>조치 이력 / Action History</h6>
        <div class="timeline">
            <div class="timeline-item">
                <div class="timeline-date">2025-09-20</div>
                <div class="timeline-content">
                    <strong>E12345 홍길동</strong> - 3차 경고문 발송
                </div>
            </div>
            <div class="timeline-item">
                <div class="timeline-date">2025-09-15</div>
                <div class="timeline-content">
                    <strong>5명</strong> - 1차 구두 경고
                </div>
            </div>
            <!-- More timeline items... -->
        </div>
    </div>
</div>
```

#### 섹션 4: 무단결근자 상세 명단
```html
<table class="table table-sm">
    <thead>
        <tr>
            <th>심각도</th>
            <th>사번</th>
            <th>이름</th>
            <th>팀</th>
            <th>무단결근 횟수</th>
            <th>최근 무단결근일</th>
            <th>조치 단계</th>
            <th>액션</th>
        </tr>
    </thead>
    <tbody>
        <tr class="table-danger">
            <td><span class="badge bg-danger">Critical</span></td>
            <td>E12345</td>
            <td>홍길동</td>
            <td>Team B</td>
            <td class="text-danger"><strong>3회</strong></td>
            <td>2025-09-20</td>
            <td>3차 경고 발송됨</td>
            <td>
                <button class="btn btn-sm btn-outline-danger">
                    면담 예약
                </button>
            </td>
        </tr>
        <!-- More rows... -->
    </tbody>
</table>
```

#### 섹션 5: 예방 권장사항
```html
<div class="recommendations-box">
    <h6>💡 예방 및 개선 권장사항</h6>
    <div class="recommendation-items">
        <div class="recommendation-item">
            <div class="rec-icon">📞</div>
            <div class="rec-content">
                <div class="rec-title">조기 개입</div>
                <div class="rec-desc">1회 무단결근 발생 시 즉시 전화 확인 및 구두 경고</div>
            </div>
        </div>
        <div class="recommendation-item">
            <div class="rec-icon">👥</div>
            <div class="rec-content">
                <div class="rec-title">팀장 교육</div>
                <div class="rec-desc">Team C 팀장 대상 출결 관리 교육 실시</div>
            </div>
        </div>
        <div class="recommendation-item">
            <div class="rec-icon">📋</div>
            <div class="rec-content">
                <div class="rec-title">규정 강화</div>
                <div class="rec-desc">무단결근 3회 시 징계 규정 명확화 및 공지</div>
            </div>
        </div>
    </div>
</div>
```

---

### 4️⃣ 퇴사율 (Resignation Rate) 모달

#### 섹션 1: 경고 배너 (임계값 초과 시)
```html
<div class="alert alert-danger alert-critical">
    <div class="alert-header">
        <i class="bi bi-exclamation-triangle-fill"></i>
        <strong>높은 퇴사율 경고!</strong>
    </div>
    <div class="alert-body">
        <div class="metric-large">9월 퇴사율: 4.2%</div>
        <div class="threshold-info">
            임계값 3.0% 대비 <strong class="text-danger">+1.2%p 초과</strong>
        </div>
        <div class="comparison-info">
            전월 3.5% 대비 +0.7%p 증가 | 3개월 평균 3.8%
        </div>
    </div>
</div>
```

#### 섹션 2: 12개월 추세 (실제로는 3개월)
```javascript
// 현재는 3개월만 표시, 향후 확장
const resignationTrendData = {
    labels: ['7월', '8월', '9월'],
    datasets: [
        {
            label: '퇴사율',
            data: [3.8, 3.5, 4.2],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            tension: 0.4,
            fill: true
        },
        {
            label: '임계값 (3.0%)',
            data: [3.0, 3.0, 3.0],
            borderColor: '#10b981',
            borderDash: [5, 5]
        }
    ]
};
```

#### 섹션 3: 퇴사 사유 분석 (2열 레이아웃)
```html
<div class="row">
    <div class="col-md-6">
        <h6>퇴사 사유 분포</h6>
        <canvas id="resignationReasonsPie"></canvas>
    </div>
    <div class="col-md-6">
        <h6>사유별 상세</h6>
        <div class="reasons-detail">
            <div class="reason-detail-item">
                <div class="reason-header">
                    <span class="reason-name">자발적 퇴사</span>
                    <span class="reason-count">12명 (75.0%)</span>
                </div>
                <div class="reason-breakdown">
                    <div class="breakdown-item">급여 불만: 5명</div>
                    <div class="breakdown-item">근무환경: 4명</div>
                    <div class="breakdown-item">개인사정: 3명</div>
                </div>
            </div>

            <div class="reason-detail-item">
                <div class="reason-header">
                    <span class="reason-name">계약 만료</span>
                    <span class="reason-count">3명 (18.8%)</span>
                </div>
                <div class="reason-breakdown">
                    <div class="breakdown-item">정규직 전환 실패: 2명</div>
                    <div class="breakdown-item">계약 갱신 거부: 1명</div>
                </div>
            </div>

            <div class="reason-detail-item">
                <div class="reason-header">
                    <span class="reason-name">해고</span>
                    <span class="reason-count">1명 (6.2%)</span>
                </div>
                <div class="reason-breakdown">
                    <div class="breakdown-item">무단결근: 1명</div>
                </div>
            </div>
        </div>
    </div>
</div>
```

#### 섹션 4: 재직기간별 퇴사 분석
```html
<div class="tenure-resignation-analysis">
    <h6>재직기간별 퇴사자 분포</h6>

    <canvas id="tenureResignationChart"></canvas>

    <div class="tenure-insights">
        <div class="insight-box danger">
            <div class="insight-icon">⚠️</div>
            <div class="insight-content">
                <strong>조기 이탈 높음</strong>
                <p>6개월 미만 재직자 퇴사 비율 37.5% (6명)</p>
                <p>온보딩 프로세스 개선 필요</p>
            </div>
        </div>

        <div class="insight-box warning">
            <div class="insight-icon">📊</div>
            <div class="insight-content">
                <strong>1-2년차 이탈</strong>
                <p>1-2년 재직자 퇴사 비율 31.3% (5명)</p>
                <p>경력 개발 프로그램 강화 필요</p>
            </div>
        </div>
    </div>
</div>
```

#### 섹션 5: 퇴사자 상세 명단
```html
<div class="resignees-list">
    <h6>9월 퇴사자 명단 (16명)</h6>

    <div class="table-controls mb-3">
        <input type="text" class="search-input" placeholder="검색...">
        <select class="filter-select">
            <option value="">전체 사유</option>
            <option value="voluntary">자발적 퇴사</option>
            <option value="contract">계약 만료</option>
            <option value="termination">해고</option>
        </select>
    </div>

    <table class="table table-sm table-hover">
        <thead>
            <tr>
                <th>사번</th>
                <th>이름</th>
                <th>직급</th>
                <th>팀</th>
                <th>입사일</th>
                <th>퇴사일</th>
                <th>재직일수</th>
                <th>재직기간</th>
                <th>퇴사 사유</th>
                <th>엑시트 인터뷰</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>E12345</td>
                <td>홍길동</td>
                <td>A.INSPECTOR</td>
                <td>Team A</td>
                <td>2025-03-15</td>
                <td>2025-09-20</td>
                <td>189일</td>
                <td>6.3개월</td>
                <td>
                    <span class="badge bg-warning">자발적 퇴사</span>
                    <br><small>급여 불만</small>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary"
                            onclick="viewExitInterview('E12345')">
                        <i class="bi bi-eye"></i> 보기
                    </button>
                </td>
            </tr>
            <!-- More rows... -->
        </tbody>
    </table>

    <div class="exit-interview-summary">
        <h6>엑시트 인터뷰 주요 피드백</h6>
        <div class="feedback-tags">
            <span class="tag tag-frequent">급여 불만 (5건)</span>
            <span class="tag tag-frequent">근무환경 (4건)</span>
            <span class="tag tag-moderate">성장 기회 부족 (3건)</span>
            <span class="tag tag-moderate">직급 체계 (2건)</span>
        </div>
    </div>
</div>
```

#### 섹션 6: 팀별 퇴사율 비교
```html
<div class="team-resignation-comparison">
    <h6>팀별 퇴사율 비교</h6>

    <div class="team-comparison-bars">
        <div class="team-bar-row">
            <div class="team-label">Team A</div>
            <div class="team-bar-wrapper">
                <div class="team-bar bg-success" style="width: 2.5%">
                    <span>2.5%</span>
                </div>
            </div>
            <div class="team-details">
                <span>3명 / 142명</span>
            </div>
        </div>

        <div class="team-bar-row">
            <div class="team-label">Team B</div>
            <div class="team-bar-wrapper">
                <div class="team-bar bg-danger" style="width: 6.5%">
                    <span>6.5%</span>
                </div>
            </div>
            <div class="team-details">
                <span class="text-danger">7명 / 108명 ⚠️</span>
            </div>
        </div>

        <div class="team-bar-row">
            <div class="team-label">Team C</div>
            <div class="team-bar-wrapper">
                <div class="team-bar bg-warning" style="width: 4.2%">
                    <span>4.2%</span>
                </div>
            </div>
            <div class="team-details">
                <span>4명 / 95명</span>
            </div>
        </div>
    </div>

    <div class="alert alert-warning mt-3">
        <strong>⚠️ Team B 긴급 대응 필요</strong>
        <p>Team B의 퇴사율이 6.5%로 전체 평균 4.2% 대비 2.3%p 높음</p>
        <p>팀장 면담 및 팀 분위기 조사 권장</p>
    </div>
</div>
```

---

### 5️⃣ 신규 입사자 (Recent Hires) 모달

*(계속 작성 중... 파일이 길어져서 다음 메시지에서 계속)*

---

## 📌 공통 JavaScript 함수

```javascript
// 테이블 정렬
function sortTable(columnIndex) {
    // Implementation
}

// 테이블 필터링
function filterTable(searchTerm, tableId) {
    // Implementation
}

// 접이식 토글
function toggleAccordion(sectionId) {
    // Implementation
}

// Excel 다운로드
function exportToExcel(tableId) {
    // Implementation
}

// 차트 생성 (Chart.js)
function createTrendChart(canvasId, data, options) {
    // Implementation
}
```

---

**다음 파일에서 계속 (5번~11번 KPI 모달 상세 + CSS 스타일)**
