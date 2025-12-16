"""
trend_analyzer.py - Generic Trend Analysis Engine
범용 추세 분석 엔진

CORE REUSABILITY PRINCIPLE / 핵심 재사용성 원칙:
This module implements subject/object-agnostic trend analysis.
The same function works for ANY combination of subject and metric:
- analyze_trend(data, subject="Overall", metric="absence_rate", period="weekly")
- analyze_trend(data, subject="Team A", metric="attendance_rate", period="weekly")
- analyze_trend(data, subject="Assembly", metric="unauthorized_absence", period="monthly")

이 모듈은 주체/객체 독립적 추세 분석을 구현합니다.
동일한 함수가 주체와 메트릭의 모든 조합에 작동합니다.

Core Features / 핵심 기능:
- Subject-agnostic analysis / 주체 독립적 분석
- Metric-agnostic calculation / 메트릭 독립적 계산
- Time period flexibility (daily, weekly, monthly) / 시간 기간 유연성
- Automatic trend detection / 자동 추세 감지
- Comparison with previous periods / 이전 기간과 비교
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ..utils.logger import get_logger
from ..utils.date_parser import DateParser


@dataclass
class TrendPoint:
    """
    Single data point in a trend
    추세의 단일 데이터 포인트
    """
    timestamp: datetime
    value: float
    label: str  # Human-readable label (e.g., "Week 1", "September") / 사람이 읽을 수 있는 라벨
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendAnalysisResult:
    """
    Result of trend analysis
    추세 분석 결과
    """
    subject: str  # What is being analyzed (e.g., "Overall", "Team A") / 분석 대상
    metric: str  # What metric (e.g., "absence_rate") / 메트릭
    period: str  # Time period (e.g., "weekly") / 시간 기간
    data_points: List[TrendPoint]
    trend_direction: str  # "increasing", "decreasing", "stable" / 추세 방향
    average_value: float
    min_value: float
    max_value: float
    change_percentage: Optional[float] = None  # Change from first to last point / 첫 번째에서 마지막까지 변화
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrendAnalyzer:
    """
    Generic trend analyzer for any subject/metric combination
    모든 주체/메트릭 조합을 위한 범용 추세 분석기

    REUSABILITY DESIGN / 재사용성 설계:
    This class is designed to work with any subject (team, position, overall)
    and any metric (absence rate, attendance rate, resignation rate, etc.)
    without requiring code changes. Only data and parameters change.

    이 클래스는 코드 변경 없이 모든 주체(팀, 직급, 전체)와
    모든 메트릭(결근율, 출근율, 퇴사율 등)과 작동하도록 설계되었습니다.
    데이터와 매개변수만 변경됩니다.
    """

    def __init__(self, date_parser: Optional[DateParser] = None):
        """
        Initialize TrendAnalyzer
        TrendAnalyzer 초기화

        Args:
            date_parser: Custom date parser instance / 커스텀 날짜 파서 인스턴스
        """
        self.logger = get_logger()
        self.date_parser = date_parser or DateParser()

    def analyze_trend(
        self,
        data: pd.DataFrame,
        subject: str,
        metric: str,
        time_column: str,
        value_column: str,
        period: str = "weekly",
        subject_filter: Optional[Dict[str, Any]] = None,
        aggregation_method: str = "mean"
    ) -> TrendAnalysisResult:
        """
        Analyze trend for any subject/metric combination
        모든 주체/메트릭 조합에 대한 추세 분석

        REUSABILITY EXAMPLE / 재사용성 예시:
        >>> # Example 1: Overall absence rate weekly trend
        >>> # 예시 1: 전체 결근율 주차별 추세
        >>> analyzer = TrendAnalyzer()
        >>> result1 = analyzer.analyze_trend(
        ...     data=df,
        ...     subject="Overall",
        ...     metric="absence_rate",
        ...     time_column="date",
        ...     value_column="absence_rate",
        ...     period="weekly"
        ... )
        >>>
        >>> # Example 2: Team A attendance rate weekly trend
        >>> # 예시 2: 팀 A 출근율 주차별 추세
        >>> result2 = analyzer.analyze_trend(
        ...     data=df,
        ...     subject="Team A",
        ...     metric="attendance_rate",
        ...     time_column="date",
        ...     value_column="attendance_rate",
        ...     period="weekly",
        ...     subject_filter={"team": "Team A"}
        ... )
        >>>
        >>> # Example 3: Unauthorized absence trend
        >>> # 예시 3: 무단결근 추세
        >>> result3 = analyzer.analyze_trend(
        ...     data=df,
        ...     subject="Overall",
        ...     metric="unauthorized_absence_rate",
        ...     time_column="date",
        ...     value_column="unapproved_absence_days",
        ...     period="weekly"
        ... )

        Args:
            data: Input DataFrame / 입력 DataFrame
            subject: Subject being analyzed (e.g., "Overall", "Team A", "Position 1")
                    분석 대상 주체
            metric: Metric being analyzed (e.g., "absence_rate", "attendance_rate")
                   분석 메트릭
            time_column: Column name containing timestamps / 타임스탬프가 포함된 열 이름
            value_column: Column name containing metric values / 메트릭 값이 포함된 열 이름
            period: Time period for grouping ("daily", "weekly", "monthly")
                   그룹화 시간 기간
            subject_filter: Optional dictionary to filter data by subject
                           주체별로 데이터를 필터링하는 선택적 딕셔너리
                           Example: {"team": "Assembly", "position": "Inspector"}
            aggregation_method: How to aggregate values ("mean", "sum", "median")
                              값을 집계하는 방법

        Returns:
            TrendAnalysisResult with trend data and analysis
            추세 데이터 및 분석이 포함된 TrendAnalysisResult
        """
        self.logger.info(
            f"추세 분석 시작",
            f"Starting trend analysis",
            subject=subject,
            metric=metric,
            period=period
        )

        # 1. Filter data by subject if specified / 지정된 경우 주체별로 데이터 필터링
        filtered_data = data.copy()
        if subject_filter:
            for column, value in subject_filter.items():
                if column in filtered_data.columns:
                    filtered_data = filtered_data[filtered_data[column] == value]

        # 2. Parse time column / 시간 열 파싱
        if time_column in filtered_data.columns:
            filtered_data['_parsed_time'] = filtered_data[time_column].apply(
                self.date_parser.parse_date
            )
            # Remove rows with invalid dates / 유효하지 않은 날짜가 있는 행 제거
            filtered_data = filtered_data[filtered_data['_parsed_time'].notna()]
        else:
            self.logger.warning(
                f"시간 열을 찾을 수 없습니다",
                f"Time column not found",
                column=time_column
            )
            return TrendAnalysisResult(
                subject=subject,
                metric=metric,
                period=period,
                data_points=[],
                trend_direction="unknown",
                average_value=0.0,
                min_value=0.0,
                max_value=0.0
            )

        # 3. Group data by time period / 시간 기간별로 데이터 그룹화
        grouped_data = self._group_by_period(
            filtered_data,
            period,
            value_column,
            aggregation_method
        )

        # 4. Create trend points / 추세 포인트 생성
        trend_points = self._create_trend_points(grouped_data, period)

        # 5. Analyze trend direction / 추세 방향 분석
        trend_direction = self._detect_trend_direction(trend_points)

        # 6. Calculate statistics / 통계 계산
        values = [point.value for point in trend_points]
        average_value = np.mean(values) if values else 0.0
        min_value = min(values) if values else 0.0
        max_value = max(values) if values else 0.0

        # 7. Calculate change percentage / 변화율 계산
        change_percentage = None
        if len(values) >= 2:
            first_value = values[0]
            last_value = values[-1]
            if first_value != 0:
                change_percentage = ((last_value - first_value) / first_value) * 100

        result = TrendAnalysisResult(
            subject=subject,
            metric=metric,
            period=period,
            data_points=trend_points,
            trend_direction=trend_direction,
            average_value=average_value,
            min_value=min_value,
            max_value=max_value,
            change_percentage=change_percentage,
            metadata={
                'total_data_points': len(trend_points),
                'subject_filter': subject_filter,
                'aggregation_method': aggregation_method
            }
        )

        self.logger.info(
            f"추세 분석 완료",
            f"Trend analysis completed",
            subject=subject,
            metric=metric,
            trend=trend_direction,
            points=len(trend_points)
        )

        return result

    def compare_trends(
        self,
        current_trend: TrendAnalysisResult,
        previous_trend: TrendAnalysisResult
    ) -> Dict[str, Any]:
        """
        Compare current trend with previous period
        현재 추세를 이전 기간과 비교

        Args:
            current_trend: Current period trend analysis / 현재 기간 추세 분석
            previous_trend: Previous period trend analysis / 이전 기간 추세 분석

        Returns:
            Dictionary with comparison results / 비교 결과 딕셔너리
        """
        comparison = {
            'subject': current_trend.subject,
            'metric': current_trend.metric,
            'current_average': current_trend.average_value,
            'previous_average': previous_trend.average_value,
            'average_change': current_trend.average_value - previous_trend.average_value,
            'average_change_percentage': 0.0,
            'trend_change': None,
            'improved': False
        }

        # Calculate percentage change / 변화율 계산
        if previous_trend.average_value != 0:
            comparison['average_change_percentage'] = (
                (comparison['average_change'] / previous_trend.average_value) * 100
            )

        # Determine if trend changed / 추세가 변경되었는지 확인
        if current_trend.trend_direction != previous_trend.trend_direction:
            comparison['trend_change'] = f"{previous_trend.trend_direction} → {current_trend.trend_direction}"

        # Determine if improved (depends on metric type)
        # 개선 여부 확인 (메트릭 유형에 따라 다름)
        # For negative metrics (absence, resignation), lower is better
        # 부정적 메트릭(결근, 퇴사)의 경우 낮을수록 좋음
        negative_metrics = ['absence_rate', 'resignation_rate', 'unauthorized_absence']
        if any(metric in current_trend.metric.lower() for metric in negative_metrics):
            comparison['improved'] = current_trend.average_value < previous_trend.average_value
        else:
            # For positive metrics (attendance, full_attendance), higher is better
            # 긍정적 메트릭(출근, 만근)의 경우 높을수록 좋음
            comparison['improved'] = current_trend.average_value > previous_trend.average_value

        return comparison

    def _group_by_period(
        self,
        data: pd.DataFrame,
        period: str,
        value_column: str,
        aggregation_method: str
    ) -> pd.DataFrame:
        """
        Group data by time period
        시간 기간별로 데이터 그룹화

        Args:
            data: Input DataFrame with '_parsed_time' column
                 '_parsed_time' 열이 있는 입력 DataFrame
            period: Time period ("daily", "weekly", "monthly")
            value_column: Column to aggregate / 집계할 열
            aggregation_method: Aggregation method / 집계 방법

        Returns:
            Grouped DataFrame / 그룹화된 DataFrame
        """
        # Create period key / 기간 키 생성
        if period == "daily":
            data['_period'] = data['_parsed_time'].dt.date
        elif period == "weekly":
            # Group by week number / 주 번호로 그룹화
            data['_period'] = data['_parsed_time'].dt.to_period('W').apply(lambda x: x.start_time)
        elif period == "monthly":
            data['_period'] = data['_parsed_time'].dt.to_period('M').apply(lambda x: x.start_time)
        else:
            # Default to daily / 기본값 daily
            data['_period'] = data['_parsed_time'].dt.date

        # Aggregate by period / 기간별로 집계
        if aggregation_method == "mean":
            grouped = data.groupby('_period')[value_column].mean().reset_index()
        elif aggregation_method == "sum":
            grouped = data.groupby('_period')[value_column].sum().reset_index()
        elif aggregation_method == "median":
            grouped = data.groupby('_period')[value_column].median().reset_index()
        else:
            grouped = data.groupby('_period')[value_column].mean().reset_index()

        return grouped.sort_values('_period')

    def _create_trend_points(
        self,
        grouped_data: pd.DataFrame,
        period: str
    ) -> List[TrendPoint]:
        """
        Create TrendPoint objects from grouped data
        그룹화된 데이터에서 TrendPoint 객체 생성

        Args:
            grouped_data: Grouped DataFrame / 그룹화된 DataFrame
            period: Time period for labeling / 라벨링을 위한 시간 기간

        Returns:
            List of TrendPoint objects / TrendPoint 객체 목록
        """
        trend_points = []

        for idx, row in grouped_data.iterrows():
            timestamp = row['_period']
            value = float(row.iloc[1])  # Second column is the value / 두 번째 열이 값

            # Create human-readable label / 사람이 읽을 수 있는 라벨 생성
            if period == "daily":
                label = timestamp.strftime("%Y-%m-%d")
            elif period == "weekly":
                week_num = timestamp.isocalendar()[1]
                label = f"Week {week_num}"
            elif period == "monthly":
                label = timestamp.strftime("%B %Y")
            else:
                label = str(timestamp)

            trend_points.append(TrendPoint(
                timestamp=timestamp,
                value=value,
                label=label
            ))

        return trend_points

    def _detect_trend_direction(self, trend_points: List[TrendPoint]) -> str:
        """
        Detect overall trend direction
        전체 추세 방향 감지

        Args:
            trend_points: List of trend points / 추세 포인트 목록

        Returns:
            Trend direction: "increasing", "decreasing", "stable", "unknown"
            추세 방향
        """
        if len(trend_points) < 2:
            return "unknown"

        values = [point.value for point in trend_points]

        # Calculate linear regression slope / 선형 회귀 기울기 계산
        x = np.arange(len(values))
        y = np.array(values)

        # Handle case where all values are the same / 모든 값이 같은 경우 처리
        if np.std(y) == 0:
            return "stable"

        # Calculate correlation coefficient / 상관 계수 계산
        correlation = np.corrcoef(x, y)[0, 1]

        # Determine trend based on correlation / 상관 관계를 기반으로 추세 결정
        if abs(correlation) < 0.3:
            return "stable"
        elif correlation > 0:
            return "increasing"
        else:
            return "decreasing"
