"""
performance_optimizer.py - Performance Optimization Utilities
성능 최적화 유틸리티

Provides caching, parallel processing, and performance monitoring
캐싱, 병렬 처리, 성능 모니터링 제공
"""

import time
import hashlib
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..utils.logger import get_logger


class PerformanceOptimizer:
    """
    Performance optimization utilities for HR Dashboard
    HR 대시보드를 위한 성능 최적화 유틸리티
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize PerformanceOptimizer
        PerformanceOptimizer 초기화

        Args:
            cache_dir: Directory for cache storage / 캐시 저장 디렉토리
        """
        self.logger = get_logger()

        # Set cache directory
        if cache_dir is None:
            hr_root = Path(__file__).parent.parent.parent
            cache_dir = hr_root / ".cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Performance metrics storage
        self.performance_metrics = {}

    def cache_result(self, ttl_seconds: int = 3600):
        """
        Decorator for caching function results
        함수 결과를 캐싱하는 데코레이터

        Args:
            ttl_seconds: Time to live in seconds / 캐시 유효 시간(초)

        Example:
            @optimizer.cache_result(ttl_seconds=3600)
            def expensive_calculation(data):
                return complex_computation(data)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                cache_file = self.cache_dir / f"{cache_key}.pickle"

                # Check if cached result exists and is fresh
                if cache_file.exists():
                    mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if datetime.now() - mod_time < timedelta(seconds=ttl_seconds):
                        try:
                            with open(cache_file, 'rb') as f:
                                result = pickle.load(f)
                                self.logger.debug(
                                    f"캐시에서 결과 반환",
                                    f"Returning cached result",
                                    function=func.__name__
                                )
                                return result
                        except Exception as e:
                            self.logger.warning(
                                f"캐시 읽기 실패",
                                f"Failed to read cache",
                                error=str(e)
                            )

                # Execute function and cache result
                result = func(*args, **kwargs)

                try:
                    with open(cache_file, 'wb') as f:
                        pickle.dump(result, f)
                    self.logger.debug(
                        f"결과 캐시 저장",
                        f"Cached result saved",
                        function=func.__name__
                    )
                except Exception as e:
                    self.logger.warning(
                        f"캐시 저장 실패",
                        f"Failed to save cache",
                        error=str(e)
                    )

                return result

            return wrapper
        return decorator

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate unique cache key from function and arguments
        함수와 인자로부터 고유한 캐시 키 생성
        """
        # Create a string representation of arguments
        key_parts = [func_name]

        for arg in args:
            if isinstance(arg, pd.DataFrame):
                # For DataFrames, use shape and column names as key
                key_parts.append(f"df_{arg.shape}_{list(arg.columns)}")
            elif isinstance(arg, (list, dict)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(arg))

        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        key_string = "|".join(key_parts)

        # Generate MD5 hash for the key
        return hashlib.md5(key_string.encode()).hexdigest()

    def measure_performance(self, operation_name: str):
        """
        Decorator to measure function performance
        함수 성능을 측정하는 데코레이터

        Args:
            operation_name: Name of the operation / 작업 이름

        Example:
            @optimizer.measure_performance("data_loading")
            def load_data():
                return pd.read_csv("large_file.csv")
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = self._get_memory_usage()

                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    raise e
                finally:
                    end_time = time.time()
                    end_memory = self._get_memory_usage()

                    duration = end_time - start_time
                    memory_delta = end_memory - start_memory

                    # Store performance metrics
                    if operation_name not in self.performance_metrics:
                        self.performance_metrics[operation_name] = []

                    self.performance_metrics[operation_name].append({
                        'timestamp': datetime.now().isoformat(),
                        'duration_seconds': duration,
                        'memory_delta_mb': memory_delta,
                        'success': success
                    })

                    self.logger.info(
                        f"성능 측정 완료",
                        f"Performance measured",
                        operation=operation_name,
                        duration=f"{duration:.2f}s",
                        memory_delta=f"{memory_delta:.2f}MB"
                    )

                return result

            return wrapper
        return decorator

    def _get_memory_usage(self) -> float:
        """
        Get current memory usage in MB
        현재 메모리 사용량을 MB 단위로 가져오기
        """
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0  # Return 0 if psutil not available

    def parallel_process(
        self,
        func: Callable,
        items: List[Any],
        max_workers: Optional[int] = None,
        use_process_pool: bool = False
    ) -> List[Any]:
        """
        Process items in parallel
        항목을 병렬로 처리

        Args:
            func: Function to apply to each item / 각 항목에 적용할 함수
            items: List of items to process / 처리할 항목 리스트
            max_workers: Maximum number of workers / 최대 워커 수
            use_process_pool: Use ProcessPoolExecutor instead of ThreadPoolExecutor
                            ProcessPoolExecutor 사용 여부

        Returns:
            List of results in original order / 원래 순서의 결과 리스트

        Example:
            def process_month(month):
                return calculate_metrics(month)

            results = optimizer.parallel_process(process_month, months, max_workers=4)
        """
        if not items:
            return []

        # Determine number of workers
        if max_workers is None:
            import multiprocessing
            max_workers = min(len(items), multiprocessing.cpu_count())

        self.logger.info(
            f"병렬 처리 시작",
            f"Starting parallel processing",
            items_count=len(items),
            workers=max_workers
        )

        # Choose executor type
        Executor = ProcessPoolExecutor if use_process_pool else ThreadPoolExecutor

        results = [None] * len(items)

        with Executor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(func, item): i
                for i, item in enumerate(items)
            }

            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    self.logger.error(
                        f"병렬 처리 오류",
                        f"Parallel processing error",
                        index=index,
                        error=str(e)
                    )
                    results[index] = None

        self.logger.info(
            f"병렬 처리 완료",
            f"Parallel processing completed",
            successful=sum(1 for r in results if r is not None)
        )

        return results

    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame memory usage
        DataFrame 메모리 사용량 최적화

        Args:
            df: DataFrame to optimize / 최적화할 DataFrame

        Returns:
            Optimized DataFrame / 최적화된 DataFrame
        """
        start_memory = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB

        # Optimize numeric columns
        for col in df.select_dtypes(include=['int']).columns:
            col_min = df[col].min()
            col_max = df[col].max()

            # Downcast integers
            if col_min >= 0:
                if col_max < 255:
                    df[col] = df[col].astype(np.uint8)
                elif col_max < 65535:
                    df[col] = df[col].astype(np.uint16)
                elif col_max < 4294967295:
                    df[col] = df[col].astype(np.uint32)
            else:
                if col_min > np.iinfo(np.int8).min and col_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif col_min > np.iinfo(np.int16).min and col_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif col_min > np.iinfo(np.int32).min and col_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)

        # Optimize float columns
        for col in df.select_dtypes(include=['float']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')

        # Convert object columns to category if appropriate
        for col in df.select_dtypes(include=['object']).columns:
            num_unique = df[col].nunique()
            num_total = len(df[col])
            if num_unique / num_total < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')

        end_memory = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        reduction = (start_memory - end_memory) / start_memory * 100

        self.logger.info(
            f"DataFrame 최적화 완료",
            f"DataFrame optimization completed",
            start_mb=f"{start_memory:.2f}",
            end_mb=f"{end_memory:.2f}",
            reduction=f"{reduction:.1f}%"
        )

        return df

    def batch_process(
        self,
        func: Callable,
        items: List[Any],
        batch_size: int = 100
    ) -> List[Any]:
        """
        Process items in batches for memory efficiency
        메모리 효율성을 위해 배치로 항목 처리

        Args:
            func: Function to apply to each batch / 각 배치에 적용할 함수
            items: List of items to process / 처리할 항목 리스트
            batch_size: Size of each batch / 각 배치의 크기

        Returns:
            List of all results / 모든 결과 리스트
        """
        results = []
        total_batches = (len(items) + batch_size - 1) // batch_size

        self.logger.info(
            f"배치 처리 시작",
            f"Starting batch processing",
            total_items=len(items),
            batch_size=batch_size,
            total_batches=total_batches
        )

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_num = i // batch_size + 1

            self.logger.debug(
                f"배치 처리 중",
                f"Processing batch",
                batch_num=batch_num,
                batch_size=len(batch)
            )

            batch_results = func(batch)
            results.extend(batch_results)

        return results

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get performance metrics report
        성능 메트릭 보고서 가져오기

        Returns:
            Dictionary with performance statistics / 성능 통계 딕셔너리
        """
        report = {}

        for operation, metrics in self.performance_metrics.items():
            if metrics:
                durations = [m['duration_seconds'] for m in metrics]
                memory_deltas = [m['memory_delta_mb'] for m in metrics]
                success_rate = sum(1 for m in metrics if m['success']) / len(metrics) * 100

                report[operation] = {
                    'count': len(metrics),
                    'avg_duration_seconds': np.mean(durations),
                    'min_duration_seconds': np.min(durations),
                    'max_duration_seconds': np.max(durations),
                    'avg_memory_delta_mb': np.mean(memory_deltas),
                    'success_rate': success_rate
                }

        return report

    def clear_cache(self, older_than_hours: Optional[int] = None):
        """
        Clear cache files
        캐시 파일 삭제

        Args:
            older_than_hours: Clear only files older than specified hours
                            지정된 시간보다 오래된 파일만 삭제
        """
        count = 0
        now = datetime.now()

        for cache_file in self.cache_dir.glob("*.pickle"):
            if older_than_hours:
                mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if now - mod_time < timedelta(hours=older_than_hours):
                    continue

            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                self.logger.warning(
                    f"캐시 파일 삭제 실패",
                    f"Failed to delete cache file",
                    file=str(cache_file),
                    error=str(e)
                )

        self.logger.info(
            f"캐시 삭제 완료",
            f"Cache cleared",
            files_deleted=count
        )