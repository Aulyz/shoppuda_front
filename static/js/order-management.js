// File: static/js/order-management.js

document.addEventListener('DOMContentLoaded', function() {
    // 주문 관리 페이지 초기화
    initializeOrderManagement();
    
    // 실시간 업데이트
    setupRealTimeUpdates();
    
    // 키보드 단축키
    setupKeyboardShortcuts();
});

function initializeOrderManagement() {
    // 상태별 색상 설정
    const statusColors = {
        'PENDING': 'bg-yellow-100 text-yellow-800',
        'CONFIRMED': 'bg-blue-100 text-blue-800',
        'PROCESSING': 'bg-indigo-100 text-indigo-800',
        'SHIPPED': 'bg-purple-100 text-purple-800',
        'DELIVERED': 'bg-green-100 text-green-800',
        'CANCELLED': 'bg-red-100 text-red-800',
        'REFUNDED': 'bg-gray-100 text-gray-800'
    };

    // 상태 배지 업데이트
    document.querySelectorAll('[data-status]').forEach(badge => {
        const status = badge.getAttribute('data-status');
        if (statusColors[status]) {
            badge.className = badge.className.replace(/bg-\w+-\d+\s+text-\w+-\d+/, statusColors[status]);
        }
    });

    // 테이블 정렬 기능
    setupTableSorting();
    
    // 필터 자동 적용
    setupAutoFilters();
}

function setupTableSorting() {
    const headers = document.querySelectorAll('th[data-sort]');
    
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const sortField = this.getAttribute('data-sort');
            const currentOrder = this.getAttribute('data-order') || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // URL 파라미터 업데이트
            const url = new URL(window.location);
            url.searchParams.set('sort', sortField);
            url.searchParams.set('order', newOrder);
            
            window.location.href = url.toString();
        });
    });
}

function setupAutoFilters() {
    // 플랫폼 필터 자동 적용
    const platformFilter = document.getElementById('platform');
    if (platformFilter) {
        platformFilter.addEventListener('change', function() {
            if (this.value) {
                applyFilter('platform', this.value);
            }
        });
    }

    // 상태 필터 자동 적용
    const statusFilter = document.getElementById('status');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            if (this.value) {
                applyFilter('status', this.value);
            }
        });
    }
}

function applyFilter(filterType, value) {
    const url = new URL(window.location);
    url.searchParams.set(filterType, value);
    url.searchParams.delete('page'); // 페이지 리셋
    
    window.location.href = url.toString();
}

function setupRealTimeUpdates() {
    // 30초마다 주문 상태 업데이트 확인
    setInterval(checkForUpdates, 30000);
    
    // 페이지 포커스 시 업데이트 확인
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            checkForUpdates();
        }
    });
}

async function checkForUpdates() {
    try {
        const response = await fetch('/api/orders/updates/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.has_updates) {
                showUpdateNotification(data.update_count);
            }
        }
    } catch (error) {
        console.error('Update check failed:', error);
    }
}

function showUpdateNotification(count) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <i class="fas fa-info-circle"></i>
            <span>${count}개의 주문이 업데이트되었습니다.</span>
            <button onclick="window.location.reload()" class="ml-2 text-blue-200 hover:text-white">
                <i class="fas fa-refresh"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // 5초 후 자동 제거
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + 키 조합
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'f': // 검색 포커스
                    e.preventDefault();
                    const searchInput = document.getElementById('search');
                    if (searchInput) {
                        searchInput.focus();
                        searchInput.select();
                    }
                    break;
                    
                case 'r': // 새로고침
                    e.preventDefault();
                    window.location.reload();
                    break;
                    
                case 'e': // CSV 내보내기
                    e.preventDefault();
                    exportOrdersCSV();
                    break;
            }
        }
        
        // Escape 키로 모달 닫기
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
}

function closeAllModals() {
    // Alpine.js 모달 닫기
    window.dispatchEvent(new CustomEvent('close-modals'));
    
    // SweetAlert 닫기
    if (window.Swal && Swal.isVisible()) {
        Swal.close();
    }
}

