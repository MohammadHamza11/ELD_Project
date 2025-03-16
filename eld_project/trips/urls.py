from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_trip, name='create_trip'),
    path('', views.list_trips, name='list_trips'),
    path('<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('<int:trip_id>/update/', views.update_trip, name='update_trip'),
    path('<int:trip_id>/delete/', views.delete_trip, name='delete_trip'),
    path('<int:trip_id>/pdf/', views.generate_trip_pdf, name='generate_trip_pdf'),
    path('<int:trip_id>/image/', views.generate_trip_image, name='generate_trip_image'),
    path('<int:trip_id>/map/', views.trip_map_data, name='trip_map_data'),
]
