# KPI 모달 상세 설계 Part 3

## 실제 데이터 현황 (Data Availability)

✅ **Basic Manpower Data**: July, August, September 2025
✅ **Attendance Data**: July, August, September 2025
✅ **AQL History**: May, June, July, August, September 2025 (5개월)
✅ **5PRS Data**: July, August, September 2025

**추세 차트 전략**:
- 현재: 3개월 추세 표시 (7월~9월)
- 향후: 매월 자동 누적 (10월, 11월, 12월...)
- 장기: 6개월+ 완전한 추세 분석

---

## 🔟 장기근속자 (Long-term Employees) 모달

### 모달 구조 (6개 섹션)

#### 섹션 1: 현황 요약 (3-Stat Summary)

```html
<div class="modal-stat-grid">
    <div class="modal-stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            🏆
        </div>
        <div class="stat-info">
            <div class="stat-value">315명</div>
            <div class="stat-label">장기근속자 (1년+)</div>
            <div class="stat-sublabel">Long-term Employees</div>
            <div class="stat-change positive">+23 vs 8월</div>
        </div>
    </div>

    <div class="modal-stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            📈
        </div>
        <div class="stat-info">
            <div class="stat-value">80.2%</div>
            <div class="stat-label">장기근속률</div>
            <div class="stat-sublabel">Retention Rate (1yr+)</div>
            <div class="stat-change positive">+4.1%p vs 8월</div>
        </div>
    </div>

    <div class="modal-stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
            ⏱️
        </div>
        <div class="stat-info">
            <div class="stat-value">892일</div>
            <div class="stat-label">평균 재직일수</div>
            <div class="stat-sublabel">Average Tenure Days</div>
            <div class="stat-change positive">+18일 vs 8월</div>
        </div>
    </div>
</div>
```

#### 섹션 2: 재직기간 분포 (Tenure Distribution)

```html
<div class="tenure-distribution">
    <h6>재직기간 분포 / Tenure Distribution</h6>
    <canvas id="tenureDistributionChart"></canvas>
</div>

<script>
const tenureDistributionData = {
    labels: [
        '1-2년 / 1-2yr',
        '2-3년 / 2-3yr',
        '3-5년 / 3-5yr',
        '5-10년 / 5-10yr',
        '10년+ / 10yr+'
    ],
    datasets: [{
        label: '인원수 / Count',
        data: [142, 89, 58, 21, 5],  // 실제 데이터에서 계산
        backgroundColor: [
            'rgba(102, 126, 234, 0.7)',
            'rgba(118, 75, 162, 0.7)',
            'rgba(237, 100, 166, 0.7)',
            'rgba(255, 154, 158, 0.7)',
            'rgba(250, 208, 196, 0.7)'
        ],
        borderWidth: 1,
        borderColor: '#fff'
    }]
};

new Chart(document.getElementById('tenureDistributionChart'), {
    type: 'doughnut',
    data: tenureDistributionData,
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: { font: { size: 11 } }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((context.parsed / total) * 100).toFixed(1);
                        return `${context.label}: ${context.parsed}명 (${percentage}%)`;
                    }
                }
            }
        }
    }
});
</script>
```

#### 섹션 3: 장기근속 Top 10 랭킹

```html
<div class="tenure-top10">
    <h6>🏆 장기근속 Top 10 / Top 10 Long-term Employees</h6>
    <div class="table-responsive">
        <table class="table table-hover sortable-table">
            <thead class="sticky-header">
                <tr>
                    <th onclick="sortTable(this, 0)">순위<br>Rank</th>
                    <th onclick="sortTable(this, 1)">사원명<br>Name</th>
                    <th onclick="sortTable(this, 2)">직급<br>Position</th>
                    <th onclick="sortTable(this, 3)">팀<br>Team</th>
                    <th onclick="sortTable(this, 4)">입사일<br>Join Date</th>
                    <th onclick="sortTable(this, 5)">재직일수<br>Days</th>
                    <th onclick="sortTable(this, 6)">재직년수<br>Years</th>
                    <th onclick="sortTable(this, 7)">포상 등급<br>Award Tier</th>
                </tr>
            </thead>
            <tbody>
                <tr class="rank-1">
                    <td>
                        <div class="rank-badge gold">🥇 1</div>
                    </td>
                    <td>
                        <div class="employee-cell">
                            <div class="employee-name">Nguyễn Thị Lan</div>
                            <div class="employee-id">VN-2015-001</div>
                        </div>
                    </td>
                    <td><span class="badge bg-primary">LINE LEADER</span></td>
                    <td>Assembly Team A</td>
                    <td>2015-03-15</td>
                    <td class="text-end fw-bold">3,821일</td>
                    <td class="text-end fw-bold">10.5년</td>
                    <td><span class="badge bg-danger">최우수 / Platinum</span></td>
                </tr>
                <tr class="rank-2">
                    <td>
                        <div class="rank-badge silver">🥈 2</div>
                    </td>
                    <td>
                        <div class="employee-cell">
                            <div class="employee-name">Trần Văn Minh</div>
                            <div class="employee-id">VN-2016-042</div>
                        </div>
                    </td>
                    <td><span class="badge bg-info">ASSEMBLY INSPECTOR</span></td>
                    <td>QC Team B</td>
                    <td>2016-07-20</td>
                    <td class="text-end fw-bold">3,359일</td>
                    <td class="text-end fw-bold">9.2년</td>
                    <td><span class="badge bg-danger">최우수 / Platinum</span></td>
                </tr>
                <tr class="rank-3">
                    <td>
                        <div class="rank-badge bronze">🥉 3</div>
                    </td>
                    <td>
                        <div class="employee-cell">
                            <div class="employee-name">Lê Thị Hương</div>
                            <div class="employee-id">VN-2017-089</div>
                        </div>
                    </td>
                    <td><span class="badge bg-success">AQL INSPECTOR</span></td>
                    <td>Quality Team C</td>
                    <td>2017-01-10</td>
                    <td class="text-end fw-bold">3,186일</td>
                    <td class="text-end fw-bold">8.7년</td>
                    <td><span class="badge bg-warning">우수 / Gold</span></td>
                </tr>
                <!-- ... 7명 더 ... -->
            </tbody>
        </table>
    </div>
</div>

<style>
.rank-badge {
    display: inline-block;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    text-align: center;
    line-height: 40px;
    font-weight: bold;
    font-size: 14px;
}

.rank-badge.gold {
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    color: #fff;
    box-shadow: 0 4px 8px rgba(255, 215, 0, 0.4);
}

.rank-badge.silver {
    background: linear-gradient(135deg, #C0C0C0 0%, #A9A9A9 100%);
    color: #fff;
    box-shadow: 0 4px 8px rgba(192, 192, 192, 0.4);
}

.rank-badge.bronze {
    background: linear-gradient(135deg, #CD7F32 0%, #A0522D 100%);
    color: #fff;
    box-shadow: 0 4px 8px rgba(205, 127, 50, 0.4);
}

.rank-1 { background-color: rgba(255, 215, 0, 0.1); }
.rank-2 { background-color: rgba(192, 192, 192, 0.1); }
.rank-3 { background-color: rgba(205, 127, 50, 0.1); }
</style>
```

