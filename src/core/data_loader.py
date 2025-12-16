"""
data_loader.py - HR Data Loading Module
HR 데이터 로딩 모듈

Handles loading of HR data from various sources (CSV, Excel, Google Drive).
다양한 소스(CSV, Excel, Google Drive)에서 HR 데이터 로딩을 처리합니다.

Core Features / 핵심 기능:
- Load from local CSV/Excel files / 로컬 CSV/Excel 파일에서 로드
- Load from Google Drive / Google Drive에서 로드
- Automatic format detection / 자동 형식 감지
- Data normalization / 데이터 정규화
- Caching for performance / 성능을 위한 캐싱

NO FAKE DATA POLICY / 가짜 데이터 금지 정책:
- Never generate fake/dummy data / 가짜/더미 데이터를 절대 생성하지 않음
- Return empty DataFrames if data doesn't exist / 데이터가 없으면 빈 DataFrame 반환
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import json

from ..utils.logger import get_logger
from ..utils.date_parser import DateParser

try:
    from ..integration.google_drive_sync import GoogleDriveSync, GOOGLE_DRIVE_AVAILABLE
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False


class DataLoader:
    """
    Main data loader for HR data sources
    HR 데이터 소스용 메인 데이터 로더
    """

    def __init__(
        self,
        data_root: Optional[str] = None,
        cache_enabled: bool = True,
        date_parser: Optional[DateParser] = None
    ):
        """
        Initialize DataLoader
        DataLoader 초기화

        Args:
            data_root: Root directory for data files / 데이터 파일 루트 디렉토리
            cache_enabled: Enable DataFrame caching / DataFrame 캐싱 활성화
            date_parser: Custom date parser instance / 커스텀 날짜 파서 인스턴스
        """
        self.logger = get_logger()

        # Set default data root / 기본 데이터 루트 설정
        if data_root is None:
            hr_root = Path(__file__).parent.parent.parent
            data_root = hr_root / "data" / "input"

        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)

        self.cache_enabled = cache_enabled
        self.cache: Dict[str, pd.DataFrame] = {}

        self.date_parser = date_parser or DateParser()

        # Google Drive sync (optional) / Google Drive 동기화 (선택)
        self.drive_sync: Optional[GoogleDriveSync] = None
        if GOOGLE_DRIVE_AVAILABLE:
            try:
                self.drive_sync = GoogleDriveSync()
                if self.drive_sync.initialize():
                    self.logger.info(
                        "Google Drive 동기화 초기화 완료",
                        "Google Drive sync initialized"
                    )
            except Exception as e:
                self.logger.warning(
                    "Google Drive 동기화를 사용할 수 없습니다",
                    "Google Drive sync not available",
                    error=str(e)
                )

    def load_basic_manpower(
        self,
        month: int,
        year: int,
        file_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load basic manpower data for a specific month
        특정 월의 기본 인력 데이터 로드

        Args:
            month: Month number (1-12) / 월 번호 (1-12)
            year: Year (e.g., 2025) / 년도
            file_path: Custom file path (overrides default) / 커스텀 파일 경로 (기본값 덮어쓰기)

        Returns:
            DataFrame with manpower data / 인력 데이터가 있는 DataFrame

        Examples:
            >>> loader = DataLoader()
            >>> df = loader.load_basic_manpower(9, 2025)
            >>> print(df.columns)
        """
        cache_key = f"basic_manpower_{year}_{month:02d}"

        # Check cache / 캐시 확인
        if self.cache_enabled and cache_key in self.cache:
            self.logger.debug(
                f"캐시에서 인력 데이터 반환",
                f"Returning manpower data from cache",
                month=month,
                year=year
            )
            return self.cache[cache_key].copy()

        # Determine file path / 파일 경로 결정
        if file_path is None:
            month_names = {
                1: "january", 2: "february", 3: "march", 4: "april",
                5: "may", 6: "june", 7: "july", 8: "august",
                9: "september", 10: "october", 11: "november", 12: "december"
            }
            month_name = month_names.get(month, "").lower()
            file_path = self.data_root / f"basic manpower data {month_name}.csv"
        else:
            file_path = Path(file_path)

        # Load data / 데이터 로드
        try:
            df = self._load_csv_or_excel(file_path)

            # Normalize column names / 열 이름 정규화
            df = self._normalize_column_names(df)

            # Parse date columns / 날짜 열 파싱
            date_columns = ['entrance_date', 'stop_working_date', 'resignation_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].apply(self.date_parser.parse_date)

            # Cache result / 결과 캐시
            if self.cache_enabled:
                self.cache[cache_key] = df.copy()

            self.logger.info(
                f"인력 데이터 로드 완료",
                f"Basic manpower data loaded",
                month=month,
                year=year,
                rows=len(df),
                columns=len(df.columns)
            )

            return df

        except FileNotFoundError:
            self.logger.warning(
                f"인력 데이터 파일을 찾을 수 없습니다",
                f"Basic manpower data file not found",
                file=str(file_path)
            )
            # NO FAKE DATA - Return empty DataFrame / 가짜 데이터 없음 - 빈 DataFrame 반환
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(
                f"인력 데이터 로드 실패",
                f"Failed to load basic manpower data",
                file=str(file_path),
                error=str(e)
            )
            return pd.DataFrame()

    def load_attendance(
        self,
        month: int,
        year: int,
        file_path: Optional[str] = None,
        converted: bool = True
    ) -> pd.DataFrame:
        """
        Load attendance data for a specific month
        특정 월의 출근 데이터 로드

        Args:
            month: Month number (1-12) / 월 번호 (1-12)
            year: Year (e.g., 2025) / 년도
            file_path: Custom file path / 커스텀 파일 경로
            converted: Whether to load converted attendance data / 변환된 출근 데이터 로드 여부

        Returns:
            DataFrame with attendance data / 출근 데이터가 있는 DataFrame
        """
        cache_key = f"attendance_{year}_{month:02d}_{'converted' if converted else 'original'}"

        # Check cache / 캐시 확인
        if self.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key].copy()

        # Determine file path / 파일 경로 결정
        if file_path is None:
            month_names = {
                1: "january", 2: "february", 3: "march", 4: "april",
                5: "may", 6: "june", 7: "july", 8: "august",
                9: "september", 10: "october", 11: "november", 12: "december"
            }
            month_name = month_names.get(month, "").lower()
            subfolder = "converted" if converted else "original"
            file_suffix = "_converted" if converted else ""
            file_path = self.data_root / "attendance" / subfolder / f"attendance data {month_name}{file_suffix}.csv"
        else:
            file_path = Path(file_path)

        # Load data / 데이터 로드
        try:
            df = self._load_csv_or_excel(file_path)

            # Normalize column names / 열 이름 정규화
            df = self._normalize_column_names(df)

            # Cache result / 결과 캐시
            if self.cache_enabled:
                self.cache[cache_key] = df.copy()

            self.logger.info(
                f"출근 데이터 로드 완료",
                f"Attendance data loaded",
                month=month,
                year=year,
                converted=converted,
                rows=len(df)
            )

            return df

        except FileNotFoundError:
            self.logger.warning(
                f"출근 데이터 파일을 찾을 수 없습니다",
                f"Attendance data file not found",
                file=str(file_path)
            )
            # NO FAKE DATA / 가짜 데이터 없음
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(
                f"출근 데이터 로드 실패",
                f"Failed to load attendance data",
                file=str(file_path),
                error=str(e)
            )
            return pd.DataFrame()

    def load_aql_history(
        self,
        month: int,
        year: int,
        file_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load AQL (Acceptable Quality Level) history data
        AQL(허용 품질 수준) 이력 데이터 로드

        Args:
            month: Month number (1-12) / 월 번호 (1-12)
            year: Year (e.g., 2025) / 년도
            file_path: Custom file path / 커스텀 파일 경로

        Returns:
            DataFrame with AQL history / AQL 이력이 있는 DataFrame
        """
        cache_key = f"aql_history_{year}_{month:02d}"

        # Check cache / 캐시 확인
        if self.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key].copy()

        # Determine file path / 파일 경로 결정
        if file_path is None:
            month_names_korean = {
                1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6",
                7: "7", 8: "8", 9: "9", 10: "10", 11: "11", 12: "12"
            }
            month_kr = month_names_korean.get(month, str(month))
            file_path = self.data_root / "AQL history" / f"1.HSRG AQL REPORT-{month_kr}.{year}.csv"
        else:
            file_path = Path(file_path)

        # Load data / 데이터 로드
        try:
            df = self._load_csv_or_excel(file_path)
            df = self._normalize_column_names(df)

            # Cache result / 결과 캐시
            if self.cache_enabled:
                self.cache[cache_key] = df.copy()

            self.logger.info(
                f"AQL 이력 데이터 로드 완료",
                f"AQL history data loaded",
                month=month,
                year=year,
                rows=len(df)
            )

            return df

        except FileNotFoundError:
            self.logger.warning(
                f"AQL 이력 파일을 찾을 수 없습니다",
                f"AQL history file not found",
                file=str(file_path)
            )
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(
                f"AQL 이력 로드 실패",
                f"Failed to load AQL history",
                file=str(file_path),
                error=str(e)
            )
            return pd.DataFrame()

    def load_5prs_data(
        self,
        month: int,
        year: int,
        file_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load 5PRS (5-Point Rating System) data
        5PRS(5점 평가 시스템) 데이터 로드

        Args:
            month: Month number (1-12) / 월 번호 (1-12)
            year: Year (e.g., 2025) / 년도
            file_path: Custom file path / 커스텀 파일 경로

        Returns:
            DataFrame with 5PRS data / 5PRS 데이터가 있는 DataFrame
        """
        cache_key = f"5prs_{year}_{month:02d}"

        # Check cache / 캐시 확인
        if self.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key].copy()

        # Determine file path / 파일 경로 결정
        if file_path is None:
            month_names = {
                1: "january", 2: "february", 3: "march", 4: "april",
                5: "may", 6: "june", 7: "july", 8: "august",
                9: "september", 10: "october", 11: "november", 12: "december"
            }
            month_name = month_names.get(month, "").lower()
            file_path = self.data_root / f"5prs data {month_name}.csv"
        else:
            file_path = Path(file_path)

        # Load data / 데이터 로드
        try:
            df = self._load_csv_or_excel(file_path)
            df = self._normalize_column_names(df)

            # Cache result / 결과 캐시
            if self.cache_enabled:
                self.cache[cache_key] = df.copy()

            self.logger.info(
                f"5PRS 데이터 로드 완료",
                f"5PRS data loaded",
                month=month,
                year=year,
                rows=len(df)
            )

            return df

        except FileNotFoundError:
            self.logger.warning(
                f"5PRS 파일을 찾을 수 없습니다",
                f"5PRS file not found",
                file=str(file_path)
            )
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(
                f"5PRS 로드 실패",
                f"Failed to load 5PRS data",
                file=str(file_path),
                error=str(e)
            )
            return pd.DataFrame()

    def _load_csv_or_excel(self, file_path: Path) -> pd.DataFrame:
        """
        Load data from CSV or Excel file with automatic format detection
        자동 형식 감지로 CSV 또는 Excel 파일에서 데이터 로드

        Args:
            file_path: Path to file / 파일 경로

        Returns:
            DataFrame with loaded data / 로드된 데이터가 있는 DataFrame

        Raises:
            FileNotFoundError: If file doesn't exist / 파일이 없는 경우
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found / 파일을 찾을 수 없습니다: {file_path}")

        # Detect file format / 파일 형식 감지
        suffix = file_path.suffix.lower()

        try:
            if suffix == '.csv':
                # Try different encodings / 다양한 인코딩 시도
                for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin1']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        self.logger.debug(
                            f"CSV 로드 성공",
                            f"CSV loaded successfully",
                            file=str(file_path),
                            encoding=encoding
                        )
                        return df
                    except UnicodeDecodeError:
                        continue
                raise ValueError(f"Could not decode CSV file / CSV 파일 디코딩 불가: {file_path}")

            elif suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                return df

            else:
                # Default to CSV / 기본값 CSV
                df = pd.read_csv(file_path)
                return df

        except Exception as e:
            self.logger.error(
                f"파일 로드 실패",
                f"Failed to load file",
                file=str(file_path),
                error=str(e)
            )
            raise

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names to lowercase with underscores
        열 이름을 소문자와 밑줄로 정규화

        Args:
            df: Input DataFrame / 입력 DataFrame

        Returns:
            DataFrame with normalized column names / 정규화된 열 이름이 있는 DataFrame
        """
        # Create a copy to avoid modifying the original / 원본 수정 방지를 위해 복사본 생성
        df_copy = df.copy()

        # Normalize column names / 열 이름 정규화
        df_copy.columns = [
            col.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            for col in df_copy.columns
        ]

        return df_copy

    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """
        Clear data cache
        데이터 캐시 지우기

        Args:
            cache_key: Specific cache key to clear (clears all if None)
                      지울 특정 캐시 키 (None이면 전체 지우기)
        """
        if cache_key is None:
            self.cache.clear()
            self.logger.info("모든 캐시 지움", "All cache cleared")
        elif cache_key in self.cache:
            del self.cache[cache_key]
            self.logger.info(
                f"캐시 키 지움",
                f"Cache key cleared",
                key=cache_key
            )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        캐시 통계 반환

        Returns:
            Dictionary with cache statistics / 캐시 통계 딕셔너리
        """
        return {
            'enabled': self.cache_enabled,
            'cached_items': len(self.cache),
            'cache_keys': list(self.cache.keys()),
            'total_memory_mb': sum(df.memory_usage(deep=True).sum() for df in self.cache.values()) / (1024 * 1024)
        }
