from django.urls import path
from . import views

urlpatterns = [
    path('control-robot/', views.controlRobot, name="control-robot"),
    path('read-txt/', views.readTxt, name="read-txt"),
    path('createWorkOrder/', views.createWorkOrder, name="createWorkOrder"),
    path('getWorkOrderData/', views.getWorkOrderData, name="getWorkOrderData"),
    path('aiCalculate/', views.aiCalculate, name="aiCalculate"),
    path('getAiWorkOrderData/', views.getAiWorkOrderData, name="getAiWorkOrderData"),
    # step2
    path('uploadCsv/', views.uploadCsv, name="uploadCsv"),
    path('aiTraining/', views.aiTraining, name="aiTraining"),
    path('getOrderData/', views.getOrderData, name="getOrderData"),
    path('executeRobot/', views.executeRobot, name="executeRobot"),
    path('robotSetting/', views.robotSetting, name="robotSetting"),
    path('executingOrder/', views.executingOrder, name="executingOrder"),
    path('getMultipleOrderData/', views.getMultipleOrderData, name="getMultipleOrderData"),
    path('createMultipleOrder/', views.createMultipleOrder, name="createMultipleOrder"),
    path('deleteMultipleOrder/', views.deleteMultipleOrder, name="deleteMultipleOrder"),
    

    # qrcode
    # path('getOrderXlsxFile/', views.getOrderXlsxFile, name="getOrderXlsxFile"),
    # path('getQRcodeFromCamera/', views.getQRcodeFromCamera, name="getQRcodeFromCamera"),
    # path('getQRcodeDataFromDatabase/', views.getQRcodeDataFromDatabase, name="getQRcodeDataFromDatabase"),
]