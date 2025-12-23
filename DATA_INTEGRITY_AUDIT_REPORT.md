# 데이터 정합성 검증 보고서 (Data Integrity Audit Report)

**감사 날짜 (Audit Date):** 2025-12-22
**대상 월 (Target Month):** 2025-12
**감사관 (Auditor):** Data Integrity Auditor Agent #2
**대시보드 (Dashboard):** docs/HR_Dashboard_Complete_2025_12.html

---

## 1. 검증 요약 (Verification Summary)

| 구분 (Category) | 검증 항목 수 (Items) | 일치 (Match) | 불일치 (Mismatch) | 일치율 (Accuracy) |
|----------------|-------------------|-------------|------------------|------------------|
| **전체 메트릭** | 11 | 1 | 10 | **9.1%** |

### 🚨 결론 (Conclusion)

**❌ 불일치 발견 - 수정 필요 (DISCREPANCIES FOUND - CORRECTIONS REQUIRED)**

원본 CSV 데이터로부터 계산한 값과 대시보드 HTML에 임베디드된 값 사이에 **10개의 유의미한 불일치**가 발견되었습니다.

---

## 2. 12월 검증 상세 (December Verification Details)

### 일치 항목 (Matching Items)

| 항목 (Metric) | 원본 계산값 (Source) | 대시보드값 (Dashboard) | 차이 (Diff) | 상태 (Status) |
|--------------|-------------------|-------------------|------------|-------------|
| **총 인원수 (Total Employees)** | 411 | 411 | 0 | ✅ 일치 |

### 불일치 항목 (Mismatching Items)

| 항목 (Metric) | 원본 계산값 (Source) | 대시보드값 (Dashboard) | 차이 (Diff) | 불일치율 |
|--------------|-------------------|-------------------|------------|---------|
| **결근율 (Absence Rate)** | 12.3% | 10.9% | +1.4%p | 11.4% |
| **무단결근율 (Unauthorized Absence)** | 0.69% | 2.68% | -1.99%p | 288% |
| **퇴사율 (Resignation Rate)** | 1.0% | 1.9% | -0.9%p | 90% |
| **신규 입사자 (Recent Hires)** | 11 | 12 | -1 | 9.1% |
| **퇴사자 (Recent Resignations)** | 4 | 8 | -4 | 100% |
| **만근자 (Perfect Attendance)** | 99 | 239 | -140 | 141% |
| **장기근속자 (Long-term Employees)** | 288 | 349 | -61 | 21.2% |
| **60일 미만 (Under 60 Days)** | 18 | 19 | -1 | 5.6% |
| **배치 후 퇴사 (Post-Assignment Resignations)** | 2 | 0 | +2 | 100% |
| **데이터 오류 (Data Errors)** | 0 | 24 | -24 | N/A |

---

## 3. 불일치 원인 분석 (Root Cause Analysis)

### 3.1 계산 로직 차이 (Calculation Logic Differences)

#### **만근자 (Perfect Attendance): 99 vs 239**
- **원본 로직:** 출근 데이터에서 결근 기록이 하나도 없는 직원
- **대시보드 로직:** 미상 (가능성: 월별 전체 근무일 충족 기준)
- **권장 조치:** 만근자 정의 통일 필요

#### **무단결근율 (Unauthorized Absence): 0.69% vs 2.68%**
- **원본 로직:** AR1/AR2 사유 / 전체 출근 기록
- **대시보드 로직:** 직원당 무단결근 플래그 비율로 추정
- **차이:** 계산 분모가 다름 (기록 수 vs 직원 수)

#### **퇴사자 (Recent Resignations): 4 vs 8**
- **원본 로직:** `stop_date`가 2025-12인 직원 수
- **대시보드 로직:** `resigned_this_month` 플래그 = true인 직원 수
- **차이:** 플래그 설정 로직 불일치 또는 데이터 처리 시점 차이

### 3.2 데이터 필터링 차이 (Data Filtering Differences)

#### **장기근속자 (Long-term Employees): 288 vs 349**
- **원본 로직:** 재직 기간 ≥ 365일 (2025-12-31 기준)
- **대시보드 로직:** `long_term` 플래그 = true
- **가능 원인:**
  1. 재직 기간 계산 기준일 차이
  2. 휴직/복직 기간 포함 여부 차이
  3. 입사일 파싱 방식 차이

### 3.3 데이터 소스 불일치 (Data Source Misalignment)

