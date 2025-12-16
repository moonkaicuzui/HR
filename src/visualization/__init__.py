"""
visualization package - Chart and HTML generation modules
차트 및 HTML 생성 모듈 패키지

This package provides visualization capabilities:
이 패키지는 시각화 기능을 제공합니다:
- chart_generator: Template-based Chart.js configuration generation
                  템플릿 기반 Chart.js 설정 생성
- html_builder: Complete HTML dashboard generation
               완전한 HTML 대시보드 생성
"""

from .chart_generator import (
    ChartGenerator,
    ChartData,
    ChartConfig
)

from .html_builder import HTMLBuilder

__all__ = [
    'ChartGenerator',
    'ChartData',
    'ChartConfig',
    'HTMLBuilder'
]
