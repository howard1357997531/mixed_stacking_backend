import socket
import time
import pandas as pd
import csv
from .main import cameraCheck

robot_state=True
motion_state=0
itemstatus=0
angle=0

# ------------------------------
# web_socket
from views import websocket_robot_state, websocket_object_count
# ------------------------------

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

def status():
        global itemstatus
        return itemstatus

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
    count_list=0
    for index, row in Supply_columns.iterrows():
        supply_initial = row.to_list()
        Base=[2]
        supply_data=Base+supply_initial+posture1    
        catch_list.append(supply_data)
    for index, row in Place_columns.iterrows():
        place_initial = row.to_list()
        if  place_initial[4]== 1.0:
            posture=posture2
        else :
            posture=posture1    
        if place_initial[0]==1:
            Base=[3]
        else:
            Base=[4]
        place_data=Base+place_initial[1:4]+posture
        put_list.append(place_data)
        count_list+=1
    return (catch_list,put_list,count_list)
##########################################################################
class Yaskawa_control():
    
    def __init__(self, ip ,port):
        self.server_ip = ip
        self.server_port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # --------------------
        # self.orderId = orderId
        # --------------------

    def send_packet(self,data_packet):
        self.client_socket.sendto(data_packet, (self.server_ip, self.server_port))
        response, addr = self.client_socket.recvfrom(1024)
        return response
   
    #控制用命令
    def send_control(self, control_input):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 8D 0A 01 10 00 00 " + control_input.replace(" ", ""))
        response = self.send_packet(data_packet) 
        RES = str('5945524320000000030101010000008039393939393939398200000000000000')
        # if response.hex() == RES:
        #     print('fail')
        # else:
        #     print('success')
    #即時控制用#
    ########################   
    def servo(self):
        self.send_control('01')
        self.send_control('05')
        
    def keepgo(self):
        global robot_state
        robot_state=True
        self.send_control('15')

    def pause(self):
        self.send_control('07')
        self.send_control('05')

    def reset(self):
        global robot_state
        self.send_control('07')
        self.send_control('00')
        self.send_control('25')
        self.send_control('00')
        robot_state=False

    def close(self):
        self.client_socket.close()
        print("Connection closed.")

    def speed(self,D_data):
        D_data=D_data*50
        D_data_hex= decimal_to_hex(D_data)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 01 00 01 02 00 00  " + D_data_hex.replace(" ", ""))
        self.send_packet(data_packet)
        return D_data
    ####################### 
    #D23 單個D傳值測試
    def sendD23(self,D_data):
        D_data_hex= decimal_to_hex(D_data)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 17 00 01 02 00 00  " + D_data_hex.replace(" ", ""))
        self.send_packet(data_packet)

    #D格式資料處理+傳送
    def Dword_packet(self,data_D):
        for position, value in data_D.items():
            if position in ['process']:
                decimal_value = int(value * 1)
            elif position in ['case']:
                decimal_value = int(value * 1)
            elif position in ['userbase']:
                decimal_value = int(value * 1)
            elif position in ['X', 'Y', 'Z']:
                decimal_value = int(value * 1000)
            else:
                decimal_value = int(value * 10000)
            hex_value = decimal_to_hex(decimal_value)
            #print(hex_value)

            Datalengh_mapping = {'process': '04','case': '04','userbase': '04','X': '04','Y': '04','Z': '04','A': '04','B': '04','C': '04'}#資料長度
            position_mapping = {'process': '11','case': '12','userbase': '10','X': '04','Y': '05','Z': '06','A': '07','B': '08','C': '09'}#座標編號
            Write_mapping = '02'

            data_packet = bytes.fromhex(f"59 45 52 43 20 00 {Datalengh_mapping[position]} 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 {position_mapping[position]} 00 01 {Write_mapping}  00 00 " + hex_value.replace(" ", ""))
            self.send_packet(data_packet)
            #print(f"Received response from MOTOMAN robot: {response.hex()}") 
                         
    #上位機訊號
    def PCsignal(self,a):
        signal=decimal_to_hex1(a)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 08 00 01 02 00 00  " + signal.replace(" ", ""))
        self.send_packet(data_packet)

    #讀取座標暫存器:B8
    def request_PCsignal(self):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 08 00 01 01 00 00 00" )
        response=self.send_packet(data_packet)
        response_R = response.hex()[-18:]
        # print(f"Received response from MOTOMAN robot: {response.hex()}")
        if response_R[:2]=='81':
            if response_R.endswith("01"):
                status=True
            else:
                status=False
            return status
          
    #B011為TRUE才需要校正
    def send_boxcheck(self,a):
        signal=decimal_to_hex1(a)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 0B 00 01 02 00 00  " + signal.replace(" ", ""))
        self.send_packet(data_packet)

    #B012檢查狀態1正確 2錯誤 3下一個
    def sendB12(self,a):
        signal=decimal_to_hex1(a)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 0C 00 01 02 00 00  " + signal.replace(" ", ""))
        self.send_packet(data_packet)

    #讀取網域輸入信號'00'break全部迴圈   
    def request_robotsystem(self):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 8D 0A 01 0E 00 00 00" )
        response=self.send_packet(data_packet)
        response_R = response.hex()[-18:]
        #print(f"Received response from MOTOMAN robot: {response.hex()}")
        last_char = response_R[-1]
        status = int(last_char, 16)
        return status
    
    #檢查系統狀態
    def request_system(self):
        global robot_state
        if robot_state:
            status=True
        else:
            # The above code is declaring a variable `status` and assigning it the value `False`.
            status=False
        return status 
    #狀態請求
    def request_sendB12(self):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 0C 00 01 01 00 00 00" )
        response=self.send_packet(data_packet)
        response_R = response.hex()
        last_digit = int(response_R[-1])
        return last_digit 
       
    #機器人接收/動作暫存器:B100
    def request_robotsignal(self):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 64 00 01 01 00 00 00" )
        response=self.send_packet(data_packet)
        response_R = response.hex()[-18:]
        #print(f"Received response from MOTOMAN robot: {response.hex()}")
        if response_R[:2]=='81':
            if response_R.endswith("01"):
                status=True
            else:
                status=False
            return status
            
    #讀取機器人是否初始化
    def request_Initial(self):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 67 00 01 01 00 00 00" )
        response=self.send_packet(data_packet)
        response_R = response.hex()[-18:]
        #print(f"Received response from MOTOMAN robot: {response.hex()}")
        if response_R[:2]=='81':
            if response_R.endswith("01"):
                status=True
            else:
                status=False
            return status
           
    #sensor訊號:in(9)
    def request_sensor9(self):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 D4 07 01 0E 00 00 00" )
        response=self.send_packet(data_packet)
        response_R = response.hex()[-18:]
        #print(f"Received response from MOTOMAN robot: {response.hex()}")
        if response_R[:2]=='8e':
            signal_hex = response_R[-2:]
            signal_int = int(signal_hex, 16)
            signal_binary = bin(signal_int)[2:].zfill(8) 
            if signal_binary[-1] == '1':
                status=True
            else:
                status=False
            return status
          
    #sensor訊號:in(10)
    def request_sensor10(self):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 D4 07 01 0E 00 00 00" )
        response=self.send_packet(data_packet)
        response_R = response.hex()[-18:]
        #print(f"Received response from MOTOMAN robot: {response.hex()}")
        if response_R[:2]=='8e':
            signal_hex = response_R[-2:]
            signal_int = int(signal_hex, 16)
            signal_binary = bin(signal_int)[2:].zfill(8) 
            if signal_binary[-2] == '1':
                status=True
            else:
                status=False
            return status
          
    #sensor訊號:in(11)
    def request_sensor11(self):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 D4 07 01 0E 00 00 00" )
        response=self.send_packet(data_packet)
        response_R = response.hex()[-18:]
        # print(f"Received response from MOTOMAN robot: {response.hex()}")
        # print(response_R)
        if response_R[:2]=='8e':
            signal_hex = response_R[-2:]
            signal_int = int(signal_hex,16)
            signal_binary = bin(signal_int)[2:].zfill(8) 
            if signal_binary[-3] == '1':
                status=True
            else:
                status=False
            return status
        
    #訊號檢查
    def handshake(self):
        global itemstatus
        global motion_state
        self.PCsignal(True)
        sendsignal=False
        robotsignal=False
        time.sleep(0.05) 
        if self.request_PCsignal()==True:
            sendsignal=True
            print('send_packet success')
            while True:
                if self.request_system()==False:
                    print('STOP2')
                    break     
                if self.request_robotsignal()==True:
                    print('Robot recieve_data success')
                    if motion_state==1:
                        itemstatus=3
                    self.PCsignal(False )
                    time.sleep(0.05) 
                    while True:
                        if self.request_robotsignal()==False:
                            print(self.request_robotsignal())
                            robotsignal=True
                            print('Robot action finish')
                            break
                        if self.request_system()==False:
                            print('STOP3')
                            break
                if robotsignal==True and sendsignal==True:
                    print('send_packet next time')
                    break
        else:
            print('send_packet fail')
            sendsignal=False
            robotsignal=False    
        return (sendsignal,robotsignal)
    
    #工單檢查函式
    def supplycheck(self, orderId):
        global itemstatus
        global robot_state
        global angle
        itemstatus=5
        robot_state=True
        # --------------------------------
        box_positions_conveyor_path = os.path.join(settings.MEDIA_ROOT, f'Figures_step2_{orderId}', 'box_positions_conveyor.csv')
        # --------------------------------
        Supply = pd.read_csv(box_positions_conveyor_path)
        Supply_columns = Supply['matched_box_name']
        for name in Supply_columns: 
            if self.request_system()==False:
                itemstatus=0
                break
            while True:
                if self.request_system()==False:
                    itemstatus=0
                    break
                time.sleep(0.1)
                if itemstatus !=1 and self.request_sensor11():
                    print('開始檢測')
                    sd = cameraCheck()
                #相機函式
                    if sd[0] == name.replace('外箱', '').replace('A', ''):#檢查第一位
                        print("Incoming materials are correct")
                        websocket_robot_state('correct')
                        if sd[1]==1:
                            angle=1
                            print("angle:1")
                        else:
                            angle=0
                            print("angle:0")
                        #正確
                        itemstatus=1
                        break
                    else:
                        #錯誤
                        itemstatus=2
                        print("Incoming materials are false")
                        
                        websocket_robot_state('error')
                    

    #將上位機數據傳入手臂
    def send_data(self,D_data):   
        print(D_data)
        data_dict={'process':D_data[0],'case':D_data[1],'userbase':D_data[2],'X':D_data[3],'Y':D_data[4],'Z':D_data[5],'A':D_data[6],'B':D_data[7],'C':D_data[8]}
        self.Dword_packet(data_dict)

        hand_result=self.handshake()
        if hand_result==(True,True):
            result=True
        else:
            result=False
        return result
    
