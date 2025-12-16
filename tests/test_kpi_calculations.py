"""
test_kpi_calculations.py - Unit tests for KPI calculation logic
KPI 계산 로직에 대한 단위 테스트

Tests the accuracy and correctness of KPI calculations
KPI 계산의 정확성과 올바름을 테스트합니다
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics.hr_metric_calculator import HRMetricCalculator
from src.analytics.kpi_validator import KPIValidator, KPIValidationResult
from src.data.monthly_data_collector import MonthlyDataCollector


class TestKPICalculations:
    """Test suite for KPI calculations / KPI 계산 테스트 스위트"""

    @pytest.fixture
    def sample_manpower_data(self):
        """Create sample manpower data for testing / 테스트용 샘플 인력 데이터 생성"""
        data = {
            'Employee No': ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010'],
            'Name': [f'Employee {i}' for i in range(1, 11)],
            'Entrance Date': [
                '2024-01-15', '2024-02-01', '2024-03-10', '2024-08-15', '2025-08-20',
                '2025-09-01', '2025-09-10', '2025-09-15', '2024-06-01', '2024-07-01'
            ],
            'Stop working Date': [
                None, None, None, None, None,
                '2025-09-25', None, None, '2025-09-20', None
            ],
            'Position': ['Inspector'] * 10,
            'Team': ['Assembly'] * 5 + ['Stitching'] * 5,
            'TYPE': ['TQC'] * 6 + ['RQC'] * 4
        }
        df = pd.DataFrame(data)
        df['Entrance Date'] = pd.to_datetime(df['Entrance Date'])
        df['Stop working Date'] = pd.to_datetime(df['Stop working Date'])
        return df

    @pytest.fixture
    def sample_attendance_data(self):
        """Create sample attendance data for testing / 테스트용 샘플 출근 데이터 생성"""
        # Create 20 working days of attendance records
        employee_ids = ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010']
        dates = pd.date_range('2025-09-01', '2025-09-30', freq='B')[:20]  # Business days only

        records = []
        for emp_id in employee_ids:
            for date in dates:
                # Simulate some absences
                if emp_id == '003' and date.day in [5, 10, 15]:  # 3 absences for employee 003
                    comp_add = 'Vắng mặt'
                    reason = 'AR1'  # Unauthorized
                elif emp_id == '005' and date.day in [8, 12]:  # 2 absences for employee 005
                    comp_add = 'Vắng mặt'
                    reason = 'Thai sản'  # Maternity
                else:
                    comp_add = 'Có mặt'
                    reason = ''

                records.append({
                    'ID No': int(emp_id),
                    'Date': date,
                    'compAdd': comp_add,
                    'Reason Description': reason
                })

        return pd.DataFrame(records)

    @pytest.fixture
    def calculator(self):
        """Create calculator instance / 계산기 인스턴스 생성"""
        collector = MonthlyDataCollector(Path(__file__).parent.parent)
        return HRMetricCalculator(collector, report_date=datetime(2025, 9, 30))

    @pytest.fixture
    def validator(self):
        """Create validator instance / 검증기 인스턴스 생성"""
        return KPIValidator()

    def test_resignation_rate_calculation(self, sample_manpower_data, calculator):
        """
        Test resignation rate calculation with average monthly headcount
        월평균 인원을 사용한 퇴사율 계산 테스트
        """
        # Expected: 2 resignations (006 and 009) in September
        # At month start: 10 employees
        # At month end: 8 employees (2 resigned)
        # Average: (10 + 8) / 2 = 9
        # Rate: 2 / 9 * 100 = 22.2%

        resignation_rate = calculator._resignation_rate(sample_manpower_data, 2025, 9)

        assert resignation_rate == 22.2, f"Expected 22.2%, got {resignation_rate}%"

    def test_resignation_rate_no_resignations(self, sample_manpower_data, calculator):
        """
        Test resignation rate when no resignations occur
        퇴사자가 없을 때 퇴사율 테스트
        """
        # Change month to August (no resignations in August)
        resignation_rate = calculator._resignation_rate(sample_manpower_data, 2025, 8)

        assert resignation_rate == 0.0, f"Expected 0.0%, got {resignation_rate}%"

    def test_absence_rate_active_only(self, sample_manpower_data, sample_attendance_data, calculator):
        """
        Test absence rate calculation for active employees only
        재직자만 포함한 결근율 계산 테스트
        """
        # Should exclude employees 006 and 009 who resigned
        absence_rate = calculator._absence_rate(
            sample_attendance_data,
            sample_manpower_data,
            2025, 9
        )

        # 8 active employees * 20 days = 160 records
        # Employee 003: 3 absences, Employee 005: 2 absences = 5 total
        # Rate: 5 / 160 * 100 = 3.1%
        assert abs(absence_rate - 3.1) < 0.2, f"Expected ~3.1%, got {absence_rate}%"

    def test_absence_rate_all_employees(self, sample_manpower_data, sample_attendance_data, calculator):
        """
        Test absence rate calculation including all employees
        모든 직원을 포함한 결근율 계산 테스트
        """
        absence_rate_all = calculator._absence_rate_all(
            sample_attendance_data,
            sample_manpower_data,
            2025, 9
        )

        # 10 employees * 20 days = 200 records
        # 5 absences total
        # Rate: 5 / 200 * 100 = 2.5%
        assert absence_rate_all == 2.5, f"Expected 2.5%, got {absence_rate_all}%"

    def test_unauthorized_absence_rate(self, sample_manpower_data, sample_attendance_data, calculator):
        """
        Test unauthorized absence rate calculation
        무단결근율 계산 테스트
        """
        unauthorized_rate = calculator._unauthorized_absence_rate(
            sample_attendance_data,
            sample_manpower_data,
            2025, 9
        )

        # Employee 003 has 3 unauthorized absences (AR1)
        # 8 active employees * 20 days = 160 records
        # Rate: 3 / 160 * 100 = 1.9%
        assert abs(unauthorized_rate - 1.9) < 0.2, f"Expected ~1.9%, got {unauthorized_rate}%"

    def test_total_employees_count(self, sample_manpower_data, calculator):
        """
        Test total employees count at report date
        보고서 생성일 기준 총 직원 수 테스트
        """
        total = calculator._total_employees(sample_manpower_data, 2025, 9)

        # At report date (Sep 30): 8 active employees (006 and 009 resigned)
        assert total == 8, f"Expected 8 employees, got {total}"

    def test_recent_hires(self, sample_manpower_data, calculator):
        """
        Test recent hires count for target month
        대상 월의 신규 입사자 수 테스트
        """
        hires = calculator._recent_hires(sample_manpower_data, 2025, 9)

        # 3 hires in September: 006, 007, 008
        assert hires == 3, f"Expected 3 hires, got {hires}"

    def test_long_term_employees(self, sample_manpower_data, calculator):
        """
        Test long-term employees count (1+ year tenure)
        장기근속자 수 테스트 (1년 이상)
        """
        long_term = calculator._long_term_employees(sample_manpower_data, 2025, 9)

        # Employees with tenure >= 365 days and still active
        # Employees 001, 002, 003, 009 (009 resigned), 010
        # Active: 001, 002, 003, 010 = 4
        assert long_term == 4, f"Expected 4 long-term employees, got {long_term}"

    def test_under_60_days(self, sample_manpower_data, calculator):
        """
        Test employees with tenure under 60 days
        재직 기간 60일 미만 직원 테스트
        """
        under_60 = calculator._under_60_days(sample_manpower_data, 2025, 9)

        # Active employees with < 60 days tenure at month end
        # 005 (Aug 20), 007 (Sep 10), 008 (Sep 15) = 3
        # 006 resigned, so not counted
        assert under_60 == 3, f"Expected 3 employees under 60 days, got {under_60}"

    def test_kpi_validator_normal_range(self, validator):
        """
        Test KPI validator with normal values
        정상 범위 내 값으로 KPI 검증기 테스트
        """
        metrics = {
            'resignation_rate': 5.0,
            'absence_rate': 10.0,
            'unauthorized_absence_rate': 2.0,
            'total_employees': 100
        }

        result = validator.validate_metrics(metrics)

        assert result.is_valid, "Normal metrics should be valid"
        assert result.summary['critical_count'] == 0, "Should have no critical warnings"

    def test_kpi_validator_critical_values(self, validator):
        """
        Test KPI validator with critical values
        임계값으로 KPI 검증기 테스트
        """
        metrics = {
            'resignation_rate': 25.0,  # Critical: > 20%
            'absence_rate': 35.0,  # Critical: > 30%
            'unauthorized_absence_rate': 18.0,  # Critical: > 15%
            'total_employees': 50
        }

        result = validator.validate_metrics(metrics)

        assert not result.is_valid, "Critical metrics should be invalid"
        assert result.summary['critical_count'] >= 3, "Should have at least 3 critical warnings"

    def test_kpi_validator_consistency_check(self, validator):
        """
        Test KPI validator consistency checks
        KPI 검증기 일관성 확인 테스트
        """
        metrics = {
            'absence_rate': 10.0,
            'absence_rate_all': 5.0,  # Should not be less than active-only rate
            'unauthorized_absence_rate': 15.0  # Should not exceed total absence rate
        }

        result = validator.validate_metrics(metrics)

        # Should detect consistency issues
        consistency_warnings = [w for w in result.warnings if 'consistency' in w.metric_id]
        assert len(consistency_warnings) >= 1, "Should detect consistency issues"

    def test_kpi_validator_historical_anomaly(self, validator):
        """
        Test KPI validator historical anomaly detection
        KPI 검증기 과거 데이터 이상치 감지 테스트
        """
        current_metrics = {
            'resignation_rate': 20.0,  # Significantly higher than historical
            'absence_rate': 8.0,
            'unauthorized_absence_rate': 1.0
        }

        historical_metrics = [
            {'resignation_rate': 3.0, 'absence_rate': 7.0, 'unauthorized_absence_rate': 0.8},
            {'resignation_rate': 2.5, 'absence_rate': 8.5, 'unauthorized_absence_rate': 1.2},
            {'resignation_rate': 3.5, 'absence_rate': 6.5, 'unauthorized_absence_rate': 0.9},
            {'resignation_rate': 2.8, 'absence_rate': 7.8, 'unauthorized_absence_rate': 1.1}
        ]

        result = validator.validate_metrics(current_metrics, historical_metrics)

        # Should detect anomaly in resignation rate
        historical_warnings = [w for w in result.warnings if w.historical_avg is not None]
        assert len(historical_warnings) >= 1, "Should detect historical anomalies"

    def test_edge_case_zero_employees(self, calculator):
        """
        Test edge case with zero employees
        직원이 0명인 엣지 케이스 테스트
        """
        empty_df = pd.DataFrame()

        resignation_rate = calculator._resignation_rate(empty_df, 2025, 9)
        total = calculator._total_employees(empty_df, 2025, 9)

        assert resignation_rate == 0.0, "Should handle empty data gracefully"
        assert total == 0, "Should return 0 for empty data"

    def test_edge_case_all_resigned(self, sample_manpower_data, calculator):
        """
        Test edge case where all employees resigned
        모든 직원이 퇴사한 엣지 케이스 테스트
        """
        # Set all employees as resigned
        sample_manpower_data['Stop working Date'] = pd.Timestamp('2025-09-15')

        resignation_rate = calculator._resignation_rate(sample_manpower_data, 2025, 9)
        total = calculator._total_employees(sample_manpower_data, 2025, 9)

        # All 10 resigned, average = (10 + 0) / 2 = 5
        # Rate = 10 / 5 * 100 = 200%
        assert resignation_rate == 200.0, f"Expected 200%, got {resignation_rate}%"
        assert total == 0, "Should have 0 active employees"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])