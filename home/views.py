import json
from django.utils import timezone
import psycopg2
from django.db.models import Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

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

    seven_days_ago = timezone.now() - timedelta(days=7)

    week_sensor_data = get_sensor_data_by_time(seven_days_ago)
    context = {
        'segment': 'index',
        'username': username,
        'sensor_group_names': get_sensor_group_names(),
        'week_sensor_data': week_sensor_data,
    }

    return render(request, "pages/index.html", context)


def get_sensor_data_by_time(date):
    data_points = SensorCollectedData.objects.filter(sensor_date_time__gte=date)[:10]
    data_json = serialize('json', data_points, fields=('sensor_data',))
    json_data = json.dumps(data_json)

    return json_data


# api
def historical_weather(request):
    print("Calculating Historical Weather")
    weather_data_dict = weather_historical_data()

    return JsonResponse(weather_data_dict)


def forecast_weather(request):
    print("Calculating Forcast")
    weather_forcast_dict = forecast_weather()

    return JsonResponse(weather_forcast_dict)


# api
def calculate_forecast_weather():
    print("Calculating Weather Forecast")
    weather_data_dict = weather_historical_data()

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

    return render(request, "pages/live_analysis_old.html", context)


def general_information(request):
    context = {
        'segment': 'general_information',
        'username': 'One',
        'sensor_group': get_sensor_group_names(),
    }

    return render(request, "pages/general_information.html", context)


def weather_forcast(request):
    context = {
        'segment': 'weather_forcast',
        'username': 'One',
        'sensor_group': get_sensor_group_names(),
    }

    return render(request, "pages/forecast.html", context)


# backend proceessing function
def generate_forcast(x=18.018254006, y=-76.744447946):
    # Setup the Open-Meteo API client with cache and retry on error
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 18.01825,
        "longitude": -76.74444,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "evapotranspiration",
                   "soil_temperature_0cm", "soil_moisture_0_to_1cm", "direct_radiation"]
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_evapotranspiration = hourly.Variables(3).ValuesAsNumpy()
    hourly_soil_temperature_0cm = hourly.Variables(4).ValuesAsNumpy()
    hourly_soil_moisture_0_to_1cm = hourly.Variables(5).ValuesAsNumpy()
    hourly_direct_radiation = hourly.Variables(6).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["evapotranspiration"] = hourly_evapotranspiration
    hourly_data["soil_temperature_0cm"] = hourly_soil_temperature_0cm
    hourly_data["soil_moisture_0_to_1cm"] = hourly_soil_moisture_0_to_1cm
    hourly_data["direct_radiation"] = hourly_direct_radiation

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    temperature_2m = hourly_dataframe[['date', 'temperature_2m']].to_json(orient='records', date_format='iso')
    relative_humidity_2m = hourly_dataframe[['date', 'relative_humidity_2m']].to_json(orient='records',
                                                                                      date_format='iso')
    precipitation = hourly_dataframe[['date', 'precipitation']].to_json(orient='records', date_format='iso')
    evapotranspiration = hourly_dataframe[['date', 'evapotranspiration']].to_json(orient='records', date_format='iso')
    soil_temperature_0cm = hourly_dataframe[['date', 'soil_temperature_0cm']].to_json(orient='records',
                                                                                      date_format='iso')
    soil_moisture_0_to_1cm = hourly_dataframe[['date', 'soil_moisture_0_to_1cm']].to_json(orient='records',
                                                                                          date_format='iso')
    direct_radiation = hourly_dataframe[['date', 'direct_radiation']].to_json(orient='records', date_format='iso')

    weather_data_dict = {
        'temperature_2m': temperature_2m,
        'evapotranspiration': evapotranspiration,
        'relative_humidity_2m': relative_humidity_2m,
        'precipitation': precipitation,
        'soil_temperature_0cm': soil_temperature_0cm,
        'soil_moisture_0_to_1cm': soil_moisture_0_to_1cm,
        'direct_radiation': direct_radiation,
    }

    print(temperature_2m)
    print(relative_humidity_2m)
    print(precipitation)
    print(evapotranspiration)
    print(soil_temperature_0cm)
    print(soil_moisture_0_to_1cm)
    print(direct_radiation)

    return JsonResponse(weather_data_dict, safe=False)


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


def connect_to_db():
    conn = psycopg2.connect(
        database="gisdb",
        host="localhost",
        user="django",
        password="root",
        port="5432"
    )
    conn.autocommit = True
    return conn


db_cursor = connect_to_db().cursor()


def contribute(request):
    context = {

    }

    if request.method == 'POST':
        if 'contribute_submit' in request.POST:
            username = request.POST.get('user_name')
            email = request.POST.get('email_address')
            phone_number = request.POST.get('phone_number')
            lat = request.POST.get('lat')
            long = request.POST.get('long')

            db_cursor.execute(
                """INSERT INTO public.user_requests(email, username, sensor_group_location, creation_date, phoneNumber)VALUES(%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s);""",
                (email, username, float(lat), float(long), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), phone_number))

    return render(request, "pages/contribute.html", context)

def live_analytics_frame(request):

    return render(request,"pages/live_analysis_frame.html")
def report(request):
    context = {
        'segment': 'report',
        'username': 'One',
        'sensor_group_names': get_sensor_group_names(),
    }

    if request.method == 'POST':
        if 'report_submit' in request.POST:
            past_days = request.POST.get('sensor_group_select')
            forecast_days = request.POST.get('forecast_select')

            selected_variables = request.POST.getlist('variable_select')
            print(selected_variables)

            report = generate_report(past_days, forecast_days, selected_variables)

            return render(request, "pages/report_generated.html", context)

    return render(request, "pages/report.html", context)


