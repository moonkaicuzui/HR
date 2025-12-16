# Hardcoding Documentation / 하드코딩 문서화
# HR Dashboard System

## Purpose / 목적

This document catalogs all unavoidable hardcoded elements in the HR Dashboard System, explaining why they cannot be moved to configuration files and providing guidelines for future modifications.

이 문서는 HR 대시보드 시스템의 불가피한 하드코딩 요소를 분류하고, 왜 설정 파일로 이동할 수 없는지 설명하며 향후 수정을 위한 가이드라인을 제공합니다.

## Philosophy / 철학

**Principle**: "Minimize hardcoding, document unavoidable cases"
**원칙**: "하드코딩을 최소화하고, 불가피한 경우를 문서화한다"

- ✅ **Configurable**: Business rules, thresholds, formulas → JSON files
- ✅ **설정 가능**: 비즈니스 규칙, 임계값, 공식 → JSON 파일

- ❌ **Unavoidable Hardcoding**: Framework logic, data types, core algorithms
- ❌ **불가피한 하드코딩**: 프레임워크 로직, 데이터 타입, 핵심 알고리즘

---

## Category 1: Python Framework Requirements
## 범주 1: Python 프레임워크 요구사항

### 1.1 Data Types and Pandas DataFrame Operations
### 1.1 데이터 타입 및 Pandas DataFrame 연산

**Location / 위치**: `src/core/data_loader.py`, `src/analytics/metric_calculator.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/core/data_loader.py
def load_basic_manpower(self, month: int, year: int) -> pd.DataFrame:
    """Return type must be pd.DataFrame - cannot be configured"""
    try:
        df = pd.read_csv(file_path)  # read_csv is Pandas-specific
        return df
    except FileNotFoundError:
        return pd.DataFrame()  # Empty DataFrame - cannot be in JSON
```

**Why Hardcoded / 하드코딩 이유**:
- Pandas DataFrame is a **Python object type**, not a configuration value
- Pandas DataFrame은 설정 값이 아닌 **Python 객체 타입**
- Core data structure for data processing
- 데이터 처리를 위한 핵심 데이터 구조
- Alternative would require building custom data structure (not practical)
- 대안은 커스텀 데이터 구조 구축 필요 (비실용적)

**Modification Guidelines / 수정 가이드라인**:
- ✅ If changing data processing library: Update all DataFrame references
- ✅ 데이터 처리 라이브러리 변경 시: 모든 DataFrame 참조 업데이트
- ✅ If adding new data source: Follow same pattern (try/except, return empty DataFrame)
- ✅ 새 데이터 소스 추가 시: 동일한 패턴 따르기 (try/except, 빈 DataFrame 반환)

---

### 1.2 Date Parsing Logic
### 1.2 날짜 파싱 로직

**Location / 위치**: `src/utils/date_parser.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/utils/date_parser.py
KOREAN_MONTHS = {
    "1월": 1, "2월": 2, "3월": 3, "4월": 4,
    "5월": 5, "6월": 6, "7월": 7, "8월": 8,
    "9월": 9, "10월": 10, "11월": 11, "12월": 12
}

DATE_PATTERNS = [
    r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2025-09-25
    r'(\d{4})/(\d{1,2})/(\d{1,2})',  # 2025/09/25
    r'(\d{1,2})-([A-Za-z]{3})-(\d{4})',  # 25-Sep-2025
    # ... 12+ patterns
]
```

**Why Hardcoded / 하드코딩 이유**:
- **Language-specific constants** (Korean month names) are cultural knowledge
- **언어별 상수** (한국어 월 이름)는 문화적 지식
- Regex patterns are **parsing algorithms**, not business rules
- 정규 표현식 패턴은 비즈니스 규칙이 아닌 **파싱 알고리즘**
- Moving to JSON would make maintenance harder, not easier
- JSON으로 이동하면 유지보수가 더 어려워짐 (쉬워지지 않음)

**Configuration Alternative (if needed) / 설정 대안 (필요시)**:
```json
// config/date_formats.json (OPTIONAL - not recommended)
{
  "korean_months": {
    "1월": 1,
    "2월": 2
  },
  "patterns": [
    {"regex": "(\\d{4})-(\\d{1,2})-(\\d{1,2})", "format": "YYYY-MM-DD"}
  ]
}
```

**Current Recommendation / 현재 권장사항**: Keep hardcoded (better readability)
**현재 권장사항**: 하드코딩 유지 (가독성 향상)

