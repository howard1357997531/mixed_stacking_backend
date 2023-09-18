from django.urls import path
from . import views

urlpatterns = [
    path('control-robot/', views.controlRobot, name="control-robot"),
    path('read-txt/', views.readTxt, name="read-txt"),
    path('createWorkOrder/', views.createWorkOrder, name="createWorkOrder"),
    path('getWorkOrderData/', views.getWorkOrderData, name="getWorkOrderData"),
    path('aiCalculate/', views.aiCalculate, name="aiCalculate"),
    path('getAiWorkOrderData/', views.getAiWorkOrderData, name="getAiWorkOrderData"),
    #-----
    path('uploadCsv/', views.uploadCsv, name="uploadCsv"),
    path('getOrderData/', views.getOrderData, name="getOrderData"),
]