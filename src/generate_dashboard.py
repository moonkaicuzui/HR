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
from pathlib import Path
import argparse
from datetime import datetime

# Add parent directory to path for imports
# 부모 디렉토리를 import 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder


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

    return parser.parse_args()


def main():
    """
    Main entry point for dashboard generation
    대시보드 생성의 메인 진입점
    """
    # Parse command line arguments
    # 명령줄 인수 파싱
    args = parse_arguments()

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

        print(f"💾 Saving dashboard to: {output_file}")
        print(f"💾 대시보드 저장 중: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Get file size
        # 파일 크기 가져오기
        file_size_kb = output_file.stat().st_size / 1024

        # Success message
        # 성공 메시지
        print()
        print("=" * 70)
        print("✅ Dashboard generation completed successfully!")
        print("✅ 대시보드 생성이 성공적으로 완료되었습니다!")
        print("=" * 70)
        print(f"📁 Output file / 출력 파일: {output_file}")
        print(f"📏 File size / 파일 크기: {file_size_kb:.1f} KB")
        print()
        print("💡 Dashboard features / 대시보드 기능:")
        print("   • 3 tabs: Overview, Trends, Employee Details")
        print("   • Multi-month trend charts")
        print("   • Interactive KPI cards with modals")
        print("   • Employee detail table with filter/search/sort")
        print("   • Export to CSV/JSON")
        print("   • Multi-language support (런타임 전환 가능)")
        print()
        print("🌐 Open the HTML file in your browser to view the dashboard")
        print("🌐 브라우저에서 HTML 파일을 열어 대시보드를 확인하세요")
        print("=" * 70)

        return 0

    except Exception as e:
        # Error handling
        # 에러 처리
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
        print("=" * 70)

        # Print full traceback for debugging
        # 디버깅을 위한 전체 traceback 출력
        import traceback
        print("\nFull error traceback / 전체 에러 traceback:")
        traceback.print_exc()

        return 1


if __name__ == '__main__':
    sys.exit(main())
