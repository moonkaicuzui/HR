# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An HR Dashboard System with a **configuration-driven architecture** that generates self-contained HTML dashboards from HR data. The system enforces a strict **NO FAKE DATA** policy - it returns empty results rather than generating synthetic data when source data is missing.

**Core Philosophy**: Business logic lives in JSON configuration files, not in Python code. The same functions work for ANY subject/metric combination through parameterization.

## Quick Commands

### Generate Dashboard
```bash
# Interactive (recommended)
./action.sh

# Direct Python execution
python src/generate_dashboard.py --month 9 --year 2025 --language ko

# Available languages: ko (Korean), en (English), vi (Vietnamese)
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Sync Data from Google Drive (Optional)
```bash
python sync_monthly_data.py --month 9 --year 2025
```

### Validation
```bash
# Comprehensive tests
python test_dashboard_comprehensive.py

# Metrics validation
python validate_dashboard_metrics.py
```

## Architecture Principles

### 1. Configuration Over Code
All business rules are defined in JSON files under `config/`:
- `metric_definitions.json` - Metric formulas, thresholds, display formats
- `chart_templates.json` - Reusable chart configurations
- `translations.json` - Multi-language UI text
- `dashboard_config.json` - Layout and styling
- `drive_config.json` - Google Drive integration settings

**Critical**: When adding new metrics or modifying thresholds, edit JSON files ONLY. Never hardcode business logic in Python.

### 2. Subject/Metric Agnostic Design
Functions are parameterized to work with ANY combination:
```python
# ONE function works for all scenarios
trend_analyzer.analyze_trend(
    subject="Overall",  # or "Team A", "Position X", etc.
    metric="absence_rate",  # or ANY metric from config
    subject_filter={"team": "Team A"}  # optional filtering
)
```

This eliminates code duplication - the same `analyze_trend()` function handles overall absence rate, team-specific attendance, unauthorized absence trends, etc.

### 3. NO FAKE DATA Policy
```python
# CORRECT - Return empty DataFrame if file missing
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    return pd.DataFrame()  # Empty, not synthetic

# NEVER generate random/estimated/placeholder data
```

The dashboard will display "0" or "데이터 없음" rather than fake data.

### 4. Layered Architecture
```
Presentation (action.sh, HTML output)
    ↓
Visualization (complete_dashboard_builder.py, chart_generator.py)
    ↓
Analytics (metric_calculator.py, trend_analyzer.py)
    ↓
Core (data_loader.py, data_validator.py, error_detector.py)
    ↓
Integration (google_drive_sync.py)
    ↓
Utilities (i18n.py, date_parser.py, logger.py)
    ↓
Configuration (JSON files)
```

## Key Modules

### complete_dashboard_builder.py
Main orchestrator that coordinates all layers. Generates self-contained HTML with:
- 3-tab interface (Overview, Trends, Employee Details)
- 11 KPI cards with interactive modals
- Multi-month trend charts
- Employee data table with filter/search/sort
- Runtime language switching (KO/EN/VI)

### metric_calculator.py
JSON-driven metric calculation engine. Loads formulas from `metric_definitions.json` and executes them without hardcoded logic. Returns `MetricValue` objects with calculated value, threshold evaluation, and color assignment.

### data_loader.py
Multi-source data loading with intelligent caching. Implements the NO FAKE DATA policy - returns empty DataFrame for missing files. Sources include:
- Basic manpower data
- Attendance records
- AQL history
- 5PRS data
- Team structure

### data_validator.py & error_detector.py
6-category error detection system:
1. Temporal errors (future dates, invalid sequences)
2. TYPE errors (missing/invalid classifications)
3. Position errors (missing job titles)
4. Team errors (unknown team references)
5. Attendance errors (actual > total days, negative values)
6. Duplicate errors (duplicate employee numbers)

## Development Patterns

### Adding New Metrics (No Code Changes)
1. Edit `config/metric_definitions.json`:
```json
{
  "new_metric": {
    "id": "new_metric",
    "formula": "YOUR_FORMULA",
    "data_sources": ["attendance"],
    "thresholds": {
      "excellent": {"max": 5, "color": "#28a745"}
    }
  }
}
```

2. Edit `config/translations.json`:
```json
{
  "ko": {"metrics": {"new_metric": "새 메트릭"}},
  "en": {"metrics": {"new_metric": "New Metric"}},
  "vi": {"metrics": {"new_metric": "Chỉ số mới"}}
}
```

3. Run `./action.sh` - no Python changes needed!

### Bilingual Code Comments
All code comments must be in both Korean and English:
```python
def calculate_metric(self, data: pd.DataFrame):
    """
    Calculate metric value from data
    데이터로부터 메트릭 값 계산

    This function is reusable for any metric definition
    이 함수는 모든 메트릭 정의에 재활용 가능합니다
    """