#### 섹션 4: 팀별 장기근속률 비교

```html
<div class="team-tenure-comparison">
    <h6>팀별 장기근속률 비교 / Team-wise Long-term Retention</h6>
    <canvas id="teamTenureChart"></canvas>
</div>

<script>
const teamTenureData = {
    labels: [
        'Assembly Team A',
        'Assembly Team B',
        'QC Team A',
        'QC Team B',
        'Packaging Team',
        'Maintenance Team'
    ],
    datasets: [{
        label: '장기근속률 (1년+) / Long-term Rate (%)',
        data: [85.3, 82.1, 78.9, 76.5, 73.2, 91.4],  // 실제 데이터
        backgroundColor: 'rgba(102, 126, 234, 0.7)',
        borderColor: '#667eea',
        borderWidth: 1
    }]
};

new Chart(document.getElementById('teamTenureChart'), {
    type: 'bar',
    data: teamTenureData,
    options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `장기근속률: ${context.parsed.x}%`;
                    }
                }
            }
        },
        scales: {
            x: {
                beginAtZero: true,
                max: 100,
                ticks: {
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }
        }
    }
});
</script>
```

#### 섹션 5: 근속 포상 대상자 계산

```html
<div class="tenure-award-calculation">
    <h6>💰 근속 포상 대상자 산출 / Tenure Award Calculation</h6>

    <div class="alert alert-info">
        <strong>📋 포상 기준 / Award Criteria</strong>
        <ul>
            <li>🏆 Platinum (10년+): $2,000 상당 포상</li>
            <li>🥇 Gold (5-10년): $1,000 상당 포상</li>
            <li>🥈 Silver (3-5년): $500 상당 포상</li>
            <li>🥉 Bronze (1-3년): 감사장 수여</li>
        </ul>
    </div>

    <div class="award-tier-summary">
        <div class="row g-3">
            <div class="col-md-3">
                <div class="award-tier-card platinum">
                    <div class="tier-icon">🏆</div>
                    <div class="tier-name">Platinum</div>
                    <div class="tier-count">5명</div>
                    <div class="tier-amount">$10,000</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="award-tier-card gold">
                    <div class="tier-icon">🥇</div>
                    <div class="tier-name">Gold</div>
                    <div class="tier-count">21명</div>
                    <div class="tier-amount">$21,000</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="award-tier-card silver">
                    <div class="tier-icon">🥈</div>
                    <div class="tier-name">Silver</div>
                    <div class="tier-count">58명</div>
                    <div class="tier-amount">$29,000</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="award-tier-card bronze">
                    <div class="tier-icon">🥉</div>
                    <div class="tier-name">Bronze</div>
                    <div class="tier-count">231명</div>
                    <div class="tier-amount">감사장</div>
                </div>
            </div>
        </div>

        <div class="alert alert-success mt-3">
            <strong>💵 총 포상 예산 / Total Award Budget</strong>
            <div class="budget-summary">
                <span class="budget-amount">$60,000</span>
                <span class="budget-desc">(315명 대상)</span>
            </div>
        </div>
    </div>
</div>

<style>
.award-tier-card {
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.award-tier-card:hover {
    transform: translateY(-5px);
}

.award-tier-card.platinum {
    background: linear-gradient(135deg, #e0e0e0 0%, #bdbdbd 100%);
}

.award-tier-card.gold {
    background: linear-gradient(135deg, #ffd700 0%, #ffa500 100%);
}

.award-tier-card.silver {
    background: linear-gradient(135deg, #c0c0c0 0%, #a9a9a9 100%);
}

.award-tier-card.bronze {
    background: linear-gradient(135deg, #cd7f32 0%, #a0522d 100%);
}

.tier-icon {
    font-size: 36px;
    margin-bottom: 10px;
}

.tier-name {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 5px;
    color: #333;
}

.tier-count {
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 5px;
    color: #1a1a1a;
}

.tier-amount {
    font-size: 14px;
    color: #555;
}

.budget-amount {
    font-size: 32px;
    font-weight: bold;
    color: #28a745;
    margin-right: 10px;
}
</style>
```

#### 섹션 6: 전체 장기근속자 명단

