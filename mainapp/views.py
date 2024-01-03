from django.shortcuts import render
from django.conf import settings
from django.db.models import Max
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializer import workOrderSerializer, aiWorkOrderSerializer, OrderSerializer, MultipleOrderSerilaizer, MultipleOrderItemSerilaizer
from .models import workOrder, aiWorkOrder, Order, OrderItem, MultipleOrder, MultipleOrderItem, ExecutingOrder

from .main_result_UI import ai_calculate
from .ai.main_result_2d import main as main_2d
from .ai.main_result_3d import main as main_3d
from datetime import datetime
from io import BytesIO
import random
import qrcode
import pandas as pd
import time
import uuid
import csv
import os
import io

from channels.layers import get_channel_layer
from web_socket.consumers import RobotControlConsumers
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

def websocket_robot_state(state):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {
            'type': 'robot_mode_change',
            'mode': state
        }
    )

def websocket_object_count(count):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {
            'type': 'object_count_change',
            'count': count
        }
    )

def websocket_object_name(name, nextName):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {
            'type': 'object_name_change',
            'name': name,
            'nextName': nextName,
        }
    )

def websocket_visual_result(visual_result, count, buffer_order=None, check_numberlist=None):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {
            'type': 'visual_result_change',
            'visual_result': visual_result,
            'visual_count': count,
            'buffer_order': buffer_order,
            'check_numberlist': check_numberlist,
        }
    )

def websocket_buffer(bufferquanlity):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {   
            'type': 'visual_buffer_change',
            "bufferquanlity": bufferquanlity
        }
    )


@api_view(['POST'])
def controlRobot(request):
    data = request.data
    data = data[0] if type(request.data) == list else data
    
    if data.get('mode') != 'reset':
        csv_id = data.get('id')
        # step1 ------------------------
        # order = workOrder.objects.filter(id=csv_id).first()
        # order_count = order.total_count
        # ------------------------------

        # step2 ------------------------
        order = Order.objects.filter(id=csv_id).first()
        order_count = len(order.aiTraining_order.split(','))
        # ------------------------------
        print(csv_id)
        print(order_count)

    robot_speed = int(data.get('speed')) if int(data.get('speed')) <= 100 else 100
    txt_path = os.path.join(settings.MEDIA_ROOT, 'output.txt')
    channel_layer = get_channel_layer()
    

    # if data.get('mode') == 'activate':
    #     main(csv_id, order_count)
    #     speed(50)
    # elif data.get('mode') == 'pause':
    #     robot_control('192.168.1.15', 10040).pause()
    # elif data.get('mode') == 're-activate':
    #     robot_control('192.168.1.15', 10040).start()
    # elif data.get('mode') == 'speed':
    #     speed(robot_speed)
    # elif data.get('mode') == 'reset':
    #     with open (txt_path, "w") as f:
    #         f.write(f'')
    #     robot_control('192.168.1.15',10040).pause()
    #     robot_control('192.168.1.15',10040).reset()

    # 1,準備抓取第1個物件,18,activate
    # step1 ------------------------
    # ai = aiWorkOrder.objects.filter(worklist_id=csv_id).first().list_order.split(',')
    # ------------------------------

    # step2 ------------------------
    ai = Order.objects.filter(id=csv_id).first().aiTraining_order.split(',')
    # ------------------------------
    if data.get('mode') == 'activate':
        time.sleep(2)
        for i, data in enumerate(ai, start=1):
            print(f'第{i}次')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f'{i},Grabbing No.{i} box,{data},prepare,1')
            async_to_sync(channel_layer.group_send)(
                'count_room',
                {
                    'type': 'robot_count_change',
                    'count': i
                }
            )
            time.sleep(3)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f'{i},Operating No.{i} box,{data},operate,1')
            time.sleep(3)
        with open (txt_path, "w", encoding='utf-8') as f:
            f.write(f'')
        print("inner activate")
    elif data.get('mode') == 'pause':
        print("inner pause")
    elif data.get('mode') == 're-activate':
        print("inner re-activate")
    elif data.get('mode') == 'speed':
        print("inner speed")
    elif data.get('mode') == 'reset':
        with open (txt_path, "w") as f:
            f.write(f'')
        print("inner reset")

    return Response({"robot"})

