from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Default route
    path('add-events/', views.add_events, name='add_events'),
]