```html
<div class="all-longterm-list">
    <h6>전체 장기근속자 명단 (315명) / All Long-term Employees List</h6>

    <div class="list-controls mb-3">
        <div class="row g-2">
            <div class="col-md-4">
                <input type="text" class="form-control" id="longtermSearch"
                       placeholder="🔍 검색 / Search (Name, ID, Team)">
            </div>
            <div class="col-md-3">
                <select class="form-select" id="longtermTierFilter">
                    <option value="">전체 등급 / All Tiers</option>
                    <option value="Platinum">Platinum (10년+)</option>
                    <option value="Gold">Gold (5-10년)</option>
                    <option value="Silver">Silver (3-5년)</option>
                    <option value="Bronze">Bronze (1-3년)</option>
                </select>
            </div>
            <div class="col-md-3">
                <select class="form-select" id="longtermTeamFilter">
                    <option value="">전체 팀 / All Teams</option>
                    <option value="Assembly">Assembly Teams</option>
                    <option value="QC">QC Teams</option>
                    <option value="Packaging">Packaging Team</option>
                    <option value="Maintenance">Maintenance Team</option>
                </select>
            </div>
            <div class="col-md-2">
                <button class="btn btn-success w-100" onclick="exportLongtermToExcel()">
                    📊 Excel 다운로드
                </button>
            </div>
        </div>
    </div>

    <div class="table-responsive" style="max-height: 500px;">
        <table class="table table-hover sortable-table" id="longtermTable">
            <thead class="sticky-header">
                <tr>
                    <th onclick="sortTable(this, 0)">사원번호<br>ID</th>
                    <th onclick="sortTable(this, 1)">사원명<br>Name</th>
                    <th onclick="sortTable(this, 2)">직급<br>Position</th>
                    <th onclick="sortTable(this, 3)">팀<br>Team</th>
                    <th onclick="sortTable(this, 4)">입사일<br>Join Date</th>
                    <th onclick="sortTable(this, 5)">재직일수<br>Days</th>
                    <th onclick="sortTable(this, 6)">재직년수<br>Years</th>
                    <th onclick="sortTable(this, 7)">포상 등급<br>Award</th>
                </tr>
            </thead>
            <tbody id="longtermTableBody">
                <!-- JavaScript로 동적 생성 -->
            </tbody>
        </table>
    </div>

    <div class="table-footer">
        <span id="longtermCount">총 315명 표시 / Showing 315 employees</span>
    </div>
</div>

<script>
// 검색 및 필터링 로직
document.getElementById('longtermSearch').addEventListener('input', filterLongtermTable);
document.getElementById('longtermTierFilter').addEventListener('change', filterLongtermTable);
document.getElementById('longtermTeamFilter').addEventListener('change', filterLongtermTable);

function filterLongtermTable() {
    const searchText = document.getElementById('longtermSearch').value.toLowerCase();
    const tierFilter = document.getElementById('longtermTierFilter').value;
    const teamFilter = document.getElementById('longtermTeamFilter').value;

    const rows = document.querySelectorAll('#longtermTableBody tr');
    let visibleCount = 0;

    rows.forEach(row => {
        const name = row.cells[1].textContent.toLowerCase();
        const id = row.cells[0].textContent.toLowerCase();
        const team = row.cells[3].textContent;
        const tier = row.cells[7].textContent;

        const matchSearch = name.includes(searchText) || id.includes(searchText) || team.toLowerCase().includes(searchText);
        const matchTier = !tierFilter || tier.includes(tierFilter);
        const matchTeam = !teamFilter || team.includes(teamFilter);

        if (matchSearch && matchTier && matchTeam) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    document.getElementById('longtermCount').textContent =
        `총 ${visibleCount}명 표시 / Showing ${visibleCount} employees`;
}

function exportLongtermToExcel() {
    // Excel export 로직 (SheetJS 활용)
    const table = document.getElementById('longtermTable');
    const wb = XLSX.utils.table_to_book(table, {sheet: "Long-term Employees"});
    XLSX.writeFile(wb, '장기근속자_명단_2025_09.xlsx');
}
</script>
```

---

## 1️⃣1️⃣ 데이터 오류 (Data Errors) 모달

### 모달 구조 (5개 섹션)

#### 섹션 1: 오류 현황 요약 (3-Stat Summary)

```html
<div class="modal-stat-grid">
    <div class="modal-stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            ⚠️
        </div>
        <div class="stat-info">
            <div class="stat-value">28건</div>
            <div class="stat-label">총 오류 건수</div>
            <div class="stat-sublabel">Total Data Errors</div>
            <div class="stat-change negative">+5 vs 8월</div>
        </div>
    </div>

    <div class="modal-stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
            🔴
        </div>
        <div class="stat-info">
            <div class="stat-value">8건</div>
            <div class="stat-label">심각 오류 (Critical)</div>
            <div class="stat-sublabel">Immediate Action Required</div>
            <div class="stat-change negative">+2 vs 8월</div>
        </div>
    </div>

    <div class="modal-stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            📊
        </div>
        <div class="stat-info">
            <div class="stat-value">71.4%</div>
            <div class="stat-label">데이터 품질 점수</div>
            <div class="stat-sublabel">Data Quality Score</div>
            <div class="stat-change negative">-1.8%p vs 8월</div>
        </div>
    </div>
</div>
```

#### 섹션 2: 심각도별 오류 분포

```html
<div class="error-severity-distribution">
    <h6>심각도별 오류 분포 / Error Distribution by Severity</h6>
    <div class="severity-cards-grid">
        <div class="severity-card critical">
            <div class="severity-header">
                <div class="severity-icon">🔴</div>
                <div class="severity-title">Critical</div>
            </div>
            <div class="severity-count">8건</div>
            <div class="severity-desc">즉시 조치 필요</div>
            <div class="severity-examples">
                • 입사일/퇴사일 모순 (3건)<br>
                • 중복 사원번호 (2건)<br>
                • 필수 필드 누락 (3건)
            </div>
        </div>

        <div class="severity-card warning">
            <div class="severity-header">
                <div class="severity-icon">🟡</div>
                <div class="severity-title">Warning</div>
            </div>
            <div class="severity-count">12건</div>
            <div class="severity-desc">검토 및 확인 필요</div>
            <div class="severity-examples">
                • 출근율 계산 이상 (5건)<br>
                • 직급 매핑 미정의 (4건)<br>
                • 팀 정보 불일치 (3건)
            </div>
        </div>

        <div class="severity-card info">
            <div class="severity-header">
                <div class="severity-icon">🔵</div>
                <div class="severity-title">Info</div>
            </div>
            <div class="severity-count">8건</div>
            <div class="severity-desc">참고 정보</div>
            <div class="severity-examples">
                • 선택 필드 미입력 (6건)<br>
                • 포맷 표준화 권장 (2건)
            </div>
        </div>
    </div>
</div>

<style>
.severity-cards-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-top: 15px;
}

.severity-card {
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.severity-card:hover {
    transform: translateY(-5px);
}

.severity-card.critical {
    background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
    border-left: 4px solid #dc3545;
}

.severity-card.warning {
    background: linear-gradient(135deg, #fffef5 0%, #fff4d6 100%);
    border-left: 4px solid #ffc107;
}

.severity-card.info {
    background: linear-gradient(135deg, #f0f8ff 0%, #d6ebff 100%);
    border-left: 4px solid #0dcaf0;
}

.severity-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.severity-icon {
    font-size: 24px;
}

.severity-title {
    font-size: 16px;
    font-weight: bold;
    color: #333;
}

.severity-count {
    font-size: 32px;
    font-weight: bold;
    margin: 10px 0;
    color: #1a1a1a;
}

.severity-desc {
    font-size: 13px;
    color: #666;
    margin-bottom: 10px;
}

.severity-examples {
    font-size: 11px;
    color: #555;
    line-height: 1.6;
    background: rgba(255,255,255,0.5);
    padding: 10px;
    border-radius: 6px;
}
</style>
```

