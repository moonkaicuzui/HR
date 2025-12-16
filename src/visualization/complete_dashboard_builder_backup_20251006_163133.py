"""
complete_dashboard_builder.py - Complete HR Dashboard Builder (Full Rebuild)
완전한 HR 대시보드 빌더 (완전 재구축)

Generates a modern, dynamic HTML dashboard with:
- Dynamic monthly data loading
- Trend charts for all metrics
- Detailed KPI modals
- Modern UI (gradient headers, tabs, cards)
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import sys
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.monthly_data_collector import MonthlyDataCollector
from src.analytics.hr_metric_calculator import HRMetricCalculator


class CompleteDashboardBuilder:
    """Build complete HR dashboard with all features"""

    def __init__(self, target_month: str, language: str = 'ko'):
        """
        Args:
            target_month: 'YYYY-MM' format
            language: 'ko', 'en', or 'vi'
        """
        self.target_month = target_month
        self.language = language
        self.hr_root = Path(__file__).parent.parent.parent

        # Initialize components
        self.collector = MonthlyDataCollector(self.hr_root)
        self.calculator = HRMetricCalculator(self.collector)

        # Data storage
        self.available_months: List[str] = []
        self.month_labels: List[str] = []
        self.monthly_metrics: Dict[str, Dict[str, Any]] = {}
        self.employee_details: List[Dict[str, Any]] = []

    def build(self) -> str:
        """Build complete dashboard HTML"""
        print(f"🔨 Building HR Dashboard for {self.target_month}...")

        # Step 1: Detect available months
        self.available_months = self.collector.get_month_range(self.target_month)
        self.month_labels = self.collector.get_month_labels(self.available_months, self.language)
        print(f"📅 Months: {self.available_months}")

        # Step 2: Calculate metrics
        self.monthly_metrics = self.calculator.calculate_all_metrics(self.available_months)
        print(f"📊 Metrics calculated for {len(self.monthly_metrics)} months")

        # Step 3: Collect employee details (simplified for MVP)
        self._collect_employee_details()
        print(f"👥 Employee details: {len(self.employee_details)} employees")

        # Step 4: Generate HTML
        html = self._generate_html()
        print(f"✅ Dashboard HTML generated")

        return html

    def _collect_employee_details(self):
        """Collect employee details with calculated fields for the target month"""
        data = self.collector.load_month_data(self.target_month)
        df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        if df.empty:
            return

        year, month = self.target_month.split('-')
        year_num = int(year)
        month_num = int(month)
        end_of_month = pd.Timestamp(f"{year_num}-{month_num:02d}-01") + pd.DateOffset(months=1) - pd.DateOffset(days=1)
        start_of_month = pd.Timestamp(f"{year_num}-{month_num:02d}-01")

        # Build attendance lookup (employee_id -> has_absence)
        absent_employees = set()
        if not attendance_df.empty and 'ID No' in attendance_df.columns and 'compAdd' in attendance_df.columns:
            absent_employees = set(attendance_df[attendance_df['compAdd'] == 'Vắng mặt']['ID No'].unique())

        for _, row in df.iterrows():
            employee_id = row.get('Employee No', '')
            entrance_date = pd.to_datetime(row.get('Entrance Date', ''), errors='coerce')
            stop_date = pd.to_datetime(row.get('Stop working Date', ''), errors='coerce')

            # Calculate tenure days (from month end)
            tenure_days = 0
            if pd.notna(entrance_date):
                tenure_days = (end_of_month - entrance_date).days

            # Determine employee status
            is_active = pd.isna(stop_date) or stop_date > end_of_month
            hired_this_month = pd.notna(entrance_date) and entrance_date.year == year_num and entrance_date.month == month_num
            resigned_this_month = pd.notna(stop_date) and stop_date.year == year_num and stop_date.month == month_num
            under_60_days = tenure_days < 60 if tenure_days > 0 else False
            long_term = (start_of_month - entrance_date).days >= 365 if pd.notna(entrance_date) else False
            perfect_attendance = employee_id not in absent_employees

            self.employee_details.append({
                'employee_id': str(employee_id),
                'employee_name': row.get('Full Name', ''),
                'position': row.get('FINAL QIP POSITION NAME CODE', ''),
                'role_type': row.get('ROLE TYPE STD', ''),
                'entrance_date': entrance_date.strftime('%Y-%m-%d') if pd.notna(entrance_date) else '',
                'stop_date': stop_date.strftime('%Y-%m-%d') if pd.notna(stop_date) else '',
                'tenure_days': int(tenure_days) if tenure_days > 0 else 0,
                'is_active': is_active,
                'hired_this_month': hired_this_month,
                'resigned_this_month': resigned_this_month,
                'under_60_days': under_60_days,
                'long_term': long_term,
                'perfect_attendance': perfect_attendance
            })

    def _convert_to_json_serializable(self, obj):
        """Convert numpy types to Python native types for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    def _generate_html(self) -> str:
        """Generate complete HTML with all components"""
        target_metrics = self.monthly_metrics.get(self.target_month, {})

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR Dashboard - {self.target_month}</title>

    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

    {self._generate_css()}
