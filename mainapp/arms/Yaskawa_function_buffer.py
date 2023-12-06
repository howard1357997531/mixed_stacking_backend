import socket
# import websockets
import asyncio
import time
import pandas as pd
import time
from .Dimension_2_3D_single import Dimension_2_3D
from .Dimension_3D_single import Dimension_3D
import cv2
import numpy as np
from .camera import intelCamera_copy
from .qrcode import qrClass
import threading

# ------------------------------
# web_socket
from mainapp.views import (websocket_robot_state, websocket_object_count, 
    websocket_object_name, websocket_visual_result)
from django.conf import settings
import os
# ------------------------------

process = True
try:
    camera = intelCamera_copy.L515() 
except:
     process = False
     pass
config =  {
            "resolution":"720p",
            "fps":"15",
            "depthMode":"WFOV",
            "algin":"color"
        }

#camera = azuredkCamera.azureDK(config)
try:
	camera.openCamera()
except :
    process = False
        
    print('No Camera camera.openCamera')

#crop = {'xmin' :150, 'xmax':1920,'ymin':450, 'ymax':790, 'total height':495}  resolution 1920*1280    *******
crop = {'xmin' :10, 'xmax':1280,'ymin':280, 'ymax':550, 'total height':270} # resolution 1280*720      *******

dimenssion_object = Dimension_2_3D(crop = crop)
qr_object = qrClass(crop = crop)

dimenssion_3D_object = Dimension_3D(crop = crop)

def voting_preprocess(dst, src, key):
    dst[src[key]] = dst.get(src[key], 0) + 1
    return dst

def voting(result, key_list, data_list):
    for key in key_list:
        for src in data_list:
            result_dict = voting_preprocess(result_dict, src, key)         
    return result

# Supply = pd.read_csv('box_positions_conveyor.csv')
# Supply_namecolumns = Supply['matched_box_name']
# Supply_columns = Supply[['pos_x', 'pos_y', 'pos_z']]

# buffer_supply = pd.read_csv('box_positions_conveyor_catch.csv')
# buffer_namecolumns = buffer_supply['matched_box_name']
# buffer_catch = buffer_supply[['pos_x', 'pos_y', 'pos_z']]
# buffer_put = buffer_supply[['bin_name', 'buffer_x', 'buffer_y', 'buffer_z', 'orientation']]

# Place = pd.read_csv('box_positions_final.csv')
# Place_columns = Place[['bin_name','X_cog', 'Y_cog', 'Z_cog','orientation']]
# name_list1=[]
# for name in Supply_namecolumns:
#     name_list1.append(name)
##########################################################################
# data process
def decimal_to_hex(decimal):
    hex_string = hex(decimal & 0xFFFFFFFF)[2:]  
    hex_padded = hex_string.zfill(8)
    hex_reversed = hex_padded[6:8] + hex_padded[4:6] + hex_padded[2:4] + hex_padded[0:2]
    hex_formatted = ' '.join(hex_reversed[i:i+2] for i in range(0, len(hex_reversed), 2))
    return hex_formatted

def decimal_to_hex1(decimal):
    hex_string = hex(decimal & 0xFFFFFFFF)[2:] 
    hex_padded = hex_string.zfill(2)
    hex_reversed = hex_padded[0:2]
    hex_formatted = ' '.join(hex_reversed[i:i+2] for i in range(0, len(hex_reversed), 2))
    return hex_formatted
  
