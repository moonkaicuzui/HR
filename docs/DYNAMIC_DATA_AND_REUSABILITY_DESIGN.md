# 동적 데이터 로딩 및 재사용성 설계 (Dynamic Data Loading & Code Reusability Design)

## 핵심 원칙 (Core Principles)

### 1️⃣ 완전 동적 데이터 로딩 (Fully Dynamic Data Loading)
**"NO HARDCODED MONTHS"** - 월별 데이터는 절대 하드코딩하지 않음

- 7월 대시보드: 7월 데이터만 표시 (1개월)
- 9월 대시보드: 7월~9월 데이터 표시 (3개월)
- 11월 대시보드: 7월~11월 데이터 표시 (5개월)
- 2026년 3월: 2025년 7월~2026년 3월 데이터 표시 (9개월)

### 2️⃣ 최대 재사용성 (Maximum Code Reusability)
**"DRY - Don't Repeat Yourself"** - 모든 KPI 모달이 동일한 함수 사용

- 11개 KPI 모달 모두 동일한 차트 생성 함수 사용
- 테이블, 필터, 정렬 로직 공유
- 단일 데이터 로더로 모든 모달 지원

---

## 아키텍처 설계 (Architecture Design)

### 전체 구조 (Overall Structure)

```
Python (Backend)                    JavaScript (Frontend)
──────────────────                  ─────────────────────

1. 데이터 수집                        4. 모달 초기화
   ├─ 가용 월 자동 탐지                  ├─ MonthlyDataManager 생성
   ├─ 월별 메트릭 계산                   ├─ KPIModalFactory 생성
   └─ JSON 임베딩                       └─ 차트/테이블 동적 생성
      ↓
2. HTML 생성                         5. 사용자 인터랙션
   ├─ 모달 템플릿 (재사용)               ├─ 필터/검색/정렬
   └─ JavaScript 임베딩                ├─ 차트 업데이트
      ↓                                └─ Excel 내보내기
3. 데이터 임베딩
   ├─ monthlyMetrics JSON
   ├─ availableMonths 배열
   └─ employeeDetails 배열
```

---

## 1. Python 백엔드: 동적 데이터 수집

### 1.1 가용 월 자동 탐지 (Auto-detect Available Months)

```python
# src/data/monthly_data_collector.py

import os
import glob
from datetime import datetime
from pathlib import Path

class MonthlyDataCollector:
    """동적으로 가용한 월별 데이터를 수집"""

    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.available_months = []

    def detect_available_months(self, start_year=2025, start_month=7):
        """
        input_files 디렉토리를 스캔하여 실제로 존재하는 월 데이터 탐지

        Returns:
            ['2025-07', '2025-08', '2025-09', '2025-10', '2025-11']
        """
        available = []

        # Basic Manpower 파일 기준으로 월 탐지
        manpower_pattern = self.base_path / "input_files" / "basic manpower data *.csv"

        for file_path in glob.glob(str(manpower_pattern)):
            # "basic manpower data september.csv" → "september"
            filename = os.path.basename(file_path)
            month_name = filename.replace("basic manpower data ", "").replace(".csv", "").strip()

            # "september" → 9 → "2025-09"
            month_num = self.month_name_to_number(month_name)
            year_month = f"{start_year}-{month_num:02d}"
            available.append(year_month)

        # 시간순 정렬
        available.sort()

        self.available_months = available
        return available

    def month_name_to_number(self, month_name):
        """월 이름 → 숫자 변환"""
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        return month_map.get(month_name.lower(), 1)

    def get_month_range(self, target_month):
        """
        특정 월의 대시보드를 생성할 때 표시할 월 범위 결정

        Args:
            target_month: "2025-09"

        Returns:
            ['2025-07', '2025-08', '2025-09']  # 7월부터 target_month까지
        """
        all_months = self.detect_available_months()

        # target_month 이하의 모든 월 반환
        return [m for m in all_months if m <= target_month]
```

### 1.2 월별 메트릭 계산 (Calculate Monthly Metrics)