##########################################################################    
    #Demo1
    def Robot_Demo1(self):
        self.reset()
        time.sleep(1)
        self.servo()
        self.keepgo()
        print('等待初始化')
        while True:
            if self.request_system()==False:
                break
            if self.request_Initial()==True:
                print('回到起始位')
                break
        catch_list, put_list,count_list = getdata()
        count=1
        packet = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        for catch_input, put_input in zip(catch_list, put_list):
                while True:
                    if self.request_system()==False:
                        break
                    print('catch第%d次'%(count))
                    case=1
                    packet[1]=case
                    packet[-7:]=catch_input
                    packet[4]=0
                    result=self.send_data(packet)
                    if result==True:
                        break  
                while True:
                    if self.request_system()==False:
                        break
                    print('put第%d次'%(count))
                    case=2
                    packet[1]=case
                    packet[-7:]=put_input
                    result=self.send_data(packet)
                    if result==True:
                        count+=1
                        break   
                if count==count_list+1 or self.request_system()==False:
                    if self.request_system()==False:
                        print('系統重置')
                    else:
                        case=3
                        packet[1]=case
                        home_input=[1, 0, 0, 0, 0, 0, 0]
                        packet[-7:]=home_input
                        result=self.send_data(packet)
                        print('回到原點')
                    break
        self.pause()
        self.reset()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.close()
        print("Connection closed.")  