**Modification Guidelines / 수정 가이드라인**:
- ✅ Adding new language: Add new LANGUAGE_MONTHS dictionary
- ✅ 새 언어 추가: 새 LANGUAGE_MONTHS 딕셔너리 추가
- ✅ Adding new date format: Append to DATE_PATTERNS list
- ✅ 새 날짜 형식 추가: DATE_PATTERNS 리스트에 추가

---

### 1.3 Logger Configuration
### 1.3 로거 설정

**Location / 위치**: `src/utils/logger.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/utils/logger.py
class HRLogger:
    def __init__(self, name: str, log_dir: Path = None):
        # Hardcoded log format
        # 하드코딩된 로그 형식
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Hardcoded rotation settings
        # 하드코딩된 로테이션 설정
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
```

**Why Hardcoded / 하드코딩 이유**:
- Log format is a **technical specification**, not a business rule
- 로그 형식은 비즈니스 규칙이 아닌 **기술 사양**
- Rotation settings are **system maintenance parameters**
- 로테이션 설정은 **시스템 유지보수 매개변수**
- Changing these requires understanding logging best practices
- 이러한 변경은 로깅 모범 사례 이해 필요

**Configuration Alternative (if needed) / 설정 대안 (필요시)**:
```json
// config/logging_config.json (OPTIONAL)
{
  "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  "date_format": "%Y-%m-%d %H:%M:%S",
  "rotation": {
    "max_bytes": 10485760,
    "backup_count": 5
  }
}
```

**Current Recommendation / 현재 권장사항**: Keep hardcoded (Python logging standard)
**현재 권장사항**: 하드코딩 유지 (Python 로깅 표준)

**Modification Guidelines / 수정 가이드라인**:
- ✅ Changing log format: Update formatter string
- ✅ 로그 형식 변경: formatter 문자열 업데이트
- ✅ Changing rotation: Update maxBytes/backupCount
- ✅ 로테이션 변경: maxBytes/backupCount 업데이트

---

## Category 2: Core Calculation Algorithms
## 범주 2: 핵심 계산 알고리즘

### 2.1 Formula Execution Engine
### 2.1 공식 실행 엔진

**Location / 위치**: `src/analytics/metric_calculator.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/analytics/metric_calculator.py
def _execute_calculation(self, data: pd.DataFrame, method: str, metric_def: dict):
    """
    Core calculation engine - MUST be hardcoded
    핵심 계산 엔진 - 반드시 하드코딩 필요
    """
    if method == 'percentage':
        # Percentage calculation logic (ALGORITHM)
        # 백분율 계산 로직 (알고리즘)
        numerator = data[metric_def['numerator_column']].sum()
        denominator = data[metric_def['denominator_column']].sum()
        if denominator == 0:
            return 0.0  # Avoid division by zero
        return (numerator / denominator) * 100

    elif method == 'sum':
        return data[metric_def['value_column']].sum()

    elif method == 'average':
        return data[metric_def['value_column']].mean()

    elif method == 'count':
        return len(data)
```

**Why Hardcoded / 하드코딩 이유**:
- These are **mathematical algorithms**, not business rules
- 이들은 비즈니스 규칙이 아닌 **수학적 알고리즘**
- The formula strings in JSON are **data**, this is the **interpreter**
- JSON의 공식 문자열은 **데이터**, 이것은 **해석기**
- Moving to configuration would require building a formula parser (complex, risky)
- 설정으로 이동하면 공식 파서 구축 필요 (복잡하고 위험)

**What IS Configurable / 설정 가능한 것**:
```json
// metric_definitions.json
{
  "absence_rate": {
    "calculation_method": "percentage",  // ← This is configurable
    "numerator_column": "absent_days",   // ← This is configurable
    "denominator_column": "total_days"   // ← This is configurable
  }
}
```

**Modification Guidelines / 수정 가이드라인**:
- ✅ Adding new calculation method: Add new elif branch
- ✅ 새 계산 방법 추가: 새 elif 분기 추가
- ✅ Example: Adding 'median' method
- ✅ 예시: 'median' 메서드 추가
  ```python
  elif method == 'median':
      return data[metric_def['value_column']].median()
  ```

---

### 2.2 Threshold Evaluation Logic
### 2.2 임계값 평가 로직

