# Chart Utilities Documentation
차트 유틸리티 사용 설명서

## 개요 (Overview)

`chart_utils.js`는 HR Dashboard에서 사용하는 재사용 가능한 차트 생성 함수들을 제공합니다.

**제공 함수:**
- `createMonthlyTrendChart()` - 월별 트렌드 차트
- `createWeeklyTrendChart()` - 주차별 트렌드 차트
- `createMonthOverMonthBarChart()` - 전월 대비 변화 가로 막대 차트
- `createTeamDistributionChart()` - 팀별 분포 차트
- `createTypeDistributionChart()` - TYPE별 분포 파이 차트
- `calculateTrendline()` - 선형 회귀 추세선 계산
- `extractWeeklyData()` - 주차별 데이터 추출

---

## 설치 (Installation)

HTML 파일의 `<head>` 섹션에 Chart.js 다음에 추가:

```html
<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<!-- Chart Utilities -->
<script src="chart_utils.js"></script>
```

---

## 함수 사용법 (Function Usage)

### 1. `createMonthlyTrendChart()`

월별 트렌드 차트를 생성합니다 (추세선 포함).

**사용 예시:**
```javascript
const chart = createMonthlyTrendChart(
    'modalChart1_monthly',  // canvas ID
    ['9월', '10월'],        // 월 레이블
    [502, 399],             // 직원 수 값
    {
        title: '월별 총 재직자 수 트렌드',
        lineColor: '#FF6B6B',
        lineBackgroundColor: 'rgba(255, 107, 107, 0.1)',
        trendlineColor: '#45B7D1'
    }
);
```

**파라미터:**
- `canvasId` (string): Canvas element ID
- `labels` (Array): 월 레이블 배열
- `values` (Array): 각 월의 직원 수 배열
- `options` (Object): 커스터마이징 옵션
  - `title`: 차트 제목
  - `lineColor`: 선 색상
  - `lineBackgroundColor`: 배경 색상
  - `trendlineColor`: 추세선 색상
  - `dataLabel`: 데이터 레이블 (기본값: '월별 총인원')
  - `yAxisLabel`: Y축 레이블 (기본값: '명')
  - `showTrendline`: 추세선 표시 여부 (기본값: true)

**반환값:** Chart.js 인스턴스

---

### 2. `createWeeklyTrendChart()`

주차별 트렌드 차트를 생성합니다 (추세선 포함).

**사용 예시:**
```javascript
const weeklyData = [
    { label: '09/01', value: 393 },
    { label: '09/08', value: 395 },
    { label: '09/15', value: 398 }
];

const chart = createWeeklyTrendChart(
    'modalChart1_weekly',
    weeklyData,
    {
        title: '주차별 총 재직자 수 트렌드',
        lineColor: '#4ECDC4',
        trendlineColor: '#95E1D3'
    }
);
```

**파라미터:**
- `canvasId` (string): Canvas element ID
- `weeklyData` (Array): `{label, value}` 객체 배열
- `options` (Object): 커스터마이징 옵션
  - `title`: 차트 제목
  - `lineColor`: 선 색상
  - `lineBackgroundColor`: 배경 색상
  - `trendlineColor`: 추세선 색상
  - `noDataMessage`: 데이터 없을 때 메시지

**반환값:** Chart.js 인스턴스 또는 null (데이터 없을 경우)

---

### 3. `createMonthOverMonthBarChart()`

전월 대비 변화를 보여주는 가로 막대 차트를 생성합니다.

**사용 예시:**
```javascript
const chart = createMonthOverMonthBarChart(
    'modalChart1_change',
    ['ASSEMBLY', 'STITCHING', 'CUTTING'],  // 팀 이름
    [120, 95, 80],     // 당월 값
    [115, 98, 82],     // 전월 값
    {
        title: '팀별 인원 변화 (전월 대비)',
        currentLabel: '10월',
        previousLabel: '9월'
    }
);
```

**파라미터:**
- `canvasId` (string): Canvas element ID
- `labels` (Array): 팀 이름 배열
- `currentValues` (Array): 당월 값 배열
- `previousValues` (Array): 전월 값 배열
- `options` (Object): 커스터마이징 옵션
  - `title`: 차트 제목
  - `currentLabel`: 당월 레이블 (기본값: '당월')
  - `previousLabel`: 전월 레이블 (기본값: '전월')
  - `currentColor`: 당월 색상
  - `previousColor`: 전월 색상

**반환값:** Chart.js 인스턴스

---

### 4. `createTeamDistributionChart()`

팀별 분포를 보여주는 가로 막대 차트를 생성합니다.

**사용 예시:**
```javascript
const chart = createTeamDistributionChart(
    'modalChart1_teams',
    ['ASSEMBLY', 'STITCHING', 'CUTTING'],
    [120, 95, 80],
    {
        title: '팀별 재직자 수 분포'
    }
);
```

**파라미터:**
- `canvasId` (string): Canvas element ID
- `labels` (Array): 팀 이름 배열
- `values` (Array): 각 팀의 직원 수 배열
- `options` (Object): 커스터마이징 옵션
  - `title`: 차트 제목
  - `colors`: 색상 배열 (기본값: 미리 정의된 10가지 색상)
  - `indexAxis`: 차트 방향 (기본값: 'y' - 가로 막대)

**반환값:** Chart.js 인스턴스

---

### 5. `createTypeDistributionChart()`

TYPE별 분포를 보여주는 파이 차트를 생성합니다.

**사용 예시:**
```javascript
const chart = createTypeDistributionChart(
    'modalChart1_types',
    ['TYPE-1', 'TYPE-2', 'TYPE-3'],
    [150, 120, 129],
    {
        title: 'TYPE별 인원 현황'
    }
);
```

