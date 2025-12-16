"""
enhanced_modal_generator.py - Enhanced KPI Modal Generator with Management Insights
팀별 및 개인별 관리 인사이트를 제공하는 향상된 KPI 모달 생성기

Provides both macro (team-level) and micro (individual-level) perspectives
거시적(팀 수준) 및 미시적(개인 수준) 관점 제공
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

class EnhancedModalGenerator:
    """
    Generate enhanced modals with management-focused insights
    관리 중심 인사이트를 포함한 향상된 모달 생성
    """

    def __init__(self, translator, metric_calculator, logger):
        """
        Initialize Enhanced Modal Generator
        향상된 모달 생성기 초기화
        """
        self.t = translator
        self.metric_calculator = metric_calculator
        self.logger = logger

        # Define KPI thresholds for priority scoring
        # 우선순위 점수를 위한 KPI 임계값 정의
        self.kpi_thresholds = {
            'resignation_rate': {'critical': 20, 'warning': 15, 'normal': 10},
            'absence_rate': {'critical': 30, 'warning': 20, 'normal': 10},
            'unauthorized_absence_rate': {'critical': 15, 'warning': 10, 'normal': 5},
            'early_resignation_30': {'critical': 30, 'warning': 20, 'normal': 10},
            'early_resignation_60': {'critical': 25, 'warning': 15, 'normal': 8},
            'early_resignation_90': {'critical': 20, 'warning': 10, 'normal': 5},
            'overtime_rate': {'critical': 30, 'warning': 20, 'normal': 10}
        }

    def generate_enhanced_modal(self,
                              modal_id: str,
                              metric_id: str,
                              current_data: pd.DataFrame,
                              historical_data: Dict[str, pd.DataFrame],
                              attendance_data: Optional[pd.DataFrame] = None) -> str:
        """
        Generate enhanced modal with management insights
        관리 인사이트를 포함한 향상된 모달 생성

        Args:
            modal_id: Modal identifier / 모달 식별자
            metric_id: Metric identifier / 메트릭 식별자
            current_data: Current month data / 현재 월 데이터
            historical_data: Historical data by month / 월별 과거 데이터
            attendance_data: Attendance data if needed / 필요시 출근 데이터

        Returns:
            HTML string for enhanced modal / 향상된 모달 HTML 문자열
        """
        # Get team-based analysis
        team_analysis = self._analyze_teams(metric_id, current_data, attendance_data)

        # Get individual analysis for problematic teams
        individual_analysis = self._analyze_individuals(
            metric_id, current_data, attendance_data, team_analysis['problematic_teams']
        )

        # Get month-over-month comparison
        mom_comparison = self._get_month_over_month(metric_id, historical_data)

        # Get management priorities
        priorities = self._calculate_management_priorities(
            team_analysis, individual_analysis, mom_comparison
        )

        # Generate modal HTML
        modal_html = self._build_modal_html(
            modal_id, metric_id, team_analysis, individual_analysis,
            mom_comparison, priorities
        )

        return modal_html

    def _analyze_teams(self, metric_id: str, data: pd.DataFrame,
                      attendance_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyze KPI metrics by team
        팀별 KPI 메트릭 분석
        """
        teams = data['Team'].unique() if 'Team' in data.columns else []
        team_metrics = []

        for team in teams:
            team_data = data[data['Team'] == team]

            # Calculate metric for this team
            if metric_id == 'resignation_rate':
                value = self._calculate_team_resignation_rate(team_data)
            elif metric_id == 'absence_rate':
                value = self._calculate_team_absence_rate(team_data, attendance_data)
            elif metric_id == 'unauthorized_absence_rate':
                value = self._calculate_team_unauthorized_absence_rate(team_data, attendance_data)
            else:
                value = 0

            # Determine status based on thresholds
            status = self._get_status(metric_id, value)

            team_metrics.append({
                'team': team,
                'value': value,
                'status': status,
                'employee_count': len(team_data),
                'risk_score': self._calculate_risk_score(metric_id, value)
            })

        # Sort by risk score
        team_metrics.sort(key=lambda x: x['risk_score'], reverse=True)

        # Identify problematic teams
        problematic_teams = [tm['team'] for tm in team_metrics if tm['status'] in ['critical', 'warning']]

        return {
            'team_metrics': team_metrics,
            'problematic_teams': problematic_teams,
            'average_value': np.mean([tm['value'] for tm in team_metrics]),
            'worst_team': team_metrics[0] if team_metrics else None
        }

    def _analyze_individuals(self, metric_id: str, data: pd.DataFrame,
                           attendance_data: Optional[pd.DataFrame],
                           problematic_teams: List[str]) -> Dict[str, Any]:
        """
        Analyze individuals within problematic teams
        문제가 있는 팀 내 개인 분석
        """
        individual_issues = []

        for team in problematic_teams:
            team_data = data[data['Team'] == team]

            if metric_id == 'resignation_rate':
                # Find recent hires at risk
                recent_hires = team_data[
                    (pd.Timestamp.now() - pd.to_datetime(team_data['Entrance Date'])).dt.days <= 90
                ]
                for _, emp in recent_hires.iterrows():
                    days_employed = (pd.Timestamp.now() - emp['Entrance Date']).days
                    individual_issues.append({
                        'employee_no': emp['Employee No'],
                        'name': emp['Name'],
                        'team': team,
                        'issue_type': 'early_resignation_risk',
                        'value': days_employed,
                        'description': f"입사 {days_employed}일 - 조기퇴사 위험",
                        'priority': 'high' if days_employed < 30 else 'medium'
                    })

            elif metric_id in ['absence_rate', 'unauthorized_absence_rate']:
                if attendance_data is not None:
                    # Find individuals with high absence rates
                    for _, emp in team_data.iterrows():
                        emp_attendance = attendance_data[
                            attendance_data['ID No'] == int(emp['Employee No'])
                        ]
                        if len(emp_attendance) > 0:
                            absence_count = len(emp_attendance[emp_attendance['compAdd'] == 'Vắng mặt'])
                            total_days = len(emp_attendance)
                            absence_rate = (absence_count / total_days * 100) if total_days > 0 else 0

                            if absence_rate > 10:  # Threshold for concern
                                individual_issues.append({
                                    'employee_no': emp['Employee No'],
                                    'name': emp['Name'],
                                    'team': team,
                                    'issue_type': 'high_absence',
                                    'value': absence_rate,
                                    'description': f"결근율 {absence_rate:.1f}%",
                                    'priority': 'high' if absence_rate > 20 else 'medium'
                                })

        # Sort by priority and value
        individual_issues.sort(key=lambda x: (
            0 if x['priority'] == 'high' else 1,
            -x['value']
        ))

        return {
            'individuals': individual_issues[:20],  # Top 20 individuals
            'total_count': len(individual_issues),
            'high_priority_count': sum(1 for i in individual_issues if i['priority'] == 'high')
        }

    def _get_month_over_month(self, metric_id: str,
                             historical_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Calculate month-over-month comparison
        전월 대비 비교 계산
        """
        if len(historical_data) < 2:
            return {
                'current_value': 0,
                'previous_value': 0,
                'change': 0,
                'change_percent': 0,
                'trend': 'stable',
                'trend_icon': '→'
            }

        # Sort by date
        sorted_months = sorted(historical_data.keys())
        current_month = sorted_months[-1]
        previous_month = sorted_months[-2] if len(sorted_months) > 1 else current_month

        # Calculate metrics for both months
        current_value = self._calculate_overall_metric(
            metric_id, historical_data[current_month], None
        )
        previous_value = self._calculate_overall_metric(
            metric_id, historical_data[previous_month], None
        )

        change = current_value - previous_value
        change_percent = (change / previous_value * 100) if previous_value != 0 else 0

        # Determine trend
        if abs(change_percent) < 5:
            trend = 'stable'
        elif change > 0:
            trend = 'worsening' if self._is_negative_metric(metric_id) else 'improving'
        else:
            trend = 'improving' if self._is_negative_metric(metric_id) else 'worsening'

        return {
            'current_value': current_value,
            'previous_value': previous_value,
            'change': change,
            'change_percent': change_percent,
            'trend': trend,
            'trend_icon': self._get_trend_icon(trend)
        }

    def _calculate_management_priorities(self, team_analysis: Dict,
                                        individual_analysis: Dict,
                                        mom_comparison: Dict) -> List[Dict]:
        """
        Calculate management priorities based on all analyses
        모든 분석을 기반으로 관리 우선순위 계산
        """
        priorities = []

        # Add team-level priorities
        for team_metric in team_analysis['team_metrics'][:5]:  # Top 5 teams
            if team_metric['status'] in ['critical', 'warning']:
                priorities.append({
                    'type': 'team',
                    'target': team_metric['team'],
                    'metric_value': team_metric['value'],
                    'risk_score': team_metric['risk_score'],
                    'action': self._get_recommended_action(team_metric['status']),
                    'priority_level': 'critical' if team_metric['status'] == 'critical' else 'high'
                })

        # Add individual-level priorities
        for individual in individual_analysis['individuals'][:5]:  # Top 5 individuals
            priorities.append({
                'type': 'individual',
                'target': f"{individual['name']} ({individual['employee_no']})",
                'team': individual['team'],
                'issue': individual['issue_type'],
                'metric_value': individual['value'],
                'action': self._get_individual_action(individual['issue_type']),
                'priority_level': individual['priority']
            })

        # Sort by priority level and risk score
        priorities.sort(key=lambda x: (
            0 if x.get('priority_level') == 'critical' else
            1 if x.get('priority_level') == 'high' else 2,
            -x.get('risk_score', 0)
        ))

        return priorities[:10]  # Return top 10 priorities

    def _build_modal_html(self, modal_id: str, metric_id: str,
                         team_analysis: Dict, individual_analysis: Dict,
                         mom_comparison: Dict, priorities: List[Dict]) -> str:
        """
        Build the enhanced modal HTML
        향상된 모달 HTML 구축
        """
        # Use I18n t() method for translation
        # I18n t() 메서드를 사용하여 번역
        try:
            metric_name = self.t.t(f"metrics.{metric_id}")
        except:
            metric_name = metric_id

        html = f"""
        <div class="modal fade" id="{modal_id}" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-graph-up"></i> {metric_name} - Management Insights
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Navigation Tabs -->
                        <ul class="nav nav-tabs mb-3" role="tablist">
                            <li class="nav-item">
                                <a class="nav-link active" data-bs-toggle="tab" href="#overview-{modal_id}">
                                    <i class="bi bi-speedometer2"></i> Overview
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" data-bs-toggle="tab" href="#teams-{modal_id}">
                                    <i class="bi bi-people"></i> Team Analysis
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" data-bs-toggle="tab" href="#individuals-{modal_id}">
                                    <i class="bi bi-person-badge"></i> Individual Details
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" data-bs-toggle="tab" href="#priorities-{modal_id}">
                                    <i class="bi bi-exclamation-triangle"></i> Management Priorities
                                </a>
                            </li>
                        </ul>

                        <!-- Tab Contents -->
                        <div class="tab-content">
                            {self._build_overview_tab(modal_id, mom_comparison, team_analysis)}
                            {self._build_teams_tab(modal_id, team_analysis)}
                            {self._build_individuals_tab(modal_id, individual_analysis)}
                            {self._build_priorities_tab(modal_id, priorities)}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        return html

    def _build_overview_tab(self, modal_id: str, mom_comparison: Dict, team_analysis: Dict) -> str:
        """Build overview tab content"""
        trend_color = 'success' if mom_comparison['trend'] == 'improving' else 'danger' if mom_comparison['trend'] == 'worsening' else 'warning'

        return f"""
        <div class="tab-pane fade show active" id="overview-{modal_id}">
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Month-over-Month Comparison</h6>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span>Current Month:</span>
                                <strong>{mom_comparison['current_value']:.1f}%</strong>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span>Previous Month:</span>
                                <strong>{mom_comparison['previous_value']:.1f}%</strong>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span>Change:</span>
                                <span class="badge bg-{trend_color}">
                                    {mom_comparison['trend_icon']} {mom_comparison['change']:.1f}%
                                    ({mom_comparison['change_percent']:+.1f}%)
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h6 class="card-title">Summary Statistics</h6>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span>Teams Analyzed:</span>
                                <strong>{len(team_analysis['team_metrics'])}</strong>
                            </div>
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span>Problematic Teams:</span>
                                <strong class="text-danger">{len(team_analysis['problematic_teams'])}</strong>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span>Average Value:</span>
                                <strong>{team_analysis['average_value']:.1f}%</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _build_teams_tab(self, modal_id: str, team_analysis: Dict) -> str:
        """Build teams analysis tab content"""
        rows = ""
        for tm in team_analysis['team_metrics']:
            status_badge = self._get_status_badge(tm['status'])
            rows += f"""
            <tr>
                <td>{tm['team']}</td>
                <td>{tm['employee_count']}</td>
                <td>{tm['value']:.1f}%</td>
                <td>{status_badge}</td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar bg-{self._get_risk_color(tm['risk_score'])}"
                             style="width: {tm['risk_score']}%">
                            {tm['risk_score']:.0f}
                        </div>
                    </div>
                </td>
            </tr>
            """

        return f"""
        <div class="tab-pane fade" id="teams-{modal_id}">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Team</th>
                            <th>Employees</th>
                            <th>Metric Value</th>
                            <th>Status</th>
                            <th>Risk Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _build_individuals_tab(self, modal_id: str, individual_analysis: Dict) -> str:
        """Build individuals tab content"""
        if not individual_analysis['individuals']:
            return f"""
            <div class="tab-pane fade" id="individuals-{modal_id}">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> No individual issues identified
                </div>
            </div>
            """

        rows = ""
        for ind in individual_analysis['individuals']:
            priority_badge = f"<span class='badge bg-{'danger' if ind['priority'] == 'high' else 'warning'}'>{ind['priority'].upper()}</span>"
            rows += f"""
            <tr>
                <td>{ind['employee_no']}</td>
                <td>{ind['name']}</td>
                <td>{ind['team']}</td>
                <td>{ind['description']}</td>
                <td>{priority_badge}</td>
            </tr>
            """

        return f"""
        <div class="tab-pane fade" id="individuals-{modal_id}">
            <div class="alert alert-warning mb-3">
                <i class="bi bi-exclamation-triangle"></i>
                Found {individual_analysis['total_count']} individuals requiring attention
                ({individual_analysis['high_priority_count']} high priority)
            </div>
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Employee No</th>
                            <th>Name</th>
                            <th>Team</th>
                            <th>Issue</th>
                            <th>Priority</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _build_priorities_tab(self, modal_id: str, priorities: List[Dict]) -> str:
        """Build management priorities tab content"""
        if not priorities:
            return f"""
            <div class="tab-pane fade" id="priorities-{modal_id}">
                <div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> No immediate management action required
                </div>
            </div>
            """

        cards = ""
        for i, priority in enumerate(priorities, 1):
            priority_color = 'danger' if priority['priority_level'] == 'critical' else 'warning' if priority['priority_level'] == 'high' else 'info'
            icon = 'people-fill' if priority['type'] == 'team' else 'person-fill'

            cards += f"""
            <div class="col-md-6 mb-3">
                <div class="card border-{priority_color}">
                    <div class="card-header bg-{priority_color} text-white">
                        <i class="bi bi-{icon}"></i> Priority #{i} - {priority['priority_level'].upper()}
                    </div>
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">{priority['type'].title()} Level</h6>
                        <p class="card-text">
                            <strong>Target:</strong> {priority['target']}<br>
                            {'<strong>Team:</strong> ' + priority.get('team', '') + '<br>' if priority.get('team') else ''}
                            <strong>Metric Value:</strong> {priority['metric_value']:.1f}<br>
                            <strong>Recommended Action:</strong> {priority['action']}
                        </p>
                    </div>
                </div>
            </div>
            """

        return f"""
        <div class="tab-pane fade" id="priorities-{modal_id}">
            <div class="row">
                {cards}
            </div>
        </div>
        """

    # Helper methods
    def _calculate_team_resignation_rate(self, team_data: pd.DataFrame) -> float:
        """Calculate resignation rate for a team"""
        # Implementation would use metric_calculator
        return 0.0

    def _calculate_team_absence_rate(self, team_data: pd.DataFrame,
                                    attendance_data: Optional[pd.DataFrame]) -> float:
        """Calculate absence rate for a team"""
        return 0.0

    def _calculate_team_unauthorized_absence_rate(self, team_data: pd.DataFrame,
                                                 attendance_data: Optional[pd.DataFrame]) -> float:
        """Calculate unauthorized absence rate for a team"""
        return 0.0

    def _calculate_overall_metric(self, metric_id: str, data: pd.DataFrame,
                                 attendance_data: Optional[pd.DataFrame]) -> float:
        """Calculate overall metric value"""
        return 0.0

    def _get_status(self, metric_id: str, value: float) -> str:
        """Get status based on metric value and thresholds"""
        if metric_id not in self.kpi_thresholds:
            return 'normal'

        thresholds = self.kpi_thresholds[metric_id]
        if value >= thresholds['critical']:
            return 'critical'
        elif value >= thresholds['warning']:
            return 'warning'
        else:
            return 'normal'

    def _calculate_risk_score(self, metric_id: str, value: float) -> float:
        """Calculate risk score (0-100)"""
        if metric_id not in self.kpi_thresholds:
            return 0

        thresholds = self.kpi_thresholds[metric_id]
        if value >= thresholds['critical']:
            return min(100, value / thresholds['critical'] * 80)
        elif value >= thresholds['warning']:
            return 40 + (value - thresholds['warning']) / (thresholds['critical'] - thresholds['warning']) * 40
        elif value >= thresholds['normal']:
            return 20 + (value - thresholds['normal']) / (thresholds['warning'] - thresholds['normal']) * 20
        else:
            return value / thresholds['normal'] * 20

    def _is_negative_metric(self, metric_id: str) -> bool:
        """Check if higher values are negative for this metric"""
        negative_metrics = [
            'resignation_rate', 'absence_rate', 'unauthorized_absence_rate',
            'early_resignation_30', 'early_resignation_60', 'early_resignation_90'
        ]
        return metric_id in negative_metrics

    def _get_trend_icon(self, trend: str) -> str:
        """Get icon for trend"""
        icons = {
            'improving': '↓',
            'worsening': '↑',
            'stable': '→'
        }
        return icons.get(trend, '→')

    def _get_status_badge(self, status: str) -> str:
        """Get HTML badge for status"""
        badges = {
            'critical': '<span class="badge bg-danger">Critical</span>',
            'warning': '<span class="badge bg-warning">Warning</span>',
            'normal': '<span class="badge bg-success">Normal</span>'
        }
        return badges.get(status, '<span class="badge bg-secondary">Unknown</span>')

    def _get_risk_color(self, risk_score: float) -> str:
        """Get color based on risk score"""
        if risk_score >= 80:
            return 'danger'
        elif risk_score >= 60:
            return 'warning'
        else:
            return 'success'

    def _get_recommended_action(self, status: str) -> str:
        """Get recommended action based on status"""
        actions = {
            'critical': 'Immediate intervention required - Schedule team meeting within 48 hours',
            'warning': 'Close monitoring needed - Review team practices and provide support',
            'normal': 'Continue current practices with regular monitoring'
        }
        return actions.get(status, 'Monitor situation')

    def _get_individual_action(self, issue_type: str) -> str:
        """Get recommended action for individual issues"""
        actions = {
            'early_resignation_risk': 'Schedule 1-on-1 meeting, review onboarding process',
            'high_absence': 'Conduct wellness check, review workload and support needs',
            'performance_issue': 'Create improvement plan with clear goals and timeline'
        }
        return actions.get(issue_type, 'Individual attention required')