/**
 * chart_utils.js - Reusable Chart Creation Utilities
 * 재사용 가능한 차트 생성 유틸리티
 *
 * Provides standardized chart creation functions for HR Dashboard:
 * - Monthly/Weekly trend charts with trendlines
 * - Team distribution charts
 * - Month-over-month comparison charts
 * - Treemap visualizations
 */

/**
 * Calculate linear regression trendline
 * 선형 회귀 추세선 계산
 */
function calculateTrendline(values) {
    const n = values.length;
    const xValues = Array.from({ length: n }, (_, i) => i);
    const sumX = xValues.reduce((a, b) => a + b, 0);
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = xValues.reduce((sum, x, i) => sum + x * values[i], 0);
    const sumX2 = xValues.reduce((sum, x) => sum + x * x, 0);
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    return xValues.map(x => slope * x + intercept);
}

/**
 * Create monthly trend chart
 * 월별 트렌드 차트 생성
 *
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - Month labels (e.g., ['9월', '10월'])
 * @param {Array} values - Employee counts for each month
 * @param {Object} options - Chart customization options
 * @returns {Chart} Chart.js instance
 */
function createMonthlyTrendChart(canvasId, labels, values, options = {}) {
    const defaultOptions = {
        title: '월별 총 재직자 수 트렌드',
        lineColor: '#FF6B6B',
        lineBackgroundColor: 'rgba(255, 107, 107, 0.1)',
        trendlineColor: '#45B7D1',
        dataLabel: '월별 총인원',
        trendlineLabel: '추세선',
        yAxisLabel: '명',
        height: 400,
        showTrendline: true,
        ...options
    };

    const trendlineData = calculateTrendline(values);
    const ctx = document.getElementById(canvasId).getContext('2d');

    const datasets = [
        {
            label: defaultOptions.dataLabel,
            data: values,
            borderColor: defaultOptions.lineColor,
            backgroundColor: defaultOptions.lineBackgroundColor,
            tension: 0.3,
            borderWidth: 3,
            pointRadius: 5,
            pointHoverRadius: 7,
            fill: true
        }
    ];

    if (defaultOptions.showTrendline) {
        datasets.push({
            label: defaultOptions.trendlineLabel,
            data: trendlineData,
            borderColor: defaultOptions.trendlineColor,
            borderDash: [10, 5],
            borderWidth: 2,
            fill: false,
            pointRadius: 0,
            pointHoverRadius: 0
        });
    }

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: defaultOptions.title,
                    align: 'start',
                    font: { size: 18, weight: 600 },
                    padding: { bottom: 10 },
                    color: '#333'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + defaultOptions.yAxisLabel;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + defaultOptions.yAxisLabel;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create weekly trend chart
 * 주차별 트렌드 차트 생성
 *
 * @param {string} canvasId - Canvas element ID
 * @param {Array} weeklyData - Array of {label, value} objects
 * @param {Object} options - Chart customization options
 * @returns {Chart} Chart.js instance or null if no data
 */
function createWeeklyTrendChart(canvasId, weeklyData, options = {}) {
    const defaultOptions = {
        title: '주차별 총 재직자 수 트렌드',
        lineColor: '#4ECDC4',
        lineBackgroundColor: 'rgba(78, 205, 196, 0.1)',
        trendlineColor: '#95E1D3',
        dataLabel: '주차별 총인원',
        trendlineLabel: '추세선',
        yAxisLabel: '명',
        noDataMessage: '주차별 데이터가 없습니다',
        showTrendline: true,
        ...options
    };

    if (!weeklyData || weeklyData.length === 0) {
        // Show no data message
        const canvas = document.getElementById(canvasId);
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.font = '16px Arial';
            ctx.fillStyle = '#666';
            ctx.textAlign = 'center';
            ctx.fillText(defaultOptions.noDataMessage, canvas.width / 2, canvas.height / 2);
        }
        return null;
    }

    const labels = weeklyData.map(w => w.label);
    const values = weeklyData.map(w => w.value);
    const trendlineData = calculateTrendline(values);
    const ctx = document.getElementById(canvasId).getContext('2d');

    const datasets = [
        {
            label: defaultOptions.dataLabel,
            data: values,
            borderColor: defaultOptions.lineColor,
            backgroundColor: defaultOptions.lineBackgroundColor,
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5,
            fill: true
        }
    ];

    if (defaultOptions.showTrendline) {
        datasets.push({
            label: defaultOptions.trendlineLabel,
            data: trendlineData,
            borderColor: defaultOptions.trendlineColor,
            borderDash: [10, 5],
            borderWidth: 2,
            fill: false,
            pointRadius: 0,
            pointHoverRadius: 0
        });
    }

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: defaultOptions.title,
                    align: 'start',
                    font: { size: 18, weight: 600 },
                    padding: { bottom: 10 },
                    color: '#333'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + defaultOptions.yAxisLabel;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + defaultOptions.yAxisLabel;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create horizontal bar chart for month-over-month comparison
 * 전월 대비 변화 가로 막대 차트 생성
 *
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - Team names
 * @param {Array} currentValues - Current month values
 * @param {Array} previousValues - Previous month values
 * @param {Object} options - Chart customization options
 * @returns {Chart} Chart.js instance
 */
function createMonthOverMonthBarChart(canvasId, labels, currentValues, previousValues, options = {}) {
    const defaultOptions = {
        title: '팀별 인원 변화 (전월 대비)',
        currentLabel: '당월',
        previousLabel: '전월',
        currentColor: '#4ECDC4',
        previousColor: '#95E1D3',
        yAxisLabel: '명',
        indexAxis: 'y', // horizontal bar
        ...options
    };

    const ctx = document.getElementById(canvasId).getContext('2d');

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: defaultOptions.previousLabel,
                    data: previousValues,
                    backgroundColor: defaultOptions.previousColor,
                    borderColor: defaultOptions.previousColor,
                    borderWidth: 1
                },
                {
                    label: defaultOptions.currentLabel,
                    data: currentValues,
                    backgroundColor: defaultOptions.currentColor,
                    borderColor: defaultOptions.currentColor,
                    borderWidth: 1
                }
            ]
        },
        options: {
            indexAxis: defaultOptions.indexAxis,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: defaultOptions.title,
                    align: 'start',
                    font: { size: 18, weight: 600 },
                    padding: { bottom: 10 },
                    color: '#333'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.x + defaultOptions.yAxisLabel;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + defaultOptions.yAxisLabel;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create team distribution chart
 * 팀별 분포 차트 생성
 *
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - Team names
 * @param {Array} values - Employee counts
 * @param {Object} options - Chart customization options
 * @returns {Chart} Chart.js instance
 */
function createTeamDistributionChart(canvasId, labels, values, options = {}) {
    const defaultOptions = {
        title: '팀별 재직자 수 분포',
        colors: [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DFE6E9', '#74B9FF', '#A29BFE', '#FD79A8', '#FDCB6E'
        ],
        yAxisLabel: '명',
        indexAxis: 'y',
        ...options
    };

    const ctx = document.getElementById(canvasId).getContext('2d');

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '인원',
                data: values,
                backgroundColor: defaultOptions.colors,
                borderColor: defaultOptions.colors.map(c => c),
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: defaultOptions.indexAxis,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: defaultOptions.title,
                    align: 'start',
                    font: { size: 18, weight: 600 },
                    padding: { bottom: 10 },
                    color: '#333'
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed.x + defaultOptions.yAxisLabel;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + defaultOptions.yAxisLabel;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create TYPE distribution pie chart
 * TYPE별 분포 파이 차트 생성
 *
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - TYPE names
 * @param {Array} values - Employee counts
 * @param {Object} options - Chart customization options
 * @returns {Chart} Chart.js instance
 */
function createTypeDistributionChart(canvasId, labels, values, options = {}) {
    const defaultOptions = {
        title: 'TYPE별 인원 현황',
        colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
        ...options
    };

    const ctx = document.getElementById(canvasId).getContext('2d');

    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: defaultOptions.colors,
                borderColor: '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: defaultOptions.title,
                    align: 'start',
                    font: { size: 18, weight: 600 },
                    padding: { bottom: 10 },
                    color: '#333'
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed + '명 (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create treemap chart for hierarchical team visualization
 * 트리맵 차트 생성
 *
 * @param {string} containerId - Container element ID
 * @param {Object} teamData - Team hierarchy data
 * @param {Object} options - Chart customization options
 */
function createTreemapChart(containerId, teamData, options = {}) {
    const defaultOptions = {
        title: '팀별 인원 계층 구조',
        colorScale: d3.scaleOrdinal(d3.schemeCategory10),
        showLabels: true,
        showValues: true,
        ...options
    };

    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <h6 style="margin-bottom: 15px; font-weight: 600;">${defaultOptions.title}</h6>
        <div id="${containerId}_treemap" style="width: 100%; height: 400px;"></div>
    `;

    // Implementation using d3.js or other treemap library
    // This is a placeholder - actual implementation depends on the library used
    console.log('Treemap chart data:', teamData);
}

/**
 * Extract weekly data from monthly metrics
 * 월별 메트릭에서 주차별 데이터 추출
 *
 * @param {Array} metricsArray - Array of monthly metrics
 * @returns {Array} Array of {label, value} objects for weekly data (only includes weeks with data > 0)
 */
function extractWeeklyData(metricsArray) {
    const allWeeklyData = [];

    metricsArray.forEach((month, monthIdx) => {
        if (month.weekly_metrics && typeof month.weekly_metrics === 'object') {
            // Handle object format: {Week1: {date: "09/01", total_employees: 393}, ...}
            Object.entries(month.weekly_metrics).sort().forEach(([weekKey, weekData]) => {
                const employeeCount = weekData.total_employees || 0;
                // Only include weeks with actual data (> 0)
                if (employeeCount > 0) {
                    allWeeklyData.push({
                        label: weekData.date || `${month.month.substring(5)} ${weekKey}`,
                        value: employeeCount
                    });
                }
            });
        } else if (Array.isArray(month.weekly_metrics)) {
            // Handle array format
            month.weekly_metrics.forEach((week, weekIdx) => {
                const employeeCount = week.total_employees || 0;
                // Only include weeks with actual data (> 0)
                if (employeeCount > 0) {
                    allWeeklyData.push({
                        label: `${month.month.substring(5)} W${weekIdx + 1}`,
                        value: employeeCount
                    });
                }
            });
        }
    });

    return allWeeklyData;
}

/**
 * =============================================================================
 * REUSABLE MODAL SYSTEM
 * 재사용 가능한 모달 시스템
 * =============================================================================
 */

/**
 * Create a reusable detail analysis modal
 * 재사용 가능한 상세 분석 모달 생성
 *
 * @param {Object} config - Modal configuration
 * @param {string} config.modalId - Unique modal identifier
 * @param {string} config.title - Modal title
 * @param {Array<Object>} config.sections - Array of section configurations
 * @param {Function} config.onClose - Optional close callback
 * @returns {Object} Modal control object with show/hide/destroy methods
 *
 * @example
 * // ASSEMBLY 팀 총 재직자 수
 * const modal = createDetailModal({
 *   modalId: 'assembly-total-employees',
 *   title: 'ASSEMBLY - 총 재직자 수 상세 분석',
 *   sections: [
 *     {
 *       type: 'weeklyTrend',
 *       title: '주차별 ASSEMBLY 총 재직자 수 트렌드 (20주)',
 *       data: weeklyData,
 *       chartOptions: { lineColor: '#6366f1' }
 *     },
 *     {
 *       type: 'teamDistribution',
 *       title: '팀별 재직자 수 분포',
 *       data: teamData
 *     },
 *     {
 *       type: 'custom',
 *       render: (container) => {
 *         container.innerHTML = '<button>단기</button>';
 *       }
 *     }
 *   ]
 * });
 * modal.show();
 */
function createDetailModal(config) {
    const {
        modalId,
        title,
        sections = [],
        onClose
    } = config;

    // Generate unique IDs for this modal
    const sanitizedId = modalId.replace(/[^a-zA-Z0-9]/g, '_');
    const modalElementId = `detail-modal-${sanitizedId}`;

    // Chart storage for cleanup
    const modalCharts = [];

    // Create modal HTML structure
    const modalHTML = `
        <div id="${modalElementId}" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4);">
            <div class="modal-content" style="background-color: #fefefe; margin: 5% auto; padding: 0; border-radius: 8px; max-width: 1200px; width: 90%; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <div class="modal-header" style="padding: 20px; border-bottom: 1px solid #e9ecef; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px 8px 0 0;">
                    <h2 class="modal-title" style="margin: 0; font-size: 24px; font-weight: 600;">${title}</h2>
                    <span class="close-modal" style="font-size: 28px; font-weight: bold; cursor: pointer; color: white; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">&times;</span>
                </div>
                <div class="modal-body" id="${modalElementId}-body" style="padding: 20px; max-height: 70vh; overflow-y: auto;">
                    <!-- Sections will be inserted here -->
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById(modalElementId);
    if (existingModal) {
        existingModal.remove();
    }

    // Insert modal into DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    const modalElement = document.getElementById(modalElementId);
    const modalBody = document.getElementById(`${modalElementId}-body`);
    const closeBtn = modalElement.querySelector('.close-modal');

    // Render sections
    sections.forEach((section, index) => {
        const sectionId = `${modalElementId}-section-${index}`;
        const sectionDiv = document.createElement('div');
        sectionDiv.id = sectionId;
        sectionDiv.className = 'modal-section';
        sectionDiv.style.marginBottom = '30px';

        if (section.type === 'weeklyTrend') {
            // Weekly trend chart section
            const canvasId = `${sectionId}-canvas`;
            sectionDiv.innerHTML = `
                <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;">
                    ${section.title || '주차별 트렌드'}
                </h4>
                <div style="position: relative; height: 400px;">
                    <canvas id="${canvasId}"></canvas>
                </div>
            `;
            modalBody.appendChild(sectionDiv);

            // Create chart after DOM insertion
            setTimeout(() => {
                const chart = createWeeklyTrendChart(canvasId, section.data, section.chartOptions || {});
                if (chart) modalCharts.push(chart);
            }, 100);

        } else if (section.type === 'teamDistribution') {
            // Team distribution chart section
            const canvasId = `${sectionId}-canvas`;
            sectionDiv.innerHTML = `
                <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;">
                    ${section.title || '팀별 분포'}
                </h4>
                <div style="position: relative; height: 400px;">
                    <canvas id="${canvasId}"></canvas>
                </div>
            `;
            modalBody.appendChild(sectionDiv);

            setTimeout(() => {
                const labels = section.data.map(d => d.label || d.name);
                const values = section.data.map(d => d.value || d.count);
                const chart = createTeamDistributionChart(canvasId, labels, values, section.chartOptions || {});
                if (chart) modalCharts.push(chart);
            }, 100);

        } else if (section.type === 'custom') {
            // Custom section with user-provided render function
            modalBody.appendChild(sectionDiv);
            if (typeof section.render === 'function') {
                section.render(sectionDiv);
            }
        }
    });

    // Close handlers
    const closeModal = () => {
        // Destroy all charts
        modalCharts.forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        modalCharts.length = 0;

        // Hide modal
        modalElement.style.display = 'none';

        // Call user callback
        if (typeof onClose === 'function') {
            onClose();
        }
    };

    closeBtn.addEventListener('click', closeModal);
    modalElement.addEventListener('click', (e) => {
        if (e.target === modalElement) {
            closeModal();
        }
    });

    // Return control object
    return {
        show: () => {
            modalElement.style.display = 'block';
        },
        hide: closeModal,
        destroy: () => {
            closeModal();
            modalElement.remove();
        },
        getElement: () => modalElement,
        getCharts: () => modalCharts
    };
}

/**
 * Create preset modal configurations
 * 사전 정의된 모달 설정 생성기
 */
const ModalPresets = {
    /**
     * Total employees detail modal
     * 총 재직자 수 상세 분석 모달
     */
    totalEmployees: (teamName, weeklyData, distributionData) => ({
        modalId: `${teamName}-total-employees`,
        title: `${teamName} - 총 재직자 수 상세 분석`,
        sections: [
            {
                type: 'weeklyTrend',
                title: `주차별 ${teamName} 총 재직자 수 트렌드`,
                data: weeklyData,
                chartOptions: {
                    lineColor: '#6366f1',
                    title: `주차별 ${teamName} 총 재직자 수 트렌드`
                }
            },
            {
                type: 'teamDistribution',
                title: '팀별 재직자 수 분포',
                data: distributionData
            }
        ]
    }),

    /**
     * Long-term employees detail modal
     * 장기근속자 상세 분석 모달
     */
    longTermEmployees: (weeklyData, distributionData) => ({
        modalId: 'long-term-employees',
        title: '장기근속자 상세 분석',
        sections: [
            {
                type: 'weeklyTrend',
                title: '주차별 장기근속자 수 트렌드',
                data: weeklyData,
                chartOptions: {
                    lineColor: '#10b981',
                    yAxisLabel: '명',
                    title: '주차별 장기근속자 수 트렌드'
                }
            },
            distributionData ? {
                type: 'teamDistribution',
                title: '팀별 장기근속자 분포',
                data: distributionData
            } : null
        ].filter(Boolean)
    }),

    /**
     * Data error detail modal
     * 데이터 오류 상세 분석 모달
     */
    dataErrors: (weeklyData) => ({
        modalId: 'data-errors',
        title: '데이터 오류 상세 분석',
        sections: [
            {
                type: 'weeklyTrend',
                title: '주차별 데이터 오류 건수 트렌드',
                data: weeklyData,
                chartOptions: {
                    lineColor: '#ef4444',
                    yAxisLabel: '건',
                    title: '주차별 데이터 오류 건수 트렌드'
                }
            }
        ]
    })
};

// Export functions (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        calculateTrendline,
        createMonthlyTrendChart,
        createWeeklyTrendChart,
        createMonthOverMonthBarChart,
        createTeamDistributionChart,
        createTypeDistributionChart,
        createTreemapChart,
        extractWeeklyData,
        createDetailModal,
        ModalPresets
    };
}
