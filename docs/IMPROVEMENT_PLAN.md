# HR 대시보드 개선 계획서
# HR Dashboard Improvement Plan

**작성일 / Date**: 2025-10-06
**버전 / Version**: 1.0

---

## 📊 1. 데이터 정확성 검증 결과

### 발견된 문제점

| 메트릭 | 대시보드 값 | 실제 값 | 차이 | 문제 원인 |
|--------|------------|---------|------|----------|
| 재직자 수 | 393 | 393 | ✅ 일치 | - |
| 신규 입사자 (9월) | 485 | 7 | ⚠️ -478 | 전체 데이터를 신규로 계산 |
| 최근 퇴사자 (9월) | 16 | 8 | ⚠️ -8 | 계산 로직 오류 |
| 장기근속자 (1년+) | 284 | 315 | ⚠️ +31 | 기준일 계산 오류 |
| 60일 미만 재직자 | 35 | 45 | ⚠️ +10 | 날짜 계산 오류 |
| 배정 후 퇴사자 | 26 | 92 | ⚠️ +66 | 필터링 조건 오류 |
| 개근 직원 | 485 | 0 | ⚠️ -485 | 출근 데이터 매칭 실패 |
| 결근율 | 0% | 100% | ⚠️ 심각 | WTime 컬럼 해석 오류 |

### 수정 필요 사항

1. **Entrance Date / Stop working Date 파싱 개선**
   - 현재: 날짜 파싱이 제대로 되지 않음
   - 개선: pandas to_datetime with format specification

2. **출근 데이터 매칭 로직 수정**
   - 현재: ID No와 Employee No 매칭 실패
   - 개선: 컬럼명 매핑 테이블 추가

3. **WTime 컬럼 해석 수정**
   - 현재: WTime = 0을 결근으로 해석
   - 개선: WTime > 0을 근무로 해석

---

## 🎨 2. UI 개선 계획 (인센티브 대시보드 참조)

### 2.1 인센티브 대시보드의 우수한 디자인 요소

#### ✅ 적용할 요소들

1. **헤더 디자인**
   ```css
   - Gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
   - 패딩: 40px (현재 30px보다 넓음)
   - 그림자: 0 10px 30px rgba(0,0,0,0.15)
   - 보더 반경: 15px
   ```

2. **탭 네비게이션 시스템**
   - Overview / 팀별 분석 / 트렌드 분석 / 데이터 품질
   - 탭 간 전환 시 부드러운 애니메이션
   - Active 탭 그라디언트 강조

3. **카드 레이아웃**
   - 3x3 그리드 (현재 3열 구조 유지)
   - 카드 번호 뱃지 (오른쪽 상단 원형)
   - 호버 시 5px 상승 효과

4. **Summary Card 디자인**
   ```css
   .summary-card {
       border-radius: 12px;
       padding: 25px;
       box-shadow: 0 4px 6px rgba(0,0,0,0.07);
   }

   .summary-card h2 {
       font-size: 2rem;
       font-weight: 700;
   }
   ```

5. **Type Badge 스타일**
   - TYPE-1: #dbeafe / #1e40af (파랑)
   - TYPE-2: #fce7f3 / #be185d (핑크)
   - TYPE-3: #d1fae5 / #047857 (초록)

### 2.2 Management 대시보드의 우수한 기능 요소

#### ✅ 적용할 기능들

1. **카드 번호 시스템**
   ```html
   <div class="card-number">1</div>
   <div class="card-number">2</div>
   ...
   ```

2. **전월 대비 변화량 표시**
   ```html
   <div class="card-change change-positive">
       ↑ 전월 대비 +12명
   </div>
   <div class="card-change change-negative">
       ↓ 전월 대비 -5명
   </div>
   ```

3. **3x3 그리드 레이아웃**
   ```css
   .cards-grid-3x3 {
       display: grid;
       grid-template-columns: repeat(3, 1fr);
       gap: 20px;
   }
   ```

4. **팀별 카드 그리드**
   ```css
   .team-grid {
       display: grid;
       grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
       gap: 20px;
   }
   ```

---

## 📈 3. 차트 레이아웃 개선 계획

### 현재 문제점
- ❌ 1열 구조: 모든 차트가 세로로 나열됨
- ❌ 공간 활용 비효율적
- ❌ 스크롤이 너무 길어짐

### 개선 방안

#### 3.1 2열 그리드 레이아웃
```css
.charts-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin-top: 30px;
}

/* 전체 너비 차트용 */
.chart-full-width {
    grid-column: 1 / -1;
}
```

#### 3.2 차트 배치 계획
```
┌─────────────────────────────────────────┐
│  Weekly Trend (전체 너비)                │
└─────────────────────────────────────────┘
┌───────────────────┬──────────────────────┐
│  Absence Rate     │  Resignation Rate    │
├───────────────────┼──────────────────────┤
│  Attendance Trend │  Team Distribution   │
└───────────────────┴──────────────────────┘
```

#### 3.3 반응형 디자인
```css
@media (max-width: 1024px) {
    .charts-grid {
        grid-template-columns: 1fr;
    }
}
```