##########################################################################
    #Demo2
    def Robot_Demo2(self, orderId):
        global itemstatus
        global angle
        global motion_state
        self.reset()
        time.sleep(1)
        self.servo()
        self.keepgo()
        print('等待初始化')
        while True:
            if self.request_system()==False:
                break
            if self.request_Initial()==True:
                print('回到起始位')
                break
        catch_list, put_list, count_list = getdata(orderId)
        count=1
        packet = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        for catch_input, put_input in zip(catch_list, put_list):
                print('等待檢測')
                websocket_robot_state('detect')
                while True:
                    if self.request_system()==False:
                        break
                    if itemstatus==1 and self.request_sensor11()==False:
                        if angle==1:
                            catch_input[1], catch_input[2] = catch_input[2], catch_input[1]
                            catch_input[-3:]=[180.0,0.0,90.0]
                        print('檢測正確')
                        print(catch_input)
                        self.send_boxcheck(True)
                        break
                while True:
                    motion_state=1
                    if self.request_system()==False:
                        break
                    print('catch第%d次'%(count))
                    websocket_robot_state('prepare')
                    websocket_object_count(count)
                    case=1
                    packet[1]=case
                    packet[-7:]=catch_input
                    packet[4]=0
                    result=self.send_data(packet)
                    if result==True:
                        #itemstatus=4
                        break  
                while True:
                    motion_state=2
                    if self.request_system()==False:
                        break
                    print('put第%d次'%(count))
                    websocket_robot_state('operate')
                    websocket_object_count(count)
                    case=2
                    packet[1]=case
                    packet[-7:]=put_input
                    result=self.send_data(packet)
                    if result==True:
                        count+=1
                        break   
                if count==count_list+1 or self.request_system()==False:
                    if self.request_system()==False:
                        print('系統重置')
                        websocket_robot_state('reset')
                    else:
                        case=3
                        packet[1]=case
                        home_input=[1, 0, 0, 0, 0, 0, 0]
                        packet[-7:]=home_input
                        result=self.send_data(packet)
                        print('回到原點')
                    break
        self.pause()
        self.reset()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.close()
        print("Connection closed.")  
##########################################################################   
