import socket
# import websockets
import asyncio
import time
import pandas as pd
import xml.etree.ElementTree as ET
import time
from .Dimension_2_3D_single import Dimension_2_3D
from .Dimension_3D_single import Dimension_3D
import cv2
import numpy as np
from .camera import intelCamera_copy
from .qrcode import qrClass
import threading

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

aaa=0
signal_int=int(aaa)
signalbinary = bin(signal_int)[2:].zfill(8)
motionsignal=signalbinary 
sensorsignal=signalbinary 
statussignal=signalbinary 

# Supply = pd.read_csv('box_positions_conveyor.csv')
# Place = pd.read_csv('box_positions_final.csv')
# Supply_namecolumns = Supply['matched_box_name']
# Supply_columns = Supply[['pos_x', 'pos_y', 'pos_z']]
# Place_columns = Place[['bin_name','X_cog', 'Y_cog', 'Z_cog','orientation']]
# name_list1=[]
# for name in Supply_namecolumns:
#     name_list1.append(name)
#爬取位置資料 並分析姿勢轉換成列
def mix_pack(Supply_columns, Place_columns):  ####混料系統####
    catch_list = []
    put_list = []
    posture1=[48.23, 0, 180]
    posture2=[138.23, 0, 180]
    count_list=1

    for index, row in Supply_columns.iterrows():
        supply_initial = row.to_list()
        Base=[12]
        supply_data=Base+supply_initial+posture1    
        catch_list.append(supply_data)

    for index, row in Place_columns.iterrows():
        place_initial = row.to_list()
        posture = posture2 if place_initial[4] == 1.0 else posture1    
        Base = [13] if place_initial[0] == 1 else [14]
        place_data=Base+place_initial[1:4]+posture
        put_list.append(place_data)
        count_list+=1

    return (catch_list,put_list,count_list)

