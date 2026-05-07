from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("production/", views.production, name="production"),
    path("reception/", views.reception, name="reception"),
    path("expedition/", views.expedition, name="expedition"),
    path("stock/", views.stock, name="stock"),
]
