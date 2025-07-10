// static/js/notifications.js
class NotificationManager {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.bindEvents();
    }
    
    connectWebSocket() {
        if (!window.WebSocket) {
            console.error('WebSocket을 지원하지 않는 브라우저입니다.');
            return;
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('알림 WebSocket 연결됨');
            this.reconnectAttempts = 0;
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.socket.onclose = (event) => {
            console.log('알림 WebSocket 연결 끊어짐');
            this.handleReconnect();
        };
        
        this.socket.onerror = (error) => {
            console.error('알림 WebSocket 오류:', error);
        };
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'notification':
                this.showNotification(data.data);
                this.updateNotificationUI(data.data);
                break;
            default:
                console.log('알 수 없는 메시지 타입:', data.type);
        }
    }
    
    showNotification(notification) {
        // SweetAlert2 토스트 알림
        Swal.fire({
            title: notification.title,
            text: notification.message,
            icon: this.getIconType(notification.notification_type),
            position: 'top-end',
            showConfirmButton: false,
            timer: 5000,
            timerProgressBar: true,
            toast: true,
            background: document.documentElement.classList.contains('dark') ? '#374151' : '#ffffff',
            color: document.documentElement.classList.contains('dark') ? '#f9fafb' : '#111827',
            didOpen: (toast) => {
                toast.addEventListener('click', () => {
                    if (notification.url) {
                        window.location.href = notification.url;
                    }
                });
            }
        });
        
        // 브라우저 네이티브 알림 (권한이 있는 경우)
        this.showBrowserNotification(notification);
    }
    
    async showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const browserNotification = new Notification(notification.title, {
                body: notification.message,
                icon: '/static/images/notification-icon.png',
                tag: `notification-${notification.id}`,
                requireInteraction: false
            });
            
            browserNotification.onclick = () => {
                window.focus();
                if (notification.url) {
                    window.location.href = notification.url;
                }
                browserNotification.close();
            };
            
            // 5초 후 자동 닫기
            setTimeout(() => {
                browserNotification.close();
            }, 5000);
        }
    }
    
    updateNotificationUI(notification) {
        // 알림 개수 업데이트
        const badgeElement = document.querySelector('.notification-badge');
        if (badgeElement) {
            const currentCount = parseInt(badgeElement.textContent) || 0;
            const newCount = currentCount + 1;
            badgeElement.textContent = newCount > 99 ? '99+' : newCount;
            badgeElement.style.display = 'flex';
        }
        
        // 알림 목록에 새 알림 추가 (열려있는 경우)
        const notificationList = document.querySelector('#notification-list');
        if (notificationList) {
            const notificationElement = this.createNotificationElement(notification);
            notificationList.insertBefore(notificationElement, notificationList.firstChild);
        }
        
        // 커스텀 이벤트 발생
        window.dispatchEvent(new CustomEvent('new-notification', {
            detail: notification
        }));
    }
    
    createNotificationElement(notification) {
        const element = document.createElement('div');
        element.className = 'notification-item px-4 py-3 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer bg-blue-50 dark:bg-blue-900/20';
        element.dataset.notificationId = notification.id;
        
        element.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <div class="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-600 flex items-center justify-center">
                        <i class="${notification.icon} ${notification.color} text-sm"></i>
                    </div>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">${notification.title}</p>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">${notification.message}</p>
                    <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">방금 전</p>
                </div>
                <div class="flex-shrink-0">
                    <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                </div>
            </div>
        `;
        
        element.addEventListener('click', () => {
            this.markAsRead(notification.id);
            if (notification.url) {
                window.location.href = notification.url;
            }
        });
        
        return element;
    }
    
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/notifications/mark-read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                // UI 업데이트
                const element = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (element) {
                    element.classList.remove('bg-blue-50', 'dark:bg-blue-900/20');
                    const badge = element.querySelector('.w-2.h-2.bg-blue-500');
                    if (badge) badge.remove();
                }
                
                // 알림 개수 감소
                this.decrementNotificationCount();
            }
        } catch (error) {
            console.error('알림 읽음 처리 오류:', error);
        }
    }
    
    decrementNotificationCount() {
        const badgeElement = document.querySelector('.notification-badge');
        if (badgeElement) {
            const currentCount = parseInt(badgeElement.textContent) || 0;
            const newCount = Math.max(0, currentCount - 1);
            
            if (newCount === 0) {
                badgeElement.style.display = 'none';
            } else {
                badgeElement.textContent = newCount > 99 ? '99+' : newCount;
            }
        }
    }
    
    getIconType(notificationType) {
        const iconMap = {
            'order': 'success',
            'stock': 'warning',
            'payment': 'success',
            'system': 'info',
            'warning': 'warning',
            'info': 'info'
        };
        return iconMap[notificationType] || 'info';
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('최대 재연결 시도 횟수를 초과했습니다.');
        }
    }
    
    bindEvents() {
        // 브라우저 알림 권한 요청
        this.requestNotificationPermission();
        
        // 페이지 포커스 시 WebSocket 재연결 확인
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && (!this.socket || this.socket.readyState === WebSocket.CLOSED)) {
                this.connectWebSocket();
            }
        });
    }
    
    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            console.log('브라우저 알림 권한:', permission);
        }
    }
    
    // WebSocket 메시지 전송
    sendMessage(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        }
    }
    
    // 알림 읽음 처리 (WebSocket을 통해)
    markNotificationReadWS(notificationId) {
        this.sendMessage({
            type: 'mark_read',
            notification_id: notificationId
        });
    }
    
    // 모든 알림 읽음 처리 (WebSocket을 통해)
    markAllNotificationsReadWS() {
        this.sendMessage({
            type: 'mark_all_read'
        });
    }
}
