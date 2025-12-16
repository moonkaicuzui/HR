"""
monthly_data_collector.py - Dynamic Monthly Data Collection
동적 월별 데이터 수집

CORE PRINCIPLE: NO HARDCODED MONTHS
핵심 원칙: 월 정보 하드코딩 금지

This module automatically detects which months have available data
by scanning the input_files directory structure.
이 모듈은 input_files 디렉토리 구조를 스캔하여
어떤 월에 사용 가능한 데이터가 있는지 자동으로 탐지합니다.
"""

import os
import glob
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import pandas as pd


class MonthlyDataCollector:
    """
    Dynamically detect and collect monthly data
    동적으로 월별 데이터 탐지 및 수집

    NO HARDCODING: Automatically scans for available months
    하드코딩 없음: 사용 가능한 월을 자동으로 스캔
    """

    MONTH_NAMES = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        # Korean month names (한국어 월 이름)
        '1월': 1, '2월': 2, '3월': 3, '4월': 4,
        '5월': 5, '6월': 6, '7월': 7, '8월': 8,
        '9월': 9, '10월': 10, '11월': 11, '12월': 12
    }

    def __init__(self, hr_root: Path):
        """
        Initialize MonthlyDataCollector

        Args:
            hr_root: Path to HR project root directory
        """
        self.hr_root = Path(hr_root)
        self.input_dir = self.hr_root / "input_files"
        self.available_months: List[str] = []
        self.month_data_map: Dict[str, Dict[str, Path]] = {}

    def detect_available_months(self, start_year: int = 2025, start_month: int = 7) -> List[str]:
        """
        Scan input_files directory to detect which months have data
        input_files 디렉토리를 스캔하여 어떤 월에 데이터가 있는지 탐지

        Args:
            start_year: Starting year to scan from (기본: 2025)
            start_month: Starting month to scan from (기본: 7월)

        Returns:
            List of year-month strings in format 'YYYY-MM'
            'YYYY-MM' 형식의 년-월 문자열 리스트

        Example:
            >>> collector = MonthlyDataCollector(Path('.'))
            >>> months = collector.detect_available_months()
            >>> print(months)
            ['2025-07', '2025-08', '2025-09', '2025-10', '2025-11']
        """
        detected_months = set()

        # Pattern 1: Basic manpower data files
        # 패턴 1: 기본 인력 데이터 파일
        manpower_pattern = str(self.input_dir / "basic manpower data *.csv")
        for file_path in glob.glob(manpower_pattern):
            month_str = self._extract_month_from_filename(file_path, "basic manpower data")
            if month_str:
                detected_months.add(month_str)

        # Pattern 2: Attendance data files in converted directory
        # 패턴 2: converted 디렉토리의 출근 데이터 파일
        attendance_dir = self.input_dir / "attendance" / "converted"
        if attendance_dir.exists():
            # Try pattern: attendance_YYYY_MM.csv
            attendance_pattern = str(attendance_dir / "attendance_*.csv")
            for file_path in glob.glob(attendance_pattern):
                month_str = self._extract_month_from_attendance(file_path)
                if month_str:
                    detected_months.add(month_str)

            # Try pattern: attendance data {month}_converted.csv
            attendance_pattern2 = str(attendance_dir / "attendance data *_converted.csv")
            for file_path in glob.glob(attendance_pattern2):
                month_str = self._extract_month_from_filename(file_path, "attendance data")
                if month_str:
                    detected_months.add(month_str)

        # Pattern 3: AQL history files
        # 패턴 3: AQL 이력 파일
        aql_dir = self.input_dir / "AQL history"
        if aql_dir.exists():
            # Try pattern: AQL history {month}.csv
            aql_pattern = str(aql_dir / "AQL history *.csv")
            for file_path in glob.glob(aql_pattern):
                month_str = self._extract_month_from_filename(file_path, "AQL history")
                if month_str:
                    detected_months.add(month_str)

            # Try pattern: 1.HSRG AQL REPORT-{MONTH}.2025.csv
            aql_pattern2 = str(aql_dir / "*.HSRG AQL REPORT-*.2025.csv")
            for file_path in glob.glob(aql_pattern2):
                month_str = self._extract_month_from_aql(file_path)
                if month_str:
                    detected_months.add(month_str)

        # Pattern 4: 5PRS data files
        # 패턴 4: 5PRS 데이터 파일
        prs_pattern = str(self.input_dir / "5prs data *.csv")
        for file_path in glob.glob(prs_pattern):
            month_str = self._extract_month_from_filename(file_path, "5prs data")
            if month_str:
                detected_months.add(month_str)

        # Sort chronologically
        # 시간순으로 정렬
        self.available_months = sorted(list(detected_months))

        return self.available_months

    def _extract_month_from_filename(self, file_path: str, prefix: str) -> Optional[str]:
        """
        Extract month from filename
        파일명에서 월 추출

        Args:
            file_path: Full path to file
            prefix: Prefix to remove (e.g., "basic manpower data")

        Returns:
            Month string in 'YYYY-MM' format or None
        """
        try:
            filename = os.path.basename(file_path)
            # Remove prefix and extension
            month_part = filename.replace(prefix, "").replace(".csv", "").strip()

            # Try to parse as month name
            month_num = self.MONTH_NAMES.get(month_part.lower())
            if month_num:
                # Assume 2025 for now (can be made dynamic later)
                return f"2025-{month_num:02d}"

            return None

        except Exception:
            return None

    def _extract_month_from_attendance(self, file_path: str) -> Optional[str]:
        """
        Extract month from attendance filename
        출근 파일명에서 월 추출

        Pattern: attendance_YYYY_MM.csv
        """
        try:
            filename = os.path.basename(file_path)
            # attendance_2025_09.csv → 2025_09
            parts = filename.replace("attendance_", "").replace(".csv", "").split("_")
            if len(parts) == 2:
                year, month = parts
                return f"{year}-{month}"
            return None
        except Exception:
            return None

    def _extract_month_from_aql(self, file_path: str) -> Optional[str]:
        """
        Extract month from AQL filename
        AQL 파일명에서 월 추출

        Pattern: 1.HSRG AQL REPORT-{MONTH}.2025.csv
        Example: 1.HSRG AQL REPORT-JULY.2025.csv → 2025-07
        """
        try:
            filename = os.path.basename(file_path)
            # Extract month part between '-' and '.2025'
            if "REPORT-" in filename and ".2025" in filename:
                month_part = filename.split("REPORT-")[1].split(".2025")[0]
                month_num = self.MONTH_NAMES.get(month_part.lower())
                if month_num:
                    return f"2025-{month_num:02d}"
            return None
        except Exception:
            return None

    def get_month_range(self, target_month: str) -> List[str]:
        """
        Get all available months up to and including target month
        목표 월까지의 모든 사용 가능한 월 가져오기

        Args:
            target_month: Target month in 'YYYY-MM' format

        Returns:
            List of months from earliest available to target month
            가장 이른 사용 가능한 월부터 목표 월까지의 리스트

        Example:
            >>> collector.get_month_range('2025-11')
            ['2025-07', '2025-08', '2025-09', '2025-10', '2025-11']
        """
        if not self.available_months:
            self.detect_available_months()

        return [m for m in self.available_months if m <= target_month]

    def get_month_labels(self, months: List[str], language: str = 'ko') -> List[str]:
        """
        Convert month strings to human-readable labels
        월 문자열을 읽기 쉬운 레이블로 변환

        Args:
            months: List of 'YYYY-MM' strings
            language: Language for labels ('ko', 'en', 'vi')

        Returns:
            List of formatted month labels

        Example:
            >>> collector.get_month_labels(['2025-07', '2025-08'], 'ko')
            ['7월 July', '8월 August']
        """
        labels = []

        month_names_ko = ['1월', '2월', '3월', '4월', '5월', '6월',
                          '7월', '8월', '9월', '10월', '11월', '12월']
        month_names_en = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_names_vi = ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4',
                          'Tháng 5', 'Tháng 6', 'Tháng 7', 'Tháng 8',
                          'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12']

        for month_str in months:
            try:
                year, month = month_str.split('-')
                month_num = int(month)

                if language == 'ko':
                    label = f"{month_names_ko[month_num-1]} {month_names_en[month_num-1]}"
                elif language == 'en':
                    label = f"{month_names_en[month_num-1]} {year}"
                elif language == 'vi':
                    label = f"{month_names_vi[month_num-1]} {year}"
                else:
                    label = month_str

                labels.append(label)

            except Exception:
                labels.append(month_str)

        return labels

    def get_file_paths_for_month(self, year_month: str) -> Dict[str, Optional[Path]]:
        """
        Get file paths for all data sources for a specific month
        특정 월의 모든 데이터 소스 파일 경로 가져오기

        Args:
            year_month: Month in 'YYYY-MM' format

        Returns:
            Dictionary mapping data source to file path
            데이터 소스를 파일 경로로 매핑하는 딕셔너리

        Example:
            >>> paths = collector.get_file_paths_for_month('2025-09')
            >>> print(paths)
            {
                'basic_manpower': Path('input_files/basic manpower data september.csv'),
                'attendance': Path('input_files/attendance/converted/attendance_2025_09.csv'),
                'aql': Path('input_files/AQL history/AQL history september.csv'),
                '5prs': Path('input_files/5prs data september.csv')
            }
        """
        year, month_num = year_month.split('-')
        month_num_int = int(month_num)

        # Reverse lookup: month number to name
        month_name = None
        for name, num in self.MONTH_NAMES.items():
            if num == month_num_int and name.isalpha() and name.islower():
                month_name = name
                break

        paths = {}

        if month_name:
            # Basic manpower
            manpower_path = self.input_dir / f"basic manpower data {month_name}.csv"
            paths['basic_manpower'] = manpower_path if manpower_path.exists() else None

            # Attendance - try multiple patterns
            attendance_path1 = self.input_dir / "attendance" / "converted" / f"attendance_{year}_{month_num}.csv"
            attendance_path2 = self.input_dir / "attendance" / "converted" / f"attendance data {month_name}_converted.csv"

            if attendance_path1.exists():
                paths['attendance'] = attendance_path1
            elif attendance_path2.exists():
                paths['attendance'] = attendance_path2
            else:
                paths['attendance'] = None

            # AQL - try multiple patterns
            aql_path1 = self.input_dir / "AQL history" / f"AQL history {month_name}.csv"
            aql_path2 = self.input_dir / "AQL history" / f"1.HSRG AQL REPORT-{month_name.upper()}.2025.csv"

            if aql_path1.exists():
                paths['aql'] = aql_path1
            elif aql_path2.exists():
                paths['aql'] = aql_path2
            else:
                paths['aql'] = None

            # 5PRS
            prs_path = self.input_dir / f"5prs data {month_name}.csv"
            paths['5prs'] = prs_path if prs_path.exists() else None

        return paths

    def load_month_data(self, year_month: str) -> Dict[str, pd.DataFrame]:
        """
        Load all data for a specific month
        특정 월의 모든 데이터 로드

        Args:
            year_month: Month in 'YYYY-MM' format

        Returns:
            Dictionary mapping data source to DataFrame

        NO FAKE DATA: Returns empty DataFrame if file doesn't exist
        가짜 데이터 없음: 파일이 없으면 빈 DataFrame 반환
        """
        paths = self.get_file_paths_for_month(year_month)
        data = {}

        for source, path in paths.items():
            if path and path.exists():
                try:
                    df = pd.read_csv(path, encoding='utf-8')
                    data[source] = df
                except Exception as e:
                    print(f"⚠️ Failed to load {source} for {year_month}: {e}")
                    data[source] = pd.DataFrame()
            else:
                # NO FAKE DATA - return empty DataFrame
                data[source] = pd.DataFrame()

        return data

    def get_data_availability_report(self) -> Dict[str, Any]:
        """
        Generate report of data availability across months
        월별 데이터 가용성 보고서 생성

        Returns:
            Report dictionary with availability status
        """
        if not self.available_months:
            self.detect_available_months()

        report = {
            'total_months': len(self.available_months),
            'month_range': {
                'start': self.available_months[0] if self.available_months else None,
                'end': self.available_months[-1] if self.available_months else None
            },
            'months': self.available_months,
            'data_sources': {}
        }

        # Check availability for each data source
        for month in self.available_months:
            paths = self.get_file_paths_for_month(month)
            for source, path in paths.items():
                if source not in report['data_sources']:
                    report['data_sources'][source] = []
                report['data_sources'][source].append({
                    'month': month,
                    'available': path is not None and path.exists()
                })

        return report


