// File: project/static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    // 실시간 시계 업데이트
    updateClock();
    setInterval(updateClock, 1000);
    
    // 카드 호버 효과
    initCardHoverEffects();
    
    // 페이지 로딩 애니메이션
    initPageAnimations();
    
    // 통계 카운터 애니메이션
    initCounterAnimation();
});

function updateClock() {
    const now = new Date();
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    };
    const timeString = now.toLocaleString('ko-KR', options);
    
    const clockElement = document.getElementById('current-time');
    if (clockElement) {
        clockElement.textContent = timeString;
    }
}

function initCardHoverEffects() {
    const cards = document.querySelectorAll('.dashboard-card, .hover\\:shadow-lg');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
            this.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });
}

function initPageAnimations() {
    // 페이지 로드 시 요소들을 순차적으로 애니메이션
    const elements = document.querySelectorAll('.space-y-6 > *');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function initCounterAnimation() {
    // 숫자 카운터 애니메이션
    const counters = document.querySelectorAll('.text-2xl.font-semibold');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent.replace(/[^0-9]/g, ''));
        if (isNaN(target)) return;
        
        let current = 0;
        const increment = target / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            
            if (counter.textContent.includes('원')) {
                counter.textContent = Math.floor(current).toLocaleString() + '원';
            } else {
                counter.textContent = Math.floor(current).toLocaleString();
            }
        }, 30);
    });
}

// 차트 초기화 (Chart.js 사용 시)
function initCharts() {
    // 매출 차트
    const salesCtx = document.getElementById('salesChart');
    if (salesCtx) {
        new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: [], // 서버에서 데이터 받아옴
                datasets: [{
                    label: '일별 매출',
                    data: [],
                    borderColor: 'rgb(79, 70, 229)',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString() + '원';
                            }
                        }
                    }
                }
            }
        });
    }
}

// AJAX로 실시간 데이터 업데이트
function updateDashboardData() {
    fetch('/api/dashboard/stats/')
        .then(response => response.json())
        .then(data => {
            // 통계 업데이트
            updateStatCard('total-products', data.products.total);
            updateStatCard('low-stock-products', data.products.low_stock);
            updateStatCard('today-orders', data.orders.today);
            updateStatCard('month-revenue', data.orders.month_revenue);
        })
        .catch(error => {
            console.error('Dashboard data update failed:', error);
        });
}

function updateStatCard(id, value) {
    const element = document.getElementById(id);
    if (element) {
        if (id === 'month-revenue') {
            element.textContent = value.toLocaleString() + '원';
        } else {
            element.textContent = value.toLocaleString();
        }
    }
}

// 알림 토스트
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'warning' ? 'bg-yellow-500' :
        'bg-blue-500'
    } text-white`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // 애니메이션
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'transform 0.3s ease';
    
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // 자동 제거
    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}
