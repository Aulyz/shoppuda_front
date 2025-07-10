# search/urls.py
from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    # 검색 결과 페이지
    path('', views.SearchView.as_view(), name='results'),
    
    # 검색 API
    path('api/', views.search_api, name='api'),
    
    # 빠른 검색 API (드롭다운용)
    path('quick/', views.quick_search_api, name='quick_api'),
]