#### 섹션 3: 카테고리별 오류 분석

```html
<div class="error-category-analysis">
    <h6>카테고리별 오류 분석 / Error Analysis by Category</h6>

    <div class="accordion" id="errorCategoryAccordion">
        <!-- 카테고리 1: 시간적 모순 -->
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button" type="button" data-bs-toggle="collapse"
                        data-bs-target="#category1">
                    <span class="error-badge critical">3건</span>
                    1️⃣ 시간적 모순 (Temporal Inconsistency)
                </button>
            </h2>
            <div id="category1" class="accordion-collapse collapse show">
                <div class="accordion-body">
                    <div class="alert alert-danger">
                        <strong>🔴 Critical - 즉시 조치 필요</strong>
                    </div>
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>사원번호</th>
                                <th>사원명</th>
                                <th>오류 내용</th>
                                <th>상세</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>VN-2024-1234</td>
                                <td>Nguyễn Văn A</td>
                                <td>퇴사일이 입사일보다 빠름</td>
                                <td>입사: 2024-09-15 / 퇴사: 2024-08-20</td>
                            </tr>
                            <tr>
                                <td>VN-2023-5678</td>
                                <td>Trần Thị B</td>
                                <td>배정일이 입사일보다 빠름</td>
                                <td>입사: 2023-05-10 / 배정: 2023-04-15</td>
                            </tr>
                            <tr>
                                <td>VN-2025-9012</td>
                                <td>Lê Văn C</td>
                                <td>미래 입사일</td>
                                <td>입사: 2025-12-01 (현재: 2025-09-30)</td>
                            </tr>
                        </tbody>
                    </table>
                    <div class="recommendation">
                        <strong>💡 권장 조치:</strong> HR 시스템에서 날짜 데이터 재확인 및 수정 필요
                    </div>
                </div>
            </div>
        </div>

        <!-- 카테고리 2: 유형 모순 -->
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                        data-bs-target="#category2">
                    <span class="error-badge warning">4건</span>
                    2️⃣ 유형 모순 (Type Mismatch)
                </button>
            </h2>
            <div id="category2" class="accordion-collapse collapse">
                <div class="accordion-body">
                    <div class="alert alert-warning">
                        <strong>🟡 Warning - 검토 및 확인 필요</strong>
                    </div>
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>사원번호</th>
                                <th>사원명</th>
                                <th>오류 내용</th>
                                <th>상세</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>VN-2024-2345</td>
                                <td>Phạm Thị D</td>
                                <td>직급 미정의</td>
                                <td>Position: "SENIOR QC" (매핑 없음)</td>
                            </tr>
                            <tr>
                                <td>VN-2024-3456</td>
                                <td>Hoàng Văn E</td>
                                <td>직급 미정의</td>
                                <td>Position: "QUALITY LEAD" (매핑 없음)</td>
                            </tr>
                            <tr>
                                <td>VN-2023-4567</td>
                                <td>Đặng Thị F</td>
                                <td>숫자 필드에 텍스트</td>
                                <td>WTime: "N/A" (숫자 기대)</td>
                            </tr>
                            <tr>
                                <td>VN-2024-5678</td>
                                <td>Vũ Văn G</td>
                                <td>날짜 형식 불일치</td>
                                <td>Join Date: "15-09-2024" (YYYY-MM-DD 기대)</td>
                            </tr>
                        </tbody>
                    </table>
                    <div class="recommendation">
                        <strong>💡 권장 조치:</strong> position_condition_matrix.json에 누락된 직급 추가, 데이터 타입 표준화
                    </div>
                </div>
            </div>
        </div>

        <!-- 카테고리 3: 직급 매핑 오류 -->
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                        data-bs-target="#category3">
                    <span class="error-badge warning">4건</span>
                    3️⃣ 직급 매핑 오류 (Position Mapping Error)
                </button>
            </h2>
            <div id="category3" class="accordion-collapse collapse">
                <div class="accordion-body">
                    <p>position_condition_matrix.json에 정의되지 않은 직급이 발견되었습니다.</p>
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>직급 (Position)</th>
                                <th>발견 건수</th>
                                <th>영향받는 직원</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>SENIOR QC</td>
                                <td>2명</td>
                                <td>VN-2024-2345, VN-2024-6789</td>
                            </tr>
                            <tr>
                                <td>QUALITY LEAD</td>
                                <td>1명</td>
                                <td>VN-2024-3456</td>
                            </tr>
                            <tr>
                                <td>INSPECTOR TRAINEE</td>
                                <td>1명</td>
                                <td>VN-2025-0001</td>
                            </tr>
                        </tbody>
                    </table>
                    <div class="recommendation">
                        <strong>💡 권장 조치:</strong> config_files/position_condition_matrix.json 업데이트 필요
                    </div>
                </div>
            </div>
        </div>

        <!-- 카테고리 4: 팀 정보 불일치 -->
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                        data-bs-target="#category4">
                    <span class="error-badge warning">3건</span>
                    4️⃣ 팀 정보 불일치 (Team Information Mismatch)
                </button>
            </h2>
            <div id="category4" class="accordion-collapse collapse">
                <div class="accordion-body">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>사원번호</th>
                                <th>사원명</th>
                                <th>오류 내용</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>VN-2024-7890</td>
                                <td>Bùi Thị H</td>
                                <td>팀명 미입력 (NULL)</td>
                            </tr>
                            <tr>
                                <td>VN-2023-8901</td>
                                <td>Đinh Văn I</td>
                                <td>팀명 표준 위반 ("Team-A" vs "Assembly Team A")</td>
                            </tr>
                            <tr>
                                <td>VN-2024-9012</td>
                                <td>Dương Thị K</td>
                                <td>상급자 ID 존재하지 않음 (boss_id: 99999)</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- 카테고리 5: 출근 데이터 이상 -->
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                        data-bs-target="#category5">
                    <span class="error-badge warning">5건</span>
                    5️⃣ 출근 데이터 이상 (Attendance Data Anomaly)
                </button>
            </h2>
            <div id="category5" class="accordion-collapse collapse">
                <div class="accordion-body">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>사원번호</th>
                                <th>사원명</th>
                                <th>오류 내용</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>VN-2024-1111</td>
                                <td>Mai Thị L</td>
                                <td>출근율 100% 초과 (계산 오류)</td>
                            </tr>
                            <tr>
                                <td>VN-2023-2222</td>
                                <td>Cao Văn M</td>
                                <td>퇴사자인데 9월 출근 기록 존재</td>
                            </tr>
                            <tr>
                                <td>VN-2024-3333</td>
                                <td>Tô Thị N</td>
                                <td>WTime 음수 값 (-2.5)</td>
                            </tr>
                            <tr>
                                <td>VN-2024-4444</td>
                                <td>Lý Văn O</td>
                                <td>근무일수가 월 영업일 초과 (30일 > 26일)</td>
                            </tr>
                            <tr>
                                <td>VN-2025-5555</td>
                                <td>Hồ Thị P</td>
                                <td>9월 입사자인데 출근 데이터 없음</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- 카테고리 6: 중복 데이터 -->
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                        data-bs-target="#category6">
                    <span class="error-badge critical">2건</span>
                    6️⃣ 중복 데이터 (Duplicate Records)
                </button>
            </h2>
            <div id="category6" class="accordion-collapse collapse">
                <div class="accordion-body">
                    <div class="alert alert-danger">
                        <strong>🔴 Critical - 데이터 무결성 침해</strong>
                    </div>
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>사원번호</th>
                                <th>중복 건수</th>
                                <th>상세</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>VN-2024-6666</td>
                                <td>2건</td>
                                <td>동일 사원번호로 2개 행 존재 (행 145, 287)</td>
                            </tr>
                            <tr>
                                <td>VN-2023-7777</td>
                                <td>2건</td>
                                <td>동일 사원번호로 2개 행 존재 (행 89, 312)</td>
                            </tr>
                        </tbody>
                    </table>
                    <div class="recommendation">
                        <strong>💡 권장 조치:</strong> HR 시스템에서 중복 레코드 확인 후 병합 또는 삭제
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.error-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    margin-right: 10px;
}

.error-badge.critical {
    background: #dc3545;
    color: white;
}

.error-badge.warning {
    background: #ffc107;
    color: #333;
}

.error-badge.info {
    background: #0dcaf0;
    color: white;
}

.recommendation {
    margin-top: 15px;
    padding: 12px;
    background: #f0f8ff;
    border-left: 4px solid #0dcaf0;
    border-radius: 6px;
}
</style>
```

