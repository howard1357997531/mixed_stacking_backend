import socket
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
# ------------------------------

process = True
try:
    camera = intelCamera_copy.L515() 
except:
     process = False
     pass
config =  {
            "resolution":"1080p",
            "fps":"15",
            "depthMode":"WFOV",
            "algin":"color"
        }
        

#camera = azuredkCamera.azureDK(config)
try:
	camera.openCamera()
except :
    process = False
        
    print('No Camera')

crop = {'xmin' :150, 'xmax':1920,'ymin':450, 'ymax':790, 'total height':495}

dimenssion_object = Dimension_2_3D(crop = crop)
qr_object = qrClass(crop = crop)

dimenssion_3D_object = Dimension_3D(crop = crop)


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

# -----------------------
from django.conf import settings
import os
# -----------------------

def getdata(orderId):
    # -----------------------
    orderId = orderId
    box_positions_conveyor_path = os.path.join(settings.MEDIA_ROOT, f'Figures_step2_{orderId}', 'box_positions_conveyor.csv')
    box_positions_final_path = os.path.join(settings.MEDIA_ROOT, f'Figures_step2_{orderId}', 'box_positions_final.csv')
    # -----------------------
    Supply = pd.read_csv(box_positions_conveyor_path)
    Place = pd.read_csv(box_positions_final_path)
    Supply_columns = Supply[['pos_x', 'pos_y', 'pos_z']]
    Place_columns = Place[['bin_name','X_cog', 'Y_cog', 'Z_cog','orientation']]

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
        self.name_list=[]
        self.angle_checked=[]
        self.checkangle=0
        self.name_checked=[]
        self.name_wrong=[]
        self.motion_state=0
        self.Pc_checked=False
        self.Pc_system=False
        self.Order_checked=False
        self.removelock=False
        self.controllock=False
        self.commandlock=False
        self.lock=threading.Lock()
        self.lock1=threading.Lock()
        self.thread0=threading.Thread(target=self.control_response)
        ########################上位機-機器人########################
        self.Pc_servo=0
        self.Pc_control=0
        self.Pc_start=False
        self.Pc_pause=False
        self.Pc_keepgo=False
        self.Pc_reset=False
        self.Pc_command=0
        self.Pc_boxchecked=False
        self.Pc_wrong=False
        self.Pc_send=False
        # self.Pc_speed=20

        self.Robot_start=False#100
        self.Robot_initial=False#101
        self.Robot_received=False#102
        self.Robot_motion=False#103
        self.Robot_boxchecked=False#104

        #in(9)~in(11)
        self.Robot_sensor1=False
        self.Robot_sensor2=False
        self.Robot_sensor3=False
        ########################上位機-機器人########################
        ########################前台-上位機########################
        self.Pc_catch=False
        self.Pc_put=False
        self.Pc_finish=False
        self.frontend_display=0
        self.frontend_boxnumber=0
        self.frontend_start=False
        self.frontend_pause=False
        self.frontend_keepgo=False
        self.frontend_reset=False
        self.frontend_catch=False
        self.frontend_put=False
        self.frontend_finish=False
        ########################前台-上位機########################

        # websocket
        self.order_count = 1
        self.robot_count = 1
        self.detect_count_change = False
        self.detect_count = 1
        self.detect_box = []

    def send_position(self, data_D):
        position_mapping = {'process': '11', 'case': '12', 'userbase': '10', 'X': '04', 'Y': '05', 'Z': '06', 'A': '07', 'B': '08', 'C': '09'}

        for position, value in data_D.items():
            decimal_value = int(value * (1 if position in ['process', 'case', 'userbase'] else 1000 if position in ['X', 'Y', 'Z'] else 10000))
            hex_value = decimal_to_hex(decimal_value)

            data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 {position_mapping[position]} 00 01 02 00 00 " + hex_value.replace(" ", ""))
            self.client_socket3.sendto(data_packet, (self.server_ip, self.server_port))

            time.sleep(0.01)

    async def send_control(self):
        while not self.Pc_finish:
            self.Pc_control= (self.Pc_reset << 5) + (self.Pc_keepgo << 4) + (self.Pc_pause << 3)+ (self.Pc_start << 2)+ self.Pc_servo
            Pc_control_string = decimal_to_hex1(self.Pc_control)
            data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 8D 0A 01 10 00 00 " + Pc_control_string.replace(" ", ""))
            self.client_socket0.sendto(data_packet, (self.server_ip, self.server_port)) 
            response, addr = self.client_socket0.recvfrom(1024)
            # response_R = response.hex()[-18:]
            # print(response.hex())
            await asyncio.sleep(0)
       
    async def send_command(self):
        while not self.Pc_finish:
            self.Pc_command= (self.Pc_send << 2) + (self.Pc_wrong << 1) + self.Pc_boxchecked
            Pc_command_string = decimal_to_hex1(self.Pc_command)
            data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 8E 0A 01 10 00 00 " + Pc_command_string.replace(" ", ""))
            self.client_socket1.sendto(data_packet, (self.server_ip, self.server_port)) 
            response, addr = self.client_socket1.recvfrom(1024)
            # response_R = response.hex()[-18:]
            # print(response.hex() )
            await asyncio.sleep(0)    

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
        loop.run_until_complete(asyncio.gather(task1,task2,task3,))  
    
    #即時控制用#
    ########################   
    def start(self):
        self.Pc_system=True
        self.Pc_servo=3
        self.Pc_start=True

    def pause(self):
        self.Pc_keepgo=False
        self.Pc_pause=True

    def keepgo(self):
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

    #整合視覺#
    ########################   
    def main(self):
        count = 0
        #out_raw = cv2.VideoWriter(f"recording.avi", cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 3, (1920, 1080))
        if not process:
            return None

        for idx_, i in enumerate(camera.getData()):	
            if not i :
                continue
            start_ = time.time()

            image, pc , depth_image =  i
            image_crop = image[crop['ymin']:crop['ymax'], crop['xmin']:crop['xmax']]    
            # cv2.imshow('image_crop', image_crop)
            # cv2.waitKey(1)
            if  self.Robot_sensor1:
                Box_id=['#0']
                angle=str(-1)
                return Box_id,angle
                
            if True:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image_copy = np.copy(image)
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

                # two detect count equal can show
                if dbrcount == pyzbarcount:

                    #
                    #image_qr, boxID_list,sorted_dict_by_value_desc,angle_list = qr_object.qr_result(image.copy(), pc)
                    image_qr, boxID_list,sorted_dict_by_value_desc,angle_list = qr_object.qr_result(image, pc)

                    if boxID_list and angle_list:
                        qr_dict = {'box_id': boxID_list, 'angle': angle_list}
                    else:
                        qr_dict = {'box_id': '0', 'angle': '-1'}

                    box_id = qr_dict['box_id']
                    angle = qr_dict['angle']
                    for idx, box in enumerate(qr_dict['box_id']):
                        if box == '#20':
                            angle[idx] = 0

                    cv2.putText(image, f"ID: {box_id}, angle: {angle}",(50,50), cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255,1))
                    cv2.imshow('image',image)
                    Box_id = ['#' + item for item in box_id]
                    # print(Box_id,angle)
                    # Box_id 檢測到的全部東西 ex: ['#9', '#7']
                    print('Box_id: ', Box_id)
                    print('angle: ', angle)
                    # --------------------------------
                    if self.detect_count_change:
                        # 此段為改變偵測順序
                        websocket_visual_result(None, self.detect_count)
                    websocket_visual_result(Box_id, None)
                    self.detect_count_change = False
                    self.detect_box = Box_id
                    # --------------------------------

                    return Box_id,angle
            time.sleep(0.3)       

    def thread2_supplycheck(self):
        self.frontend_display=4
        while self.Pc_system:  
            if (self.Robot_sensor3 or self.frontend_display==2) and not self.removelock:
            # if self.Robot_sensor3 and not self.removelock and not self.Robot_sensor1:
                print('開始檢測')
                self.Pc_checked=True
                result = self.main()
                # result = self.main()
                if result[0][0] != '#0'or result[1] != '-1':                
                    while self.Pc_system:
                        Box_ID = result[0][:]
                        Box_angle = result[1][:]

                        for item in self.name_checked:
                            if item in Box_ID:
                                Box_ID.remove(item)
                                time.sleep(0.01)
                        for item in self.angle_checked:
                            if item in Box_angle:
                                Box_angle.remove(item)
                                time.sleep(0.01)
                        # 偵測正確就會移除對的
                        print(self.name_list)
                        if len(Box_ID)!=0:
                            if self.name_list[0] == Box_ID[0]:
                                self.name_checked.append(self.name_list.pop(0))
                                self.angle_checked.append(Box_angle[0])
                                print('Box correct:',self.name_checked,self.angle_checked)
                                # ------------------------------
                                websocket_robot_state('correct')          
                                # ------------------------------
                                self.frontend_boxnumber+=1
                                #正確
                                self.frontend_display=1
                            else:
                                #錯誤
                                self.frontend_display=2
                                # self.name_wrong.appendmoc(Box_ID[0])
                                print('Box false:',Box_ID[0])
                                # ------------------------------
                                websocket_robot_state('error')          
                                # ------------------------------
                                break
                        
                        else:
                            break
                        time.sleep(0.5)
                        self.frontend_display=3
                self.Pc_checked=False
            # ------------------------------
            else:
                if self.detect_count_change:
                    self.detect_box = self.detect_box[1:]
                    # 此段為改變偵測順序
                    websocket_visual_result(self.detect_box, self.detect_count)
                self.detect_count_change = False
            # ------------------------------
            time.sleep(0.5)
        self.frontend_display=0

    # def thread2_supplycheck(self):
    #     asyncio.run(self.supplycheck())

    def Pc_speed(self,D_data):
        D_data=D_data*50
        D_data_hex= decimal_to_hex(D_data)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 01 00 01 02 00 00  " + D_data_hex.replace(" ", ""))
        self.client_socket4.sendto(data_packet, (self.server_ip, self.server_port))

    ####################### 
    def frontend_motion(self):
        self.frontend_start=self.Pc_start
        self.frontend_pause=self.Pc_pause
        self.frontend_keepgo=self.Pc_keepgo
        self.frontend_reset=self.Pc_reset
        self.frontend_catch=self.Pc_catch
        self.frontend_put=self.Pc_put
        self.frontend_finish=self.Pc_finish      
    #流程檢查
    def process_track(self):
        status=False
        self.Pc_send=True

        while self.Pc_system:
            time.sleep(0.1)
            if self.Robot_received:
                print('send command recieved')
            
                while self.Pc_system:
                    time.sleep(0.1)
                    if self.Robot_motion:
                        self.Pc_send=False
                        print('Robot recieve then in action')

                        while self.Pc_system:
                            time.sleep(0.1)
                            if not self.Robot_motion:
                                print('Robot action finish')
                                # ----------------------------
                                if self.robot_count <= self.order_count:
                                    websocket_robot_state('prepare')
                                    websocket_object_count(self.robot_count)
                                # ----------------------------
                                break
                            
                        print('send_packet next time')
                        status=True
                        return status
                   
    def motion(self,case,position,checkangle):
        packet = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        packet[1]=case
        packet[-7:]=position

        if case==1:
            if checkangle==1:
                packet[3], packet[4] = packet[4], packet[3]
                packet[-1:]=[90.0]
            packet[4]=0

        print(packet)
        packet_dict={'process':packet[0],'case':packet[1],'userbase':packet[2],'X':packet[3],
                     'Y':packet[4],'Z':packet[5],'A':packet[6],'B':packet[7],'C':packet[8]}
         
        self.send_position(packet_dict)

        result = self.process_track()

        return result
    
    def Camera_orderchecked(self):

        while self.Pc_system:

            if not self.Pc_checked  and not len(self.name_checked)==0 and self.Robot_sensor1:
                # 這邊開始關閉偵測
                self.removelock=True

                self.checkangle = 1 if self.angle_checked[0]== 1 else 0
            
                print('移除前:',self.name_checked, self.angle_checked)
                self.name_checked.pop(0)
                self.angle_checked.pop(0)
                break
                
            time.sleep(0.1)

    #Demo1  
    def Robot_Demo1(self, orderId, order_list, order_count, isFinish_queue):    
        # --------------------------------
        box_positions_conveyor_path = os.path.join(settings.MEDIA_ROOT, f'Figures_step2_{orderId}', 'box_positions_conveyor.csv')
        # --------------------------------
        Supply = pd.read_csv(box_positions_conveyor_path)
        Supply_namecolumns = Supply['matched_box_name']
        name_list1=[]
        for name in Supply_namecolumns:
            name_list1.append(name.replace('外箱', '').replace('A', ''))
        self.name_list=name_list1[:]

        # asyncio.run(self.R1(orderId, order_list, order_count, isFinish_queue))  
    # async def R1(self, orderId, order_list, order_count, isFinish_queue):
        count=1
        self.thread0.start()
        self.reset()
        time.sleep(1)
        self.start()
        print('等待機器人啟動')

        while self.Pc_system:
            if self.Robot_start:
                print('程式啟動')
                break
            time.sleep(0.1)
        while self.Pc_system:

            if self.Robot_initial:
                print('回到起始位')
                break
            time.sleep(0.1)

        catch_list, put_list,count_list = getdata(orderId)

        for catch_input, put_input in zip(catch_list, put_list):
                print('等待檢測')
                # 此行註解到變 demo1
                # self.Camera_orderchecked()

                # -----------------------
                websocket_object_count(count)
                next_name = order_list[count] if count < order_count else ""
                websocket_object_name(order_list[count - 1], next_name)
                #------------------------
                
                while self.Pc_system:
                    self.Pc_boxchecked=True
                    print('catch第%d次'%(count))
                    # -----------------------
                    websocket_robot_state('prepare')
                    # -----------------------
                    self.Pc_catch=True
                    self.Pc_put=False
                    taskmotion=self.motion(1,catch_input,self.checkangle)
                
                    if taskmotion:
                        self.Pc_boxchecked=False
                        self.removelock=False
                        break  

                while self.Pc_system:
                    print('put第%d次'%(count))
                    # -----------------------
                    websocket_robot_state('operate')
                    # -----------------------
                    self.Pc_catch=False
                    self.Pc_put=True
                    taskmotion=self.motion(2,put_input,self.checkangle)
                    
                    if taskmotion:
                        count+=1
                        break

                if count==count_list or not self.Pc_system:
                    if not self.Pc_system:
                        print('系統重置')
                        # --------------------
                        isFinish_queue.put(False)
                        # --------------------
                    else:
                        self.Pc_speed(20)
                        home_input=[1, 0, 0, 0, 0, 0, 0]
                        self.motion(3,home_input,self.checkangle)
                        print('回到原點')
                        # --------------------
                        isFinish_queue.put(True)
                        # --------------------
                    break
                time.sleep(0.1)
        time.sleep(0.5)
        self.Pc_finish=True
        self.Pc_system=False
        print("Connection closed.")

    #Demo2    
    def Robot_Demo2(self, orderId, order_list, order_count, isFinish_queue):
        # --------------------------------
        self.order_count = order_count
        box_positions_conveyor_path = os.path.join(settings.MEDIA_ROOT, f'Figures_step2_{orderId}', 'box_positions_conveyor.csv')
        # --------------------------------
        Supply = pd.read_csv(box_positions_conveyor_path)
        Supply_namecolumns = Supply['matched_box_name']
        name_list1=[]
        for name in Supply_namecolumns:
            name_list1.append(name.replace('外箱', '').replace('A', ''))
        self.name_list=name_list1[:]

        # asyncio.run(self.R1(orderId, order_list, order_count, isFinish_queue))  
    # async def R1(self, orderId, order_list, order_count, isFinish_queue):
        count=1
        self.thread0.start()
        self.reset()
        time.sleep(1)
        self.start()
        print('等待機器人啟動')

        while self.Pc_system:
            if self.Robot_start:
                print('程式啟動')
                break
            time.sleep(0.1)
        while self.Pc_system:

            if self.Robot_initial:
                print('回到起始位')
                break
            time.sleep(0.1)

        catch_list, put_list,count_list = getdata(orderId)
        # -----------------------
        websocket_robot_state('detect')
        websocket_object_count(1)
        websocket_robot_state('prepare')               
        #------------------------

        for catch_input, put_input in zip(catch_list, put_list):
                print('等待檢測')
                # 此行註解到變 demo1
                self.Camera_orderchecked()

                # -----------------------
                if count == 1:
                    websocket_robot_state('prepare')
                    websocket_object_count(count)              
                #------------------------
                
                while self.Pc_system:
                    self.Pc_boxchecked=True
                    print('catch第%d次'%(count))
                    self.Pc_catch=True
                    self.Pc_put=False
                    taskmotion=self.motion(1,catch_input,self.checkangle)

                    if taskmotion:
                        self.Pc_boxchecked=False
                        # -----------------------
                        if count < order_count:
                            next_name = order_list[count + 1] if count < order_count - 1 else ''
                            websocket_object_name(order_list[count], next_name)
                        # -----------------------
                        # 解鎖開始偵測
                        self.removelock=False
                        # -----------------------
                        self.detect_count_change = True
                        self.detect_count = count + 1
                        # -----------------------
                        break  

                while self.Pc_system:
                    print('put第%d次'%(count))
                    # ------------------------------
                    websocket_robot_state('operate')
                    self.robot_count = count + 1
                    # ------------------------------
                    self.Pc_catch=False
                    self.Pc_put=True
                    taskmotion=self.motion(2,put_input,self.checkangle)
                    
                    if taskmotion:
                        count+=1
                        break

                if count==count_list or not self.Pc_system:
                    if not self.Pc_system:
                        print('系統重置')
                        # --------------------
                        isFinish_queue.put(False)
                        # --------------------
                    else:
                        self.Pc_speed(20)
                        home_input=[1, 0, 0, 0, 0, 0, 0]
                        self.motion(3,home_input,self.checkangle)
                        print('回到原點')
                        # --------------------
                        isFinish_queue.put(True)
                        # --------------------
                    break
                time.sleep(0.1)
        time.sleep(0.5)
        self.Pc_finish=True
        self.Pc_system=False
        self.thread0.join()
        print("Connection closed.")  
# ########################################################################## 