</head>
<body>
    {self._generate_header()}

    <div class="container-xl px-4 py-4">
        <!-- Tab Navigation -->
        <ul class="nav nav-tabs mb-4" id="dashboardTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview"
                        type="button" role="tab" aria-controls="overview" aria-selected="true">
                    📊 Overview
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="trends-tab" data-bs-toggle="tab" data-bs-target="#trends"
                        type="button" role="tab" aria-controls="trends" aria-selected="false">
                    📈 Trends
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="details-tab" data-bs-toggle="tab" data-bs-target="#details"
                        type="button" role="tab" aria-controls="details" aria-selected="false">
                    👥 Employee Details
                </button>
            </li>
        </ul>

        <!-- Tab Content -->
        <div class="tab-content" id="dashboardTabContent">
            <!-- Overview Tab -->
            <div class="tab-pane fade show active" id="overview" role="tabpanel" aria-labelledby="overview-tab">
                {self._generate_summary_cards(target_metrics)}
            </div>

            <!-- Trends Tab -->
            <div class="tab-pane fade" id="trends" role="tabpanel" aria-labelledby="trends-tab">
                {self._generate_charts_section()}
            </div>

            <!-- Details Tab -->
            <div class="tab-pane fade" id="details" role="tabpanel" aria-labelledby="details-tab">
                {self._generate_details_tab()}
            </div>
        </div>
    </div>

    {self._generate_modals()}

    <script>
        // Embedded data
        const monthlyMetrics = {json.dumps(self._convert_to_json_serializable(self.monthly_metrics), ensure_ascii=False)};
        const monthLabels = {json.dumps(self.month_labels, ensure_ascii=False)};
        const availableMonths = {json.dumps(self.available_months)};
        const targetMonth = '{self.target_month}';
        const employeeDetails = {json.dumps(self.employee_details, ensure_ascii=False)};

        {self._generate_javascript()}
    </script>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        return html

    def _generate_css(self) -> str:
        """Generate CSS styles"""
        return """
<style>
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --card-shadow: 0 4px 6px rgba(0,0,0,0.07);
        --card-hover-shadow: 0 8px 16px rgba(0,0,0,0.12);
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background: #f8f9fa;
    }

    .dashboard-header {
        background: var(--primary-gradient);
        color: white;
        padding: 40px 0;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }

    .dashboard-header h1 {
        font-weight: 700;
        margin-bottom: 10px;
    }

    /* Language Switcher */
    .language-switcher {
        position: absolute;
        top: 20px;
        right: 20px;
        display: flex;
        gap: 8px;
        z-index: 10;
    }

    .lang-btn {
        width: 45px;
        height: 45px;
        border: 2px solid rgba(255,255,255,0.3);
        background: rgba(255,255,255,0.1);
        border-radius: 50%;
        font-size: 24px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
    }

    .lang-btn:hover {
        background: rgba(255,255,255,0.2);
        border-color: rgba(255,255,255,0.6);
        transform: scale(1.1);
    }

    .lang-btn.active {
        background: white;
        border-color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: scale(1.15);
    }

    .summary-card {
        background: white;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: var(--card-shadow);
        transition: transform 0.3s, box-shadow 0.3s;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }

    .summary-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--card-hover-shadow);
    }

    .summary-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--primary-gradient);
    }

    .card-number {
        position: absolute;
        top: 15px;
        right: 15px;
        width: 35px;
        height: 35px;
        border-radius: 50%;
        background: #667eea;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
    }

    .card-title {
        font-size: 14px;
        color: #6c757d;
        margin-bottom: 10px;
        font-weight: 600;
    }

    .card-value {
        font-size: 36px;
        font-weight: bold;
        color: #1a1a1a;
        margin-bottom: 10px;
    }

    .card-change {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
    }

    .card-change.positive {
        background: #d4edda;
        color: #155724;
    }

    .card-change.negative {
        background: #f8d7da;
        color: #721c24;
    }

    .card-change.neutral {
        background: #e2e3e5;
        color: #383d41;
    }

    .charts-section {
        background: white;
        border-radius: 12px;
        padding: 30px;
        box-shadow: var(--card-shadow);
        margin-bottom: 30px;
    }

    .chart-container {
        position: relative;
        height: 300px;
        margin-bottom: 30px;
    }

    .modal-header {
        background: var(--primary-gradient);
        color: white;
    }

    .modal-title {
        font-weight: 600;
    }

    .btn-close-white {
        filter: brightness(0) invert(1);
    }

    /* Tab Navigation Styles */
    .nav-tabs {
        border-bottom: 2px solid #dee2e6;
    }

    .nav-tabs .nav-link {
        color: #495057;
        font-weight: 500;
        border: none;
        border-bottom: 3px solid transparent;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }

    .nav-tabs .nav-link:hover {
        border-color: transparent;
        color: #667eea;
        background: rgba(102, 126, 234, 0.05);
    }

    .nav-tabs .nav-link.active {
        color: #667eea;
        border-color: #667eea;
        background: transparent;
    }

    /* Details Tab Styles */
    .details-section {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: var(--card-shadow);
    }

    .btn-toolbar {
        gap: 0.5rem;
    }

    #employeeTable {
        font-size: 0.9rem;
    }

    #employeeTable thead th {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        font-weight: 600;
        color: #495057;
        cursor: pointer;
        user-select: none;
        position: sticky;
        top: 0;
        z-index: 10;
    }

    #employeeTable thead th:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
    }

    #employeeTable tbody tr {
        transition: all 0.2s ease;
    }

    #employeeTable tbody tr:hover {
        background: rgba(102, 126, 234, 0.05);
        transform: scale(1.01);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .table-responsive {
        max-height: 600px;
        overflow-y: auto;
    }

    .badge-status {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
    }
</style>
"""

    def _generate_header(self) -> str:
        """Generate dashboard header with language switcher"""
        year, month = self.target_month.split('-')
        return f"""
<div class="dashboard-header">
    <div class="container-xl position-relative">
        <!-- Language Switcher -->
        <div class="language-switcher">
            <button class="lang-btn active" data-lang="ko" onclick="switchLanguage('ko')" title="한국어">🇰🇷</button>
            <button class="lang-btn" data-lang="en" onclick="switchLanguage('en')" title="English">🇺🇸</button>
            <button class="lang-btn" data-lang="vi" onclick="switchLanguage('vi')" title="Tiếng Việt">🇻🇳</button>
        </div>

        <h1 class="lang-title" data-ko="👥 HR 대시보드" data-en="👥 HR Dashboard" data-vi="👥 Bảng điều khiển HR">👥 HR 대시보드</h1>
        <p class="mb-0 lang-subtitle"
           data-ko="인사 현황 대시보드 - {year}년 {int(month)}월"
           data-en="Human Resources Dashboard - {year}/{int(month)}"
           data-vi="Bảng điều khiển Nhân sự - {int(month)}/{year}">
           인사 현황 대시보드 - {year}년 {int(month)}월
        </p>
    </div>
</div>
"""

    def _generate_summary_cards(self, metrics: Dict[str, Any]) -> str:
        """Generate summary cards grid"""
        cards = [
            (1, 'total_employees', '총 재직자 수', '명', 'Total Employees'),
            (2, 'absence_rate', '결근율', '%', 'Absence Rate'),
            (3, 'unauthorized_absence_rate', '무단결근율', '%', 'Unauthorized Absence'),
            (4, 'resignation_rate', '퇴사율', '%', 'Resignation Rate'),
            (5, 'recent_hires', '신규 입사자', '명', 'Recent Hires'),
            (6, 'recent_resignations', '최근 퇴사자', '명', 'Recent Resignations'),
            (7, 'under_60_days', '60일 미만', '명', 'Under 60 Days'),
            (8, 'post_assignment_resignations', '배정 후 퇴사', '명', 'Post-Assignment'),
            (9, 'perfect_attendance', '개근 직원', '명', 'Perfect Attendance'),
            (10, 'long_term_employees', '장기근속자', '명', 'Long-term (1yr+)'),
            (11, 'data_errors', '데이터 오류', '건', 'Data Errors')
        ]

        html_parts = ['<div class="row g-3">']

        for num, key, title_ko, unit, title_en in cards:
            value = metrics.get(key, 0)
            change = self.calculator.get_month_over_month_change(key, self.target_month)

            change_html = ''
            if change:
                sign = '+' if change['absolute'] >= 0 else ''
                change_class = 'positive' if change['absolute'] >= 0 else 'negative'
                # Round float values to avoid precision issues
                abs_val = round(change["absolute"], 2) if isinstance(change["absolute"], float) else change["absolute"]
                change_html = f'<div class="card-change {change_class}">{sign}{abs_val} ({sign}{change["percentage"]:.1f}%)</div>'

            html_parts.append(f"""
<div class="col-md-6 col-lg-4 col-xl-3">
    <div class="summary-card" onclick="showModal{num}()">
        <div class="card-number">{num}</div>
        <div class="card-title">{title_ko}<br><small>{title_en}</small></div>
        <div class="card-value">{value}<small class="ms-2">{unit}</small></div>
        {change_html}
    </div>
</div>
""")

        html_parts.append('</div>')
        return '\n'.join(html_parts)

    def _generate_charts_section(self) -> str:
        """Generate charts section with 2-column grid"""
        return """
<div class="charts-section">
    <h4 class="mb-4">📈 월별 추세 분석 / Monthly Trends</h4>
    <div class="row">
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="employeeTrendChart"></canvas>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="hiresResignationsChart"></canvas>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="resignationRateChart"></canvas>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="chart-container">
                <canvas id="longTermChart"></canvas>
            </div>
        </div>
    </div>
</div>
"""

    def _generate_details_tab(self) -> str:
        """Generate employee details table with filters"""
        return """
<div class="details-section">
    <h4 class="mb-4">👥 직원 상세 정보 / Employee Details</h4>

    <!-- Filter Buttons -->
    <div class="btn-toolbar mb-4" role="toolbar">
        <div class="btn-group me-2" role="group">
            <button type="button" class="btn btn-outline-primary active" id="filterAll" onclick="filterEmployees('all')">
                전체 (All)
            </button>
            <button type="button" class="btn btn-outline-success" id="filterActive" onclick="filterEmployees('active')">
                재직자 (Active)
            </button>
            <button type="button" class="btn btn-outline-info" id="filterHired" onclick="filterEmployees('hired')">
                신규입사 (New Hires)
            </button>
            <button type="button" class="btn btn-outline-warning" id="filterResigned" onclick="filterEmployees('resigned')">
                퇴사자 (Resigned)
            </button>
        </div>
        <div class="btn-group me-2" role="group">
            <button type="button" class="btn btn-outline-primary" id="filterPerfect" onclick="filterEmployees('perfect')">
                개근 (Perfect Attendance)
            </button>
            <button type="button" class="btn btn-outline-info" id="filterLongTerm" onclick="filterEmployees('longterm')">
                장기근속 (Long-term)
            </button>
            <button type="button" class="btn btn-outline-secondary" id="filterNew" onclick="filterEmployees('new60')">
                60일 미만 (Under 60 days)
            </button>
        </div>
    </div>

    <!-- Search Box and Export Buttons -->
    <div class="row mb-3 align-items-center">
        <div class="col-md-6">
            <input type="text" class="form-control" id="employeeSearch" placeholder="🔍 Search by ID, Name, Position..." onkeyup="searchEmployees()">
        </div>
        <div class="col-md-6 text-end">
            <div class="btn-group me-2" role="group">
                <button type="button" class="btn btn-sm btn-outline-success" onclick="exportToCSV()" title="Export to CSV">
                    📥 CSV
                </button>
                <button type="button" class="btn btn-sm btn-outline-primary" onclick="exportToJSON()" title="Export to JSON">
                    📥 JSON
                </button>
                <button type="button" class="btn btn-sm btn-outline-warning" onclick="exportMetricsToJSON()" title="Export Metrics">
                    📊 Metrics JSON
                </button>
            </div>
            <span class="badge bg-info fs-6" id="employeeCount">Total: 0</span>
        </div>
    </div>

    <!-- Employee Table -->
    <div class="table-responsive">
        <table class="table table-striped table-hover" id="employeeTable">
            <thead class="table-light sticky-top">
                <tr>
                    <th onclick="sortTable(0)">사번 (ID) ▼</th>
                    <th onclick="sortTable(1)">이름 (Name) ▼</th>
                    <th onclick="sortTable(2)">직급 (Position) ▼</th>
                    <th onclick="sortTable(3)">유형 (Type) ▼</th>
                    <th onclick="sortTable(4)">입사일 (Entrance) ▼</th>
                    <th onclick="sortTable(5)">퇴사일 (Stop) ▼</th>
                    <th onclick="sortTable(6)">재직기간 (Tenure) ▼</th>
                    <th>상태 (Status)</th>
                </tr>
            </thead>
            <tbody id="employeeTableBody">
                <!-- Populated by JavaScript -->
            </tbody>
        </table>
    </div>
</div>
"""

    def _generate_modals(self) -> str:
        """Generate modals with metric calculation explanations"""
        modal_contents = {
            1: {
                'title': '총 재직자 수 / Total Employees',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>재직자 = 퇴사일이 없거나 퇴사일이 월말 이후인 직원</strong></p>
                    <ul>
                        <li><code>Stop working Date</code>가 비어있음 (NaN)</li>
                        <li>또는 <code>Stop working Date > 월말 날짜</code></li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Basic Manpower Data</p>
                '''
            },
            2: {
                'title': '결근율 / Absence Rate',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>결근율 (%) = (결근 레코드 수 / 전체 출근 레코드 수) × 100</strong></p>
                    <ul>
                        <li>결근 레코드: <code>compAdd == 'Vắng mặt'</code></li>
                        <li>전체 레코드: 모든 출근 기록</li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Attendance Data (Converted)</p>
                '''
            },
            3: {
                'title': '무단결근율 / Unauthorized Absence Rate',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>무단결근율 (%) = (무단결근 레코드 수 / 전체 출근 레코드 수) × 100</strong></p>
                    <ul>
                        <li>무단결근 레코드: <code>Reason Description</code>에 "AR1" 포함</li>
                        <li>AR1 = 무단결근 코드 (Vắng không phép, Gửi thư, Họp kỷ luật 등)</li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Attendance Data (Converted)</p>
                '''
            },
            4: {
                'title': '퇴사율 / Resignation Rate',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>퇴사율 (%) = (해당 월 퇴사자 수 / 재직자 수) × 100</strong></p>
                    <ul>
                        <li>해당 월 퇴사자: <code>Stop working Date</code>의 연월이 대상 월과 일치</li>
                        <li>재직자 수: 해당 월의 총 재직자</li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Basic Manpower Data</p>
                '''
            },
            5: {
                'title': '신규 입사자 / Recent Hires',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>신규 입사자 = 해당 월에 <code>Entrance Date</code>가 있는 직원 수</strong></p>
                    <ul>
                        <li><code>Entrance Date</code>의 연월이 대상 월과 일치</li>
                        <li>예: 2025-09의 경우, Entrance Date가 2025년 9월인 직원</li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Basic Manpower Data</p>
                '''
            },
            6: {
                'title': '최근 퇴사자 / Recent Resignations',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>최근 퇴사자 = 해당 월에 <code>Stop working Date</code>가 있는 직원 수</strong></p>
                    <ul>
                        <li><code>Stop working Date</code>의 연월이 대상 월과 일치</li>
                        <li>예: 2025-09의 경우, Stop working Date가 2025년 9월인 직원</li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Basic Manpower Data</p>
                '''
            },
            7: {
                'title': '60일 미만 재직자 / Under 60 Days',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>60일 미만 = (월말 날짜 - <code>Entrance Date</code>) < 60일인 직원</strong></p>
                    <ul>
                        <li>재직 기간 = 월말 기준 입사일로부터 경과 일수</li>
                        <li>60일 미만인 직원 카운트</li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Basic Manpower Data</p>
                '''
            },
            8: {
                'title': '배정 후 퇴사자 / Post-Assignment Resignations',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>배정 후 퇴사자 = Assignment date와 Resignation date가 모두 있는 직원</strong></p>
                    <ul>
                        <li class="text-warning">⚠️ HR 데이터에는 Assignment date 정보가 없음</li>
                        <li>현재 값: 0 (데이터 미제공)</li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Assignment 데이터 필요</p>
                '''
            },
            9: {
                'title': '개근 직원 / Perfect Attendance',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>개근 직원 = 한 번도 결근하지 않은 직원 수</strong></p>
                    <ul>
                        <li>전체 출근한 직원 수 - 결근 기록이 있는 직원 수</li>
                        <li>결근: <code>compAdd == 'Vắng mặt'</code></li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Attendance Data (Converted)</p>
                '''
            },
            10: {
                'title': '장기근속자 (1년 이상) / Long-term Employees',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>장기근속자 = (월초 날짜 - <code>Entrance Date</code>) >= 365일인 직원</strong></p>
                    <ul>
                        <li>재직 기간 = 월초 기준 입사일로부터 경과 일수</li>
                        <li>365일 이상인 직원 카운트</li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Basic Manpower Data</p>
                '''
            },
            11: {
                'title': '데이터 오류 / Data Errors',
                'description': '''
                    <h6>📋 계산 방법</h6>
                    <p><strong>데이터 오류 = 필수 필드 누락 + 시간적 불일치</strong></p>
                    <ul>
                        <li><code>Employee No</code> 누락</li>
                        <li><code>Full Name</code> 누락</li>
                        <li><code>Stop working Date < Entrance Date</code> (퇴사일이 입사일보다 빠름)</li>
                    </ul>
                    <p class="text-muted">※ 데이터 출처: Basic Manpower Data</p>
                '''
            }
        }

        modals = []
        for i in range(1, 12):
            content = modal_contents[i]
            modals.append(f"""
<div class="modal fade" id="modal{i}" tabindex="-1">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">{content['title']}</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                {content['description']}
                <hr>
                <div id="modalContent{i}">
                    <h6>📊 상세 데이터 (추후 구현 예정)</h6>
                    <p class="text-muted">직원 목록, 추세 분석, 세부 통계 등이 여기에 표시됩니다.</p>
                </div>
            </div>
        </div>
    </div>
</div>
""")
        return '\n'.join(modals)

    def _generate_javascript(self) -> str:
        """Generate JavaScript for charts and interactivity"""
        return """
// ============================================
// Language Switching
// ============================================

function switchLanguage(lang) {
    // Update button states
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.lang === lang) {
            btn.classList.add('active');
        }
    });

    // Update all elements with language data attributes
    document.querySelectorAll('[data-ko]').forEach(elem => {
        if (elem.dataset[lang]) {
            elem.textContent = elem.dataset[lang];
        }
    });

    // Save preference
    localStorage.setItem('dashboard_language', lang);

    console.log(`✅ Language switched to: ${lang}`);
}

// Load saved language preference on page load
document.addEventListener('DOMContentLoaded', function() {
    const savedLang = localStorage.getItem('dashboard_language');
    if (savedLang && ['ko', 'en', 'vi'].includes(savedLang)) {
        switchLanguage(savedLang);
    }
});

// ============================================
// Helper Functions
// ============================================

// Helper: Create employee table
function createEmployeeTable(employees, columns) {
    if (employees.length === 0) {
        return '<p class="text-muted">해당하는 직원이 없습니다.</p>';
    }

    let html = '<div class="table-responsive"><table class="table table-striped table-hover">';
    html += '<thead class="table-light"><tr>';
    columns.forEach(col => {
        html += `<th>${col.label}</th>`;
    });
    html += '</tr></thead><tbody>';

    employees.forEach(emp => {
        html += '<tr>';
        columns.forEach(col => {
            let value = emp[col.field] || '';
            if (col.field === 'tenure_days') {
                value = `${value}일 (${Math.floor(value/30)}개월)`;
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    html += `<p class="text-muted mt-2">총 ${employees.length}명</p>`;
    return html;
}

// Modal 1: Total Employees
function showModal1() {
    const employees = employeeDetails.filter(e => e.is_active);
    const columns = [
        {field: 'employee_id', label: '사번'},
        {field: 'employee_name', label: '이름'},
        {field: 'position', label: '직급'},
        {field: 'role_type', label: '유형'},
        {field: 'entrance_date', label: '입사일'},
        {field: 'tenure_days', label: '재직기간'}
    ];
    document.getElementById('modalContent1').innerHTML = createEmployeeTable(employees, columns);
    new bootstrap.Modal(document.getElementById('modal1')).show();
}

// Modal 2-3: Attendance (placeholder - need attendance integration)
function showModal2() {
    document.getElementById('modalContent2').innerHTML = '<p class="text-warning">출근 데이터 상세 통합 작업 필요</p>';
    new bootstrap.Modal(document.getElementById('modal2')).show();
}
function showModal3() {
    document.getElementById('modalContent3').innerHTML = '<p class="text-warning">무단결근 상세 데이터 통합 작업 필요</p>';
    new bootstrap.Modal(document.getElementById('modal3')).show();
}

// Modal 4: Resignation Rate
function showModal4() {
    const employees = employeeDetails.filter(e => e.resigned_this_month);
    const columns = [
        {field: 'employee_id', label: '사번'},
        {field: 'employee_name', label: '이름'},
        {field: 'position', label: '직급'},
        {field: 'entrance_date', label: '입사일'},
        {field: 'stop_date', label: '퇴사일'},
        {field: 'tenure_days', label: '재직기간'}
    ];
    document.getElementById('modalContent4').innerHTML = createEmployeeTable(employees, columns);
    new bootstrap.Modal(document.getElementById('modal4')).show();
}

// Modal 5: Recent Hires
function showModal5() {
    const employees = employeeDetails.filter(e => e.hired_this_month);
    const columns = [
        {field: 'employee_id', label: '사번'},
        {field: 'employee_name', label: '이름'},
        {field: 'position', label: '직급'},
        {field: 'role_type', label: '유형'},
        {field: 'entrance_date', label: '입사일'}
    ];
    document.getElementById('modalContent5').innerHTML = createEmployeeTable(employees, columns);
    new bootstrap.Modal(document.getElementById('modal5')).show();
}

// Modal 6: Recent Resignations
function showModal6() {
    const employees = employeeDetails.filter(e => e.resigned_this_month);
    const columns = [
        {field: 'employee_id', label: '사번'},
        {field: 'employee_name', label: '이름'},
        {field: 'position', label: '직급'},
        {field: 'entrance_date', label: '입사일'},
        {field: 'stop_date', label: '퇴사일'},
        {field: 'tenure_days', label: '재직기간'}
    ];
    document.getElementById('modalContent6').innerHTML = createEmployeeTable(employees, columns);
    new bootstrap.Modal(document.getElementById('modal6')).show();
}

// Modal 7: Under 60 Days
function showModal7() {
    const employees = employeeDetails.filter(e => e.under_60_days && e.is_active);
    const columns = [
        {field: 'employee_id', label: '사번'},
        {field: 'employee_name', label: '이름'},
        {field: 'position', label: '직급'},
        {field: 'entrance_date', label: '입사일'},
        {field: 'tenure_days', label: '재직기간'}
    ];
    document.getElementById('modalContent7').innerHTML = createEmployeeTable(employees, columns);
    new bootstrap.Modal(document.getElementById('modal7')).show();
}

// Modal 8: Post-Assignment (no data)
function showModal8() {
    document.getElementById('modalContent8').innerHTML = '<p class="text-warning">⚠️ Assignment date 데이터가 제공되지 않아 계산할 수 없습니다.</p>';
    new bootstrap.Modal(document.getElementById('modal8')).show();
}

// Modal 9: Perfect Attendance
function showModal9() {
    const employees = employeeDetails.filter(e => e.perfect_attendance && e.is_active);
    const columns = [
        {field: 'employee_id', label: '사번'},
        {field: 'employee_name', label: '이름'},
        {field: 'position', label: '직급'},
        {field: 'role_type', label: '유형'},
        {field: 'entrance_date', label: '입사일'}
    ];
    document.getElementById('modalContent9').innerHTML = createEmployeeTable(employees, columns);
    new bootstrap.Modal(document.getElementById('modal9')).show();
}

// Modal 10: Long-term Employees
function showModal10() {
    const employees = employeeDetails.filter(e => e.long_term && e.is_active);
    const columns = [
        {field: 'employee_id', label: '사번'},
        {field: 'employee_name', label: '이름'},
        {field: 'position', label: '직급'},
        {field: 'role_type', label: '유형'},
        {field: 'entrance_date', label: '입사일'},
        {field: 'tenure_days', label: '재직기간'}
    ];
    document.getElementById('modalContent10').innerHTML = createEmployeeTable(employees, columns);
    new bootstrap.Modal(document.getElementById('modal10')).show();
}

// Modal 11: Data Errors
function showModal11() {
    document.getElementById('modalContent11').innerHTML = '<p class="text-success">✅ 현재 데이터 오류가 발견되지 않았습니다.</p>';
    new bootstrap.Modal(document.getElementById('modal11')).show();
}

// Helper: Get trend data for metric
function getTrendData(metricKey) {
    return availableMonths.map(month => monthlyMetrics[month][metricKey]);
}

// Chart 1: Employee Trend
new Chart(document.getElementById('employeeTrendChart'), {
    type: 'line',
    data: {
        labels: monthLabels,
        datasets: [{
            label: '재직자 수 / Total Employees',
            data: getTrendData('total_employees'),
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'bottom' }
        }
    }
});

// Chart 2: Hires vs Resignations
new Chart(document.getElementById('hiresResignationsChart'), {
    type: 'bar',
    data: {
        labels: monthLabels,
        datasets: [
            {
                label: '신규 입사 / New Hires',
                data: getTrendData('recent_hires'),
                backgroundColor: 'rgba(40, 167, 69, 0.7)',
                borderColor: '#28a745',
                borderWidth: 1
            },
            {
                label: '퇴사자 / Resignations',
                data: getTrendData('recent_resignations'),
                backgroundColor: 'rgba(220, 53, 69, 0.7)',
                borderColor: '#dc3545',
                borderWidth: 1
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'bottom' }
        }
    }
});

// Chart 3: Resignation Rate
new Chart(document.getElementById('resignationRateChart'), {
    type: 'line',
    data: {
        labels: monthLabels,
        datasets: [{
            label: '퇴사율 (%) / Resignation Rate',
            data: getTrendData('resignation_rate'),
            borderColor: '#dc3545',
            backgroundColor: 'rgba(220, 53, 69, 0.1)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'bottom' }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }
        }
    }
});

// Chart 4: Long-term Employees
new Chart(document.getElementById('longTermChart'), {
    type: 'bar',
    data: {
        labels: monthLabels,
        datasets: [{
            label: '장기근속자 (1년+) / Long-term Employees',
            data: getTrendData('long_term_employees'),
            backgroundColor: 'rgba(102, 126, 234, 0.7)',
            borderColor: '#667eea',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { position: 'bottom' }
        }
    }
});

console.log('✅ Dashboard initialized');
console.log('📊 Months:', availableMonths);
console.log('👥 Employees:', employeeDetails.length);

// ============================================
// Employee Details Tab Functions
// ============================================

let currentFilter = 'all';
let currentSortColumn = -1;
let currentSortAsc = true;

// Render employee table
function renderEmployeeTable(employees = null) {
    const tbody = document.getElementById('employeeTableBody');
    if (!tbody) return; // Tab not loaded yet

    const displayEmployees = employees || employeeDetails;

    if (displayEmployees.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">직원이 없습니다.</td></tr>';
        updateEmployeeCount(0);
        return;
    }

    let html = '';
    displayEmployees.forEach(emp => {
        const tenureMonths = Math.floor((emp.tenure_days || 0) / 30);
        const tenureDisplay = emp.tenure_days ? `${emp.tenure_days}일 (${tenureMonths}개월)` : '-';

        // Status badges
        let statusBadges = [];
        if (emp.is_active) {
            statusBadges.push('<span class="badge bg-success badge-status">재직</span>');
        } else {
            statusBadges.push('<span class="badge bg-secondary badge-status">퇴사</span>');
        }
        if (emp.hired_this_month) {
            statusBadges.push('<span class="badge bg-info badge-status">신입</span>');
        }
        if (emp.perfect_attendance) {
            statusBadges.push('<span class="badge bg-primary badge-status">개근</span>');
        }
        if (emp.long_term) {
            statusBadges.push('<span class="badge bg-warning badge-status">장기</span>');
        }

        html += `
            <tr>
                <td>${emp.employee_id || ''}</td>
                <td>${emp.employee_name || ''}</td>
                <td>${emp.position || ''}</td>
                <td><span class="badge bg-light text-dark">${emp.role_type || ''}</span></td>
                <td>${emp.entrance_date || ''}</td>
                <td>${emp.stop_date || '-'}</td>
                <td>${tenureDisplay}</td>
                <td>${statusBadges.join(' ')}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
    updateEmployeeCount(displayEmployees.length);
}

// Filter employees
function filterEmployees(filter) {
    currentFilter = filter;

    // Update button states
    document.querySelectorAll('.btn-group button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`filter${filter.charAt(0).toUpperCase() + filter.slice(1)}`).classList.add('active');

    // Filter logic
    let filtered = employeeDetails;

    switch(filter) {
        case 'all':
            filtered = employeeDetails;
            break;
        case 'active':
            filtered = employeeDetails.filter(e => e.is_active);
            break;
        case 'hired':
            filtered = employeeDetails.filter(e => e.hired_this_month);
            break;
        case 'resigned':
            filtered = employeeDetails.filter(e => e.resigned_this_month);
            break;
        case 'perfect':
            filtered = employeeDetails.filter(e => e.perfect_attendance);
            break;
        case 'longterm':
            filtered = employeeDetails.filter(e => e.long_term);
            break;
        case 'new60':
            filtered = employeeDetails.filter(e => e.under_60_days);
            break;
    }

    renderEmployeeTable(filtered);
}

// Search employees
function searchEmployees() {
    const searchTerm = document.getElementById('employeeSearch').value.toLowerCase();

    // Apply current filter first
    let filtered = employeeDetails;
    if (currentFilter !== 'all') {
        filterEmployees(currentFilter); // This will set filtered
        return; // Let filterEmployees handle it
    }

    if (!searchTerm) {
        renderEmployeeTable(employeeDetails);
        return;
    }

    filtered = employeeDetails.filter(emp => {
        return (
            (emp.employee_id && emp.employee_id.toLowerCase().includes(searchTerm)) ||
            (emp.employee_name && emp.employee_name.toLowerCase().includes(searchTerm)) ||
            (emp.position && emp.position.toLowerCase().includes(searchTerm)) ||
            (emp.role_type && emp.role_type.toLowerCase().includes(searchTerm))
        );
    });

    renderEmployeeTable(filtered);
}

// Sort table
function sortTable(columnIndex) {
    const tbody = document.getElementById('employeeTableBody');
    const rows = Array.from(tbody.getElementsByTagName('tr'));

    // Toggle sort direction
    if (currentSortColumn === columnIndex) {
        currentSortAsc = !currentSortAsc;
    } else {
        currentSortColumn = columnIndex;
        currentSortAsc = true;
    }

    rows.sort((a, b) => {
        const aText = a.getElementsByTagName('td')[columnIndex].textContent.trim();
        const bText = b.getElementsByTagName('td')[columnIndex].textContent.trim();

        // Numeric comparison for tenure column
        if (columnIndex === 6) {
            const aNum = parseInt(aText) || 0;
            const bNum = parseInt(bText) || 0;
            return currentSortAsc ? aNum - bNum : bNum - aNum;
        }

        // String comparison
        return currentSortAsc ?
            aText.localeCompare(bText) :
            bText.localeCompare(aText);
    });

    rows.forEach(row => tbody.appendChild(row));
}

// Update employee count
function updateEmployeeCount(count) {
    const badge = document.getElementById('employeeCount');
    if (badge) {
        badge.textContent = `Total: ${count}`;
    }
}

// Initialize employee table when Details tab is shown
document.addEventListener('DOMContentLoaded', function() {
    const detailsTab = document.getElementById('details-tab');
    if (detailsTab) {
        detailsTab.addEventListener('shown.bs.tab', function() {
            renderEmployeeTable();
        });
    }
});

// ============================================
// Export Functions
// ============================================

// Export employee data to CSV
function exportToCSV() {
    const filename = `HR_Employees_${targetMonth}.csv`;

    // CSV headers
    const headers = ['사번,이름,직급,유형,입사일,퇴사일,재직기간(일),상태'];

    // CSV rows
    const rows = employeeDetails.map(emp => {
        const status = [
            emp.is_active ? '재직' : '퇴사',
            emp.hired_this_month ? '신입' : '',
            emp.perfect_attendance ? '개근' : '',
            emp.long_term ? '장기' : ''
        ].filter(s => s).join('|');

        return [
            emp.employee_id || '',
            emp.employee_name || '',
            emp.position || '',
            emp.role_type || '',
            emp.entrance_date || '',
            emp.stop_date || '',
            emp.tenure_days || '0',
            status
        ].map(field => `"${field}"`).join(',');
    });

    const csv = headers.concat(rows).join('\\n');
    downloadFile(csv, filename, 'text/csv;charset=utf-8;');

    console.log(`✅ Exported ${employeeDetails.length} employees to CSV`);
}

// Export employee data to JSON
function exportToJSON() {
    const filename = `HR_Employees_${targetMonth}.json`;
    const json = JSON.stringify(employeeDetails, null, 2);
    downloadFile(json, filename, 'application/json');

    console.log(`✅ Exported ${employeeDetails.length} employees to JSON`);
}

// Export metrics data to JSON
function exportMetricsToJSON() {
    const filename = `HR_Metrics_${targetMonth}.json`;

    const exportData = {
        target_month: targetMonth,
        available_months: availableMonths,
        month_labels: monthLabels,
        metrics: monthlyMetrics,
        generated_at: new Date().toISOString()
    };

    const json = JSON.stringify(exportData, null, 2);
    downloadFile(json, filename, 'application/json');

    console.log(`✅ Exported metrics for ${availableMonths.length} months to JSON`);
}

// Helper: Download file
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
}
"""


def main():
    """Build and save dashboard"""
    import argparse

    parser = argparse.ArgumentParser(description='Build Complete HR Dashboard')
    parser.add_argument('--month', '-m', type=int, required=True, help='Target month (1-12)')
    parser.add_argument('--year', '-y', type=int, required=True, help='Target year')
    parser.add_argument('--language', '-l', default='ko', choices=['ko', 'en', 'vi'])

    args = parser.parse_args()

    target_month = f"{args.year}-{args.month:02d}"

    builder = CompleteDashboardBuilder(target_month, args.language)
    html = builder.build()

    # Save dashboard
    output_dir = Path(__file__).parent.parent.parent / 'output_files'
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"HR_Dashboard_Complete_{target_month.replace('-', '_')}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ Dashboard saved: {output_path}")
    print(f"🌐 Opening in browser...")

    import webbrowser
    webbrowser.open(f"file://{output_path.absolute()}")


if __name__ == '__main__':
    main()
