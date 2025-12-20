"""
Pre-Validation Framework for HR Dashboard
HR 대시보드 사전 검증 프레임워크

Validates data files before processing to provide early error detection.
처리 전 데이터 파일을 검증하여 조기 오류 감지를 제공합니다.

Features:
- Check required input files exist
- Validate file encoding (UTF-8)
- Check for empty/corrupted CSV files
- Verify date columns are parseable
- Month consistency validation across data sources
"""

import os
import json
import chardet
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class ValidationResult:
    """
    Result of a single validation check
    단일 검증 결과
    """
    check_name: str
    passed: bool
    message_ko: str
    message_en: str
    severity: str = "error"  # error, warning, info
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """
    Complete validation report
    전체 검증 보고서
    """
    results: List[ValidationResult] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if any errors exist / 오류 존재 여부 확인"""
        return any(r.severity == "error" and not r.passed for r in self.results)

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings exist / 경고 존재 여부 확인"""
        return any(r.severity == "warning" and not r.passed for r in self.results)

    @property
    def error_count(self) -> int:
        """Count errors / 오류 수"""
        return sum(1 for r in self.results if r.severity == "error" and not r.passed)

    @property
    def warning_count(self) -> int:
        """Count warnings / 경고 수"""
        return sum(1 for r in self.results if r.severity == "warning" and not r.passed)

    def add(self, result: ValidationResult):
        """Add a validation result / 검증 결과 추가"""
        self.results.append(result)

    def print_report(self, language: str = "ko"):
        """
        Print validation report to console
        검증 보고서 콘솔 출력
        """
        print("\n" + "=" * 70)
        if language == "ko":
            print("📋 데이터 사전 검증 결과")
        else:
            print("📋 Pre-Validation Results")
        print("=" * 70)

        # Group by severity
        errors = [r for r in self.results if r.severity == "error" and not r.passed]
        warnings = [r for r in self.results if r.severity == "warning" and not r.passed]
        passed = [r for r in self.results if r.passed]

        # Print errors
        if errors:
            print(f"\n🚨 {'오류' if language == 'ko' else 'Errors'} ({len(errors)}):")
            for r in errors:
                msg = r.message_ko if language == "ko" else r.message_en
                print(f"   ❌ {r.check_name}: {msg}")

        # Print warnings
        if warnings:
            print(f"\n⚠️  {'경고' if language == 'ko' else 'Warnings'} ({len(warnings)}):")
            for r in warnings:
                msg = r.message_ko if language == "ko" else r.message_en
                print(f"   ⚠️  {r.check_name}: {msg}")

        # Print passed (summary only)
        if passed:
            print(f"\n✅ {'통과' if language == 'ko' else 'Passed'}: {len(passed)}/{len(self.results)}")

        print("=" * 70)

        if self.has_errors:
            if language == "ko":
                print("❌ 검증 실패 - 위 오류를 먼저 해결하세요.")
            else:
                print("❌ Validation failed - please fix the errors above.")
        elif self.has_warnings:
            if language == "ko":
                print("⚠️  검증 통과 (경고 있음) - 대시보드 생성을 계속합니다.")
            else:
                print("⚠️  Validation passed with warnings - continuing dashboard generation.")
        else:
            if language == "ko":
                print("✅ 모든 검증 통과 - 대시보드 생성을 시작합니다.")
            else:
                print("✅ All validations passed - starting dashboard generation.")
        print()


