from django.urls import path, re_path
from .consumers import RobotControlConsumers

websocket_urlpatterns = [
    path('ws/RobotControlConsumers/', RobotControlConsumers.as_asgi())
]

# websocket_urlpatterns = [
#     re_path(r'ws/RobotControlConsumers/$', RobotControlConsumers.as_asgi()),
# ]
