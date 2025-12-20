"""
HR Dashboard Generation - Complete Dashboard Version
HR 대시보드 생성 - 완전판 버전

This module generates a complete HR dashboard with:
- Dynamic monthly data loading
- Multi-month trend analysis
- 3-tab interface (Overview, Trends, Employee Details)
- Modern UI with Bootstrap 5 and Chart.js
- Multi-language support (KO/EN/VI)

이 모듈은 다음을 포함한 완전한 HR 대시보드를 생성합니다:
- 동적 월별 데이터 로딩
- 다중 월 트렌드 분석
- 3탭 인터페이스 (개요, 트렌드, 직원 상세)
- Bootstrap 5 및 Chart.js를 사용한 현대적인 UI
- 다국어 지원 (한국어/영어/베트남어)

NO FAKE DATA policy: System returns empty results if data doesn't exist.
가짜 데이터 없음 정책: 데이터가 없으면 빈 결과를 반환합니다.
"""

import sys
import json
import shutil
from pathlib import Path
import argparse
from datetime import datetime
import pandas as pd

# Add parent directory to path for imports
# 부모 디렉토리를 import 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder
from src.utils.pre_validator import run_pre_validation
from src.utils.logger import init_logger, get_logger


def check_dependencies() -> bool:
    """
    Check Python version and required packages
    Python 버전 및 필수 패키지 확인

    Returns:
        bool: True if all dependencies are met / 모든 의존성이 충족되면 True
    """
    import sys

    # Check Python version
    # Python 버전 확인
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required / Python 3.8 이상 필요")
        print(f"   Current: {sys.version}")
        return False

    # Check required packages
    # 필수 패키지 확인
    required_packages = ['pandas', 'numpy', 'chardet']
    missing = []

    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"❌ Missing packages / 누락된 패키지: {', '.join(missing)}")
        print(f"   Run: pip install {' '.join(missing)}")
        return False

    return True


def backup_existing_dashboard(output_file: Path) -> None:
    """
    Backup existing dashboard before overwriting
    덮어쓰기 전 기존 대시보드 백업

    Args:
        output_file: Path to the output file / 출력 파일 경로
    """
    if output_file.exists():
        backup_dir = output_file.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{output_file.stem}_backup_{timestamp}{output_file.suffix}"
        backup_file = backup_dir / backup_name

        shutil.copy(output_file, backup_file)
        print(f"📦 Backed up existing dashboard to: {backup_file}")
        print(f"📦 기존 대시보드 백업: {backup_file}")


def detect_data_year(month: int, project_root: Path) -> int:
    """
    Detect actual year from sync manifest (based on Google Drive folder name)
    동기화 매니페스트에서 연도 감지 (Google Drive 폴더명 기준)

    Args:
        month: Target month / 대상 월
        project_root: Project root path / 프로젝트 루트 경로

    Returns:
        int: Detected year or current year as fallback / 감지된 연도 또는 현재 연도
    """
    month_names = {
        1: 'january', 2: 'february', 3: 'march', 4: 'april',
        5: 'may', 6: 'june', 7: 'july', 8: 'august',
        9: 'september', 10: 'october', 11: 'november', 12: 'december'
    }

    month_name = month_names.get(month, '')
    manifest_path = project_root / "input_files" / "sync_manifest.json"

    # Try to read year from sync manifest (created by sync_monthly_data.py)
    # 동기화 매니페스트에서 연도 읽기 시도 (sync_monthly_data.py에서 생성)
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            if month_name in manifest.get("months", {}):
                year = manifest["months"][month_name].get("year")
                if year:
                    print(f"📋 Year detected from sync manifest: {year}")
                    print(f"   Source: Google Drive folder {manifest['months'][month_name].get('folder', 'unknown')}")
                    return int(year)
        except Exception as e:
            print(f"⚠️  Error reading sync manifest: {e}")

    # Fallback: check if data file exists
    # 대체: 데이터 파일 존재 확인
    data_file = project_root / "input_files" / f"basic manpower data {month_name}.csv"
    if not data_file.exists():
        print(f"⚠️  Data file not found: {data_file}")
        print(f"⚠️  Sync manifest not found for {month_name}")
        print(f"💡 Run: python sync_monthly_data.py --month {month} --year YYYY")

    return datetime.now().year


