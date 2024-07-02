from django.urls import path
from . import views

urlpatterns = [
    path('', views.url_form, name='url_form'),
    path('register/', views.register, name='register'),
    path('whitelist/', views.WhitelistView.as_view(), name='whitelist'),
    path('report/', views.report, name='report'),
    path('search/', views.search, name='search'),  # 검색 결과 페이지 URL
]
