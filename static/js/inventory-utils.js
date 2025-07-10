// static/js/inventory-utils.js - 재고 관리 JavaScript 유틸리티 함수들

// CSRF 토큰 가져오기
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) {
        return token.value;
    }
    
    // 쿠키에서 CSRF 토큰 가져오기
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return decodeURIComponent(value);
        }
    }
    
    // meta 태그에서 CSRF 토큰 가져오기
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    
    console.warn('CSRF 토큰을 찾을 수 없습니다.');
    return '';
}

// SweetAlert2 알림 함수들
function showSuccess(message, title = '성공') {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'success',
            title: title,
            text: message,
            timer: 3000,
            timerProgressBar: true,
            showConfirmButton: false,
            toast: true,
            position: 'top-end',
            background: '#f0f9ff',
            color: '#0c4a6e',
            iconColor: '#059669'
        });
    } else {
        // SweetAlert2가 없으면 기본 alert 사용
        alert(`${title}: ${message}`);
    }
}

function showError(message, title = '오류') {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: title,
            text: message,
            timer: 5000,
            timerProgressBar: true,
            showConfirmButton: true,
            confirmButtonColor: '#dc2626',
            background: '#fef2f2',
            color: '#7f1d1d',
            iconColor: '#dc2626'
        });
    } else {
        alert(`${title}: ${message}`);
    }
}

function showWarning(message, title = '경고') {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'warning',
            title: title,
            text: message,
            timer: 4000,
            timerProgressBar: true,
            showConfirmButton: true,
            confirmButtonColor: '#d97706',
            background: '#fffbeb',
            color: '#78350f',
            iconColor: '#d97706'
        });
    } else {
        alert(`${title}: ${message}`);
    }
}

function showInfo(message, title = '정보') {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'info',
            title: title,
            text: message,
            timer: 3000,
            timerProgressBar: true,
            showConfirmButton: false,
            toast: true,
            position: 'top-end',
            background: '#eff6ff',
            color: '#1e3a8a',
            iconColor: '#3b82f6'
        });
    } else {
        alert(`${title}: ${message}`);
    }
}

// 로딩 상태 관리
let loadingAlert = null;

function showLoading(message = '처리 중...') {
    if (typeof Swal !== 'undefined') {
        loadingAlert = Swal.fire({
            title: message,
            html: `
                <div class="flex flex-col items-center space-y-4">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p class="text-sm text-gray-600">잠시만 기다려주세요...</p>
                </div>
            `,
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            background: '#ffffff',
            backdrop: 'rgba(0,0,0,0.4)'
        });
    }
}

function hideLoading() {
    if (loadingAlert && typeof Swal !== 'undefined') {
        Swal.close();
        loadingAlert = null;
    }
}

// 확인 대화상자
function showConfirm(message, title = '확인', confirmText = '확인', cancelText = '취소') {
    if (typeof Swal !== 'undefined') {
        return Swal.fire({
            title: title,
            text: message,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#059669',
            cancelButtonColor: '#6b7280',
            confirmButtonText: confirmText,
            cancelButtonText: cancelText,
            reverseButtons: true,
            focusCancel: true
        });
    } else {
        return new Promise((resolve) => {
            const result = confirm(`${title}\n\n${message}`);
            resolve({ isConfirmed: result });
        });
    }
}

// 숫자 포맷팅 함수들
function formatNumber(number, decimals = 0) {
    return new Intl.NumberFormat('ko-KR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(number);
}

function formatCurrency(amount, currency = 'KRW') {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// 날짜 포맷팅
function formatDate(dateString, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    const formatOptions = { ...defaultOptions, ...options };
    const date = new Date(dateString);
    
    return new Intl.DateTimeFormat('ko-KR', formatOptions).format(date);
}

// 상대적 시간 표시
function formatRelativeTime(dateString) {
    const now = new Date();
    const date = new Date(dateString);
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return '방금 전';
    } else if (diffInSeconds < 3600) {
        return `${Math.floor(diffInSeconds / 60)}분 전`;
    } else if (diffInSeconds < 86400) {
        return `${Math.floor(diffInSeconds / 3600)}시간 전`;
    } else if (diffInSeconds < 604800) {
        return `${Math.floor(diffInSeconds / 86400)}일 전`;
    } else {
        return formatDate(dateString, { month: 'short', day: 'numeric' });
    }
}

// 재고 상태 체크 함수
function getStockStatus(currentStock, minStock, maxStock) {
    if (currentStock === 0) {
        return {
            status: 'out_of_stock',
            label: '재고없음',
            color: 'red',
            priority: 0
        };
    } else if (currentStock <= minStock) {
        return {
            status: 'low_stock',
            label: '부족',
            color: 'yellow',
            priority: 1
        };
    } else if (currentStock > maxStock) {
        return {
            status: 'overstock',
            label: '과다',
            color: 'purple',
            priority: 3
        };
    } else {
        return {
            status: 'normal',
            label: '정상',
            color: 'green',
            priority: 2
        };
    }
}

// 재고 상태 뱃지 HTML 생성
function createStockStatusBadge(currentStock, minStock, maxStock) {
    const status = getStockStatus(currentStock, minStock, maxStock);
    const colorClasses = {
        red: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
        yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
        purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
        green: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
    };
    
    const icons = {
        out_of_stock: 'fa-ban',
        low_stock: 'fa-exclamation-triangle',
        overstock: 'fa-arrow-up',
        normal: 'fa-check'
    };
    
    return `
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClasses[status.color]}">
            <i class="fas ${icons[status.status]} w-3 h-3 mr-1"></i>
            ${status.label}
        </span>
    `;
}

// 검색 결과 하이라이트
function highlightSearchTerm(text, searchTerm) {
    if (!searchTerm || !text) return text;
    
    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">$1</mark>');
}

// 로컬 스토리지 유틸리티 (설정 저장용)
const InventoryStorage = {
    // 설정 저장
    saveSetting(key, value) {
        try {
            localStorage.setItem(`inventory_${key}`, JSON.stringify(value));
        } catch (e) {
            console.warn('설정 저장 실패:', e);
        }
    },
    
    // 설정 불러오기
    loadSetting(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(`inventory_${key}`);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn('설정 불러오기 실패:', e);
            return defaultValue;
        }
    },
    
    // 설정 삭제
    removeSetting(key) {
        try {
            localStorage.removeItem(`inventory_${key}`);
        } catch (e) {
            console.warn('설정 삭제 실패:', e);
        }
    }
};

