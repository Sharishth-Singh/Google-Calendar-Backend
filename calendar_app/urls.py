from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Default route
    path('add-events/', views.add_events, name='add_events'),
    path('get_events/', views.get_events, name='get_events'),  # GET to fetch today's events
]

