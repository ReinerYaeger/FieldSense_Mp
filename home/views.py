from datetime import timedelta
from django.db.models import Max
from django.db.models.functions import TruncMonth, ExtractMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from django.core.serializers import serialize
from datetime import datetime, timedelta

from .models import *

import openmeteo_requests

import requests_cache
import pandas as pd
import numpy as np
from retry_requests import retry


def index(request):
    username = "Guest"

    if request.user.is_authenticated:
        username = request.user.first_name

    context = {
        'segment': 'index',
        'username': username,
        'sensor_group_names': get_sensor_group_names(),

    }
    return render(request, "pages/index.html", context)


def calculate_weather(request):
    print("Calculating Qeatrher")
    weather_data_dict = weather_data()
    if request.method == 'POST':
        x = request.POST.get('x')
        y = request.POST.get('y')
        weather_data_dict = weather_data(x, y)

        # precipitation_probability = np.mean(weather_data_dict["daily_data"]["precipitation_probability_max"])

        # evapotranspiration = np.mean(weather_data_dict["daily_data"]["et0_fao_evapotranspiration"])


    return JsonResponse(weather_data_dict)


def tables(request):
    context = {
        'segment': 'tables',
        'username': 'One',
    }
    return render(request, "pages/dynamic-tables.html", context)


def live_analytics(request):

    context = {
        'segment': 'live_analytics',
        'username': 'One',
        'sensor_group': get_sensor_group_names(),
    }

    return render(request, "pages/live_analysis.html", context)


def map(request):
    context = {
        'segment': 'map',
        'username': 'One',
        # "sensor_data": serialize('geojson', SensorCollectedData.objects.all()),
    }

    return render(request, "pages/arc_gis_map.html", context)


def wra_map(request):
    context = {
        'segment': 'map',
        'username': 'One',
        # "sensor_data": serialize('geojson', SensorCollectedData.objects.all()),
    }

    return render(request, "pages/wra_map.html", context)


def environmental_statistics(request):
    context = {
        'segment': 'environmental_statistics',
        'username': 'One',
    }
    return render(request, "pages/environmental_statistics.html", context)


def contribute(request):
    context = {

    }

    return render(request,"pages/application_sensor_group.html",context)


def report(request):
    context = {
        'segment': 'report',
        'username': 'One',
    }
    return render(request, "pages/report.html", context)


def sensor_location(request):
    dataset = serialize('geojson', SensorGroup.objects.all())
    return HttpResponse(dataset, content_type='application/json')


def sensor_dataset(request):
    # Get unique latest sensor names and corresponding data with datetime
    latest_sensor_data = SensorCollectedData.objects.values('sensor_name').annotate(
        latest_date=Max('sensor_date_time')).order_by()

    # Initialize an empty list to store serialized data
    serialized_data = []

    # Loop through unique latest sensor data
    for sensor_data in latest_sensor_data:
        sensor_name = sensor_data['sensor_name']
        latest_date = sensor_data['latest_date']
        # Get the corresponding SensorCollectedData object
        sensor_data_obj = SensorCollectedData.objects.filter(sensor_name=sensor_name,
                                                             sensor_date_time=latest_date).first()
        if sensor_data_obj:
            # Serialize the object
            serialized_obj = serialize('geojson', [sensor_data_obj])
            serialized_data.append(serialized_obj)

    # Combine all serialized data
    dataset = '[' + ','.join(serialized_data) + ']'

    return HttpResponse(dataset, content_type='application/json')


def weather_data(x=18.0182222, y=-76.7440833):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": x,
        "longitude": y,
        "hourly": ["temperature_2m", "precipitation", "evapotranspiration", "et0_fao_evapotranspiration",
                   "wind_speed_10m", "temperature_80m", "soil_temperature_6cm"]
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    for response in responses:


        print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
        print(f"Elevation {response.Elevation()} m asl")
        print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
        print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
    hourly_evapotranspiration = hourly.Variables(2).ValuesAsNumpy()
    hourly_et0_fao_evapotranspiration = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(4).ValuesAsNumpy()
    hourly_temperature_80m = hourly.Variables(5).ValuesAsNumpy()
    hourly_soil_temperature_6cm = hourly.Variables(6).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["evapotranspiration"] = hourly_evapotranspiration
    hourly_data["et0_fao_evapotranspiration"] = hourly_et0_fao_evapotranspiration
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["temperature_80m"] = hourly_temperature_80m
    hourly_data["soil_temperature_6cm"] = hourly_soil_temperature_6cm

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    temperature_2m = hourly_dataframe[['date', 'temperature_2m']].to_json(orient='records', date_format='iso')
    precipitation = hourly_dataframe[['date', 'precipitation']].to_json(orient='records', date_format='iso')
    evapotranspiration = hourly_dataframe[['date', 'evapotranspiration']].to_json(orient='records', date_format='iso')
    et0_fao_evapotranspiration = hourly_dataframe[['date', 'et0_fao_evapotranspiration']].to_json(orient='records',
                                                                                                  date_format='iso')
    wind_speed_10m = hourly_dataframe[['date', 'wind_speed_10m']].to_json(orient='records', date_format='iso')
    soil_temperature_6cm = hourly_dataframe[['date', 'soil_temperature_6cm']].to_json(orient='records',
                                                                                      date_format='iso')

    weather_data_dict = {
        'temperature_2m': temperature_2m,
        'evapotranspiration': evapotranspiration,
        'et0_fao_evapotranspiration': et0_fao_evapotranspiration,
        'precipitation': precipitation,
        'wind_speed_10m': wind_speed_10m,
        'soil_temperature_6cm': soil_temperature_6cm,
    }

    return weather_data_dict


def get_day_avg_sensor_data(request):
    latest_sensor_data = SensorCollectedData.objects.values('sensor_name').annotate(
        latest_date=Max('sensor_date_time')).order_by()

    serialized_data = []
    sensor_data_sum = 0
    sensor_count = 0

    for sensor_data in latest_sensor_data:
        sensor_name = sensor_data['sensor_name']
        latest_date = sensor_data['latest_date']
        sensor_data_objs = SensorCollectedData.objects.filter(sensor_name=sensor_name,
                                                              sensor_date_time=latest_date).all()
        for obj in sensor_data_objs:
            sensor_data_sum += obj.sensor_data
            sensor_count += 1

    if sensor_count > 0:
        daily_avg_sensor_data = sensor_data_sum / sensor_count
        response_data = '{{"average_sensor_data": {}}}'.format(daily_avg_sensor_data)
    else:
        response_data = '{"error": "No sensor data found"}'

    return HttpResponse(response_data, content_type='application/json')


def get_sensor_group_names():
    unique_sensor_groups = SensorGroup.objects.values('sensor_group_name', 'sensor_group_location')

    return unique_sensor_groups


def average_reading_past_week(request):
    # Get today's date
    today = datetime.now().date()

    # Initialize lists to store dates and corresponding average readings
    dates = []
    average_readings = []

    # Query average readings for the past 7 days
    for i in range(7):
        # Calculate the date for the current iteration
        date = today - timedelta(days=i)

        # Query the average sensor data for the current date
        avg_reading = SensorCollectedData.objects.filter(sensor_date_time__date=date).aggregate(avg_reading=Avg('sensor_data'))['avg_reading']
        if avg_reading == None:
            avg_reading = 0
        # Store the date and average reading
        dates.append(date.strftime('%Y-%m-%d'))
        average_readings.append(avg_reading)

    # Return data as JSON
    return JsonResponse({'dates': dates, 'average_readings': average_readings})
