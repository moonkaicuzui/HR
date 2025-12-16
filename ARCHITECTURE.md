# HR Dashboard System - Architecture Documentation
# HR 대시보드 시스템 - 아키텍처 문서

## Table of Contents / 목차

1. [System Overview / 시스템 개요](#system-overview)
2. [Core Principles / 핵심 원칙](#core-principles)
3. [Architecture Layers / 아키텍처 계층](#architecture-layers)
4. [Module Descriptions / 모듈 설명](#module-descriptions)
5. [Data Flow / 데이터 흐름](#data-flow)
6. [Reusability Pattern / 재활용성 패턴](#reusability-pattern)
7. [Configuration System / 설정 시스템](#configuration-system)
8. [Error Handling / 에러 처리](#error-handling)

---

## System Overview / 시스템 개요

The HR Dashboard System is a **completely independent**, **configuration-driven**, and **highly reusable** dashboard generation platform designed to analyze and visualize HR metrics without any hardcoded business logic.

HR 대시보드 시스템은 **완전히 독립적**이고 **설정 기반**이며 **높은 재활용성**을 가진 대시보드 생성 플랫폼으로, 하드코딩된 비즈니스 로직 없이 HR 메트릭을 분석하고 시각화하도록 설계되었습니다.

### Key Characteristics / 주요 특징

- **Zero Hardcoded Logic**: All business rules in JSON configuration files / 모든 비즈니스 규칙이 JSON 설정 파일에 있음
- **Subject/Object Agnostic**: Same functions work for ANY subject (team/position/overall) and metric combination / 동일한 함수가 모든 주제(팀/직급/전체)와 메트릭 조합에서 작동
- **NO FAKE DATA Policy**: System returns empty results if data doesn't exist, never generates synthetic data / 데이터가 없으면 빈 결과를 반환하며 가짜 데이터를 생성하지 않음
- **Multi-language Support**: Full Korean, English, Vietnamese translations / 한국어, 영어, 베트남어 완전 번역 지원
- **Self-Contained**: No external dependencies beyond Python standard library + pandas / Python 표준 라이브러리 + pandas 외 외부 의존성 없음
- **Single-File Output**: Complete HTML dashboard with embedded JavaScript and CSS / JavaScript와 CSS가 임베디드된 완전한 HTML 대시보드

---

## Core Principles / 핵심 원칙

### 1. Configuration Over Code / 코드보다 설정

**Philosophy**: Business logic belongs in configuration files, not in code.
**철학**: 비즈니스 로직은 코드가 아닌 설정 파일에 속합니다.

```
✅ Adding new metric → Update metric_definitions.json only
✅ 새 메트릭 추가 → metric_definitions.json만 업데이트

❌ Adding new metric → Write new Python function
❌ 새 메트릭 추가 → 새 Python 함수 작성
```

**Benefits / 이점**:
- Non-developers can modify business rules / 비개발자도 비즈니스 규칙 수정 가능
- No code deployment for configuration changes / 설정 변경에 코드 배포 불필요
- Easier testing and validation / 더 쉬운 테스트 및 검증

### 2. Reusability Through Parameterization / 매개변수화를 통한 재활용성

**Philosophy**: Write once, use for any subject/metric combination.
**철학**: 한 번 작성하여 모든 주제/메트릭 조합에 사용.

**Example / 예시**:
```python
# REUSABLE FUNCTION - Works for ANY subject and metric
# 재활용 가능 함수 - 모든 주제와 메트릭에서 작동

# Overall absence rate trend
result1 = trend_analyzer.analyze_trend(
    data=df,
    subject="Overall",
    metric="absence_rate",
    time_column="month",
    value_column="absence_rate"
)

# Team A attendance trend
result2 = trend_analyzer.analyze_trend(
    data=df,
    subject="Team A",
    metric="attendance_rate",
    time_column="month",
    value_column="attendance_rate",
    subject_filter={"team": "Team A"}
)

# SAME FUNCTION - Only parameters change!
# 동일한 함수 - 매개변수만 변경!
```

### 3. NO FAKE DATA Policy / 가짜 데이터 금지 정책

**Philosophy**: "우리사전에 가짜 데이타는 없다" (No fake data in our dictionary)
**철학**: "우리사전에 가짜 데이타는 없다"

**Implementation / 구현**:
```python
def load_data_source(self, file_path):
    """
    Load data from file or return empty DataFrame
    파일에서 데이터 로드 또는 빈 DataFrame 반환
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        self.logger.warning(f"File not found: {file_path}")
        # NO FAKE DATA - Return empty DataFrame
        # 가짜 데이터 없음 - 빈 DataFrame 반환
        return pd.DataFrame()
```

**Rules / 규칙**:
- ✅ Return empty DataFrame if file doesn't exist / 파일이 없으면 빈 DataFrame 반환
- ✅ Display 0 or "데이터 없음" in dashboard / 대시보드에 0 또는 "데이터 없음" 표시
- ✅ Log warnings for missing data / 누락된 데이터에 대한 경고 로그
- ❌ Never generate random/estimated/synthetic data / 무작위/추정/합성 데이터 생성 금지

### 4. Bilingual Code Comments / 이중 언어 코드 주석

**Philosophy**: All code comments in both Korean and English simultaneously.
**철학**: 모든 코드 주석을 한국어와 영어로 동시에 작성.

**Example / 예시**:
```python
def calculate_metric(self, data: pd.DataFrame):
    """
    Calculate metric value from data
    데이터로부터 메트릭 값 계산

    This function is reusable for any metric definition
    이 함수는 모든 메트릭 정의에 재활용 가능합니다
    """
```

---

## Architecture Layers / 아키텍처 계층

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│                      프레젠테이션 계층                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ HTMLBuilder  │  │action.sh     │  │   Browser    │       │
│  │ HTML 빌더    │  │자동화 스크립트 │  │   브라우저    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   Visualization Layer                        │
│                      시각화 계층                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │  ChartGenerator (템플릿 기반 차트 생성)              │       │
│  │  - Template-driven chart configuration            │       │
│  │  - Reusable for any data / 모든 데이터 재활용 가능   │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    Analytics Layer                           │
│                      분석 계층                                │
│  ┌───────────────────┐  ┌───────────────────────┐           │
│  │ MetricCalculator  │  │  TrendAnalyzer        │           │
│  │ 메트릭 계산기      │  │  트렌드 분석기          │           │
│  │ (JSON-driven)     │  │  (Subject-agnostic)   │           │
│  └───────────────────┘  └───────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer                              │
│                      핵심 계층                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ DataLoader   │  │DataValidator │  │ErrorDetector │      │
│  │ 데이터 로더  │  │데이터 검증기  │  │에러 감지기    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   Integration Layer                          │
│                      통합 계층                                │
│  ┌──────────────────────────────────────────────────┐       │
│  │  GoogleDriveSync (선택적 클라우드 동기화)           │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    Utilities Layer                           │
│                      유틸리티 계층                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │   I18n   │  │DateParser│  │ HRLogger │                  │
│  │ 다국어화  │  │날짜 파서  │  │ 로거      │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                  Configuration Layer                         │
│                      설정 계층                                │
│  ┌──────────────────────────────────────────────────┐       │
│  │  JSON Configuration Files (비즈니스 로직)         │       │
│  │  - metric_definitions.json                        │       │
│  │  - chart_templates.json                           │       │
│  │  - dashboard_config.json                          │       │
│  │  - translations.json                              │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Descriptions / 모듈 설명

### Configuration Files / 설정 파일

#### `config/metric_definitions.json`
**Purpose**: Define all metrics without code / 코드 없이 모든 메트릭 정의

**Structure / 구조**:
```json
{
  "absence_rate": {
    "id": "absence_rate",
    "formula": "100 - (SUM(actual_working_days) / SUM(total_working_days) * 100)",
    "data_sources": ["attendance", "basic_manpower"],
    "calculation_method": "percentage",
    "thresholds": {
      "excellent": {"max": 3, "color": "#28a745"},
      "critical": {"min": 10, "color": "#dc3545"}
    },
    "trend_enabled": true,
    "reusable": true
  }
}
```

**Key Features / 주요 기능**:
- Declarative metric definitions / 선언적 메트릭 정의
- Threshold-based evaluation / 임계값 기반 평가
- Automatic color assignment / 자동 색상 할당
- Reusability flag / 재활용성 플래그

#### `config/chart_templates.json`
**Purpose**: Reusable chart configurations / 재활용 가능한 차트 설정

**Structure / 구조**:
```json
{
  "line_trend": {
    "type": "line",
    "description": "Generic line chart for trends",
    "applicable_to": ["absence_rate", "attendance_rate", "any_percentage_metric"],
    "config": {
      "responsive": true,
      "scales": {
        "y": {
          "beginAtZero": true,
          "ticks": {
            "callback": "function(value) { return value + '%'; }"
          }
        }
      }
    }
  }
}
```

**Key Features / 주요 기능**:
- Template inheritance / 템플릿 상속
- Applicable scope definition / 적용 범위 정의
- Chart.js configuration / Chart.js 설정

#### `config/translations.json`
**Purpose**: Complete UI translations / 완전한 UI 번역

**Structure / 구조**:
```json
{
  "ko": {
    "cards": {
      "total_employees": "전체 직원"
    },
    "metrics": {
      "absence_rate": "결근율"
    }
  },
  "en": {
    "cards": {
      "total_employees": "Total Employees"
    },
    "metrics": {
      "absence_rate": "Absence Rate"
    }
  },
  "vi": {
    "cards": {
      "total_employees": "Tổng số nhân viên"
    },
    "metrics": {
      "absence_rate": "Tỷ lệ vắng mặt"
    }
  }
}
```

#### `config/dashboard_config.json`
**Purpose**: Dashboard layout and styling / 대시보드 레이아웃 및 스타일링

**Key Sections / 주요 섹션**:
- `layout`: Grid system, responsive breakpoints / 그리드 시스템, 반응형 중단점
- `cards`: Summary card configurations / 요약 카드 설정
- `colors`: Theme colors / 테마 색상
- `typography`: Font settings / 폰트 설정

### Utilities Layer / 유틸리티 계층

#### `src/utils/i18n.py`
**Responsibilities / 책임**:
- Multi-language translation management / 다국어 번역 관리
- Nested key support with dot notation / 점 표기법으로 중첩 키 지원
- Fallback to default language / 기본 언어로 폴백
- Language switching / 언어 전환

**API Example / API 예시**:
```python
i18n = I18n('translations.json', default_lang='ko')
text = i18n.t('cards.total_employees', lang='en')  # "Total Employees"
```

#### `src/utils/date_parser.py`
**Responsibilities / 책임**:
- Parse 12+ date formats including Korean month names / 한국 월 이름 포함 12가지 이상 날짜 형식 파싱
- Working days calculation / 근무일 계산
- Date range validation / 날짜 범위 검증

**Supported Formats / 지원 형식**:
- `2025-09-25`, `2025/09/25`, `25-Sep-2025`
- `2025년 9월 25일`, `2025년 9월`
- Excel serial dates / Excel 일련번호 날짜

#### `src/utils/logger.py`
**Responsibilities / 책임**:
- Bilingual logging (Korean + English) / 이중 언어 로깅 (한국어 + 영어)
- Structured log format / 구조화된 로그 형식
- File rotation (10MB, 5 backups) / 파일 로테이션 (10MB, 5개 백업)
- Multiple log levels / 다중 로그 레벨

### Integration Layer / 통합 계층

#### `src/integration/google_drive_sync.py`
**Responsibilities / 책임**:
- Google Drive file synchronization / Google Drive 파일 동기화
- Smart caching with MD5 checksum / MD5 체크섬을 이용한 스마트 캐싱
- Batch file operations / 배치 파일 작업
- Optional - system works offline / 선택 사항 - 시스템 오프라인 작동

**Key Methods / 주요 메서드**:
```python
sync.download_file(file_id, local_path)  # Download single file
sync.sync_folder(folder_id, local_dir)    # Sync entire folder
sync.list_files(query)                     # Search files
```

### Core Layer / 핵심 계층

#### `src/core/data_loader.py`
**Responsibilities / 책임**:
- Load data from multiple sources / 여러 소스에서 데이터 로드
- **NO FAKE DATA**: Return empty DataFrame if file missing / **가짜 데이터 없음**: 파일 누락 시 빈 DataFrame 반환
- Intelligent caching / 지능형 캐싱
- Data source abstraction / 데이터 소스 추상화

**Supported Sources / 지원 소스**:
- Basic manpower data / 기본 인력 데이터
- Attendance records / 출근 기록
- AQL (Acceptable Quality Limit) history / AQL 이력
- 5PRS (5-Point Rating System) / 5점 평가 시스템
- Team structure / 팀 구조

#### `src/core/data_validator.py`
**Responsibilities / 책임**:
- Schema validation / 스키마 검증
- Temporal logic validation / 시간 논리 검증
- Cross-dataset consistency / 데이터셋 간 일관성
- Business rule validation / 비즈니스 규칙 검증

**Validation Types / 검증 유형**:
1. **Schema**: Required columns, data types / 필수 컬럼, 데이터 타입
2. **Temporal**: Date sequences, future dates / 날짜 순서, 미래 날짜
3. **Business**: Attendance logic, team assignments / 출근 논리, 팀 배정
4. **Consistency**: Cross-dataset references / 데이터셋 간 참조

#### `src/core/error_detector.py`
**Responsibilities / 책임**:
- Categorized error detection (6 types) / 범주화된 오류 감지 (6가지 유형)
- Error severity classification / 오류 심각도 분류
- Dashboard error reporting / 대시보드 오류 보고

**Error Categories / 오류 범주**:
1. Temporal errors / 시간 오류
2. TYPE errors / TYPE 오류
3. Position errors / 직급 오류
4. Team errors / 팀 오류
5. Attendance errors / 출근 오류
6. Duplicate errors / 중복 오류

### Analytics Layer / 분석 계층

#### `src/analytics/metric_calculator.py`
**Responsibilities / 책임**:
- **Zero hardcoded formulas** - all from JSON / **하드코딩된 공식 없음** - 모두 JSON에서
- Subject/metric-agnostic calculation / 주제/메트릭 무관 계산
- Threshold evaluation / 임계값 평가
- Color assignment / 색상 할당

**Reusability Example / 재활용성 예시**:
```python
# Same function for any metric
# 모든 메트릭에 동일한 함수

calc = MetricCalculator('metric_definitions.json')

# Overall absence rate
result1 = calc.calculate_metric('absence_rate', data, subject='Overall')

# Team A attendance rate
result2 = calc.calculate_metric('attendance_rate', data, subject='Team A',
                                subject_filter={'team': 'Team A'})
```

#### `src/analytics/trend_analyzer.py`
**Responsibilities / 책임**:
- Generic trend analysis for ANY subject/metric / 모든 주제/메트릭에 대한 일반 트렌드 분석
- Time-series aggregation / 시계열 집계
- Trend direction detection / 트렌드 방향 감지
- Statistical summary / 통계 요약

**Reusability Principle / 재활용성 원칙**:
```python
analyzer = TrendAnalyzer()

# Works for ANY combination:
# 모든 조합에서 작동:
# - Overall + absence_rate
# - Team A + attendance_rate
# - Position X + resignation_rate
# - ANY subject + ANY metric

result = analyzer.analyze_trend(
    data=df,
    subject="Any Subject",  # 파라미터화됨
    metric="any_metric",    # 파라미터화됨
    time_column="month",
    value_column="metric_value",
    subject_filter={"column": "value"}  # Optional filtering
)
```

### Visualization Layer / 시각화 계층

#### `src/visualization/chart_generator.py`
**Responsibilities / 책임**:
- Template-based chart generation / 템플릿 기반 차트 생성
- Chart.js configuration / Chart.js 설정
- Reusable for any data / 모든 데이터에 재활용 가능
- Chart instance management / 차트 인스턴스 관리

**Template Usage / 템플릿 사용**:
```python
gen = ChartGenerator('chart_templates.json')

# Generate chart from template - works for ANY data
# 템플릿에서 차트 생성 - 모든 데이터에 작동

chart = gen.generate_chart(
    chart_data=ChartData(labels=['Jan', 'Feb'], datasets=[...]),
    template_name='line_trend',  # Reusable template
    title='Any Metric Trend'
)
```

#### `src/visualization/html_builder.py`
**Responsibilities / 책임**:
- Complete HTML dashboard generation / 완전한 HTML 대시보드 생성
- Single-file output (embedded CSS/JS) / 단일 파일 출력 (임베디드 CSS/JS)
- Responsive design / 반응형 디자인
- Multi-language UI / 다국어 UI

**Output Characteristics / 출력 특성**:
- ✅ Self-contained (no external dependencies) / 자체 포함 (외부 의존성 없음)
- ✅ Portable (works offline) / 이식 가능 (오프라인 작동)
- ✅ Bootstrap 5 + Chart.js v4 from CDN / CDN에서 Bootstrap 5 + Chart.js v4

### Orchestration Layer / 조율 계층

#### `src/generate_dashboard.py`
**Responsibilities / 책임**:
- Main orchestrator coordinating all modules / 모든 모듈을 조율하는 메인 오케스트레이터
- Pipeline execution / 파이프라인 실행
- Error handling / 오류 처리
- Output generation / 출력 생성

**Pipeline Steps / 파이프라인 단계**:
1. Load all data sources / 모든 데이터 소스 로드
2. Validate and detect errors / 검증 및 오류 감지
3. Calculate metrics (JSON-driven) / 메트릭 계산 (JSON 기반)
4. Analyze trends (reusable) / 트렌드 분석 (재활용 가능)
5. Generate charts (template-driven) / 차트 생성 (템플릿 기반)
6. Build HTML dashboard / HTML 대시보드 빌드
7. Save to file / 파일에 저장

#### `action.sh`
**Responsibilities / 책임**:
- Complete automation / 완전 자동화
- User-friendly CLI / 사용자 친화적 CLI
- Month/year/language selection / 월/년도/언어 선택
- Google Drive sync option / Google Drive 동기화 옵션
- Browser auto-open / 브라우저 자동 열기

**Features / 기능**:
- ✅ Interactive prompts / 대화형 프롬프트
- ✅ Input validation / 입력 검증
- ✅ Colored output / 색상 출력
- ✅ Error handling / 오류 처리
- ✅ Summary report / 요약 보고서

---

## Data Flow / 데이터 흐름

```
┌──────────────────────────────────────────────────────────────┐
│              START: action.sh Execution                       │
│              시작: action.sh 실행                              │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │   User Input Collection  │
        │   사용자 입력 수집        │
        │  - Month/Year            │
        │  - Language              │
        │  - Google Drive sync     │
        └────────────┬─────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │ Google Drive Sync      │
        │ (Optional)             │
        │ Google Drive 동기화    │
        └────────────┬─────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│              Data Loading Phase                             │
│              데이터 로딩 단계                                 │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Basic    │  │Attendance│  │   AQL    │  │  5PRS    │  │
│  │ Manpower │  │  출근     │  │  품질    │  │  평가    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ↓ DataLoader                                              │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │   Pandas DataFrames (or empty if not exists)     │     │
│  │   Pandas DataFrame (없으면 빈 상태)                │     │
│  │   NO FAKE DATA - 가짜 데이터 없음                  │     │
│  └──────────────────────────────────────────────────┘     │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│            Validation Phase                                 │
│            검증 단계                                         │
│                                                             │
│  DataValidator + ErrorDetector                             │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │ • Schema validation / 스키마 검증                 │     │
│  │ • Temporal logic / 시간 논리                      │     │
│  │ • 6 error categories / 6가지 오류 범주             │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ↓ Error Report / 오류 보고서                              │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│           Metric Calculation Phase                          │
│           메트릭 계산 단계                                    │
│                                                             │
│  MetricCalculator (JSON-driven)                            │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │  Load metric_definitions.json                    │     │
│  │  ↓                                                │     │
│  │  For each metric:                                │     │
│  │    - Execute formula / 공식 실행                  │     │
│  │    - Evaluate threshold / 임계값 평가             │     │
│  │    - Assign color / 색상 할당                     │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ↓ MetricValue objects / MetricValue 객체                  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│            Trend Analysis Phase                             │
│            트렌드 분석 단계                                   │
│                                                             │
│  TrendAnalyzer (Subject-agnostic)                          │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │  For each trend-enabled metric:                  │     │
│  │    - Aggregate by time period                    │     │
│  │    - Detect trend direction                      │     │
│  │    - Calculate statistics                        │     │
│  │  SAME FUNCTION for all subjects/metrics          │     │
│  │  모든 주제/메트릭에 동일한 함수                     │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ↓ TrendAnalysisResult objects                             │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│           Chart Generation Phase                            │
│           차트 생성 단계                                      │
│                                                             │
│  ChartGenerator (Template-driven)                          │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │  Load chart_templates.json                       │     │
│  │  ↓                                                │     │
│  │  For each metric/trend:                          │     │
│  │    - Select template / 템플릿 선택                │     │
│  │    - Generate Chart.js config / 설정 생성        │     │
│  │  REUSABLE templates for any data                 │     │
│  │  모든 데이터에 재활용 가능 템플릿                   │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ↓ ChartConfig objects / ChartConfig 객체                  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│            HTML Build Phase                                 │
│            HTML 빌드 단계                                    │
│                                                             │
│  HTMLBuilder                                               │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │  1. Build HTML structure / HTML 구조 빌드         │     │
│  │  2. Embed Bootstrap 5 CSS / Bootstrap 5 CSS 임베드│     │
│  │  3. Create summary cards / 요약 카드 생성          │     │
│  │  4. Embed charts with Chart.js / Chart.js 차트 임베드│   │
│  │  5. Add i18n support / 다국어 지원 추가            │     │
│  │  6. Single-file output / 단일 파일 출력            │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ↓ Complete HTML string / 완전한 HTML 문자열               │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │   Save to File         │
        │   파일에 저장           │
        │   output_files/         │
        │   HR_Dashboard_         │
        │   YYYY_MM.html         │
        └────────────┬─────────────┘
                     │
                     ↓
        ┌────────────────────────┐
        │   Open in Browser      │
        │   브라우저에서 열기     │
        │   (Optional)           │
        └────────────┬─────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────────────┐
│                 END: Dashboard Ready                          │
│                 종료: 대시보드 준비 완료                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Reusability Pattern / 재활용성 패턴

### Pattern 1: Subject/Object Agnostic Functions
### 패턴 1: 주제/객체 무관 함수

**Problem / 문제**: Writing separate functions for "overall absence rate", "Team A attendance", "unauthorized absence trend" leads to code duplication.
**문제**: "전체 결근율", "팀 A 출근율", "무단 결근 트렌드"에 대해 별도 함수를 작성하면 코드 중복이 발생합니다.

**Solution / 해결책**: Single function with subject/metric parameters.
**해결책**: 주제/메트릭 매개변수를 가진 단일 함수.

**Implementation / 구현**:
```python
def analyze_trend(
    data: pd.DataFrame,
    subject: str,           # "Overall", "Team A", "Position X"
    metric: str,            # "absence_rate", "attendance_rate"
    subject_filter: Optional[Dict] = None  # {"team": "Team A"}
) -> TrendAnalysisResult:
    """
    ONE FUNCTION - works for ANY subject/metric combination
    하나의 함수 - 모든 주제/메트릭 조합에서 작동
    """
    # Filter data if subject-specific
    if subject_filter:
        for key, value in subject_filter.items():
            data = data[data[key] == value]

    # Calculate trend (SAME LOGIC for all)
    # 트렌드 계산 (모든 경우에 동일한 로직)
    trend = calculate_trend_metrics(data, metric)

    return TrendAnalysisResult(
        subject=subject,
        metric=metric,
        trend_data=trend
    )
```

**Benefits / 이점**:
- ✅ Write once, use anywhere / 한 번 작성, 어디서나 사용
- ✅ Easy testing (single function) / 쉬운 테스트 (단일 함수)
- ✅ Maintainability / 유지보수성
- ✅ Extensibility (add new subjects via parameters) / 확장성 (매개변수로 새 주제 추가)

### Pattern 2: Configuration-Driven Business Logic
### 패턴 2: 설정 기반 비즈니스 로직

**Problem / 문제**: Hardcoded thresholds and formulas in code require developer changes.
**문제**: 코드에 하드코딩된 임계값과 공식은 개발자 변경이 필요합니다.

**Solution / 해결책**: Define all business logic in JSON configuration.
**해결책**: 모든 비즈니스 로직을 JSON 설정에 정의.

**Implementation / 구현**:
```json
// metric_definitions.json
{
  "absence_rate": {
    "formula": "100 - (SUM(actual) / SUM(total) * 100)",
    "thresholds": {
      "excellent": {"max": 3, "color": "#28a745"},
      "good": {"min": 3, "max": 5, "color": "#17a2b8"},
      "warning": {"min": 5, "max": 10, "color": "#ffc107"},
      "critical": {"min": 10, "color": "#dc3545"}
    }
  }
}
```

```python
# Python code (NO HARDCODING)
# Python 코드 (하드코딩 없음)
def calculate_metric(metric_id: str, data: pd.DataFrame):
    definition = load_from_json(metric_id)  # Load from JSON
    value = execute_formula(definition['formula'], data)
    threshold = evaluate_threshold(value, definition['thresholds'])
    return MetricValue(value, threshold.color)
```

**Benefits / 이점**:
- ✅ Non-developers can update thresholds / 비개발자도 임계값 업데이트 가능
- ✅ No code deployment needed / 코드 배포 불필요
- ✅ Version control for business rules / 비즈니스 규칙 버전 관리

### Pattern 3: Template-Based Generation
### 패턴 3: 템플릿 기반 생성

**Problem / 문제**: Each chart type requires custom code.
**문제**: 각 차트 유형에 커스텀 코드가 필요합니다.

**Solution / 해결책**: Define reusable chart templates.
**해결책**: 재활용 가능한 차트 템플릿 정의.

**Implementation / 구현**:
```json
// chart_templates.json
{
  "line_trend": {
    "type": "line",
    "applicable_to": ["ANY_METRIC"],
    "config": {
      "responsive": true,
      "plugins": {
        "legend": {"display": true}
      }
    }
  }
}
```

```python
# Use template for ANY data
# 모든 데이터에 템플릿 사용
def generate_chart(data, template_name):
    template = load_template(template_name)
    return apply_template(template, data)

# Works for:
# - Absence rate trend
# - Attendance trend
# - ANY metric trend
```

---

## Configuration System / 설정 시스템

### Configuration Hierarchy / 설정 계층

```
config/
├── dashboard_config.json       # Layout, styling / 레이아웃, 스타일링
├── metric_definitions.json     # Business logic / 비즈니스 로직
├── chart_templates.json        # Visualization / 시각화
└── translations.json           # UI text / UI 텍스트
```

### Adding New Metric (No Code Required)
### 새 메트릭 추가 (코드 불필요)

**Steps / 단계**:

1. **Edit `metric_definitions.json`**:
```json
{
  "new_metric_id": {
    "id": "new_metric_id",
    "formula": "YOUR_FORMULA_HERE",
    "data_sources": ["attendance"],
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

2. **Edit `translations.json`**:
```json
{
  "ko": {
    "metrics": {
      "new_metric_id": "새 메트릭 이름"
    }
  },
  "en": {
    "metrics": {
      "new_metric_id": "New Metric Name"
    }
  }
}
```

3. **Run dashboard generation**:
```bash
./action.sh
```

✅ **No Python code changes required!**
✅ **Python 코드 변경 불필요!**

---

## Error Handling / 에러 처리

### Error Detection Categories / 에러 감지 범주

1. **Temporal Errors / 시간 오류**
   - Future entrance dates / 미래 입사일
   - Invalid date sequences / 유효하지 않은 날짜 순서

2. **TYPE Errors / TYPE 오류**
   - Missing TYPE classification / TYPE 분류 누락
   - Invalid TYPE values / 유효하지 않은 TYPE 값

3. **Position Errors / 직급 오류**
   - Missing position information / 직급 정보 누락

4. **Team Errors / 팀 오류**
   - Missing team assignments / 팀 배정 누락
   - Unknown team references / 알 수 없는 팀 참조

5. **Attendance Errors / 출근 오류**
   - Actual > Total working days / 실제 > 총 근무일
   - Negative values / 음수 값

6. **Duplicate Errors / 중복 오류**
   - Duplicate employee numbers / 중복 직원 번호

### Error Severity Levels / 오류 심각도 수준

- **Critical / 심각**: Data corruption, blocking errors / 데이터 손상, 차단 오류
- **Warning / 경고**: Potential issues, data quality / 잠재적 문제, 데이터 품질
- **Info / 정보**: Informational messages / 정보성 메시지

---

## Summary / 요약

The HR Dashboard System achieves complete independence and maximum reusability through:

HR 대시보드 시스템은 다음을 통해 완전한 독립성과 최대 재활용성을 달성합니다:

1. **Configuration-Driven Architecture** / **설정 기반 아키텍처**
   - Zero hardcoded business logic / 하드코딩된 비즈니스 로직 없음
   - All rules in JSON files / 모든 규칙이 JSON 파일에

2. **Subject/Object Agnostic Design** / **주제/객체 무관 설계**
   - Same functions for ANY combination / 모든 조합에 동일한 함수
   - Parameterization over duplication / 중복보다 매개변수화

3. **NO FAKE DATA Policy** / **가짜 데이터 금지 정책**
   - Return empty if data missing / 데이터 누락 시 비어있음 반환
   - Never generate synthetic data / 합성 데이터 생성 금지

4. **Multi-Language Support** / **다국어 지원**
   - Complete translations (KO/EN/VI) / 완전한 번역 (한국어/영어/베트남어)
   - Bilingual code comments / 이중 언어 코드 주석

5. **Full Automation** / **완전 자동화**
   - One-click dashboard generation / 원클릭 대시보드 생성
   - User-friendly CLI / 사용자 친화적 CLI

This architecture enables non-developers to modify business rules and add new metrics without touching Python code, while maintaining high code quality and reusability.

이 아키텍처는 비개발자가 Python 코드를 건드리지 않고 비즈니스 규칙을 수정하고 새 메트릭을 추가할 수 있게 하며, 동시에 높은 코드 품질과 재활용성을 유지합니다.
