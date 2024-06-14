from django.urls import path
from . import views

urlpatterns = [
    path('process_url/', views.process_url, name='process_url'),
]
