from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .views import sensor_location

urlpatterns = [
  path('', views.index,  name='index'),
  path('tables/', views.tables, name='tables'),
  path('live_analytics/', views.live_analytics, name='live_analytics'),
  path('map/', views.map, name='map'),
  path('wra_map/', views.wra_map, name='wra_map'),
  path('environmental_statistics/', views.environmental_statistics, name='environmental_statistics'),
  path('report/', views.report, name='report'),
  path('contribute/',views.contribute,name='contribute'),

  path('sensor_dataset/', views.sensor_dataset, name='sensor_dataset'),
  path('sensor_location/', views.sensor_location, name='sensor_location'),

  path('weather_data/', views.weather_data, name='weather_data'),
  path('calculate_weather/', views.calculate_weather, name='calculate_weather'),


  path('get_day_avg_sensor_data/', views.get_day_avg_sensor_data, name='get_day_avg_sensor_data'),
  path('average_reading_past_week/', views.average_reading_past_week, name='average_reading_past_week'),







]


