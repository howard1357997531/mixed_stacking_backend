from rest_framework.serializers import ModelSerializer
from .models import workOrder, aiWorkOrder

class workOrderSerializer(ModelSerializer):
    class Meta:
        model = workOrder
        fields = "__all__"

class aiWorkOrderSerializer(ModelSerializer):
    class Meta:
        model = aiWorkOrder
        fields = "__all__"