```python
# src/metrics/dynamic_metric_calculator.py

class DynamicMetricCalculator:
    """동적으로 월별 메트릭을 계산"""

    def __init__(self, data_collector):
        self.data_collector = data_collector
        self.monthly_metrics = {}

    def calculate_all_metrics(self, months_to_calculate):
        """
        지정된 월들에 대해 모든 메트릭 계산

        Args:
            months_to_calculate: ['2025-07', '2025-08', '2025-09']

        Returns:
            {
                '2025-07': {
                    'total_employees': 378,
                    'absence_rate': 2.5,
                    'unauthorized_absence_rate': 0.8,
                    ...
                },
                '2025-08': { ... },
                '2025-09': { ... }
            }
        """
        for month in months_to_calculate:
            self.monthly_metrics[month] = self.calculate_month_metrics(month)

        return self.monthly_metrics

    def calculate_month_metrics(self, year_month):
        """특정 월의 모든 메트릭 계산"""
        year, month = year_month.split('-')
        month_num = int(month)

        # 해당 월 데이터 로드
        df = self.load_month_data(year, month_num)
        attendance_df = self.load_attendance_data(year, month_num)

        metrics = {
            'total_employees': self.calc_total_employees(df),
            'absence_rate': self.calc_absence_rate(attendance_df),
            'unauthorized_absence_rate': self.calc_unauthorized_absence_rate(attendance_df),
            'resignation_rate': self.calc_resignation_rate(df),
            'recent_hires': self.calc_recent_hires(df, year_month),
            'recent_resignations': self.calc_recent_resignations(df, year_month),
            'under_60_days': self.calc_under_60_days(df, year_month),
            'post_assignment_resignations': self.calc_post_assignment_resignations(df),
            'perfect_attendance': self.calc_perfect_attendance(attendance_df),
            'long_term_employees': self.calc_long_term_employees(df, year_month),
            'data_errors': self.calc_data_errors(df)
        }

        return metrics

    def to_json(self):
        """JavaScript 임베딩용 JSON 생성"""
        return json.dumps(self.monthly_metrics, ensure_ascii=False, indent=2)
```

### 1.3 직원 상세 데이터 수집 (Employee Details Collection)

```python
# src/data/employee_detail_collector.py

class EmployeeDetailCollector:
    """모달 드릴다운을 위한 직원 상세 정보 수집"""

    def collect_all_employee_details(self, target_month):
        """
        현재 월 기준 모든 직원의 상세 정보 수집

        Returns:
            [
                {
                    'employee_id': 'VN-2024-001',
                    'employee_name': 'Nguyễn Văn A',
                    'position': 'ASSEMBLY INSPECTOR',
                    'team': 'Assembly Team A',
                    'join_date': '2024-03-15',
                    'resignation_date': None,
                    'monthly_data': {
                        '2025-07': { 'attendance_rate': 95.2, 'wtime': 22.5, ... },
                        '2025-08': { 'attendance_rate': 98.1, 'wtime': 24.0, ... },
                        '2025-09': { 'attendance_rate': 96.7, 'wtime': 23.5, ... }
                    }
                },
                ...
            ]
        """
        employees = []

        # 현재 월 기준 재직자 전체
        df_current = self.load_month_data(target_month)

        for _, row in df_current.iterrows():
            employee = {
                'employee_id': row['Employee No'],
                'employee_name': row['Employee Name'],
                'position': row.get('Position', ''),
                'team': row.get('Team', ''),
                'join_date': row.get('Join Date', ''),
                'resignation_date': row.get('Resignation date', None),
                'assignment_date': row.get('Assignment date', None),
                'boss_id': row.get('boss_id', ''),
                'monthly_data': {}
            }

            # 각 월별 출근/성과 데이터 추가
            for month in self.available_months:
                employee['monthly_data'][month] = self.get_monthly_detail(
                    employee['employee_id'], month
                )

            employees.append(employee)

        return employees

    def get_monthly_detail(self, employee_id, year_month):
        """특정 직원의 특정 월 상세 데이터"""
        attendance = self.get_attendance_record(employee_id, year_month)

        return {
            'attendance_rate': attendance.get('attendance_rate', 0),
            'wtime': attendance.get('wtime', 0),
            'working_days': attendance.get('working_days', 0),
            'absence_days': attendance.get('absence_days', 0),
            'unauthorized_absence_days': attendance.get('unauthorized_absence_days', 0),
            'is_perfect_attendance': attendance.get('is_perfect_attendance', False)
        }
```