#### 섹션 4: 오류 해결 가이드

```html
<div class="error-resolution-guide">
    <h6>🛠️ 오류 해결 가이드 / Error Resolution Guide</h6>

    <div class="resolution-steps">
        <div class="step-card">
            <div class="step-number">1</div>
            <div class="step-content">
                <div class="step-title">Critical 오류 우선 처리</div>
                <div class="step-desc">
                    시간적 모순, 중복 데이터 등 데이터 무결성을 침해하는 오류를 먼저 해결합니다.
                </div>
                <div class="step-action">
                    <button class="btn btn-sm btn-danger" onclick="exportCriticalErrors()">
                        📊 Critical 오류 리포트 다운로드
                    </button>
                </div>
            </div>
        </div>

        <div class="step-card">
            <div class="step-number">2</div>
            <div class="step-content">
                <div class="step-title">직급 매핑 업데이트</div>
                <div class="step-desc">
                    position_condition_matrix.json에 누락된 직급을 추가합니다.
                </div>
                <div class="step-action">
                    <code style="font-size: 11px;">
                        config_files/position_condition_matrix.json 수정 필요
                    </code>
                </div>
            </div>
        </div>

        <div class="step-card">
            <div class="step-number">3</div>
            <div class="step-content">
                <div class="step-title">데이터 표준화</div>
                <div class="step-desc">
                    날짜 형식, 팀명 표기, 필드 타입 등을 표준화합니다.
                </div>
                <div class="step-action">
                    <button class="btn btn-sm btn-primary" onclick="runDataStandardization()">
                        🔄 자동 표준화 실행
                    </button>
                </div>
            </div>
        </div>

        <div class="step-card">
            <div class="step-number">4</div>
            <div class="step-content">
                <div class="step-title">재검증</div>
                <div class="step-desc">
                    수정 후 전체 데이터 재검증을 실행합니다.
                </div>
                <div class="step-action">
                    <code style="font-size: 11px;">
                        python src/validate_hr_data.py 9 2025
                    </code>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.resolution-steps {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.step-card {
    display: flex;
    gap: 15px;
    padding: 20px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    transition: transform 0.3s;
}

.step-card:hover {
    transform: translateX(5px);
}

.step-number {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: bold;
    flex-shrink: 0;
}

.step-content {
    flex: 1;
}

.step-title {
    font-size: 16px;
    font-weight: bold;
    color: #333;
    margin-bottom: 8px;
}

.step-desc {
    font-size: 13px;
    color: #666;
    margin-bottom: 10px;
}

.step-action {
    margin-top: 10px;
}
</style>
```

#### 섹션 5: 전체 오류 목록