// 테이블 정렬 유틸리티
function sortTable(table, columnIndex, direction = 'asc') {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        // 숫자인지 확인
        const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return direction === 'asc' ? aNum - bNum : bNum - aNum;
        } else {
            return direction === 'asc' ? 
                aVal.localeCompare(bVal, 'ko-KR') : 
                bVal.localeCompare(aVal, 'ko-KR');
        }
    });
    
    // 정렬된 행들을 다시 추가
    rows.forEach(row => tbody.appendChild(row));
}

// 키보드 단축키 설정
function setupInventoryKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + F: 검색 포커스
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Ctrl/Cmd + E: 내보내기
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            const exportBtn = document.querySelector('[data-action="export"]');
            if (exportBtn) {
                e.preventDefault();
                exportBtn.click();
            }
        }
        
        // Ctrl/Cmd + R: 새로고침 (기본 동작 유지하되 확인)
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            const hasUnsavedChanges = document.querySelector('.unsaved-changes');
            if (hasUnsavedChanges) {
                e.preventDefault();
                showConfirm('저장하지 않은 변경사항이 있습니다. 새로고침하시겠습니까?')
                    .then((result) => {
                        if (result.isConfirmed) {
                            window.location.reload();
                        }
                    });
            }
        }
    });
}

// 애니메이션 유틸리티
function addFadeInAnimation(elements, delay = 100) {
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * delay);
    });
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 키보드 단축키 설정
    setupInventoryKeyboardShortcuts();
    
    // 테이블 행들에 페이드인 애니메이션 적용
    const tableRows = document.querySelectorAll('tbody tr');
    if (tableRows.length > 0) {
        addFadeInAnimation(tableRows, 50);
    }
    
    // 통계 카드들에 애니메이션 적용
    const statCards = document.querySelectorAll('.grid > div');
    if (statCards.length > 0) {
        addFadeInAnimation(statCards, 100);
    }
    
    // 툴팁 초기화 (Bootstrap이나 다른 툴팁 라이브러리가 있는 경우)
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// CSS 클래스 추가/제거 유틸리티
function addClass(element, className) {
    if (element && !element.classList.contains(className)) {
        element.classList.add(className);
    }
}

function removeClass(element, className) {
    if (element && element.classList.contains(className)) {
        element.classList.remove(className);
    }
}

function toggleClass(element, className) {
    if (element) {
        element.classList.toggle(className);
    }
}

// 디바운스 함수 (검색 입력 최적화용)
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// 스로틀 함수 (스크롤 이벤트 최적화용)
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 전역 스코프에 함수들 노출
window.InventoryUtils = {
    getCsrfToken,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoading,
    hideLoading,
    showConfirm,
    formatNumber,
    formatCurrency,
    formatDate,
    formatRelativeTime,
    getStockStatus,
    createStockStatusBadge,
    highlightSearchTerm,
    InventoryStorage,
    sortTable,
    setupInventoryKeyboardShortcuts,
    addFadeInAnimation,
    addClass,
    removeClass,
    toggleClass,
    debounce,
    throttle
};

// 편의를 위해 자주 사용하는 함수들을 전역으로 노출
window.getCsrfToken = getCsrfToken;
window.showSuccess = showSuccess;
window.showError = showError;
window.showWarning = showWarning;
window.showInfo = showInfo;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showConfirm = showConfirm;