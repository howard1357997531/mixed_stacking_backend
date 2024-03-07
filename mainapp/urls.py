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
    path('filterOrderData/', views.filterOrderData, name="filterOrderData"),
    path('editOrder/', views.editOrder, name="editOrder"),
    path('deleteOrder/', views.deleteOrder, name="deleteOrder"),
    path('executeRobot/', views.executeRobot, name="executeRobot"),
    path('robotSetting/', views.robotSetting, name="robotSetting"),
    path('executeRobotAutoRetrieve/', views.executeRobotAutoRetrieve, name="executeRobotAutoRetrieve"),
    path('executeRobotFinish/', views.executeRobotFinish, name="executeRobotFinish"),
    path('executingOrder/', views.executingOrder, name="executingOrder"),
    path('getMultipleOrderData/', views.getMultipleOrderData, name="getMultipleOrderData"),
    path('createMultipleOrder/', views.createMultipleOrder, name="createMultipleOrder"),
    path('deleteMultipleOrder/', views.deleteMultipleOrder, name="deleteMultipleOrder"),
    path('history_record/', views.history_record, name="history_record"),
    path('filter_history_record/', views.filter_history_record, name="filter_history_record"),
    

    # qrcode
    # path('getOrderXlsxFile/', views.getOrderXlsxFile, name="getOrderXlsxFile"),
    # path('getQRcodeFromCamera/', views.getQRcodeFromCamera, name="getQRcodeFromCamera"),
    # path('getQRcodeDataFromDatabase/', views.getQRcodeDataFromDatabase, name="getQRcodeDataFromDatabase"),
]