// 주문 상태 일괄 변경
async function bulkStatusUpdate(orderIds, newStatus) {
    const statusNames = {
        'PENDING': '대기중',
        'CONFIRMED': '확인됨',
        'PROCESSING': '처리중',
        'SHIPPED': '배송중',
        'DELIVERED': '배송완료',
        'CANCELLED': '취소됨',
        'REFUNDED': '환불됨'
    };

    const result = await Swal.fire({
        title: '일괄 상태 변경',
        text: `선택된 ${orderIds.length}개 주문을 ${statusNames[newStatus]} 상태로 변경하시겠습니까?`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: '변경',
        cancelButtonText: '취소',
        showLoaderOnConfirm: true,
        preConfirm: async () => {
            try {
                const response = await fetch('/orders/bulk-status-update/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        order_ids: orderIds,
                        status: newStatus
                    })
                });

                if (!response.ok) {
                    throw new Error('서버 오류가 발생했습니다.');
                }

                const data = await response.json();
                return data;
            } catch (error) {
                Swal.showValidationMessage(error.message);
            }
        },
        allowOutsideClick: () => !Swal.isLoading()
    });

    if (result.isConfirmed) {
        showSuccess(`${orderIds.length}개 주문의 상태가 변경되었습니다.`);
        setTimeout(() => window.location.reload(), 1000);
    }
}

// 주문 검색 자동완성
function setupOrderSearch() {
    const searchInput = document.getElementById('search');
    if (!searchInput) return;

    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            hideSearchSuggestions();
            return;
        }
        
        searchTimeout = setTimeout(() => {
            fetchSearchSuggestions(query);
        }, 300);
    });
    
    // 검색 입력 필드 외부 클릭 시 제안 숨김
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target)) {
            hideSearchSuggestions();
        }
    });
}

