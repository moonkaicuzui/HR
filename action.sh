#!/bin/bash

################################################################################
# HR Dashboard Generation - Complete Automation Script
# HR 대시보드 생성 - 완전 자동화 스크립트
#
# This script automates the entire HR dashboard generation process:
# 이 스크립트는 전체 HR 대시보드 생성 프로세스를 자동화합니다:
# - User-friendly month/year selection / 사용자 친화적 월/년도 선택
# - Optional Google Drive synchronization / 선택적 Google Drive 동기화
# - Complete dashboard generation with validation / 검증을 포함한 완전한 대시보드 생성
# - Automatic browser opening / 자동 브라우저 열기
#
# NO FAKE DATA policy enforced throughout execution
# 전체 실행에서 가짜 데이터 금지 정책 적용
################################################################################

# Color codes for output / 출력용 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory (HR folder root)
# 스크립트 디렉토리 (HR 폴더 루트)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Python executable (can be customized)
# Python 실행 파일 (커스터마이징 가능)
PYTHON_CMD=${PYTHON_CMD:-python3}

################################################################################
# Helper Functions / 헬퍼 함수
################################################################################

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Python is available / Python 사용 가능 여부 확인
check_python() {
    if ! command -v $PYTHON_CMD &> /dev/null; then
        print_error "Python not found. Please install Python 3.8 or higher."
        print_error "Python을 찾을 수 없습니다. Python 3.8 이상을 설치하세요."
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found / Python $PYTHON_VERSION 발견"
}

# Check and install required Python packages / 필수 Python 패키지 확인 및 설치
check_dependencies() {
    print_info "Checking Python dependencies... / Python 의존성 확인 중..."

    if [ -f "requirements.txt" ]; then
        $PYTHON_CMD -m pip install -q -r requirements.txt
        print_success "Dependencies installed / 의존성 설치 완료"
    else
        print_warning "requirements.txt not found. Proceeding anyway..."
        print_warning "requirements.txt를 찾을 수 없습니다. 계속 진행..."
    fi
}

# Validate month input / 월 입력 검증
validate_month() {
    local month=$1
    if [[ ! "$month" =~ ^[1-9]$|^1[0-2]$ ]]; then
        return 1
    fi
    return 0
}

# Validate year input / 년도 입력 검증
validate_year() {
    local year=$1
    if [[ ! "$year" =~ ^20[2-9][0-9]$ ]]; then
        return 1
    fi
    return 0
}

# Get month name in Korean / 한국어 월 이름 가져오기
get_month_name_ko() {
    case $1 in
        1) echo "1월";;
        2) echo "2월";;
        3) echo "3월";;
        4) echo "4월";;
        5) echo "5월";;
        6) echo "6월";;
        7) echo "7월";;
        8) echo "8월";;
        9) echo "9월";;
        10) echo "10월";;
        11) echo "11월";;
        12) echo "12월";;
    esac
}

# Get month name in English / 영어 월 이름 가져오기
get_month_name_en() {
    case $1 in
        1) echo "January";;
        2) echo "February";;
        3) echo "March";;
        4) echo "April";;
        5) echo "May";;
        6) echo "June";;
        7) echo "July";;
        8) echo "August";;
        9) echo "September";;
        10) echo "October";;
        11) echo "November";;
        12) echo "December";;
    esac
}

################################################################################
# User Input Functions / 사용자 입력 함수
################################################################################

get_month_year() {
    print_header "Month and Year Selection / 월 및 년도 선택"

    # Default to current month/year / 기본값은 현재 월/년도
    CURRENT_MONTH=$(date +%-m)
    CURRENT_YEAR=$(date +%Y)

    # Get month / 월 입력
    while true; do
        echo -e "\n${BLUE}Enter target month (1-12) [Default: $CURRENT_MONTH]:${NC}"
        echo -e "${BLUE}대상 월을 입력하세요 (1-12) [기본값: $CURRENT_MONTH]:${NC}"
        read -r MONTH

        # Use default if empty / 비어있으면 기본값 사용
        MONTH=${MONTH:-$CURRENT_MONTH}

        if validate_month "$MONTH"; then
            MONTH_KO=$(get_month_name_ko $MONTH)
            MONTH_EN=$(get_month_name_en $MONTH)
            print_success "Selected month: $MONTH ($MONTH_EN / $MONTH_KO)"
            break
        else
            print_error "Invalid month. Please enter 1-12."
            print_error "유효하지 않은 월입니다. 1-12를 입력하세요."
        fi
    done

    # Get year / 년도 입력
    while true; do
        echo -e "\n${BLUE}Enter target year (e.g., 2025) [Default: $CURRENT_YEAR]:${NC}"
        echo -e "${BLUE}대상 연도를 입력하세요 (예: 2025) [기본값: $CURRENT_YEAR]:${NC}"
        read -r YEAR

        # Use default if empty / 비어있으면 기본값 사용
        YEAR=${YEAR:-$CURRENT_YEAR}

        if validate_year "$YEAR"; then
            print_success "Selected year: $YEAR"
            break
        else
            print_error "Invalid year. Please enter a year like 2025."
            print_error "유효하지 않은 연도입니다. 2025와 같은 연도를 입력하세요."
        fi
    done
}

