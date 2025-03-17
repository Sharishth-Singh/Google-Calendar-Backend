from django.urls import path
from . import views

urlpatterns = [
    path('add-events/', views.add_events, name='add_events'),
]