**Location / 위치**: `src/analytics/metric_calculator.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/analytics/metric_calculator.py
def _evaluate_threshold(self, value: float, thresholds: dict) -> tuple:
    """
    Threshold evaluation algorithm - comparison logic
    임계값 평가 알고리즘 - 비교 로직
    """
    for level in ['critical', 'warning', 'good', 'excellent']:
        threshold = thresholds.get(level, {})

        min_val = threshold.get('min', float('-inf'))
        max_val = threshold.get('max', float('inf'))

        # Comparison algorithm (HARDCODED)
        # 비교 알고리즘 (하드코딩)
        if min_val <= value < max_val:
            return level, threshold.get('color', '#000000')

    return 'unknown', '#808080'  # Default gray
```

**Why Hardcoded / 하드코딩 이유**:
- **Comparison logic** (<=, <) is an algorithm, not a business rule
- **비교 로직** (<=, <)은 비즈니스 규칙이 아닌 알고리즘
- The threshold **values** are in JSON (configurable)
- 임계값 **값**은 JSON에 있음 (설정 가능)
- The evaluation **method** is in code (algorithm)
- 평가 **방법**은 코드에 있음 (알고리즘)

**What IS Configurable / 설정 가능한 것**:
```json
// metric_definitions.json
{
  "thresholds": {
    "excellent": {"max": 3, "color": "#28a745"},   // ← Values configurable
    "good": {"min": 3, "max": 5, "color": "#17a2b8"},
    "warning": {"min": 5, "max": 10, "color": "#ffc107"},
    "critical": {"min": 10, "color": "#dc3545"}
  }
}
```

**Modification Guidelines / 수정 가이드라인**:
- ✅ Changing threshold values: Edit JSON file
- ✅ 임계값 변경: JSON 파일 편집
- ✅ Adding new threshold level: Add to JSON + update iteration order in code
- ✅ 새 임계값 레벨 추가: JSON에 추가 + 코드에서 반복 순서 업데이트

---

## Category 3: HTML/JavaScript Generation
## 범주 3: HTML/JavaScript 생성

### 3.1 Bootstrap 5 and Chart.js Integration
### 3.1 Bootstrap 5 및 Chart.js 통합

**Location / 위치**: `src/visualization/html_builder.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/visualization/html_builder.py
def _build_head(self, title: str) -> str:
    """Generate HTML head with CDN links"""
    return f"""
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>

        <!-- Bootstrap 5 CSS -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
              rel="stylesheet">

        <!-- Chart.js -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>

        <!-- Bootstrap 5 JS -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </head>
    """
```

**Why Hardcoded / 하드코딩 이유**:
- CDN URLs are **technical dependencies**, not business rules
- CDN URL은 비즈니스 규칙이 아닌 **기술 의존성**
- Version numbers must match API compatibility
- 버전 번호는 API 호환성과 일치해야 함
- Changing these requires testing entire dashboard
- 이들을 변경하면 전체 대시보드 테스트 필요

**Configuration Alternative (if needed) / 설정 대안 (필요시)**:
```json
// config/dashboard_config.json
{
  "cdn_dependencies": {
    "bootstrap_css": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
    "chartjs": "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"
  }
}
```

**Current Recommendation / 현재 권장사항**: Keep hardcoded (framework dependency)
**현재 권장사항**: 하드코딩 유지 (프레임워크 의존성)

**Modification Guidelines / 수정 가이드라인**:
- ✅ Upgrading Bootstrap: Update version in URL + test entire dashboard
- ✅ Bootstrap 업그레이드: URL 버전 업데이트 + 전체 대시보드 테스트
- ✅ Upgrading Chart.js: Update version + test all charts
- ✅ Chart.js 업그레이드: 버전 업데이트 + 모든 차트 테스트

---

### 3.2 JavaScript Chart Initialization
### 3.2 JavaScript 차트 초기화

**Location / 위치**: `src/visualization/html_builder.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/visualization/html_builder.py
def _build_scripts(self, charts: List, language: str) -> str:
    """Generate JavaScript for chart initialization"""
    scripts = """
    <script>
    // Chart.js instance management (ALGORITHM)
    // Chart.js 인스턴스 관리 (알고리즘)
    function initializeCharts() {
        // Destroy existing instances to prevent memory leaks
        // 메모리 누수 방지를 위해 기존 인스턴스 제거
        if (window.chartInstances) {
            window.chartInstances.forEach(chart => chart.destroy());
        }
        window.chartInstances = [];

        // Initialize new charts
        // 새 차트 초기화
        charts.forEach(config => {
            const ctx = document.getElementById(config.id).getContext('2d');
            const chart = new Chart(ctx, config);
            window.chartInstances.push(chart);
        });
    }

    // Initialize on page load
    // 페이지 로드 시 초기화
    document.addEventListener('DOMContentLoaded', initializeCharts);
    </script>
    """
    return scripts
```