class PreValidator:
    """
    Pre-validation engine for HR Dashboard data
    HR 대시보드 데이터 사전 검증 엔진
    """

    MONTH_NAMES = {
        1: 'january', 2: 'february', 3: 'march', 4: 'april',
        5: 'may', 6: 'june', 7: 'july', 8: 'august',
        9: 'september', 10: 'october', 11: 'november', 12: 'december'
    }

    def __init__(self, project_root: Path, year: int, month: int):
        """
        Initialize pre-validator
        사전 검증기 초기화

        Args:
            project_root: Project root path / 프로젝트 루트 경로
            year: Target year / 대상 연도
            month: Target month / 대상 월
        """
        self.project_root = project_root
        self.year = year
        self.month = month
        self.month_name = self.MONTH_NAMES.get(month, '')
        self.input_dir = project_root / "input_files"
        self.report = ValidationReport()

    def validate_all(self) -> ValidationReport:
        """
        Run all validations
        모든 검증 실행

        Returns:
            ValidationReport: Complete validation report / 전체 검증 보고서
        """
        # 1. Check required files
        self._validate_required_files()

        # 2. Validate file encodings
        self._validate_file_encodings()

        # 3. Check CSV structure
        self._validate_csv_structure()

        # 4. Validate date columns
        self._validate_date_columns()

        # 5. Check month consistency
        self._validate_month_consistency()

        return self.report

    def _get_expected_files(self) -> Dict[str, Tuple[Path, str]]:
        """
        Get list of expected files with their importance
        예상 파일 목록과 중요도 반환

        Returns:
            Dict mapping file key to (path, severity)
        """
        files = {
            "basic_manpower": (
                self.input_dir / f"basic manpower data {self.month_name}.csv",
                "error"  # Required / 필수
            ),
            "attendance": (
                self.input_dir / "attendance" / "converted" / f"attendance data {self.month_name}_converted.csv",
                "error"  # Required / 필수
            ),
        }

        # Optional files (warning if missing)
        optional_files = {
            "5prs": (
                self.input_dir / f"5prs data {self.month_name}.csv",
                "warning"
            ),
        }

        files.update(optional_files)
        return files

    def _validate_required_files(self):
        """
        Check if required files exist
        필수 파일 존재 여부 확인
        """
        expected_files = self._get_expected_files()

        for file_key, (file_path, severity) in expected_files.items():
            exists = file_path.exists()

            if exists:
                self.report.add(ValidationResult(
                    check_name=f"file_exists_{file_key}",
                    passed=True,
                    message_ko=f"파일 존재: {file_path.name}",
                    message_en=f"File exists: {file_path.name}",
                    severity="info"
                ))
            else:
                self.report.add(ValidationResult(
                    check_name=f"file_exists_{file_key}",
                    passed=False,
                    message_ko=f"파일 없음: {file_path.name}",
                    message_en=f"File missing: {file_path.name}",
                    severity=severity,
                    details={"path": str(file_path)}
                ))

    def _validate_file_encodings(self):
        """
        Validate file encodings are UTF-8 compatible
        파일 인코딩이 UTF-8 호환인지 확인
        """
        expected_files = self._get_expected_files()

        for file_key, (file_path, _) in expected_files.items():
            if not file_path.exists():
                continue

            try:
                # Read first 10KB to detect encoding
                with open(file_path, 'rb') as f:
                    raw_data = f.read(10240)

                detected = chardet.detect(raw_data)
                encoding = detected.get('encoding', 'unknown')
                confidence = detected.get('confidence', 0)

                # Accept UTF-8, ASCII, or high-confidence encodings
                is_valid = encoding and (
                    encoding.lower() in ['utf-8', 'ascii', 'utf-8-sig'] or
                    confidence >= 0.8
                )

                if is_valid:
                    self.report.add(ValidationResult(
                        check_name=f"encoding_{file_key}",
                        passed=True,
                        message_ko=f"인코딩 확인: {encoding} ({confidence:.0%})",
                        message_en=f"Encoding valid: {encoding} ({confidence:.0%})",
                        severity="info"
                    ))
                else:
                    self.report.add(ValidationResult(
                        check_name=f"encoding_{file_key}",
                        passed=False,
                        message_ko=f"인코딩 문제: {encoding} (신뢰도 {confidence:.0%})",
                        message_en=f"Encoding issue: {encoding} (confidence {confidence:.0%})",
                        severity="warning",
                        details={"encoding": encoding, "confidence": confidence}
                    ))

            except Exception as e:
                self.report.add(ValidationResult(
                    check_name=f"encoding_{file_key}",
                    passed=False,
                    message_ko=f"인코딩 확인 실패: {str(e)}",
                    message_en=f"Encoding check failed: {str(e)}",
                    severity="warning"
                ))

    def _validate_csv_structure(self):
        """
        Validate CSV files are readable and not empty
        CSV 파일이 읽을 수 있고 비어있지 않은지 확인
        """
        expected_files = self._get_expected_files()

        for file_key, (file_path, severity) in expected_files.items():
            if not file_path.exists():
                continue

            try:
                # Try to read CSV
                df = pd.read_csv(file_path, nrows=5, encoding='utf-8')

                if df.empty:
                    self.report.add(ValidationResult(
                        check_name=f"csv_structure_{file_key}",
                        passed=False,
                        message_ko=f"CSV 파일이 비어있음: {file_path.name}",
                        message_en=f"CSV file is empty: {file_path.name}",
                        severity=severity
                    ))
                elif len(df.columns) < 2:
                    self.report.add(ValidationResult(
                        check_name=f"csv_structure_{file_key}",
                        passed=False,
                        message_ko=f"CSV 컬럼 부족: {len(df.columns)}개",
                        message_en=f"CSV has too few columns: {len(df.columns)}",
                        severity="warning"
                    ))
                else:
                    self.report.add(ValidationResult(
                        check_name=f"csv_structure_{file_key}",
                        passed=True,
                        message_ko=f"CSV 구조 정상: {len(df.columns)}개 컬럼",
                        message_en=f"CSV structure valid: {len(df.columns)} columns",
                        severity="info"
                    ))

            except pd.errors.EmptyDataError:
                self.report.add(ValidationResult(
                    check_name=f"csv_structure_{file_key}",
                    passed=False,
                    message_ko=f"CSV 파일이 비어있거나 손상됨",
                    message_en=f"CSV file is empty or corrupted",
                    severity=severity
                ))
            except Exception as e:
                self.report.add(ValidationResult(
                    check_name=f"csv_structure_{file_key}",
                    passed=False,
                    message_ko=f"CSV 읽기 실패: {str(e)[:50]}",
                    message_en=f"CSV read failed: {str(e)[:50]}",
                    severity=severity
                ))

    def _validate_date_columns(self):
        """
        Validate date columns are parseable
        날짜 컬럼이 파싱 가능한지 확인
        """
        # Check basic manpower file
        basic_file = self.input_dir / f"basic manpower data {self.month_name}.csv"

        if not basic_file.exists():
            return

        try:
            df = pd.read_csv(basic_file, nrows=100, encoding='utf-8')

            date_columns = ['Entrance Date', 'Stop working Date']
            for col in date_columns:
                if col not in df.columns:
                    continue

                # Try to parse dates
                non_null = df[col].dropna()
                if len(non_null) == 0:
                    continue

                try:
                    parsed = pd.to_datetime(non_null, errors='coerce')
                    parse_rate = parsed.notna().sum() / len(non_null)

                    if parse_rate >= 0.9:
                        self.report.add(ValidationResult(
                            check_name=f"date_column_{col}",
                            passed=True,
                            message_ko=f"날짜 컬럼 정상: {col} ({parse_rate:.0%} 파싱됨)",
                            message_en=f"Date column valid: {col} ({parse_rate:.0%} parsed)",
                            severity="info"
                        ))
                    else:
                        self.report.add(ValidationResult(
                            check_name=f"date_column_{col}",
                            passed=False,
                            message_ko=f"날짜 파싱 문제: {col} ({parse_rate:.0%}만 파싱됨)",
                            message_en=f"Date parsing issue: {col} (only {parse_rate:.0%} parsed)",
                            severity="warning",
                            details={"parse_rate": parse_rate}
                        ))
                except Exception as e:
                    self.report.add(ValidationResult(
                        check_name=f"date_column_{col}",
                        passed=False,
                        message_ko=f"날짜 파싱 실패: {col}",
                        message_en=f"Date parsing failed: {col}",
                        severity="warning"
                    ))

        except Exception as e:
            self.report.add(ValidationResult(
                check_name="date_columns",
                passed=False,
                message_ko=f"날짜 검증 실패: {str(e)[:50]}",
                message_en=f"Date validation failed: {str(e)[:50]}",
                severity="warning"
            ))

    def _validate_month_consistency(self):
        """
        Check month consistency across data sources
        데이터 소스 간 월 일관성 확인
        """
        # Check sync manifest for month info
        manifest_path = self.input_dir / "sync_manifest.json"

        if not manifest_path.exists():
            self.report.add(ValidationResult(
                check_name="month_consistency",
                passed=True,  # Not an error if manifest doesn't exist
                message_ko="동기화 매니페스트 없음 (수동 데이터 사용)",
                message_en="No sync manifest (using manual data)",
                severity="info"
            ))
            return

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            month_data = manifest.get("months", {}).get(self.month_name, {})

            if month_data:
                manifest_year = month_data.get("year")

                if manifest_year and int(manifest_year) == self.year:
                    self.report.add(ValidationResult(
                        check_name="month_consistency",
                        passed=True,
                        message_ko=f"월 일관성 확인: {self.year}년 {self.month}월",
                        message_en=f"Month consistency valid: {self.year}-{self.month:02d}",
                        severity="info"
                    ))
                elif manifest_year:
                    self.report.add(ValidationResult(
                        check_name="month_consistency",
                        passed=False,
                        message_ko=f"연도 불일치: 요청 {self.year}년 vs 데이터 {manifest_year}년",
                        message_en=f"Year mismatch: requested {self.year} vs data {manifest_year}",
                        severity="warning",
                        details={"requested_year": self.year, "data_year": manifest_year}
                    ))
            else:
                self.report.add(ValidationResult(
                    check_name="month_consistency",
                    passed=True,
                    message_ko=f"매니페스트에 {self.month_name} 데이터 없음",
                    message_en=f"No {self.month_name} data in manifest",
                    severity="info"
                ))

        except Exception as e:
            self.report.add(ValidationResult(
                check_name="month_consistency",
                passed=False,
                message_ko=f"매니페스트 읽기 실패: {str(e)[:50]}",
                message_en=f"Manifest read failed: {str(e)[:50]}",
                severity="warning"
            ))


def run_pre_validation(project_root: Path, year: int, month: int, language: str = "ko") -> Tuple[bool, ValidationReport]:
    """
    Run pre-validation and return result
    사전 검증 실행 및 결과 반환

    Args:
        project_root: Project root path / 프로젝트 루트 경로
        year: Target year / 대상 연도
        month: Target month / 대상 월
        language: Output language (ko/en) / 출력 언어

    Returns:
        Tuple of (success, report)
    """
    validator = PreValidator(project_root, year, month)
    report = validator.validate_all()
    report.print_report(language)

    return not report.has_errors, report