#### **데이터 오류 (Data Errors): 0 vs 24**
- **원본 로직:** 6가지 카테고리 오류 검출 (temporal, TYPE, position, team, attendance, duplicate)
- **대시보드 로직:** `has_data_error` 플래그 = true
- **차이:** 24명의 직원에게 오류 플래그가 설정되어 있으나 원본 검증에서는 감지 안됨
- **권장 조치:** error_type, error_description 필드 확인 필요

---

## 4. Edge Case 검증 (Edge Case Verification)

| 케이스 (Case) | 발생 위치 (Location) | 현재 처리 (Current) | 권장 처리 (Recommended) | 상태 (Status) |
|-------------|------------------|------------------|----------------------|-------------|
| **분모 = 0** | 전체 메트릭 | try-except 처리 | 0으로 반환 | ✅ 정상 |
| **NULL 날짜** | entrance_date, stop_date | 빈 문자열 처리 | datetime 파싱 예외 처리 | ✅ 정상 |
| **미래 날짜** | 일부 직원 | 플래그 설정 | 오류로 표시 | ⚠️ 24건 발견 |
| **반올림 일관성** | 비율 메트릭 | 소수점 1-2자리 | 통일 필요 | ⚠️ 개선 권장 |
| **중복 employee_no** | 원본 데이터 | 미검출 | 중복 체크 강화 | ✅ 정상 |
| **플래그 불일치** | 여러 메트릭 | 런타임 계산 | 전처리 통일 | ❌ **수정 필요** |

---

## 5. 전월 비교 검증 (Month-over-Month Comparison)

※ 11월 데이터와의 비교는 대시보드의 "변화량" 표시를 검증하기 위한 것이나, 현재 감사에서는 12월 단독 검증에 집중하였습니다.

추가 검증이 필요한 경우 다음 명령어로 11월 데이터 검증 가능:
```bash
python validate_dashboard_metrics.py --month 11 --year 2025
```

---

## 6. 상세 분석 (Detailed Analysis)

### 6.1 원본 데이터 기준 (Source Data - Ground Truth)

**데이터 파일:**
- 인력: `input_files/basic manpower data december.csv` (554 records)
- 출근: `input_files/attendance/converted/attendance data december_converted.csv` (6,549 records)

**계산 방법:**
- `MetricCalculator` 클래스 사용
- `metric_definitions.json` 공식 적용
- 보고 날짜: 2025-12-31 (월말 기준)
- 재직자 정의: `entrance_date ≤ report_date AND (stop_date IS NULL OR stop_date > report_date)`

**결과:**
```
총 재직자: 411
결근율: 12.3%
무단결근율: 0.69%
퇴사율: 1.0%
신규 입사자: 11
퇴사자: 4
만근자: 99
장기근속자 (1년+): 288
60일 미만: 18
배치 후 퇴사: 2
데이터 오류: 0
```

### 6.2 대시보드 임베디드 데이터 (Dashboard Embedded Data)

**데이터 위치:**
- HTML 라인: 8041-8042
- 변수명: `const employeeDetails`
- 형식: JSON 배열 (554 objects)

**사전 계산된 플래그:**
- `is_active`: 재직 여부
- `hired_this_month`: 이번 달 입사
- `resigned_this_month`: 이번 달 퇴사
- `under_60_days`: 60일 미만 근속
- `long_term`: 장기근속 (1년+)
- `perfect_attendance`: 만근
- `has_unauthorized_absence`: 무단결근 여부
- `post_assignment_resignation`: 배치 후 퇴사
- `has_data_error`: 데이터 오류 여부

**계산 결과:**
```
총 재직자: 411 ✅
결근율: 10.9% ❌
무단결근율: 2.68% ❌
퇴사율: 1.9% ❌
신규 입사자: 12 ❌
퇴사자: 8 ❌
만근자: 239 ❌
장기근속자: 349 ❌
60일 미만: 19 ❌
배치 후 퇴사: 0 ❌
데이터 오류: 24 ❌
```

---

## 7. 권장 조치 사항 (Recommended Actions)

### 우선순위 1 - 즉시 수정 (Priority 1 - Immediate Correction)

1. **퇴사자 수 불일치 (4 vs 8)**
   - 원인 조사: `resigned_this_month` 플래그 로직 검토
   - 조치: `stop_date` 기준 12월 퇴사자 재확인
   - 파일: `src/visualization/complete_dashboard_builder.py`

