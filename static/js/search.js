// static/js/search.js
class SearchManager {
    constructor() {
        this.searchInput = null;
        this.searchDropdown = null;
        this.searchTimeout = null;
        this.currentResults = [];
        this.selectedIndex = -1;
        
        this.init();
    }
    
    init() {
        this.bindElements();
        this.bindEvents();
    }
    
    bindElements() {
        this.searchInput = document.querySelector('#global-search-input');
        this.searchDropdown = document.querySelector('#search-dropdown');
    }
    
    bindEvents() {
        if (!this.searchInput) return;
        
        this.searchInput.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });
        
        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });
        
        this.searchInput.addEventListener('focus', () => {
            if (this.currentResults.length > 0) {
                this.showDropdown();
            }
        });
        
        // 외부 클릭 시 드롭다운 숨기기
        document.addEventListener('click', (e) => {
            if (!this.searchInput.contains(e.target) && !this.searchDropdown?.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }
    
    handleInput(query) {
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        if (query.length < 2) {
            this.hideDropdown();
            return;
        }
        
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, 300);
    }
    
    async performSearch(query) {
        try {
            const response = await fetch(`/search/quick/?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.currentResults = data.results;
            this.selectedIndex = -1;
            this.renderResults();
            this.showDropdown();
            
        } catch (error) {
            console.error('검색 오류:', error);
            this.hideDropdown();
        }
    }
    
    renderResults() {
        if (!this.searchDropdown) return;
        
        if (this.currentResults.length === 0) {
            this.searchDropdown.innerHTML = `
                <div class="px-4 py-3 text-center text-gray-500 dark:text-gray-400">
                    검색 결과가 없습니다.
                </div>
            `;
            return;
        }
        
        const resultsHTML = this.currentResults.map((result, index) => `
            <div class="search-result-item ${index === this.selectedIndex ? 'bg-gray-100 dark:bg-gray-600' : ''}" 
                 data-index="${index}" 
                 data-url="${result.url}">
                <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-600 flex items-center justify-center">
                        <i class="${result.icon} text-sm text-gray-600 dark:text-gray-300"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="font-medium text-gray-900 dark:text-white truncate">${result.title}</p>
                        <p class="text-sm text-gray-500 dark:text-gray-400 truncate">${result.subtitle}</p>
                    </div>
                    <div class="text-xs text-gray-400 dark:text-gray-500">
                        ${this.getTypeLabel(result.type)}
                    </div>
                </div>
            </div>
        `).join('');
        
        const footerHTML = `
            <div class="p-3 border-t border-gray-200 dark:border-gray-700">
                <button onclick="window.location.href='/search/?q=${encodeURIComponent(this.searchInput.value)}'" 
                        class="w-full text-left text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
                    <i class="fas fa-search mr-2"></i>
                    모든 검색 결과 보기
                </button>
            </div>
        `;
        
        this.searchDropdown.innerHTML = resultsHTML + footerHTML;
        
        // 결과 항목 클릭 이벤트
        this.searchDropdown.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const url = item.dataset.url;
                if (url) {
                    window.location.href = url;
                }
            });
        });
    }
    
    handleKeyDown(e) {
        if (!this.searchDropdown || this.currentResults.length === 0) return;
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.currentResults.length - 1);
                this.updateSelection();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.updateSelection();
                break;
                
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0 && this.selectedIndex < this.currentResults.length) {
                    const selectedResult = this.currentResults[this.selectedIndex];
                    window.location.href = selectedResult.url;
                } else {
                    // 전체 검색 결과 페이지로 이동
                    window.location.href = `/search/?q=${encodeURIComponent(this.searchInput.value)}`;
                }
                break;
                
            case 'Escape':
                this.hideDropdown();
                this.searchInput.blur();
                break;
        }
    }
    
    updateSelection() {
        const items = this.searchDropdown.querySelectorAll('.search-result-item');
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('bg-gray-100', 'dark:bg-gray-600');
            } else {
                item.classList.remove('bg-gray-100', 'dark:bg-gray-600');
            }
        });
    }
    
    showDropdown() {
        if (this.searchDropdown) {
            this.searchDropdown.style.display = 'block';
        }
    }
    
    hideDropdown() {
        if (this.searchDropdown) {
            this.searchDropdown.style.display = 'none';
        }
        this.selectedIndex = -1;
    }
    
    getTypeLabel(type) {
        const labels = {
            'product': '상품',
            'order': '주문',
            'category': '카테고리',
            'customer': '고객'
        };
        return labels[type] || type;
    }
}
