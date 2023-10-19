from rest_framework.serializers import ModelSerializer
from .models import workOrder, aiWorkOrder, Order, OrderItem

class workOrderSerializer(ModelSerializer):
    class Meta:
        model = workOrder
        fields = "__all__"

class aiWorkOrderSerializer(ModelSerializer):
    class Meta:
        model = aiWorkOrder
        fields = "__all__"

class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ("name", "width", "height", "depth", "quantity")

class OrderSerializer(ModelSerializer):
    orderItem = OrderItemSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = ("id", "name", "unique_code", "aiTraining_order", "aiTraining_state", "createdAt", "modifiedAt", "orderItem")