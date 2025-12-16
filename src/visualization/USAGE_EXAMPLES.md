# Chart Utils & Modal System - 사용 예제

재사용 가능한 차트 및 모달 시스템 사용 가이드입니다.

## 📦 설치 및 불러오기

```html
<!-- HTML 파일에 포함 -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="./src/visualization/chart_utils.js"></script>
```

---

## 🎯 핵심 개념

### 1. 재사용 가능한 차트 함수
- `createWeeklyTrendChart()` - 주차별 트렌드 차트
- `createMonthlyTrendChart()` - 월별 트렌드 차트
- `createTeamDistributionChart()` - 팀별 분포 차트

### 2. 재사용 가능한 모달 시스템
- `createDetailModal()` - 설정 기반 모달 생성
- `ModalPresets` - 사전 정의된 모달 템플릿

---

## 📊 사용 예제

### 예제 1: ASSEMBLY 팀 총 재직자 수 모달

```javascript
// 주차별 데이터 준비
const weeklyData = [
  { label: '07/01', value: 143 },
  { label: '07/08', value: 143 },
  { label: '07/15', value: 143 },
  { label: '07/22', value: 143 },
  { label: '08/01', value: 143 },
  { label: '08/08', value: 143 },
  { label: '08/15', value: 143 }
];

// 팀별 분포 데이터
const teamDistribution = [
  { label: 'ASSEMBLY', value: 143 },
  { label: 'STITCHING', value: 98 },
  { label: 'BOTTOM', value: 30 }
];

// 모달 생성 및 표시
const modal = createDetailModal({
  modalId: 'assembly-total-employees',
  title: 'ASSEMBLY - 총 재직자 수 상세 분석',
  sections: [
    {
      type: 'weeklyTrend',
      title: '주차별 ASSEMBLY 총 재직자 수 트렌드 (20주)',
      data: weeklyData,
      chartOptions: {
        lineColor: '#6366f1',
        lineBackgroundColor: 'rgba(99, 102, 241, 0.1)',
        trendlineColor: '#45B7D1',
        yAxisLabel: '명'
      }
    },
    {
      type: 'teamDistribution',
      title: '팀별 재직자 수 분포',
      data: teamDistribution
    },
    {
      type: 'custom',
      render: (container) => {
        container.innerHTML = `
          <div style="text-align: right;">
            <button onclick="alert('단기 데이터 표시')"
                    style="padding: 8px 16px; background: #667eea; color: white;
                           border: none; border-radius: 4px; cursor: pointer;">
              단기
            </button>
          </div>
        `;
      }
    }
  ]
});

// 모달 표시
modal.show();

// 나중에 모달 닫기
// modal.hide();

// 완전히 제거
// modal.destroy();
```

---

### 예제 2: 장기근속자 상세 분석 모달 (사전 정의된 템플릿 사용)

```javascript
// 데이터 준비
const longTermWeeklyData = [
  { label: '07/01', value: 0 },
  { label: '07/08', value: 0 },
  { label: '08/01', value: 280 },
  { label: '08/08', value: 280 }
];

const longTermDistribution = [
  { label: 'ASSEMBLY', value: 95 },
  { label: 'STITCHING', value: 75 },
  { label: 'BOTTOM', value: 30 }
];

// 프리셋 사용
const config = ModalPresets.longTermEmployees(longTermWeeklyData, longTermDistribution);
const modal = createDetailModal(config);
modal.show();
```

---

### 예제 3: 데이터 오류 모달 (분포 차트 없음)

```javascript
const errorWeeklyData = [
  { label: '07/01', value: 0 },
  { label: '07/08', value: 0 },
  { label: '07/15', value: 0 },
  { label: '08/01', value: 0 }
];

const config = ModalPresets.dataErrors(errorWeeklyData);
const modal = createDetailModal(config);
modal.show();
```

---

### 예제 4: 완전 커스텀 모달 (여러 섹션 조합)

```javascript
const customModal = createDetailModal({
  modalId: 'custom-analysis',
  title: '커스텀 분석 대시보드',
  sections: [
    {
      type: 'weeklyTrend',
      title: '주간 트렌드',
      data: weeklyData,
      chartOptions: { lineColor: '#f59e0b' }
    },
    {
      type: 'custom',
      render: (container) => {
        container.innerHTML = `
          <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
            <h4>추가 정보</h4>
            <p>여기에 원하는 HTML 콘텐츠를 추가할 수 있습니다.</p>
            <ul>
              <li>커스텀 테이블</li>
              <li>커스텀 차트</li>
              <li>버튼 및 인터랙션</li>
            </ul>
          </div>
        `;
      }
    },
    {
      type: 'teamDistribution',
      title: '팀별 분포',
      data: teamDistribution
    }
  ],
  onClose: () => {
    console.log('모달이 닫혔습니다');
  }
});

customModal.show();
```

---

### 예제 5: 차트만 독립적으로 사용 (모달 없이)

```javascript
// HTML에 canvas 요소 추가
// <canvas id="my-weekly-chart"></canvas>

const weeklyData = [
  { label: '07/01', value: 143 },
  { label: '07/08', value: 145 },
  { label: '07/15', value: 147 }
];

// 차트 생성
const chart = createWeeklyTrendChart('my-weekly-chart', weeklyData, {
  title: '주차별 인원 트렌드',
  lineColor: '#10b981',
  yAxisLabel: '명',
  showTrendline: true
});

// 나중에 차트 제거
// chart.destroy();
```

