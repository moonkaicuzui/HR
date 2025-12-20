"""
js_utilities.py - JavaScript Utility Module Generator
자바스크립트 유틸리티 모듈 생성기

This module generates reusable JavaScript utilities for the HR Dashboard,
including security, accessibility, performance, and data handling functions.
이 모듈은 HR 대시보드용 재사용 가능한 자바스크립트 유틸리티를 생성합니다.
보안, 접근성, 성능, 데이터 처리 함수 포함.
"""

from typing import Dict, Any


class JSUtilities:
    """
    Generate JavaScript utility modules
    자바스크립트 유틸리티 모듈 생성
    """

    @staticmethod
    def get_security_utils() -> str:
        """
        Generate security utility functions
        보안 유틸리티 함수 생성

        Includes XSS prevention, input sanitization
        XSS 방지, 입력 살균 포함
        """
        return """
// ========================================
// Security Utilities / 보안 유틸리티
// ========================================

const SecurityUtils = {
    /**
     * Sanitize HTML to prevent XSS attacks
     * XSS 공격 방지를 위한 HTML 살균
     * @param {string} str - Input string
     * @returns {string} Sanitized string
     */
    sanitizeHTML: function(str) {
        if (typeof str !== 'string') return str;
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    /**
     * Safe innerHTML setter with optional trusted mode
     * 신뢰 모드 옵션이 있는 안전한 innerHTML 설정자
     * @param {HTMLElement} element - Target element
     * @param {string} html - HTML content
     * @param {boolean} trusted - Whether content is trusted
     */
    setInnerHTML: function(element, html, trusted = false) {
        if (!element) return;
        if (trusted) {
            element.innerHTML = html;
        } else {
            element.innerHTML = this.sanitizeHTML(html);
        }
    },

    /**
     * Escape special characters for use in regex
     * 정규식 사용을 위한 특수 문자 이스케이프
     * @param {string} str - Input string
     * @returns {string} Escaped string
     */
    escapeRegex: function(str) {
        return str.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
    },

    /**
     * Validate email format
     * 이메일 형식 검증
     * @param {string} email - Email address
     * @returns {boolean} Valid or not
     */
    isValidEmail: function(email) {
        const re = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
        return re.test(email);
    }
};
"""

    @staticmethod
    def get_accessibility_utils() -> str:
        """
        Generate accessibility utility functions
        접근성 유틸리티 함수 생성
        """
        return """
// ========================================
// Accessibility Utilities / 접근성 유틸리티
// ========================================

const A11yUtils = {
    /**
     * Announce message to screen readers
     * 스크린 리더에 메시지 공지
     * @param {string} message - Message to announce
     * @param {string} priority - 'polite' or 'assertive'
     */
    announce: function(message, priority = 'polite') {
        const announcer = document.getElementById('sr-announcer') || this.createAnnouncer();
        announcer.setAttribute('aria-live', priority);
        announcer.textContent = '';
        setTimeout(() => { announcer.textContent = message; }, 100);
    },

    /**
     * Create screen reader announcer element
     * 스크린 리더 공지 요소 생성
     * @returns {HTMLElement} Announcer element
     */
    createAnnouncer: function() {
        const announcer = document.createElement('div');
        announcer.id = 'sr-announcer';
        announcer.setAttribute('role', 'status');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'visually-hidden';
        document.body.appendChild(announcer);
        return announcer;
    },

    /**
     * Trap focus within a modal or dialog
     * 모달 또는 다이얼로그 내에 포커스 가두기
     * @param {HTMLElement} container - Container element
     */
    trapFocus: function(container) {
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        container.addEventListener('keydown', function(e) {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    },

    /**
     * Handle keyboard navigation for custom components
     * 사용자 정의 컴포넌트의 키보드 내비게이션 처리
     * @param {Event} event - Keyboard event
     * @param {Function} callback - Action callback
     */
    handleKeyboardClick: function(event, callback) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            callback(event);
        }
    },

    /**
     * Update aria-sort attribute on table headers
     * 테이블 헤더의 aria-sort 속성 업데이트
     * @param {HTMLElement} header - Table header element
     * @param {string} direction - 'ascending', 'descending', or 'none'
     */
    updateAriaSort: function(header, direction) {
        const allHeaders = header.parentElement.querySelectorAll('th[aria-sort]');
        allHeaders.forEach(th => th.setAttribute('aria-sort', 'none'));
        header.setAttribute('aria-sort', direction);
    }
};
"""

    @staticmethod
    def get_performance_utils() -> str:
        """
        Generate performance utility functions
        성능 유틸리티 함수 생성
        """
        return """
// ========================================
// Performance Utilities / 성능 유틸리티
// ========================================

const PerformanceUtils = {
    /**
     * Debounce function to limit execution rate
     * 실행 속도를 제한하는 디바운스 함수
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function} Debounced function
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function to limit execution frequency
     * 실행 빈도를 제한하는 쓰로틀 함수
     * @param {Function} func - Function to throttle
     * @param {number} limit - Time limit in ms
     * @returns {Function} Throttled function
     */
    throttle: function(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Request animation frame wrapper for smooth updates
     * 부드러운 업데이트를 위한 requestAnimationFrame 래퍼
     * @param {Function} callback - Callback function
     */
    nextFrame: function(callback) {
        requestAnimationFrame(() => {
            requestAnimationFrame(callback);
        });
    },

    /**
     * Measure execution time of a function
     * 함수 실행 시간 측정
     * @param {string} label - Performance label
     * @param {Function} func - Function to measure
     * @returns {*} Function result
     */
    measure: function(label, func) {
        const start = performance.now();
        const result = func();
        const end = performance.now();
        if (DEBUG_MODE) {
            debugLog(`[Performance] ${label}: ${(end - start).toFixed(2)}ms`);
        }
        return result;
    },

    /**
     * Lazy load images with IntersectionObserver
     * IntersectionObserver로 이미지 지연 로드
     * @param {string} selector - Image selector
     */
    lazyLoadImages: function(selector = 'img[data-src]') {
        const images = document.querySelectorAll(selector);
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    observer.unobserve(img);
                }
            });
        });
        images.forEach(img => observer.observe(img));
    }
};
"""

    @staticmethod
    def get_data_utils() -> str:
        """
        Generate data handling utility functions
        데이터 처리 유틸리티 함수 생성
        """
        return """
// ========================================
// Data Utilities / 데이터 유틸리티
// ========================================

const DataUtils = {
    /**
     * Format number with thousands separator
     * 천 단위 구분자로 숫자 포맷
     * @param {number} num - Number to format
     * @returns {string} Formatted number
     */
    formatNumber: function(num) {
        if (num === null || num === undefined) return '-';
        return num.toLocaleString();
    },

    /**
     * Format percentage with specified decimals
     * 지정된 소수점으로 백분율 포맷
     * @param {number} value - Percentage value
     * @param {number} decimals - Decimal places
     * @returns {string} Formatted percentage
     */
    formatPercent: function(value, decimals = 1) {
        if (value === null || value === undefined) return '-';
        return value.toFixed(decimals) + '%';
    },

    /**
     * Format date in localized format
     * 지역화된 형식으로 날짜 포맷
     * @param {string} dateStr - Date string
     * @param {string} lang - Language code
     * @returns {string} Formatted date
     */
    formatDate: function(dateStr, lang = 'ko') {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;

        const options = { year: 'numeric', month: '2-digit', day: '2-digit' };
        return date.toLocaleDateString(lang === 'ko' ? 'ko-KR' : lang === 'vi' ? 'vi-VN' : 'en-US', options);
    },

    /**
     * Calculate tenure in days
     * 재직 일수 계산
     * @param {string} startDate - Start date
     * @param {string} endDate - End date (optional, defaults to today)
     * @returns {number} Days
     */
    calculateTenure: function(startDate, endDate = null) {
        if (!startDate) return 0;
        const start = new Date(startDate);
        const end = endDate ? new Date(endDate) : new Date();
        const diffTime = Math.abs(end - start);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    },

    /**
     * Sort array of objects by key
     * 키로 객체 배열 정렬
     * @param {Array} arr - Array to sort
     * @param {string} key - Sort key
     * @param {boolean} ascending - Sort direction
     * @returns {Array} Sorted array
     */
    sortByKey: function(arr, key, ascending = true) {
        return [...arr].sort((a, b) => {
            const valA = a[key];
            const valB = b[key];

            if (valA === valB) return 0;
            if (valA === null || valA === undefined) return 1;
            if (valB === null || valB === undefined) return -1;

            const comparison = valA < valB ? -1 : 1;
            return ascending ? comparison : -comparison;
        });
    },

    /**
     * Deep clone an object
     * 객체 깊은 복사
     * @param {Object} obj - Object to clone
     * @returns {Object} Cloned object
     */
    deepClone: function(obj) {
        return JSON.parse(JSON.stringify(obj));
    },

    /**
     * Filter array by search term across multiple fields
     * 여러 필드에서 검색어로 배열 필터링
     * @param {Array} arr - Array to filter
     * @param {string} searchTerm - Search term
     * @param {Array} fields - Fields to search
     * @returns {Array} Filtered array
     */
    filterBySearch: function(arr, searchTerm, fields) {
        if (!searchTerm) return arr;
        const term = searchTerm.toLowerCase();
        return arr.filter(item => {
            return fields.some(field => {
                const value = item[field];
                if (value === null || value === undefined) return false;
                return String(value).toLowerCase().includes(term);
            });
        });
    }
};
"""

    @staticmethod
    def get_dom_utils() -> str:
        """
        Generate DOM manipulation utility functions
        DOM 조작 유틸리티 함수 생성
        """
        return """
// ========================================
// DOM Utilities / DOM 유틸리티
// ========================================

const DOMUtils = {
    /**
     * Create element with attributes and content
     * 속성과 콘텐츠로 요소 생성
     * @param {string} tag - Tag name
     * @param {Object} attrs - Attributes
     * @param {string|HTMLElement} content - Content
     * @returns {HTMLElement} Created element
     */
    createElement: function(tag, attrs = {}, content = null) {
        const el = document.createElement(tag);
        Object.entries(attrs).forEach(([key, value]) => {
            if (key === 'className') {
                el.className = value;
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    el.dataset[dataKey] = dataValue;
                });
            } else if (key.startsWith('on') && typeof value === 'function') {
                el.addEventListener(key.slice(2).toLowerCase(), value);
            } else {
                el.setAttribute(key, value);
            }
        });
        if (content) {
            if (typeof content === 'string') {
                el.textContent = content;
            } else {
                el.appendChild(content);
            }
        }
        return el;
    },

    /**
     * Show element with optional animation
     * 선택적 애니메이션으로 요소 표시
     * @param {HTMLElement} element - Element to show
     * @param {string} display - Display type
     */
    show: function(element, display = 'block') {
        if (element) element.style.display = display;
    },

    /**
     * Hide element
     * 요소 숨기기
     * @param {HTMLElement} element - Element to hide
     */
    hide: function(element) {
        if (element) element.style.display = 'none';
    },

    /**
     * Toggle element visibility
     * 요소 가시성 전환
     * @param {HTMLElement} element - Element to toggle
     * @param {string} display - Display type when visible
     */
    toggle: function(element, display = 'block') {
        if (!element) return;
        element.style.display = element.style.display === 'none' ? display : 'none';
    },

    /**
     * Add class to element
     * 요소에 클래스 추가
     * @param {HTMLElement} element - Target element
     * @param {string} className - Class name
     */
    addClass: function(element, className) {
        if (element) element.classList.add(className);
    },

    /**
     * Remove class from element
     * 요소에서 클래스 제거
     * @param {HTMLElement} element - Target element
     * @param {string} className - Class name
     */
    removeClass: function(element, className) {
        if (element) element.classList.remove(className);
    },

    /**
     * Get element by ID with null check
     * null 체크와 함께 ID로 요소 가져오기
     * @param {string} id - Element ID
     * @returns {HTMLElement|null} Element or null
     */
    getById: function(id) {
        return document.getElementById(id);
    },

    /**
     * Query selector with null check
     * null 체크와 함께 querySelector
     * @param {string} selector - CSS selector
     * @param {HTMLElement} parent - Parent element
     * @returns {HTMLElement|null} Element or null
     */
    query: function(selector, parent = document) {
        return parent.querySelector(selector);
    },

    /**
     * Query selector all
     * querySelectorAll
     * @param {string} selector - CSS selector
     * @param {HTMLElement} parent - Parent element
     * @returns {NodeList} NodeList
     */
    queryAll: function(selector, parent = document) {
        return parent.querySelectorAll(selector);
    }
};
"""

    @staticmethod
    def get_storage_utils() -> str:
        """
        Generate storage utility functions
        저장소 유틸리티 함수 생성
        """
        return """
// ========================================
// Storage Utilities / 저장소 유틸리티
// ========================================

const StorageUtils = {
    /**
     * Get item from localStorage with JSON parsing
     * JSON 파싱과 함께 localStorage에서 항목 가져오기
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value
     * @returns {*} Stored value or default
     */
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            debugLog('Storage get error:', e);
            return defaultValue;
        }
    },

    /**
     * Set item in localStorage with JSON stringifying
     * JSON 문자열화와 함께 localStorage에 항목 설정
     * @param {string} key - Storage key
     * @param {*} value - Value to store
     */
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            debugLog('Storage set error:', e);
        }
    },

    /**
     * Remove item from localStorage
     * localStorage에서 항목 제거
     * @param {string} key - Storage key
     */
    remove: function(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            debugLog('Storage remove error:', e);
        }
    },

    /**
     * Check if localStorage is available
     * localStorage 사용 가능 여부 확인
     * @returns {boolean} Available or not
     */
    isAvailable: function() {
        try {
            const test = '__storage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }
};
"""

    @staticmethod
    def get_export_utils() -> str:
        """
        Generate export utility functions
        내보내기 유틸리티 함수 생성
        """
        return """
// ========================================
// Export Utilities / 내보내기 유틸리티
// ========================================

const ExportUtils = {
    /**
     * Export data to CSV file
     * CSV 파일로 데이터 내보내기
     * @param {Array} data - Data array
     * @param {Array} headers - Column headers
     * @param {string} filename - Output filename
     */
    toCSV: function(data, headers, filename = 'export.csv') {
        const BOM = '\\uFEFF';
        const headerRow = headers.join(',');
        const rows = data.map(row => {
            return headers.map(h => {
                const val = row[h.key] || row[h] || '';
                return `"${String(val).replace(/"/g, '""')}"`;
            }).join(',');
        });

        const csv = BOM + [headerRow, ...rows].join('\\n');
        this.downloadFile(csv, filename, 'text/csv;charset=utf-8');
    },

    /**
     * Export data to JSON file
     * JSON 파일로 데이터 내보내기
     * @param {Object} data - Data object
     * @param {string} filename - Output filename
     */
    toJSON: function(data, filename = 'export.json') {
        const json = JSON.stringify(data, null, 2);
        this.downloadFile(json, filename, 'application/json');
    },

    /**
     * Download file with given content
     * 주어진 콘텐츠로 파일 다운로드
     * @param {string} content - File content
     * @param {string} filename - Filename
     * @param {string} mimeType - MIME type
     */
    downloadFile: function(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    },

    /**
     * Print specific element
     * 특정 요소 인쇄
     * @param {string} elementId - Element ID to print
     */
    printElement: function(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
            <head>
                <title>Print</title>
                <style>
                    body { font-family: sans-serif; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background: #f5f5f5; }
                </style>
            </head>
            <body>${element.innerHTML}</body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
};
"""

    def get_all_utilities(self) -> str:
        """
        Get all JavaScript utilities combined
        모든 자바스크립트 유틸리티 결합
        """
        return "\n".join([
            "// ================================================================",
            "// HR Dashboard JavaScript Utilities",
            "// HR 대시보드 자바스크립트 유틸리티",
            "// Generated by js_utilities.py",
            "// ================================================================",
            "",
            "// Debug mode flag / 디버그 모드 플래그",
            "const DEBUG_MODE = false;",
            "",
            "function debugLog(...args) {",
            "    if (DEBUG_MODE) console.log('[HR Dashboard]', ...args);",
            "}",
            "",
            self.get_security_utils(),
            "",
            self.get_accessibility_utils(),
            "",
            self.get_performance_utils(),
            "",
            self.get_data_utils(),
            "",
            self.get_dom_utils(),
            "",
            self.get_storage_utils(),
            "",
            self.get_export_utils(),
        ])


def main():
    """Test JSUtilities / JSUtilities 테스트"""
    js_utils = JSUtilities()
    js_code = js_utils.get_all_utilities()
    print("Generated JS length:", len(js_code), "characters")
    print("\n--- First 500 chars ---")
    print(js_code[:500])


if __name__ == "__main__":
    main()
