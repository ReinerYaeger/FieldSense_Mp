import asyncio
import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Avg
from .models import SensorCollectedData
from .views import calculate_weather

@sync_to_async
def get_avg_sensor_data(sensor_name):
    avg_data = SensorCollectedData.objects.filter(sensor_name=sensor_name).aggregate(Avg('sensor_data'))
    return avg_data['sensor_data__avg'] if avg_data['sensor_data__avg'] is not None else 0.0


@sync_to_async
def get_avg_sensor_data_per_group():
    sensor_groups = SensorCollectedData.objects.values_list('sensor_group_name', flat=True).distinct()

    avg_data_per_group = []
    for group in sensor_groups:
        avg_data = SensorCollectedData.objects.filter(sensor_group_name=group).aggregate(Avg('sensor_data'))
        avg_data_value = avg_data['sensor_data__avg'] if avg_data['sensor_data__avg'] is not None else 0.0
        avg_data_per_group.append({'group_name': group, 'avg_sensor_data': avg_data_value})

    return avg_data_per_group



@sync_to_async
def get_latest_sensor_data(sensor_name):
    try:
        latest_data = SensorCollectedData.objects.filter(sensor_name=sensor_name).latest('sensor_date_time')
        return latest_data
    except SensorCollectedData.DoesNotExist:
        return None


class DataConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

        sensor_names = ['A0', 'A1', 'A2']

        while True:
            avg_data = {}

            for sensor_name in sensor_names:
                avg_data[sensor_name] = await get_avg_sensor_data(sensor_name)

            avg_data_avg = sum(avg_data.values()) / len(avg_data) if avg_data else 0.0

            avg_data_per_group = await get_avg_sensor_data_per_group()

            latest_data = await get_latest_sensor_data('A0')
            if latest_data:
                sensor_data = latest_data.sensor_data
                sensor_date_time = latest_data.sensor_date_time

                await self.send(
                    json.dumps({
                        'type': 'LSR',
                        'label': sensor_date_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'avg_sensor_data': avg_data_avg,
                        'avg_sensor_per_group': avg_data_per_group,
                        'sensor_group_name': "University of Technology",
                    })
                )

            await asyncio.sleep(5)


class MapDataConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

        sensor_names = ['A0', 'A1', 'A2']
        avg_data = {}

        for sensor_name in sensor_names:
            avg_data[sensor_name] = await get_avg_sensor_data(sensor_name)

        avg_data_avg = sum(avg_data.values()) / len(avg_data) if avg_data else 0.0

        avg_data_per_group = await get_avg_sensor_data_per_group()

        latest_data = await get_latest_sensor_data('A0')
        if latest_data:
            sensor_data = latest_data.sensor_data
            sensor_date_time = latest_data.sensor_date_time

            await self.send(
                json.dumps({
                    'type': 'LSR',
                    'label': sensor_date_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'avg_sensor_data': avg_data_avg,
                    'avg_sensor_per_group': avg_data_per_group,
                    'sensor_group_name': "University of Technology",
                })
            )


class WeatherData(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

        await self.send(
            json.dumps(calculate_weather())
        )
