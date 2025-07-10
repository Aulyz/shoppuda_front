// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // 알림 매니저 초기화
    if (window.WebSocket) {
        window.notificationManager = new NotificationManager();
    }
    
    // 검색 매니저 초기화
    window.searchManager = new SearchManager();
    
    // 전역 유틸리티 함수들
    window.shopudaUtils = {
        // 로딩 표시
        showLoading: function(message = '처리 중입니다...') {
            Swal.fire({
                title: message,
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
        },
        
        // 로딩 숨기기
        hideLoading: function() {
            Swal.close();
        },
        
        // 성공 메시지
        showSuccess: function(message, timer = 3000) {
            Swal.fire({
                icon: 'success',
                title: '성공',
                text: message,
                timer: timer,
                showConfirmButton: false
            });
        },
        
        // 오류 메시지
        showError: function(message) {
            Swal.fire({
                icon: 'error',
                title: '오류',
                text: message,
                confirmButtonText: '확인'
            });
        },
        
        // 확인 대화상자
        confirm: function(message, confirmText = '확인', cancelText = '취소') {
            return Swal.fire({
                title: '확인',
                text: message,
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: confirmText,
                cancelButtonText: cancelText
            });
        },
        
        // CSRF 토큰 가져오기
        getCSRFToken: function() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                   document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';
        },
        
        // 날짜 포맷팅
        formatDate: function(date, format = 'YYYY-MM-DD') {
            if (!(date instanceof Date)) {
                date = new Date(date);
            }
            
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            
            return format
                .replace('YYYY', year)
                .replace('MM', month)
                .replace('DD', day)
                .replace('HH', hours)
                .replace('mm', minutes);
        },
        
        // 숫자 포맷팅 (천 단위 구분)
        formatNumber: function(number) {
            return new Intl.NumberFormat('ko-KR').format(number);
        },
        
        // 통화 포맷팅
        formatCurrency: function(amount) {
            return new Intl.NumberFormat('ko-KR', {
                style: 'currency',
                currency: 'KRW'
            }).format(amount);
        },
        
        // Debounce 함수
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
        
        // API 호출 헬퍼
        apiCall: async function(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            };
            
            const mergedOptions = {
                ...defaultOptions,
                ...options,
                headers: {
                    ...defaultOptions.headers,
                    ...options.headers
                }
            };
            
            try {
                const response = await fetch(url, mergedOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return await response.json();
                } else {
                    return await response.text();
                }
            } catch (error) {
                console.error('API 호출 오류:', error);
                throw error;
            }
        }
    };
    
    // 다크모드 토글 기능
    const darkModeToggle = document.querySelector('#dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.documentElement.classList.toggle('dark');
            const isDark = document.documentElement.classList.contains('dark');
            localStorage.setItem('darkMode', isDark);
        });
    }
    
    // 사이드바 토글 기능
    const sidebarToggle = document.querySelector('#sidebar-toggle');
    const sidebar = document.querySelector('#sidebar');
    const sidebarOverlay = document.querySelector('#sidebar-overlay');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('show');
            }
        });
        
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                sidebar.classList.remove('show');
                sidebarOverlay.classList.remove('show');
            });
        }
    }
    
    // 툴팁 초기화
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltipText = this.dataset.tooltip;
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip absolute z-50 px-2 py-1 text-xs text-white bg-gray-900 rounded shadow-lg pointer-events-none';
            tooltip.textContent = tooltipText;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
            
            this.tooltipElement = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this.tooltipElement) {
                document.body.removeChild(this.tooltipElement);
                this.tooltipElement = null;
            }
        });
    });
    
    // 자동 저장 기능
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        const saveInterval = parseInt(form.dataset.autoSave) || 30000; // 기본 30초
        
        let saveTimeout;
        const debouncedSave = window.shopudaUtils.debounce(() => {
            saveFormData(form);
        }, 2000);
        
        inputs.forEach(input => {
            input.addEventListener('input', debouncedSave);
        });
        
        // 주기적 저장
        setInterval(() => {
            saveFormData(form);
        }, saveInterval);
    });
    
    function saveFormData(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // 로컬 스토리지에 저장
        const formId = form.id || 'auto-save-form';
        localStorage.setItem(`auto-save-${formId}`, JSON.stringify({
            data: data,
            timestamp: Date.now()
        }));
        
        console.log('폼 데이터 자동 저장됨:', formId);
    }
    
    // 저장된 폼 데이터 복원
    function restoreFormData() {
        const autoSaveForms = document.querySelectorAll('[data-auto-save]');
        autoSaveForms.forEach(form => {
            const formId = form.id || 'auto-save-form';
            const savedData = localStorage.getItem(`auto-save-${formId}`);
            
            if (savedData) {
                try {
                    const parsed = JSON.parse(savedData);
                    const ageInMinutes = (Date.now() - parsed.timestamp) / 1000 / 60;
                    
                    // 10분 이내의 데이터만 복원
                    if (ageInMinutes < 10) {
                        Object.keys(parsed.data).forEach(key => {
                            const input = form.querySelector(`[name="${key}"]`);
                            if (input && !input.value) {
                                input.value = parsed.data[key];
                            }
                        });
                        
                        // 복원 알림
                        const restoreNotice = document.createElement('div');
                        restoreNotice.className = 'auto-save-notice bg-blue-100 border border-blue-300 text-blue-700 px-4 py-2 rounded mb-4';
                        restoreNotice.innerHTML = `
                            <i class="fas fa-info-circle mr-2"></i>
                            이전에 작성하던 내용이 복원되었습니다.
                            <button type="button" class="ml-2 text-blue-800 underline" onclick="this.parentElement.remove()">닫기</button>
                        `;
                        form.insertBefore(restoreNotice, form.firstChild);
                    }
                } catch (error) {
                    console.error('저장된 폼 데이터 복원 오류:', error);
                }
            }
        });
    }
    
    // 페이지 로드 시 폼 데이터 복원
    restoreFormData();
    
    // 폼 제출 시 자동 저장 데이터 삭제
    document.addEventListener('submit', function(e) {
        if (e.target.hasAttribute('data-auto-save')) {
            const formId = e.target.id || 'auto-save-form';
            localStorage.removeItem(`auto-save-${formId}`);
        }
    });
    
    // 페이지 떠날 때 확인 (수정된 폼이 있는 경우)
    let formModified = false;
    const trackedForms = document.querySelectorAll('[data-confirm-leave]');
    
    trackedForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                formModified = true;
            });
        });
        
        form.addEventListener('submit', () => {
            formModified = false;
        });
    });
    
    window.addEventListener('beforeunload', function(e) {
        if (formModified) {
            e.preventDefault();
            e.returnValue = '변경사항이 저장되지 않았습니다. 페이지를 떠나시겠습니까?';
            return e.returnValue;
        }
    });
    
    // 키보드 단축키
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K: 검색 포커스
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('#global-search-input');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Ctrl/Cmd + /: 단축키 도움말
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            showKeyboardShortcuts();
        }
        
        // ESC: 모달/드롭다운 닫기
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show, .dropdown.show');
            openModals.forEach(modal => {
                modal.classList.remove('show');
            });
        }
    });
    
    function showKeyboardShortcuts() {
        Swal.fire({
            title: '키보드 단축키',
            html: `
                <div class="text-left space-y-2">
                    <div class="flex justify-between">
                        <span><kbd class="px-2 py-1 bg-gray-200 rounded">Ctrl + K</kbd></span>
                        <span>검색 포커스</span>
                    </div>
                    <div class="flex justify-between">
                        <span><kbd class="px-2 py-1 bg-gray-200 rounded">Ctrl + /</kbd></span>
                        <span>단축키 도움말</span>
                    </div>
                    <div class="flex justify-between">
                        <span><kbd class="px-2 py-1 bg-gray-200 rounded">ESC</kbd></span>
                        <span>모달/드롭다운 닫기</span>
                    </div>
                </div>
            `,
            confirmButtonText: '확인'
        });
    }
    
    // 이미지 지연 로딩
    const lazyImages = document.querySelectorAll('img[data-src]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // 지원하지 않는 브라우저는 즉시 로드
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
        });
    }
    
    // 무한 스크롤
    const infiniteScrollContainers = document.querySelectorAll('[data-infinite-scroll]');
    infiniteScrollContainers.forEach(container => {
        let loading = false;
        let page = 1;
        const url = container.dataset.infiniteScroll;
        
        const loadMore = async () => {
            if (loading) return;
            loading = true;
            
            try {
                const response = await fetch(`${url}?page=${page + 1}`);
                const data = await response.json();
                
                if (data.html) {
                    container.insertAdjacentHTML('beforeend', data.html);
                    page++;
                }
                
                if (!data.has_next) {
                    scrollObserver.disconnect();
                }
            } catch (error) {
                console.error('무한 스크롤 로딩 오류:', error);
            } finally {
                loading = false;
            }
        };
        
        const scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    loadMore();
                }
            });
        }, { threshold: 0.1 });
        
        const sentinel = document.createElement('div');
        sentinel.className = 'infinite-scroll-sentinel';
        container.appendChild(sentinel);
        scrollObserver.observe(sentinel);
    });
    
    console.log('Shopuda ERP 초기화 완료');
});

// 전역 함수들
window.markNotificationRead = function(notificationId) {
    if (window.notificationManager) {
        window.notificationManager.markAsRead(notificationId);
    }
};

window.markAllNotificationsRead = function() {
    if (window.notificationManager) {
        window.notificationManager.markAllNotificationsReadWS();
    }
};

window.performGlobalSearch = function(query) {
    if (query && query.trim()) {
        window.location.href = `/search/?q=${encodeURIComponent(query.trim())}`;
    }
};