"""
analytics package - Reusable analysis engines
분석 패키지 - 재활용 가능한 분석 엔진

This package provides subject/metric-agnostic analysis engines:
이 패키지는 주제/메트릭 무관 분석 엔진을 제공합니다:
- trend_analyzer: Generic trend analysis for any subject/metric
                 모든 주제/메트릭에 대한 일반 트렌드 분석
- metric_calculator: Configuration-driven metric calculation
                    설정 기반 메트릭 계산

REUSABILITY PRINCIPLE:
The same analysis functions work for ANY combination of subject and metric.
Example: analyze_trend() works for "overall absence rate", "team A attendance",
        or any other subject/metric combination.
"""

from .trend_analyzer import (
    TrendAnalyzer,
    TrendPoint,
    TrendAnalysisResult
)

from .metric_calculator import (
    MetricCalculator,
    MetricValue,
    MetricCalculationResult
)

__all__ = [
    # Trend analysis
    'TrendAnalyzer',
    'TrendPoint',
    'TrendAnalysisResult',

    # Metric calculation
    'MetricCalculator',
    'MetricValue',
    'MetricCalculationResult'
]