2. **만근자 수 대폭 차이 (99 vs 239)**
   - 원인: 만근 정의 불일치
   - 조치: 출근 데이터 기반 결근 기록 재확인
   - 통일 기준: "2025-12월 출근 데이터에 결근(AR1-AR5) 기록이 없는 재직자"

3. **무단결근율 계산 오류 (0.69% vs 2.68%)**
   - 원인: 분모 차이 (출근 기록 수 vs 직원 수)
   - 조치: 공식 통일 필요
   - 권장 공식: `(AR1/AR2 기록 수 / 전체 출근 기록 수) * 100`

### 우선순위 2 - 검토 필요 (Priority 2 - Review Required)

4. **장기근속자 차이 (288 vs 349)**
   - 조치: `tenure_days` 계산 로직 확인
   - 기준: 2025-12-31 기준 365일 이상

5. **데이터 오류 24건**
   - 조치: 24명의 `error_type`, `error_description` 확인
   - 원본 검증에서 미검출된 이유 파악

### 우선순위 3 - 개선 권장 (Priority 3 - Enhancement)

6. **결근율 차이 (12.3% vs 10.9%)**
   - 조치: `working_days`, `absent_days` 집계 로직 확인
   - 검증: 수작업 샘플링으로 실제 값 대조

7. **플래그 사전 계산 vs 런타임 계산 통일**
   - 현재: 대시보드는 플래그 기반, 검증은 런타임 계산
   - 권장: 단일 truth source로 통일 (검증 스크립트 우선)

---

## 8. 데이터 품질 분석 (Data Quality Analysis)

### 8.1 데이터 완전성 (Data Completeness)
- ✅ 총 554명 직원 데이터 모두 로드됨
- ✅ 6,549건 출근 기록 모두 로드됨
- ⚠️ 24명에게 데이터 오류 플래그 존재

### 8.2 데이터 일관성 (Data Consistency)
- ❌ 계산 방법 불일치 (10/11 metrics)
- ❌ 플래그 vs 런타임 계산 차이
- ✅ 날짜 형식 파싱 정상 작동

### 8.3 데이터 정확성 (Data Accuracy)
- ✅ 원본 CSV 데이터 무결성 확인
- ⚠️ 대시보드 임베디드 값 재검증 필요
- ❌ 플래그 설정 로직 수정 필요

---

## 9. 테스트 증적 (Test Evidence)

### 실행 명령어 (Execution Commands)
```bash
# 원본 데이터 검증
python validate_dashboard_metrics.py --month 12 --year 2025

# 대시보드 추출 및 비교
python final_audit_report.py

# 상세 보고서 생성
python compare_metrics.py
```

### 로그 파일 (Log Files)
- 없음 (스크립트 출력이 전체 로그)

---

## 10. 최종 결론 (Final Conclusion)

### ❌ 배포 승인 불가 (DEPLOYMENT NOT APPROVED)

**이유 (Reason):**
1. **11개 중 10개 메트릭 불일치** (90.9% 오류율)
2. **핵심 지표 부정확:** 퇴사자 수, 만근자 수, 무단결근율
3. **데이터 오류 24건** 원인 미파악

### 필수 조치 후 재검증 필요 (Re-audit Required After Fixes)

다음 조치를 완료한 후 재감사가 필요합니다:

1. ✅ **플래그 설정 로직 수정** (`complete_dashboard_builder.py`)
2. ✅ **만근자 정의 통일** (출근 데이터 기반 재계산)
3. ✅ **무단결근율 공식 수정** (분모 통일)
4. ✅ **퇴사자 수 재확인** (stop_date 필터링 검증)
5. ✅ **데이터 오류 24건 조사** (error_type 확인)

### 재검증 명령어 (Re-audit Command)
```bash
# 수정 후 다시 실행
python final_audit_report.py
```

---

## 부록 A: 검증 스크립트 (Appendix A: Verification Scripts)

생성된 검증 스크립트:
1. `validate_dashboard_metrics.py` - 원본 데이터 메트릭 계산
2. `compare_metrics.py` - 원본 vs 대시보드 비교
3. `final_audit_report.py` - 종합 감사 보고서 생성
4. `verify_dashboard_display.py` - HTML 임베디드 데이터 추출

---

## 부록 B: 연락처 (Appendix B: Contact)

문의사항:
- **감사 담당:** Data Integrity Auditor Agent #2
- **보고서 생성일:** 2025-12-22
- **대시보드 버전:** HR_Dashboard_Complete_2025_12.html

---

**보고서 끝 (End of Report)**
