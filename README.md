# HR Dashboard System
# HR 대시보드 시스템

**Version**: 1.0.0
**Last Updated**: 2025-10-05

---

## Quick Start / 빠른 시작

### One-Command Dashboard Generation / 원클릭 대시보드 생성

```bash
cd HR
./action.sh
```

Follow the interactive prompts to:
대화형 프롬프트를 따라:
- Select month and year / 월과 연도 선택
- Choose language (Korean/English/Vietnamese) / 언어 선택 (한국어/영어/베트남어)
- Enable Google Drive sync (optional) / Google Drive 동기화 활성화 (선택사항)

Output dashboard will be saved to `output_files/HR_Dashboard_YYYY_MM.html`
출력 대시보드는 `output_files/HR_Dashboard_YYYY_MM.html`에 저장됩니다

---

## Table of Contents / 목차

1. [Overview / 개요](#overview)
2. [Key Features / 주요 기능](#key-features)
3. [Project Structure / 프로젝트 구조](#project-structure)
4. [Installation / 설치](#installation)
5. [Usage / 사용법](#usage)
6. [Configuration / 설정](#configuration)
7. [Architecture / 아키텍처](#architecture)
8. [Development / 개발](#development)
9. [Troubleshooting / 문제 해결](#troubleshooting)

---

## Overview / 개요

The HR Dashboard System is a **configuration-driven**, **highly reusable** dashboard generation platform designed to analyze and visualize HR metrics without hardcoded business logic.

HR 대시보드 시스템은 하드코딩된 비즈니스 로직 없이 HR 메트릭을 분석하고 시각화하도록 설계된 **설정 기반**, **높은 재활용성**을 가진 대시보드 생성 플랫폼입니다.

### Core Principles / 핵심 원칙

1. **NO FAKE DATA** / **가짜 데이터 없음**
   - System returns empty results if data doesn't exist
   - Never generates synthetic data
   - 데이터가 없으면 빈 결과 반환
   - 합성 데이터를 생성하지 않음

2. **Configuration Over Code** / **코드보다 설정**
   - All business rules in JSON files
   - Zero hardcoded formulas or thresholds
   - 모든 비즈니스 규칙이 JSON 파일에
   - 하드코딩된 공식이나 임계값 없음

3. **Reusability Through Parameterization** / **매개변수화를 통한 재활용성**
   - Same functions work for ANY subject/metric combination
   - "Overall absence rate", "Team A attendance", "Unauthorized absence trend" use identical code
   - 동일한 함수가 모든 주제/메트릭 조합에서 작동
   - "전체 결근율", "팀 A 출근율", "무단 결근 트렌드"가 동일한 코드 사용

4. **Multi-Language Support** / **다국어 지원**
   - Full Korean, English, Vietnamese translations
   - Bilingual code comments (Korean + English)
   - 한국어, 영어, 베트남어 완전 번역
   - 이중 언어 코드 주석 (한국어 + 영어)

---

## Key Features / 주요 기능

### ✨ User Features / 사용자 기능

- **Interactive Dashboard** / **대화형 대시보드**
  - Summary cards with color-coded metrics
  - Interactive charts (Chart.js v4)
  - Responsive design (Bootstrap 5)
  - 색상으로 구분된 메트릭이 있는 요약 카드
  - 대화형 차트 (Chart.js v4)
  - 반응형 디자인 (Bootstrap 5)

- **Multi-Language UI** / **다국어 UI**
  - Korean, English, Vietnamese support
  - Language switching via dropdown
  - Persistent language preference
  - 한국어, 영어, 베트남어 지원
  - 드롭다운으로 언어 전환
  - 지속적인 언어 선호도

- **Error Reporting** / **오류 보고**
  - 6 error categories (temporal, type, position, team, attendance, duplicate)
  - Severity classification (critical, warning, info)
  - Detailed error descriptions
  - 6가지 오류 범주 (시간, TYPE, 직급, 팀, 출근, 중복)
  - 심각도 분류 (심각, 경고, 정보)
  - 상세한 오류 설명

### 🔧 Technical Features / 기술적 기능

- **Zero Hardcoding** / **하드코딩 없음**
  - All metrics defined in JSON
  - All thresholds in configuration
  - All translations in JSON
  - 모든 메트릭이 JSON에 정의
  - 모든 임계값이 설정에
  - 모든 번역이 JSON에

- **Google Drive Integration** / **Google Drive 통합**
  - Optional cloud synchronization
  - Smart caching with MD5 checksums
  - Batch file operations
  - 선택적 클라우드 동기화
  - MD5 체크섬을 이용한 스마트 캐싱
  - 배치 파일 작업

- **Single-File Output** / **단일 파일 출력**
  - Complete HTML with embedded CSS/JS
  - No external dependencies for viewing
  - Works offline
  - CSS/JS가 임베디드된 완전한 HTML
  - 보기에 외부 의존성 없음
  - 오프라인 작동

---

## Project Structure / 프로젝트 구조

```
HR/
├── action.sh                    # Main automation script / 메인 자동화 스크립트
├── README.md                    # This file / 이 파일
├── ARCHITECTURE.md              # Detailed architecture documentation / 상세 아키텍처 문서
├── HARDCODING_DOCUMENTATION.md  # Hardcoding catalog / 하드코딩 목록
│
├── config/                      # Configuration files / 설정 파일
│   ├── dashboard_config.json    # Dashboard layout & styling / 대시보드 레이아웃 및 스타일
│   ├── metric_definitions.json  # Metric formulas & thresholds / 메트릭 공식 및 임계값
│   ├── chart_templates.json     # Reusable chart configs / 재활용 가능한 차트 설정
│   └── translations.json        # Multi-language UI text / 다국어 UI 텍스트
│
├── src/                         # Source code / 소스 코드
│   ├── utils/                   # Utility modules / 유틸리티 모듈
│   │   ├── i18n.py              # Internationalization / 국제화
│   │   ├── date_parser.py       # Date parsing (12+ formats) / 날짜 파싱 (12가지 이상 형식)
│   │   └── logger.py            # Bilingual logging / 이중 언어 로깅
│   │
│   ├── integration/             # External integrations / 외부 통합
│   │   └── google_drive_sync.py # Google Drive sync / Google Drive 동기화
│   │
│   ├── core/                    # Core data modules / 핵심 데이터 모듈
│   │   ├── data_loader.py       # Multi-source data loading / 다중 소스 데이터 로딩
│   │   ├── data_validator.py    # Data validation / 데이터 검증
│   │   └── error_detector.py    # Error categorization / 오류 분류
│   │
│   ├── analytics/               # Analysis engines / 분석 엔진
│   │   ├── metric_calculator.py # JSON-driven metrics / JSON 기반 메트릭
│   │   └── trend_analyzer.py    # Subject-agnostic trends / 주제 무관 트렌드
│   │
│   ├── visualization/           # Chart & HTML generation / 차트 및 HTML 생성
│   │   ├── chart_generator.py   # Template-based charts / 템플릿 기반 차트
│   │   └── html_builder.py      # Complete HTML dashboard / 완전한 HTML 대시보드
│   │
│   └── generate_dashboard.py    # Main orchestrator / 메인 오케스트레이터
│
├── input_files/                 # Data sources (created on first run) / 데이터 소스 (첫 실행 시 생성)
│   ├── basic_manpower/          # Basic manpower data / 기본 인력 데이터
│   ├── attendance/              # Attendance records / 출근 기록
│   ├── aql/                     # AQL history / AQL 이력
│   └── 5prs/                    # 5PRS data / 5PRS 데이터
│
├── output_files/                # Generated dashboards / 생성된 대시보드
│   └── HR_Dashboard_YYYY_MM.html
│
├── credentials/                 # Google Drive credentials (optional) / Google Drive 인증 (선택)
│   └── service-account-key.json
│
└── logs/                        # Application logs / 애플리케이션 로그
    └── hr_dashboard_YYYY-MM-DD.log
```

---

## Installation / 설치

### Prerequisites / 전제조건

- Python 3.8 or higher / Python 3.8 이상
- pip (Python package manager) / pip (Python 패키지 관리자)

### Step 1: Install Dependencies / 단계 1: 의존성 설치

```bash
cd HR
pip install -r requirements.txt
```

**Required packages / 필수 패키지**:
- pandas >= 1.3.0
- openpyxl >= 3.0.9 (for Excel support)

**Optional packages / 선택 패키지** (for Google Drive sync):
- google-auth >= 2.16.0
- google-api-python-client >= 2.80.0

### Step 2: Configure Google Drive (Optional) / 단계 2: Google Drive 설정 (선택)

If using Google Drive synchronization / Google Drive 동기화 사용 시:

1. Create a Google Cloud project / Google Cloud 프로젝트 생성
2. Enable Google Drive API / Google Drive API 활성화
3. Create service account credentials / 서비스 계정 인증 생성
4. Download JSON key file / JSON 키 파일 다운로드
5. Save as `credentials/service-account-key.json`

---

## Usage / 사용법

### Method 1: Interactive Script (Recommended) / 방법 1: 대화형 스크립트 (권장)

```bash
./action.sh
```

The script will guide you through:
스크립트가 다음을 안내합니다:
1. Month and year selection / 월 및 연도 선택
2. Language preference / 언어 선호도
3. Google Drive sync option / Google Drive 동기화 옵션
4. Automatic dashboard generation / 자동 대시보드 생성
5. Browser opening (optional) / 브라우저 열기 (선택)

### Method 2: Direct Python Command / 방법 2: 직접 Python 명령

```bash
python src/generate_dashboard.py --month 9 --year 2025 --language ko
```

**Arguments / 인수**:
- `--month, -m`: Target month (1-12) / 대상 월 (1-12)
- `--year, -y`: Target year (e.g., 2025) / 대상 연도 (예: 2025)
- `--language, -l`: Dashboard language (ko/en/vi) / 대시보드 언어 (ko/en/vi)
- `--sync`: Enable Google Drive sync / Google Drive 동기화 활성화

**Examples / 예시**:
```bash
# Korean dashboard for September 2025
python src/generate_dashboard.py --month 9 --year 2025 --language ko

# English dashboard with Google Drive sync
python src/generate_dashboard.py --month 9 --year 2025 --language en --sync

# Vietnamese dashboard
python src/generate_dashboard.py --month 9 --year 2025 --language vi
```

---

## Configuration / 설정

### Adding New Metric (No Code Required) / 새 메트릭 추가 (코드 불필요)

**Step 1**: Edit `config/metric_definitions.json`
**단계 1**: `config/metric_definitions.json` 편집

```json
{
  "my_new_metric": {
    "id": "my_new_metric",
    "formula": "SUM(column_name) / COUNT(*)",
    "data_sources": ["basic_manpower"],
    "calculation_method": "percentage",
    "thresholds": {
      "excellent": {"max": 5, "color": "#28a745"},
      "critical": {"min": 15, "color": "#dc3545"}
    },
    "trend_enabled": true,
    "reusable": true
  }
}
```

**Step 2**: Edit `config/translations.json`
**단계 2**: `config/translations.json` 편집

```json
{
  "ko": {
    "metrics": {
      "my_new_metric": "내 새 메트릭"
    }
  },
  "en": {
    "metrics": {
      "my_new_metric": "My New Metric"
    }
  },
  "vi": {
    "metrics": {
      "my_new_metric": "Chỉ số mới của tôi"
    }
  }
}
```

**Step 3**: Run dashboard generation
**단계 3**: 대시보드 생성 실행

```bash
./action.sh
```

✅ **No Python code changes required!**
✅ **Python 코드 변경 불필요!**

### Changing Thresholds / 임계값 변경

Edit `config/metric_definitions.json`:
`config/metric_definitions.json` 편집:

```json
{
  "absence_rate": {
    "thresholds": {
      "excellent": {"max": 3, "color": "#28a745"},
      "good": {"min": 3, "max": 5, "color": "#17a2b8"},
      "warning": {"min": 5, "max": 10, "color": "#ffc107"},
      "critical": {"min": 10, "color": "#dc3545"}
    }
  }
}
```

No code deployment needed - just regenerate dashboard.
코드 배포 불필요 - 대시보드만 재생성.

---

## Architecture / 아키텍처

### High-Level Design / 상위 수준 설계

```
┌─────────────────────────────────────────────┐
│        Presentation Layer                    │
│        (HTMLBuilder, action.sh)              │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│        Visualization Layer                   │
│        (ChartGenerator)                      │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│        Analytics Layer                       │
│   (MetricCalculator, TrendAnalyzer)          │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│        Core Layer                            │
│ (DataLoader, DataValidator, ErrorDetector)   │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│        Integration Layer                     │
│        (GoogleDriveSync)                     │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│        Utilities Layer                       │
│    (I18n, DateParser, HRLogger)              │
└─────────────────────────────────────────────┘
```

### Reusability Pattern / 재활용성 패턴

**Key Principle**: Same function works for ANY subject/metric combination
**핵심 원칙**: 동일한 함수가 모든 주제/메트릭 조합에서 작동

```python
# ONE FUNCTION for all trend analyses
# 모든 트렌드 분석에 하나의 함수

trend_analyzer.analyze_trend(
    subject="Overall",          # Can be "Team A", "Position X", etc.
    metric="absence_rate",      # Can be ANY metric
    subject_filter={}           # Optional filtering
)
```

For detailed architecture documentation, see **[ARCHITECTURE.md](./ARCHITECTURE.md)**.
상세한 아키텍처 문서는 **[ARCHITECTURE.md](./ARCHITECTURE.md)**를 참조하세요.

---

## Development / 개발

### Code Style / 코드 스타일

- **Bilingual Comments** / **이중 언어 주석**: All comments in Korean + English simultaneously
- **Type Hints** / **타입 힌트**: Use Python type annotations for all functions
- **Docstrings** / **문서화 문자열**: Include bilingual docstrings for all public functions
- **PEP 8** / **PEP 8**: Follow Python style guidelines

**Example / 예시**:
```python
def calculate_metric(
    self,
    metric_id: str,
    data: pd.DataFrame,
    subject: str = "Overall"
) -> MetricValue:
    """
    Calculate metric value from data
    데이터로부터 메트릭 값 계산

    Args:
        metric_id: Metric identifier from metric_definitions.json
                   metric_definitions.json의 메트릭 식별자
        data: Input DataFrame
              입력 DataFrame
        subject: Subject name (e.g., "Overall", "Team A")
                 주제 이름 (예: "Overall", "Team A")

    Returns:
        MetricValue with calculated value, threshold, and color
        계산된 값, 임계값, 색상을 포함한 MetricValue
    """
```

### Adding New Module / 새 모듈 추가

1. Create module file in appropriate `src/` subdirectory / `src/` 하위 디렉토리에 모듈 파일 생성
2. Add bilingual comments and docstrings / 이중 언어 주석 및 문서화 문자열 추가
3. Follow reusability principle (parameterize, don't duplicate) / 재활용성 원칙 따르기 (매개변수화, 중복 금지)
4. Update `__init__.py` to export public API / `__init__.py` 업데이트하여 공개 API 내보내기
5. Document in ARCHITECTURE.md / ARCHITECTURE.md에 문서화
6. If hardcoding required, document in HARDCODING_DOCUMENTATION.md / 하드코딩이 필요하면 HARDCODING_DOCUMENTATION.md에 문서화

### Testing / 테스트

```bash
# Run manual tests
# 수동 테스트 실행
python src/generate_dashboard.py --month 9 --year 2025 --language ko

# Check logs
# 로그 확인
tail -f logs/hr_dashboard_$(date +%Y-%m-%d).log

# Verify output
# 출력 확인
open output_files/HR_Dashboard_2025_09.html
```

---

## Troubleshooting / 문제 해결

### Issue: Module not found / 문제: 모듈을 찾을 수 없음

```bash
ModuleNotFoundError: No module named 'pandas'
```

**Solution / 해결책**:
```bash
pip install -r requirements.txt
```

### Issue: Google Drive authentication failed / 문제: Google Drive 인증 실패

```bash
google.auth.exceptions.DefaultCredentialsError
```

**Solution / 해결책**:
1. Check `credentials/service-account-key.json` exists / `credentials/service-account-key.json` 존재 확인
2. Verify service account has Drive API access / 서비스 계정에 Drive API 액세스 있는지 확인
3. Or run without `--sync` flag / 또는 `--sync` 플래그 없이 실행

### Issue: Empty dashboard (no data) / 문제: 빈 대시보드 (데이터 없음)

**Solution / 해결책**:
1. Check `input_files/` directory has required data files / `input_files/` 디렉토리에 필수 데이터 파일 있는지 확인
2. Verify file naming matches expected patterns / 파일 명명이 예상 패턴과 일치하는지 확인
3. Check logs for FileNotFoundError warnings / FileNotFoundError 경고 로그 확인
4. **Remember**: System returns empty if data doesn't exist (NO FAKE DATA policy) / **기억**: 데이터가 없으면 빈 상태 반환 (가짜 데이터 금지 정책)

### Issue: Dashboard not opening in browser / 문제: 브라우저에서 대시보드가 열리지 않음

**Solution / 해결책**:
```bash
# Manually open the dashboard file
# 대시보드 파일 수동으로 열기
open output_files/HR_Dashboard_2025_09.html

# Or use browser file menu
# 또는 브라우저 파일 메뉴 사용
```

### Issue: Wrong language displayed / 문제: 잘못된 언어 표시

**Solution / 해결책**:
1. Check `--language` argument / `--language` 인수 확인
2. Verify `config/translations.json` has required language / `config/translations.json`에 필수 언어 있는지 확인
3. Clear browser localStorage and reload / 브라우저 localStorage 지우고 다시 로드

### Checking Logs / 로그 확인

All operations are logged to `logs/` directory:
모든 작업이 `logs/` 디렉토리에 로그됨:

```bash
# View latest log
# 최신 로그 보기
tail -f logs/hr_dashboard_$(date +%Y-%m-%d).log

# Search for errors
# 오류 검색
grep "ERROR" logs/hr_dashboard_*.log
```

---

## Documentation / 문서

- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: Detailed system architecture, design patterns, and module descriptions
- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: 상세한 시스템 아키텍처, 설계 패턴 및 모듈 설명

- **[HARDCODING_DOCUMENTATION.md](./HARDCODING_DOCUMENTATION.md)**: Catalog of unavoidable hardcoded elements with modification guidelines
- **[HARDCODING_DOCUMENTATION.md](./HARDCODING_DOCUMENTATION.md)**: 수정 가이드라인이 포함된 불가피한 하드코딩 요소 목록

---

## FAQ / 자주 묻는 질문

**Q: Can I add new metrics without coding?**
**Q: 코딩 없이 새 메트릭을 추가할 수 있나요?**

A: Yes! Edit `config/metric_definitions.json` and `config/translations.json`, then regenerate the dashboard.
A: 네! `config/metric_definitions.json`과 `config/translations.json`을 편집한 다음 대시보드를 재생성하세요.

**Q: What if my data file doesn't exist?**
**Q: 데이터 파일이 존재하지 않으면 어떻게 되나요?**

A: The system will return empty results (NO FAKE DATA policy). Check logs for warnings.
A: 시스템은 빈 결과를 반환합니다 (가짜 데이터 금지 정책). 경고 로그를 확인하세요.

**Q: How do I change threshold values?**
**Q: 임계값을 어떻게 변경하나요?**

A: Edit the `thresholds` section in `config/metric_definitions.json`. No code changes needed.
A: `config/metric_definitions.json`의 `thresholds` 섹션을 편집하세요. 코드 변경 불필요.

**Q: Can I use this without Google Drive?**
**Q: Google Drive 없이 사용할 수 있나요?**

A: Yes, Google Drive sync is optional. Just run without `--sync` flag.
A: 네, Google Drive 동기화는 선택 사항입니다. `--sync` 플래그 없이 실행하세요.

**Q: How do I add a new language?**
**Q: 새 언어를 어떻게 추가하나요?**

A: Add new language code to `config/translations.json` with all required translations.
A: 모든 필수 번역과 함께 `config/translations.json`에 새 언어 코드를 추가하세요.

---

## License / 라이선스

This project is proprietary software for internal use.
이 프로젝트는 내부 사용을 위한 독점 소프트웨어입니다.

---

## Contact / 연락처

For questions or support / 질문 또는 지원:
- Check documentation in `ARCHITECTURE.md` and `HARDCODING_DOCUMENTATION.md`
- Review logs in `logs/` directory
- Contact development team

**Version**: 1.0.0
**Last Updated**: 2025-10-05