def generate_report(past_days, forecast_days, selected_variables):
    print("Calculating Report Data")
    weather_data_dict = generate_report_data(past_days, forecast_days, selected_variables)

    return JsonResponse(weather_data_dict)

def generate_report_data(past_days, forecast_days, selected_variables):
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 18.01825,
        "longitude": -76.74444,
        "hourly": selected_variables,
        "past_days": past_days,
        "forecast_days": forecast_days
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_evapotranspiration = hourly.Variables(3).ValuesAsNumpy()
    hourly_soil_temperature_0cm = hourly.Variables(4).ValuesAsNumpy()
    hourly_soil_moisture_0_to_1cm = hourly.Variables(5).ValuesAsNumpy()
    hourly_direct_radiation = hourly.Variables(6).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["evapotranspiration"] = hourly_evapotranspiration
    hourly_data["soil_temperature_0cm"] = hourly_soil_temperature_0cm
    hourly_data["soil_moisture_0_to_1cm"] = hourly_soil_moisture_0_to_1cm
    hourly_data["direct_radiation"] = hourly_direct_radiation

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    temperature_2m = hourly_dataframe[['date', 'temperature_2m']].to_json(orient='records', date_format='iso')
    precipitation = hourly_dataframe[['date', 'precipitation']].to_json(orient='records', date_format='iso')
    evapotranspiration = hourly_dataframe[['date', 'evapotranspiration']].to_json(orient='records',
                                                                                                  date_format='iso')
    relative_humidity_2m = hourly_dataframe[['date', 'relative_humidity_2m']].to_json(orient='records',
                                                                                      date_format='iso')
    soil_temperature_0cm = hourly_dataframe[['date', 'soil_temperature_0cm']].to_json(orient='records',
                                                                                                date_format='iso')
    direct_radiation = hourly_dataframe[['date', 'direct_radiation']].to_json(orient='records', date_format='iso')

    weather_data_dict = {
        'temperature_2m': temperature_2m,
        'evapotranspiration': evapotranspiration,
        'precipitation': precipitation,
        'soil_temperature_0cm': soil_temperature_0cm,
        'relative_humidity_2m': relative_humidity_2m,
        'direct_radiation': direct_radiation,
    }
    print(temperature_2m)
    print(evapotranspiration)
    print(precipitation)
    print(soil_temperature_0cm)
    print(relative_humidity_2m)
    print(direct_radiation)

    return weather_data_dict


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


def weather_historical_data(x=18.0182222, y=-76.7440833):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    today_date = datetime.now().strftime("%Y-%m-%d")
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": x,
        "longitude": y,
        "start_date": str(seven_days_ago),
        "end_date": str(today_date),
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "et0_fao_evapotranspiration",
                   "soil_temperature_0_to_7cm", "direct_radiation"]
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_et0_fao_evapotranspiration = hourly.Variables(3).ValuesAsNumpy()
    hourly_soil_temperature_0_to_7cm = hourly.Variables(4).ValuesAsNumpy()
    hourly_direct_radiation = hourly.Variables(5).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["et0_fao_evapotranspiration"] = hourly_et0_fao_evapotranspiration
    hourly_data["soil_temperature_0_to_7cm"] = hourly_soil_temperature_0_to_7cm
    hourly_data["direct_radiation"] = hourly_direct_radiation

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    temperature_2m = hourly_dataframe[['date', 'temperature_2m']].to_json(orient='records', date_format='iso')
    precipitation = hourly_dataframe[['date', 'precipitation']].to_json(orient='records', date_format='iso')
    et0_fao_evapotranspiration = hourly_dataframe[['date', 'et0_fao_evapotranspiration']].to_json(orient='records',
                                                                                                  date_format='iso')
    relative_humidity_2m = hourly_dataframe[['date', 'relative_humidity_2m']].to_json(orient='records',
                                                                                      date_format='iso')
    soil_temperature_0_to_7cm = hourly_dataframe[['date', 'soil_temperature_0_to_7cm']].to_json(orient='records',
                                                                                                date_format='iso')
    direct_radiation = hourly_dataframe[['date', 'direct_radiation']].to_json(orient='records', date_format='iso')

    weather_data_dict = {
        'temperature_2m': temperature_2m,
        'et0_fao_evapotranspiration': et0_fao_evapotranspiration,
        'precipitation': precipitation,
        'soil_temperature_0_to_7cm': soil_temperature_0_to_7cm,
        'relative_humidity_2m': relative_humidity_2m,
        'direct_radiation': direct_radiation,
    }
    print(temperature_2m)
    print(et0_fao_evapotranspiration)
    print(precipitation)
    print(soil_temperature_0_to_7cm)
    print(relative_humidity_2m)
    print(direct_radiation)

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
        avg_reading = \
            SensorCollectedData.objects.filter(sensor_date_time__date=date).aggregate(avg_reading=Avg('sensor_data'))[
                'avg_reading']
        if avg_reading == None:
            avg_reading = 0
        # Store the date and average reading
        dates.append(date.strftime('%Y-%m-%d'))
        average_readings.append(avg_reading)

    # Return data as JSON
    return JsonResponse({'dates': dates, 'average_readings': average_readings})


## admin pages

def view_requests(request):
    customer_request = SensorGroup.objects.all()
    context = {
        'customer_request': customer_request,
    }

    return render(request, "pages/dynamic-tables.html", context)


def sgr_panel(request):
    sensor_group_list = SensorGroup.objects.all()
    context = {
        'sensor_group_list': sensor_group_list,
    }

    return render(request, "pages/sgr_panel.html", context)
