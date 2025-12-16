"""
test_enhanced_modals.py - Test Enhanced Modal Generation
향상된 모달 생성 테스트

Tests the enhanced modal generator for management insights
관리 인사이트를 위한 향상된 모달 생성기 테스트
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.visualization.enhanced_modal_generator import EnhancedModalGenerator
from src.utils.i18n import I18n
from src.utils.logger import get_logger
from src.data.monthly_data_collector import MonthlyDataCollector
from src.analytics.hr_metric_calculator import HRMetricCalculator


class TestEnhancedModalGenerator:
    """Test suite for enhanced modal generator / 향상된 모달 생성기 테스트 스위트"""

    @pytest.fixture
    def generator(self):
        """Create generator instance / 생성기 인스턴스 생성"""
        i18n = I18n(default_lang='ko')
        logger = get_logger()
        collector = MonthlyDataCollector(Path(__file__).parent.parent)
        calculator = HRMetricCalculator(collector)
        return EnhancedModalGenerator(i18n, calculator, logger)

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing / 테스트용 샘플 데이터 생성"""
        data = {
            'Employee No': ['001', '002', '003', '004', '005'],
            'Name': [f'Employee {i}' for i in range(1, 6)],
            'Team': ['Assembly', 'Assembly', 'Stitching', 'Stitching', 'OSC'],
            'Entrance Date': pd.date_range('2024-01-01', periods=5, freq='M'),
            'Stop working Date': [None, None, '2025-09-15', None, None],
            'Position': ['Inspector'] * 5,
            'TYPE': ['TQC'] * 3 + ['RQC'] * 2
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def attendance_data(self):
        """Create sample attendance data / 샘플 출근 데이터 생성"""
        records = []
        for emp_id in ['001', '002', '003', '004', '005']:
            for i in range(20):  # 20 working days
                records.append({
                    'ID No': int(emp_id),
                    'Date': pd.Timestamp('2025-09-01') + pd.Timedelta(days=i),
                    'compAdd': 'Có mặt' if np.random.random() > 0.1 else 'Vắng mặt',
                    'Reason Description': 'AR1' if np.random.random() > 0.5 else ''
                })
        return pd.DataFrame(records)

    def test_modal_generation(self, generator, sample_data, attendance_data):
        """
        Test basic modal generation
        기본 모달 생성 테스트
        """
        historical_data = {'2025-09': sample_data, '2025-08': sample_data}

        modal_html = generator.generate_enhanced_modal(
            modal_id='test_modal',
            metric_id='resignation_rate',
            current_data=sample_data,
            historical_data=historical_data,
            attendance_data=attendance_data
        )

        # Check that HTML was generated
        assert modal_html is not None
        assert len(modal_html) > 0
        assert 'modal fade' in modal_html
        assert 'Management Insights' in modal_html

    def test_team_analysis(self, generator, sample_data, attendance_data):
        """
        Test team analysis functionality
        팀 분석 기능 테스트
        """
        team_analysis = generator._analyze_teams(
            'resignation_rate', sample_data, attendance_data
        )

        # Check team analysis structure
        assert 'team_metrics' in team_analysis
        assert 'problematic_teams' in team_analysis
        assert 'average_value' in team_analysis
        assert 'worst_team' in team_analysis

        # Check team metrics
        assert len(team_analysis['team_metrics']) > 0
        for tm in team_analysis['team_metrics']:
            assert 'team' in tm
            assert 'value' in tm
            assert 'status' in tm
            assert 'risk_score' in tm

    def test_individual_analysis(self, generator, sample_data, attendance_data):
        """
        Test individual analysis functionality
        개인 분석 기능 테스트
        """
        problematic_teams = ['Assembly', 'Stitching']
        individual_analysis = generator._analyze_individuals(
            'absence_rate', sample_data, attendance_data, problematic_teams
        )

        # Check individual analysis structure
        assert 'individuals' in individual_analysis
        assert 'total_count' in individual_analysis
        assert 'high_priority_count' in individual_analysis

    def test_month_over_month_comparison(self, generator, sample_data):
        """
        Test month-over-month comparison
        전월 대비 비교 테스트
        """
        historical_data = {
            '2025-08': sample_data,
            '2025-09': sample_data
        }

        mom_comparison = generator._get_month_over_month(
            'resignation_rate', historical_data
        )

        # Check comparison structure
        assert 'current_value' in mom_comparison
        assert 'previous_value' in mom_comparison
        assert 'change' in mom_comparison
        assert 'change_percent' in mom_comparison
        assert 'trend' in mom_comparison

    def test_management_priorities(self, generator):
        """
        Test management priority calculation
        관리 우선순위 계산 테스트
        """
        team_analysis = {
            'team_metrics': [
                {'team': 'Assembly', 'value': 25, 'status': 'critical', 'risk_score': 85},
                {'team': 'Stitching', 'value': 15, 'status': 'warning', 'risk_score': 60}
            ],
            'problematic_teams': ['Assembly'],
            'average_value': 20,
            'worst_team': {'team': 'Assembly'}
        }

        individual_analysis = {
            'individuals': [
                {
                    'employee_no': '001',
                    'name': 'Employee 1',
                    'team': 'Assembly',
                    'issue_type': 'high_absence',
                    'value': 25,
                    'priority': 'high'
                }
            ],
            'total_count': 1,
            'high_priority_count': 1
        }

        mom_comparison = {
            'current_value': 20,
            'previous_value': 15,
            'change': 5,
            'change_percent': 33.3,
            'trend': 'worsening'
        }

        priorities = generator._calculate_management_priorities(
            team_analysis, individual_analysis, mom_comparison
        )

        # Check priorities
        assert len(priorities) > 0
        for priority in priorities:
            assert 'type' in priority
            assert 'target' in priority
            assert 'action' in priority
            assert 'priority_level' in priority

    def test_modal_html_structure(self, generator, sample_data, attendance_data):
        """
        Test modal HTML structure
        모달 HTML 구조 테스트
        """
        historical_data = {'2025-09': sample_data}

        modal_html = generator.generate_enhanced_modal(
            modal_id='test_modal',
            metric_id='absence_rate',
            current_data=sample_data,
            historical_data=historical_data,
            attendance_data=attendance_data
        )

        # Check for key HTML elements
        assert 'nav-tabs' in modal_html
        assert 'Overview' in modal_html
        assert 'Team Analysis' in modal_html
        assert 'Individual Details' in modal_html
        assert 'Management Priorities' in modal_html
        assert 'tab-content' in modal_html

    def test_risk_scoring(self, generator):
        """
        Test risk score calculation
        위험 점수 계산 테스트
        """
        # Test critical level
        risk_score = generator._calculate_risk_score('resignation_rate', 25)
        assert risk_score >= 80

        # Test warning level
        risk_score = generator._calculate_risk_score('resignation_rate', 18)
        assert 40 <= risk_score < 80

        # Test normal level
        risk_score = generator._calculate_risk_score('resignation_rate', 5)
        assert risk_score < 40

    def test_status_determination(self, generator):
        """
        Test status determination based on thresholds
        임계값 기반 상태 결정 테스트
        """
        # Test critical status
        status = generator._get_status('resignation_rate', 25)
        assert status == 'critical'

        # Test warning status
        status = generator._get_status('resignation_rate', 18)
        assert status == 'warning'

        # Test normal status
        status = generator._get_status('resignation_rate', 5)
        assert status == 'normal'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])