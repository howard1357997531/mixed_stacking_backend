from django.shortcuts import render
from django.conf import settings
from django.db.models import Max
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializer import workOrderSerializer, aiWorkOrderSerializer, OrderSerializer
from .models import workOrder, aiWorkOrder, Order, OrderItem

from .robot import main, robot_control, speed
# from .main_result_20230830 import activate_cal
from .main_result_20230911 import activate_cal
from .main_result_UI import ai_calculate
from io import BytesIO
import random
import datetime
import qrcode
import pandas as pd
import time
import uuid
import csv
import os

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
            'type': 'robot_count_change',
            'count': count
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
        [1, "#7A外箱", 35, 26, 20, data.get("7A")],
        [2, "#9外箱", 43, 32, 23, data.get("9")],
        [3, "#16A外箱", 35, 26, 16, data.get("16A")],
        [4, "#18A外箱", 35, 26, 18, data.get("18A")],
        [5, "#13外箱", 56, 25, 14, data.get("13")],
        [6, "#20外箱", 53, 34, 13, data.get("20")],
        [7, "#22外箱", 45, 26, 18, data.get("22")],
        [8, "#26外箱", 72, 25, 20, data.get("26")],
        [9, "#29外箱", 65, 25, 18, data.get("29")],
        [10, "#33外箱", 44, 21, 18, data.get("33")],
        [11, "#35外箱", 102, 46, 18, data.get("35")],
    ]

    workOrder.objects.create(
        name = data.get("name"),
        _16A_qty = data.get("16A"),
        _18A_qty = data.get("18A"),
        _33_qty = data.get("33"),
        _7A_qty = data.get("7A"),
        _13_qty = data.get("13"),
        _22_qty = data.get("22"),
        _20_qty = data.get("20"),
        _29_qty = data.get("29"),
        _9_qty = data.get("9"),
        _26_qty = data.get("26"),
        _35_qty = data.get("35"),
    )

    max_id = workOrder.objects.aggregate(Max('id')).get('id__max')
    order = workOrder.objects.filter(id=max_id).first()
    order.file_name =  f'box_data_{max_id}.csv'
    order.save()

    csv_file = os.path.join(settings.MEDIA_ROOT, f'box_data_{max_id}.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
    
        for row in csv_data:
            writer.writerow(row)

    # 亂數
    # items = []
    # for key, value in data.items():
    #     items.extend([key] * value)
    # random.shuffle(items)
    # print("original data:", data)
    # print("random data:", items)
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
    activate_cal(worklist_id, unique_code="", step=1)
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

# from .arm.Yaskawa_function import Yaskawa_control
# import threading

@api_view(['POST'])
def executeRobot(request):
    try:
        orderId = int(request.data.get('orderId'))
        order = Order.objects.filter(id=orderId).first()
        order_count = len(order.aiTraining_order.split(','))

        # robot = Yaskawa_control('192.168.1.15', 10040)
        # thread1 = threading.Thread(target=robot.Robot_Demo2, args=(orderId,))
        # thread1.start()
        # time.sleep(2)
        # thread2 = threading.Thread(target=robot.supplycheck, args=(orderId,))
        # thread2.start()

        # test
        
        time.sleep(2)
        for i in range(1, order_count + 1):
            print(f'第{i}次')
            websocket_object_count(i) 
            websocket_robot_state('detect')
            websocket_robot_state('prepare')
            time.sleep(10)

            if i % 2 == 0:
                websocket_robot_state('correct')
            else:
                websocket_robot_state('error')
                time.sleep(2)
                websocket_robot_state('correct')
            
            time.sleep(2)
            websocket_robot_state('operate')
            time.sleep(2)
            
            # if i == 8 :
            #     break
        # websocket_robot_state('已結束')
        return Response({}, status=status.HTTP_200_OK)
    except:
        return Response({'error_msg': '啟動手臂失敗'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def robotSetting(request):
    try:
        data = request.data
        mode = data.get('mode')
        channel_layer = get_channel_layer()
        # robot = Yaskawa_control('192.168.1.15', 10040)
        # if mode == 'pause':
        #     robot.pause()
        # elif mode == 'unPause':
        #     robot.keepgo()
        # elif mode == 'speedUp' or mode == 'speedDown':
        #     robot_speed = data.get('speed') + 10 if mode == "speedUp" else data.get('speed') - 10
        #     robot_speed = 100 if robot_speed > 100 else robot_speed
        #     speed(robot_speed)
        # elif mode == 'reset':
        #     robot.pause()
        #     robot.reset()

        if mode == 'pause':
            print(mode)
        elif mode == 'unPause':
            print(mode)
        elif mode == 'speedUp' or mode == 'speedDown':
            robot_speed = data.get('speed') + 10 if mode == "speedUp" else data.get('speed') - 10
            robot_speed = 100 if robot_speed > 100 else robot_speed
            print(mode, robot_speed)
        elif mode == 'reset':
            print(mode)
            websocket_robot_state('reset')

        return Response({}, status=status.HTTP_200_OK)
    except:
        return Response({'error_msg': '啟動手臂失敗'}, status=status.HTTP_400_BAD_REQUEST)
        

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
        worklist_id = request.data.get("orderId")
        order = Order.objects.filter(id=int(worklist_id)).first()
        if request.data.get('mode') == 'error':
            order.aiTraining_state = "no_training"
            order.save()
            return Response('ok', status=status.HTTP_200_OK)
        
        order.aiTraining_state = "is_training"
        order.save()
        unique_code = order.unique_code
        print(worklist_id)
        print(type(worklist_id))
        print(unique_code)
        t1 = time.time()
        ai_calculate(worklist_id, unique_code, step=2)
        t2 = time.time()
        training_time = round(t2-t1, 3)
        ai_csvfile_path = os.path.join(settings.MEDIA_ROOT, f'Figures_step2_{worklist_id}', f'box_positions_final.csv')
        ai_df = pd.read_csv(ai_csvfile_path)
        ai_list = ai_df['matched_box_name'].tolist()
        aiResult_str = ','.join([ai.replace('#', '').replace('外箱', '') for ai in ai_list])

        order.aiTraining_order = aiResult_str
        order.aiTraining_state = "finish_training"
        order.save()
        # aiWorkOrder.objects.create(
        #     name = work_order.name,
        #     worklist_id = worklist_id,
        #     list_order = ai_str,
        #     training_time = training_time
        # )

        return Response({"aiResult_str": aiResult_str}, status=status.HTTP_200_OK)
    except:
        return Response('request fail', status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def getOrderData(request):
    try:
        # time.sleep(5)
        # order = Order.objects.get(id=123456).order_by('-id')
        order = Order.objects.all().order_by('-id')
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except:
        error_msg = 'not found orderlist'
        return Response({'error_msg': error_msg}, status=status.HTTP_400_BAD_REQUEST)



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
    
