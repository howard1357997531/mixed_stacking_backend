from django.contrib import admin
from .models import workOrder, aiWorkOrder, Order, OrderItem, MultipleOrder, MultipleOrderItem, HistoryRecord, ExecutingOrder

@admin.register(workOrder)
class workOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'file_name', 'hasAiTrained', 'createdAt')

@admin.register(aiWorkOrder)
class aiWorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'worklist_id', 'list_order', 'createdAt')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unique_code', 'aiTraining_order', 'aiTraining_state', 'is_today_latest', 'createdAt')
    # list_display = [field.name for field in Order._meta.fields]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'width', 'height', 'quantity')

@admin.register(MultipleOrder)
class MultipleOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'orderSelectId_str', 'is_today_latest', 'createdAt')

@admin.register(MultipleOrderItem)
class MultipleOrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'multiple_order', 'order')

@admin.register(HistoryRecord)
class HistoryRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'order_id', 'insert_index', 'reset_index', 'reset_all_index', 'start_time', 'end_time', 'is_new')

@admin.register(ExecutingOrder)
class ExecutingOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_id', 'order_name', 'order_type', 'executing_index', 'finished', 'createdAt')

# @admin.register(QRcodeExecute)
# class QRcodeExecuteAdmin(admin.ModelAdmin):
#     list_display = ('id', 'unique_code', 'is_execute')