```html
<div class="all-errors-list">
    <h6>전체 오류 목록 (28건) / All Errors List</h6>

    <div class="list-controls mb-3">
        <div class="row g-2">
            <div class="col-md-4">
                <input type="text" class="form-control" id="errorSearch"
                       placeholder="🔍 검색 / Search (ID, Name, Category)">
            </div>
            <div class="col-md-3">
                <select class="form-select" id="errorSeverityFilter">
                    <option value="">전체 심각도 / All Severities</option>
                    <option value="Critical">🔴 Critical</option>
                    <option value="Warning">🟡 Warning</option>
                    <option value="Info">🔵 Info</option>
                </select>
            </div>
            <div class="col-md-3">
                <select class="form-select" id="errorCategoryFilter">
                    <option value="">전체 카테고리 / All Categories</option>
                    <option value="시간적 모순">시간적 모순</option>
                    <option value="유형 모순">유형 모순</option>
                    <option value="직급 매핑">직급 매핑 오류</option>
                    <option value="팀 정보">팀 정보 불일치</option>
                    <option value="출근 데이터">출근 데이터 이상</option>
                    <option value="중복 데이터">중복 데이터</option>
                </select>
            </div>
            <div class="col-md-2">
                <button class="btn btn-danger w-100" onclick="exportErrorsToExcel()">
                    📊 오류 리포트
                </button>
            </div>
        </div>
    </div>

    <div class="table-responsive" style="max-height: 500px;">
        <table class="table table-hover sortable-table" id="errorsTable">
            <thead class="sticky-header">
                <tr>
                    <th onclick="sortTable(this, 0)">심각도<br>Severity</th>
                    <th onclick="sortTable(this, 1)">카테고리<br>Category</th>
                    <th onclick="sortTable(this, 2)">사원번호<br>ID</th>
                    <th onclick="sortTable(this, 3)">사원명<br>Name</th>
                    <th onclick="sortTable(this, 4)">오류 내용<br>Error Description</th>
                    <th onclick="sortTable(this, 5)">상세 정보<br>Details</th>
                </tr>
            </thead>
            <tbody id="errorsTableBody">
                <!-- JavaScript로 동적 생성 -->
            </tbody>
        </table>
    </div>

    <div class="table-footer">
        <span id="errorCount">총 28건 표시 / Showing 28 errors</span>
    </div>
</div>

<script>
function exportErrorsToExcel() {
    const table = document.getElementById('errorsTable');
    const wb = XLSX.utils.table_to_book(table, {sheet: "Data Errors"});
    XLSX.writeFile(wb, 'HR_데이터_오류_리포트_2025_09.xlsx');
}
</script>
```

---

## 공통 CSS 스타일 (Common CSS Styles)

모든 KPI 모달에서 사용되는 공통 CSS 스타일입니다.

```css
/* ========================================
   모달 기본 스타일 / Modal Base Styles
   ======================================== */

.modal-content {
    border-radius: 15px;
    border: none;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.modal-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 15px 15px 0 0;
    padding: 25px 30px;
    border-bottom: none;
}

.modal-title {
    font-size: 24px;
    font-weight: bold;
    display: flex;
    align-items: center;
    gap: 10px;
}

.modal-body {
    padding: 30px;
    max-height: 70vh;
    overflow-y: auto;
}

.modal-body::-webkit-scrollbar {
    width: 8px;
}

.modal-body::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

.modal-body::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
}

/* ========================================
   Stat Grid Layouts
   ======================================== */

.modal-stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-bottom: 30px;
}

.modal-stat-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    display: flex;
    align-items: center;
    gap: 15px;
    transition: transform 0.3s, box-shadow 0.3s;
}

.modal-stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.12);
}

.stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    flex-shrink: 0;
}

.stat-info {
    flex: 1;
}

.stat-value {
    font-size: 28px;
    font-weight: bold;
    color: #1a1a1a;
    line-height: 1.2;
}

.stat-label {
    font-size: 13px;
    color: #555;
    font-weight: 600;
    margin-top: 4px;
}

.stat-sublabel {
    font-size: 11px;
    color: #888;
    margin-top: 2px;
}

.stat-change {
    display: inline-block;
    margin-top: 8px;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: bold;
}

.stat-change.positive {
    background: #d4edda;
    color: #155724;
}

.stat-change.negative {
    background: #f8d7da;
    color: #721c24;
}

.stat-change.neutral {
    background: #e2e3e5;
    color: #383d41;
}

/* ========================================
   Chart Containers
   ======================================== */

.trend-chart-container,
.comparison-chart-container,
.distribution-chart-container {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}

.trend-chart-container h6,
.comparison-chart-container h6,
.distribution-chart-container h6 {
    font-size: 15px;
    font-weight: bold;
    color: #333;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e9ecef;
}

.trend-chart-container canvas,
.comparison-chart-container canvas,
.distribution-chart-container canvas {
    max-height: 300px;
}

/* ========================================
   Table Styles
   ======================================== */

.table-responsive {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.sortable-table {
    margin-bottom: 0;
}

.sortable-table thead th {
    cursor: pointer;
    user-select: none;
    position: relative;
    padding: 12px 15px;
    font-size: 12px;
    line-height: 1.4;
}

.sortable-table thead th:hover {
    background: #e9ecef;
}

.sortable-table thead th::after {
    content: ' ⇅';
    opacity: 0.3;
    font-size: 10px;
}

.sticky-header {
    position: sticky;
    top: 0;
    background: #f8f9fa;
    z-index: 10;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.table-hover tbody tr:hover {
    background-color: rgba(102, 126, 234, 0.05);
    cursor: pointer;
}

.table-footer {
    background: #f8f9fa;
    padding: 12px 15px;
    border-radius: 0 0 12px 12px;
    font-size: 13px;
    color: #666;
    text-align: center;
}

/* ========================================
   Employee Cell Styles
   ======================================== */

.employee-cell {
    display: flex;
    flex-direction: column;
}

.employee-name {
    font-weight: 600;
    color: #333;
    font-size: 13px;
}

.employee-id {
    font-size: 11px;
    color: #888;
    margin-top: 2px;
}

/* ========================================
   Badge Styles
   ======================================== */

.badge {
    font-size: 10px;
    padding: 4px 8px;
    font-weight: 600;
}

.type-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: bold;
}

.type-badge.type1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.type-badge.type2 {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
}

.type-badge.type3 {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
}

/* ========================================
   Timeline Styles
   ======================================== */

.timeline {
    position: relative;
    padding-left: 40px;
}

.timeline::before {
    content: '';
    position: absolute;
    left: 10px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.timeline-item {
    position: relative;
    margin-bottom: 20px;
    padding: 15px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: -34px;
    top: 20px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #667eea;
    border: 3px solid white;
    box-shadow: 0 0 0 2px #667eea;
}

.timeline-date {
    font-size: 11px;
    color: #888;
    margin-bottom: 5px;
}

.timeline-content {
    font-size: 13px;
    color: #333;
}

/* ========================================
   Heatmap Calendar Styles
   ======================================== */

.heatmap-calendar {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 4px;
    margin-top: 10px;
}

.heatmap-day {
    aspect-ratio: 1;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: bold;
    cursor: pointer;
    transition: transform 0.2s;
}

.heatmap-day:hover {
    transform: scale(1.1);
    z-index: 10;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.heatmap-day.level-0 { background: #ebedf0; color: #333; }
.heatmap-day.level-1 { background: #c6e48b; color: #333; }
.heatmap-day.level-2 { background: #7bc96f; color: white; }
.heatmap-day.level-3 { background: #239a3b; color: white; }
.heatmap-day.level-4 { background: #196127; color: white; }

/* ========================================
   Risk Card Styles
   ======================================== */

.risk-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin: 20px 0;
}

.risk-card {
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.risk-card:hover {
    transform: translateY(-5px);
}

.risk-card.high {
    background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
    border-left: 4px solid #dc3545;
}

.risk-card.medium {
    background: linear-gradient(135deg, #fffef5 0%, #fff4d6 100%);
    border-left: 4px solid #ffc107;
}

.risk-card.low {
    background: linear-gradient(135deg, #f0fff4 0%, #d4f4dd 100%);
    border-left: 4px solid #28a745;
}

.risk-icon {
    font-size: 36px;
    margin-bottom: 10px;
}

.risk-label {
    font-size: 14px;
    font-weight: bold;
    color: #333;
    margin-bottom: 5px;
}

.risk-count {
    font-size: 32px;
    font-weight: bold;
    color: #1a1a1a;
}

/* ========================================
   Accordion Styles
   ======================================== */

.accordion-button {
    font-size: 14px;
    font-weight: 600;
    color: #333;
}

.accordion-button:not(.collapsed) {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    color: #1565c0;
}

.accordion-body {
    font-size: 13px;
    line-height: 1.6;
}

/* ========================================
   Animation Keyframes
   ======================================== */

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeIn 0.5s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.slide-in {
    animation: slideIn 0.4s ease-out;
}

/* ========================================
   Responsive Design
   ======================================== */

@media (max-width: 768px) {
    .modal-stat-grid {
        grid-template-columns: 1fr;
    }

    .risk-grid,
    .severity-cards-grid {
        grid-template-columns: 1fr;
    }

    .heatmap-calendar {
        grid-template-columns: repeat(7, 1fr);
        gap: 2px;
    }

    .heatmap-day {
        font-size: 9px;
    }
}
```