```

### Data File Naming Conventions
```
input_files/
├── basic manpower data {month}.csv
├── attendance/converted/attendance data {month}_converted.csv
├── AQL history/1.HSRG AQL REPORT-{MONTH}.{year}.csv
├── 5prs data {month}.csv
└── {year}년 {month} 인센티브 지급 세부 정보.csv
```

Month format: "2025_09" or "Sep 2025" or "9월"

## Output

Single HTML file saved to:
```
output_files/HR_Dashboard_Complete_{YEAR}_{MM}.html
```

The file is self-contained with:
- Embedded Bootstrap 5 CSS
- Embedded Chart.js v4 JavaScript
- All data embedded as JSON
- No external dependencies
- Works offline

## Important Context

### Why Configuration-Driven?
Non-developers (HR managers, analysts) can modify thresholds and add metrics by editing JSON files. No code deployment required.

### Why Subject/Metric Agnostic?
Previously, each combination (overall absence, team attendance, position turnover) required separate functions. Now ONE function with parameters handles all cases.

### Google Drive Integration
Optional - system works completely offline. If enabled:
- Uses service account credentials from `credentials/service-account-key.json`
- Smart caching with MD5 checksums
- Batch file operations
- Graceful fallback to local files if sync fails

### Multi-Language Support
Dashboard includes all three languages (Korean, English, Vietnamese) with runtime switching via dropdown selector. No need to regenerate for different languages.

### Date Parsing
Supports 12+ date formats including:
- ISO: `2025-09-25`
- Korean: `2025년 9월 25일`
- Excel serial numbers
- Various slash/dash formats

See `src/utils/date_parser.py` for full list.

## Testing & Validation

The codebase includes comprehensive validation:
- **66 comprehensive tests** covering all layers
- **11 metric validations** against source data
- Automated via `test_dashboard_comprehensive.py` and `validate_dashboard_metrics.py`

When modifying core logic, run both test suites before committing.

## Important Files

- `ARCHITECTURE.md` - Detailed technical architecture (45KB)
- `HARDCODING_DOCUMENTATION.md` - Catalog of unavoidable hardcoded elements
- `README.md` - User-facing documentation with bilingual instructions
- `action.sh` - Main automation script with interactive CLI

## Multi-Agent Verification Framework (10-Agent Principle)
## 다중 에이전트 검증 프레임워크 (10 에이전트 원칙)

All significant changes to this project MUST be validated through a 10-agent verification framework.
이 프로젝트의 모든 중요한 변경사항은 10개 에이전트 검증 프레임워크를 통해 검증되어야 합니다.

### Tier 1: Core Technical Verification (50% weight)
### 티어 1: 핵심 기술 검증 (가중치 50%)

| Agent | Role | Focus Area |
|-------|------|------------|
| **1. Metric Logic Architect** | 메트릭 로직 설계자 | Validate metric formulas, threshold logic, calculation accuracy |
| **2. Data Integrity Auditor** | 데이터 무결성 감사자 | Compare source CSV vs dashboard embedded values, flag logic verification |
| **3. Logic Consistency Validator** | 로직 일관성 검증자 | Cross-check calculations between modules, ensure config-code alignment |

**Validation Criteria / 검증 기준:**
- All 11 metrics must match source data 100%
- Flag setting logic must align with MetricCalculator
- No hardcoded business logic in Python code

### Tier 2: User Effectiveness Simulation (35% weight)
### 티어 2: 사용자 효과성 시뮬레이션 (가중치 35%)

| Agent | Role | Persona Focus |
|-------|------|---------------|
| **4. Division Director Simulator** | 사업부장 시뮬레이터 | Strategic KPI overview, team comparison, trend analysis |
| **5. Team Leader Simulator** | 팀장 시뮬레이터 | Team-specific metrics, individual employee tracking, action items |
| **6. HR Strategist** | HR 전략가 | Policy implications, compliance, retention analysis |
| **7. Executive Simulator** | 경영진 시뮬레이터 | High-level summary, critical alerts, decision support |

**Validation Criteria / 검증 기준:**
- Each persona can complete their top 3 use cases
- Information hierarchy matches user priority
- Actionable insights are clearly highlighted

### Tier 3: Quality Assurance (15% weight)
### 티어 3: 품질 보증 (가중치 15%)

| Agent | Role | Review Focus |
|-------|------|--------------|
| **8. Technical Reviewer** | 기술 검토자 | Code quality, performance, maintainability |
| **9. Security Reviewer** | 보안 검토자 | XSS prevention, data exposure, input validation |
| **10. UX Reviewer** | UX 검토자 | Accessibility (WCAG 2.1 AA), responsiveness, usability |

**Validation Criteria / 검증 기준:**
- No security vulnerabilities (OWASP Top 10)
- WCAG 2.1 AA compliance
- Sub-3s load time on standard connections

### Tier 4: Specialized Testing (Optional)
### 티어 4: 전문 테스팅 (선택적)

| Agent | Role | Test Focus |
|-------|------|------------|
| **11. Functional Testing Agent** | 기능 테스트 에이전트 | Filter logic, search, pagination, export, data integrity |
| **12. Employee Details UX Specialist** | 직원 상세 UX 전문가 | Table UX, column layout, filter UX, mobile responsiveness |

**Validation Criteria / 검증 기준:**
- All 10 filters work correctly with accurate counts
- Search covers all fields with Korean/Vietnamese character support
- Pagination and sorting work correctly
- Export functions produce valid CSV/JSON output
- Mobile responsiveness at 320px, 768px, 1024px breakpoints

### When to Invoke Multi-Agent Verification
### 다중 에이전트 검증 호출 시점

**Required (필수):**
- New metric addition or modification
- Dashboard generation logic changes
- Data processing pipeline updates
- Major UI/UX changes

**Recommended (권장):**
- Bug fixes affecting calculations
- Performance optimizations
- Configuration file changes

### ⚡ Automatic Agent Verification Principle (AUTO-VERIFY)
### ⚡ 자동 에이전트 검증 원칙 (자동 검증)

**IMPORTANT**: All user requests to this project should be automatically validated by relevant agents.
**중요**: 이 프로젝트에 대한 모든 사용자 요청은 관련 에이전트에 의해 자동으로 검증되어야 합니다.

**Auto-Verification Rules / 자동 검증 규칙:**

| Request Type | Auto-Activated Agents | Verification Level |
|--------------|----------------------|-------------------|
| Code changes to `complete_dashboard_builder.py` | Agent #1, #2, #3 | Full Tier 1 |
| Metric formula changes | Agent #1, #2 | Data Integrity |
| UI/UX modifications | Agent #8, #10, #12 | Tech + UX + Details |
| Any dashboard regeneration | Agent #2 | Data Integrity Audit |
| Bug fixes | Agent #3, #8 | Logic + Tech |
| Performance changes | Agent #8 | Technical Review |
| Security-related changes | Agent #9 | Security Review |
| Employee Details tab changes | Agent #10, #11, #12 | Full Tier 4 |
| Filter/Search functionality | Agent #11 | Functional Testing |
| Table/Export features | Agent #11, #12 | Functional + UX |

**Auto-Verification Workflow / 자동 검증 워크플로우:**
```
1. User Request → Analyze request type
2. Auto-select relevant agents based on request type
3. Execute verification in background
4. Report discrepancies immediately
5. Block deployment if Tier 1 fails
```

**Quick Agent Reference / 에이전트 빠른 참조:**
- **#1 Metric Logic**: Formula validation
- **#2 Data Integrity**: Source vs Dashboard comparison
- **#3 Logic Consistency**: Cross-module verification
- **#4-7 User Personas**: Effectiveness testing
- **#8 Technical**: Code quality
- **#9 Security**: Vulnerability check
- **#10 UX**: Accessibility
- **#11 Functional Testing**: Filter, search, pagination, export testing
- **#12 Employee Details UX**: Table UX, column layout, mobile responsiveness

### Verification Command
### 검증 명령어

```bash
# Request multi-agent verification
# 다중 에이전트 검증 요청
"10개 에이전트로 검증해줘" or "Run 10-agent verification"
```

### Passing Criteria
### 통과 기준

| Tier | Minimum Score | Pass Condition |
|------|---------------|----------------|
| Tier 1 | 90/100 | All metrics 100% accurate |
| Tier 2 | 75/100 | All personas can complete core tasks |
| Tier 3 | 80/100 | No P0/P1 issues |
| **Overall** | **80/100** | **Weighted average meets threshold** |

### Audit Trail
### 감사 추적

All verification results should be documented in:
모든 검증 결과는 다음에 기록됩니다:
- `AUDIT_SUMMARY.txt` - Executive summary
- `DATA_INTEGRITY_AUDIT_REPORT.md` - Detailed findings
- `COMPARISON_TABLE.txt` - Metric-by-metric comparison

## Common Pitfalls

1. **Don't hardcode business logic** - Use JSON configuration
2. **Don't create duplicate functions** - Parameterize existing ones
3. **Don't generate fake data** - Return empty results instead
4. **Don't forget bilingual comments** - All comments need Korean + English
5. **Don't skip validation** - Run tests after changes
6. **Don't skip multi-agent verification** - Run 10-agent check for significant changes

## Dependencies

Core:
- Python 3.8+
- pandas >= 1.3.0
- numpy >= 1.21.0
- openpyxl >= 3.0.9

Optional (Google Drive):
- google-auth >= 2.16.0
- google-api-python-client >= 2.80.0