**파라미터:**
- `canvasId` (string): Canvas element ID
- `labels` (Array): TYPE 레이블 배열
- `values` (Array): 각 TYPE의 직원 수 배열
- `options` (Object): 커스터마이징 옵션
  - `title`: 차트 제목
  - `colors`: 색상 배열 (기본값: 5가지 색상)

**반환값:** Chart.js 인스턴스

---

### 6. `extractWeeklyData()`

월별 메트릭 배열에서 주차별 데이터를 추출합니다.

**사용 예시:**
```javascript
const metricsArray = [
    {
        month: '2024-09',
        weekly_metrics: {
            Week1: { date: '09/01', total_employees: 393 },
            Week2: { date: '09/08', total_employees: 395 }
        }
    }
];

const weeklyData = extractWeeklyData(metricsArray);
// 반환값: [{ label: '09/01', value: 393 }, { label: '09/08', value: 395 }]
```

**파라미터:**
- `metricsArray` (Array): 월별 메트릭 객체 배열

**반환값:** `{label, value}` 객체 배열

---

### 7. `calculateTrendline()`

선형 회귀를 사용하여 추세선 데이터를 계산합니다.

**사용 예시:**
```javascript
const values = [502, 399, 343, 332];
const trendline = calculateTrendline(values);
// 반환값: [476.5, 423.5, 370.5, 317.5] (예시)
```

**파라미터:**
- `values` (Array): 숫자 값 배열

**반환값:** 추세선 값 배열

---

## 완전한 사용 예시 (Complete Example)

### HTML
```html
<div class="modal-chart-container mb-4">
    <h6>월별 총 재직자 수 트렌드</h6>
    <div style="height: 400px; position: relative;">
        <canvas id="modalChart1_monthly"></canvas>
    </div>
</div>
```

### JavaScript
```javascript
// 데이터 준비
const monthLabels = ['9월', '10월'];
const monthValues = [502, 399];

// 차트 생성
const chart = createMonthlyTrendChart(
    'modalChart1_monthly',
    monthLabels,
    monthValues,
    {
        title: '월별 총 재직자 수 트렌드',
        lineColor: '#FF6B6B',
        lineBackgroundColor: 'rgba(255, 107, 107, 0.1)',
        trendlineColor: '#45B7D1',
        dataLabel: '월별 총인원',
        yAxisLabel: '명'
    }
);

// 차트 제거 (필요한 경우)
chart.destroy();
```

---

## 기존 코드 마이그레이션 (Migration Guide)

### Before (기존 코드)
```javascript
// 100+ 줄의 Chart.js 설정 코드
const ctx = document.getElementById('myChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: { ... },
    options: { ... }
});
```

### After (chart_utils.js 사용)
```javascript
// 5줄로 간소화
const chart = createMonthlyTrendChart(
    'myChart',
    labels,
    values,
    { title: '차트 제목' }
);
```

**장점:**
- ✅ 코드 90% 감소
- ✅ 재사용성 향상
- ✅ 유지보수 용이
- ✅ 일관된 스타일

---

## 커스터마이징 가이드 (Customization Guide)

### 색상 변경
```javascript
const chart = createMonthlyTrendChart(
    'myChart',
    labels,
    values,
    {
        lineColor: '#your-color',
        lineBackgroundColor: 'rgba(r, g, b, 0.1)',
        trendlineColor: '#your-trendline-color'
    }
);
```

### 추세선 제거
```javascript
const chart = createMonthlyTrendChart(
    'myChart',
    labels,
    values,
    { showTrendline: false }
);
```

### 레이블 변경
```javascript
const chart = createMonthlyTrendChart(
    'myChart',
    labels,
    values,
    {
        dataLabel: '사용자 정의 레이블',
        yAxisLabel: '단위'
    }
);
```

---

## 문제 해결 (Troubleshooting)

### 차트가 표시되지 않음
1. Chart.js가 chart_utils.js보다 먼저 로드되었는지 확인
2. Canvas ID가 올바른지 확인
3. 데이터 배열이 비어있지 않은지 확인

### 추세선이 표시되지 않음
- `showTrendline: true` 옵션이 설정되어 있는지 확인
- 데이터 포인트가 2개 이상인지 확인

### 색상이 적용되지 않음
- 색상 값이 유효한 CSS 색상 형식인지 확인
- 예: '#FF6B6B', 'rgba(255, 107, 107, 0.1)'

---

## 성능 최적화 (Performance Optimization)

### 차트 인스턴스 관리
```javascript
// 차트 저장
const modalCharts = {};

// 차트 생성
modalCharts['monthly'] = createMonthlyTrendChart(...);

// 차트 업데이트 전 기존 차트 제거
if (modalCharts['monthly']) {
    modalCharts['monthly'].destroy();
}
modalCharts['monthly'] = createMonthlyTrendChart(...);
```

### 대량 데이터 처리
```javascript
// 데이터 포인트가 많을 경우 샘플링
const sampledData = values.filter((_, index) => index % 2 === 0);
```

---

## 버전 정보 (Version History)

**v1.0.0** (2025-01-09)
- Initial release
- 6개 차트 생성 함수 제공
- 추세선 계산 유틸리티 포함
- 주차별 데이터 추출 함수 포함

---

## 라이선스 (License)

이 유틸리티는 HR Dashboard 프로젝트의 일부입니다.

---

## 지원 (Support)

문제가 발생하거나 개선 사항이 있으면 프로젝트 이슈 트래커에 보고해주세요.
