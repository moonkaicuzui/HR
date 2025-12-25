# Data Integrity Audit Report
## December 2025 Dashboard vs Source CSV Comparison

**Audit Date:** 2025-12-25
**Target Month:** December 2025
**Auditor:** Data Integrity Auditor (Agent #2)

---

## Executive Summary

**Critical Findings:**
1. ✅ **Total Employees Match:** 560 employees (Source CSV = Dashboard)
2. ✅ **Active Employees Match:** 416 active employees (Source CSV = Dashboard)
3. 🚨 **CRITICAL DISCREPANCY:** Resigned employee count - Source CSV shows **144 resigned** but dashboard only displays **5 resigned**
4. 🚨 **CRITICAL DISCREPANCY:** Unauthorized absence count - Source CSV shows **23 unique active employees** but dashboard shows **0**
5. ⚠️ **Minor Discrepancy:** Filter count shows "무단 26" (3 more than actual)

---

## Detailed Comparison Table

| Metric | Screenshot/Dashboard | Source CSV | Discrepancy | Status |
|--------|---------------------|------------|-------------|--------|
| **Total Employees (560 표시 인원)** | 560 | 560 | 0 | ✅ MATCH |
| **Active Employees (재직)** | 416 | 416 | 0 | ✅ MATCH |
| **Resigned Employees (퇴사)** | 5 | 144 | -139 | 🚨 **CRITICAL** |
| **Unique Employees with Absences** | 342 | 420 | -78 | ⚠️ Significant |
| **Unauthorized Absence Card** | 0 | 23 | -23 | 🚨 **CRITICAL** |
| **Unauthorized Filter Count** | 26 | 23 | +3 | ⚠️ Minor |
| **Total Absence Records** | N/A | 8,262 | N/A | - |
| **Active Employee Absence Records** | N/A | 8,217 | N/A | - |

---

## Root Cause Analysis

### 1. Resigned Employee Count Discrepancy (5 vs 144)

**Source Data Analysis:**
```
Total employees: 560
Active (Stop working Date is null or > 2025-12-31): 416
Resigned (Stop working Date is not null and <= 2025-12-31): 144
```

**Expected Behavior:**
- Dashboard should show: 416 재직 (active) / 144 퇴사 (resigned)

**Actual Behavior:**
- Dashboard shows: 416 재직 / 5 퇴사

**Probable Cause:**
The dashboard is likely filtering resigned employees differently, possibly:
1. Only showing employees who resigned **in December 2025** (resigned_this_month)
2. Filtering out employees who resigned before the target month

**Code Location:**
- `src/visualization/complete_dashboard_builder.py` lines 280-285
- Variable: `resigned_this_month`

---

### 2. Unauthorized Absence Count Discrepancy (0 vs 23)

**Source Data Analysis:**
```
Unauthorized absence patterns: 'AR1|AR2|Không phép|Vắng không phép'

Total unauthorized records (all employees): 72
Unique employees with unauthorized absences: 26

Active employees only:
Unauthorized records: 45
Unique active employees: 23
```

**Breakdown by Reason:**
- AR2 - ốm ngắn ngày, tai nạn ngoài giờ lv: 41 records
- AR1 - Vắng không phép: 15 records
- AR1 - Gửi thư: 15 records
- AR1 - Họp kỷ luật: 1 record

**Expected Behavior:**
- Dashboard card should show: **23명 무단결근자**
- Filter should show: **무단 23**

**Actual Behavior:**
- Dashboard card shows: **0명 무단결근자**
- Filter shows: **무단 26**

**Probable Causes:**
1. **Card Display Bug:** The unauthorized absence card calculation is returning 0 despite having data
2. **Filter Count Mismatch:** Filter is including 3 additional resigned employees (26 total vs 23 active)

**Code Location:**
- `src/visualization/complete_dashboard_builder.py` lines 250-259 (unauthorized pattern matching)
- Lines 4437-4460 (unauthorized status calculation)

---

### 3. Employees with Absences Discrepancy (342 vs 420)

**Source Data Analysis:**
```
Unique employees with absences in attendance data: 420
Active employees with absences: 416
```

**Expected Behavior:**
- Should show 416 active employees with absences (excluding resigned)

**Actual Behavior:**
- Shows 342 employees

**Probable Cause:**
- Dashboard may be filtering out certain absence types
- Or counting logic differs from source data

---

## Data Integrity Verification

### Source CSV Files Synced:
✅ `basic manpower data december.csv` - 560 rows, 106.2 KB
✅ `attendance data december_converted.csv` - 8,262 rows, 685.4 KB
✅ `5prs data december.csv` - 486.4 KB
✅ `AQL REPORT-DECEMBER.2025.csv` - 204.0 KB

### Data Quality:
- No TYPE column in basic manpower data (uses Stop working Date instead)
- All 560 employees have valid Employee No
- Attendance data has proper ID No matching
- Unauthorized absence patterns are correctly defined

---

## Calculation Logic Review

### Current Unauthorized Absence Logic (Code):
```python
# Line 256-259 in complete_dashboard_builder.py
unauthorized_pattern = 'AR1|AR2|Không phép|Vắng không phép'
unauthorized_absent_employees = set(
    attendance_df[attendance_df['Reason Description'].str.contains(
        unauthorized_pattern, na=False, case=False)]['ID No'].unique()
)
```

**This logic is CORRECT** - it matches the source data perfectly.

### Issue Location:
The bug appears to be in how the unauthorized count is **displayed** in the dashboard card, not in the data collection logic.

Specifically:
- Lines 4437-4460: `unauthorized_count` calculation
- Line 4440: `if emp.get('has_unauthorized_absence', False):`

**Hypothesis:** The `has_unauthorized_absence` flag is not being set correctly in the `employeeDetails` array.

---

## Recommendations

### Priority 1: Fix Resigned Employee Display
**Action:** Clarify business requirement
- Should dashboard show:
  - A) All resigned employees up to end of month (144)? ✅ Recommended
  - B) Only employees who resigned in target month (5)?

