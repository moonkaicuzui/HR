"""
virtual_scroll.py - Virtual Scrolling Implementation for Large Tables
대형 테이블용 가상 스크롤링 구현

This module provides virtual scrolling functionality for efficiently
rendering large datasets (1000+ rows) in the HR Dashboard.
이 모듈은 HR 대시보드에서 대규모 데이터 세트(1000+ 행)를
효율적으로 렌더링하기 위한 가상 스크롤링 기능을 제공합니다.

Key Benefits:
- Only renders visible rows plus buffer
- Reduces DOM nodes from 1000s to ~50
- Smooth scrolling experience
- Memory efficient
"""


class VirtualScrollGenerator:
    """
    Generate virtual scrolling JavaScript code
    가상 스크롤링 자바스크립트 코드 생성
    """

    def __init__(self, row_height: int = 48, buffer_size: int = 10):
        """
        Initialize VirtualScrollGenerator

        Args:
            row_height: Height of each row in pixels
            buffer_size: Number of extra rows to render above/below viewport
        """
        self.row_height = row_height
        self.buffer_size = buffer_size

    def get_virtual_scroll_js(self) -> str:
        """
        Generate complete virtual scrolling JavaScript
        완전한 가상 스크롤링 자바스크립트 생성

        Returns:
            JavaScript code for virtual scrolling
        """
        return f"""
// ========================================
// Virtual Scrolling Implementation
// 가상 스크롤링 구현
// ========================================

const VirtualScroll = {{
    // Configuration / 설정
    config: {{
        rowHeight: {self.row_height},
        bufferSize: {self.buffer_size},
        enabled: true,
        threshold: 200  // Enable virtual scroll when rows > threshold
    }},

    // State / 상태
    state: {{
        data: [],
        filteredData: [],
        container: null,
        tbody: null,
        scrollTop: 0,
        visibleStart: 0,
        visibleEnd: 0,
        totalHeight: 0,
        viewportHeight: 0,
        isScrolling: false,
        scrollTimeout: null,
        renderQueue: null
    }},

    /**
     * Initialize virtual scrolling
     * 가상 스크롤링 초기화
     * @param {{string}} containerId - Container element ID
     * @param {{string}} tbodyId - Table body element ID
     * @param {{Array}} data - Data array
     */
    init: function(containerId, tbodyId, data) {{
        this.state.container = document.getElementById(containerId);
        this.state.tbody = document.getElementById(tbodyId);
        this.state.data = data;
        this.state.filteredData = [...data];

        if (!this.state.container || !this.state.tbody) {{
            debugLog('Virtual scroll: Container or tbody not found');
            return;
        }}

        // Check if virtual scrolling should be enabled
        // 가상 스크롤링 활성화 여부 확인
        if (data.length <= this.config.threshold) {{
            debugLog('Virtual scroll: Disabled (data below threshold)');
            this.config.enabled = false;
            this.renderAllRows();
            return;
        }}

        debugLog('Virtual scroll: Enabled for', data.length, 'rows');
        this.setupContainer();
        this.bindEvents();
        this.render();
    }},

    /**
     * Setup container for virtual scrolling
     * 가상 스크롤링을 위한 컨테이너 설정
     */
    setupContainer: function() {{
        // Make container scrollable
        // 컨테이너를 스크롤 가능하게 만들기
        this.state.container.style.height = '600px';
        this.state.container.style.overflow = 'auto';
        this.state.container.style.position = 'relative';

        // Create spacer elements for scroll area
        // 스크롤 영역을 위한 스페이서 요소 생성
        this.state.totalHeight = this.state.filteredData.length * this.config.rowHeight;
        this.state.viewportHeight = this.state.container.clientHeight;

        // Add padding elements
        // 패딩 요소 추가
        const topPadding = document.createElement('tr');
        topPadding.id = 'virtual-scroll-top-padding';
        topPadding.style.height = '0px';
        topPadding.setAttribute('aria-hidden', 'true');

        const bottomPadding = document.createElement('tr');
        bottomPadding.id = 'virtual-scroll-bottom-padding';
        bottomPadding.style.height = '0px';
        bottomPadding.setAttribute('aria-hidden', 'true');

        // Clear tbody and add paddings
        // tbody 초기화 및 패딩 추가
        this.state.tbody.innerHTML = '';
        this.state.tbody.appendChild(topPadding);
        this.state.tbody.appendChild(bottomPadding);
    }},

    /**
     * Bind scroll and resize events
     * 스크롤 및 리사이즈 이벤트 바인딩
     */
    bindEvents: function() {{
        // Throttled scroll handler
        // 쓰로틀된 스크롤 핸들러
        const throttledScroll = PerformanceUtils.throttle(() => {{
            this.onScroll();
        }}, 16);  // ~60fps

        this.state.container.addEventListener('scroll', throttledScroll, {{ passive: true }});

        // Resize handler
        // 리사이즈 핸들러
        window.addEventListener('resize', PerformanceUtils.debounce(() => {{
            this.state.viewportHeight = this.state.container.clientHeight;
            this.render();
        }}, 250));
    }},

    /**
     * Handle scroll event
     * 스크롤 이벤트 처리
     */
    onScroll: function() {{
        this.state.scrollTop = this.state.container.scrollTop;
        this.render();
    }},

    /**
     * Calculate visible range and render rows
     * 표시 범위 계산 및 행 렌더링
     */
    render: function() {{
        if (!this.config.enabled) return;

        const scrollTop = this.state.scrollTop;
        const viewportHeight = this.state.viewportHeight;
        const rowHeight = this.config.rowHeight;
        const buffer = this.config.bufferSize;
        const dataLength = this.state.filteredData.length;

        // Calculate visible range with buffer
        // 버퍼가 포함된 표시 범위 계산
        let startIndex = Math.floor(scrollTop / rowHeight) - buffer;
        let endIndex = Math.ceil((scrollTop + viewportHeight) / rowHeight) + buffer;

        // Clamp to valid range
        // 유효한 범위로 제한
        startIndex = Math.max(0, startIndex);
        endIndex = Math.min(dataLength, endIndex);

        // Check if re-render needed
        // 재렌더링 필요 여부 확인
        if (startIndex === this.state.visibleStart && endIndex === this.state.visibleEnd) {{
            return;
        }}

        this.state.visibleStart = startIndex;
        this.state.visibleEnd = endIndex;

        // Use requestAnimationFrame for smooth rendering
        // 부드러운 렌더링을 위해 requestAnimationFrame 사용
        if (this.state.renderQueue) {{
            cancelAnimationFrame(this.state.renderQueue);
        }}

        this.state.renderQueue = requestAnimationFrame(() => {{
            this.renderRows(startIndex, endIndex);
        }});
    }},

    /**
     * Render rows in the visible range
     * 표시 범위 내의 행 렌더링
     * @param {{number}} start - Start index
     * @param {{number}} end - End index
     */
    renderRows: function(start, end) {{
        const tbody = this.state.tbody;
        const data = this.state.filteredData;
        const rowHeight = this.config.rowHeight;

        // Calculate padding heights
        // 패딩 높이 계산
        const topPaddingHeight = start * rowHeight;
        const bottomPaddingHeight = (data.length - end) * rowHeight;

        // Get padding elements
        // 패딩 요소 가져오기
        const topPadding = document.getElementById('virtual-scroll-top-padding');
        const bottomPadding = document.getElementById('virtual-scroll-bottom-padding');

        // Create document fragment for batch DOM updates
        // 배치 DOM 업데이트를 위한 document fragment 생성
        const fragment = document.createDocumentFragment();

        // Create top padding
        // 상단 패딩 생성
        const newTopPadding = document.createElement('tr');
        newTopPadding.id = 'virtual-scroll-top-padding';
        newTopPadding.style.height = topPaddingHeight + 'px';
        newTopPadding.setAttribute('aria-hidden', 'true');
        fragment.appendChild(newTopPadding);

        // Render visible rows
        // 표시되는 행 렌더링
        for (let i = start; i < end && i < data.length; i++) {{
            const row = this.createRow(data[i], i);
            fragment.appendChild(row);
        }}

        // Create bottom padding
        // 하단 패딩 생성
        const newBottomPadding = document.createElement('tr');
        newBottomPadding.id = 'virtual-scroll-bottom-padding';
        newBottomPadding.style.height = bottomPaddingHeight + 'px';
        newBottomPadding.setAttribute('aria-hidden', 'true');
        fragment.appendChild(newBottomPadding);

        // Replace tbody content
        // tbody 콘텐츠 교체
        tbody.innerHTML = '';
        tbody.appendChild(fragment);

        // Announce to screen readers
        // 스크린 리더에 공지
        if (typeof A11yUtils !== 'undefined') {{
            A11yUtils.announce(`Showing rows ${{start + 1}} to ${{Math.min(end, data.length)}} of ${{data.length}}`);
        }}
    }},

    /**
     * Create a table row element
     * 테이블 행 요소 생성
     * @param {{Object}} rowData - Row data object
     * @param {{number}} index - Row index
     * @returns {{HTMLElement}} Table row element
     */
    createRow: function(rowData, index) {{
        // This should be customized based on actual column structure
        // 실제 열 구조에 따라 사용자 정의되어야 함
        const tr = document.createElement('tr');
        tr.setAttribute('data-index', index);
        tr.setAttribute('role', 'row');

        // Use the global createEmployeeRow function if available
        // 사용 가능한 경우 전역 createEmployeeRow 함수 사용
        if (typeof createEmployeeRow === 'function') {{
            return createEmployeeRow(rowData, index);
        }}

        // Fallback: generic row creation
        // 폴백: 일반 행 생성
        Object.values(rowData).forEach((value, colIndex) => {{
            const td = document.createElement('td');
            td.textContent = value ?? '-';
            td.setAttribute('role', 'cell');
            tr.appendChild(td);
        }});

        return tr;
    }},

    /**
     * Update data and re-render
     * 데이터 업데이트 및 재렌더링
     * @param {{Array}} newData - New data array
     */
    updateData: function(newData) {{
        this.state.filteredData = newData;
        this.state.totalHeight = newData.length * this.config.rowHeight;

        if (newData.length <= this.config.threshold) {{
            this.config.enabled = false;
            this.renderAllRows();
        }} else {{
            this.config.enabled = true;
            this.state.scrollTop = 0;
            this.state.container.scrollTop = 0;
            this.render();
        }}
    }},

    /**
     * Render all rows without virtual scrolling (for small datasets)
     * 가상 스크롤링 없이 모든 행 렌더링 (소규모 데이터 세트용)
     */
    renderAllRows: function() {{
        const tbody = this.state.tbody;
        const data = this.state.filteredData;

        const fragment = document.createDocumentFragment();
        data.forEach((rowData, index) => {{
            fragment.appendChild(this.createRow(rowData, index));
        }});

        tbody.innerHTML = '';
        tbody.appendChild(fragment);
    }},

    /**
     * Scroll to specific row
     * 특정 행으로 스크롤
     * @param {{number}} index - Row index
     */
    scrollToRow: function(index) {{
        if (!this.state.container) return;
        const scrollTop = index * this.config.rowHeight;
        this.state.container.scrollTop = scrollTop;
    }},

    /**
     * Get current scroll position info
     * 현재 스크롤 위치 정보 가져오기
     * @returns {{Object}} Scroll info
     */
    getScrollInfo: function() {{
        return {{
            scrollTop: this.state.scrollTop,
            visibleStart: this.state.visibleStart,
            visibleEnd: this.state.visibleEnd,
            totalRows: this.state.filteredData.length,
            viewportHeight: this.state.viewportHeight
        }};
    }},

    /**
     * Destroy virtual scroll instance
     * 가상 스크롤 인스턴스 제거
     */
    destroy: function() {{
        if (this.state.renderQueue) {{
            cancelAnimationFrame(this.state.renderQueue);
        }}
        this.state.data = [];
        this.state.filteredData = [];
        this.state.container = null;
        this.state.tbody = null;
    }}
}};

// Export for global access
// 전역 접근을 위한 내보내기
window.VirtualScroll = VirtualScroll;
"""

    def get_integration_code(self) -> str:
        """
        Get code for integrating virtual scroll with existing table
        기존 테이블과 가상 스크롤 통합을 위한 코드

        Returns:
            JavaScript integration code
        """
        return """
// ========================================
// Virtual Scroll Integration
// 가상 스크롤 통합
// ========================================

/**
 * Initialize virtual scrolling for employee table
 * 직원 테이블용 가상 스크롤링 초기화
 */
function initVirtualScrolling() {
    // Check if we have large dataset
    // 대규모 데이터 세트 확인
    if (typeof employeeData !== 'undefined' && employeeData.length > 200) {
        debugLog('Initializing virtual scrolling for', employeeData.length, 'employees');

        // Initialize virtual scroll
        // 가상 스크롤 초기화
        VirtualScroll.init('employee-table-container', 'employeeTableBody', employeeData);

        // Override filter function to use virtual scroll
        // 가상 스크롤을 사용하도록 필터 함수 재정의
        const originalFilter = window.filterEmployees;
        window.filterEmployees = function(filterType) {
            const filteredData = originalFilter(filterType, true);  // Get data without rendering
            VirtualScroll.updateData(filteredData);
        };

        // Override search function
        // 검색 함수 재정의
        const originalSearch = window.searchEmployees;
        window.searchEmployees = function() {
            const filteredData = originalSearch(true);  // Get data without rendering
            VirtualScroll.updateData(filteredData);
        };
    }
}

// Initialize on DOM ready
// DOM 준비 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // Delay initialization to ensure data is loaded
    // 데이터 로드를 보장하기 위해 초기화 지연
    setTimeout(initVirtualScrolling, 100);
});
"""


def main():
    """Test VirtualScrollGenerator / VirtualScrollGenerator 테스트"""
    generator = VirtualScrollGenerator()
    js_code = generator.get_virtual_scroll_js()
    print("Generated JS length:", len(js_code), "characters")
    print("\n--- Virtual Scroll Configuration ---")
    print(f"Row height: {generator.row_height}px")
    print(f"Buffer size: {generator.buffer_size} rows")


if __name__ == "__main__":
    main()