---

### 예제 6: 여러 모달 동시 관리

```javascript
// 모달 저장소
const modals = {};

// 총 재직자 모달
modals.totalEmployees = createDetailModal(
  ModalPresets.totalEmployees('ASSEMBLY', weeklyData, teamDistribution)
);

// 장기근속자 모달
modals.longTerm = createDetailModal(
  ModalPresets.longTermEmployees(longTermWeeklyData, longTermDistribution)
);

// 데이터 오류 모달
modals.errors = createDetailModal(
  ModalPresets.dataErrors(errorWeeklyData)
);

// KPI 카드 클릭 이벤트에 연결
document.getElementById('total-employees-kpi').addEventListener('click', () => {
  modals.totalEmployees.show();
});

document.getElementById('long-term-kpi').addEventListener('click', () => {
  modals.longTerm.show();
});

document.getElementById('errors-kpi').addEventListener('click', () => {
  modals.errors.show();
});
```

---

## 🎨 차트 커스터마이징 옵션

### Weekly Trend Chart 옵션

```javascript
{
  title: '차트 제목',
  lineColor: '#6366f1',              // 라인 색상
  lineBackgroundColor: 'rgba(99, 102, 241, 0.1)',  // 배경 색상
  trendlineColor: '#45B7D1',         // 추세선 색상
  dataLabel: '주차별 총인원',        // 데이터 레이블
  trendlineLabel: '추세선',          // 추세선 레이블
  yAxisLabel: '명',                  // Y축 단위
  showTrendline: true,               // 추세선 표시 여부
  noDataMessage: '데이터가 없습니다'  // 빈 데이터 메시지
}
```

### Team Distribution Chart 옵션

```javascript
{
  title: '팀별 분포',
  colors: [
    '#FF6B6B', '#4ECDC4', '#45B7D1',
    '#96CEB4', '#FFEAA7'
  ],
  yAxisLabel: '명',
  indexAxis: 'y'  // 'x' for vertical, 'y' for horizontal
}
```

---

## 🔧 API 레퍼런스

### createDetailModal(config)

**Parameters:**
- `config.modalId` (string) - 고유 모달 ID
- `config.title` (string) - 모달 제목
- `config.sections` (Array) - 섹션 배열
  - `type`: 'weeklyTrend' | 'teamDistribution' | 'custom'
  - `title`: 섹션 제목
  - `data`: 차트 데이터
  - `chartOptions`: 차트 옵션 (선택사항)
  - `render`: 커스텀 렌더 함수 (custom 타입)
- `config.onClose` (Function) - 닫기 콜백 (선택사항)

**Returns:**
- `show()` - 모달 표시
- `hide()` - 모달 숨기기
- `destroy()` - 모달 완전 제거
- `getElement()` - DOM 요소 반환
- `getCharts()` - 차트 인스턴스 배열 반환

---

### ModalPresets

**totalEmployees(teamName, weeklyData, distributionData)**
- 총 재직자 수 상세 분석 모달 설정 반환

**longTermEmployees(weeklyData, distributionData)**
- 장기근속자 상세 분석 모달 설정 반환

**dataErrors(weeklyData)**
- 데이터 오류 상세 분석 모달 설정 반환

---

## 💡 모범 사례

### 1. 메모리 관리
```javascript
// 모달이 더 이상 필요 없을 때 완전히 제거
modal.destroy();

// 차트가 더 이상 필요 없을 때 제거
chart.destroy();
```

### 2. 데이터 검증
```javascript
// 데이터가 비어있을 때 처리
if (!weeklyData || weeklyData.length === 0) {
  console.warn('주차별 데이터가 없습니다');
  return;
}

const modal = createDetailModal({
  // ...config
});
```

### 3. 에러 처리
```javascript
try {
  const modal = createDetailModal(config);
  modal.show();
} catch (error) {
  console.error('모달 생성 실패:', error);
  alert('데이터를 불러오는 중 오류가 발생했습니다');
}
```

---

## 🚀 기대 효과

✅ **코드 재사용성**: 3개 이상의 지표에 동일 코드 사용
✅ **유지보수성**: 중앙화된 로직으로 버그 수정 용이
✅ **확장성**: 새로운 지표 추가 시 설정만으로 구현
✅ **일관성**: 모든 차트가 동일한 UX 제공
✅ **개발 속도**: 설정 기반 개발로 50% 이상 시간 절약

---

## 🐛 문제 해결

### 차트가 표시되지 않음
- Canvas 요소가 DOM에 존재하는지 확인
- Chart.js 라이브러리가 로드되었는지 확인
- 데이터 형식이 올바른지 확인

### 모달이 뒤에 표시됨
- `z-index` 값 조정 (기본값: 1000)
- 다른 요소의 `z-index` 확인

### 여러 모달 동시 표시 문제
- 각 모달에 고유한 `modalId` 사용
- 모달 열기 전에 다른 모달 닫기

---

## 📝 추가 참고사항

- Chart.js 공식 문서: https://www.chartjs.org/docs/
- 이 시스템은 Vanilla JavaScript로 작성되어 프레임워크 없이 사용 가능
- TypeScript 타입 정의는 향후 추가 예정