---

## 🔍 4. KPI 모달 상세 정보 개선 계획

### 현재 모달 내용
```
✅ 제목 (다국어)
✅ 설명
✅ 현재 값
❌ 추세 데이터 없음
❌ 비교 데이터 없음
❌ 드릴다운 상세 없음
```

### 개선할 모달 내용

#### 4.1 총 직원 수 (Total Employees) 모달

```html
<div class="modal-body">
    <!-- 1. 현재 상태 요약 -->
    <div class="stat-summary-grid">
        <div class="stat-box">
            <div class="stat-label">현재 재직자</div>
            <div class="stat-value">393명</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">전월 대비</div>
            <div class="stat-value text-success">+12명 (↑3.1%)</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">전년 동월 대비</div>
            <div class="stat-value text-danger">-25명 (↓6.0%)</div>
        </div>
    </div>

    <!-- 2. 6개월 추세 차트 -->
    <div class="trend-section">
        <h6>최근 6개월 추세</h6>
        <canvas id="employeesTrendChart"></canvas>
    </div>

    <!-- 3. 구성 분석 -->
    <div class="composition-section">
        <h6>직원 구성</h6>
        <div class="composition-grid">
            <div>직급별: A.INSPECTOR (45%), LINE LEADER (22%), ...</div>
            <div>팀별: Team A (35%), Team B (28%), ...</div>
            <div>재직기간: 1년+ (284명), 6개월-1년 (54명), ...</div>
        </div>
    </div>

    <!-- 4. 상세 목록 (접이식) -->
    <div class="accordion">
        <button class="accordion-toggle">
            전체 직원 목록 보기 (393명) ▼
        </button>
        <div class="accordion-content">
            <table class="table">
                <thead>
                    <tr>
                        <th>사번</th>
                        <th>이름</th>
                        <th>직급</th>
                        <th>팀</th>
                        <th>입사일</th>
                        <th>재직일수</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- 직원 목록 -->
                </tbody>
            </table>
        </div>
    </div>
</div>
```

#### 4.2 결근율 (Absence Rate) 모달

```html
<div class="modal-body">
    <!-- 1. 현재 상태 -->
    <div class="alert alert-warning">
        <strong>9월 결근율: 2.3%</strong> (전월 1.8% 대비 0.5%p 증가)
    </div>

    <!-- 2. 추세 차트 (6개월) -->
    <canvas id="absenceRateTrendChart"></canvas>

    <!-- 3. 팀별 비교 -->
    <div class="comparison-section">
        <h6>팀별 결근율 비교</h6>
        <div class="team-bars">
            <div class="team-bar">
                <span>Team A</span>
                <div class="bar" style="width: 50%">1.5%</div>
            </div>
            <div class="team-bar">
                <span>Team B</span>
                <div class="bar" style="width: 75%">2.8%</div>
            </div>
            <!-- ... -->
        </div>
    </div>

    <!-- 4. 주요 결근자 리스트 -->
    <div class="top-absentees">
        <h6>결근 빈도 상위 10명</h6>
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>순위</th>
                    <th>사번</th>
                    <th>이름</th>
                    <th>팀</th>
                    <th>결근일수</th>
                    <th>결근율</th>
                </tr>
            </thead>
            <tbody>
                <!-- 결근자 목록 -->
            </tbody>
        </table>
    </div>

    <!-- 5. 결근 사유 분석 -->
    <div class="absence-reasons">
        <h6>결근 사유 분포</h6>
        <canvas id="absenceReasonsPieChart"></canvas>
    </div>
</div>
```

#### 4.3 퇴사율 (Resignation Rate) 모달

```html
<div class="modal-body">
    <!-- 1. 경고 배너 -->
    <div class="alert alert-danger">
        <i class="bi bi-exclamation-triangle"></i>
        <strong>높은 퇴사율 경고!</strong> 9월 퇴사율 4.2% (임계값 3.0% 초과)
    </div>

    <!-- 2. 추세 분석 -->
    <div class="trend-analysis">
        <h6>퇴사율 추세 (12개월)</h6>
        <canvas id="resignationTrendChart"></canvas>
    </div>

    <!-- 3. 퇴사 이유 분석 -->
    <div class="resignation-reasons">
        <h6>주요 퇴사 사유</h6>
        <div class="reasons-grid">
            <div class="reason-item">
                <div class="reason-label">자발적 퇴사</div>
                <div class="reason-value">12명 (75%)</div>
            </div>
            <div class="reason-item">
                <div class="reason-label">계약 만료</div>
                <div class="reason-value">3명 (19%)</div>
            </div>
            <div class="reason-item">
                <div class="reason-label">해고</div>
                <div class="reason-value">1명 (6%)</div>
            </div>
        </div>
    </div>

    <!-- 4. 재직기간별 퇴사 분석 -->
    <div class="tenure-analysis">
        <h6>재직기간별 퇴사자 분포</h6>
        <canvas id="tenureDistributionChart"></canvas>
    </div>

    <!-- 5. 퇴사자 목록 -->
    <div class="resignees-list">
        <h6>9월 퇴사자 명단 (16명)</h6>
        <table class="table">
            <thead>
                <tr>
                    <th>사번</th>
                    <th>이름</th>
                    <th>직급</th>
                    <th>팀</th>
                    <th>입사일</th>
                    <th>퇴사일</th>
                    <th>재직일수</th>
                    <th>사유</th>
                </tr>
            </thead>
            <tbody>
                <!-- 퇴사자 목록 -->
            </tbody>
        </table>
    </div>
</div>
```