@api_view(['GET'])
def readTxt(request):
    txt_path = os.path.join(settings.MEDIA_ROOT, 'output.txt')
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return Response(content)

@api_view(['POST'])
def createWorkOrder(request):
    data = request.data
    
    csv_data = [
        ["box_id", "name", "width", "height", "depth", "quantity"],
        [1, "#7A", 70, 52, 40, data.get("7A")],
        [2, "#9", 86, 64, 46, data.get("9")],
        [3, "#16A", 70, 52, 32, data.get("16A")],
        [4, "#18A", 70, 52, 36, data.get("18A")],
        [5, "#13", 112, 50, 28, data.get("13")],
        [6, "#20", 106, 68, 26, data.get("20")],
        [7, "#22", 90, 52, 36, data.get("22")],
        [8, "#26", 144, 50, 40, data.get("26")],
        [9, "#29", 130, 50, 36, data.get("29")],
        [10, "#33", 88, 42, 36, data.get("33")],
        [11, "#35", 204, 92, 36, data.get("35")],
    ]

    # csv_data = [
    #     ["box_id", "name", "width", "height", "depth", "quantity"],
    #     [1, "#7A", 35, 26, 20, data.get("7A")],
    #     [2, "#9", 43, 32, 23, data.get("9")],
    #     [3, "#16A", 35, 26, 16, data.get("16A")],
    #     [4, "#18A", 35, 26, 18, data.get("18A")],
    #     [5, "#13", 56, 25, 14, data.get("13")],
    #     [6, "#20", 53, 34, 13, data.get("20")],
    #     [7, "#22", 45, 26, 18, data.get("22")],
    #     [8, "#26", 72, 25, 20, data.get("26")],
    #     [9, "#29", 65, 25, 18, data.get("29")],
    #     [10, "#33", 44, 21, 18, data.get("33")],
    #     [11, "#35", 102, 46, 18, data.get("35")],
    # ]

    unique_code = uuid.uuid4().hex
    unique_code_exist = Order.objects.filter(unique_code=unique_code)
    while unique_code_exist:
        unique_code = uuid.uuid4().hex
        unique_code_exist = Order.objects.filter(unique_code=unique_code)
        if unique_code_exist is None:
            break
    
    today = datetime.now()
    today_order = Order.objects.filter(createdAt__year=today.year, createdAt__month=today.month,
            createdAt__day=today.day)
    if today_order.exists():
        today_order.update(is_today_latest=False)

    csv_file_content = io.StringIO()
    csv_writer = csv.writer(csv_file_content, lineterminator='\n')
    for row in csv_data:
        csv_writer.writerow(row)

    order = Order.objects.create(
                name=data.get("name"),
                unique_code=unique_code)
    
    order.csv_file.save(f'{unique_code}.csv', ContentFile(csv_file_content.getvalue()))
    csv_file_content.close()

    for i, data in enumerate(csv_data, start=1):
        if i == 1:
            continue
        OrderItem.objects.create(
            order = order,
            name = data[1].replace('外箱', ''),
            width = data[2],
            height = data[3],
            depth = data[4],
            quantity = int(data[5])
        )
    return Response({'ok'})