# Language selection removed - dashboard supports runtime language switching
# 언어 선택 제거 - 대시보드가 런타임 언어 전환을 지원함

get_google_drive_option() {
    print_header "Google Drive Sync / Google Drive 동기화"

    echo -e "\n${BLUE}Enable Google Drive synchronization? / Google Drive 동기화를 활성화하시겠습니까?${NC}"
    echo "  (Requires credentials/service-account-key.json)"
    echo "  (credentials/service-account-key.json 필요)"
    echo -e "${BLUE}[y/N]:${NC}"
    read -r SYNC_CHOICE

    case $(echo "$SYNC_CHOICE" | tr '[:upper:]' '[:lower:]') in
        y|yes)
            # Check if credentials exist / 인증 정보 존재 확인
            if [ -f "credentials/service-account-key.json" ]; then
                SYNC_FLAG="--sync"
                print_success "Google Drive sync enabled / Google Drive 동기화 활성화"
            else
                print_error "Credentials not found: credentials/service-account-key.json"
                print_error "인증 정보를 찾을 수 없음: credentials/service-account-key.json"
                SYNC_FLAG=""
                print_warning "Proceeding without Google Drive sync / Google Drive 동기화 없이 진행"
            fi
            ;;
        *)
            SYNC_FLAG=""
            print_info "Google Drive sync disabled / Google Drive 동기화 비활성화"
            ;;
    esac
}

################################################################################
# Google Drive Synchronization / Google Drive 동기화
################################################################################

sync_google_drive() {
    print_header "Syncing Data from Google Drive / Google Drive에서 데이터 동기화 중"

    # Check if sync script exists
    if [ ! -f "sync_monthly_data.py" ]; then
        print_error "sync_monthly_data.py not found!"
        print_error "sync_monthly_data.py를 찾을 수 없습니다!"
        return 1
    fi

    print_info "Downloading data for $YEAR-$(printf %02d $MONTH) ($MONTH_EN / $MONTH_KO)..."
    echo ""

    # Execute sync script / 동기화 스크립트 실행
    SYNC_CMD="$PYTHON_CMD sync_monthly_data.py --month $MONTH --year $YEAR"

    if $SYNC_CMD; then
        print_success "Google Drive sync completed successfully!"
        print_success "Google Drive 동기화가 성공적으로 완료되었습니다!"
        echo ""
        return 0
    else
        print_error "Google Drive sync failed!"
        print_error "Google Drive 동기화에 실패했습니다!"
        print_warning "Proceeding with local files if available..."
        print_warning "가능한 경우 로컬 파일로 진행합니다..."
        echo ""
        return 1
    fi
}

################################################################################
# Dashboard Generation / 대시보드 생성
################################################################################

generate_dashboard() {
    print_header "Generating HR Dashboard / HR 대시보드 생성 중"

    print_info "Target: $YEAR-$(printf %02d $MONTH) ($MONTH_EN / $MONTH_KO)"
    print_info "Note: Dashboard includes all language translations (KO/EN/VI)"

    # Check if main script exists
    if [ ! -f "src/generate_dashboard.py" ]; then
        print_error "src/generate_dashboard.py not found!"
        print_error "src/generate_dashboard.py를 찾을 수 없습니다!"
        return 1
    fi

    # Build command (without --sync flag as it's deprecated)
    # 명령 빌드 (--sync 플래그 제거, deprecated됨)
    CMD="$PYTHON_CMD src/generate_dashboard.py --month $MONTH --year $YEAR --language ko"

    print_info "Executing: $CMD"
    echo ""

    # Execute dashboard generation / 대시보드 생성 실행
    if $CMD; then
        print_success "Dashboard generation completed successfully!"
        print_success "대시보드 생성이 성공적으로 완료되었습니다!"

        # Copy chart utilities to output directory / 차트 유틸리티를 output 디렉토리로 복사
        if [ -f "src/visualization/chart_utils.js" ]; then
            cp "src/visualization/chart_utils.js" "output_files/"
            print_success "Chart utilities copied to output directory"
            print_success "차트 유틸리티가 output 디렉토리로 복사되었습니다"
        fi

        return 0
    else
        print_error "Dashboard generation failed!"
        print_error "대시보드 생성에 실패했습니다!"
        return 1
    fi
}

