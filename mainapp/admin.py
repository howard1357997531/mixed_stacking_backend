from django.contrib import admin
from .models import workOrder, aiWorkOrder, Order, OrderItem

@admin.register(workOrder)
class workOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'file_name', 'hasAiTrained', 'createdAt')

@admin.register(aiWorkOrder)
class aiWorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'worklist_id', 'list_order', 'createdAt')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unique_code', 'aiTraining_state', 'createdAt')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'width', 'height', 'count')