def mix_pack(orderId):  ####混料系統####
    # ---------------------------
    box_positions_conveyor_path = os.path.join(
        settings.MEDIA_ROOT, f'ai_figure/Figures_{orderId}', 'box_positions_conveyor.csv')
    box_positions_final_path = os.path.join(
        settings.MEDIA_ROOT, f'ai_figure/Figures_{orderId}', 'box_positions_final.csv')
    Supply = pd.read_csv(box_positions_conveyor_path)
    Supply_columns = Supply[['pos_x', 'pos_y', 'pos_z']]
    Place = pd.read_csv(box_positions_final_path)
    Place_columns = Place[['bin_name','X_cog', 'Y_cog', 'Z_cog','orientation']]
    # ---------------------------
    catch_list = []
    put_list = []
    posture1=[0.0,0.0,180.0]
    posture2=[90.0,0.0,180.0]
    count_list=1

    for index, row in Supply_columns.iterrows():
        supply_initial = row.to_list()
        Base=[2]
        supply_data=Base+supply_initial+posture1    
        catch_list.append(supply_data)

    for index, row in Place_columns.iterrows():
        place_initial = row.to_list()
        posture = posture2 if place_initial[4] == 1.0 else posture1    
        Base = [3] if place_initial[0] == 1 else [4]
        place_data=Base+place_initial[1:4]+posture
        put_list.append(place_data)
        count_list+=1

    return (catch_list,put_list,count_list)

def buffer_11box():
    # ---------------------------
    box_positions_conveyor_catch_path = os.path.join(
        settings.MEDIA_ROOT, f'box_positions_conveyor_catch.csv')
    buffer_supply = pd.read_csv(box_positions_conveyor_catch_path)
    buffer_namecolumns = buffer_supply['matched_box_name']
    buffer_catch = buffer_supply[['pos_x', 'pos_y', 'pos_z']]
    buffer_put = buffer_supply[['bin_name', 'buffer_x', 'buffer_y', 'buffer_z', 'orientation']]
    # ---------------------------
    Quanlity = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    buffer_name = []
    posture1 = [0.0,0.0,180.0]
    posture2 = [90.0,0.0,180.0]
    buffer_catch_list = []
    buffer_put_list = []
    for name in buffer_namecolumns:
        buffer_name.append(name)

    for index, row in buffer_catch.iterrows():
        buffer_catch_initial = row.to_list()
        Base = [2]
        buffer_catch_data = Base + buffer_catch_initial + posture1    
        buffer_catch_list.append(buffer_catch_data)
    
    for index, row in buffer_put.iterrows():
        buffer_put_initial = row.to_list()
        posture = posture2 if buffer_put_initial[4] == 1.0 else posture1    
        Base = [5] if buffer_put_initial[0] == 3 else [6]
        buffer_put_data = Base + buffer_put_initial[1:4] + posture
        buffer_put_list.append(buffer_put_data)


    return (buffer_name, buffer_catch_list, buffer_put_list, Quanlity)

def smart_pack(orderId):  ####智慧堆棧系統####
    # ---------------------------
    box_positions_conveyor_path = os.path.join(
        settings.MEDIA_ROOT, f'ai_figure/Figures_{orderId}', 'box_positions_conveyor.csv')
    Supply = pd.read_csv(box_positions_conveyor_path)
    Supply_columns = Supply[['pos_x', 'pos_y', 'pos_z']]
    Place = pd.read_csv('box_positions_final.csv')
    Place_columns = Place[['bin_name','X_cog', 'Y_cog', 'Z_cog','orientation']]
    # ---------------------------
    catch_list = []
    put_list = []
    posture1=[180.0,0.0,0.0]
    posture2=[180.0,0.0,90.0]
    count_list=1

    for index, row in Supply_columns.iterrows():
        supply_initial = row.to_list()
        Base=[2]
        supply_data=Base+supply_initial+posture1    
        catch_list.append(supply_data)

    for index, row in Place_columns.iterrows():
        place_initial = row.to_list()
        posture = posture2 if place_initial[4] == 1.0 else posture1    
        Base = [3] if place_initial[0] == 1 else [4]
        place_data=Base+place_initial[1:4]+posture
        put_list.append(place_data)
        count_list+=1

    return (catch_list,put_list,count_list)
