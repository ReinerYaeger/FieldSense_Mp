from django.urls import path
from . import consumer

websocket_urlpatterns = [
    path('ws/socket-server/', consumer.DataConsumer.as_asgi()),
    path('ws/map-data-socket/', consumer.MapDataConsumer.as_asgi())
]
