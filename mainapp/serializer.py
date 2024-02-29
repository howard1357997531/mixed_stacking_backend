from rest_framework.serializers import ModelSerializer, SerializerMethodField
from .models import workOrder, aiWorkOrder, Order, OrderItem, MultipleOrder, MultipleOrderItem, HistoryRecord

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
    # 需要在 model.py 寫 relative_name
    orderItem = OrderItemSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = ("id", "name", "unique_code", "aiTraining_order", "aiLayer_order", "aiTraining_state", 
                  "createdAt", "modifiedAt", "is_today_latest", "orderItem")

class MultipleOrderItemSerializer(ModelSerializer):
    order = SerializerMethodField(read_only=True)

    class Meta:
        model = MultipleOrderItem
        fields = ("order",)

    def get_order(self, obj):
        order = Order.objects.filter(id=obj.order.id).first()
        serializer = OrderSerializer(order)
        return serializer.data

class MultipleOrderSerializer(ModelSerializer):
    multipleOrder = MultipleOrderItemSerializer(many=True, required=False)

    class Meta:
        model = MultipleOrder
        fields = ("id", "name", "orderSelectId_str", "is_today_latest", "createdAt", "modifiedAt", "multipleOrder")

class HistoryRecordSerializer(ModelSerializer):
    class Meta:
        model = HistoryRecord
        fields = ("id", "name", "order_id", "insert_index", "reset_index", "start_time", "end_time", "createdAt")