**Why Hardcoded / 하드코딩 이유**:
- This is **JavaScript runtime logic**, not configuration data
- 이것은 설정 데이터가 아닌 **JavaScript 런타임 로직**
- Chart.js API calls are **framework-specific**
- Chart.js API 호출은 **프레임워크별**
- Memory management is an **algorithm** (destroy/create pattern)
- 메모리 관리는 **알고리즘** (제거/생성 패턴)

**Modification Guidelines / 수정 가이드라인**:
- ✅ Changing chart library: Rewrite entire initialization logic
- ✅ 차트 라이브러리 변경: 전체 초기화 로직 재작성
- ✅ Adding chart event handlers: Add to initialization function
- ✅ 차트 이벤트 핸들러 추가: 초기화 함수에 추가

---

### 3.3 Language Switching Function
### 3.3 언어 전환 함수

**Location / 위치**: `src/visualization/html_builder.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/visualization/html_builder.py
def _build_language_switcher(self) -> str:
    """JavaScript function for language switching"""
    return """
    <script>
    function changeLanguage(lang) {
        // Save preference to localStorage (BROWSER API)
        // localStorage에 선호도 저장 (브라우저 API)
        localStorage.setItem('dashboard_language', lang);

        // Update all translatable elements (DOM MANIPULATION)
        // 모든 번역 가능 요소 업데이트 (DOM 조작)
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = translations[lang][key];
            if (translation) {
                element.textContent = translation;
            }
        });

        // Re-render charts with new language (CHART.JS API)
        // 새 언어로 차트 재렌더링 (Chart.js API)
        initializeCharts(lang);
    }
    </script>
    """
```

**Why Hardcoded / 하드코딩 이유**:
- Uses **browser APIs** (localStorage, DOM manipulation)
- **브라우저 API** 사용 (localStorage, DOM 조작)
- Chart re-rendering is **framework-specific** (Chart.js)
- 차트 재렌더링은 **프레임워크별** (Chart.js)
- JavaScript function logic, not data
- JavaScript 함수 로직, 데이터 아님

**What IS Configurable / 설정 가능한 것**:
```json
// translations.json - The actual translation strings ARE configurable
// translations.json - 실제 번역 문자열은 설정 가능
{
  "ko": {"title": "HR 대시보드"},
  "en": {"title": "HR Dashboard"}
}
```

**Modification Guidelines / 수정 가이드라인**:
- ✅ Adding new translatable element: Add data-i18n attribute + translation in JSON
- ✅ 새 번역 가능 요소 추가: data-i18n 속성 추가 + JSON에 번역 추가
- ✅ Changing storage mechanism: Replace localStorage with alternative
- ✅ 저장 메커니즘 변경: localStorage를 대안으로 교체

---

## Category 4: File System Operations
## 범주 4: 파일 시스템 작업

### 4.1 File Path Construction
### 4.1 파일 경로 구성

**Location / 위치**: `src/core/data_loader.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/core/data_loader.py
def _get_file_path(self, month: int, year: int, file_type: str) -> Path:
    """
    Construct file path based on naming convention
    명명 규칙에 따라 파일 경로 구성
    """
    month_name_ko = self._get_month_name_ko(month)  # "9월"
    month_name_en = self._get_month_name_en(month)  # "september"

    # File naming convention (HARDCODED PATTERN)
    # 파일 명명 규칙 (하드코딩된 패턴)
    if file_type == 'basic_manpower':
        filename = f"basic manpower data {month_name_en}.csv"
    elif file_type == 'attendance':
        filename = f"attendance_data_{year}_{month:02d}.xlsx"
    elif file_type == 'aql':
        filename = f"AQL history/{month_name_ko}.csv"

    return self.input_dir / filename
```