def update_dashboards_json(year: int, month: int, stats: dict, project_root: Path):
    """
    Update docs/dashboards.json with new dashboard entry
    docs/dashboards.json에 새 대시보드 항목 업데이트

    Args:
        year: Dashboard year / 대시보드 연도
        month: Dashboard month / 대시보드 월
        stats: Dashboard statistics / 대시보드 통계
        project_root: Project root path / 프로젝트 루트 경로
    """
    dashboards_json_path = project_root / "docs" / "dashboards.json"

    # Load existing data or create new
    # 기존 데이터 로드 또는 새로 생성
    if dashboards_json_path.exists():
        with open(dashboards_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "version": "1.0.0",
            "description": "HR Dashboard manifest file",
            "dashboards": []
        }

    # Create new dashboard entry
    # 새 대시보드 항목 생성
    new_entry = {
        "file": f"HR_Dashboard_Complete_{year}_{month:02d}.html",
        "year": year,
        "month": month,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "stats": stats
    }

    # Remove existing entry for same year/month if exists
    # 같은 연도/월의 기존 항목이 있으면 제거
    data["dashboards"] = [
        d for d in data["dashboards"]
        if not (d.get("year") == year and d.get("month") == month)
    ]

    # Add new entry at the beginning
    # 새 항목을 맨 앞에 추가
    data["dashboards"].insert(0, new_entry)

    # Sort by year and month (descending)
    # 연도와 월로 정렬 (내림차순)
    data["dashboards"].sort(key=lambda x: (x.get("year", 0), x.get("month", 0)), reverse=True)

    # Update lastUpdated
    # lastUpdated 업데이트
    data["lastUpdated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save updated data
    # 업데이트된 데이터 저장
    with open(dashboards_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"📋 Updated dashboards.json: {dashboards_json_path}")
    print(f"📋 dashboards.json 업데이트됨: {dashboards_json_path}")


def generate_partial_dashboard(
    target_month: str,
    language: str,
    error_message: str,
    project_root: Path
) -> str:
    """
    Generate a minimal partial dashboard when full generation fails
    전체 생성 실패 시 최소 부분 대시보드 생성

    Args:
        target_month: Target month in YYYY-MM format / YYYY-MM 형식의 대상 월
        language: Dashboard language / 대시보드 언어
        error_message: Error that caused full generation to fail / 전체 생성 실패 원인 오류
        project_root: Project root path / 프로젝트 루트 경로

    Returns:
        str: Minimal HTML dashboard / 최소 HTML 대시보드
    """
    from datetime import datetime

    generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Error summary based on language
    # 언어에 따른 오류 요약
    titles = {
        'ko': 'HR 대시보드 - 부분 생성',
        'en': 'HR Dashboard - Partial Generation',
        'vi': 'Bảng điều khiển HR - Tạo một phần'
    }
    error_titles = {
        'ko': '⚠️ 전체 대시보드 생성 실패',
        'en': '⚠️ Full Dashboard Generation Failed',
        'vi': '⚠️ Tạo bảng điều khiển đầy đủ thất bại'
    }
    error_descs = {
        'ko': '일부 데이터가 누락되어 전체 대시보드를 생성할 수 없습니다.',
        'en': 'Full dashboard could not be generated due to missing data.',
        'vi': 'Không thể tạo bảng điều khiển đầy đủ do thiếu dữ liệu.'
    }
    suggestions = {
        'ko': [
            'input_files/ 디렉토리에 필요한 데이터 파일이 있는지 확인',
            '파일 명명 규칙이 올바른지 확인',
            'logs/ 디렉토리에서 자세한 오류 메시지 확인'
        ],
        'en': [
            'Verify required data files exist in input_files/ directory',
            'Check that file naming conventions are correct',
            'Review logs/ directory for detailed error messages'
        ],
        'vi': [
            'Xác minh các tệp dữ liệu cần thiết tồn tại trong thư mục input_files/',
            'Kiểm tra quy ước đặt tên tệp chính xác',
            'Xem thư mục logs/ để biết thông báo lỗi chi tiết'
        ]
    }

    title = titles.get(language, titles['en'])
    error_title = error_titles.get(language, error_titles['en'])
    error_desc = error_descs.get(language, error_descs['en'])
    suggestion_list = suggestions.get(language, suggestions['en'])

    suggestions_html = '\n'.join([f'<li>{s}</li>' for s in suggestion_list])

    return f'''<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {target_month}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background-color: #f8fafc; min-height: 100vh; }}
        .error-container {{ max-width: 800px; margin: 50px auto; padding: 20px; }}
        .error-card {{ background: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .error-icon {{ font-size: 64px; margin-bottom: 20px; }}
        .error-title {{ color: #f59e0b; font-size: 28px; margin-bottom: 16px; }}
        .error-desc {{ color: #64748b; margin-bottom: 24px; }}
        .error-details {{ background: #fef3cd; border-radius: 8px; padding: 16px; margin-bottom: 24px; font-family: monospace; font-size: 13px; overflow-x: auto; }}
        .suggestions {{ background: #f1f5f9; border-radius: 8px; padding: 20px; }}
        .suggestions h5 {{ color: #334155; margin-bottom: 12px; }}
        .suggestions li {{ color: #64748b; margin-bottom: 8px; }}
        .meta-info {{ text-align: center; color: #94a3b8; font-size: 12px; margin-top: 24px; }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-card text-center">
            <div class="error-icon">⚠️</div>
            <h2 class="error-title">{error_title}</h2>
            <p class="error-desc">{error_desc}</p>

            <div class="error-details text-start">
                <strong>Error Details:</strong><br>
                {error_message}
            </div>

            <div class="suggestions text-start">
                <h5>💡 Suggestions / 해결 방법:</h5>
                <ul>
                    {suggestions_html}
                </ul>
            </div>

            <div class="meta-info">
                <p>Target Month: {target_month}</p>
                <p>Generated: {generation_time}</p>
            </div>
        </div>
    </div>
</body>
</html>'''


def validate_inputs(args, project_root: Path) -> bool:
    """
    Validate user inputs for security and correctness
    보안 및 정확성을 위한 사용자 입력 검증

    Args:
        args: Parsed command line arguments / 파싱된 명령줄 인수
        project_root: Project root path / 프로젝트 루트 경로

    Returns:
        bool: True if all inputs are valid / 모든 입력이 유효하면 True
    """
    # Validate year range (reasonable range: 2020-2050)
    # 연도 범위 검증 (합리적인 범위: 2020-2050)
    if not (2020 <= args.year <= 2050):
        print(f"❌ Invalid year: {args.year}")
        print(f"❌ 잘못된 연도: {args.year}")
        print("   Valid range / 유효 범위: 2020-2050")
        return False

    # Validate output directory if specified
    # 출력 디렉토리 지정 시 검증
    if args.output_dir:
        output_path = Path(args.output_dir).resolve()

        # Prevent path traversal attacks
        # 경로 탐색 공격 방지
        try:
            output_path.relative_to(project_root)
        except ValueError:
            # Output is outside project root - check if it's a safe location
            # 프로젝트 루트 외부 - 안전한 위치인지 확인
            if '..' in args.output_dir:
                print(f"❌ Invalid output directory (path traversal not allowed)")
                print(f"❌ 잘못된 출력 디렉토리 (경로 탐색 허용 안됨)")
                return False

        # Check if parent directory exists or can be created
        # 부모 디렉토리 존재 또는 생성 가능 여부 확인
        if not output_path.parent.exists():
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                print(f"❌ Cannot create output directory: {output_path}")
                print(f"❌ 출력 디렉토리를 생성할 수 없습니다: {output_path}")
                return False

    return True


def parse_arguments():
    """
    Parse command line arguments
    명령줄 인수 파싱

    Returns:
        argparse.Namespace: Parsed arguments / 파싱된 인수
    """
    parser = argparse.ArgumentParser(
        description="HR Dashboard Generator - Complete Version / HR 대시보드 생성기 - 완전판",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples / 예시:
  # Generate dashboard for September 2025 in Korean
  python src/generate_dashboard.py --month 9 --year 2025 --language ko

  # Generate dashboard for October 2025 in English
  python src/generate_dashboard.py --month 10 --year 2025 --language en

  # Generate dashboard for current month
  python src/generate_dashboard.py
        """
    )

    # Get current month/year as defaults
    # 현재 월/년도를 기본값으로 가져오기
    now = datetime.now()

    parser.add_argument(
        '--month', '-m',
        type=int,
        default=now.month,
        choices=range(1, 13),
        help='Target month (1-12) / 대상 월 (1-12)'
    )

    parser.add_argument(
        '--year', '-y',
        type=int,
        default=now.year,
        help='Target year (e.g., 2025) / 대상 연도 (예: 2025)'
    )

    parser.add_argument(
        '--language', '-l',
        type=str,
        default='ko',
        choices=['ko', 'en', 'vi'],
        help='Dashboard language (ko/en/vi) / 대시보드 언어 (ko/en/vi)'
    )

    parser.add_argument(
        '--sync',
        action='store_true',
        help='Enable Google Drive synchronization (deprecated - not used in complete version) / Google Drive 동기화 활성화 (완전판에서는 사용 안 함)'
    )

    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default=None,
        help='Output directory for dashboard file (default: output_files/) / 대시보드 파일 출력 디렉토리 (기본값: output_files/)'
    )

    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip pre-validation checks / 사전 검증 건너뛰기'
    )

    parser.add_argument(
        '--force-year',
        action='store_true',
        help='Force use of specified year without auto-correction / 지정된 연도 강제 사용 (자동 수정 안함)'
    )

    parser.add_argument(
        '--partial',
        action='store_true',
        help='Allow partial dashboard generation even with missing data / 데이터 누락 시에도 부분 대시보드 생성 허용'
    )

    return parser.parse_args()


def main():
    """
    Main entry point for dashboard generation
    대시보드 생성의 메인 진입점
    """
    # Check dependencies first
    # 의존성 먼저 확인
    if not check_dependencies():
        return 1

    # Initialize logger
    # 로거 초기화
    logger = init_logger(
        name="HR_Dashboard",
        log_level="INFO",
        console_output=False,  # Don't duplicate to console (already using print)
        file_output=True
    )

    # Parse command line arguments
    # 명령줄 인수 파싱
    args = parse_arguments()

    # Validate inputs
    # 입력 검증
    if not validate_inputs(args, project_root):
        return 1

    logger.info(
        f"대시보드 생성 시작",
        f"Dashboard generation started",
        month=args.month,
        year=args.year,
        language=args.language
    )

    # Auto-detect year from data file
    # 데이터 파일에서 연도 자동 감지
    detected_year = detect_data_year(args.month, project_root)

    # Validate and correct year if needed (unless --force-year is used)
    # 필요 시 연도 검증 및 수정 (--force-year 사용 시 제외)
    if args.year != detected_year:
        print("=" * 70)
        print("⚠️  YEAR MISMATCH DETECTED / 연도 불일치 감지")
        print("=" * 70)
        print(f"   Specified year / 지정된 연도: {args.year}")
        print(f"   Detected year / 감지된 연도: {detected_year}")
        print()
        if args.force_year:
            print(f"⚠️  Using specified year {args.year} (--force-year)")
            print(f"⚠️  지정된 연도 {args.year} 사용 (--force-year)")
        else:
            print(f"🔄 Auto-correcting to {detected_year}")
            print(f"🔄 {detected_year}년으로 자동 수정합니다")
            args.year = detected_year
        print("=" * 70)
        print()

    # Format target month as YYYY-MM
    # 대상 월을 YYYY-MM 형식으로 포맷
    target_month = f"{args.year}-{args.month:02d}"

    # Print banner
    # 배너 출력
    print("=" * 70)
    print("HR Dashboard Generator - Complete Version")
    print("HR 대시보드 생성기 - 완전판")
    print("=" * 70)
    print(f"Target Month / 대상 월: {target_month}")
    print(f"Language / 언어: {args.language.upper()}")
    print("=" * 70)
    print()

    # Run pre-validation checks (unless --skip-validation is used)
    # 사전 검증 실행 (--skip-validation 사용 시 제외)
    if not args.skip_validation:
        validation_passed, validation_report = run_pre_validation(
            project_root=project_root,
            year=args.year,
            month=args.month,
            language=args.language
        )

        if not validation_passed:
            print("❌ Pre-validation failed. Please fix the errors above before generating the dashboard.")
            print("❌ 사전 검증 실패. 대시보드 생성 전에 위 오류를 먼저 해결하세요.")
            print("💡 Use --skip-validation to bypass / --skip-validation으로 건너뛰기 가능")
            return 1
    else:
        print("⏭️  Skipping pre-validation (--skip-validation)")
        print("⏭️  사전 검증 건너뛰기 (--skip-validation)")

    try:
        # Calculate report_date as end of target month
        # target month의 마지막 날을 report_date로 계산
        import pandas as pd
        month_start = pd.Timestamp(f"{args.year}-{args.month:02d}-01")
        report_date = month_start + pd.DateOffset(months=1) - pd.DateOffset(days=1)

        print(f"📅 Report Date (month end): {report_date.strftime('%Y-%m-%d')}")
        print()

        # Initialize Complete Dashboard Builder
        # 완전판 대시보드 빌더 초기화
        print("🔧 Initializing Complete Dashboard Builder...")
        print("🔧 완전판 대시보드 빌더 초기화 중...")

        builder = CompleteDashboardBuilder(
            target_month=target_month,
            language=args.language,
            report_date=report_date
        )

        # Build dashboard HTML
        # 대시보드 HTML 빌드
        print("🔨 Building dashboard HTML...")
        print("🔨 대시보드 HTML 빌드 중...")

        html_content = builder.build()

        # Save to output file
        # 출력 파일에 저장
        if args.output_dir:
            output_dir = Path(args.output_dir)
        else:
            output_dir = Path(__file__).parent.parent / "output_files"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"HR_Dashboard_Complete_{args.year}_{args.month:02d}.html"

        # Backup existing dashboard before overwriting
        # 덮어쓰기 전 기존 대시보드 백업
        backup_existing_dashboard(output_file)

        print(f"💾 Saving dashboard to: {output_file}")
        print(f"💾 대시보드 저장 중: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Get file size
        # 파일 크기 가져오기
        file_size_kb = output_file.stat().st_size / 1024

        # Copy to docs folder for GitHub Pages
        # GitHub Pages용 docs 폴더에 복사
        docs_dir = project_root / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        docs_file = docs_dir / output_file.name
        shutil.copy(output_file, docs_file)
        print(f"📂 Copied to docs/: {docs_file}")
        print(f"📂 docs/에 복사됨: {docs_file}")

        # Extract stats from builder for dashboards.json
        # dashboards.json용 통계 추출
        target_month_key = f"{args.year}-{args.month:02d}"
        stats = {
            "total": "-",
            "absenceRate": "-",
            "resignationRate": "-"
        }

        if hasattr(builder, 'monthly_metrics') and target_month_key in builder.monthly_metrics:
            metrics = builder.monthly_metrics[target_month_key]
            stats["total"] = str(metrics.get('total_employees', '-'))
            absence_rate = metrics.get('absence_rate')
            if absence_rate is not None:
                stats["absenceRate"] = f"{absence_rate}%"
            resignation_rate = metrics.get('resignation_rate')
            if resignation_rate is not None:
                stats["resignationRate"] = f"{resignation_rate}%"

        # Update dashboards.json
        # dashboards.json 업데이트
        update_dashboards_json(args.year, args.month, stats, project_root)

        # Log success
        # 성공 로그
        logger.info(
            f"대시보드 생성 완료",
            f"Dashboard generation completed",
            output_file=str(output_file),
            file_size_kb=round(file_size_kb, 1),
            total_employees=stats.get("total", "-")
        )
        logger.log_file_operation("write", str(output_file), success=True)
        logger.log_file_operation("copy", str(docs_file), success=True)

        # Success message
        # 성공 메시지
        print()
        print("=" * 70)
        print("✅ Dashboard generation completed successfully!")
        print("✅ 대시보드 생성이 성공적으로 완료되었습니다!")
        print("=" * 70)
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"📁 Output file / 출력 파일: {output_file}")
        print(f"📂 Docs file / Docs 파일: {docs_file}")
        print(f"📏 File size / 파일 크기: {file_size_kb:.1f} KB")
        print(f"🕐 Generated / 생성 시간: {generation_time}")
        print()
        print("💡 Dashboard features / 대시보드 기능:")
        print("   • 3 tabs: Overview, Trends, Employee Details")
        print("   • Multi-month trend charts")
        print("   • Interactive KPI cards with modals")
        print("   • Employee detail table with filter/search/sort")
        print("   • Export to CSV/JSON")
        print("   • Multi-language support (런타임 전환 가능)")
        print()
        print("🌐 GitHub Pages URL:")
        print(f"   https://moonkaicuzui.github.io/HR/{output_file.name}")
        print()
        print("🌐 Open the HTML file in your browser to view the dashboard")
        print("🌐 브라우저에서 HTML 파일을 열어 대시보드를 확인하세요")
        print()
        print(f"📝 Log file / 로그 파일: {project_root / 'logs' / 'hr_dashboard.log'}")
        print("=" * 70)

        return 0

    except Exception as e:
        # Error handling with logging
        # 로깅과 함께 에러 처리
        logger.log_error_with_traceback(
            f"대시보드 생성 실패: {str(e)}",
            f"Dashboard generation failed: {str(e)}"
        )

        # Check if partial dashboard generation is enabled
        # 부분 대시보드 생성이 활성화되어 있는지 확인
        if args.partial:
            print()
            print("=" * 70)
            print("⚠️  Full dashboard generation failed, attempting partial recovery...")
            print("⚠️  전체 대시보드 생성 실패, 부분 복구 시도 중...")
            print("=" * 70)

            try:
                # Try to generate a minimal dashboard with available data
                # 사용 가능한 데이터로 최소 대시보드 생성 시도
                partial_html = generate_partial_dashboard(
                    target_month=target_month,
                    language=args.language,
                    error_message=str(e),
                    project_root=project_root
                )

                if partial_html:
                    # Save partial dashboard
                    output_file = output_dir / f"HR_Dashboard_Complete_{args.year}_{args.month:02d}_PARTIAL.html"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(partial_html)

                    print()
                    print("⚠️  Partial dashboard generated with limited data")
                    print("⚠️  제한된 데이터로 부분 대시보드가 생성되었습니다")
                    print(f"📁 Output file / 출력 파일: {output_file}")
                    logger.warning(
                        "부분 대시보드 생성 (제한된 데이터)",
                        "Partial dashboard generated (limited data)",
                        output_file=str(output_file)
                    )
                    return 0
            except Exception as partial_error:
                logger.log_error_with_traceback(
                    f"부분 대시보드 생성도 실패: {str(partial_error)}",
                    f"Partial dashboard generation also failed: {str(partial_error)}"
                )

        print()
        print("=" * 70)
        print("❌ Dashboard generation failed!")
        print("❌ 대시보드 생성에 실패했습니다!")
        print("=" * 70)
        print(f"Error / 에러: {str(e)}")
        print()
        print("💡 Troubleshooting tips / 문제 해결 팁:")
        print("   1. Check if input data files exist in input_files/ directory")
        print("      input_files/ 디렉토리에 입력 데이터 파일이 있는지 확인")
        print("   2. Verify file naming conventions match expected patterns")
        print("      파일 명명 규칙이 예상 패턴과 일치하는지 확인")
        print("   3. Check logs/ directory for detailed error messages")
        print("      자세한 오류 메시지는 logs/ 디렉토리 확인")
        print("   4. Try --partial flag for partial dashboard generation")
        print("      부분 대시보드 생성을 위해 --partial 플래그 시도")
        print("=" * 70)

        # Print full traceback for debugging
        # 디버깅을 위한 전체 traceback 출력
        import traceback
        print("\nFull error traceback / 전체 에러 traceback:")
        traceback.print_exc()

        return 1


if __name__ == '__main__':
    sys.exit(main())