################################################################################
# Validation / 검증
################################################################################

run_comprehensive_tests() {
    print_header "Running Comprehensive Tests / 종합 테스트 실행 중"

    if [ ! -f "test_dashboard_comprehensive.py" ]; then
        print_warning "test_dashboard_comprehensive.py not found. Skipping tests."
        print_warning "test_dashboard_comprehensive.py를 찾을 수 없습니다. 테스트를 건너뜁니다."
        return 1
    fi

    print_info "Running 66 comprehensive tests..."
    print_info "66개의 종합 테스트 실행 중..."
    echo ""

    if $PYTHON_CMD test_dashboard_comprehensive.py; then
        print_success "All tests passed! (66/66)"
        print_success "모든 테스트 통과! (66/66)"
        return 0
    else
        print_error "Some tests failed!"
        print_error "일부 테스트가 실패했습니다!"
        return 1
    fi
}

run_metrics_validation() {
    print_header "Validating Metrics / 메트릭 검증 중"

    if [ ! -f "validate_dashboard_metrics.py" ]; then
        print_warning "validate_dashboard_metrics.py not found. Skipping validation."
        print_warning "validate_dashboard_metrics.py를 찾을 수 없습니다. 검증을 건너뜁니다."
        return 1
    fi

    print_info "Validating metrics for $YEAR-$(printf %02d $MONTH)..."
    print_info "$YEAR-$(printf %02d $MONTH)의 메트릭 검증 중..."
    echo ""

    # Pass month and year to validation script
    if $PYTHON_CMD validate_dashboard_metrics.py --month $MONTH --year $YEAR; then
        print_success "Metrics validation completed!"
        print_success "메트릭 검증 완료!"
        return 0
    else
        print_error "Metric validation failed!"
        print_error "메트릭 검증에 실패했습니다!"
        return 1
    fi
}

################################################################################
# Post-Generation Actions / 생성 후 작업
################################################################################

open_dashboard() {
    print_header "Opening Dashboard / 대시보드 열기"

    # Find generated dashboard file / 생성된 대시보드 파일 찾기
    DASHBOARD_FILE="output_files/HR_Dashboard_Complete_${YEAR}_$(printf %02d $MONTH).html"

    if [ -f "$DASHBOARD_FILE" ]; then
        FILE_SIZE=$(du -h "$DASHBOARD_FILE" | cut -f1)
        print_info "Generated file: $DASHBOARD_FILE (Size: $FILE_SIZE)"
        print_info "생성된 파일: $DASHBOARD_FILE (크기: $FILE_SIZE)"

        echo -e "\n${BLUE}Open dashboard in browser? / 브라우저에서 대시보드를 여시겠습니까?${NC}"
        echo -e "${BLUE}[Y/n]:${NC}"
        read -r OPEN_CHOICE

        case $(echo "$OPEN_CHOICE" | tr '[:upper:]' '[:lower:]') in
            n|no)
                print_info "Dashboard saved at: $DASHBOARD_FILE"
                print_info "대시보드 저장 위치: $DASHBOARD_FILE"
                ;;
            *)
                # Open in default browser / 기본 브라우저에서 열기
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    # macOS
                    open "$DASHBOARD_FILE"
                elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                    # Linux
                    xdg-open "$DASHBOARD_FILE" 2>/dev/null
                elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
                    # Windows
                    start "$DASHBOARD_FILE"
                fi
                print_success "Dashboard opened in browser / 브라우저에서 대시보드 열림"
                print_info "Use language selector (🇰🇷/🇺🇸/🇻🇳) in top-right corner to switch languages"
                print_info "우측 상단의 언어 선택기(🇰🇷/🇺🇸/🇻🇳)로 언어를 전환할 수 있습니다"
                ;;
        esac
    else
        print_warning "Dashboard file not found: $DASHBOARD_FILE"
        print_warning "대시보드 파일을 찾을 수 없음: $DASHBOARD_FILE"
    fi
}