---

## 공통 JavaScript 함수 (Common JavaScript Functions)

모든 KPI 모달에서 재사용 가능한 JavaScript 함수들입니다.

```javascript
/* ========================================
   Table Sorting Function
   ======================================== */

function sortTable(header, columnIndex) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // 현재 정렬 방향 확인
    const currentDirection = header.dataset.sortDirection || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

    // 모든 헤더의 정렬 표시 초기화
    table.querySelectorAll('th').forEach(th => {
        th.dataset.sortDirection = '';
        th.style.background = '';
    });

    // 현재 헤더 정렬 방향 설정
    header.dataset.sortDirection = newDirection;
    header.style.background = '#e9ecef';

    // 행 정렬
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();

        // 숫자 감지 (쉼표, % 제거)
        const aNum = parseFloat(aValue.replace(/,/g, '').replace(/%/g, ''));
        const bNum = parseFloat(bValue.replace(/,/g, '').replace(/%/g, ''));

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
        } else {
            return newDirection === 'asc'
                ? aValue.localeCompare(bValue, 'vi')
                : bValue.localeCompare(aValue, 'vi');
        }
    });

    // 정렬된 행 다시 추가
    rows.forEach(row => tbody.appendChild(row));
}

/* ========================================
   Table Filtering Function
   ======================================== */

function filterTableBySearchAndFilters(tableId, searchInputId, filterIds, counterId) {
    const searchText = document.getElementById(searchInputId).value.toLowerCase();
    const filters = {};

    filterIds.forEach(filterId => {
        filters[filterId] = document.getElementById(filterId).value;
    });

    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tbody tr');
    let visibleCount = 0;

    rows.forEach(row => {
        const cells = Array.from(row.cells).map(cell => cell.textContent.toLowerCase());

        // 검색어 매칭
        const matchSearch = searchText === '' || cells.some(cell => cell.includes(searchText));

        // 필터 매칭
        let matchFilters = true;
        for (const [filterId, filterValue] of Object.entries(filters)) {
            if (filterValue !== '') {
                const filterIndex = parseInt(filterId.split('_')[1] || 0);
                matchFilters = matchFilters && cells[filterIndex].includes(filterValue.toLowerCase());
            }
        }

        if (matchSearch && matchFilters) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    if (counterId) {
        document.getElementById(counterId).textContent =
            `총 ${visibleCount}명 표시 / Showing ${visibleCount} employees`;
    }
}

/* ========================================
   Accordion Toggle Function
   ======================================== */

function toggleAccordion(accordionId) {
    const accordion = document.getElementById(accordionId);
    const isOpen = accordion.classList.contains('show');

    // Bootstrap collapse 사용
    const bsCollapse = new bootstrap.Collapse(accordion, {
        toggle: true
    });
}

/* ========================================
   Excel Export Function (using SheetJS)
   ======================================== */

function exportTableToExcel(tableId, filename) {
    // SheetJS (xlsx.full.min.js) 라이브러리 필요
    const table = document.getElementById(tableId);
    const wb = XLSX.utils.table_to_book(table, {sheet: "Sheet1"});
    XLSX.writeFile(wb, filename);
}

/* ========================================
   Chart Creation Helpers
   ======================================== */

function createTrendChart(canvasId, labels, datasets, yAxisLabel = '') {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // 기존 차트 파괴 (중요!)
    if (window[canvasId + '_chart']) {
        window[canvasId + '_chart'].destroy();
    }

    window[canvasId + '_chart'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { size: 11 } }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: yAxisLabel !== '',
                        text: yAxisLabel
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function createComparisonChart(canvasId, labels, data, label, chartType = 'bar') {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // 기존 차트 파괴
    if (window[canvasId + '_chart']) {
        window[canvasId + '_chart'].destroy();
    }

    window[canvasId + '_chart'] = new Chart(ctx, {
        type: chartType,
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: chartType === 'bar'
                    ? 'rgba(102, 126, 234, 0.7)'
                    : data.map((_, i) => `hsl(${i * 30}, 70%, 60%)`),
                borderColor: chartType === 'bar'
                    ? '#667eea'
                    : '#fff',
                borderWidth: chartType === 'bar' ? 1 : 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: chartType !== 'bar',
                    position: 'bottom'
                }
            },
            scales: chartType === 'bar' ? {
                y: { beginAtZero: true }
            } : {}
        }
    });
}

/* ========================================
   Modal Show/Hide Handlers
   ======================================== */

function showKPIModal(kpiNumber) {
    const modalId = `kpiModal${kpiNumber}`;
    const modal = new bootstrap.Modal(document.getElementById(modalId));

    // 데이터 로드 (필요 시)
    loadKPIModalData(kpiNumber);

    modal.show();
}

function loadKPIModalData(kpiNumber) {
    // AJAX 또는 로컬 JSON에서 상세 데이터 로드
    // 예: fetch(`/api/kpi/${kpiNumber}/details`)
    //     .then(response => response.json())
    //     .then(data => populateModalWithData(kpiNumber, data));
}

/* ========================================
   Date Formatting Helper
   ======================================== */

function formatDate(dateString, locale = 'ko-KR') {
    const date = new Date(dateString);
    return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

function calculateDaysBetween(date1, date2) {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    const diffTime = Math.abs(d2 - d1);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

/* ========================================
   Number Formatting Helper
   ======================================== */

function formatNumber(num, decimals = 0) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatCurrency(amount, currency = 'VND') {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0
    }).format(amount);
}

/* ========================================
   Heatmap Calendar Generator
   ======================================== */

function generateHeatmapCalendar(containerId, year, month, dataMap) {
    const container = document.getElementById(containerId);
    const daysInMonth = new Date(year, month, 0).getDate();
    const firstDayOfWeek = new Date(year, month - 1, 1).getDay();

    container.innerHTML = '';

    // 요일 헤더
    const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
    weekdays.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'heatmap-weekday-header';
        dayHeader.textContent = day;
        container.appendChild(dayHeader);
    });

    // 빈 칸 (월 시작 전)
    for (let i = 0; i < firstDayOfWeek; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'heatmap-day empty';
        container.appendChild(emptyDay);
    }

    // 일별 데이터
    for (let day = 1; day <= daysInMonth; day++) {
        const dayDiv = document.createElement('div');
        const dateKey = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const value = dataMap[dateKey] || 0;

        // 레벨 결정 (0-4)
        const level = value === 0 ? 0 : Math.min(Math.floor(value / 5) + 1, 4);

        dayDiv.className = `heatmap-day level-${level}`;
        dayDiv.textContent = day;
        dayDiv.title = `${dateKey}: ${value}건`;

        container.appendChild(dayDiv);
    }
}

/* ========================================
   Risk Score Calculator
   ======================================== */

function calculateRiskScore(employee) {
    let score = 0;

    // 출근율 (30%)
    const attendanceRate = parseFloat(employee.attendance_rate || 100);
    if (attendanceRate < 95) {
        score += (95 - attendanceRate) * 0.3;
    }

    // 교육 참여도 (25%)
    const trainingRate = parseFloat(employee.training_participation || 100);
    if (trainingRate < 80) {
        score += (80 - trainingRate) * 0.25;
    }

    // 멘토 피드백 (25%)
    const mentorFeedback = employee.mentor_feedback || 'positive';
    if (mentorFeedback === 'negative') {
        score += 25;
    } else if (mentorFeedback === 'neutral') {
        score += 12.5;
    }

    // 무단결근 (20%)
    const unauthorizedAbsences = parseInt(employee.unauthorized_absences || 0);
    score += unauthorizedAbsences * 20;

    return Math.min(Math.round(score), 100);
}

function getRiskLevel(score) {
    if (score >= 70) return { level: 'high', label: '높음 / High', color: '#dc3545' };
    if (score >= 40) return { level: 'medium', label: '보통 / Medium', color: '#ffc107' };
    return { level: 'low', label: '낮음 / Low', color: '#28a745' };
}
```