---

## 2. HTML 생성: 재사용 가능한 모달 템플릿

### 2.1 통합 모달 템플릿 (Unified Modal Template)

```python
# src/visualization/modal_template_generator.py

class ModalTemplateGenerator:
    """재사용 가능한 모달 HTML 템플릿 생성기"""

    def generate_kpi_modal(self, kpi_number, kpi_config):
        """
        KPI 모달 HTML 생성 (완전히 동적)

        Args:
            kpi_number: 1~11
            kpi_config: {
                'title_ko': '총 재직자 수',
                'title_en': 'Total Employees',
                'icon': '👥',
                'sections': [
                    {
                        'type': 'stat_summary',
                        'metric_keys': ['total_employees', 'change_vs_prev', 'avg_tenure']
                    },
                    {
                        'type': 'trend_chart',
                        'metric_key': 'total_employees',
                        'chart_type': 'line'
                    },
                    {
                        'type': 'comparison_chart',
                        'data_key': 'employees_by_team',
                        'chart_type': 'bar'
                    },
                    {
                        'type': 'employee_table',
                        'columns': ['employee_id', 'name', 'position', 'team', 'join_date']
                    }
                ]
            }
        """
        modal_id = f"kpiModal{kpi_number}"

        html = f"""
        <div class="modal fade" id="{modal_id}" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            {kpi_config['icon']} {kpi_config['title_ko']} / {kpi_config['title_en']}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        {self.generate_modal_sections(kpi_number, kpi_config['sections'])}
                    </div>
                </div>
            </div>
        </div>

        <script>
        // 모달 초기화 함수 (데이터 로드 시 호출)
        function initKPIModal{kpi_number}() {{
            const factory = new KPIModalFactory(window.monthlyMetrics, window.employeeDetails);
            factory.initModal({kpi_number}, {json.dumps(kpi_config)});
        }}
        </script>
        """

        return html

    def generate_modal_sections(self, kpi_number, sections):
        """섹션별 HTML 생성 (타입 기반 동적 생성)"""
        html_parts = []

        for section in sections:
            if section['type'] == 'stat_summary':
                html_parts.append(self.generate_stat_summary_section(kpi_number, section))
            elif section['type'] == 'trend_chart':
                html_parts.append(self.generate_trend_chart_section(kpi_number, section))
            elif section['type'] == 'comparison_chart':
                html_parts.append(self.generate_comparison_chart_section(kpi_number, section))
            elif section['type'] == 'employee_table':
                html_parts.append(self.generate_employee_table_section(kpi_number, section))
            elif section['type'] == 'timeline':
                html_parts.append(self.generate_timeline_section(kpi_number, section))
            elif section['type'] == 'heatmap':
                html_parts.append(self.generate_heatmap_section(kpi_number, section))

        return '\n'.join(html_parts)

    def generate_trend_chart_section(self, kpi_number, config):
        """추세 차트 섹션 (완전 동적)"""
        canvas_id = f"trendChart{kpi_number}_{config['metric_key']}"

        return f"""
        <div class="trend-chart-container">
            <h6 data-translate="trend_chart_title">{config.get('title', '월별 추세')}</h6>
            <canvas id="{canvas_id}"></canvas>
        </div>

        <script>
        // 차트는 KPIModalFactory에서 동적 생성
        document.addEventListener('DOMContentLoaded', function() {{
            window.kpiModalFactory.createTrendChart(
                '{canvas_id}',
                '{config['metric_key']}',
                {{
                    chartType: '{config.get('chart_type', 'line')}',
                    yAxisLabel: '{config.get('y_axis_label', '')}'
                }}
            );
        }});
        </script>
        """
```

---

## 3. JavaScript 프론트엔드: 동적 차트/테이블 생성