**If A:** Update display logic to show cumulative resigned count
**If B:** Update label to clarify "이번 달 퇴사" (resigned this month)

### Priority 2: Fix Unauthorized Absence Card
**Action:** Debug `has_unauthorized_absence` flag assignment
- Verify flag is set correctly in employee data preparation
- Check if `unauthorized_absent_employees` set is populated
- Trace data flow from line 257 to line 4440

**Expected Fix Location:**
- `src/visualization/complete_dashboard_builder.py` line 299
- Ensure `has_unauthorized_absence = employee_id in unauthorized_absent_employees` works correctly

### Priority 3: Reconcile Filter Count
**Action:** Verify filter logic
- Filter shows 26 (includes 3 resigned employees)
- Card should show 23 (active employees only)
- Decide if filter should exclude resigned employees

---

## Testing Checklist

After fixes:
- [ ] Verify resigned count matches source CSV (144 or 5 with clarified label)
- [ ] Verify unauthorized absence card shows 23 (not 0)
- [ ] Verify filter count matches card count (23)
- [ ] Verify absence count matches active employees with absences (416)
- [ ] Re-run full data integrity audit
- [ ] Compare all 11 KPI metrics against source calculations

---

## Audit Trail

**Data Sources:**
- Google Drive sync: 2025-12-25 14:11:57
- Folder: `2025_12`
- Files: 4 files successfully synced

**Analysis Method:**
1. Synced latest data from Google Drive
2. Analyzed source CSV files with Python pandas
3. Generated fresh dashboard (2025-12-25)
4. Compared embedded data vs source data
5. Identified calculation discrepancies

**Verification Scripts:**
- `sync_monthly_data.py --month 12 --year 2025`
- Custom pandas analysis scripts (embedded in audit)

---

## Sign-off

**Data Integrity Auditor (Agent #2)**
Date: 2025-12-25
Status: ⚠️ Critical discrepancies identified - requires immediate attention

**Next Steps:**
1. Review with Metric Logic Architect (Agent #1)
2. Fix calculation bugs in `complete_dashboard_builder.py`
3. Re-run 10-agent verification after fixes
4. Update AUDIT_SUMMARY.txt with resolution
