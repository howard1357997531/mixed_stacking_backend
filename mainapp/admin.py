from django.contrib import admin
from .models import workOrder, aiWorkOrder

@admin.register(workOrder)
class workOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'file_name', 'hasAiTrained', 'createdAt')

@admin.register(aiWorkOrder)
class aiWorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'worklist_id', 'list_order', 'createdAt')

