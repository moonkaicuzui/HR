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

## Common Pitfalls

1. **Don't hardcode business logic** - Use JSON configuration
2. **Don't create duplicate functions** - Parameterize existing ones
3. **Don't generate fake data** - Return empty results instead
4. **Don't forget bilingual comments** - All comments need Korean + English
5. **Don't skip validation** - Run tests after changes

## Dependencies

Core:
- Python 3.8+
- pandas >= 1.3.0
- numpy >= 1.21.0
- openpyxl >= 3.0.9

Optional (Google Drive):
- google-auth >= 2.16.0
- google-api-python-client >= 2.80.0
