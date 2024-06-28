from django.urls import path
from . import views

urlpatterns = [
    path('start_crawl/', views.start_crawl, name='start_crawl'),
    path('classify_urls/', views.classify_urls, name='classify_urls'),  # 새로운 URL 패턴 추가
    path('success/', views.success, name='success'),
]