**Why Hardcoded / 하드코딩 이유**:
- File naming is determined by **external data sources** (HR team's file naming)
- 파일 명명은 **외부 데이터 소스**에 의해 결정 (HR 팀의 파일 명명)
- Pattern matching is an **algorithm**, not a business rule
- 패턴 매칭은 비즈니스 규칙이 아닌 **알고리즘**
- If HR team changes naming convention, code must change anyway
- HR 팀이 명명 규칙을 변경하면 어쨌든 코드를 변경해야 함

**Configuration Alternative (if needed) / 설정 대안 (필요시)**:
```json
// config/file_patterns.json (OPTIONAL)
{
  "basic_manpower": "basic manpower data {month_en}.csv",
  "attendance": "attendance_data_{year}_{month:02d}.xlsx",
  "aql": "AQL history/{month_ko}.csv"
}
```

**Current Recommendation / 현재 권장사항**: Keep hardcoded (external dependency)
**현재 권장사항**: 하드코딩 유지 (외부 의존성)

**Modification Guidelines / 수정 가이드라인**:
- ✅ HR team changes file naming: Update pattern strings
- ✅ HR 팀이 파일 명명 변경: 패턴 문자열 업데이트
- ✅ Adding new file type: Add new elif branch with pattern
- ✅ 새 파일 유형 추가: 패턴이 있는 새 elif 분기 추가

---

## Category 5: Google Drive Integration
## 범주 5: Google Drive 통합

### 5.1 Google Drive API Authentication
### 5.1 Google Drive API 인증

**Location / 위치**: `src/integration/google_drive_sync.py`

**Hardcoded Elements / 하드코딩 요소**:
```python
# File: src/integration/google_drive_sync.py
def _authenticate(self):
    """
    Google Drive API authentication
    Google Drive API 인증
    """
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.file'
    ]  # OAuth2 scopes (GOOGLE API REQUIREMENT)

    credentials = service_account.Credentials.from_service_account_file(
        self.credentials_path,
        scopes=SCOPES
    )

    self.service = build('drive', 'v3', credentials=credentials)
```

**Why Hardcoded / 하드코딩 이유**:
- OAuth2 scopes are defined by **Google Drive API specification**
- OAuth2 범위는 **Google Drive API 사양**에 의해 정의
- Not business rules, but **external API requirements**
- 비즈니스 규칙이 아닌 **외부 API 요구사항**
- Changing these would break authentication
- 이들을 변경하면 인증이 중단됨

**Modification Guidelines / 수정 가이드라인**:
- ✅ Changing to user OAuth (not service account): Replace authentication logic
- ✅ 사용자 OAuth로 변경 (서비스 계정 아님): 인증 로직 교체
- ✅ Upgrading Drive API version: Update 'v3' to new version
- ✅ Drive API 버전 업그레이드: 'v3'를 새 버전으로 업데이트

---

## Summary: What to Configure vs. What to Hardcode
## 요약: 설정할 것 vs. 하드코딩할 것

### ✅ SHOULD BE IN CONFIGURATION (JSON)
### ✅ 설정에 있어야 함 (JSON)

| Element / 요소 | Location / 위치 | Reason / 이유 |
|----------------|-----------------|---------------|
| Metric formulas / 메트릭 공식 | `metric_definitions.json` | Business rules / 비즈니스 규칙 |
| Threshold values / 임계값 | `metric_definitions.json` | Business rules / 비즈니스 규칙 |
| Chart templates / 차트 템플릿 | `chart_templates.json` | Visualization preferences / 시각화 선호도 |
| UI translations / UI 번역 | `translations.json` | Language content / 언어 콘텐츠 |
| Colors / 색상 | `dashboard_config.json` | Styling / 스타일링 |
| Layout settings / 레이아웃 설정 | `dashboard_config.json` | UI preferences / UI 선호도 |

### ❌ MUST REMAIN HARDCODED (Python/JavaScript)
### ❌ 하드코딩 유지 필요 (Python/JavaScript)

| Element / 요소 | Location / 위치 | Reason / 이유 |
|----------------|-----------------|---------------|
| Data types / 데이터 타입 | All `.py` files | Python language requirement / Python 언어 요구사항 |
| Calculation algorithms / 계산 알고리즘 | `metric_calculator.py` | Mathematical logic / 수학적 로직 |
| Date parsing patterns / 날짜 파싱 패턴 | `date_parser.py` | Parsing algorithm / 파싱 알고리즘 |
| Chart.js API calls / Chart.js API 호출 | `html_builder.py` | Framework-specific / 프레임워크별 |
| DOM manipulation / DOM 조작 | `html_builder.py` | Browser API / 브라우저 API |
| Google Drive scopes / Google Drive 범위 | `google_drive_sync.py` | External API requirement / 외부 API 요구사항 |
| File I/O operations / 파일 I/O 작업 | `data_loader.py` | System operations / 시스템 작업 |

---

## Decision Tree: Should I Configure or Hardcode?
## 의사결정 트리: 설정해야 하나 하드코딩해야 하나?

```
┌─────────────────────────────────┐
│  New element to add              │
│  추가할 새 요소                    │
└────────────┬────────────────────┘
             │
             ↓
    ┌────────────────────┐
    │ Is it a business   │ YES → ┌──────────────────────┐
    │ rule or threshold? │       │ Put in JSON config   │
    │ 비즈니스 규칙 또는  │       │ JSON 설정에 넣기      │
    │ 임계값인가?         │       └──────────────────────┘
    └────────┬───────────┘
             │ NO
             ↓
    ┌────────────────────┐
    │ Is it UI text or   │ YES → ┌──────────────────────┐
    │ translation?       │       │ Put in translations  │
    │ UI 텍스트 또는     │       │ translations.json에  │
    │ 번역인가?          │       │ 넣기                 │
    └────────┬───────────┘       └──────────────────────┘
             │ NO
             ↓
    ┌────────────────────┐
    │ Is it a chart      │ YES → ┌──────────────────────┐
    │ template?          │       │ Put in chart         │
    │ 차트 템플릿인가?   │       │ templates            │
    └────────┬───────────┘       │ chart_templates.json │
             │ NO                 └──────────────────────┘
             ↓
    ┌────────────────────┐
    │ Is it an algorithm │ YES → ┌──────────────────────┐
    │ or framework code? │       │ HARDCODE in Python   │
    │ 알고리즘 또는      │       │ Python에 하드코딩     │
    │ 프레임워크 코드?   │       └──────────────────────┘
    └────────┬───────────┘
             │ NO
             ↓
    ┌────────────────────┐
    │ Is it an external  │ YES → ┌──────────────────────┐
    │ API requirement?   │       │ HARDCODE (document   │
    │ 외부 API 요구사항? │       │ here)                │
    └────────┬───────────┘       │ 하드코딩 (여기 문서화)│
             │ NO                 └──────────────────────┘
             ↓
    ┌────────────────────┐
    │ Consult team &     │
    │ document decision  │
    │ 팀 협의 및         │
    │ 결정 문서화        │
    └────────────────────┘
```

---

## Maintenance Guidelines / 유지보수 가이드라인

### When to Update This Document / 이 문서를 업데이트할 때

1. **Adding new hardcoded element** / **새 하드코딩 요소 추가**
   - Document why it must be hardcoded / 왜 하드코딩이 필요한지 문서화
   - Provide modification guidelines / 수정 가이드라인 제공
   - Consider configuration alternative / 설정 대안 고려

2. **Moving from hardcode to config** / **하드코딩에서 설정으로 이동**
   - Remove from this document / 이 문서에서 제거
   - Update ARCHITECTURE.md / ARCHITECTURE.md 업데이트
   - Add migration notes / 마이그레이션 노트 추가

3. **Framework/library upgrade** / **프레임워크/라이브러리 업그레이드**
   - Update version numbers in hardcoded sections / 하드코딩 섹션의 버전 번호 업데이트
   - Test all affected functionality / 영향받는 모든 기능 테스트
   - Document breaking changes / 호환성 문제 문서화

### Code Review Checklist / 코드 리뷰 체크리스트

When reviewing code changes / 코드 변경 검토 시:

- [ ] Is new hardcoding justified? / 새 하드코딩이 정당한가?
- [ ] Could it be moved to configuration? / 설정으로 이동할 수 있는가?
- [ ] Is it documented in this file? / 이 파일에 문서화되었는가?
- [ ] Are modification guidelines provided? / 수정 가이드라인이 제공되는가?

---

## Contact / 연락처

**Questions about hardcoding decisions?**
**하드코딩 결정에 대한 질문이 있으신가요?**

1. Check this document first / 먼저 이 문서 확인
2. Review ARCHITECTURE.md for design patterns / 설계 패턴은 ARCHITECTURE.md 검토
3. Consult development team / 개발 팀 협의

**Last Updated**: 2025-10-05
**최종 업데이트**: 2025-10-05