show_summary() {
    print_header "Summary / 요약"

    echo -e "\n${GREEN}Dashboard Generation Summary:${NC}"
    echo -e "${GREEN}대시보드 생성 요약:${NC}"
    echo -e "  • Target Period / 대상 기간: $YEAR-$(printf %02d $MONTH) ($MONTH_EN / $MONTH_KO)"
    echo -e "  • Google Drive Sync / Google Drive 동기화: $([ -n "$SYNC_FLAG" ] && echo 'Enabled / 활성화' || echo 'Disabled / 비활성화')"
    echo -e "  • Output Location / 출력 위치: output_files/"
    echo -e "  • Languages Supported / 지원 언어: Korean, English, Vietnamese (런타임 전환)"
    echo ""

    print_info "Dashboard features / 대시보드 기능:"
    echo -e "  • 3 tabs: Overview, Trends, Employee Details"
    echo -e "  • 11 KPI metrics with modals"
    echo -e "  • 4 Chart.js trend visualizations"
    echo -e "  • Employee table with filter/search/sort"
    echo -e "  • Export to CSV/JSON"
    echo ""
}

################################################################################
# Main Execution / 메인 실행
################################################################################

main() {
    clear

    print_header "HR Dashboard Generation - Automation Script"
    print_header "HR 대시보드 생성 - 자동화 스크립트"

    echo -e "\n${BLUE}This script will guide you through the HR dashboard generation process.${NC}"
    echo -e "${BLUE}이 스크립트는 HR 대시보드 생성 프로세스를 안내합니다.${NC}\n"

    # Step 1: Check Python / Python 확인
    check_python

    # Step 2: Check dependencies / 의존성 확인
    check_dependencies

    # Step 3: Get user inputs / 사용자 입력 받기
    get_month_year
    get_google_drive_option

    # Step 4: Confirm before proceeding / 진행 전 확인
    echo -e "\n${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Ready to generate dashboard with the following settings:${NC}"
    echo -e "${YELLOW}다음 설정으로 대시보드를 생성할 준비가 되었습니다:${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo -e "  • Period / 기간: $YEAR-$(printf %02d $MONTH) ($MONTH_EN / $MONTH_KO)"
    echo -e "  • Languages / 언어: KO/EN/VI (런타임 전환 가능)"
    echo -e "  • Google Drive: $([ -n "$SYNC_FLAG" ] && echo 'Yes / 예' || echo 'No / 아니오')"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo -e "\n${BLUE}Proceed? / 진행하시겠습니까? [Y/n]:${NC}"
    read -r PROCEED

    case $(echo "$PROCEED" | tr '[:upper:]' '[:lower:]') in
        n|no)
            print_warning "Operation cancelled by user / 사용자가 작업을 취소했습니다"
            exit 0
            ;;
    esac

    # Step 5: Sync from Google Drive (if enabled) / Google Drive 동기화 (활성화된 경우)
    if [ -n "$SYNC_FLAG" ]; then
        sync_google_drive
        # Continue even if sync fails (will use local files)
        # 동기화 실패해도 계속 진행 (로컬 파일 사용)
    fi

    # Step 6: Generate dashboard / 대시보드 생성
    if generate_dashboard; then
        # Step 7: Run validation (optional) / 검증 실행 (선택사항)
        echo -e "\n${BLUE}Run validation tests? / 검증 테스트를 실행하시겠습니까? [Y/n]:${NC}"
        read -r RUN_VALIDATION

        case $(echo "$RUN_VALIDATION" | tr '[:upper:]' '[:lower:]') in
            n|no)
                print_info "Skipping validation / 검증을 건너뜁니다"
                ;;
            *)
                run_comprehensive_tests
                run_metrics_validation
                ;;
        esac

        # Step 8: Post-generation actions / 생성 후 작업
        open_dashboard
        show_summary

        print_success "All done! / 모든 작업 완료!"
        exit 0
    else
        print_error "Dashboard generation failed."
        print_error "대시보드 생성 실패."
        exit 1
    fi
}

# Run main function / 메인 함수 실행
main "$@"