@api_view(['GET'])
def getWorkOrderData(request):
    order = workOrder.objects.all().order_by('-id')
    serializer = workOrderSerializer(order, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def aiCalculate(request):
    worklist_id = request.data.get("id")
    t1 = time.time()
    # activate_cal(worklist_id, unique_code="", step=1)
    t2 = time.time()
    training_time = round(t2-t1, 3)
    ai_csvfile_path = os.path.join(settings.MEDIA_ROOT, f'Figures_{worklist_id}', f'box_positions_final.csv')
    ai_df = pd.read_csv(ai_csvfile_path)
    ai_list = ai_df['matched_box_name'].tolist()
    ai_str = ','.join([ai.replace('#', '').replace('外箱', '') for ai in ai_list])
    work_order = workOrder.objects.filter(id=int(worklist_id)).first()
    work_order.hasAiTrained = True
    work_order.save()
    aiWorkOrder.objects.create(
        name = work_order.name,
        worklist_id = worklist_id,
        list_order = ai_str,
        training_time = training_time
    )

    return Response({"worklist_id": worklist_id, "list_order": ai_str, "training_time": training_time})
    # return Response({"worklist_id": worklist_id,  "training_time": training_time})

# ---------------------
import threading
from queue import Queue
import random
import copy

TEST_RESET = False
TEST_RAUSE = False

class Robot_test():
    def __init__(self, order_count, order_list, isFinish_queue):
        self.time_count = 1
        self.supply = True
        self.camera_detect = True
        self.order_count = order_count
        self.order_list = order_list
        self.isFinish_queue = isFinish_queue
        self.detect_count = 1             # 視覺偵測記數
        self.new_round_random_count = 1   # 每一輪視覺偵測記數(新一輪都會重置為1)
        self.has_error_detect_list = []

    def supply_check(self):
        while self.supply and not TEST_RESET:
            if self.camera_detect:
                # 一開始先給隨機偵測數量，後面給的數量不會低於前面數量
                self.new_round_random_count = random.randint(self.new_round_random_count, 4)
                detect_list = self.order_list[self.detect_count - 1: self.detect_count - 1 + self.new_round_random_count]
                error_count = random.randint(0, len(detect_list) - 1)
                # 第一個固定對錯，後面隨機給對錯
                error_index = list(range(1, len(detect_list)))
                error_list_index = random.sample(error_index, error_count)
                # print(f'第{self.detect_count}次')
                # print('detect_list: ', detect_list)
                # print('first has_error_detect_list: ', self.has_error_detect_list)
                # print('error_count: ', error_count)
                # print('error_list_index: ', error_list_index)

                self.has_error_detect_list = copy.deepcopy(detect_list)  
                # print('copy has_error_detect_list: ', self.has_error_detect_list)

                # 第一個固定偵測對錯(基數全對，偶數三秒鐘後變對)
                # print('time_count: ', self.time_count)
                if self.detect_count % 2 == 0:
                    if self.time_count <= 4:
                        self.has_error_detect_list[0] = 'error'
                        websocket_robot_state('error')
                    else:
                        self.has_error_detect_list[0] = detect_list[0]
                        websocket_robot_state('correct')
                else: 
                    websocket_robot_state('correct')

                if len(error_list_index) != 0:
                    for index in error_list_index:
                        self.has_error_detect_list[index] = 'error' 
                # print('final has_error_detect_list:', self.has_error_detect_list)
                websocket_visual_result(self.has_error_detect_list, None)

                time.sleep(1.5)
                self.time_count += 1
                time.sleep(1.5)
            
    def robot(self):
        time.sleep(4)
        for i in range(1, self.order_count + 1):
            websocket_object_count(i)
            websocket_robot_state('prepare')
            print(f'準備操作第{i}個物件')
            
            while not TEST_RESET:
                if self.time_count == 4:
                    # 手臂向下夾取物件時會停止拍照，直到升到某個相機照不到的高度才會繼續拍照
                    self.camera_detect = False
                    print('停止偵測')
                    if self.detect_count < self.order_count:
                        self.detect_count += 1

                    next_name = self.order_list[self.detect_count] if self.detect_count < self.order_count else ""
                    self.new_round_random_count = 1
                    self.has_error_detect_list = []
                    self.time_count = 1
                    time.sleep(1) if not TEST_RESET else time.sleep(0)
                    self.camera_detect = True
                    # 開始偵測之後再發下一個count，不然前台的detect result 還是上一個的
                    # 因為停止偵測之後就不再更新
                    websocket_visual_result(None, self.detect_count)
                    websocket_object_name(self.order_list[self.detect_count - 1], next_name)
                    print('開始偵測')
                    time.sleep(1) if not TEST_RESET else time.sleep(0)
                    websocket_robot_state('operate')
                    print('手臂操作中\n')
                    time.sleep(4) if not TEST_RESET else time.sleep(0)
                    break
        
        self.supply = False
        if TEST_RESET:
            self.isFinish_queue.put(False)
        else:
            self.isFinish_queue.put(True)

def robot_test(order_count, order_list, isFinish_queue):
    time.sleep(2)
    for i in range(1, order_count + 1):
        print(f'第{i}次')
        websocket_object_count(i)
        if i != 1:
            next_name = order_list[i] if i < order_count else ""
            websocket_object_name(order_list[i - 1], next_name)
        websocket_robot_state('detect')
        websocket_robot_state('prepare')
        time.sleep(5)

        if i % 2 == 0:
            websocket_robot_state('correct')
        else:
            websocket_robot_state('error')
            time.sleep(4)
            websocket_robot_state('correct')
        
        time.sleep(2)
        websocket_robot_state('operate')
        time.sleep(2)
        
        # if i == 1 :
        #     break
    isFinish_queue.put(True)
    websocket_robot_state('finish')

# from .arms.Yaskawa_function import Yaskawa_control
# from .arms.Yaskawa_function_buffer import Yaskawa_control as Yaskawa_control_buffer
from .arm_buffer.Yaskawa_function import Yaskawa_control as Yaskawa_control_buffer
# from .arm.kuka_function import Kuka_control
YASKAWA_ROBOT_BUFFER = None
YASKAWA_ROBOT = None
KUKA_ROBOT  = None

@api_view(['POST'])
def executeRobot(request):
    global YASKAWA_ROBOT_BUFFER, YASKAWA_ROBOT, KUKA_ROBOT
    try:
        orderId = int(request.data.get('orderId'))
        order = Order.objects.filter(id=orderId).first()
        order_list = order.aiTraining_order.split(',')
        order_count = len(order_list)
        isFinish_queue = Queue()
        
        # '''
        YASKAWA_ROBOT_BUFFER = Yaskawa_control_buffer('192.168.1.15', 10040)
        # YASKAWA_ROBOT = Yaskawa_control('192.168.1.15', 10040)
        # KUKA_ROBOT = Kuka_control()

        # demo1
        # thread1 = threading.Thread(target=YASKAWA_ROBOT.Robot_Demo1, args=(orderId, order_list, order_count, isFinish_queue))
        # thread1 = threading.Thread(target=KUKA_ROBOT.Robot_Demo, args=(orderId, order_list, order_count, isFinish_queue))
        # thread1.start()
        # thread1.join()

        # demo2
        # thread1 = threading.Thread(target=YASKAWA_ROBOT.Robot_Demo2, args=(orderId, order_list, order_count, isFinish_queue))
        # thread1.start()
        # time.sleep(2)
        # thread2 = threading.Thread(target=YASKAWA_ROBOT.thread2_supplycheck)
        # thread2.start()
        # thread1.join(); thread2.join()

        # demo3
        YASKAWA_ROBOT_BUFFER.dectect_open()
        thread1 = threading.Thread(target=YASKAWA_ROBOT_BUFFER.thread2_supplycheck)
        thread1.start()
        time.sleep(2)
        thread2 = threading.Thread(target=YASKAWA_ROBOT_BUFFER.Robot_Demo, args=(orderId, order_list, order_count, isFinish_queue))
        thread2.start()
        thread1.join(); thread2.join()
        '''
        # test
        global TEST_RESET, TEST_RAUSE
        TEST_RESET = False
        robot = Robot_test(order_count, order_list, isFinish_queue)
        # thread1 = threading.Thread(target=robot_test, args=(order_count, order_list, isFinish_queue))
        thread1 = threading.Thread(target=robot.robot)
        thread2 = threading.Thread(target=robot.supply_check)
        thread1.start()
        time.sleep(4.1)
        thread2.start()
        thread1.join(); thread2.join()
        # '''

        robot_state = "finish" if isFinish_queue.get() else "reset"
        print('python stop!!')
        
        return Response({"robot_state": robot_state}, status=status.HTTP_200_OK)
    except:
        return Response({'error_msg': '啟動手臂失敗'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def robotSetting(request):
    try:
        data = request.data
        mode = data.get('mode')
        # YASKAWA_ROBOT_BUFFER YASKAWA_ROBOT KUKA_ROBOT
        # ''' 
        if mode == 'pause':
            YASKAWA_ROBOT_BUFFER.pause()
        elif mode == 'unPause':
            YASKAWA_ROBOT_BUFFER.keepgo()
        elif mode == 'speedUp' or mode == 'speedDown':
            robot_speed = data.get('speed') + 10 if mode == "speedUp" else data.get('speed') - 10
            robot_speed = 100 if robot_speed > 100 else robot_speed
            robot_speed = 70 if robot_speed >= 70 else robot_speed
            YASKAWA_ROBOT_BUFFER.speed(robot_speed)
        elif mode == 'reset':
            YASKAWA_ROBOT_BUFFER.reset()
        '''
        # test
        global TEST_RESET, TEST_RAUSE
        if mode == 'pause':
            print(mode)
        elif mode == 'unPause':
            print(mode)
        elif mode == 'speedUp' or mode == 'speedDown':
            robot_speed = data.get('speed') + 10 if mode == "speedUp" else data.get('speed') - 10
            robot_speed = 100 if robot_speed > 100 else robot_speed
            print(mode, robot_speed)
        elif mode == 'reset':
            TEST_RESET = True
            print(mode)
        # '''
        return Response({}, status=status.HTTP_200_OK)
    except:
        return Response({'error_msg': '啟動手臂失敗'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POSt'])
def executingOrder(request):
    try:
        print(request.data)
        print(request.data.get('name'))
        print(request.data.get('allData'))
        return Response({}, status=status.HTTP_200_OK)
    except:
        return Response({'error_msg': "fail"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def getAiWorkOrderData(request):
    ai_order = aiWorkOrder.objects.all().order_by('-id')
    serializer = aiWorkOrderSerializer(ai_order, many=True)
    return Response(serializer.data)

# step 2
@api_view(['POST'])
def uploadCsv(request):
    # if 'csv_file' not in request.data:
    #     return Response({'message': '請提供有效的 CSV 檔案'})
    csv_file_length = int(request.data.get('csv_file_length'))
    
    try:
        for i in range(csv_file_length):
            csv_file = request.data.get(f'csv_file{i+1}')
            csv_name = request.data.get(f'csv_file_name{i+1}').replace('.csv', '')
            unique_code = uuid.uuid4().hex
            unique_code_exist = Order.objects.filter(unique_code=unique_code)

            while unique_code_exist:
                unique_code = uuid.uuid4().hex
                unique_code_exist = Order.objects.filter(unique_code=unique_code)
                if unique_code_exist is None:
                    break
            # 读取CSV文件内容并保存到变量中
            # 下面 order.save() 會讓文件指针指到最後
            # 若用 csv_file.seek(0) 雖然會指到開頭但只能讀一行又會跑到最尾
            csv_content = csv_file.read().decode('utf-8')

            # 如果用一次固定時間，然後對所有供單最後設為is_today_latest=true會發生問題
            # 因為有可能有過00:00(隔天)問題，可能要每存一次csv都要檢查一次時間
            today = datetime.now()
            today_order = Order.objects.filter(createdAt__year=today.year, createdAt__month=today.month, 
                        createdAt__day=today.day)
            today_order_has_latest = Order.objects.filter(createdAt__year=today.year, createdAt__month=today.month, 
                        createdAt__day=today.day, is_today_latest=True)
            
            if today_order_has_latest.exists():
                today_order.update(is_today_latest=False)

            order = Order.objects.create(
                name=csv_name,
                unique_code=unique_code,
                csv_file=csv_file)
            order.save()
            
            csv_reader = csv.reader(csv_content.splitlines())
            next(csv_reader)
            
            for reader in csv_reader:
                # print(reader)
                OrderItem.objects.create(
                    order = order,
                    name = reader[1].replace('外箱', ''),
                    width = reader[2],
                    height = reader[3],
                    depth = reader[4],
                    quantity = int(reader[5])
                )
    except Exception as e:
        print(f'Error: {str(e)}')
        return Response({'message': 'error'})
    return Response({'message': 'CSV 檔案解析成功', 'data': 2}, status=200)

@api_view(['POST'])
def aiTraining(request):
    try:
        # worklist_id = request.data.get("orderId")
        # order = Order.objects.filter(id=int(worklist_id)).first()        
        # # order.aiTraining_state = "is_training"
        # # order.save()
        # unique_code = order.unique_code
        
        # t1 = time.time()
        # '''
        # ai_calculate(worklist_id, unique_code)
        # '''
        # main_2d(worklist_id, unique_code)
        # main_3d(worklist_id, unique_code)
        # # '''
        # t2 = time.time()
        # training_time = round(t2-t1, 3)
        # '''
        # ai_csvfile_path = os.path.join(settings.MEDIA_ROOT, f'ai_figure/Figures_{worklist_id}', f'box_positions_final.csv')
        # '''
        # ai_csvfile_path = os.path.join(settings.MEDIA_ROOT, f'ai_figure/Figures_{worklist_id}', f'box_positions_layer.csv')
        # # '''
        # ai_df = pd.read_csv(ai_csvfile_path)
        # ai_list = ai_df['matched_box_name'].tolist()
        # aiResult_str = ','.join([ai.replace('#', '').replace('外箱', '') for ai in ai_list])
        
        # order.aiTraining_order = aiResult_str
        # order.aiTraining_state = "finish_training"
        # order.save()
        time.sleep(5)
        return Response({"aiResult_str": '1,2,3,4,5'}, status=status.HTTP_200_OK)
    except:
        return Response('request fail', status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def getOrderData(request):
    try:
        time.sleep(1)
        # order = Order.objects.get(id=123456).order_by('-id')
        order = Order.objects.all().order_by('-id')
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except:
        error_msg = 'not found orderlist'
        return Response({'error_msg': error_msg}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def filterOrderData(request):
    try:
        time.sleep(1)
        state = request.GET.get('state')
        value = request.GET.get('value')
        if state == 'name':
            order = Order.objects.filter(name__icontains=value).order_by('-id')
            
        elif state == 'date':
            date = value.split('-')
            order = Order.objects.filter(createdAt__year=int(date[0]), 
                createdAt__month=int(date[1]), createdAt__day=int(date[2])).order_by('-id')
        serializer = OrderSerializer(order, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        return Response('error', status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def editOrder(request):
    try:
        data = request.data.get('orderSelectData')
        order = Order.objects.filter(id=int(data.get("id"))).first()
        orderItem = OrderItem.objects.filter(order=order)
        print(data)
        print(data.get('aiTraining_state'))
        if data.get('aiTraining_state') == "no_training":
            if order.name != data.get('name'):
                order.name = data.get('name')
                order.save()

            for item in orderItem:
                item.quantity = data[item.name]
                item.save()

            path = os.path.join(settings.MEDIA_ROOT, f'input_csv/{order.unique_code}.csv')
            with open (path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            for row in rows:
                name = row["name"].replace('外箱', '')
                row['name'] = name
                row['quantity'] = data[name]

            with open(path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['box_id', 'name', 'width', 'height', 'depth', 'quantity']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        elif data.get('aiTraining_state') == "finish_training":
            pass
        
        return Response('ok', status=status.HTTP_200_OK)
    except:
        return Response({'error_msg': 'error'}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def deleteOrder(request):
    try:
        delete_list = request.data.get('orderSelectData')
        for i in delete_list:
            order = Order.objects.filter(id=int(i)).first()
            order.delete()
        return Response('ok', status=status.HTTP_200_OK)
    except:
        return Response({'error_msg': 'error'}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def getMultipleOrderData(request):
    try:
        multiple_order = MultipleOrder.objects.all().order_by('-id')
        serializer = MultipleOrderSerilaizer(multiple_order, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        return Response({'error_msg': '取得多單資料失敗'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def createMultipleOrder(request):
    try:
        orderSelectData = request.data.get('orderSelectData')
        inputText = request.data.get('inputText')
        max_id = MultipleOrder.objects.aggregate(Max("id")).get("id__max")
        today = datetime.now()
        today_mult_order = MultipleOrder.objects.filter(createdAt__year=today.year,
                        createdAt__month=today.month, createdAt__day=today.day, is_today_latest=True)
        
        if today_mult_order.exists():
            today_mult_order.update(is_today_latest=False)

        multiple_order = MultipleOrder.objects.create(
            name = inputText,
            orderSelectId_str = ','.join(orderSelectData)
        )
        multiple_order.save()

        # 去除重複
        orderSelectSet = set(map(lambda x: int(x.split('*')[0]), orderSelectData))
        # response data
        for order in orderSelectSet:
            order = Order.objects.filter(id=int(order)).first()
            MultipleOrderItem.objects.create(
                multiple_order = multiple_order,
                order = order
            )

        multipleOrderList = []
        for i in orderSelectSet:
            order = Order.objects.filter(id=int(i)).first()
            serializer = OrderSerializer(order, many=False)
            multipleOrderList.append({"order": serializer.data})
        
        response_data = {
            "id": multiple_order.id,
            "name": inputText,
            "orderSelectId_str": ','.join(orderSelectData),
            "is_today_latest": True,
            "createdAt": datetime.now().strftime('%Y/%m/%d  %H:%M'),
            "multipleOrder": multipleOrderList
        }

        return Response(response_data, status=status.HTTP_200_OK)
    except:
        return Response({"error_msg": "建立失敗，再試一次"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def deleteMultipleOrder(request):
    try:
        order_id = request.data.get('orderId')
        multiple_order = MultipleOrder.objects.filter(id=order_id).first()
        multiple_order.delete()
        return Response('ok', status=status.HTTP_200_OK)
    except:
        return Response({'error_msg': 'fail'}, status=status.HTTP_400_BAD_REQUEST)

# qrcode

# @api_view(['POST'])
# def uploadCsv(request):
#     # if 'csv_file' not in request.data:
#     #     return Response({'message': '請提供有效的 CSV 檔案'})
#     csv_file_length = int(request.data.get('csv_file_length'))
#     print(csv_file_length)
#     try:
#         for i in range(csv_file_length):
#             csv_file = request.data.get(f'csv_file{i+1}')
#             csv_name = request.data.get(f'csv_file_name{i+1}').replace('.csv', '')
#             unique_code = uuid.uuid4().hex
#             unique_code_exist = Order.objects.filter(unique_code=unique_code)

#             while unique_code_exist:
#                 unique_code = uuid.uuid4().hex
#                 unique_code_exist = Order.objects.filter(unique_code=unique_code)
#                 if unique_code_exist is None:
#                     break
            
#             # image = qrcode.make(unique_code)
#             # # 将图像保存到模型的ImageField字段
#             # image_io = BytesIO()
#             # image.resize((150, 150))
#             # image.save(image_io, 'PNG')
#             # image_content = ContentFile(image_io.getvalue(), name=unique_code + '.png')

#             qr = qrcode.QRCode(
#                 version=1,  # 版本（1-40），版本越高，QR码容纳的数据越多
#                 error_correction=qrcode.constants.ERROR_CORRECT_L,  # 错误纠正级别
#                 box_size=10,  # 每个模块的像素大小
#                 border=4,  # 边框大小
#             )
#             print(unique_code)
#             print(csv_name)
#             qr.add_data(unique_code)
#             qr.make(fit=True)
#             img = qr.make_image(fill_color="black", back_color="white")
#             img = img.resize((120, 120))  # 指定大小为150x150
#             image_io = BytesIO()
#             img.save(image_io, 'PNG')
#             image_content = ContentFile(image_io.getvalue(), name=unique_code + '.png')

#             # 读取CSV文件内容并保存到变量中
#             # 下面 order.save() 會讓文件指针指到最後
#             # 若用 csv_file.seek(0) 雖然會指到開頭但只能讀一行又會跑到最尾
#             csv_content = csv_file.read().decode('utf-8')

#             order = Order.objects.create(
#                 name = csv_name,
#                 unique_code = unique_code,
#                 image = image_content,
#                 csv_file = csv_file)
#             order.save()
            

#             # 使用 csv.reader 來讀取 CSV 檔案內容
#             csv_reader = csv.reader(csv_content.splitlines())
#             next(csv_reader)
            
#             for reader in csv_reader:
#                 # print(reader)
#                 OrderItem.objects.create(
#                     order = order,
#                     name = reader[1].replace('外箱', ''),
#                     width = reader[2],
#                     height = reader[3],
#                     depth = reader[4],
#                     quantity = int(reader[5])
#                 )

#     except Exception as e:
#         print(f'Error: {str(e)}')
#         return Response({'message': 'error'})

#     return Response({'message': 'CSV 檔案解析成功', 'data': 2}, status=200)

# import openpyxl
# from openpyxl.drawing.image import Image
# from openpyxl.styles import Alignment

# @api_view(['POST'])
# def getOrderXlsxFile(request):
#     datas = request.data.get('datas')
#     xlsx_path = os.path.join(settings.MEDIA_ROOT, 'orderlist_step2.xlsx')
#     # 打开工作簿
#     workbook = openpyxl.load_workbook(xlsx_path)
#     # 选择工作表
#     sheet = workbook.active  # 或者通过工作表名称：sheet = workbook['Sheet1']

#     for i in range(len(datas)):
#         aiTraining_order = []
#         for count, data in enumerate(datas[i].get('aiTraining_order').split(','), start=1):
#             if len(data) == 1:
#                 data = ' ' + data
#             if count % 4 == 0:
#                 aiTraining_order.append(data + '\n')
#             else:
#                 aiTraining_order.append(data + ' ')
#         csv_name = datas[i].get('name')
#         aiTraining_text = ''.join(aiTraining_order)
#         create_at = '\n\n'.join(datas[i].get('createdAt').split('  '))
#         print(aiTraining_text)
#         print(create_at)
        
#         xlsx_count = i + 4
#         # 添加新行
#         sheet[f'A{xlsx_count}'] = i + 1
#         sheet[f'A{xlsx_count}'].alignment = Alignment(horizontal='center', vertical='center')
#         sheet.merge_cells(f'B{xlsx_count}:C{xlsx_count}')
#         sheet[f'B{xlsx_count}'] = csv_name
#         sheet[f'B{xlsx_count}'].alignment = Alignment(horizontal='center', vertical='center', wrapText=True)
#         sheet.merge_cells(f'D{xlsx_count}:F{xlsx_count}')
#         sheet[f'D{xlsx_count}'] = aiTraining_text
#         sheet[f'D{xlsx_count}'].alignment = Alignment(horizontal='center', vertical='center', wrapText=True)
#         sheet[f'G{xlsx_count}'] = create_at
#         sheet[f'G{xlsx_count}'].alignment = Alignment(horizontal='center', vertical='center', wrapText=True)
#         # text_lines = text.split('\n')  # 如果文本中有换行符，请按换行符拆分文本
#         # max_line_length = max(len(line) for line in text_lines)
#         # row_height = 15  # 自定义行高
#         # if max_line_length > 0:
#         #     row_height *= (len(text_lines) + 1)  # 增加行数以适应文本
#         # sheet.row_dimensions[4].height = row_height + 30

#         sheet.merge_cells(f'H{xlsx_count}:I{xlsx_count}')

#         # 加载图片文件
#         img = Image(os.path.join(settings.MEDIA_ROOT, 'qrcode', f'{datas[i].get("unique_code")}.png'))  # 替换为实际图片路径
        
#         # 设置图片的位置和大小
        
#         sheet.add_image(img, f'H{xlsx_count}')  # 图片跨越从A1到B2的单元格
#         # 设置H4:I4单元格的水平和垂直居中对齐
#         # for row in sheet.iter_rows(min_row=4, max_row=4, min_col=8, max_col=9):
#         #     for cell in row:
#         #         cell.alignment = Alignment(horizontal='center', vertical='center', wrapText=True)
#         sheet[f'H{xlsx_count}'].alignment = Alignment(horizontal='center', vertical='center', wrapText=True)
#         sheet.row_dimensions[6].height = 11*15 + 30
#     # 保存工作簿
#     date = datetime.datetime.now().strftime('%Y%m%d_%H_%M_%S')
#     xlsx_output_path = os.path.join(settings.MEDIA_ROOT, 'xlsx', f'output_{date}.xlsx')
#     workbook.save(xlsx_output_path)
#     return Response({'xlsx_output_path': f'http://127.0.0.1:8000/static/media/xlsx/output_{date}.xlsx'})

# @api_view(['POST'])
# def getQRcodeFromCamera(request):
#     data = request.data.get('code')
#     print(data)
#     # qrcode 上傳 AI 工單
#     # QRcodeExecute.objects.create(
#     #     unique_code = data
#     # )

#     # qrcode 上傳原始工單 
#     order = Order.objects.filter(unique_code=data).first()
#     order.upload_qrcode_select = True
#     order.save()
#     return Response({'Success'})

# @api_view(['POST'])
# def getQRcodeDataFromDatabase(request):
#     data = request.data
#     print(data)
#     try:
#         if data.get('url') == '/control-robot2':
#             qrcode = QRcodeExecute.objects.filter(is_execute=False).first()
#             order = Order.objects.filter(unique_code=qrcode.unique_code).first()
#             qrcode.is_execute = True
#             qrcode.save()
#         elif data.get('url') == '/create-orderlist':
#             order = Order.objects.filter(upload_qrcode_select = True).first()
#             order.upload_qrcode_select = False
#             order.display = True
#             order.save()

#         return Response({'mode': 'has data',
#                         'id': order.id,
#                         'name': order.name,
#                         'createdAt': order.createdAt.strftime("%Y/%m/%d  %H:%M")})
#     except:
#         return Response({'mode': 'no data'})
    
