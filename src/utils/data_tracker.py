#!/usr/bin/env python3
"""
data_tracker.py - Data Flow Tracking Utility
데이터 흐름 추적 유틸리티

Tracks data transformations through the pipeline for debugging and auditing
디버깅 및 감사를 위해 파이프라인을 통한 데이터 변환 추적
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path


class DataFlowTracker:
    """
    Track data flow through processing pipeline
    처리 파이프라인을 통한 데이터 흐름 추적
    """

    def __init__(self, enable_tracking: bool = True):
        """
        Initialize data flow tracker
        데이터 흐름 추적기 초기화
        """
        self.enable_tracking = enable_tracking
        self.tracking_log: List[Dict[str, Any]] = []
        self.stage_count = 0

    def log_stage(
        self,
        stage_name: str,
        df: pd.DataFrame,
        description: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Log a data processing stage
        데이터 처리 단계 로깅

        Args:
            stage_name: Name of the processing stage / 처리 단계 이름
            df: DataFrame at this stage / 이 단계의 DataFrame
            description: Description of what happened / 발생한 일 설명
            metadata: Additional metadata / 추가 메타데이터

        Returns:
            Stage tracking entry / 단계 추적 항목
        """
        if not self.enable_tracking:
            return {}

        self.stage_count += 1

        # Calculate data loss if previous stage exists
        # 이전 단계가 있으면 데이터 손실 계산
        data_loss = 0
        data_loss_pct = 0.0
        if len(self.tracking_log) > 0:
            prev_records = self.tracking_log[-1]['total_records']
            current_records = len(df)
            data_loss = prev_records - current_records
            data_loss_pct = (data_loss / prev_records * 100) if prev_records > 0 else 0

        # Create tracking entry
        # 추적 항목 생성
        tracking_entry = {
            'stage_number': self.stage_count,
            'stage_name': stage_name,
            'timestamp': datetime.now().isoformat(),
            'total_records': len(df),
            'data_loss': data_loss,
            'data_loss_percentage': round(data_loss_pct, 2),
            'description': description,
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            'null_counts': df.isnull().sum().to_dict(),
            'metadata': metadata or {}
        }

        # Add sample data if DataFrame not empty
        # DataFrame이 비어있지 않으면 샘플 데이터 추가
        if len(df) > 0:
            tracking_entry['sample_first_row'] = df.head(1).to_dict('records')[0]
            tracking_entry['dtypes'] = df.dtypes.astype(str).to_dict()

        self.tracking_log.append(tracking_entry)
        return tracking_entry

    def log_filter(
        self,
        filter_name: str,
        df_before: pd.DataFrame,
        df_after: pd.DataFrame,
        filter_condition: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Log a filtering operation
        필터링 작업 로깅

        Args:
            filter_name: Name of the filter / 필터 이름
            df_before: DataFrame before filtering / 필터링 전 DataFrame
            df_after: DataFrame after filtering / 필터링 후 DataFrame
            filter_condition: Description of filter condition / 필터 조건 설명
            metadata: Additional metadata / 추가 메타데이터

        Returns:
            Filter tracking entry / 필터 추적 항목
        """
        records_before = len(df_before)
        records_after = len(df_after)
        removed = records_before - records_after
        removed_pct = (removed / records_before * 100) if records_before > 0 else 0

        description = (
            f"Filter: {filter_condition} | "
            f"Removed: {removed} records ({removed_pct:.1f}%)"
        )

        filter_metadata = {
            'filter_condition': filter_condition,
            'records_before': records_before,
            'records_after': records_after,
            'records_removed': removed,
            'removal_percentage': round(removed_pct, 2)
        }

        if metadata:
            filter_metadata.update(metadata)

        return self.log_stage(filter_name, df_after, description, filter_metadata)

    def log_transformation(
        self,
        transform_name: str,
        df: pd.DataFrame,
        columns_modified: List[str],
        description: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Log a data transformation
        데이터 변환 로깅

        Args:
            transform_name: Name of transformation / 변환 이름
            df: DataFrame after transformation / 변환 후 DataFrame
            columns_modified: List of columns that were modified / 수정된 컬럼 목록
            description: Description of transformation / 변환 설명
            metadata: Additional metadata / 추가 메타데이터

        Returns:
            Transformation tracking entry / 변환 추적 항목
        """
        transform_metadata = {
            'columns_modified': columns_modified,
            'transformation_type': 'data_transformation'
        }

        if metadata:
            transform_metadata.update(metadata)

        return self.log_stage(transform_name, df, description, transform_metadata)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of data flow
        데이터 흐름 요약 가져오기

        Returns:
            Summary of all stages / 모든 단계의 요약
        """
        if not self.tracking_log:
            return {
                'total_stages': 0,
                'total_data_loss': 0,
                'total_data_loss_percentage': 0,
                'stages': []
            }

        initial_records = self.tracking_log[0]['total_records']
        final_records = self.tracking_log[-1]['total_records']
        total_loss = initial_records - final_records
        total_loss_pct = (total_loss / initial_records * 100) if initial_records > 0 else 0

        return {
            'total_stages': len(self.tracking_log),
            'initial_records': initial_records,
            'final_records': final_records,
            'total_data_loss': total_loss,
            'total_data_loss_percentage': round(total_loss_pct, 2),
            'stages': self.tracking_log
        }

    def print_summary(self):
        """
        Print formatted summary of data flow
        데이터 흐름의 포맷된 요약 출력
        """
        summary = self.get_summary()

        print("\n" + "=" * 80)
        print("📊 DATA FLOW TRACKING SUMMARY")
        print("데이터 흐름 추적 요약")
        print("=" * 80)

        print(f"\nTotal Stages: {summary['total_stages']}")
        print(f"Initial Records: {summary.get('initial_records', 0):,}")
        print(f"Final Records: {summary.get('final_records', 0):,}")
        print(f"Total Data Loss: {summary.get('total_data_loss', 0):,} "
              f"({summary.get('total_data_loss_percentage', 0):.2f}%)")

        print("\n" + "-" * 80)
        print("STAGE-BY-STAGE BREAKDOWN")
        print("단계별 분석")
        print("-" * 80)

        for stage in summary.get('stages', []):
            print(f"\n[Stage {stage['stage_number']}] {stage['stage_name']}")
            print(f"  Description: {stage['description']}")
            print(f"  Records: {stage['total_records']:,}")

            if stage['data_loss'] != 0:
                loss_indicator = "🔻" if stage['data_loss'] > 0 else "🔺"
                print(f"  {loss_indicator} Change: {stage['data_loss']:+,} "
                      f"({stage['data_loss_percentage']:+.2f}%)")

            print(f"  Memory: {stage['memory_usage_mb']:.2f} MB")

            # Show null counts if any
            # null 개수가 있으면 표시
            null_counts = stage.get('null_counts', {})
            if null_counts and any(v > 0 for v in null_counts.values()):
                print(f"  Nulls: {dict((k, v) for k, v in null_counts.items() if v > 0)}")

        print("\n" + "=" * 80)

    def export_to_json(self, output_path: Path):
        """
        Export tracking log to JSON
        추적 로그를 JSON으로 내보내기

        Args:
            output_path: Path to save JSON file / JSON 파일 저장 경로
        """
        summary = self.get_summary()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"✅ Tracking log exported to: {output_path}")

    def reset(self):
        """
        Reset tracking log
        추적 로그 초기화
        """
        self.tracking_log = []
        self.stage_count = 0


# Convenience function for quick tracking
# 빠른 추적을 위한 편의 함수
def track_data_flow(func):
    """
    Decorator to automatically track data flow through a function
    함수를 통한 데이터 흐름을 자동으로 추적하는 데코레이터
    """
    def wrapper(*args, **kwargs):
        tracker = DataFlowTracker()

        # Get DataFrame from args or kwargs
        # args 또는 kwargs에서 DataFrame 가져오기
        df = None
        for arg in args:
            if isinstance(arg, pd.DataFrame):
                df = arg
                break

        if df is None:
            for kwarg_val in kwargs.values():
                if isinstance(kwarg_val, pd.DataFrame):
                    df = kwarg_val
                    break

        # Track before execution
        # 실행 전 추적
        if df is not None:
            tracker.log_stage(
                f"{func.__name__} - Before",
                df,
                f"Input to {func.__name__}"
            )

        # Execute function
        # 함수 실행
        result = func(*args, **kwargs)

        # Track after execution
        # 실행 후 추적
        if isinstance(result, pd.DataFrame):
            tracker.log_stage(
                f"{func.__name__} - After",
                result,
                f"Output from {func.__name__}"
            )
            tracker.print_summary()

        return result

    return wrapper