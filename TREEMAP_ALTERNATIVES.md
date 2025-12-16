# 트리맵 차트 문제 분석 및 대안 제시

## 🔍 발견된 트리맵 문제

### 증상
- 트리맵 영역이 비어있음
- "트 하 팀" 같은 깨진 텍스트만 표시
- 데이터 로드/렌더링 실패

### 가능한 원인
1. **데이터 구조 문제**: 트리맵 데이터 형식 불일치
2. **차트 라이브러리 버전**: Chart.js는 트리맵을 기본 지원하지 않음
3. **플러그인 누락**: chartjs-chart-treemap 플러그인 필요하나 로드 실패 가능성
4. **데이터 타입 불일치**: 숫자/문자열 변환 문제
5. **반응형 레이아웃 충돌**: 컨테이너 크기 0px 문제

---

## ✅ 추천 대안 차트 (우선순위 순)

### 1. **Sunburst Chart (선버스트 차트)** ⭐⭐⭐⭐⭐

**장점:**
- 계층적 데이터 시각화에 최적
- 트리맵보다 시각적으로 더 매력적
- 중앙에서 외곽으로 확장되는 구조로 직관적
- 각 레벨별 비율을 색상과 크기로 명확히 표현
- 클릭 시 드릴다운 기능 구현 가능

**구현:**
```javascript
// D3.js 또는 Plotly.js 사용
const data = [{
    type: 'sunburst',
    labels: ['전체', 'ASSEMBLY INSPECTOR', 'LINE LEADER', ...],
    parents: ['', '전체', '전체', ...],
    values: [506, 280, 120, ...],
    marker: {
        colors: ['#1f77b4', '#ff7f0e', '#2ca02c', ...]
    }
}];
```

**추천 라이브러리:** Plotly.js (CDN 사용 가능)

---

### 2. **Hierarchical Bar Chart (계층적 막대 차트)** ⭐⭐⭐⭐

**장점:**
- 구현이 간단하고 안정적
- Chart.js 기본 기능으로 구현 가능 (추가 플러그인 불필요)
- 숫자 비교가 정확함
- 모바일에서도 가독성 우수

**구현:**
```javascript
// Chart.js horizontal bar chart
{
    type: 'bar',
    data: {
        labels: ['ASSEMBLY INSPECTOR', 'LINE LEADER', 'GROUP LEADER', ...],
        datasets: [{
            label: '인원 수',
            data: [280, 120, 45, ...],
            backgroundColor: ['#4CAF50', '#2196F3', '#FF9800', ...]
        }]
    },
    options: {
        indexAxis: 'y',  // 가로 막대
        responsive: true
    }
}
```

**추천 상황:** 현재 Chart.js를 사용 중이므로 가장 안전한 선택

---

### 3. **Nested Donut Chart (중첩 도넛 차트)** ⭐⭐⭐⭐

**장점:**
- 2-3단계 계층 구조 표현 가능
- 시각적으로 세련됨
- 비율 비교가 직관적
- Chart.js 기본 기능으로 구현 가능

**구현:**
```javascript
// 외부 도넛: 1차 직급
{
    type: 'doughnut',
    data: {
        labels: ['ASSEMBLY INSPECTOR', 'LINE LEADER', ...],
        datasets: [{
            data: [280, 120, 45, ...],
            backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', ...]
        }]
    }
}

// 내부 도넛: 2차 상세 분류
{
    type: 'doughnut',
    data: {
        labels: ['SHOES INSPECTOR', 'UPPER INSPECTOR', ...],
        datasets: [{
            data: [150, 130, 60, ...],
            backgroundColor: ['#FF6384AA', '#36A2EBAA', ...]  // 투명도 조절
        }]
    }
}
```

---

### 4. **Sankey Diagram (생키 다이어그램)** ⭐⭐⭐

**장점:**
- 계층 간 흐름을 시각화
- 직급 → 팀 → 부서 관계를 선으로 표현
- 데이터 흐름 파악에 최적

