#!/usr/bin/env python3
"""
regenerate_dashboard.py - Regenerate HR dashboard with updated metrics
대시보드 재생성 - 수정된 메트릭으로 HR 대시보드 재생성
"""

from pathlib import Path
from datetime import datetime

# Import current dashboard builder
from src.visualization.complete_dashboard_builder import CompleteDashboardBuilder


def main():
    """Regenerate dashboard with updated absence rate calculations"""

    print("=" * 70)
    print("🔄 HR 대시보드 재생성 중...")
    print("=" * 70)

    # Get September 2025 data (latest)
    target_month = '2025-09'

    print(f"\n📈 메트릭 계산 중 ({target_month})...")
    print("   ✅ 퇴사자를 결근율 계산에서 제외합니다")

    # Build dashboard (CompleteDashboardBuilder handles all internal logic)
    print("\n🏗️  대시보드 빌드 중...")
    builder = CompleteDashboardBuilder(
        target_month=target_month,
        language='ko',
        report_date=datetime.now()
    )

    html_output = builder.build()

    # Save to file
    hr_root = Path.cwd()
    output_file = hr_root / "output_files" / f"HR_Dashboard_Complete_{target_month.replace('-', '_')}.html"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)

    print(f"\n✅ 대시보드 생성 완료!")
    print(f"   📄 파일: {output_file}")
    print(f"   📏 크기: {output_file.stat().st_size:,} bytes")

    print("\n" + "=" * 70)
    print("📊 주요 변경사항:")
    print("=" * 70)
    print("✅ 결근율 계산에서 퇴사자 제외")
    print("✅ 출산휴가 제외 결근율에서 퇴사자 제외")
    print("✅ 무단결근율에서 퇴사자 제외")
    print("\n💡 이제 모든 결근율은 보고서 생성일 기준 재직자만 포함합니다")
    print("=" * 70)


if __name__ == '__main__':
    main()
