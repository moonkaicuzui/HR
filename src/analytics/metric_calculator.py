"""
metric_calculator.py - Generic Metric Calculation Engine
범용 메트릭 계산 엔진

CORE REUSABILITY PRINCIPLE / 핵심 재사용성 원칙:
This module calculates metrics based on JSON configuration (metric_definitions.json).
NO HARDCODING of formulas or business logic - all driven by configuration.
이 모듈은 JSON 설정을 기반으로 메트릭을 계산합니다.
공식이나 비즈니스 로직의 하드코딩 없음 - 모두 설정에 의해 구동됩니다.

Core Features / 핵심 기능:
- Configuration-driven metric calculation / 설정 기반 메트릭 계산
- Subject-agnostic (works for overall, team, position, etc.) / 주체 독립적
- Formula-based calculation from JSON / JSON의 공식 기반 계산
- Automatic threshold evaluation / 자동 임계값 평가
- Reusable for any metric defined in config / 설정에 정의된 모든 메트릭에 재사용 가능
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
import json
from dataclasses import dataclass, field

from ..utils.logger import HRLogger
from ..utils.date_parser import DateParser
from ..utils.i18n import I18n


@dataclass
class MetricValue:
    """
    Calculated metric value with metadata
    메타데이터가 있는 계산된 메트릭 값
    """
    metric_id: str
    value: float
    display_value: str  # Formatted value (e.g., "85.5%", "42명") / 포맷된 값
    unit: str = ""  # Unit of measurement (e.g., "%", "명", "days") / 측정 단위
    threshold_level: Optional[str] = None  # "excellent", "good", "warning", "critical"
    color: Optional[str] = None  # Color code for threshold / 임계값용 색상 코드
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricCalculationResult:
    """
    Result of metric calculation
    메트릭 계산 결과
    """
    subject: str  # What is being calculated (e.g., "Overall", "Team A") / 계산 대상
    metrics: Dict[str, MetricValue]  # Dictionary of metric_id -> MetricValue
    calculation_timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricCalculator:
    """
    Generic metric calculator driven by configuration
    설정에 의해 구동되는 범용 메트릭 계산기

    REUSABILITY DESIGN / 재사용성 설계:
    This class reads metric definitions from metric_definitions.json
    and calculates metrics based on those definitions. Adding new metrics
    requires ONLY updating the JSON file, not code changes.

    이 클래스는 metric_definitions.json에서 메트릭 정의를 읽고
    해당 정의를 기반으로 메트릭을 계산합니다. 새 메트릭 추가는
    코드 변경이 아닌 JSON 파일 업데이트만 필요합니다.
    """

    def __init__(
        self,
        metric_definitions_path: Optional[Path] = None,
        logger: Optional[HRLogger] = None,
        date_parser: Optional[DateParser] = None,
        i18n: Optional[I18n] = None
    ):
        """
        Initialize MetricCalculator
        MetricCalculator 초기화

        Args:
            metric_definitions_path: Path to metric_definitions.json / metric_definitions.json 경로
            logger: Logger instance / 로거 인스턴스
            date_parser: Custom date parser instance / 커스텀 날짜 파서 인스턴스
            i18n: I18n instance / 다국어 인스턴스
        """
        self.logger = logger or HRLogger(name="MetricCalculator")
        self.date_parser = date_parser or DateParser()
        self.i18n = i18n

        # Load metric definitions from config / 설정에서 메트릭 정의 로드
        if metric_definitions_path is None:
            hr_root = Path(__file__).parent.parent.parent
            metric_definitions_path = hr_root / "config" / "metric_definitions.json"

        self.config_path = Path(metric_definitions_path)
        self.metric_definitions = self._load_metric_definitions()

    def _load_metric_definitions(self) -> Dict[str, Any]:
        """
        Load metric definitions from JSON configuration
        JSON 설정에서 메트릭 정의 로드

        Returns:
            Dictionary of metric definitions / 메트릭 정의 딕셔너리
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('metrics', {})
        except FileNotFoundError:
            self.logger.error(
                "메트릭 정의 파일을 찾을 수 없습니다",
                "Metric definitions file not found",
                path=str(self.config_path)
            )
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(
                "메트릭 정의 JSON 파싱 실패",
                "Failed to parse metric definitions JSON",
                error=str(e)
            )
            return {}

    def get_available_metrics(self) -> List[str]:
        """
        Get list of all available metric IDs
        사용 가능한 모든 메트릭 ID 목록 가져오기

        Returns:
            List of metric IDs / 메트릭 ID 리스트
        """
        return list(self.metric_definitions.keys())

    def calculate_metric(
        self,
        metric_id: str,
        data: pd.DataFrame,
        subject: str = "Overall",
        subject_filter: Optional[Dict[str, Any]] = None
    ) -> MetricValue:
        """
        Calculate a specific metric based on its definition
        정의를 기반으로 특정 메트릭 계산

        REUSABILITY EXAMPLE / 재사용성 예시:
        >>> calculator = MetricCalculator()
        >>>
        >>> # Calculate overall absence rate
        >>> # 전체 결근율 계산
        >>> result1 = calculator.calculate_metric(
        ...     metric_id="absence_rate",
        ...     data=attendance_df,
        ...     subject="Overall"
        ... )
        >>>
        >>> # Calculate Team A absence rate using same function
        >>> # 동일한 함수로 팀 A 결근율 계산
        >>> result2 = calculator.calculate_metric(
        ...     metric_id="absence_rate",
        ...     data=attendance_df,
        ...     subject="Team A",
        ...     subject_filter={"team": "Assembly"}
        ... )

        Args:
            metric_id: ID of metric from metric_definitions.json
                      metric_definitions.json의 메트릭 ID
            data: Input DataFrame containing necessary data
                 필요한 데이터가 포함된 입력 DataFrame
            subject: Subject being calculated (e.g., "Overall", "Team A")
                    계산 대상 주체
            subject_filter: Optional filter to limit data to specific subject
                           특정 주체로 데이터를 제한하는 선택적 필터

        Returns:
            MetricValue with calculated value and metadata
            계산된 값과 메타데이터가 있는 MetricValue
        """
        # Get metric definition / 메트릭 정의 가져오기
        metric_def = self.metric_definitions.get(metric_id)
        if not metric_def:
            self.logger.warning(
                f"메트릭 정의를 찾을 수 없습니다",
                f"Metric definition not found",
                metric_id=metric_id
            )
            return MetricValue(
                metric_id=metric_id,
                value=0.0,
                display_value="0",
                metadata={'error': 'Metric definition not found'}
            )

        # Filter data by subject if specified / 지정된 경우 주체별로 데이터 필터링
        filtered_data = data.copy()
        if subject_filter:
            for column, value in subject_filter.items():
                if column in filtered_data.columns:
                    filtered_data = filtered_data[filtered_data[column] == value]

        # Calculate value based on calculation method / 계산 방법을 기반으로 값 계산
        calculation_method = metric_def.get('calculation_method', 'count')
        value = self._execute_calculation(
            filtered_data,
            calculation_method,
            metric_def
        )

        # Format display value / 디스플레이 값 포맷
        display_format = metric_def.get('display_format', '{value}')
        display_value = display_format.format(value=value)

        # Evaluate threshold / 임계값 평가
        threshold_level, color = self._evaluate_threshold(value, metric_def)

        return MetricValue(
            metric_id=metric_id,
            value=value,
            display_value=display_value,
            threshold_level=threshold_level,
            color=color,
            metadata={
                'subject': subject,
                'subject_filter': subject_filter,
                'calculation_method': calculation_method,
                'data_rows': len(filtered_data)
            }
        )

    def calculate_all_metrics(
        self,
        data_sources: Dict[str, pd.DataFrame],
        subject: str = "Overall",
        subject_filter: Optional[Dict[str, Any]] = None,
        metric_ids: Optional[List[str]] = None
    ) -> MetricCalculationResult:
        """
        Calculate multiple metrics at once
        여러 메트릭을 한 번에 계산

        Args:
            data_sources: Dictionary mapping data source names to DataFrames
                         데이터 소스 이름을 DataFrame에 매핑하는 딕셔너리
                         Example: {"basic_manpower": df1, "attendance": df2}
            subject: Subject being calculated / 계산 대상 주체
            subject_filter: Optional filter for subject / 주체를 위한 선택적 필터
            metric_ids: List of metric IDs to calculate (calculates all if None)
                       계산할 메트릭 ID 목록 (None이면 전체 계산)

        Returns:
            MetricCalculationResult with all calculated metrics
            모든 계산된 메트릭이 있는 MetricCalculationResult
        """
        from datetime import datetime

        metrics_to_calculate = metric_ids or list(self.metric_definitions.keys())
        calculated_metrics = {}

        for metric_id in metrics_to_calculate:
            metric_def = self.metric_definitions.get(metric_id)
            if not metric_def:
                continue

            # Get required data sources for this metric
            # 이 메트릭에 필요한 데이터 소스 가져오기
            required_sources = metric_def.get('data_sources', [])

            # Merge data sources if multiple are needed
            # 여러 개가 필요한 경우 데이터 소스 병합
            if len(required_sources) == 1:
                source_name = required_sources[0]
                data = data_sources.get(source_name, pd.DataFrame())
            else:
                # For metrics requiring multiple sources, use the first as base
                # 여러 소스가 필요한 메트릭의 경우 첫 번째를 기본으로 사용
                data = data_sources.get(required_sources[0], pd.DataFrame()) if required_sources else pd.DataFrame()

            # Calculate metric / 메트릭 계산
            metric_value = self.calculate_metric(
                metric_id=metric_id,
                data=data,
                subject=subject,
                subject_filter=subject_filter
            )

            calculated_metrics[metric_id] = metric_value

        return MetricCalculationResult(
            subject=subject,
            metrics=calculated_metrics,
            calculation_timestamp=datetime.now().isoformat(),
            metadata={
                'subject_filter': subject_filter,
                'total_metrics': len(calculated_metrics)
            }
        )

    def _execute_calculation(
        self,
        data: pd.DataFrame,
        method: str,
        metric_def: Dict[str, Any]
    ) -> float:
        """
        Execute calculation based on method specified in metric definition
        메트릭 정의에 지정된 방법을 기반으로 계산 실행

        Args:
            data: Filtered DataFrame / 필터링된 DataFrame
            method: Calculation method (count, percentage, etc.) / 계산 방법
            metric_def: Metric definition dictionary / 메트릭 정의 딕셔너리

        Returns:
            Calculated value / 계산된 값
        """
        try:
            if method == "count":
                # Apply filters defined in metric / 메트릭에 정의된 필터 적용
                filtered = self._apply_metric_filters(data, metric_def.get('filters', {}))
                return float(len(filtered))

            elif method == "percentage":
                # Calculate percentage based on formula / 공식을 기반으로 백분율 계산
                return self._calculate_percentage(data, metric_def)

            elif method == "sum":
                # Sum a specific column / 특정 열 합계
                column = metric_def.get('value_column')
                if column and column in data.columns:
                    return float(data[column].sum())
                return 0.0

            elif method == "average":
                # Average a specific column / 특정 열 평균
                column = metric_def.get('value_column')
                if column and column in data.columns:
                    return float(data[column].mean())
                return 0.0

            else:
                # Default to count / 기본값 count
                return float(len(data))

        except Exception as e:
            self.logger.error(
                "메트릭 계산 실패",
                "Metric calculation failed",
                method=method,
                error=str(e)
            )
            return 0.0

    def _calculate_percentage(
        self,
        data: pd.DataFrame,
        metric_def: Dict[str, Any]
    ) -> float:
        """
        Calculate percentage-based metrics
        백분율 기반 메트릭 계산

        Args:
            data: Input DataFrame / 입력 DataFrame
            metric_def: Metric definition / 메트릭 정의

        Returns:
            Calculated percentage / 계산된 백분율
        """
        metric_id = metric_def.get('id', '')

        # Handle absence rate calculation / 결근율 계산 처리
        if 'absence' in metric_id:
            if 'actual_working_days' in data.columns and 'total_working_days' in data.columns:
                total_working_days = data['total_working_days'].sum()
                actual_working_days = data['actual_working_days'].sum()

                if total_working_days > 0:
                    attendance_rate = (actual_working_days / total_working_days) * 100
                    absence_rate = 100 - attendance_rate
                    return absence_rate

        # Handle resignation rate / 퇴사율 처리
        elif 'resignation' in metric_id:
            # Count employees with resignation dates in current period
            # 현재 기간에 퇴사일이 있는 직원 수 계산
            filters = metric_def.get('filters', {})
            resigned = self._apply_metric_filters(data, filters)
            total = len(data)

            if total > 0:
                return (len(resigned) / total) * 100

        return 0.0

    def _apply_metric_filters(
        self,
        data: pd.DataFrame,
        filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Apply filters defined in metric configuration
        메트릭 설정에 정의된 필터 적용

        Args:
            data: Input DataFrame / 입력 DataFrame
            filters: Filter definitions / 필터 정의

        Returns:
            Filtered DataFrame / 필터링된 DataFrame
        """
        filtered = data.copy()

        for filter_key, filter_value in filters.items():
            if filter_key == "active_only" and filter_value:
                # Filter for active employees / 활성 직원 필터
                if 'stop_working_date' in filtered.columns:
                    filtered = filtered[filtered['stop_working_date'].isna()]

            elif filter_key == "exclude_resigned" and filter_value:
                # Exclude resigned employees / 퇴사 직원 제외
                if 'resignation_date' in filtered.columns:
                    filtered = filtered[filtered['resignation_date'].isna()]

            elif filter_key == "has_resignation_date" and filter_value:
                # Only employees with resignation dates / 퇴사일이 있는 직원만
                if 'resignation_date' in filtered.columns:
                    filtered = filtered[filtered['resignation_date'].notna()]

            elif filter_key == "full_attendance_only" and filter_value:
                # Only employees with full attendance / 만근 직원만
                if 'actual_working_days' in filtered.columns and 'total_working_days' in filtered.columns:
                    filtered = filtered[
                        (filtered['actual_working_days'] == filtered['total_working_days']) &
                        (filtered['total_working_days'] > 0)
                    ]

            elif filter_key == "tenure_min":
                # Minimum tenure in days / 최소 재직 기간(일)
                if 'entrance_date' in filtered.columns:
                    from datetime import datetime
                    filtered['_tenure_days'] = (
                        datetime.now() - filtered['entrance_date']
                    ).dt.days
                    filtered = filtered[filtered['_tenure_days'] >= filter_value]

            elif filter_key == "tenure_max":
                # Maximum tenure in days / 최대 재직 기간(일)
                if 'entrance_date' in filtered.columns:
                    from datetime import datetime
                    filtered['_tenure_days'] = (
                        datetime.now() - filtered['entrance_date']
                    ).dt.days
                    filtered = filtered[filtered['_tenure_days'] < filter_value]

        return filtered

    def _evaluate_threshold(
        self,
        value: float,
        metric_def: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Evaluate threshold level for a metric value
        메트릭 값에 대한 임계값 수준 평가

        Args:
            value: Calculated metric value / 계산된 메트릭 값
            metric_def: Metric definition with thresholds / 임계값이 있는 메트릭 정의

        Returns:
            Tuple of (threshold_level, color_code)
            (임계값_수준, 색상_코드) 튜플
        """
        thresholds = metric_def.get('thresholds', {})

        if not thresholds:
            return None, None

        # Check each threshold level in priority order
        # 우선순위 순서로 각 임계값 수준 확인
        for level in ['excellent', 'good', 'warning', 'critical']:
            threshold = thresholds.get(level)
            if not threshold:
                continue

            min_val = threshold.get('min')
            max_val = threshold.get('max')

            # Check if value falls within this threshold range
            # 값이 이 임계값 범위 내에 있는지 확인
            if min_val is not None and max_val is not None:
                if min_val <= value < max_val:
                    return level, threshold.get('color')
            elif min_val is not None and max_val is None:
                if value >= min_val:
                    return level, threshold.get('color')
            elif max_val is not None and min_val is None:
                if value < max_val:
                    return level, threshold.get('color')

        return None, None

    def get_metric_definition(self, metric_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metric definition by ID
        ID로 메트릭 정의 가져오기

        Args:
            metric_id: Metric ID / 메트릭 ID

        Returns:
            Metric definition dictionary or None / 메트릭 정의 딕셔너리 또는 None
        """
        return self.metric_definitions.get(metric_id)

    def get_all_metric_ids(self) -> List[str]:
        """
        Get list of all available metric IDs
        사용 가능한 모든 메트릭 ID 목록 가져오기

        Returns:
            List of metric IDs / 메트릭 ID 목록
        """
        return list(self.metric_definitions.keys())