def main():
    """
    Test MonthlyDataCollector
    MonthlyDataCollector 테스트
    """
    # Get HR root directory (assuming this file is in src/data/)
    hr_root = Path(__file__).parent.parent.parent

    collector = MonthlyDataCollector(hr_root)

    print("🔍 가용 월 탐지 중...")
    print("🔍 Detecting available months...")

    months = collector.detect_available_months()

    print(f"\n✅ 탐지 완료: {len(months)}개월")
    print(f"✅ Detection complete: {len(months)} months\n")

    print("📅 사용 가능한 월:")
    print("📅 Available months:")
    for month in months:
        print(f"  - {month}")

    print(f"\n📊 데이터 가용성 보고서:")
    print(f"📊 Data availability report:")
    report = collector.get_data_availability_report()
    print(f"\n총 {report['total_months']}개월 ({report['month_range']['start']} ~ {report['month_range']['end']})")

    print("\n데이터 소스별 가용성:")
    for source, availability in report['data_sources'].items():
        available_count = sum(1 for item in availability if item['available'])
        print(f"  {source}: {available_count}/{len(availability)} months")

    # Test month labels
    print(f"\n🏷️  월 레이블 (한국어):")
    labels_ko = collector.get_month_labels(months, 'ko')
    print(f"  {labels_ko}")

    print(f"\n🏷️  Month labels (English):")
    labels_en = collector.get_month_labels(months, 'en')
    print(f"  {labels_en}")


if __name__ == '__main__':
    main()