def smart_pack(Supply_columns, Place_columns):  ####智慧堆棧系統####
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
class Kuka_control():

    def __init__(self):
        self.server_ip  = '172.31.1.147'
        self.server_port= 54600
        self.server_port1= 54601
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.server_port))
        self.client_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket1.connect((self.server_ip, self.server_port1))
        self.system_choose=1
        self.count=1
        self.count_list=1
        self.name_list=[]
        self.angle_checked=[]
        self.checkangle=0
        self.name_checked=[]
        self.name_wrong=[]
        self.motion_state=0
        self.Pc_checked=False
        self.Pc_system=False
        self.dectect_system=False
        self.packetsendlock=False
        self.removelock=False
        self.controllock=False
        self.commandlock=False
        self.thread0=threading.Thread(target=self.control_response)
        ########################上位機-機器人########################
        self.motionsignal=motionsignal
        self.sensorsignal=sensorsignal
        self.statussignal=statussignal
        #out(300)~out(307)
        self.Pc_control=0
        self.Pc_start=False#300
        self.Pc_pause=False#301
        self.Pc_keepgo=False#302
        self.Pc_reset=False#303
        self.Pc_send=False#304
        self.Pc_boxchecked=False#305
        self.Pc_wrong=False
        self.Pc_correctfinish=False
        self.Pc_speed=20
        #out(1)~out(8)
        self.Pc_out=0
        self.Pc_suck=False#1
        self.Pc_conveyor=False#2
        self.Pc_correct=False#3
        #out(508)~out(515)
        self.Robot_start=False#508
        self.Robot_pause=False#509
        self.Robot_keepgo=False#510
        self.Robot_reset=False#511
        self.Robot_received=False#512
        self.Robot_boxchecked=False#513
       
        #out(500)~out(507)
        self.Robot_initial=False#500
        self.Robot_correctnext=False#501
        self.Robot_motion=False#502
        self.Robot_action=False#503
        #self.Robot_correctnext=False
        #self.Robot_dosuck=False
        #in(9)~in(16)
        self.Robot_sensor1=False#13
        self.Robot_sensor2=False
        self.Robot_sensor3=False
        ########################上位機-機器人########################
        ########################前台-上位機########################
        self.Pc_catch=False
        self.Pc_put=False
        self.Pc_finish=False
        self.frontend_display=0
        self.frontend_boxnumber=0
        self.frontend_motion=0
        ########################前台-上位機########################






    ###############################I/O通訊用#################################   
    async def send_position(self):
        while not self.Pc_finish:
            if self.packetsendlock:
                data_packet = self.position_packet(self.packet_dict)
                self.client_socket1.sendto(data_packet, (self.server_ip, self.server_port1))
                response, addr = self.client_socket1.recvfrom(1024)
                self.packetsendlock=False
            await asyncio.sleep(0.1)
    
    def position_packet(self,packet):
        textRoot = ET.Element('sensor')
        for key, value in packet.items():
            element = ET.SubElement(textRoot, key)
            element.text = str(value)
        return bytes(ET.tostring(textRoot,'utf_8'))
    
    async def send_control(self):
        while not self.Pc_finish:
            self.Pc_control = (self.Pc_correctfinish << 5) + (self.Pc_send << 4)+ (self.Pc_reset << 3) + (self.Pc_keepgo << 2) + (self.Pc_pause << 1)+ self.Pc_start
            packet=[self.Pc_control, self.Pc_speed]
            data_packet = self.control_packet(packet)
            self.client_socket.sendto(data_packet, (self.server_ip, self.server_port))
            await asyncio.sleep(0)

    def control_packet(self,packet):
        textRoot = ET.Element('sensor')
        control = ET.SubElement(textRoot,'control')
        speed = ET.SubElement(textRoot,'speed')
        control.text = str(packet[0])
        speed.text = str(packet[1])
        return bytes(ET.tostring(textRoot,'utf_8'))
    
    async def robot_response(self):
        while not self.Pc_finish:
            try:
                received = str(self.client_socket.recv(1024), "utf-8")
                receiveData = ET.fromstring(received)
                status = receiveData.find('status1_8').text
                sensor = receiveData.find('sensor1_8').text
                motion = receiveData.find('motion1_8').text
                status_int=int(status)
                self.statussignal = bin(status_int)[2:].zfill(8)
                sensor_int=int(sensor)
                self.sensorsignal = bin(sensor_int)[2:].zfill(8)
                motion_int=int(motion)
                self.motionsignal = bin(motion_int)[2:].zfill(8)
                self.Robot_start=bool(int(self.statussignal[-1]))#508
                self.Robot_received=bool(int(self.statussignal[-5]))#512
                self.Robot_correctfinish=bool(int(self.statussignal[-6]))#513
                self.Robot_initial=bool(int(self.motionsignal[-1]))
                self.Robot_correctnext=bool(int(self.motionsignal[-2]))
                self.Robot_motion=bool(int(self.motionsignal[-3]))
                self.Robot_action=bool(int(self.motionsignal[-4]))
                self.Robot_sensor1=bool(int(self.sensorsignal[-2]))
                # print(self.Robot_action)
                await asyncio.sleep(0)
            except:
                pass
                # print('error1')
                
    def control_response(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task1 = self.send_control()
        task2 = self.robot_response()
        task3 = self.send_position()
        # start_server = loop.run_until_complete(websockets.serve(self.handle, "localhost", 8765))
        loop.run_until_complete(asyncio.gather(task1,task2,task3))
        # start_server.close()
        # loop.run_until_complete(start_server.wait_closed())
        print("WebSocket server closed")  
    ###############################I/O通訊用#################################   
    ###############################即時控制用#################################  
    def start(self):
        self.Pc_system=True
        self.Pc_start=True

    def pause(self):
        self.frontend_motion=9
        self.Pc_pause=True
        self.Pc_keepgo=False

    def keepgo(self):
        self.frontend_motion=10
        self.Pc_pause=False
        self.Pc_keepgo=True

    def reset(self):
        self.Pc_pause=True
        time.sleep(0.1)
        self.Pc_start=False
        self.Pc_reset=True
        self.Pc_system=False
        time.sleep(0.5)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.close()
        self.client_socket1.close()
    
    def speed(self,data):
        self.Pc_speed=data
    ###############################即時控制用################################# 

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
            start_ = time.time()

            image, pc , depth_image =  i
            image_crop = image[crop['ymin']:crop['ymax'], crop['xmin']:crop['xmax']]    
            # cv2.imshow('image_crop', image_crop)
            # cv2.waitKey(1)
            if  self.Robot_sensor1:
                Box_id=['#0']
                angle=str(-1)
                return Box_id,angle
            print(1)
            
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
                    cv2.putText(image, f"ID: {box_id}, angle: {angle}",(50,50), cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255,1))
                    cv2.imshow('image',image)
                    Box_id = ['#' + item for item in box_id]
                    print(Box_id,angle)

                    return Box_id,angle
            time.sleep(0.1)       

    def thread2_supplycheck(self):
        self.frontend_display=4

        while self.dectect_system and not self.Pc_finish:  
            if (self.Robot_sensor3 or self.frontend_display==2) and not self.removelock:
                print('開始檢測')
                self.Pc_checked=True
                result = self. main()

                if result[0][0] != '#0'or result[1] != '-1':                
                    while self.dectect_system and not self.Pc_finish:   
                        Box_ID, Box_angle  = result[0][:], result[1][:]
                        
                        for item1, item2 in zip(self.name_checked, self.angle_checked):
                            if item1 in Box_ID and item2 in Box_angle:
                                Box_ID.remove(item1)
                                Box_angle.remove(item2)
                                time.sleep(0.1)
                                
                        if len(Box_ID)!=0:
                            if self.name_list[0] == Box_ID[0]:
                                self.name_checked.append(self.name_list.pop(0))
                                self.angle_checked.append(Box_angle[0])
                                print('Box correct:',self.name_checked,self.angle_checked)          
                                self.frontend_boxnumber += 1
                                self.frontend_display = 1  # 正確
                            else:
                                self.frontend_display = 2  # 錯誤
                                print('Box false:', Box_ID[0])
                                break
                        
                        else:
                            break
                        time.sleep(0.5)
                        self.frontend_display=3
                self.Pc_checked=False

            time.sleep(0.5)
            
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

                if self.frontend_motion==1:
                    await websocket.send('等待程式啟動')
                elif self.frontend_motion==2:
                    await websocket.send('等待初始化完畢')
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
                await asyncio.sleep(0)
    ###############################前台顯示用#################################
    def process_track(self):
        status=False
        self.Pc_send=True
        print('send command')

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
                            if self.Robot_action:
                                if self.motion_state == 1:
                                    self.frontend_motion = 3
                                elif self.motion_state == 2:
                                    self.frontend_motion = 4
                            if not self.Robot_motion:
                                print('Robot action finish')
                                break

                        print('send_packet next time')
                        status=True
                        return status
                    
    def motion(self,case,position,checkangle):
        packet = [0, 0, 0, 0, 0, 0, 0, 0]
        packet[0]=case
        packet[-7:]=position
        self.motion_state=case

        if case==1:
            if checkangle==1:
                packet[2], packet[3] = packet[3], packet[2]
                packet[-3]=[138.23]

        print(packet)
        self.packet_dict={'case':packet[0],'base':packet[1],'p1':packet[2],
                     'p2':packet[3],'p3':packet[4],'p4':packet[5],'p5':packet[6],'p6':packet[7]}
         
        self.packetsendlock=True 
        while self.Pc_system:
            if not self.packetsendlock:
                break
            time.sleep(0.1)

        result = self.process_track()

        return result
    
    def Robot_Demo(self, orderId, order_list, order_count, isFinish_queue):
        # --------------------------------
        self.order_list = order_list
        self.order_count = order_count
        self.isFinish_queue = isFinish_queue
        box_positions_conveyor_path = os.path.join(settings.MEDIA_ROOT, f'Figures_step2_{orderId}', 'box_positions_conveyor.csv')
        box_positions_final_path = os.path.join(settings.MEDIA_ROOT, f'Figures_step2_{orderId}', 'box_positions_final.csv')
        # --------------------------------
        Supply = pd.read_csv(box_positions_conveyor_path)
        Supply_namecolumns = Supply['matched_box_name']
        Place = pd.read_csv(box_positions_final_path)
        Supply_namecolumns = Supply['matched_box_name']
        self.Supply_columns = Supply[['pos_x', 'pos_y', 'pos_z']]
        self.Place_columns = Place[['bin_name','X_cog', 'Y_cog', 'Z_cog','orientation']]
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
        self.start()
        print('等待機器人啟動')
        self.frontend_motion=1
        while self.Pc_system:
            if self.Robot_start:
                print('程式啟動')
                break
            time.sleep(0.1)

    def initial_tile(self):
        while self.Pc_system:
            self.frontend_motion=2
            if self.Robot_initial:
                print('回到起始位')
                print('等待檢測')
                break
            time.sleep(0.1)

    def system_tile(self):
        #迴圈系統  包含運送之值 以及運算點為
        if self.system_choose==1:
            catch_list, put_list,self.count_list = mix_pack(self.Supply_columns, self.Place_columns)
        elif self.system_choose==2:
            catch_list, put_list,self.count_list = smart_pack(self.Supply_columns, self.Place_columns)

        for catch_input, put_input in zip(catch_list, put_list):
            # -----------------------
            websocket_object_count(self.count)
            next_name = self.order_list[self.count] if self.count < self.order_count else ""
            websocket_object_name(self.order_list[self.count - 1], next_name)
            #------------------------
            if self.dectect_system:
                self.Camera_orderchecked_tile()
            self.catch_tile(catch_input)
            self.put_tile(put_input)

    def Camera_orderchecked_tile(self):

        while self.Pc_system:

            if not self.Pc_checked  and not len(self.name_checked)==0 and self.Robot_sensor1:
                self.removelock=True

                self.checkangle = 1 if self.angle_checked[0]== 1 else 0
            
                print('移除前:',self.name_checked, self.angle_checked)
                self.name_checked.pop(0)
                self.angle_checked.pop(0)
                break
                
            time.sleep(0.1)

    def catch_tile(self,catch_input):
        while self.Pc_system:
            self.Pc_boxchecked=True
            print('catch第%d次'%(self.count))
            # -----------------------
            websocket_robot_state('prepare')
            # -----------------------
            if self.motion(1,catch_input,self.checkangle):
                self.frontend_motion=5
                self.Pc_boxchecked=False
                self.removelock=False
                break

    def put_tile(self,put_input):
        while self.Pc_system:
            
            print('put第%d次'%(self.count))
            # -----------------------
            websocket_robot_state('operate')
            # -----------------------
            if self.motion(2,put_input,self.checkangle):
                self.frontend_motion=6
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
                home_input=[12, 0, 0, 0, 48.23, 0, 180]
                self.motion(3,home_input,self.checkangle)
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