#### 4.4 데이터 오류 (Data Errors) 모달

```html
<div class="modal-body">
    <!-- 1. 오류 요약 -->
    <div class="error-summary">
        <div class="stat-grid">
            <div class="stat-item critical">
                <div class="stat-label">Critical</div>
                <div class="stat-value">25</div>
            </div>
            <div class="stat-item warning">
                <div class="stat-label">Warning</div>
                <div class="stat-value">5</div>
            </div>
            <div class="stat-item info">
                <div class="stat-label">Info</div>
                <div class="stat-value">0</div>
            </div>
        </div>
    </div>

    <!-- 2. 카테고리별 오류 분포 -->
    <div class="error-categories">
        <h6>오류 카테고리</h6>
        <div class="category-list">
            <div class="category-item" onclick="filterErrors('temporal')">
                <span class="category-icon">🕒</span>
                <span class="category-name">시간적 오류</span>
                <span class="category-count">8</span>
            </div>
            <div class="category-item" onclick="filterErrors('type')">
                <span class="category-icon">📋</span>
                <span class="category-name">유형 오류</span>
                <span class="category-count">5</span>
            </div>
            <div class="category-item" onclick="filterErrors('position')">
                <span class="category-icon">💼</span>
                <span class="category-name">직급 오류</span>
                <span class="category-count">3</span>
            </div>
            <!-- ... -->
        </div>
    </div>

    <!-- 3. 오류 상세 목록 -->
    <div class="error-details">
        <h6>오류 상세 내용</h6>
        <table class="table">
            <thead>
                <tr>
                    <th>심각도</th>
                    <th>카테고리</th>
                    <th>사번</th>
                    <th>이름</th>
                    <th>오류 내용</th>
                    <th>발견일</th>
                </tr>
            </thead>
            <tbody id="errorTableBody">
                <tr class="error-row critical">
                    <td><span class="badge badge-danger">Critical</span></td>
                    <td>시간적 오류</td>
                    <td>E12345</td>
                    <td>홍길동</td>
                    <td>입사일이 퇴사일보다 늦음</td>
                    <td>2025-09-25</td>
                </tr>
                <!-- ... -->
            </tbody>
        </table>
    </div>

    <!-- 4. 해결 권장사항 -->
    <div class="alert alert-info">
        <strong>💡 해결 권장사항</strong>
        <ul>
            <li>시간적 오류: basic manpower data의 날짜 필드 검증 필요</li>
            <li>유형 오류: TYPE 컬럼 표준화 작업 권장</li>
            <li>직급 오류: position_condition_matrix.json과 대조 필요</li>
        </ul>
    </div>
</div>
```

---

## 🚀 5. 구현 우선순위

### Phase 1: 데이터 정확성 수정 (최우선)
1. ✅ metric_calculator.py 수정
2. ✅ data_loader.py 컬럼 매핑 추가
3. ✅ 날짜 파싱 로직 개선
4. ✅ 검증 테스트 추가

### Phase 2: UI 개선
1. ✅ 헤더 디자인 업그레이드
2. ✅ 탭 네비게이션 추가
3. ✅ 카드 번호 뱃지 추가
4. ✅ 전월 대비 변화량 표시

### Phase 3: 차트 레이아웃 개선
1. ✅ 2열 그리드 레이아웃 구현
2. ✅ 반응형 디자인 추가
3. ✅ 차트 크기 최적화

### Phase 4: KPI 모달 상세화
1. ✅ 추세 차트 추가
2. ✅ 비교 분석 추가
3. ✅ 드릴다운 테이블 추가
4. ✅ 접이식 상세 목록

---

## 📋 6. 기술 스택

### 추가 필요 라이브러리
- Chart.js (이미 사용 중) ✅
- Bootstrap Icons (이미 사용 중) ✅
- 추가 없음 (현재 기술 스택으로 구현 가능)

### 새로 작성할 파일
1. `src/analytics/trend_analyzer.py` - 추세 분석 로직 (이미 존재)
2. `src/analytics/comparison_analyzer.py` - 비교 분석 로직 (신규)
3. `config/modal_templates.json` - 모달 템플릿 설정 (신규)

---

## ✅ 예상 효과

1. **데이터 정확성**: 100% 정확한 메트릭 계산
2. **사용자 경험**: 인센티브 대시보드 수준의 세련된 UI
3. **정보 접근성**: 모달을 통한 상세 드릴다운
4. **의사결정 지원**: 추세 및 비교 데이터 제공

---

**End of Document**