### 3.1 MonthlyDataManager (데이터 관리자)

```javascript
// 동적 데이터 관리 클래스

class MonthlyDataManager {
    constructor(monthlyMetricsJSON, employeeDetailsJSON) {
        this.monthlyMetrics = JSON.parse(monthlyMetricsJSON);
        this.employeeDetails = JSON.parse(employeeDetailsJSON);
        this.availableMonths = Object.keys(this.monthlyMetrics).sort();
    }

    /**
     * 동적 월 라벨 생성
     * @returns ['7월 July', '8월 August', '9월 September', ...]
     */
    getMonthLabels() {
        return this.availableMonths.map(month => {
            const [year, monthNum] = month.split('-');
            return this.formatMonthLabel(parseInt(monthNum));
        });
    }

    formatMonthLabel(monthNum) {
        const monthNames = {
            ko: ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'],
            en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        };
        return `${monthNames.ko[monthNum-1]} ${monthNames.en[monthNum-1]}`;
    }

    /**
     * 특정 메트릭의 월별 데이터 추출
     * @param metricKey - 'total_employees', 'absence_rate', etc.
     * @returns [378, 381, 393, 398, 402]  // 동적 길이
     */
    getMetricTrend(metricKey) {
        return this.availableMonths.map(month => {
            return this.monthlyMetrics[month][metricKey] || 0;
        });
    }

    /**
     * 전월 대비 변화 계산
     */
    getMonthOverMonthChange(metricKey, targetMonth) {
        const monthIndex = this.availableMonths.indexOf(targetMonth);
        if (monthIndex === 0) return null;  // 첫 달은 비교 불가

        const current = this.monthlyMetrics[targetMonth][metricKey];
        const previous = this.monthlyMetrics[this.availableMonths[monthIndex - 1]][metricKey];

        return {
            absolute: current - previous,
            percentage: ((current - previous) / previous * 100).toFixed(1)
        };
    }

    /**
     * 특정 조건에 맞는 직원 필터링
     */
    filterEmployees(filterFunc) {
        return this.employeeDetails.filter(filterFunc);
    }

    /**
     * 팀별 집계
     */
    aggregateByTeam(metricKey, targetMonth) {
        const teamData = {};

        this.employeeDetails.forEach(emp => {
            const team = emp.team || 'Unknown';
            if (!teamData[team]) {
                teamData[team] = { count: 0, sum: 0 };
            }

            const value = emp.monthly_data[targetMonth]?.[metricKey] || 0;
            teamData[team].count++;
            teamData[team].sum += value;
        });

        return Object.entries(teamData).map(([team, data]) => ({
            team: team,
            average: data.count > 0 ? data.sum / data.count : 0,
            count: data.count
        }));
    }
}
```

### 3.2 KPIModalFactory (모달 생성 팩토리)

