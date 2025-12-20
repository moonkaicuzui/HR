"""
Metric Validator - Calculation Validation Framework
메트릭 검증기 - 계산 검증 프레임워크

Validates calculated metrics for sanity checks and provides data quality scoring.
계산된 메트릭에 대한 검증 및 데이터 품질 점수를 제공합니다.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class ValidationWarning:
    """
    Warning from metric validation
    메트릭 검증에서 발생한 경고
    """
    metric_id: str
    message_ko: str
    message_en: str
    severity: str = "warning"  # warning, error
    actual_value: Any = None
    expected_range: Optional[str] = None


@dataclass
class DataQualityScore:
    """
    Overall data quality assessment
    전체 데이터 품질 평가
    """
    score: float  # 0-100%
    total_checks: int
    passed_checks: int
    warnings: List[ValidationWarning] = field(default_factory=list)

    @property
    def grade(self) -> str:
        """Get letter grade / 등급 반환"""
        if self.score >= 95:
            return "A"
        elif self.score >= 85:
            return "B"
        elif self.score >= 70:
            return "C"
        elif self.score >= 50:
            return "D"
        return "F"

    @property
    def grade_color(self) -> str:
        """Get grade color for display / 표시용 등급 색상"""
        colors = {
            "A": "#28a745",
            "B": "#17a2b8",
            "C": "#ffc107",
            "D": "#fd7e14",
            "F": "#dc3545"
        }
        return colors.get(self.grade, "#6c757d")


class MetricValidator:
    """
    Validates HR metrics for sanity and data quality
    HR 메트릭의 정합성 및 데이터 품질 검증
    """

    def __init__(self):
        """Initialize validator with config / 설정으로 검증기 초기화"""
        self._config = self._load_config()
        self._validation_rules = self._config.get('validation_rules', {})
        self.warnings: List[ValidationWarning] = []

    def _load_config(self) -> Dict[str, Any]:
        """Load validation config / 검증 설정 로드"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "metric_definitions.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def validate_metrics(self, metrics: Dict[str, Any]) -> DataQualityScore:
        """
        Validate all metrics and return quality score
        모든 메트릭 검증 및 품질 점수 반환

        Args:
            metrics: Dictionary of calculated metrics / 계산된 메트릭 딕셔너리

        Returns:
            DataQualityScore with overall assessment / 전체 평가를 포함한 품질 점수
        """
        self.warnings = []
        checks_passed = 0
        total_checks = 0

        # 1. Validate percentage metrics are in range [0, 100]
        # 백분율 메트릭이 [0, 100] 범위인지 검증
        percentage_metrics = [
            'absence_rate', 'absence_rate_excl_maternity',
            'unauthorized_absence_rate', 'resignation_rate',
            'attendance_rate'
        ]

        for metric_id in percentage_metrics:
            if metric_id in metrics:
                total_checks += 1
                value = metrics[metric_id]
                if isinstance(value, (int, float)):
                    if 0 <= value <= 100:
                        checks_passed += 1
                    else:
                        self.warnings.append(ValidationWarning(
                            metric_id=metric_id,
                            message_ko=f"{metric_id}: {value}%는 유효 범위(0-100%)를 벗어남",
                            message_en=f"{metric_id}: {value}% is outside valid range (0-100%)",
                            severity="error",
                            actual_value=value,
                            expected_range="0-100%"
                        ))

        # 2. Validate rate anomaly thresholds
        # 비율 이상치 임계치 검증
        anomaly_thresholds = self._validation_rules.get('rate_anomaly_thresholds', {})

        if 'absence_rate' in metrics:
            total_checks += 1
            max_absence = anomaly_thresholds.get('absence_rate_max', 50)
            if metrics['absence_rate'] <= max_absence:
                checks_passed += 1
            else:
                self.warnings.append(ValidationWarning(
                    metric_id='absence_rate',
                    message_ko=f"결근율 {metrics['absence_rate']}%가 비정상적으로 높음",
                    message_en=f"Absence rate {metrics['absence_rate']}% is abnormally high",
                    severity="warning",
                    actual_value=metrics['absence_rate'],
                    expected_range=f"≤{max_absence}%"
                ))

        if 'resignation_rate' in metrics:
            total_checks += 1
            max_resignation = anomaly_thresholds.get('resignation_rate_max', 30)
            if metrics['resignation_rate'] <= max_resignation:
                checks_passed += 1
            else:
                self.warnings.append(ValidationWarning(
                    metric_id='resignation_rate',
                    message_ko=f"퇴사율 {metrics['resignation_rate']}%가 비정상적으로 높음",
                    message_en=f"Resignation rate {metrics['resignation_rate']}% is abnormally high",
                    severity="warning",
                    actual_value=metrics['resignation_rate'],
                    expected_range=f"≤{max_resignation}%"
                ))

        # 3. Validate count metrics are non-negative
        # 카운트 메트릭이 음수가 아닌지 검증
        count_metrics = [
            'total_employees', 'recent_hires', 'recent_resignations',
            'under_60_days', 'long_term_employees', 'data_errors'
        ]

        for metric_id in count_metrics:
            if metric_id in metrics:
                total_checks += 1
                value = metrics[metric_id]
                if isinstance(value, (int, float)) and value >= 0:
                    checks_passed += 1
                else:
                    self.warnings.append(ValidationWarning(
                        metric_id=metric_id,
                        message_ko=f"{metric_id}: {value}는 음수일 수 없음",
                        message_en=f"{metric_id}: {value} cannot be negative",
                        severity="error",
                        actual_value=value,
                        expected_range="≥0"
                    ))

        # 4. Validate logical relationships
        # 논리적 관계 검증
        if 'recent_resignations' in metrics and 'total_employees' in metrics:
            total_checks += 1
            if metrics['recent_resignations'] <= metrics['total_employees']:
                checks_passed += 1
            else:
                self.warnings.append(ValidationWarning(
                    metric_id='recent_resignations',
                    message_ko=f"퇴사자 수({metrics['recent_resignations']})가 총 인원({metrics['total_employees']})보다 많음",
                    message_en=f"Resignations ({metrics['recent_resignations']}) exceeds total employees ({metrics['total_employees']})",
                    severity="error",
                    actual_value=metrics['recent_resignations']
                ))

        if 'unauthorized_absence_rate' in metrics and 'absence_rate' in metrics:
            total_checks += 1
            if metrics['unauthorized_absence_rate'] <= metrics['absence_rate']:
                checks_passed += 1
            else:
                self.warnings.append(ValidationWarning(
                    metric_id='unauthorized_absence_rate',
                    message_ko=f"무단결근율({metrics['unauthorized_absence_rate']}%)이 전체 결근율({metrics['absence_rate']}%)보다 높음",
                    message_en=f"Unauthorized absence ({metrics['unauthorized_absence_rate']}%) exceeds total absence ({metrics['absence_rate']}%)",
                    severity="warning",
                    actual_value=metrics['unauthorized_absence_rate']
                ))

        # 5. Check for required metrics presence
        # 필수 메트릭 존재 여부 확인
        required_metrics = ['total_employees', 'absence_rate', 'resignation_rate']
        for metric_id in required_metrics:
            total_checks += 1
            if metric_id in metrics and metrics[metric_id] is not None:
                checks_passed += 1
            else:
                self.warnings.append(ValidationWarning(
                    metric_id=metric_id,
                    message_ko=f"필수 메트릭 '{metric_id}'이(가) 누락됨",
                    message_en=f"Required metric '{metric_id}' is missing",
                    severity="warning"
                ))

        # Calculate score
        score = (checks_passed / total_checks * 100) if total_checks > 0 else 0

        return DataQualityScore(
            score=round(score, 1),
            total_checks=total_checks,
            passed_checks=checks_passed,
            warnings=self.warnings
        )

    def get_quality_summary(self, quality_score: DataQualityScore, language: str = "ko") -> Dict[str, Any]:
        """
        Get quality summary for display
        표시용 품질 요약 반환

        Args:
            quality_score: Quality score object / 품질 점수 객체
            language: Output language (ko/en) / 출력 언어

        Returns:
            Dictionary with formatted summary / 포맷된 요약 딕셔너리
        """
        if language == "ko":
            return {
                "title": "데이터 품질",
                "score": f"{quality_score.score:.0f}%",
                "grade": quality_score.grade,
                "grade_color": quality_score.grade_color,
                "passed": f"{quality_score.passed_checks}/{quality_score.total_checks} 검증 통과",
                "warning_count": len([w for w in quality_score.warnings if w.severity == "warning"]),
                "error_count": len([w for w in quality_score.warnings if w.severity == "error"]),
                "warnings": [w.message_ko for w in quality_score.warnings]
            }
        else:
            return {
                "title": "Data Quality",
                "score": f"{quality_score.score:.0f}%",
                "grade": quality_score.grade,
                "grade_color": quality_score.grade_color,
                "passed": f"{quality_score.passed_checks}/{quality_score.total_checks} checks passed",
                "warning_count": len([w for w in quality_score.warnings if w.severity == "warning"]),
                "error_count": len([w for w in quality_score.warnings if w.severity == "error"]),
                "warnings": [w.message_en for w in quality_score.warnings]
            }
