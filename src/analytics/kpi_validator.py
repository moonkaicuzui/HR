"""
kpi_validator.py - KPI Validation and Anomaly Detection System
KPI 검증 및 이상치 감지 시스템

Validates calculated KPIs and detects anomalies or suspicious values
계산된 KPI를 검증하고 이상치나 의심스러운 값을 감지합니다

Core Features / 핵심 기능:
- Threshold validation / 임계값 검증
- Anomaly detection / 이상치 감지
- Historical comparison / 과거 데이터 비교
- Warning generation / 경고 생성
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from ..utils.logger import get_logger


@dataclass
class ValidationWarning:
    """
    KPI validation warning
    KPI 검증 경고
    """
    metric_id: str
    severity: str  # "critical", "warning", "info"
    value: float
    message_ko: str
    message_en: str
    threshold: Optional[float] = None
    historical_avg: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KPIValidationResult:
    """
    Result of KPI validation
    KPI 검증 결과
    """
    is_valid: bool
    warnings: List[ValidationWarning]
    summary: Dict[str, Any]
    recommendations: List[str]


class KPIValidator:
    """
    KPI Validator with anomaly detection
    이상치 감지 기능이 있는 KPI 검증기
    """

    def __init__(self):
        """Initialize KPIValidator"""
        self.logger = get_logger()

        # Define normal ranges for each KPI
        # 각 KPI의 정상 범위 정의
        self.normal_ranges = {
            'resignation_rate': {'min': 0, 'max': 15, 'warning_max': 10},
            'absence_rate': {'min': 0, 'max': 20, 'warning_max': 15},
            'absence_rate_all': {'min': 0, 'max': 20, 'warning_max': 15},
            'unauthorized_absence_rate': {'min': 0, 'max': 10, 'warning_max': 5},
            'perfect_attendance': {'min': 10, 'max': 100, 'warning_min': 20},
            'total_employees': {'min': 10, 'max': 10000, 'warning_min': 50}
        }

        # Define critical thresholds that require immediate attention
        # 즉각적인 주의가 필요한 임계값 정의
        self.critical_thresholds = {
            'resignation_rate': 20,  # >20% resignation is critical
            'absence_rate': 30,  # >30% absence is critical
            'unauthorized_absence_rate': 15  # >15% unauthorized absence is critical
        }

    def validate_metrics(
        self,
        current_metrics: Dict[str, Any],
        historical_metrics: Optional[List[Dict[str, Any]]] = None
    ) -> KPIValidationResult:
        """
        Validate current metrics and detect anomalies
        현재 메트릭을 검증하고 이상치 감지

        Args:
            current_metrics: Current month's calculated metrics / 현재 월의 계산된 메트릭
            historical_metrics: Previous months' metrics for comparison / 비교용 이전 월 메트릭

        Returns:
            KPIValidationResult with warnings and recommendations
        """
        warnings = []

        # 1. Check for abnormal values
        # 비정상적인 값 확인
        for metric_id, value in current_metrics.items():
            if metric_id in self.normal_ranges and isinstance(value, (int, float)):
                warning = self._check_range(metric_id, value)
                if warning:
                    warnings.append(warning)

                # Check critical thresholds
                # 임계값 확인
                if metric_id in self.critical_thresholds:
                    if value > self.critical_thresholds[metric_id]:
                        warnings.append(ValidationWarning(
                            metric_id=metric_id,
                            severity="critical",
                            value=value,
                            message_ko=f"{metric_id}가 임계값 {self.critical_thresholds[metric_id]}%를 초과했습니다: {value}%",
                            message_en=f"{metric_id} exceeds critical threshold of {self.critical_thresholds[metric_id]}%: {value}%",
                            threshold=self.critical_thresholds[metric_id]
                        ))

        # 2. Check for data consistency
        # 데이터 일관성 확인
        consistency_warnings = self._check_consistency(current_metrics)
        warnings.extend(consistency_warnings)

        # 3. Compare with historical data if available
        # 가능한 경우 과거 데이터와 비교
        if historical_metrics:
            historical_warnings = self._check_historical_anomalies(current_metrics, historical_metrics)
            warnings.extend(historical_warnings)

        # 4. Check for zero or null values in critical metrics
        # 중요 메트릭의 0 또는 null 값 확인
        zero_warnings = self._check_zero_values(current_metrics)
        warnings.extend(zero_warnings)

        # Generate recommendations
        # 권장사항 생성
        recommendations = self._generate_recommendations(warnings)

        # Build summary
        # 요약 생성
        summary = {
            'total_warnings': len(warnings),
            'critical_count': len([w for w in warnings if w.severity == 'critical']),
            'warning_count': len([w for w in warnings if w.severity == 'warning']),
            'info_count': len([w for w in warnings if w.severity == 'info']),
            'validation_timestamp': datetime.now().isoformat()
        }

        is_valid = summary['critical_count'] == 0

        self.logger.info(
            "KPI 검증 완료",
            "KPI validation completed",
            total_warnings=len(warnings),
            critical=summary['critical_count']
        )

        return KPIValidationResult(
            is_valid=is_valid,
            warnings=warnings,
            summary=summary,
            recommendations=recommendations
        )

    def _check_range(self, metric_id: str, value: float) -> Optional[ValidationWarning]:
        """
        Check if value is within normal range
        값이 정상 범위 내에 있는지 확인
        """
        ranges = self.normal_ranges[metric_id]

        if value < ranges['min'] or value > ranges['max']:
            severity = "critical"
            message_ko = f"{metric_id}가 정상 범위를 벗어났습니다: {value} (정상: {ranges['min']}-{ranges['max']})"
            message_en = f"{metric_id} is out of normal range: {value} (normal: {ranges['min']}-{ranges['max']})"
        elif 'warning_max' in ranges and value > ranges['warning_max']:
            severity = "warning"
            message_ko = f"{metric_id}가 경고 수준입니다: {value} (경고: >{ranges['warning_max']})"
            message_en = f"{metric_id} is at warning level: {value} (warning: >{ranges['warning_max']})"
        elif 'warning_min' in ranges and value < ranges['warning_min']:
            severity = "warning"
            message_ko = f"{metric_id}가 경고 수준입니다: {value} (경고: <{ranges['warning_min']})"
            message_en = f"{metric_id} is at warning level: {value} (warning: <{ranges['warning_min']})"
        else:
            return None

        return ValidationWarning(
            metric_id=metric_id,
            severity=severity,
            value=value,
            message_ko=message_ko,
            message_en=message_en
        )

    def _check_consistency(self, metrics: Dict[str, Any]) -> List[ValidationWarning]:
        """
        Check internal consistency of metrics
        메트릭의 내부 일관성 확인
        """
        warnings = []

        # Check if absence_rate_all is less than absence_rate (should not happen)
        # absence_rate_all이 absence_rate보다 작은지 확인 (발생하면 안됨)
        if 'absence_rate' in metrics and 'absence_rate_all' in metrics:
            if isinstance(metrics['absence_rate'], (int, float)) and isinstance(metrics['absence_rate_all'], (int, float)):
                if metrics['absence_rate_all'] < metrics['absence_rate'] - 0.5:  # Allow small difference
                    warnings.append(ValidationWarning(
                        metric_id='absence_rate_consistency',
                        severity='warning',
                        value=metrics['absence_rate'],
                        message_ko=f"재직자 결근율({metrics['absence_rate']}%)이 전체 결근율({metrics['absence_rate_all']}%)보다 높습니다",
                        message_en=f"Active employee absence rate ({metrics['absence_rate']}%) is higher than total absence rate ({metrics['absence_rate_all']}%)",
                        metadata={'absence_rate': metrics['absence_rate'], 'absence_rate_all': metrics['absence_rate_all']}
                    ))

        # Check if unauthorized absence rate is higher than total absence rate
        # 무단결근율이 전체 결근율보다 높은지 확인
        if 'unauthorized_absence_rate' in metrics and 'absence_rate' in metrics:
            if isinstance(metrics['unauthorized_absence_rate'], (int, float)) and isinstance(metrics['absence_rate'], (int, float)):
                if metrics['unauthorized_absence_rate'] > metrics['absence_rate']:
                    warnings.append(ValidationWarning(
                        metric_id='unauthorized_absence_consistency',
                        severity='critical',
                        value=metrics['unauthorized_absence_rate'],
                        message_ko=f"무단결근율({metrics['unauthorized_absence_rate']}%)이 전체 결근율({metrics['absence_rate']}%)보다 높습니다",
                        message_en=f"Unauthorized absence rate ({metrics['unauthorized_absence_rate']}%) is higher than total absence rate ({metrics['absence_rate']}%)",
                        metadata={'unauthorized': metrics['unauthorized_absence_rate'], 'total': metrics['absence_rate']}
                    ))

        return warnings

    def _check_historical_anomalies(
        self,
        current: Dict[str, Any],
        historical: List[Dict[str, Any]]
    ) -> List[ValidationWarning]:
        """
        Check for anomalies compared to historical data
        과거 데이터와 비교하여 이상치 확인
        """
        warnings = []

        if not historical or len(historical) < 3:
            return warnings  # Need at least 3 months for meaningful comparison

        # Calculate historical averages and standard deviations
        # 과거 평균 및 표준편차 계산
        for metric_id in ['resignation_rate', 'absence_rate', 'unauthorized_absence_rate']:
            if metric_id in current and isinstance(current[metric_id], (int, float)):
                historical_values = []
                for h_metrics in historical:
                    if metric_id in h_metrics and isinstance(h_metrics[metric_id], (int, float)):
                        historical_values.append(h_metrics[metric_id])

                if len(historical_values) >= 3:
                    avg = np.mean(historical_values)
                    std = np.std(historical_values)
                    current_value = current[metric_id]

                    # Check if current value is more than 2 standard deviations from mean
                    # 현재 값이 평균에서 2 표준편차 이상 벗어났는지 확인
                    if std > 0 and abs(current_value - avg) > 2 * std:
                        severity = "warning" if abs(current_value - avg) <= 3 * std else "critical"
                        change_pct = ((current_value - avg) / avg * 100) if avg != 0 else 0

                        warnings.append(ValidationWarning(
                            metric_id=metric_id,
                            severity=severity,
                            value=current_value,
                            message_ko=f"{metric_id}가 과거 평균({avg:.1f})에서 크게 벗어났습니다: {current_value:.1f} (변화율: {change_pct:+.1f}%)",
                            message_en=f"{metric_id} deviates significantly from historical average ({avg:.1f}): {current_value:.1f} (change: {change_pct:+.1f}%)",
                            historical_avg=avg,
                            metadata={'std_dev': std, 'change_pct': change_pct}
                        ))

        return warnings

    def _check_zero_values(self, metrics: Dict[str, Any]) -> List[ValidationWarning]:
        """
        Check for unexpected zero or null values
        예상치 못한 0 또는 null 값 확인
        """
        warnings = []

        critical_metrics = ['total_employees']

        for metric_id in critical_metrics:
            if metric_id in metrics:
                value = metrics[metric_id]
                if value is None or value == 0:
                    warnings.append(ValidationWarning(
                        metric_id=metric_id,
                        severity='critical',
                        value=0,
                        message_ko=f"{metric_id}가 0이거나 null입니다. 데이터를 확인하세요.",
                        message_en=f"{metric_id} is zero or null. Please check the data."
                    ))

        return warnings

    def _generate_recommendations(self, warnings: List[ValidationWarning]) -> List[str]:
        """
        Generate recommendations based on warnings
        경고를 기반으로 권장사항 생성
        """
        recommendations = []

        # Check for critical warnings
        critical_warnings = [w for w in warnings if w.severity == 'critical']

        if any(w.metric_id == 'resignation_rate' for w in critical_warnings):
            recommendations.append("퇴사율이 높습니다. 퇴사 면담 데이터를 분석하고 근무 환경 개선 방안을 검토하세요.")
            recommendations.append("High resignation rate. Analyze exit interview data and review workplace improvements.")

        if any(w.metric_id == 'absence_rate' for w in critical_warnings):
            recommendations.append("결근율이 높습니다. 근태 관리 정책을 검토하고 직원 건강 프로그램을 고려하세요.")
            recommendations.append("High absence rate. Review attendance policies and consider employee wellness programs.")

        if any(w.metric_id == 'unauthorized_absence_rate' for w in critical_warnings):
            recommendations.append("무단결근율이 높습니다. 즉시 관리자와 상담하고 징계 절차를 검토하세요.")
            recommendations.append("High unauthorized absence rate. Consult with management immediately and review disciplinary procedures.")

        if any('consistency' in w.metric_id for w in warnings):
            recommendations.append("데이터 일관성 문제가 발견되었습니다. 원본 데이터를 재확인하세요.")
            recommendations.append("Data consistency issues detected. Please verify source data.")

        return recommendations