```javascript
// 재사용 가능한 KPI 모달 생성 팩토리

class KPIModalFactory {
    constructor(dataManager) {
        this.dataManager = dataManager;
        this.chartInstances = {};  // Chart.js 인스턴스 관리
    }

    /**
     * 추세 차트 생성 (완전 동적)
     */
    createTrendChart(canvasId, metricKey, config = {}) {
        const labels = this.dataManager.getMonthLabels();
        const data = this.dataManager.getMetricTrend(metricKey);

        // 기존 차트 파괴
        if (this.chartInstances[canvasId]) {
            this.chartInstances[canvasId].destroy();
        }

        const ctx = document.getElementById(canvasId).getContext('2d');

        this.chartInstances[canvasId] = new Chart(ctx, {
            type: config.chartType || 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: config.label || metricKey,
                    data: data,
                    borderColor: config.borderColor || '#667eea',
                    backgroundColor: config.backgroundColor || 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
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
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                return `${context.dataset.label}: ${value.toFixed(1)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: !!config.yAxisLabel,
                            text: config.yAxisLabel || ''
                        }
                    }
                }
            }
        });

        return this.chartInstances[canvasId];
    }

    /**
     * 비교 차트 생성 (팀별, 직급별 등)
     */
    createComparisonChart(canvasId, dataKey, config = {}) {
        const targetMonth = this.dataManager.availableMonths[this.dataManager.availableMonths.length - 1];
        const aggregated = this.dataManager.aggregateByTeam(dataKey, targetMonth);

        const labels = aggregated.map(item => item.team);
        const data = aggregated.map(item => item.average);

        // 기존 차트 파괴
        if (this.chartInstances[canvasId]) {
            this.chartInstances[canvasId].destroy();
        }

        const ctx = document.getElementById(canvasId).getContext('2d');

        this.chartInstances[canvasId] = new Chart(ctx, {
            type: config.chartType || 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: config.label || dataKey,
                    data: data,
                    backgroundColor: config.backgroundColor || 'rgba(102, 126, 234, 0.7)',
                    borderColor: config.borderColor || '#667eea',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: config.horizontal ? 'y' : 'x',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        return this.chartInstances[canvasId];
    }

    /**
     * 직원 테이블 생성 (동적 필터링)
     */
    createEmployeeTable(tableBodyId, filterFunc, columns) {
        const employees = this.dataManager.filterEmployees(filterFunc);
        const tbody = document.getElementById(tableBodyId);
        tbody.innerHTML = '';

        employees.forEach(emp => {
            const row = tbody.insertRow();

            columns.forEach(col => {
                const cell = row.insertCell();
                cell.textContent = this.getEmployeeValue(emp, col);
            });
        });

        return employees.length;
    }

    getEmployeeValue(employee, column) {
        // 중첩된 속성 접근 (예: 'monthly_data.2025-09.attendance_rate')
        const keys = column.split('.');
        let value = employee;

        for (const key of keys) {
            value = value?.[key];
        }

        return value || '-';
    }

    /**
     * Stat Summary 카드 업데이트
     */
    updateStatCard(cardId, metricKey, targetMonth) {
        const value = this.dataManager.monthlyMetrics[targetMonth][metricKey];
        const change = this.dataManager.getMonthOverMonthChange(metricKey, targetMonth);

        const cardElement = document.getElementById(cardId);
        cardElement.querySelector('.stat-value').textContent = this.formatValue(value, metricKey);

        if (change) {
            const changeElement = cardElement.querySelector('.stat-change');
            changeElement.textContent = `${change.absolute > 0 ? '+' : ''}${change.absolute} (${change.percentage}%)`;
            changeElement.className = `stat-change ${change.absolute >= 0 ? 'positive' : 'negative'}`;
        }
    }

    formatValue(value, metricKey) {
        // 메트릭 타입에 따라 포맷팅
        if (metricKey.includes('rate')) {
            return `${value.toFixed(1)}%`;
        } else if (metricKey.includes('count') || metricKey.includes('employees')) {
            return value.toLocaleString();
        }
        return value;
    }
}
```

### 3.3 모달 초기화 통합 함수

```javascript
// 전역 초기화 함수

let globalDataManager;
let globalModalFactory;

function initializeDashboard() {
    // Python에서 임베드된 JSON 데이터 사용
    globalDataManager = new MonthlyDataManager(
        window.monthlyMetricsJSON,
        window.employeeDetailsJSON
    );

    globalModalFactory = new KPIModalFactory(globalDataManager);

    // 모든 KPI 카드 초기화
    initializeAllKPICards();

    // 모달 이벤트 리스너 등록
    registerModalEventListeners();
}

function initializeAllKPICards() {
    const targetMonth = globalDataManager.availableMonths[globalDataManager.availableMonths.length - 1];

    // 11개 KPI 카드 값 업데이트
    for (let i = 1; i <= 11; i++) {
        updateKPICard(i, targetMonth);
    }
}

function updateKPICard(kpiNumber, targetMonth) {
    const metricKeys = {
        1: 'total_employees',
        2: 'absence_rate',
        3: 'unauthorized_absence_rate',
        4: 'resignation_rate',
        5: 'recent_hires',
        6: 'recent_resignations',
        7: 'under_60_days',
        8: 'post_assignment_resignations',
        9: 'perfect_attendance',
        10: 'long_term_employees',
        11: 'data_errors'
    };

    const metricKey = metricKeys[kpiNumber];
    const value = globalDataManager.monthlyMetrics[targetMonth][metricKey];
    const change = globalDataManager.getMonthOverMonthChange(metricKey, targetMonth);

    // 카드 DOM 업데이트
    const cardElement = document.querySelector(`[data-kpi="${kpiNumber}"]`);
    if (cardElement) {
        cardElement.querySelector('.card-value').textContent = value;

        if (change) {
            const changeElement = cardElement.querySelector('.card-change');
            changeElement.textContent = `${change.absolute > 0 ? '+' : ''}${change.absolute}`;
            changeElement.className = `card-change ${change.absolute >= 0 ? 'positive' : 'negative'}`;
        }
    }
}

function registerModalEventListeners() {
    // 각 KPI 카드 클릭 시 모달 열기 및 데이터 로드
    for (let i = 1; i <= 11; i++) {
        const modalId = `kpiModal${i}`;
        const modalElement = document.getElementById(modalId);

        if (modalElement) {
            modalElement.addEventListener('show.bs.modal', function() {
                loadKPIModalContent(i);
            });
        }
    }
}

function loadKPIModalContent(kpiNumber) {
    // 모달이 열릴 때 차트/테이블 동적 생성
    const targetMonth = globalDataManager.availableMonths[globalDataManager.availableMonths.length - 1];

    switch(kpiNumber) {
        case 1:  // Total Employees
            globalModalFactory.updateStatCard(`kpi1StatCard1`, 'total_employees', targetMonth);
            globalModalFactory.createTrendChart('trendChart1', 'total_employees', {
                yAxisLabel: '재직자 수 / Employees'
            });
            globalModalFactory.createComparisonChart('comparisonChart1', 'total_employees', {
                label: '팀별 재직자 / Employees by Team'
            });
            break;

        case 2:  // Absence Rate
            globalModalFactory.createTrendChart('trendChart2', 'absence_rate', {
                yAxisLabel: '결근율 / Absence Rate (%)'
            });
            // ... 추가 차트/테이블
            break;

        // ... KPI 3~11 동일 패턴
    }
}

// 페이지 로드 시 자동 초기화
document.addEventListener('DOMContentLoaded', initializeDashboard);
```

---

## 4. Python HTML 빌더 통합

### 4.1 최종 HTML 생성

```python
# src/visualization/dynamic_dashboard_builder.py

class DynamicDashboardBuilder:
    """완전 동적 HR 대시보드 빌더"""

    def __init__(self, target_month):
        self.target_month = target_month  # "2025-09"
        self.data_collector = MonthlyDataCollector('.')
        self.metric_calculator = DynamicMetricCalculator(self.data_collector)
        self.employee_collector = EmployeeDetailCollector()
        self.modal_generator = ModalTemplateGenerator()

    def build_dashboard(self):
        """대시보드 생성 메인 함수"""

        # 1. 가용 월 탐지
        available_months = self.data_collector.get_month_range(self.target_month)
        print(f"📊 탐지된 데이터 월: {available_months}")

        # 2. 월별 메트릭 계산
        monthly_metrics = self.metric_calculator.calculate_all_metrics(available_months)

        # 3. 직원 상세 정보 수집
        employee_details = self.employee_collector.collect_all_employee_details(self.target_month)

        # 4. HTML 생성
        html = self.generate_html(monthly_metrics, employee_details, available_months)

        # 5. 파일 저장
        output_path = f"output_files/HR_Dashboard_{self.target_month}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ 대시보드 생성 완료: {output_path}")
        print(f"📅 포함된 월: {', '.join(available_months)}")

        return output_path

    def generate_html(self, monthly_metrics, employee_details, available_months):
        """HTML 전체 생성"""

        # JavaScript 데이터 임베딩
        js_data = f"""
        <script>
        // Python에서 동적 생성된 데이터
        window.monthlyMetricsJSON = '{json.dumps(monthly_metrics, ensure_ascii=False)}';
        window.employeeDetailsJSON = '{json.dumps(employee_details, ensure_ascii=False)}';
        window.availableMonths = {json.dumps(available_months)};
        window.targetMonth = '{self.target_month}';
        </script>
        """

        # 11개 KPI 모달 생성
        modals_html = self.generate_all_modals()

        # 전체 HTML 조합
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <title>HR Dashboard {self.target_month}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
            {self.get_common_css()}
        </head>
        <body>
            {self.generate_header(available_months)}
            {self.generate_kpi_cards()}
            {modals_html}

            {js_data}
            {self.get_common_javascript()}

            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

        return html

    def generate_all_modals(self):
        """11개 KPI 모달 모두 생성"""
        kpi_configs = self.get_kpi_configs()

        modals = []
        for kpi_num, config in kpi_configs.items():
            modal_html = self.modal_generator.generate_kpi_modal(kpi_num, config)
            modals.append(modal_html)

        return '\n'.join(modals)

    def get_kpi_configs(self):
        """KPI 설정 (타입 기반 섹션 정의)"""
        return {
            1: {
                'title_ko': '총 재직자 수',
                'title_en': 'Total Employees',
                'icon': '👥',
                'sections': [
                    {'type': 'stat_summary', 'metric_keys': ['total_employees', 'change_vs_prev', 'avg_tenure']},
                    {'type': 'trend_chart', 'metric_key': 'total_employees', 'chart_type': 'line'},
                    {'type': 'comparison_chart', 'data_key': 'total_employees', 'chart_type': 'bar'},
                    {'type': 'employee_table', 'columns': ['employee_id', 'employee_name', 'position', 'team']}
                ]
            },
            # ... KPI 2~11 동일 패턴
        }