---

## 최종 통합 가이드 (Final Integration Guide)

### 구현 순서 (Implementation Order)

1. **공통 CSS 및 JavaScript 통합**
   - 모든 공통 스타일을 `<style>` 태그로 헤더에 추가
   - 모든 공통 함수를 `<script>` 태그로 추가

2. **KPI 모달 HTML 생성**
   - 각 KPI별로 모달 HTML 구조 생성
   - ID 규칙: `kpiModal1`, `kpiModal2`, ..., `kpiModal11`

3. **데이터 로딩 로직 구현**
   - Python에서 JSON 데이터 준비
   - JavaScript 변수로 임베드

4. **차트 초기화**
   - Chart.js 차트 생성 함수 호출
   - 기존 차트 파괴 후 재생성 (중요!)

5. **이벤트 리스너 등록**
   - 검색/필터 입력 이벤트
   - 정렬 클릭 이벤트
   - 모달 오픈 이벤트

### 데이터 준비 체크리스트

✅ Basic Manpower Data (July, August, September)
✅ Attendance Data (July, August, September)
✅ AQL History (May~September)
✅ 5PRS Data (July, August, September)
✅ Position Condition Matrix JSON
✅ Dashboard Translations JSON

### 성능 최적화 팁

1. **차트 인스턴스 관리**: 항상 기존 차트를 `destroy()` 후 재생성
2. **테이블 가상화**: 큰 테이블은 가상 스크롤링 고려 (Virtualized Table)
3. **지연 로딩**: 모달이 열릴 때 데이터 로드 (AJAX 또는 사전 임베드)
4. **캐싱**: 한 번 계산한 결과는 변수에 저장하여 재사용

---

**문서 작성 완료!** 🎉

이제 KPI 1~11번까지 모든 모달의 상세 설계가 완료되었습니다.
- Part 1: KPI 1-4
- Part 2: KPI 5-9
- Part 3: KPI 10-11 + 공통 CSS + 공통 JavaScript

다음 단계는 실제 구현 단계로 진행하시면 됩니다!
