from django.urls import path
from . import views

urlpatterns = [
    path('', views.url_form, name='url_form'),
    path('register/', views.register, name='register'),
    path('whitelist/', views.WhitelistView.as_view(), name='whitelist'),
    path('report/', views.report, name='report'),
    path('submit_report/', views.submit_report, name='submit_report'),  # 신고 제출을 처리하는 URL
    path('get_search_results/', views.get_search_results, name='get_search_results'),  # 검색 결과를 반환하는 URL
    path('search/', views.search, name='search'),  # 검색 결과 페이지 URL
    path('process_url/', views.process_url, name='process_url'),  # URL을 처리하는 뷰
]