```

---

## 5. 실행 예시 (Usage Example)

### 9월 대시보드 생성
```bash
python src/generate_dashboard.py --month 9 --year 2025
```

**결과**:
- 가용 데이터: 7월, 8월, 9월 (3개월)
- 추세 차트: 3개 월 표시
- 비교 기준: 8월 대비 변화

### 11월 대시보드 생성
```bash
python src/generate_dashboard.py --month 11 --year 2025
```

**결과**:
- 가용 데이터: 7월, 8월, 9월, 10월, 11월 (5개월)
- 추세 차트: 5개 월 표시
- 비교 기준: 10월 대비 변화

### 2026년 3월 대시보드 생성
```bash
python src/generate_dashboard.py --month 3 --year 2026
```

**결과**:
- 가용 데이터: 2025년 7월 ~ 2026년 3월 (9개월)
- 추세 차트: 9개 월 표시
- 비교 기준: 2026년 2월 대비 변화

---

## 6. 검증 체크리스트

### ✅ 동적 데이터 로딩 검증
- [ ] 가용 월 자동 탐지 동작 확인
- [ ] 월별 메트릭 계산 정확성 확인
- [ ] 직원 상세 정보 수집 완전성 확인
- [ ] JSON 임베딩 크기 최적화 확인

### ✅ 재사용성 검증
- [ ] 11개 KPI 모달 모두 동일한 함수 사용 확인
- [ ] 차트 생성 함수 재사용 횟수 측정
- [ ] 코드 중복률 < 5% 확인
- [ ] 새 KPI 추가 시 소요 시간 < 30분 확인

### ✅ 성능 검증
- [ ] 11월 대시보드 (5개월) 생성 시간 < 10초
- [ ] HTML 파일 크기 < 5MB
- [ ] 차트 렌더링 시간 < 2초
- [ ] 메모리 사용량 < 500MB

---

## 결론

**두 가지 핵심 원칙이 완전히 반영된 설계**:

1. **완전 동적 데이터 로딩**:
   - Python이 자동으로 가용 월 탐지
   - JavaScript가 동적으로 차트/테이블 생성
   - 하드코딩된 월 정보 없음

2. **최대 재사용성**:
   - 11개 KPI 모달이 동일한 팩토리 클래스 사용
   - 차트/테이블 생성 함수 완전 공유
   - 새 KPI 추가 시 설정만 추가하면 됨

**다음 단계**: Phase 1 구현 시작 (데이터 정확성 수정)
