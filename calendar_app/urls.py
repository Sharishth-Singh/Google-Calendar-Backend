from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Default route
    path('add-events/', views.add_events, name='add_events'),
    path('get_events/', views.get_events, name='get_events'),  # GET to fetch today's events
    path('get-file-content/', views.get_file_content, name='get_file_content'),  # GET to fetch today's events
    path('update-file-content/', views.update_file_content, name='update_file_content'),  # GET to fetch today's events
    path('questions/', views.fetch_pwonlyias_questions, name='fetch_pwonlyias_questions'),  # GET to fetch today's events
    path('test_test/',views.fetch_github_api_data, name='test_test'),  # GET to fetch today's events
]