##########################################################################
class Yaskawa_control():
    def __init__(self, ip ,port):
        self.server_ip = ip
        self.server_port = port
        self.client_socket0 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.system_choose = 1
        self.count = 1
        self.count_list = 1
        self.name_list = []
        self.angle_checked = []
        self.checknumber = 0
        self.motionnumber = 1
        self.motionangle  = 0
        self.motionname  = ''
        self.checknumberlist = []
        self.bufferquanlity_list = []
        self.bufferquanlity = []
        self.name_checked = []
        self.motion_state = 0
        self.Pc_checked = False
        self.Pc_system = False
        self.dectect_system = False
        self.packetsendlock = False
        self.removelock = False
        self.controllock = False
        self.commandlock = False
        self.thread0 = threading.Thread(target=self.control_response)
        ########################上位機-機器人########################
        #27010
        self.Pc_servo = 0
        self.Pc_control = 0
        self.Pc_start = False
        self.Pc_pause = False
        self.Pc_keepgo = False
        self.Pc_reset = False
        #27020
        self.Pc_command = 0
        self.Pc_boxchecked = False
        self.Pc_wrong = False
        self.Pc_send = False
        # self.Pc_speed=20

        self.Robot_start = False#100
        self.Robot_initial = False#101
        self.Robot_received = False#102
        self.Robot_motion = False#103
        self.Robot_boxchecked = False#104
        self.Robot_action = False#105

        #in(9)~in(11)
        self.Robot_sensor1 = False
        self.Robot_sensor2 = False
        self.Robot_sensor3 = False
        ########################上位機-機器人########################
        ########################前台-上位機########################
        self.Pc_catch = False
        self.Pc_put = False
        self.Pc_finish = False
        self.frontend_display = 0
        self.frontend_boxnumber = 0
        self.frontend_motion = 0
        ########################前台-上位機########################
        
        # websocket
        self.order_count = 1
        self.robot_count = 1
        self.detect_count_change = False
        self.detect_count = 1
        self.detect_box = []
        self.robot_count_bool = False

    ###############################I/O通訊用#################################   
    async def send_position(self):
        while not self.Pc_finish:
            if self.packetsendlock:
                position_mapping = {'process': '11','case': '12', 'base': '06', 'p1': '04', 'p2': '05', 'p3': '06', 'p4': '09', 'p5': '08', 'p6': '07'}
                element_mapping = {'process': '7C','case': '7C', 'base': '7F', 'p1': '7C', 'p2': '7C', 'p3': '7C', 'p4': '7C', 'p5': '7C', 'p6': '7C'}
                Datalengh_mapping = {'process': '04','case': '04', 'base': '01', 'p1': '04', 'p2': '04', 'p3': '04', 'p4': '04', 'p5': '04', 'p6': '04'}
                layer_mapping = {'process': '01','case': '01', 'base': '04', 'p1': '01', 'p2': '01', 'p3': '01', 'p4': '01', 'p5': '01', 'p6': '01'}

                for position, value in self.packet_dict.items():
                    decimal_value = int(value * (1 if position in ['process', 'case', 'base'] else 1000 if position in ['p1', 'p2', 'p3'] else 10000))
                    if position in ['base']:
                        hex_value = decimal_to_hex1(decimal_value)
                    else:
                        hex_value = decimal_to_hex(decimal_value)

                    data_packet = bytes.fromhex(f"59 45 52 43 20 00 {Datalengh_mapping[position]} 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 {element_mapping[position]} 00 {position_mapping[position]} 00 {layer_mapping[position]} 02 00 00 " + hex_value.replace(" ", ""))
                    self.client_socket3.sendto(data_packet, (self.server_ip, self.server_port))
                self.packetsendlock = False
            await asyncio.sleep(0.1)

    async def send_control(self):
        while not self.Pc_finish:
            self.Pc_control = (self.Pc_reset << 5) + (self.Pc_keepgo << 4) + (self.Pc_pause << 3)+ (self.Pc_start << 2)+ self.Pc_servo
            Pc_control_string = decimal_to_hex1(self.Pc_control)
            data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 8D 0A 01 10 00 00 " + Pc_control_string.replace(" ", ""))
            self.client_socket0.sendto(data_packet, (self.server_ip, self.server_port)) 
            response, addr = self.client_socket0.recvfrom(1024)
            await asyncio.sleep(0.05)
       
    async def send_command(self):
        while not self.Pc_finish:
            self.Pc_command = (self.Pc_send << 2) + (self.Pc_wrong << 1) + self.Pc_boxchecked
            Pc_command_string = decimal_to_hex1(self.Pc_command)
            data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 8E 0A 01 10 00 00 " + Pc_command_string.replace(" ", ""))
            self.client_socket1.sendto(data_packet, (self.server_ip, self.server_port)) 
            response, addr = self.client_socket1.recvfrom(1024)
            await asyncio.sleep(0.05)    

    async def request_response(self):
        I=0
        while not self.Pc_finish:
            data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 32 00 01 0E 00 00 00" )
            self.client_socket2.sendto(data_packet, (self.server_ip, self.server_port))
            response, addr = self.client_socket2.recvfrom(1024)
            response_R = response.hex()[-24:-4]
            if response_R[:2]=='8e':
                signal_hex = response_R[-4:]
                hex_reversed = signal_hex[2:4] + signal_hex[0:2]
                signal_int = int(hex_reversed,16)
                signal_binary = bin(signal_int)[2:].zfill(16)
                self.Robot_start=bool(int(signal_binary[-1]))
                self.Robot_initial=bool(int(signal_binary[-2]))
                self.Robot_received=bool(int(signal_binary[-3]))
                self.Robot_motion=bool(int(signal_binary[-4]))
                self.Robot_boxchecked=bool(int(signal_binary[-5]))
                self.Robot_action=bool(int(signal_binary[-6]))
                self.Robot_sensor1=bool(int(signal_binary[-9]))
                self.Robot_sensor2=bool(int(signal_binary[-10])) 
                self.Robot_sensor3=bool(int(signal_binary[-11]))
                I=I+1
                # print(I)
                await asyncio.sleep(0)
            else:
                print('fail')
     
    def control_response(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task1 = self.send_control()
        task2 = self.send_command()
        task3 = self.request_response()
        task4 = self.send_position()
        # start_server = loop.run_until_complete(websockets.serve(self.handle, "localhost", 8765))
        loop.run_until_complete(asyncio.gather(task1, task2, task3, task4))
        # start_server.close()
        # loop.run_until_complete(start_server.wait_closed())
        print("WebSocket server closed")          
    ###############################I/O通訊用#################################  
    ###############################即時控制用#################################   
    def start(self):
        self.Pc_system=True
        self.Pc_servo=3
        self.Pc_start=True

    def pause(self):
        self.frontend_motion=9
        self.Pc_keepgo=False
        self.Pc_pause=True

    def keepgo(self):
        self.frontend_motion=10
        self.Pc_pause=False
        self.Pc_keepgo=True
        self.Pc_start=False
        time.sleep(0.1)
        self.Pc_start=True

    def reset(self):
        self.Pc_keepgo=False
        self.Pc_pause=True
        time.sleep(0.1)
        self.Pc_start=False
        self.Pc_servo=0
        self.Pc_reset=True
        time.sleep(0.1)
        self.Pc_pause=False
        self.Pc_reset=False
        self.Pc_system=False

    def speed(self,D_data):
        D_data=D_data*70
        D_data_hex= decimal_to_hex(D_data)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 01 00 01 02 00 00  " + D_data_hex.replace(" ", ""))
        self.client_socket4.sendto(data_packet, (self.server_ip, self.server_port))

    def button_switch(self,a):
        hex_value=decimal_to_hex1(int(a))
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 08 00 01 02 00 00  " + hex_value.replace(" ", ""))
        self.client_socket4.sendto(data_packet, (self.server_ip, self.server_port))

    def left_button(self, a, value):
        self.button_switch(a)
        hex_value = decimal_to_hex(value*1000)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7F 00 14 00 06 02  00 00 " + hex_value.replace(" ", "") )
        self.client_socket3.sendto(data_packet, (self.server_ip, self.server_port))

    def right_button(self, a, value):
        self.button_switch(a)
        hex_value = decimal_to_hex(value*1000)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7F 00 14 00 06 02  00 00 " + hex_value.replace(" ", "") )
        self.client_socket3.sendto(data_packet, (self.server_ip, self.server_port))

    def front_button(self, a, value):
        self.button_switch(a)
        hex_value = decimal_to_hex(value*1000)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7F 00 14 00 07 02  00 00 " + hex_value.replace(" ", "") )
        self.client_socket3.sendto(data_packet, (self.server_ip, self.server_port))

    def back_button(self, a, value):
        self.button_switch(a)
        hex_value = decimal_to_hex(value*1000)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7F 00 14 00 07 02  00 00 " + hex_value.replace(" ", "") )
        self.client_socket3.sendto(data_packet, (self.server_ip, self.server_port))

    def up_button(self, a, value):
        self.button_switch(a)
        hex_value = decimal_to_hex(value*1000)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7F 00 14 00 08 02  00 00 " + hex_value.replace(" ", "") )
        self.client_socket3.sendto(data_packet, (self.server_ip, self.server_port))

    def down_button(self, a, value):
        self.button_switch(a)
        hex_value = decimal_to_hex(value*1000)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7F 00 14 00 08 02  00 00 " + hex_value.replace(" ", "") )
        self.client_socket3.sendto(data_packet, (self.server_ip, self.server_port))

    def generate_base(self, position1, position2, position3):
        for a, b, c in position1, position2, position3:
            decimal_value = int(a* 1000)
            hex_value = decimal_to_hex(decimal_value)

            Datalengh_mapping = {'X': '04','Y': '04','Z': '04'}
            position_mapping = {'X': '0a','Y': '0b','Z': '0c'}
            Write_mapping = '02'

            data_packet = bytes.fromhex(f"59 45 52 43 20 00 {Datalengh_mapping[position1]} 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 {position_mapping[position1]} 00 01 {Write_mapping}  00 00 " + hex_value.replace(" ", ""))
            self.client_socket3.sendto(data_packet, (self.server_ip, self.server_port))
            response, addr = self.client_socket3.recvfrom(1024)

    ###############################即時控制用################################# 

    ##############################每台手臂以下都一樣##########################

    ###############################整合視覺用#################################
    def dectect_open(self):
        self.dectect_system = True

    def main(self):
        count = 0
        #out_raw = cv2.VideoWriter(f"recording.avi", cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 3, (1920, 1080))
        if not process:
            return None
        for idx_, i in enumerate(camera.getData()):	
            if not i :
                continue
            start_time = time.time()

            image, pc , depth_image =  i
            image_crop = image[crop['ymin']:crop['ymax'], crop['xmin']:crop['xmax']]    
            cv2.imshow('image_crop', image_crop)
            cv2.waitKey(1)
            # if robot.request_sensor11():
            #image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            image_copy = np.copy(image)
                
            if  self.Robot_sensor1 and not self.Pc_finish:
                Box_id=['#0']
                angle=str(-1)
                return Box_id,angle

            startdecodetime = time.time()
            dbrcount = qr_object.decode_dbrcount(image)
            pyzbarcount = qr_object.decode_pyzbarcount(image_copy)
            enddecodetime =  time.time()
            print(dbrcount, pyzbarcount)
            twodecodetime=enddecodetime -startdecodetime
                # print( "Time taken twodecodetime: {0} seconds".format(twodecodetime))
                # # Calculate frames per second
            fps2  = 1 / twodecodetime
                # print( "Estimated  twodecodetime cv2 frames per second : {0}".format(fps2))

            # if True: 
                # two detect count equal can show
            if dbrcount !=pyzbarcount:
                continue
            if dbrcount == pyzbarcount:
                #image_qr, boxID_list,sorted_dict_by_value_desc,angle_list = qr_object.qr_result(image.copy(), pc)
                image_qr, boxID_list,sorted_dict_by_value_desc,angle_list = qr_object.qr_result(image, pc)
                end_time = time.time()

                # 計算執行時間，換算成 FPS
                elapsed_time = end_time - start_time
                fps = 1 / elapsed_time

                if boxID_list and angle_list:
                    qr_dict = {'box_id': boxID_list, 'angle': angle_list}
                else:
                    qr_dict = {'box_id': '0', 'angle': '-1'}
         
                box_id = qr_dict['box_id']
                angle = qr_dict['angle']

                cv2.putText(image, f"ID: {box_id}, angle: {angle}, FPS:{fps:.2f}",(50,50), cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255,1))            
                cv2.imshow('image',image)
                
                k = cv2.waitKey(1)
                # if k == ord('s'):

                #     img_name = f"image_{datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d-%H-%M-%S')}.png"
                #     cv2.imwrite(img_name, image)
                #     print(f"Image saved as {img_name}")
                Box_id = ['#' + item for item in box_id]
                print(Box_id,angle)
                # --------------------------------
                if self.detect_count_change:
                    # 此段為偵測順序改變
                    websocket_visual_result(None, self.detect_count)
                websocket_visual_result(Box_id, None)
                self.detect_count_change = False
                self.detect_box = Box_id
                # --------------------------------
                    
                if k == ord('q'):
                    break
                return Box_id,angle
            time.sleep(0.1)       

    def thread2_supplycheck(self):
        self.frontend_display=4

        while self.dectect_system and not self.Pc_finish:  
            # if (self.Robot_sensor3 or self.frontend_display==2) and not self.removelock:
            if self.Robot_sensor3 and not self.removelock:
                # print('開始檢測')
                self.Pc_checked=True
                result = self. main()

                if result[0][0] != '#0'or result[1] != '-1':                
                    while self.dectect_system and not self.Pc_finish:   
                        Box_ID, Box_angle  = result[0][:], result[1][:]
                        
                        for item1, item2 in zip(self.name_checked,self.angle_checked):
                            if item1 in Box_ID and item2 in Box_angle:
                                Box_ID.remove(item1)
                                Box_angle.remove(item2)
                                time.sleep(0.1)
                                
                        if len(Box_ID)!=0:
                            print('正確應為',self.name_list[0])
                            if self.name_list[0] == Box_ID[0]:
                                self.frontend_display = 1  # 正確
                                ######回傳視覺組比對後順序#####
                                self.checknumber=1
                                self.name_checked.append(self.name_list.pop(0))
                                self.angle_checked.append(Box_angle[0])
                                self.checknumberlist.append(self.checknumber)
                                ######回傳視覺組比對後順序#####       
                                self.frontend_boxnumber += 1
                                
                            else:
                                self.frontend_display = 2  # 錯誤
                                ######回傳視覺組比對後順序#####
                                self.checknumber=2
                                self.name_checked.append(Box_ID[0])
                                self.angle_checked.append(Box_angle[0])
                                self.checknumberlist.append(self.checknumber)
                                ######回傳視覺組比對後順序#####
                                break
                        
                        else:
                            break
                        time.sleep(0.5)
                        self.frontend_display=3

                    checked_dict= {'Box_id': self.name_checked ,'angle': self.angle_checked }
                    file = pd.DataFrame(checked_dict)
                    file.to_csv('checked_file.csv', index=False)
                    print('已經看過的箱子',self.name_checked, self.angle_checked, self.checknumberlist)

                self.Pc_checked=False

            # ------------------------------
            else:
                if self.detect_count_change:
                    self.detect_box = self.detect_box[1:]
                    # 此段為偵測順序改變
                    websocket_visual_result(self.detect_box, self.detect_count)
                self.detect_count_change = False
            # ------------------------------    

            time.sleep(0.1)

        print('檢測關閉')
        self.frontend_display=0
    ###############################整合視覺用#################################
    ###############################前台顯示用#################################  
    def frontend_dis(self):
        while True:
            self.frontend_display=int(input())
    
    async def handle(self,websocket):
        # try:
            while not self.Pc_finish:

                if self.frontend_motion==0:
                    await websocket.send('等待啟動')
                elif self.frontend_motion==1:
                    await websocket.send('程式啟動中')
                elif self.frontend_motion==2:
                    await websocket.send('初始化完畢')
                elif self.frontend_motion==3:
                    await websocket.send(f'夾取第{self.count}箱')
                elif self.frontend_motion==4:
                    await websocket.send(f'放置第{self.count}箱')
                elif self.frontend_motion==5:
                    await websocket.send(f'夾取完畢')
                elif self.frontend_motion==6:
                    await websocket.send(f'放置完畢')
                elif self.frontend_motion==7:
                    await websocket.send('系統重置')
                elif self.frontend_motion==8:
                    await websocket.send('執行完畢回原點')
                elif self.frontend_motion==9:
                    await websocket.send('機器人暫停中')
                elif self.frontend_motion==10:
                    await websocket.send('機器人繼續動作')
                await asyncio.sleep(0.1)
    ###############################前台顯示用#################################
    ###############################程式圖塊化################################# 
    def process_track(self):
        status = False
        self.Pc_send = True
        print('send command')

        while self.Pc_system:
            time.sleep(0.1)
            if self.Robot_received:
                print('send command recieved')
            
                while self.Pc_system:
                    time.sleep(0.1)
                    if self.Robot_motion:
                        self.Pc_send = False
                        print('Robot recieve then in action')

                        while self.Pc_system:
                            time.sleep(0.1)
                            if self.Robot_action:
                                if self.motion_state == 1:
                                    self.frontend_motion = 3
                                elif self.motion_state == 2:
                                    self.frontend_motion = 4
                            if not self.Robot_motion:
                                print('Robot action finish')
                                # ----------------------------
                                if self.robot_count <= self.order_count:
                                    websocket_robot_state('prepare')
                                    if self.robot_count_bool:
                                        websocket_object_count(self.robot_count)
                                # ----------------------------
                                break

                        print('send_packet next time')
                        status = True
                        return status
              
    def motion(self, process, case, position, angle):
        packet = [process, 0, 0, 0, 0, 0, 0, 0, 0]
        packet[1] = case
        packet[-7:] = position
        self.motion_state = case
        
        if case == 1:
            if angle == 1:
                packet[3], packet[4] = packet[4], packet[3]
                packet[-3] += 90.0
        
        elif case == 2:
            if self.motionnumber==2:
                packet[5] = packet[5] * self.bufferquanlity
        
        print(packet)
        self.packet_dict = {'process':packet[0],'case':packet[1],'base':packet[2],'p1':packet[3],
                     'p2':packet[4],'p3':packet[5],'p4':packet[6],'p5':packet[7],'p6':packet[8]}

        self.packetsendlock = True 
        while self.Pc_system:
            if not self.packetsendlock:
                break
            time.sleep(0.1)

        result = self.process_track()

        return result
    
    def Robot_Demo(self, orderId, order_list, order_count, isFinish_queue):
        # --------------------------------
        self.orderId = orderId
        self.order_list = order_list
        self.order_count = order_count
        self.isFinish_queue = isFinish_queue
        box_positions_conveyor_path = os.path.join(settings.MEDIA_ROOT, f'ai_figure/Figures_{orderId}', 'box_positions_conveyor.csv')
        # --------------------------------
        Supply = pd.read_csv(box_positions_conveyor_path)
        Supply_namecolumns = Supply['matched_box_name']
        name_list1=[]
        for name in Supply_namecolumns:
            name_list1.append(name.replace('外箱', '').replace('A', ''))
        self.name_list=name_list1[:]

        self.start_tile()
        self.initial_tile()
        self.system_tile()
        self.end_tile()  

    def start_tile(self):
        self.thread0.start()
        self.reset()
        time.sleep(1)
        self.start()
        print('等待機器人啟動')
        self.frontend_motion=0
        while self.Pc_system:
            if self.Robot_start:
                print('程式啟動')
                self.frontend_motion = 1
                break
            time.sleep(0.1)

    def initial_tile(self):
        while self.Pc_system:
            if self.Robot_initial:
                print('回到起始位')
                print('等待檢測')
                self.frontend_motion = 2
                break
            time.sleep(0.1)

    def system_tile(self):
        catch_list, put_list, self.count_list = mix_pack(self.orderId)
        buffer_name, buffer_catch, buffer_put, self.bufferquanlity_list = buffer_11box()
        # -----------------------
        websocket_robot_state('detect')
        # websocket_object_count(1)              
        #------------------------

        for catch_input, put_input in zip(catch_list, put_list):
        # -----------------------
            if self.count == 1:
                websocket_robot_state('prepare')
                websocket_object_count(1)              
        #------------------------

            while self.Pc_system:# 不可刪掉
                if self.dectect_system:
                    self.Camera_orderchecked_tile()

                if self.motionnumber == 1:
                    self.robot_count_bool = True
                    self.catch_tile(self.motionnumber, catch_input, 'correct')
                    self.put_tile(self.motionnumber, put_input)
                    break
                
                else:
                    index_buffer = buffer_name.index(self.motionname)
                    self.bufferquanlity = self.bufferquanlity_list[index_buffer]
                    self.robot_count_bool = False
                    self.catch_tile(self.motionnumber, buffer_catch[index_buffer], 'error')
                    self.put_tile(self.motionnumber, buffer_put[index_buffer])
                    self.bufferquanlity_list[index_buffer] += 1
                    

    def Camera_orderchecked_tile(self):
        while self.Pc_system:
            if not self.Pc_checked  and not len(self.name_checked)==0 and self.Robot_sensor1:
                self.removelock=True

                self.motionangle = 1 if self.angle_checked[0]== 1 else 0
                self.motionname = self.name_checked[0]
                self.motionnumber = self.checknumberlist[0]

                print('移除前:',self.name_checked, self.angle_checked, self.checknumberlist)
                self.name_checked.pop(0)
                self.angle_checked.pop(0)
                self.checknumberlist.pop(0)
                break
                
            time.sleep(0.1)

    def catch_tile(self,process,catch_input,state):
        
        while self.Pc_system:
            case = 1
            self.Pc_boxchecked=True
            print('正確catch第%d次'%(self.count))

            if self.motion(process, case, catch_input, self.motionangle):
                self.frontend_motion=5
                # 鎖住相機偵測
                self.Pc_boxchecked=False
                # -----------------------
                if state == 'correct':
                    count = self.count; order_list = self.order_list; order_count = self.order_count
                    if count < self.order_count:
                        next_name = order_list[count + 1] if count < order_count - 1 else ''
                        websocket_object_name(order_list[count], next_name)
                # -----------------------
                # 解鎖開始偵測
                self.removelock=False
                # -----------------------
                if state == 'correct':
                    self.detect_count_change = True
                    self.detect_count = count + 1
                # -----------------------
                break

    def put_tile(self,process,put_input):
        while self.Pc_system:
            
            case = 2
            print('正確put第%d次'%(self.count))
            # -----------------------
            websocket_robot_state('operate')
            self.robot_count = self.count + 1
            # -----------------------

            if self.motion(process, case, put_input, 0):
                self.frontend_motion=6
                if self.motionnumber == 1:
                    self.count+=1
                break

    def end_tile(self):
        if self.count==self.count_list or not self.Pc_system:
            if not self.Pc_system:
                self.frontend_motion=7
                print('系統重置')
                # --------------------
                self.isFinish_queue.put(False)
                # --------------------
            else:
                self.frontend_motion=8
                self.speed(20)
                home_input=[1, 0, 0, 0, 0, 0, 0]
                self.motion(1, 3, home_input, 1)
                print('執行完畢回原點')
                # --------------------
                self.isFinish_queue.put(True)
                # --------------------
                

        self.reset()
        time.sleep(0.1)
        self.Pc_finish=True
        self.Pc_system=False
        print("Connection closed.") 
    ################################程式圖塊化################################# 