**구현:**
```javascript
// D3.js 또는 Google Charts
{
    nodes: [
        {name: 'ASSEMBLY INSPECTOR'},
        {name: 'SHOES TEAM'},
        {name: 'ASSEMBLY LINE TQC'}
    ],
    links: [
        {source: 0, target: 1, value: 150},
        {source: 1, target: 2, value: 150}
    ]
}
```

**주의:** 추가 라이브러리 필요 (Google Charts 또는 D3.js)

---

### 5. **Interactive Table with Visual Bars (시각화 테이블)** ⭐⭐⭐

**장점:**
- 정확한 숫자와 시각화를 동시에 제공
- 검색/정렬/필터 기능 추가 가능
- 구현이 매우 간단

**구현:**
```html
<table>
    <tr>
        <td>ASSEMBLY INSPECTOR</td>
        <td>280명</td>
        <td>
            <div style="width: 100%; background: #e0e0e0;">
                <div style="width: 55%; background: #4CAF50; height: 20px;"></div>
            </div>
        </td>
    </tr>
</table>
```

---

## 🎯 최종 추천

### 즉시 적용 가능 (플러그인 불필요)
1. **Hierarchical Bar Chart** - Chart.js 기본 기능만으로 구현
2. **Nested Donut Chart** - Chart.js 기본 기능만으로 구현

### 더 나은 UX를 원한다면
1. **Sunburst Chart** - Plotly.js CDN 추가 (30KB)
2. **Sankey Diagram** - D3.js 또는 Google Charts

---

## 🔧 구현 예시 코드

### Option 1: Horizontal Bar Chart (즉시 구현 가능)

```javascript
// 기존 트리맵 코드를 이것으로 교체
const ctx = document.getElementById('positionTreemap').getContext('2d');
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: hierarchyData.labels,
        datasets: [{
            label: '직급별 인원 수',
            data: hierarchyData.values,
            backgroundColor: [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
            ]
        }]
    },
    options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const total = hierarchyData.values.reduce((a,b) => a+b, 0);
                        const percent = ((context.parsed.x / total) * 100).toFixed(1);
                        return `${context.parsed.x}명 (${percent}%)`;
                    }
                }
            }
        },
        scales: {
            x: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value + '명';
                    }
                }
            }
        }
    }
});
```

### Option 2: Sunburst Chart (Plotly.js 사용)

```html
<!-- HTML head에 추가 -->
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>

<!-- JavaScript -->
<script>
const data = [{
    type: 'sunburst',
    labels: teamData.labels,
    parents: teamData.parents,
    values: teamData.values,
    marker: {
        colorscale: 'Viridis'
    },
    hovertemplate: '<b>%{label}</b><br>인원: %{value}명<br>비율: %{percentParent}<extra></extra>'
}];

const layout = {
    margin: {l: 0, r: 0, b: 0, t: 0},
    height: 500
};

Plotly.newPlot('positionTreemap', data, layout);
</script>
```

---

## 📊 비교표

| 차트 타입 | 구현 난이도 | 추가 라이브러리 | 모바일 지원 | 시각적 매력 | 데이터 정확성 |
|----------|-----------|--------------|-----------|----------|------------|
| Horizontal Bar | ⭐ 매우 쉬움 | 불필요 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Nested Donut | ⭐⭐ 쉬움 | 불필요 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Sunburst | ⭐⭐⭐ 보통 | Plotly.js | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Sankey | ⭐⭐⭐⭐ 어려움 | D3.js/Google | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Visual Table | ⭐ 매우 쉬움 | 불필요 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🚀 즉시 적용 가능한 해결책

**추천:** 현재 상황에서는 **Horizontal Bar Chart**가 가장 안전하고 빠른 해결책입니다.

1. 추가 플러그인 불필요 (Chart.js 기본 기능)
2. 안정적인 렌더링 보장
3. 모든 브라우저/기기에서 정상 작동
4. 데이터 타입 문제에 강건함
5. 구현 시간 5분 이내

원하시면 바로 코드를 적용해드릴 수 있습니다!