async function fetchSearchSuggestions(query) {
    try {
        const response = await fetch(`/api/orders/search-suggestions/?q=${encodeURIComponent(query)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            showSearchSuggestions(data.suggestions);
        }
    } catch (error) {
        console.error('Search suggestions failed:', error);
    }
}

function showSearchSuggestions(suggestions) {
    const searchInput = document.getElementById('search');
    let suggestionContainer = document.getElementById('search-suggestions');
    
    if (!suggestionContainer) {
        suggestionContainer = document.createElement('div');
        suggestionContainer.id = 'search-suggestions';
        suggestionContainer.className = 'absolute z-10 w-full bg-white shadow-lg rounded-md mt-1 border border-gray-200 max-h-60 overflow-y-auto';
        searchInput.parentNode.style.position = 'relative';
        searchInput.parentNode.appendChild(suggestionContainer);
    }
    
    if (suggestions.length === 0) {
        suggestionContainer.innerHTML = '<div class="px-4 py-3 text-sm text-gray-500">검색 결과가 없습니다.</div>';
        return;
    }
    
    suggestionContainer.innerHTML = suggestions.map(suggestion => `
        <div class="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
             onclick="selectSearchSuggestion('${suggestion.value}', '${suggestion.type}')">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-900">${suggestion.label}</p>
                    <p class="text-sm text-gray-500">${suggestion.description}</p>
                </div>
                <span class="text-xs text-gray-400">${suggestion.type}</span>
            </div>
        </div>
    `).join('');
}

function selectSearchSuggestion(value, type) {
    const searchInput = document.getElementById('search');
    searchInput.value = value;
    hideSearchSuggestions();
    
    // 검색 실행
    searchInput.closest('form').submit();
}

function hideSearchSuggestions() {
    const suggestionContainer = document.getElementById('search-suggestions');
    if (suggestionContainer) {
        suggestionContainer.remove();
    }
}

// CSV 내보내기
function exportOrdersCSV() {
    const currentUrl = new URL(window.location);
    const exportUrl = '/orders/export-csv/' + currentUrl.search;
    
    // 다운로드 링크 생성
    const link = document.createElement('a');
    link.href = exportUrl;
    link.download = `orders_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showSuccess('CSV 파일 다운로드가 시작되었습니다.');
}

// 주문 인쇄
function printOrder(orderNumber) {
    const printWindow = window.open(`/orders/print/${orderNumber}/`, '_blank');
    printWindow.onload = function() {
        printWindow.print();
        printWindow.close();
    };
}

// 주문 복사
async function duplicateOrder(orderId) {
    const result = await Swal.fire({
        title: '주문 복사',
        text: '이 주문을 복사하여 새 주문을 생성하시겠습니까?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: '복사',
        cancelButtonText: '취소'
    });

    if (result.isConfirmed) {
        try {
            const response = await fetch(`/orders/${orderId}/duplicate/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                showSuccess('주문이 복사되었습니다.');
                window.location.href = `/orders/${data.new_order_id}/edit/`;
            } else {
                throw new Error('복사에 실패했습니다.');
            }
        } catch (error) {
            showError(error.message);
        }
    }
}

// 주문 통계 업데이트
function updateOrderStats() {
    const stats = {
        total: 0,
        pending: 0,
        processing: 0,
        shipped: 0,
        delivered: 0,
        cancelled: 0
    };

    // 현재 페이지의 주문들로부터 통계 계산
    document.querySelectorAll('tbody tr').forEach(row => {
        const statusBadge = row.querySelector('[data-status]');
        if (statusBadge) {
            const status = statusBadge.getAttribute('data-status');
            stats.total++;
            
            switch(status) {
                case 'PENDING':
                    stats.pending++;
                    break;
                case 'PROCESSING':
                    stats.processing++;
                    break;
                case 'SHIPPED':
                    stats.shipped++;
                    break;
                case 'DELIVERED':
                    stats.delivered++;
                    break;
                case 'CANCELLED':
                    stats.cancelled++;
                    break;
            }
        }
    });

    // 통계 표시 업데이트
    updateStatDisplay('total-orders', stats.total);
    updateStatDisplay('pending-orders', stats.pending);
    updateStatDisplay('processing-orders', stats.processing);
    updateStatDisplay('shipped-orders', stats.shipped);
    updateStatDisplay('delivered-orders', stats.delivered);
    updateStatDisplay('cancelled-orders', stats.cancelled);
}

function updateStatDisplay(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        // 숫자 애니메이션
        animateNumber(element, parseInt(element.textContent) || 0, value, 500);
    }
}

function animateNumber(element, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (range * progress));
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

// 필터 저장/불러오기
function saveCurrentFilters() {
    const filters = {
        search: document.getElementById('search')?.value || '',
        platform: document.getElementById('platform')?.value || '',
        status: document.getElementById('status')?.value || '',
        date_from: document.getElementById('date_from')?.value || '',
        date_to: document.getElementById('date_to')?.value || ''
    };
    
    localStorage.setItem('order_filters', JSON.stringify(filters));
    showSuccess('현재 필터가 저장되었습니다.');
}

function loadSavedFilters() {
    const savedFilters = localStorage.getItem('order_filters');
    if (!savedFilters) return;
    
    try {
        const filters = JSON.parse(savedFilters);
        
        Object.keys(filters).forEach(key => {
            const element = document.getElementById(key);
            if (element && filters[key]) {
                element.value = filters[key];
            }
        });
        
        showSuccess('저장된 필터가 적용되었습니다.');
    } catch (error) {
        console.error('Failed to load saved filters:', error);
    }
}

function clearSavedFilters() {
    localStorage.removeItem('order_filters');
    
    // 폼 초기화
    const form = document.querySelector('form');
    if (form) {
        form.reset();
    }
    
    showSuccess('필터가 초기화되었습니다.');
}

// 유틸리티 함수들
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW'
    }).format(amount);
}

function formatDate(dateString) {
    return new Intl.DateTimeFormat('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(dateString));
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 전역으로 노출할 함수들
window.OrderManagement = {
    bulkStatusUpdate,
    exportOrdersCSV,
    printOrder,
    duplicateOrder,
    saveCurrentFilters,
    loadSavedFilters,
    clearSavedFilters,
    updateOrderStats
};

// 페이지 로드 완료 후 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(() => {
            updateOrderStats();
            setupOrderSearch();
        }, 100);
    });
} else {
    setTimeout(() => {
        updateOrderStats();
        setupOrderSearch();
    }, 100);
}